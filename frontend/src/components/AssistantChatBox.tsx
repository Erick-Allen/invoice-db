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


export function AssistantChatBox() {
  const [input, setInput] = useState("");
  const [lastQuestion, setLastQuestion] = useState("");
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const message = input.trim();
    if (!message) return;

    setIsLoading(true);
    setError("");
    setLastQuestion(message);
    setResponse(null);

    try {
      const data = await askAssistant(message);
      setResponse(data.assistant_response);
      setInput("");
    } catch {
      setError("Assistant request failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="assistant-box">
      <h2>Invoice Assistant</h2>

      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about invoices..."
        />

        <button type="submit" disabled={isLoading}>
          {isLoading ? "Asking..." : "Ask"}
        </button>
      </form>

      {lastQuestion && (
        <p>
          <strong>Query:</strong> {lastQuestion}
        </p>
      )}

      {error && <p className="error">{error}</p>}

      {response && (
        <div className="assistant-result">
          <p>
            <strong>Assistant:</strong> {response.message}
          </p>

          {Array.isArray(response.data) && response.data.length > 0 && (
            <ul>
              {response.data.map((invoice) => (
                <li key={invoice.id}>
                  Invoice #{invoice.id} — {invoice.status} — $
                  {(invoice.total / 100).toFixed(2)}
                </li>
              ))}
            </ul>
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
    </section>
  );
}