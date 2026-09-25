"""
Intelligent Medical Report Summarizer Service.

Supports multiple AI backends with automatic failover:
1. Azure OpenAI (if configured)
2. Google Gemini API (Free tier from Google AI Studio)
3. Groq API (Free tier with Llama 3)
4. Standard OpenAI API
5. Built-in Clinical Lab Rule Engine (analyzes real lab values even with 0 API credits)
"""

import json
import re
from openai import AzureOpenAI, OpenAI
from app.config import Config


MEDICAL_ANALYST_SYSTEM_PROMPT = """\
You are an expert medical report analyst with deep knowledge of clinical laboratory medicine, diagnostic imaging, pathology, and general medical terminology.

Analyze the provided medical report and return ONLY valid JSON with these keys:
1. "summary": Concise 3-5 sentence clinical overview of the patient's report.
2. "key_findings": Array of strings of important clinical findings.
3. "abnormal_values": Array of objects, each with:
   - "parameter": test or parameter name
   - "value": patient's test value with units
   - "normal_range": reference interval
   - "status": "High", "Low", or "Critical"
4. "recommendations": Array of strings with actionable clinical next steps.
5. "severity": Exactly one of "Normal", "Mild", "Moderate", "Severe", "Critical".
"""

# Clinical reference database for offline analysis
REFERENCE_RANGES = [
    {
        "pattern": r"(?:hemoglobin|hb)\b",
        "name": "Hemoglobin",
        "low": 12.0, "high": 17.5,
        "unit": "g/dL",
        "normal_range": "12.0 - 17.5 g/dL",
        "advice_high": "Polycythemia evaluation recommended.",
        "advice_low": "Evaluation for anemia, iron studies, or nutritional deficiency recommended."
    },
    {
        "pattern": r"(?:total\s+leukocyte\s+count|white\s+blood\s+cells?|wbc)\b",
        "name": "WBC (Total Leukocyte Count)",
        "low": 4000, "high": 11000,
        "unit": "/cumm",
        "normal_range": "4,000 - 11,000 /cumm",
        "advice_high": "Possible active infection or inflammatory state. Clinical correlation advised.",
        "advice_low": "Leukopenia detected. Follow-up CBC advised."
    },
    {
        "pattern": r"(?:platelets?|platelet\s+count)\b",
        "name": "Platelet Count",
        "low": 150.0, "high": 450.0,
        "unit": "x10^3 /uL",
        "normal_range": "150 - 450 x10^3 /uL (1.5 - 4.5 Lakhs)",
        "advice_high": "Thrombocytosis. Consult physician for evaluation.",
        "advice_low": "Thrombocytopenia. Monitor for bleeding signs and recheck."
    },
    {
        "pattern": r"(?:fasting\s+blood\s+(?:sugar|glucose)|glucose\s*[-–]\s*fasting|fbs)\b",
        "name": "Fasting Blood Glucose",
        "low": 70.0, "high": 100.0,
        "unit": "mg/dL",
        "normal_range": "70 - 100 mg/dL",
        "advice_high": "Elevated fasting blood sugar. HbA1c test and dietary consultation recommended.",
        "advice_low": "Hypoglycemia detected. Monitor blood sugar levels closely."
    },
    {
        "pattern": r"(?:post\s+prandial\s+(?:blood\s+)?glucose|ppbs)\b",
        "name": "Post Prandial Glucose",
        "low": 70.0, "high": 140.0,
        "unit": "mg/dL",
        "normal_range": "< 140 mg/dL",
        "advice_high": "Elevated post-meal blood sugar. Consult diabetologist or physician.",
        "advice_low": "Low blood sugar."
    },
    {
        "pattern": r"(?:glycated\s+hemoglobin|hba1c)\b",
        "name": "HbA1c",
        "low": 4.0, "high": 5.7,
        "unit": "%",
        "normal_range": "< 5.7 %",
        "advice_high": "Elevated HbA1c indicates prediabetes or diabetes. Lifestyle modification & physician consult advised.",
        "advice_low": "Normal range."
    },
    {
        "pattern": r"(?:total\s+cholesterol|cholesterol\s*[-–]\s*total)\b",
        "name": "Total Cholesterol",
        "low": 100.0, "high": 200.0,
        "unit": "mg/dL",
        "normal_range": "< 200 mg/dL",
        "advice_high": "Hypercholesterolemia. Dietary modifications and lipid profile monitoring recommended.",
        "advice_low": "Low cholesterol."
    },
    {
        "pattern": r"(?:triglycerides?)\b",
        "name": "Triglycerides",
        "low": 40.0, "high": 150.0,
        "unit": "mg/dL",
        "normal_range": "< 150 mg/dL",
        "advice_high": "Elevated triglycerides. Reduce refined sugars, alcohol, and saturated fats.",
        "advice_low": "Normal range."
    },
    {
        "pattern": r"(?:serum\s+creatinine|creatinine)\b",
        "name": "Serum Creatinine",
        "low": 0.6, "high": 1.2,
        "unit": "mg/dL",
        "normal_range": "0.6 - 1.2 mg/dL",
        "advice_high": "Elevated creatinine indicates potential renal strain. Renal function panel & hydration advised.",
        "advice_low": "Low muscle mass or hyperfiltration."
    },
    {
        "pattern": r"(?:blood\s+urea\s+nitrogen|bun|blood\s+urea)\b",
        "name": "Blood Urea",
        "low": 15.0, "high": 40.0,
        "unit": "mg/dL",
        "normal_range": "15 - 40 mg/dL",
        "advice_high": "Elevated blood urea. Maintain adequate hydration and recheck kidney parameters.",
        "advice_low": "Low urea level."
    },
    {
        "pattern": r"(?:sgpt|alt|alanine\s+aminotransferase)\b",
        "name": "SGPT / ALT",
        "low": 0.0, "high": 50.0,
        "unit": "U/L",
        "normal_range": "< 50 U/L",
        "advice_high": "Elevated liver enzyme (ALT). Avoid hepatotoxic substances and consult physician.",
        "advice_low": "Normal."
    },
    {
        "pattern": r"(?:sgot|ast|aspartate\s+aminotransferase)\b",
        "name": "SGOT / AST",
        "low": 0.0, "high": 40.0,
        "unit": "U/L",
        "normal_range": "< 40 U/L",
        "advice_high": "Elevated liver enzyme (AST). Follow up with complete liver panel.",
        "advice_low": "Normal."
    },
    {
        "pattern": r"(?:thyroid\s+stimulating\s+hormone|tsh)\b",
        "name": "TSH",
        "low": 0.4, "high": 4.5,
        "unit": "uIU/mL",
        "normal_range": "0.4 - 4.5 uIU/mL",
        "advice_high": "Elevated TSH suggests primary hypothyroidism. Endocrinologist consult recommended.",
        "advice_low": "Suppressed TSH suggests hyperthyroidism. Further thyroid evaluation recommended."
    },
    {
        "pattern": r"(?:serum\s+uric\s+acid|uric\s+acid)\b",
        "name": "Uric Acid",
        "low": 3.4, "high": 7.0,
        "unit": "mg/dL",
        "normal_range": "3.4 - 7.0 mg/dL",
        "advice_high": "Hyperuricemia detected. Risk of gout; low-purine diet and hydration advised.",
        "advice_low": "Low uric acid."
    },
    {
        "pattern": r"(?:vitamin\s+d|25\s*[-–]\s*oh\s+vitamin\s+d)\b",
        "name": "Vitamin D (25-OH)",
        "low": 30.0, "high": 100.0,
        "unit": "ng/mL",
        "normal_range": "30 - 100 ng/mL",
        "advice_high": "Elevated Vitamin D.",
        "advice_low": "Vitamin D deficiency/insufficiency. Sunlight exposure and supplementation advised."
    },
    {
        "pattern": r"(?:vitamin\s+b12|cyanocobalamin)\b",
        "name": "Vitamin B12",
        "low": 211.0, "high": 911.0,
        "unit": "pg/mL",
        "normal_range": "211 - 911 pg/mL",
        "advice_high": "Elevated B12 level.",
        "advice_low": "Vitamin B12 deficiency detected. Dietary adjustments or supplementation recommended."
    }
]


