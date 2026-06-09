# invoice_db/assistant/qwen_router.py

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from invoice_db.assistant.schemas import AssistantIntent, unknown_intent


DEFAULT_QWEN_MODEL = "qwen3.5:2b"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


SYSTEM_PROMPT = """
You are a structured fallback router for an invoice assistant.

Your only job is to convert the user's message into valid JSON matching the provided schema.

Supported intents:
- invoices_by_status
- list_overdue_invoices
- list_invoices_by_customer
- list_invoices_by_total_range
- unknown

Rules:
- Use invoices_by_status only for invoice status requests involving draft, sent, paid, or void.
- Use result_type "count" when the user asks how many, count, number of, or total number.
- Use result_type "list" otherwise.
- Use list_overdue_invoices for overdue, late, past due, missed due date, or expired due date invoice requests.
- Use list_invoices_by_customer when the user asks for invoices for a customer.
- Use list_invoices_by_total_range when the user asks for invoices over, under, above, below, between, or from/to a money amount.
- Use unknown when the request is outside the supported invoice assistant actions.

Valid statuses:
- draft
- sent
- paid
- void

Money values must be integer cents:
- $500 -> 50000
- $100.25 -> 10025

Return only JSON.
Do not include markdown.
Do not include explanations.
Do not answer general questions.
"""


class QwenRouterUnavailableError(Exception):
    pass


class QwenIntentRouter:
    def __init__(self, model: str | None = None, url: str = OLLAMA_CHAT_URL):
        self.model = model or os.getenv("INVOICEDB_QWEN_MODEL", DEFAULT_QWEN_MODEL)
        self.url = url

    def route(self, message: str) -> AssistantIntent:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            "format": AssistantIntent.model_json_schema(),
            "options": {
                "temperature": 0,
            },
            "think": False,
            "stream": False,
        }

        request = Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            content = response_data["message"]["content"]

            return AssistantIntent.model_validate_json(content)

        except (HTTPError, URLError, TimeoutError) as exc:
            raise QwenRouterUnavailableError(
                "Qwen/Ollama fallback is unavailable. Make sure Ollama is running and the model is pulled."
            ) from exc

        except (KeyError, TypeError, json.JSONDecodeError, ValidationError, ValueError):
            return unknown_intent(confidence=0.0)