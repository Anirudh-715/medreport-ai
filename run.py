"""
MedReport AI - Medical Report Summarizer
Entry point for the Flask application.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  MedReport AI - Medical Report Summarizer")
    print("=" * 50)
    print(f"  Running at: http://127.0.0.1:5000")
    print(f"  Upload medical reports to get AI summaries")
    print("=" * 50 + "\n")
    app.run(debug=True, port=5000)
