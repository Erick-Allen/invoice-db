import { apiRequest } from "./client";

type AssistantInvoice = {
  id: number;
  invoice_number?: number | null;
  customer_name?: string;
  status: string;
  total: number;
  date_issued?: string;
  date_due?: string;
};

type AssistantResponse = {
  message: string;
  intent: string;
  data: AssistantInvoice[] | { count: number; status: string } | null;
};

type AssistantQueryResponse = {
  message: string;
  assistant_intent: unknown;
  assistant_response: AssistantResponse;
};

export async function askAssistant(message: string) {
  return apiRequest<AssistantQueryResponse>("/assistant/query/", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
