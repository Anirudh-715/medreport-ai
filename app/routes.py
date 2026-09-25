"""
Flask routes for the Medical Report Summarizer.
"""

import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Report
from app.config import Config

main_bp = Blueprint("main", __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp"}


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.route("/")
def index():
    """Home page with upload form."""
    missing = Config.get_missing_services()
    return render_template("index.html", missing_services=missing)


@main_bp.route("/sample-demo")
def sample_demo():
    """1-Click demo that analyzes the included sample patient pathology report."""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    sample_path = os.path.join(base_dir, "sample_data", "sample_report.pdf")
    
    if not os.path.exists(sample_path):
        flash("Sample report file not found on server.", "warning")
        return redirect(url_for("main.index"))

    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    filename = "Sample-Clinical-Report.pdf"
    report = Report(filename=filename, status="processing")
    db.session.add(report)
    db.session.commit()

    try:
        from app.services.report_analyzer import ReportAnalyzerService
        analyzer = ReportAnalyzerService()
        results = analyzer.analyze(file_bytes, filename)

        report.extracted_text = results.get("extracted_text", "")
        report.summary = results.get("summary", "")
        report.key_findings = json.dumps(results.get("key_findings", []))
        report.abnormal_values = json.dumps(results.get("abnormal_values", []))
        report.recommendations = json.dumps(results.get("recommendations", []))
        report.severity = results.get("severity", "Normal")
        report.blob_url = results.get("blob_url", "")
        report.status = "completed"
        db.session.commit()

        flash("Demo sample report analyzed successfully!", "success")
        return redirect(url_for("main.result", report_id=report.id))
    except Exception as e:
        report.status = "failed"
        report.error_message = str(e)
        db.session.commit()
        flash(f"Analysis failed: {str(e)}", "danger")
        return redirect(url_for("main.index"))


@main_bp.route("/upload", methods=["POST"])
def upload():
    """Handle file upload and trigger the analysis pipeline."""

    # --- Validate file ---
    if "file" not in request.files:
        flash("No file selected. Please choose a medical report to upload.", "danger")
        return redirect(url_for("main.index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected. Please choose a medical report to upload.", "danger")
        return redirect(url_for("main.index"))

    if not allowed_file(file.filename):
        flash(
            f"Unsupported file format. Please upload one of: {', '.join(ALLOWED_EXTENSIONS)}",
            "danger",
        )
        return redirect(url_for("main.index"))

    # --- Read file bytes ---
    filename = secure_filename(file.filename)
    file_bytes = file.read()

    # Save locally as backup
    local_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    with open(local_path, "wb") as f:
        f.write(file_bytes)

    # --- Create report record ---
    report = Report(filename=filename, status="processing")
    db.session.add(report)
    db.session.commit()

    # --- Run analysis pipeline ---
    try:
        from app.services.report_analyzer import ReportAnalyzerService

        analyzer = ReportAnalyzerService()
        results = analyzer.analyze(file_bytes, filename)

        # Update report with results
        report.extracted_text = results.get("extracted_text", "")
        report.summary = results.get("summary", "")
        report.key_findings = json.dumps(results.get("key_findings", []))
        report.abnormal_values = json.dumps(results.get("abnormal_values", []))
        report.recommendations = json.dumps(results.get("recommendations", []))
        report.severity = results.get("severity", "Unknown")
        report.blob_url = results.get("blob_url", "")
        report.status = "completed"

        db.session.commit()

        flash("Report analyzed successfully!", "success")
        return redirect(url_for("main.result", report_id=report.id))

    except Exception as e:
        report.status = "failed"
        report.error_message = str(e)
        db.session.commit()

        flash(f"Analysis failed: {str(e)}", "danger")
        return redirect(url_for("main.index"))


@main_bp.route("/result/<int:report_id>")
def result(report_id):
    """Display analysis results for a specific report."""
    report = Report.query.get_or_404(report_id)
    return render_template("result.html", report=report.to_dict())


@main_bp.route("/history")
def history():
    """Show all past analyzed reports."""
    reports = Report.query.order_by(Report.upload_time.desc()).all()
    reports_list = [r.to_dict() for r in reports]
    return render_template("history.html", reports=reports_list)


@main_bp.route("/delete/<int:report_id>", methods=["POST"])
def delete_report(report_id):
    """Delete a report from history."""
    report = Report.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash("Report deleted.", "info")
    return redirect(url_for("main.history"))
