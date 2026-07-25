import os
import json
import re
import gradio as gr
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
            {
                "role": "system",
                "content": "You are a forensic legal analyst specializing in Indian court petition fraud detection."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=6000
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'```json|```', '', raw).strip()
    return json.loads(raw)


def analyze_petition(petition_text):
    if not petition_text.strip():
        return "Please enter petition text.", "", ""
    try:
        claims = extract_claims(petition_text)
        inconsistencies = detect_inconsistencies(claims, petition_text)

        severity_weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        weighted = sum(
            severity_weights.get(i["severity"], 1)
            for i in inconsistencies
        )
        score = round(
            max(0, 100 - (weighted / (len(claims) * 3) * 100)), 1
        )
        risk = "🟢 LOW RISK" if score >= 80 else "🟡 MEDIUM RISK" if score >= 60 else "🔴 HIGH RISK"

        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for i in inconsistencies:
            counts[i["severity"]] += 1

        summary = f"""
╔══════════════════════════════════════════╗
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
All flags require human legal review.
        """

        flags = "🚨 INCONSISTENCY FLAGS\n" + "─" * 50 + "\n"
        for inc in sorted(
            inconsistencies,
            key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x["severity"],3)
        ):
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
                inc["severity"], "⚪"
            )
            flags += f"""
{emoji} FLAG #{inc["inconsistency_id"]} | {inc["type"]}
Confidence  : {int(inc["confidence_score"]*100)}%
Paragraphs  : {inc["paragraph_refs"]}
Issue       : {inc["description"]}
Forensic    : {inc.get("forensic_note", "N/A")}
Evidence    : {inc["suspicious_text"][:120]}...
""" + "─" * 50 + "\n"

        claims_out = "📋 EXTRACTED CLAIMS\n" + "─" * 50 + "\n"
        for c in claims:
            claims_out += f"""#{c["claim_id"]} [{c["claim_type"]}]
{c["claim_text"]}
Date: {c["date_mentioned"]} | Amount: {c["amount_mentioned"]}

"""
        return summary, flags, claims_out

    except Exception as e:
        return f"Error: {str(e)}", "", ""


with open("sample_data/sample_petition.txt", "r") as f:
    sample_text = f.read()

with gr.Blocks(title="LegalLens", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 🏛️ LegalLens
    ### AI-Powered Inconsistency Detection for Court Filings
    *A forensic decision-support tool — not a substitute for legal advice*
    """)

    with gr.Row():
        with gr.Column(scale=1):
            petition_input = gr.Textbox(
                label="📄 Petition Text",
                placeholder="Paste petition text here...",
                lines=20
            )
            analyze_btn = gr.Button(
                "🔍 Analyze Petition",
                variant="primary",
                size="lg"
            )
            gr.Markdown("""
            **Supported filings:**
            - Matrimonial petitions
            - Property dispute applications
            - Civil court filings (English)
            """)

        with gr.Column(scale=1):
            summary_out = gr.Textbox(
                label="📊 Consistency Report",
                lines=15,
                interactive=False
            )
            flags_out = gr.Textbox(
                label="🚨 Inconsistency Flags",
                lines=20,
                interactive=False
            )
            claims_out = gr.Textbox(
                label="📋 Extracted Claims",
                lines=15,
                interactive=False
            )

    sample_btn = gr.Button("💡 Load Sample Petition")
    sample_btn.click(fn=lambda: sample_text, outputs=petition_input)
    analyze_btn.click(
        fn=analyze_petition,
        inputs=petition_input,
        outputs=[summary_out, flags_out, claims_out]
    )

    gr.Markdown("""
    ---
    Built by **Lat Sahab** | IISc Deep Generative Models Course Project
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
