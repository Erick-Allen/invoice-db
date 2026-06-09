import { useEffect, useState } from "react";
import { listCustomers, type Customer } from "../api/customers";
import { listInvoices, type Invoice } from "../api/invoices";
import { centsToDollars } from "../utils/money";

export function DashboardPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setError("");

        const [customerData, invoiceData] = await Promise.all([
          listCustomers(),
          listInvoices(),
        ]);

        setCustomers(customerData);
        setInvoices(invoiceData);
      } catch {
        setError("Failed to load dashboard data.");
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const draftCount = invoices.filter((invoice) => invoice.status === "draft").length;
  const sentCount = invoices.filter((invoice) => invoice.status === "sent").length;
  const paidCount = invoices.filter((invoice) => invoice.status === "paid").length;
  const voidCount = invoices.filter((invoice) => invoice.status === "void").length;

  const recentCustomers = [...customers]
    .sort((a, b) => b.id - a.id)
    .slice(0, 3);

  const recentInvoices = [...invoices]
    .sort((a, b) => b.id - a.id)
    .slice(0, 3);

  function getCustomerName(customerId: number) {
    const customer = customers.find((customer) => customer.id === customerId);
    return customer ? customer.name : `Customer #${customerId}`;
  }

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Quick overview of customers and invoice activity.</p>
      </div>

      <section className="dashboard-stack">
        {error && <p className="error-message">{error}</p>}

        {isLoading ? (
          <p>Loading dashboard...</p>
        ) : (
          <>
            <div className="dashboard-summary-grid">
              <div className="dashboard-summary-card">
                <span className="dashboard-summary-label">Total Customers</span>
                <strong>{customers.length}</strong>
              </div>

              <div className="dashboard-summary-card">
                <span className="dashboard-summary-label">Total Invoices</span>
                <strong>{invoices.length}</strong>
              </div>
            </div>

            <div className="dashboard-columns">
              <div className="dashboard-panel">
                <h3>Recent Customers</h3>

                {recentCustomers.length === 0 ? (
                  <p className="empty-state">No customers found.</p>
                ) : (
                  <ul className="dashboard-list">
                    {recentCustomers.map((customer) => (
                      <li key={customer.id}>
                        <strong>{customer.name}</strong>
                        <span>{customer.email}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="dashboard-panel">
                <h3>Recent Invoices</h3>

                {recentInvoices.length === 0 ? (
                  <p className="empty-state">No invoices found.</p>
                ) : (
                  <ul className="dashboard-list">
                    {recentInvoices.map((invoice) => (
                      <li key={invoice.id}>
                        <strong>
                          {getCustomerName(invoice.customer_id)}
                        </strong>
                        <span>
                          ${centsToDollars(invoice.total)} · {invoice.status}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="dashboard-panel dashboard-status-panel">
                <h3>Invoice Status</h3>

                <div className="status-breakdown">
                  <div>
                    <span>Draft</span>
                    <strong>{draftCount}</strong>
                  </div>

                  <div>
                    <span>Sent</span>
                    <strong>{sentCount}</strong>
                  </div>

                  <div>
                    <span>Paid</span>
                    <strong>{paidCount}</strong>
                  </div>

                  <div>
                    <span>Void</span>
                    <strong>{voidCount}</strong>
                  </div>
                </div>
              </div>

            </div>
          </>
        )}
      </section>
    </>
  );
}