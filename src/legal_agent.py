import json
import re
from typing import Dict, Any, List, Optional
from src.sarvam_client import SarvamClient
from src.statute_db import StatuteDatabase

class LegalAgent:
    """
    Explainable Statute Prediction & FIR Legal Triage Agent.
    Orchestrates:
    1. Speech/Text intake
    2. Dialect translation / normalization
    3. Structured Fact Extraction
    4. Ingredient-level Statute Matching (BNS + IPC)
    5. Counterfactual & Plain-language Explanation
    6. Audio readout generation
    """

    def __init__(self, sarvam_client: SarvamClient, statute_db: Optional[StatuteDatabase] = None):
        self.client = sarvam_client
        self.db = statute_db or StatuteDatabase()

    def transcribe_audio(self, audio_path: str, language_code: str = "unknown") -> str:
        """Transcribes incoming citizen audio."""
        res = self.client.speech_to_text(audio_path, language_code)
        return res.get("transcript", "")

    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Standardizes regional text into formal English for consistent legal reasoning."""
        if source_lang.startswith("en"):
            return text
        res = self.client.translate(text, source_language_code=source_lang, target_language_code="en-IN")
        return res.get("translated_text", text)

    def translate_to_indic(self, text: str, target_lang: str) -> str:
        """Translates legal advisory back to complainant's mother tongue."""
        if target_lang.startswith("en"):
            return text
        res = self.client.translate(text, source_language_code="en-IN", target_language_code=target_lang)
        return res.get("translated_text", text)

    def analyze_incident(self, incident_text_english: str, original_incident_text: str, user_lang: str = "hi-IN") -> Dict[str, Any]:
        """
        Extracts facts, predicts statutes with strict ingredient explainability,
        and outputs a structured audit report.
        """
        statute_catalog = self.db.get_catalog_summary()

        system_prompt = f"""You are an elite Indian Criminal Law Expert specializing in the Bharatiya Nyaya Sanhita (BNS) 2023 and IPC.
Perform an EXPLAINABLE STATUTE PREDICTION for the incident.
Ground your prediction strictly on whether facts satisfy statutory ingredients from the catalog.

RELEVANT BNS SECTIONS CATALOG:
{statute_catalog}

Return a single JSON object with this exact structure:
{{
  "incident_summary": "Concise summary of facts",
  "extracted_facts": {{
    "accused_count": "number of accused",
    "weapons_used": ["weapons or None"],
    "property_involved": "property/cash involved or None",
    "violence_or_threat": "nature of force or fear",
    "location_type": "type of premises",
    "intent_mens_rea": "nature of criminal intent"
  }},
  "predicted_charges": [
    {{
      "bns_section": "e.g. 309(4)",
      "ipc_equivalent": "e.g. 392/397",
      "offence_title": "Robbery using deadly weapon",
      "confidence": "High",
      "ingredients_evaluation": [
        {{
          "ingredient": "Name of statutory ingredient",
          "status": "Satisfied",
          "supporting_fact": "Fact from complaint that proves this"
        }}
      ],
      "procedural_nature": {{
        "cognizable": true,
        "bailable": false,
        "compoundable": "No",
        "max_punishment": "Up to 10-14 years rigorous imprisonment"
      }},
      "reasoning": "Why this charge applies over lesser offenses"
    }}
  ],
  "excluded_or_borderline_charges": [
    {{
      "bns_section": "e.g. 310",
      "offence_title": "Dacoity",
      "reason_excluded": "Why this adjacent offence does not apply"
    }}
  ],
  "complainant_rights_summary": "Advice on FIR filing, victim rights, and police procedure under BNSS."
}}
"""

        user_prompt = f"Analyze this incident statement and return valid JSON:\n\n{incident_text_english}"

        # Request completion from LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        raw_response = self.client.chat_completion(messages, temperature=0.1)

        # Parse JSON
        parsed = self._extract_json(raw_response)

        # Optional: Generate Indic legal advisory text for vernacular readout
        rights_english = parsed.get("complainant_rights_summary", "")
        if rights_english and user_lang and not user_lang.startswith("en"):
            try:
                parsed["complainant_rights_summary_indic"] = self.translate_to_indic(rights_english, user_lang)
            except Exception:
                parsed["complainant_rights_summary_indic"] = rights_english
        else:
            parsed["complainant_rights_summary_indic"] = rights_english

        return parsed

    def generate_audio_advisory(self, text_to_speak: str, target_lang: str = "hi-IN") -> Optional[str]:
        """
        Uses Sarvam TTS to create audio feedback in Indic language.
        Returns base64 encoded audio string if available.
        """
        try:
            res = self.client.text_to_speech(text_to_speak, target_language_code=target_lang)
            audios = res.get("audios", [])
            if audios:
                return audios[0]
        except Exception:
            return None
        return None

    def _extract_json(self, raw_str: str) -> Dict[str, Any]:
        """Safely parses JSON from LLM output, extracting code fences if present."""
        cleaned = raw_str.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback heuristic cleanup
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                return json.loads(cleaned[start:end+1])
            raise ValueError(f"Could not parse valid JSON from response: {raw_str[:300]}...")