class OpenAISummarizerService:
    """Multi-provider AI service with rule-based medical fallback."""

    def __init__(self):
        self.clients = []

        # 1. Azure OpenAI
        azure_ep = Config.AZURE_OPENAI_ENDPOINT
        azure_key = Config.AZURE_OPENAI_KEY
        if azure_ep and azure_key and "your-resource" not in azure_ep:
            try:
                c = AzureOpenAI(
                    azure_endpoint=azure_ep,
                    api_key=azure_key,
                    api_version=Config.AZURE_OPENAI_API_VERSION,
                )
                self.clients.append({
                    "provider": "Azure OpenAI",
                    "client": c,
                    "model": Config.AZURE_OPENAI_DEPLOYMENT,
                })
            except Exception as e:
                print(f"[OpenAI] Azure init error: {e}")

        # 2. Google Gemini API (Free at aistudio.google.com)
        gemini_key = Config.GEMINI_API_KEY
        if gemini_key:
            try:
                c = OpenAI(
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    api_key=gemini_key,
                )
                self.clients.append({
                    "provider": "Google Gemini",
                    "client": c,
                    "model": "gemini-1.5-flash",
                })
            except Exception as e:
                print(f"[OpenAI] Gemini init error: {e}")

        # 3. Groq API (Free at console.groq.com)
        groq_key = Config.GROQ_API_KEY
        if groq_key:
            try:
                c = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_key,
                )
                self.clients.append({
                    "provider": "Groq Llama 3",
                    "client": c,
                    "model": "llama-3.3-70b-versatile",
                })
            except Exception as e:
                print(f"[OpenAI] Groq init error: {e}")

        # 4. Standard OpenAI
        openai_key = Config.OPENAI_API_KEY
        if openai_key and "sk-your" not in openai_key:
            try:
                c = OpenAI(api_key=openai_key)
                self.clients.append({
                    "provider": "OpenAI",
                    "client": c,
                    "model": "gpt-4o-mini",
                })
            except Exception as e:
                print(f"[OpenAI] OpenAI init error: {e}")

        print(f"[OpenAI] Configured AI providers: {[c['provider'] for c in self.clients]}")

    def summarize_report(self, extracted_text: str) -> dict:
        """Summarize text via available AI providers or clinical rule-based engine."""
        # Clean text
        text_sample = extracted_text[:12000] if extracted_text else ""

        # Try active AI providers
        for item in self.clients:
            provider = item["provider"]
            client = item["client"]
            model = item["model"]
            print(f"[OpenAI] Attempting summarization with {provider} ({model})...")

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": MEDICAL_ANALYST_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyze this medical report:\n\n{text_sample}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                content = response.choices[0].message.content
                parsed = json.loads(content)
                print(f"[OpenAI] Successfully analyzed with {provider}!")
                return {
                    "summary": parsed.get("summary", ""),
                    "key_findings": parsed.get("key_findings", []),
                    "abnormal_values": parsed.get("abnormal_values", []),
                    "recommendations": parsed.get("recommendations", []),
                    "severity": parsed.get("severity", "Normal"),
                }
            except Exception as exc:
                print(f"[OpenAI] {provider} failed: {exc}")
                continue

        # If all API providers fail or are unconfigured, run Clinical Lab Engine
        print("[OpenAI] Running Clinical Lab Rule Engine on extracted report...")
        return self._clinical_rule_engine(extracted_text)

    def _clinical_rule_engine(self, text: str) -> dict:
        """Parses extracted text for real lab test results and evaluates them against clinical norms."""
        abnormal_values = []
        key_findings = []
        recommendations = []
        tested_count = 0

        # Scan text for each standard lab reference
        for ref in REFERENCE_RANGES:
            # Match parameter name followed by value within nearby text
            matches = list(re.finditer(ref["pattern"], text, re.IGNORECASE))
            if not matches:
                continue

            for m in matches:
                # Look in the 100 characters following the match
                start_idx = m.end()
                window = text[start_idx:start_idx + 120]

                # Look for numbers (floats or ints, optionally with commas)
                num_match = re.search(r"[:\s\t=]+([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)", window)
                if not num_match:
                    continue

                raw_val = num_match.group(1).replace(",", "")
                try:
                    val = float(raw_val)
                except ValueError:
                    continue

                # Filter out obvious false positives (e.g., date parts, year 2026, tiny 0 for percentages)
                if val in (2024, 2025, 2026, 1.0, 2.0) and "page" in window.lower():
                    continue

                tested_count += 1
                status = None

                if val > ref["high"]:
                    status = "High"
                    if val > ref["high"] * 1.5:
                        status = "Critical"
                    advice = ref["advice_high"]
                elif val < ref["low"]:
                    status = "Low"
                    if val < ref["low"] * 0.6:
                        status = "Critical"
                    advice = ref["advice_low"]

                if status:
                    abnormal_values.append({
                        "parameter": ref["name"],
                        "value": f"{val} {ref['unit']}",
                        "normal_range": ref["normal_range"],
                        "status": status,
                    })
                    key_findings.append(f"{ref['name']} is {status.lower()} at {val} {ref['unit']} (Normal: {ref['normal_range']}).")
                    if advice and advice not in recommendations:
                        recommendations.append(advice)
                else:
                    key_findings.append(f"{ref['name']} is normal at {val} {ref['unit']}.")
                break

        # Calculate severity based on detected abnormalities
        has_critical = any(item["status"] == "Critical" for item in abnormal_values)
        abnormal_count = len(abnormal_values)

        if has_critical:
            severity = "Critical"
        elif abnormal_count >= 3:
            severity = "Moderate"
        elif abnormal_count >= 1:
            severity = "Mild"
        else:
            severity = "Normal"

        if not recommendations:
            recommendations.append("Continue regular wellness checkups and maintain a healthy, balanced lifestyle.")
            recommendations.append("Discuss these results with your healthcare provider for clinical correlation.")
        else:
            recommendations.append("Schedule a follow-up consultation with your attending physician to review these abnormal findings.")

        # Build summary
        if abnormal_count > 0:
            summary = (
                f"Automated clinical evaluation identified {abnormal_count} abnormal parameter(s) out of {tested_count} tested lab markers. "
                f"Key deviations include: {', '.join([a['parameter'] for a in abnormal_values[:3]])}. "
                f"The overall risk severity is assessed as {severity}. Clinical review and follow-up are recommended."
            )
        else:
            summary = (
                f"Automated clinical evaluation analyzed the patient's test parameters. "
                f"All identified routine blood parameters appear within standard acceptable reference intervals. "
                f"Overall clinical status is categorized as Normal. Always correlate laboratory findings with physician guidance."
            )

        return {
            "summary": summary,
            "key_findings": key_findings if key_findings else ["Report scanned successfully. No critical lab deviations detected."],
            "abnormal_values": abnormal_values,
            "recommendations": recommendations,
            "severity": severity,
        }
