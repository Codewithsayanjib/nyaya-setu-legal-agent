import json
import os
from typing import List, Dict, Any, Optional

class StatuteDatabase:
    """
    In-memory knowledge store for BNS statutes with ingredient requirements and IPC mapping.
    """
    def __init__(self, json_path: Optional[str] = None):
        if not json_path:
            json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "statutes.json")
        self.json_path = json_path
        self.statutes = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("sections", [])

    def get_all(self) -> List[Dict[str, Any]]:
        return self.statutes

    def find_by_bns(self, section: str) -> Optional[Dict[str, Any]]:
        section = section.strip()
        for s in self.statutes:
            if s["bns_section"] == section:
                return s
        # Fall back to the base section number, e.g. "303" -> "303(2)"
        for s in self.statutes:
            if s["bns_section"].split("(")[0] == section.split("(")[0]:
                return s
        return None

    def get_catalog_summary(self) -> str:
        """
        Returns a concise markdown representation of statutes and their statutory ingredients
        to be injected directly into LLM prompts for deterministic grounding.
        """
        lines = []
        for s in self.statutes:
            lines.append(f"### Section BNS {s['bns_section']} (Equivalent IPC {s['ipc_equivalent']}): {s['offence_title']}")
            lines.append(f"- **Description**: {s['description']}")
            lines.append(f"- **Procedural**: Cognizable: {s['cognizable']} | Bailable: {s['bailable']} | Compoundable: {s['compoundable']}")
            lines.append("- **Statutory Ingredients Required**:")
            for ing in s['ingredients']:
                lines.append(f"  * {ing}")
            lines.append("")
        return "\n".join(lines)
