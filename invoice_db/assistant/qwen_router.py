import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from invoice_db.assistant.parameter_extractor import build_assistant_intent

from pydantic import ValidationError

from invoice_db.assistant.schemas import AssistantIntent, unknown_intent


DEFAULT_QWEN_MODEL = "qwen3:0.6b"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


SYSTEM_PROMPT = """
You are a structured assistant and router for an invoice application.

Your only job is to convert the user's message into a valid JSON object matching the rules below.

Supported intents:
- invoices_by_status
- list_overdue_invoices
- list_invoices_by_customer
- list_invoices_by_total_range
- unknown

JSON Schema Requirements:
Your response must always include: intent, confidence, parameters, message
- For supported invoice intents, "message" must be null.
- For the "unknown" intent, "message" must be a string containing your direct response to the user.

Rules for "unknown" and Guardrails:
- Use "unknown" when the request is outside supported invoice actions, unclear, or conversational.
- If the user asks what the app does or how to use it, explain that InvoiceDB helps manage customers, invoices, statuses, overdue invoices, customer lookup, and total range searches.
- If the user asks something unrelated to invoices, do not answer it directly. Politely redirect them back to invoice-related actions.
- For unknown, write a short helpful response in the "message" key.
- NEVER invent invoice data, counts, totals, customers, dates, or statuses.

Invoice Intent Rules:
- Use invoices_by_status only for invoice status requests involving draft, sent, paid, or void.
- Use result_type "count" when the user asks how many, count, number of, or total number.
- Use result_type "list" otherwise.
- Use list_overdue_invoices for overdue, late, past due, missed due date, or expired due date invoice requests.
- Use list_invoices_by_customer when the user asks for invoices for a customer.
- Use list_invoices_by_total_range when the user asks for invoices over, under, above, below, between, or from/to a money amount. Do not use unless a money amount is mentioned.
- Treat settled, completed, closed out, cleared, and already paid as paid invoice status requests.

Valid statuses:
- draft, sent, paid, void

Money values must be integer cents:
- $500 -> 50000
- $100.25 -> 10025

Money values must be integer cents:
- $500 -> 50000
- $100.25 -> 10025

Examples:
User: find invoices under $500
Response:
{
  "intent": "list_invoices_by_total_range",
  "confidence": 0.95,
  "parameters": {
    "result_type": "list",
    "max_total_cents": 50000
  },
  "message": null
}

User: show invoices over $1000
Response:
{
  "intent": "list_invoices_by_total_range",
  "confidence": 0.95,
  "parameters": {
    "result_type": "list",
    "min_total_cents": 100000
  },
  "message": null
}

User: find invoices between $200 and $800
Response:
{
  "intent": "list_invoices_by_total_range",
  "confidence": 0.95,
  "parameters": {
    "result_type": "list",
    "min_total_cents": 20000,
    "max_total_cents": 80000
  },
  "message": null
}

Return only JSON. Do not include markdown formatting like ```json. Do not include explanations."""


class QwenRouterUnavailableError(Exception):
    ...


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
            with urlopen(request, timeout=8) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            raw_content = response_data["message"]["content"]

            # print("QWEN RAW CONTENT:")
            # print(raw_content)

            raw_intent = json.loads(raw_content)

            if raw_intent.get("intent") == "unknown":
                raw_intent["parameters"] = {}

            return AssistantIntent.model_validate(raw_intent)

        except (HTTPError, URLError, TimeoutError) as exc:
            raise QwenRouterUnavailableError(
                "Qwen/Ollama fallback is unavailable. Make sure Ollama is running and the model is pulled."
            ) from exc

        except (KeyError, TypeError, json.JSONDecodeError, ValidationError, ValueError) as exc:
            # print("QWEN PARSE/VALIDATION FAILED:")
            # print(exc)
            return unknown_intent(confidence=0.0)