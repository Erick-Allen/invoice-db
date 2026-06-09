export async function askAssistant(message: string) {
  const response = await fetch("http://localhost:8000/api/assistant/query/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error("Assistant request failed");
  }

  return response.json();
}