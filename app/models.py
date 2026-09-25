"""
Database models for storing analyzed medical reports.
"""

from datetime import datetime, timezone
from app import db


class Report(db.Model):
    """Represents an analyzed medical report."""

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Extracted content
    extracted_text = db.Column(db.Text, default="")

    # AI analysis results (stored as JSON strings)
    summary = db.Column(db.Text, default="")
    key_findings = db.Column(db.Text, default="[]")      # JSON list
    abnormal_values = db.Column(db.Text, default="[]")    # JSON list
    recommendations = db.Column(db.Text, default="[]")    # JSON list
    severity = db.Column(db.String(50), default="Unknown")

    # Storage
    blob_url = db.Column(db.String(500), default="")

    # Status
    status = db.Column(db.String(50), default="pending")  # pending, processing, completed, failed
    error_message = db.Column(db.Text, default="")

    def __repr__(self):
        return f"<Report {self.id}: {self.filename} ({self.status})>"

    def to_dict(self) -> dict:
        """Convert report to dictionary for easy template rendering."""
        import json
        return {
            "id": self.id,
            "filename": self.filename,
            "upload_time": self.upload_time.strftime("%d %b %Y, %I:%M %p") if self.upload_time else "",
            "summary": self.summary,
            "key_findings": json.loads(self.key_findings) if self.key_findings else [],
            "abnormal_values": json.loads(self.abnormal_values) if self.abnormal_values else [],
            "recommendations": json.loads(self.recommendations) if self.recommendations else [],
            "severity": self.severity,
            "extracted_text": self.extracted_text,
            "blob_url": self.blob_url,
            "status": self.status,
            "error_message": self.error_message,
        }
