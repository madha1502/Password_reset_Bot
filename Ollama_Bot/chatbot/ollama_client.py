import os
import requests
from typing import List, Dict

OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


class OllamaClient:
    """Thin wrapper around the Ollama REST API."""

    def __init__(self, base_url: str = OLLAMA_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model    = model
        self.available = self._ping()

    def _ping(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def is_available(self) -> bool:
        self.available = self._ping()
        return self.available

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat request and return the assistant reply string."""
        if not self.available:
            raise ConnectionError("Ollama is not reachable.")
        try:
            r = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=60,
            )
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "").strip()
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama took too long to respond.")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")
