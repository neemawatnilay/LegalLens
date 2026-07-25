import os
import json
import re
from flask import Flask, request, jsonify, render_template_string
from groq import Groq

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>LegalLens</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #2c3e50; }
        .container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        textarea { width: 100%; height: 400px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 13px; }
        button { background: #2c3e50; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; margin-top: 10px; }
        button:hover { background: #34495e; }
        .output { background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd; height: 400px; overflow-y: auto; white-space: pre-wrap; font-family: monospace; font-size: 13px; }
        h3 { color: #2c3e50; margin-top: 20px; }
        .disclaimer { background: #fff3cd; padding: 10px; border-radius: 5px; margin-top: 20px; font-size: 13px; }
        .green { background: #27ae60; }
    </style>
</head>
<body>
    <h1>🏛️ LegalLens</h1>
    <p>AI-Powered Inconsistency Detection for Indian Court Filings</p>
    <div class="container">
        <div>
            <h3>📄 Paste Petition Text</h3>
            <textarea id="petition" placeholder="Paste the full petition text here..."></textarea>
            <button onclick="analyze()">🔍 Analyze Petition</button>
            <button class="green" onclick="loadSample()">💡 Load Sample Petition</button>
        </div>
        <div>
            <h3>📊 Consistency Report</h3>
            <div class="output" id="report">Results will appear here...</div>
        </div>
    </div>
    <h3>🚨 Inconsistency Flags</h3>
    <div class="output" id="flags">Flags will appear here...</div>
    <div class="disclaimer">
        ⚠️ Decision-support tool only. All flags require human legal review.
        Built by Lat Sahab | IISc Deep Generative Models Course Project
    </div>
    <script>
        async function analyze() {
            const petition = document.getElementById("petition").value;
            if (!petition.trim()) { alert("Please enter petition text"); return; }
            document.getElementById("report").innerHTML = "⏳ Analyzing... This may take 30-60 seconds...";
            document.getElementById("flags").innerHTML = "⏳ Please wait...";
            try {
                const response = await fetch("/analyze", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({petition: petition})
                });
                const data = await response.json();
                document.getElementById("report").innerHTML = data.report;
                document.getElementById("flags").innerHTML = data.flags;
            } catch(e) {
                document.getElementById("report").innerHTML = "Error: " + e.message;
            }
        }
        async function loadSample() {
            const response = await fetch("/sample");
            const data = await response.json();
            document.getElementById("petition").value = data.text;
        }
    </script>
</body>
</html>
'''

def extract_claims(petition_text):
    prompt = """
You are a legal analyst. Extract every factual claim from this 
court petition. For each claim return a JSON object with:
- claim_id: integer
- paragraph: paragraph number
- claim_text: the claim
- claim_type: one of [DATE_FACT, FINANCIAL_FACT, LOCATION_FACT,
                      MEDICAL_FACT, BEHAVIORAL_FACT, 
                      EXHIBIT_REFERENCE, PERSON_FACT, LEGAL_FACT]
- entities: list of people, places, dates, amounts
- date_mentioned: date in YYYY-MM-DD format or null
- amount_mentioned: amount in INR as number or null
- exhibit_referenced: exhibit name or null

Return ONLY a raw JSON array. No markdown. No explanation.

Petition:
""" + petition_text

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'```json|```', '', raw).strip()
    return json.loads(raw)


def detect_inconsistencies(claims, petition_text):
    prompt = """
You are a Supreme Court level forensic legal analyst with 30 years 
of experience detecting fraud in Indian matrimonial and civil petitions.

Check for:
1. CONTRADICTION - claims directly contradicting each other
2. TIMELINE_VIOLATION - impossible or inconsistent dates
3. UNSUPPORTED_CLAIM - allegation without evidence
4. FINANCIAL_INCONSISTENCY - conflicting money amounts
5. EXHIBIT_MISMATCH - exhibit description conflicts with claim
6. DOCUMENT_AUTHENTICITY - suspicious document details
7. WITNESS_INCONSISTENCY - conflicting witness statements

For each inconsistency:
- inconsistency_id: integer
- type: from the 7 types above
- severity: HIGH, MEDIUM, or LOW
- claim_ids_involved: list
- description: detailed explanation
- paragraph_refs: paragraph numbers
- suspicious_text: exact conflicting text
- confidence_score: 0.0 to 1.0
- forensic_note: why this is suspicious

Return ONLY raw JSON array. No markdown. No explanation.

CLAIMS:
""" + json.dumps(claims, indent=2) + """

PETITION:
""" + petition_text

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a forensic legal analyst specializing in Indian court petition fraud detection."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=6000
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'```json|```', '', raw).strip()
    return json.loads(raw)


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/sample")
def sample():
    try:
        with open("sample_data/sample_petition.txt", "r") as f:
            text = f.read()
        return jsonify({"text": text})
    except:
        return jsonify({"text": "Sample file not found"})


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        petition_text = data.get("petition", "")
        claims = extract_claims(petition_text)
        inconsistencies = detect_inconsistencies(claims, petition_text)

        severity_weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        weighted = sum(severity_weights.get(i["severity"], 1) for i in inconsistencies)
        score = round(max(0, 100 - (weighted / (len(claims) * 3) * 100)), 1)
        risk = "🟢 LOW RISK" if score >= 80 else "🟡 MEDIUM RISK" if score >= 60 else "🔴 HIGH RISK"

        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for i in inconsistencies:
            counts[i["severity"]] += 1

        report = f"""╔══════════════════════════════════════════╗
║     🏛️  LEGALLENS CONSISTENCY REPORT     ║
╚══════════════════════════════════════════╝

📊 OVERVIEW
──────────────────────────────────────────
Total Claims Extracted    : {len(claims)}
Inconsistencies Found     : {len(inconsistencies)}
Consistency Score         : {score}/100
Risk Level                : {risk}

📊 BY SEVERITY
──────────────────────────────────────────
🔴 HIGH   : {counts["HIGH"]}
🟡 MEDIUM : {counts["MEDIUM"]}
🟢 LOW    : {counts["LOW"]}

⚠️  DISCLAIMER
──────────────────────────────────────────
Decision-support tool only.
All flags require human legal review."""

        flags = "🚨 INCONSISTENCY FLAGS\n" + "─" * 50 + "\n"
        for inc in sorted(inconsistencies, key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x["severity"],3)):
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(inc["severity"], "⚪")
            flags += f"""
{emoji} FLAG #{inc["inconsistency_id"]} | {inc["type"]}
Confidence  : {int(inc["confidence_score"]*100)}%
Paragraphs  : {inc["paragraph_refs"]}
Issue       : {inc["description"]}
Forensic    : {inc.get("forensic_note", "N/A")}
Evidence    : {inc["suspicious_text"][:120]}...
""" + "─" * 50 + "\n"

        return jsonify({"report": report, "flags": flags})

    except Exception as e:
        return jsonify({"report": f"Error: {str(e)}", "flags": ""})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)
