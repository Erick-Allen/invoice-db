import { useEffect, useState, type SubmitEventHandler } from "react";
import { listCustomers, type Customer } from "../api/customers";
import { createInvoice, listInvoices, updateInvoiceStatus, type Invoice, type InvoiceStatus } from "../api/invoices";

const STATUSES: InvoiceStatus[] = ["draft", "sent", "paid", "void"];

export function InvoicesPage() {
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [invoices, setInvoices] = useState<Invoice[]>([]);

    const [customerId, setCustomerId] = useState("");
    const [dateIssued, setDateIssued] = useState("");
    const [dateDue, setDateDue] = useState("");
    const [totalDollars, setTotalDollars] = useState("");
    const [status, setStatus] = useState<InvoiceStatus>("draft");

    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function loadData() {
        try {
            setError(null);

            const [customerData, invoiceData] = await Promise.all([
                listCustomers(),
                listInvoices(),
            ]);

            setCustomers(customerData);
            setInvoices(invoiceData)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load invoices.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadData();
    }, []);

    const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault()

    if (!customerId) {
        setError("Customer is required.");
        return;
    }

    if (!totalDollars.trim()) {
      setError("Invoice total is required.");
      return;
    }

    try {
        setIsSubmitting(true);
        setError(null);

        await createInvoice({
            customer_id: Number(customerId),
            date_issued: dateIssued || null,
            date_due: dateDue || null,
            total: Number(totalDollars),
        });

        setCustomerId("");
        setDateIssued("");
        setDateDue("");
        setTotalDollars("");
        setStatus("draft");

        await loadData();
        } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create invoice.");
        } finally {
        setIsSubmitting(false);
        }
    }


    async function handleStatusChange(invoiceId: number, nextStatus: InvoiceStatus) {
        try {
            setError(null);
            await updateInvoiceStatus(invoiceId, nextStatus);
            await loadData();
        }   catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update status.");
        }
    }

    function  getCustomerName(id: number) {
        const customer = customers.find((customer) => customer.id === id);
        return customer ? customer.name : `Customer #${id}`;
    }

    function getNextStatuses(status: InvoiceStatus): InvoiceStatus[] {
  switch (status) {
    case "draft":
      return ["sent"];
    case "sent":
      return ["paid", "void"];
    case "paid":
      return ["sent"];
    case "void":
      return [];
    default:
      return [];
  }
}

    return (
        <section>
            <h2>Invoices</h2>
            <p>Create invoices and update invoice statuses.</p>

            {error && <p style={{color: "red"}}>{error}</p>}

            <form onSubmit={handleSubmit} style={{ marginBottom: "2rem"}}>
                <div style={{ marginBottom: "1rem" }}>
                    <label htmlFor="customer">Customer</label>
                    <br />
                    <select
                        id="customer"
                        value={customerId}
                        onChange={(event) => setCustomerId(event.target.value)}
                    >
                        <option value="">Select a customer</option>    
                        {customers.map((customer) => (
                            <option key={customer.id} value={customer.id}>
                                {customer.name} - {customer.email}
                            </option>
                        ))}
                    </select>
                </div>

                <div style={{ marginBottom: "1rem" }}>
                    <label htmlFor="dateIssued">Date Issued</label>
                    <br />
                    <input
                        id="dateIssued"
                        type="date"
                        value={dateIssued}
                        onChange={(event) => setDateIssued(event.target.value)}
                    />
                </div>

                <div style={{ marginBottom: "1rem" }}>
                    <label htmlFor="dateDue">Date Due</label>
                    <br />
                    <input
                        id="dateDue"
                        type="date"
                        value={dateDue}
                        onChange={(event) => setDateDue(event.target.value)}
                    />
                </div>

                <div style={{ marginBottom: "1rem" }}>
                    <label htmlFor="total">Total</label>
                    <br />
                    <input
                        id="total"
                        type="text"
                        value={totalDollars}
                        onChange={(event) => setTotalDollars(event.target.value)}
                        placeholder="125.00"
                    />
                </div>

                <button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Creating..." : "Create Invoice"}
                </button>
            </form>

            {isLoading ? (
                <p>Loading Invoices...</p>
            ) : invoices.length === 0 ? (
                <p>No invoices found.</p>
            ) : (
                <table border={1} cellPadding={8}>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Customer</th>
                            <th>Date Issued</th>
                            <th>Date Due</th>
                            <th>Total</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>

                    <tbody>
                        {invoices.map((invoice) => (
                            <tr key={invoice.id}>
                                <td>{invoice.id}</td>
                                <td>{"(" + invoice.customer_id + ")" + getCustomerName(invoice.customer_id)}</td>
                                <td>{invoice.date_issued ?? "—"}</td>
                                <td>{invoice.date_due ?? "—"}</td>
                                <td>{(invoice.total)}</td>
                                <td>{invoice.status}</td>
                                <td>
                                    {getNextStatuses(invoice.status).length === 0 ? (
                                        <span>No actions</span>
                                    ) : (
                                        getNextStatuses(invoice.status).map((nextStatus) => (
                                        <button
                                            key={nextStatus}
                                            type="button"
                                            onClick={() => handleStatusChange(invoice.id, nextStatus)}
                                            style={{ marginRight: "0.5rem" }}
                                        >
                                            Mark as {nextStatus}
                                        </button>
                                        ))
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

        </section>
    )
}