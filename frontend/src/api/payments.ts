import { apiRequest } from "./client";

export const PAYMENT_METHODS = ["cash", "card", "check", "bank_transfer", "other"] as const;

export type PaymentMethod = typeof PAYMENT_METHODS[number];

export type Payment = {
    id: number;
    invoice_id: number;
    amount_cents: number;
    payment_date: string;
    method: PaymentMethod;
    note?: string | null;
};

export type PaymentSummary = {
    invoice_id: number;
    invoice_total_cents: number;
    amount_paid_cents: number;
    balance_due_cents: number;
    is_paid: boolean;
};

export type CreatePaymentPayload = {
    amount_cents: number;
    payment_date: string;
    method: PaymentMethod;
    note?: string | null;
};

export function listPayments(invoiceId: number) {
    return apiRequest<Payment[]>(`/invoices/${invoiceId}/payments/`);
}

export function getPaymentSummary(invoiceId: number) {
    return apiRequest<PaymentSummary>(`/invoices/${invoiceId}/payments/summary/`);
}

export function createPayment(invoiceId: number, payload: CreatePaymentPayload) {
    return apiRequest<Payment>(`/invoices/${invoiceId}/payments/`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function deletePayment(id: number) {
    return apiRequest<void>(`/payments/${id}/`, {
        method: "DELETE",
    });
}
