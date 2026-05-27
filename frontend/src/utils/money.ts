export function dollarsToCents(value: string): number {
  const trimmed = value.trim();

  if (!/^\d+(\.\d{1,2})?$/.test(trimmed)) {
    throw new Error("Enter a valid dollar amount.");
  }

  const [dollars, cents = ""] = trimmed.split(".");
  const paddedCents = cents.padEnd(2, "0");

  return Number(`${dollars}${paddedCents}`);
}

export function centsToDollars(cents: number): string {
  return (cents / 100).toFixed(2);
}