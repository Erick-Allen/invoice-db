export type InvoiceNumberSource = {
    id: number;
    invoice_number?: number | null;
};

export function formatInvoiceNumber(invoice: InvoiceNumberSource) {
    return `#${invoice.invoice_number ?? invoice.id}`;
}
