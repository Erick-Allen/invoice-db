import requests

class QwenUnavailableError(Exception):
    ...

class QwenClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen3:0.6b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=5
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise QwenUnavailableError("Qwen fallback is unavailable.") from exc
        
        data = response.json()
        return data.get("response", "")