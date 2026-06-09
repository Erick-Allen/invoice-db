import { useEffect, useState, type SubmitEventHandler } from "react";
import { dollarsToCents, centsToDollars } from "../utils/money";
import { listCustomers, type Customer } from "../api/customers";
import { createInvoice, listInvoices, updateInvoice, updateInvoiceStatus, deleteInvoice, type Invoice, type InvoiceStatus } from "../api/invoices";
import { AssistantChatBox } from "../components/AssistantChatBox";

export function InvoicesPage() {
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [invoices, setInvoices] = useState<Invoice[]>([]);

    const [customerId, setCustomerId] = useState("");
    const [dateIssued, setDateIssued] = useState("");
    const [dateDue, setDateDue] = useState("");
    const [totalDollars, setTotalDollars] = useState("");
    const [editingInvoiceId, setEditingInvoiceId] = useState<number | null>(null);
    const [editCustomerId, setEditCustomerId] = useState("");
    const [editDateIssued, setEditDateIssued] = useState("");
    const [editDateDue, setEditDateDue] = useState("");
    const [editTotalDollars, setEditTotalDollars] = useState("");
    
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
            total: dollarsToCents(totalDollars),
        });

        setCustomerId("");
        setDateIssued("");
        setDateDue("");
        setTotalDollars("");

        await loadData();
        } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create invoice.");
        } finally {
        setIsSubmitting(false);
        }
    }

    function startEditingInvoice(invoice: Invoice) {
        setEditingInvoiceId(invoice.id);
        setEditCustomerId(String(invoice.customer_id));
        setEditDateIssued(invoice.date_issued ?? "");
        setEditDateDue(invoice.date_due ?? "");
        setEditTotalDollars(centsToDollars(invoice.total));
    }

    function cancelEditingInvoice() {
        setEditingInvoiceId(null);
        setEditCustomerId("");
        setEditDateIssued("");
        setEditDateDue("");
        setEditTotalDollars("");
    }

    async function handleUpdateInvoice(invoiceId: number) {
    if (!editCustomerId) {
        setError("Customer is required.");
        return;
    }

    let totalCents: number;

    try {
        totalCents = dollarsToCents(editTotalDollars);
    } catch (err) {
        setError(err instanceof Error ? err.message : "Enter a valid invoice total.");
        return;
    }

    if (totalCents <= 0) {
        setError("Invoice total must be greater than 0.");
        return;
    }

    const existingInvoice = invoices.find((invoice) => invoice.id === invoiceId);

    if (!existingInvoice) {
        setError("Invoice not found.");
        return;
    }

    const noChangesDetected =
        existingInvoice.customer_id === Number(editCustomerId) &&
        (existingInvoice.date_issued ?? "") === editDateIssued &&
        (existingInvoice.date_due ?? "") === editDateDue &&
        existingInvoice.total === totalCents;

    if (noChangesDetected) {
        setError(null);
        cancelEditingInvoice();
        return;
    }

    try {
        setError(null);

        await updateInvoice(invoiceId, {
            customer_id: Number(editCustomerId),
            date_issued: editDateIssued || null,
            date_due: editDateDue || null,
            total: totalCents,
        });

        cancelEditingInvoice();
        await loadData();
    } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to update invoice.");
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

    async function handleDeleteInvoice(invoiceId: number) {
        const confirmed = window.confirm("Are you sure you want to delete this invoice?")
            
        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await deleteInvoice(invoiceId);
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete invoice.")
        }
    }

    

    return (
        <>
            <div className="page-header">
                <h2>Invoices</h2>
                <p>Create invoices and update invoice statuses.</p>
            </div>

            <section className="invoice-page-stack">

            {error && <p className="error-message">{error}</p>}

            <form onSubmit={handleSubmit} className="form-card">
            <div>
                <h3>Create Invoice</h3>
            </div>

            <div className="form-grid">
                    <div className="form-field">
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

                    <div className="form-field">
                        <label htmlFor="dateIssued">Date Issued</label>
                        <br />
                        <input
                            id="dateIssued"
                            type="date"
                            value={dateIssued}
                            onChange={(event) => setDateIssued(event.target.value)}
                        />
                    </div>

                    <div className="form-field">
                        <label htmlFor="dateDue">Date Due</label>
                        <br />
                        <input
                            id="dateDue"
                            type="date"
                            value={dateDue}
                            onChange={(event) => setDateDue(event.target.value)}
                        />
                    </div>

                    <div className="form-field">
                        <label htmlFor="total">Total</label>
                        <br />
                        <input
                            id="total"
                            type="text"
                            value={totalDollars}
                            onChange={(event) => setTotalDollars(event.target.value)}
                            placeholder="0"
                        />
                    </div>

                    <button className="primary-button" type="submit" disabled={isSubmitting}>
                        {isSubmitting ? "Creating..." : "Create Invoice"}
                    </button>
                </div>
            </form>

            <AssistantChatBox />
            <h3>Invoice List</h3>


            <div className="table-wrapper">
                {isLoading ? (
                    <p>Loading Invoices...</p>
                ) : invoices.length === 0 ? (
                    <p className="empty-state">No invoices found.</p>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Customer</th>
                                <th>Date Issued</th>
                                <th>Date Due</th>
                                <th>Total</th>
                                <th>Status</th>
                                <th>Change Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>

                        <tbody>
                            {invoices.map((invoice, index) => (
                                <tr key={invoice.id}>
                                    <td>{index + 1}</td>

                                    {editingInvoiceId === invoice.id ? (
                                        <>
                                            <td>
                                                <select   
                                                    className="wide-select"
                                                    value={editCustomerId}
                                                    onChange={(event) => setEditCustomerId(event.target.value)}
                                                >
                                                    <option value="">Select a customer</option>
                                                    {customers.map((customer) => (
                                                        <option key={customer.id} value={customer.id}>
                                                            {customer.name} - {customer.email}
                                                        </option>
                                                    ))}
                                                </select>
                                            </td>
                                            <td>
                                                <input  
                                                    type="date"
                                                    value={editDateIssued}
                                                    onChange={(event) => setEditDateIssued(event.target.value)}
                                                />
                                            </td>
                                            <td>
                                                <input  
                                                    type="date"
                                                    value={editDateDue}
                                                    onChange={(event) => setEditDateDue(event.target.value)}
                                                />
                                            </td>
                                            <td>
                                                <input  
                                                    type="text"
                                                    value={editTotalDollars}
                                                    onChange={(event) => setEditTotalDollars(event.target.value)}
                                                />
                                            </td>
                                            
                                            <td>
                                                <span className="status-badge">{invoice.status}</span>
                                            </td>
                                            <td>
                                                <span>Editing</span>
                                            </td>


                                            <td>
                                                <div className="name-actions">
                                                    <button
                                                        className="small-action-button"
                                                        type="button"
                                                        onClick={() => handleUpdateInvoice(invoice.id)}
                                                    >
                                                        Save
                                                    </button>

                                                    <button
                                                        className="small-danger-button"
                                                        type="button"
                                                        onClick={cancelEditingInvoice}
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            </td>
                                        </>
                                    ) : (
                                        <>
                                            <td>{getCustomerName(invoice.customer_id)}</td>
                                            <td>{invoice.date_issued ?? "—"}</td>
                                            <td>{invoice.date_due ?? "—"}</td>
                                            <td>${centsToDollars(invoice.total)}</td>
                                            <td>
                                                <span className="status-badge">{invoice.status}</span>
                                            </td>
                                            <td>
                                                {getNextStatuses(invoice.status).length === 0 ? (
                                                    <span>No actions</span>
                                                ) : (
                                                    getNextStatuses(invoice.status).map((nextStatus) => (
                                                    <button
                                                        className="action-button"
                                                        key={nextStatus}
                                                        type="button"
                                                        onClick={() => handleStatusChange(invoice.id, nextStatus)}
                                                    >
                                                        {nextStatus}
                                                    </button>
                                                    ))
                                                )}
                                            </td>
                                            <td>
                                                <div className="name-actions">
                                                    <button
                                                        className="small-action-button"
                                                        type="button"
                                                        onClick={() => startEditingInvoice(invoice)}
                                                    >
                                                        Edit
                                                    </button>
                                                    <button
                                                        className="small-danger-button"
                                                        type="button"
                                                        onClick={() => handleDeleteInvoice(invoice.id)}
                                                    >
                                                        Delete
                                                    </button>
                                                </div>
                                            </td>
                                        </>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
            </section>
        </>
    )
}