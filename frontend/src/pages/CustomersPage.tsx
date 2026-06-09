import {useEffect, useState, type SubmitEventHandler } from "react";
import { createCustomer, updateCustomer, deleteCustomer, listCustomers, type Customer } from "../api/customers";

export function CustomersPage() {
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [editingCustomerId, setEditingCustomerId] = useState<number | null>(null);
    const [editName, setEditName] = useState("");
    const [editEmail, setEditEmail] = useState("");

    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function loadCustomers() {
        try {
            setError(null);
            const data = await listCustomers();
            setCustomers(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load customers.");
        } finally {
            setIsLoading(false);
        }
    }

    function startEditingCustomer(customer: Customer) {
        setEditingCustomerId(customer.id);
        setEditName(customer.name);
        setEditEmail(customer.email);
    }

    function cancelEditingCustomer() {
        setEditingCustomerId(null);
        setEditName("");
        setEditEmail("");
    }

    async function handleUpdateCustomer(customerId: number) {
        const trimmedName = editName.trim();
        const trimmedEmail = editEmail.trim();

        if (!trimmedName) {
            setError("Customer name is required.");
            return;
        }

        if (!trimmedEmail) {
            setError("Customer email is required.");
            return;
        }

        try {
            setError(null);

            await updateCustomer(customerId, {
                name: trimmedName,
                email: trimmedEmail,
            });

            cancelEditingCustomer();
            await loadCustomers();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update customer.");
        }
    }

    async function handleDeleteCustomer(customerId: number) {
        const confirmed = window.confirm(
            "Are you sure you want to delete this customer?"
        );

        if (!confirmed) {
            return;
        }

        try {
            setError(null)
            await deleteCustomer(customerId);
            await loadCustomers();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete customer.");
        }
    }

    useEffect(() => {
        loadCustomers();
    }, []);

    const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        const trimmedName = name.trim();
        const trimmedEmail = email.trim();

        if (!trimmedName) {
            setError("Customer name is required.");
            return;
        }

        if (!trimmedEmail) {
            setError("Customer email is required.");
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);

            await createCustomer({
                name: trimmedName,
                email: trimmedEmail,
            });

        setName("");
        setEmail("");

        await loadCustomers();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Faild to create customer.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
    <>
        <div className="page-header">
        <h2>Customers</h2>
        <p>Create customers and view existing customer records.</p>
        </div>

        <section className="invoice-page-stack">
        {error && <p className="error-message">{error}</p>}

        <form onSubmit={handleSubmit} className="form-card">
            <div>
            <h3>Create Customer</h3>
            </div>

            <div className="form-grid">
            <div className="form-field">
                <label htmlFor="name">Name</label>
                <br />
                <input
                id="name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Jane Doe"
                />
            </div>

            <div className="form-field">
                <label htmlFor="email">Email</label>
                <br />
                <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="jane@example.com"
                />
            </div>

            <button className="primary-button" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Customer"}
            </button>
            </div>
        </form>

        <div className="section-header">
            <h3>Customer List</h3>
        </div>

        <div className="table-wrapper wide-table-wrapper">
            {isLoading ? (
            <p>Loading customers...</p>
            ) : customers.length === 0 ? (
            <p>No customers found.</p>
            ) : (
            <table className="data-table">
                <thead>
                <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Actions</th>
                </tr>
                </thead>

                <tbody>
                {customers.map((customer, index) => (
                    <tr key={customer.id}>
                    <td>{index + 1}</td>

                    {editingCustomerId === customer.id ? (
                        <>
                        <td>
                            <input
                            type="text"
                            value={editName}
                            onChange={(event) => setEditName(event.target.value)}
                            />
                        </td>
                        <td>
                            <input
                            className="wide-select"
                            type="email"
                            value={editEmail}
                            onChange={(event) => setEditEmail(event.target.value)}
                            />
                        </td>
                        <td>
                            <div className="name-actions">
                            <button
                                className="small-action-button"
                                type="button"
                                onClick={() => handleUpdateCustomer(customer.id)}
                            >
                                Save
                            </button>
                            <button
                                className="small-danger-button"
                                type="button"
                                onClick={cancelEditingCustomer}
                            >
                                Cancel
                            </button>
                            </div>
                        </td>
                        </>
                    ) : (
                        <>
                        <td>{customer.name}</td>
                        <td>{customer.email}</td>
                        <td>
                            <div className="name-actions">
                            <button
                                className="small-action-button"
                                type="button"
                                onClick={() => startEditingCustomer(customer)}
                            >
                                Edit
                            </button>

                            <button
                                className="small-danger-button"
                                type="button"
                                onClick={() => handleDeleteCustomer(customer.id)}
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
    );
}