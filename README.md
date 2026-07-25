# LegalLens
AI-Powered Inconsistency Detection for Indian Court Filings
LegalLens 🏛️

**AI-powered inconsistency detection for Indian court filings**

Indian courts handle millions of civil cases every year. A significant 
chunk of these — especially matrimonial disputes and property matters — 
contain fabricated narratives, contradictory timelines, and documents 
that don't quite add up. The problem is that spotting these 
inconsistencies manually takes a trained legal eye, time, and patience 
that most overworked judges and junior advocates simply don't have.

LegalLens reads a court petition, pulls out every factual claim, and 
cross-checks them against each other to surface contradictions, timeline 
violations, financial mismatches, and suspicious exhibit references — 
automatically.

This is not a judgment tool. It flags. Humans decide.

---

## What it does

- Extracts structured factual claims from petition text
- Detects internal contradictions across paragraphs
- Flags timeline violations using date arithmetic
- Identifies financial inconsistencies across claims
- Scores exhibit-to-claim relevance
- Generates a ranked consistency report with confidence scores

---

## Why this matters

A petition saying the petitioner suffered injuries on her *left arm* 
while the annexed medical report documents contusions on the *right arm* 
— that is the kind of thing that slips through. A complaint number 
suggesting 45 police complaints were filed in the first five days of 
January at a residential area station — that deserves a second look.

These are not obvious errors. They are the kind that a fatigued reader 
misses on page 7 of a 20-page filing. LegalLens catches them.

---

## Tech Stack

- **LLM backbone:** Llama 3.3 70B via Groq API
- **UI:** Gradio
- **Claim extraction:** Structured JSON prompting with type classification
- **Inconsistency detection:** Multi-pass forensic prompting with 
  domain-specific legal and procedural knowledge
- **Deployment:** Hugging Face Spaces

---

## Scope

Currently supports:
- Matrimonial petitions (Hindu Marriage Act)
- Property and land dispute filings
- English language petitions (Hindi support planned)

Out of scope for now:
- Criminal matters
- Politically sensitive filings

---

## How to run locally

```bash
git clone https://github.com/neemawatnilay/LegalLens.git
cd LegalLens
pip install -r requirements.txt
```

Create a `.env` file:
GROQ_API_KEY=your_key_here

Run:
```bash
python app.py
```

---

## Project Structure
LegalLens/
├── LegalLens.ipynb # Development notebook
├── app.py # Gradio application
├── requirements.txt # Dependencies
├── sample_data/
│ └── sample_petition.txt # Sample petition for testing
└── docs/
└── architecture.md # System design notes

---

## Limitations

- LLM outputs are probabilistic — confidence scores matter
- Domain-specific knowledge depends on model training data
- Not a substitute for legal counsel
- Works best on well-structured English petitions

---

## Course Context

Built as a demo project for the **Gen AI** course at 
**Indian Institute of Science (IISc)**, taught by Prof. Prathosh.

The generative modeling connection: claim-evidence alignment uses 
learned semantic representations — conceptually similar to the encoder 
in a VAE — to score how well an exhibit supports the claim it is 
attached to. Anomaly detection over legal narrative structure mirrors 
the latent variable model framework studied in the course.

---

## Author

**Lat Sahab**  
MTech CSE, IIT Guwahati (2015)  
github.com/neemawatnilay

---

*LegalLens is a research demo. Output should not be used as legal 
evidence or advice. All flags require review by a qualified legal 
professional.*
"""
