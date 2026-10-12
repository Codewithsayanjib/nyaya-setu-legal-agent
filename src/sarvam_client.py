import os
import json
import base64
import requests
from typing import Optional, Dict, Any, List

class SarvamClient:
    """
    Client wrapper for Sarvam AI APIs:
    - Speech-to-Text (saaras)
    - Translation (mayura)
    - Text-to-Speech (bulbul)
    - LLM Chat Completions (sarvam-105b)
    """

    BASE_URL = "https://api.sarvam.ai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "")
        if not self.api_key:
            # Note: During testing or initial run, allow user to set key in UI
            pass

    def _headers(self) -> Dict[str, str]:
        return {
            "api-subscription-key": self.api_key
        }

    def speech_to_text(self, audio_file_path: str, language_code: str = "unknown") -> Dict[str, Any]:
        """
        Transcribes audio using Sarvam ASR API.
        language_code: e.g., 'hi-IN', 'ta-IN', 'te-IN', 'kn-IN', 'mr-IN', 'bn-IN', 'unknown'
        """
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY is not set.")

        url = f"{self.BASE_URL}/speech-to-text"
        headers = self._headers()
        data = {
            "model": "saaras:v3"
        }
        if language_code and language_code != "unknown":
            data["language_code"] = language_code

        with open(audio_file_path, "rb") as f:
            files = {"file": (os.path.basename(audio_file_path), f, "audio/wav")}
            response = requests.post(url, headers=headers, data=data, files=files, timeout=60)

        response.raise_for_status()
        return response.json()

    def translate(self, input_text: str, source_language_code: str, target_language_code: str = "en-IN") -> Dict[str, Any]:
        """
        Translates text across Indic languages and English using Sarvam Mayura translation API.
        """
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY is not set.")

        url = f"{self.BASE_URL}/translate"
        headers = {
            **self._headers(),
            "Content-Type": "application/json"
        }
        payload = {
            "input": input_text,
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
            "speaker_gender": "Male",
            "mode": "formal",
            "model": "mayura:v1"
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def text_to_speech(self, text: str, target_language_code: str = "hi-IN", speaker: str = "priya") -> Dict[str, Any]:
        """
        Synthesizes Indic speech from text using Sarvam Bulbul TTS API (bulbul:v3).
        """
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY is not set.")

        url = f"{self.BASE_URL}/text-to-speech"
        headers = {
            **self._headers(),
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": [text[:500]],
            "target_language_code": target_language_code,
            "speaker": speaker,
            "model": "bulbul:v3"
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 4096) -> str:
        """
        Calls Sarvam's v1 chat completions endpoint with sarvam-105b.
        """
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY is not set.")

        url = f"{self.BASE_URL}/v1/chat/completions"
        headers = {
            **self._headers(),
            "Content-Type": "application/json"
        }
        payload = {
            "model": "sarvam-105b-conversations",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        res_json = response.json()
        return res_json["choices"][0]["message"]["content"]

