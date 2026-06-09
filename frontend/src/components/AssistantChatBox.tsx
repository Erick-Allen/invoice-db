import { useState } from "react";
import { askAssistant } from "../api/assistant";

type AssistantInvoice = {
  id: number;
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

const suggestedPrompts = [
  "Show overdue invoices",
  "How many paid invoices?",
  "Find invoices under $500",
  "Show draft invoices",
  "What can this app do?",
];

function formatMoney(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function formatDate(date?: string) {
  return date || "—";
}

export function AssistantChatBox() {
  const [input, setInput] = useState("");
  const [lastQuestion, setLastQuestion] = useState("");
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function submitMessage(message: string) {
    const trimmedMessage = message.trim();
    if (!trimmedMessage) return;

    setIsLoading(true);
    setError("");
    setLastQuestion(trimmedMessage);
    setResponse(null);

    try {
      const data = await askAssistant(trimmedMessage);
      setResponse(data.assistant_response);
      setInput("");
    } catch {
      setError("Assistant request failed.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await submitMessage(input);
  }

  return (
    <section className="assistant-box">
      <h2>Invoice Assistant</h2>

      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about invoices..."
          disabled={isLoading}
        />

        <button type="submit" disabled={isLoading}>
          {isLoading ? "Asking..." : "Ask"}
        </button>
      </form>

      <div className="assistant-suggestions">
        {suggestedPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={isLoading}
            onClick={() => submitMessage(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>

      <div className="assistant-conversation">
        {lastQuestion && (
          <div className="assistant-message user-message">
            <span className="assistant-label">You</span>
            <p>{lastQuestion}</p>
          </div>
        )}

        {error && <p className="error">{error}</p>}

        {isLoading && (
          <div className="assistant-message assistant-message-card">
            <span className="assistant-label">Invoice Assistant</span>
            <p>Checking your invoice data...</p>
          </div>
        )}

        {response && (
          <div className="assistant-message assistant-message-card">
            <span className="assistant-label">Invoice Assistant</span>
            <p>{response.message}</p>

            {Array.isArray(response.data) && response.data.length > 0 && (
              <div className="table-wrapper">
                <table className="data-table assistant-data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Customer</th>
                      <th>Status</th>
                      <th>Total</th>
                      <th>Due Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {response.data.map((invoice) => (
                      <tr key={invoice.id}>
                        <td>#{invoice.id}</td>
                        <td>{invoice.customer_name || "—"}</td>
                        <td>
                          <span className="status-badge">{invoice.status}</span>
                        </td>
                        <td>{formatMoney(invoice.total)}</td>
                        <td>{formatDate(invoice.date_due)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {response.data &&
              !Array.isArray(response.data) &&
              "count" in response.data && (
                <p>
                  {response.data.status}: {response.data.count}
                </p>
              )}
          </div>
        )}
      </div>
    </section>
  );
}