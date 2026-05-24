import { useEffect, useState } from 'react';
import { listCustomers, type Customer } from './api/customers';
import { listInvoices, type Invoice } from './api/invoices';
import './App.css'

function App() {
const [customers, setCustomers] = useState<Customer[]>([]);
const [invoices, setInvoices] = useState<Invoice[]>([]);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  async function loadData() {
    try {
      const [customerData, invoiceData] = await Promise.all([
        listCustomers(),
        listInvoices(),
      ]);

      setCustomers(customerData);
      setInvoices(invoiceData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    }
  }

  loadData();
}, []);

return (
  <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif "}}>
    <h1>Invoice DB</h1>
    <p>React frontend connected to Django API.</p>

    {error && (
      <p style={{ color: "red" }}>
        API error: {error}
      </p>
    )}

    <section>
      <h2>Customers</h2>
      {customers.length === 0 ? (
        <p>No customers found.</p>
      ) : (
        <ul>
          {customers.map((customer) => (
            <li key={customer.id}>
              {customer.name} - {customer.email}
            </li>
          ))}
        </ul>
      )}
    </section>
    
    <section>
       <h2>Invoices</h2>
      {invoices.length === 0 ? (
        <p>No invoices found.</p>
      ) : (
        <ul>
          {invoices.map((invoice) => (
            <li key={invoice.id}>
              Invoice #{invoice.id} - Status: {invoice.status} - Total:{" "}
              ${invoice.total}
            </li>
          ))}
        </ul>
      )}
    </section>
  </main>
)

}
export default App
