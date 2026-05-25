import {useEffect, useState, type SubmitEventHandler } from "react";
import { createCustomer, listCustomers, type Customer } from "../api/customers";

export function CustomersPage() {
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");

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
    <section>
        <h2>Customers</h2>
        <p>Create customers and view existing customer records.</p>

        {error && (
            <p style={{ color: "red"}}>
                {error}
            </p>
        )}

        <form onSubmit={handleSubmit} style={{ marginBottom: "2rem"}}>
            <div style ={{ marginBottom: "1rem"}}>
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

            <div style={{ marginBottom: "1rem" }}>
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

            <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Customer"}
            </button>
        </form>

        {isLoading ? (
            <p>Loading customers...</p>
        ) : customers.length === 0 ? (
            <p>No customers found.</p>
        ) : (
            <table border={1} cellPadding={8}>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                    </tr>
                </thead>

                <tbody>
                    {customers.map((customer) => (
                        <tr key={customer.id}>
                            <td>{customer.id}</td>
                            <td>{customer.name}</td>
                            <td>{customer.email}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        )}
    </section>
    );
}