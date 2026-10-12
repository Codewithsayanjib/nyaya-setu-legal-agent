# Nyaya-Setu (न्याय-सेतु) ⚖️
### Explainable Statute Prediction & FIR Legal Triage Agent powered by Sarvam AI

Nyaya-Setu is an agentic legal triage and explainable statute prediction system designed for Indian criminal jurisprudence. It helps common citizens, victims, and legal aid clinics convert oral or written incident accounts in Indian languages into structured, legally validated **Bharatiya Nyaya Sanhita (BNS) 2023** charges with dual **Indian Penal Code (IPC) 1860** concordance.

---

## 🌟 Why Sarvam AI Powers This Project

This project leverages the full spectrum of **Sarvam AI APIs**:
1. **Speech-to-Text (`saaras:v1`)**: Handles colloquial oral depositions in regional Indian languages (Hindi, Tamil, Kannada, Marathi, etc.).
2. **Translation & Standardization (`mayura:v1`)**: Normalizes vernacular dialect into formal legal facts while preserving the original cultural nuances.
3. **Reasoning & Statute Matching (`sarvam-105b`)**: Performs granular statutory ingredient verification rather than black-box guesses.
4. **Text-to-Speech (`bulbul:v1`)**: Synthesizes natural spoken voice feedback explaining rights and legal steps back to non-literate complainants in their mother tongue.

---

## 🚀 Key Features

* **Strict Ingredient-Level Explainability**:
  - Instead of simply predicting "Robbery - 90%", it checks constituent statutory ingredients (e.g., *Movable Property*, *Absence of Consent*, *Imminent Fear of Death*).
  - Explicitly documents **why** adjacent offences (like Dacoity) were excluded (e.g., $< 5$ perpetrators).
* **Dual BNS 2023 & IPC 1860 Mapping**:
  - Facilitates the ongoing national transition by providing police and advocates with both modern BNS sections and classic IPC references.
* **Procedural Attributes**:
  - Flags whether an offence is **Cognizable / Non-Cognizable**, **Bailable / Non-Bailable**, and **Compoundable**, along with maximum statutory penalties.
* **Built-in Mock Evaluation Mode**:
  - Allows zero-friction presentation during the workshop even if API credits or internet conditions fluctuate.

---

## 📂 Project Structure

```
├── app.py                  # Streamlit Interactive Web Application
├── requirements.txt        # Python Dependencies
├── .env.example            # Environment Key Template
├── README.md               # Documentation & Setup Guide
├── data/
│   └── statutes.json       # Curated BNS & IPC Knowledge Base with Statutory Ingredients
└── src/
    ├── __init__.py
    ├── sarvam_client.py    # Wrapper for Sarvam ASR, Translation, LLM, and TTS APIs
    ├── statute_db.py       # Knowledge retrieval & grounding catalog
    └── legal_agent.py      # Core agent orchestrating fact extraction & explainability
```

---

## 🛠️ Quickstart

### 1. Clone & Setup Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Sarvam API Key
Create a `.env` file or export the environment variable:
```bash
cp .env.example .env
# Edit .env and enter your key:
# SARVAM_API_KEY=your_actual_key
```
*(Alternatively, enter your key directly in the web UI sidebar).*

### 3. Run the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.
