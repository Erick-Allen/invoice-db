export function DashboardPage() {
  return (
    <section className="page">
      <div className="page-header">
      <h2>Dashboard</h2>
      <p>Manage customers and invoices through the Invoice DB web interface.</p>
      </div>

    <div className="form-card">
      <h3>v0.8.0 Frontend Goals</h3>
      <ul>
        <li>Create and view customers</li>
        <li>Create and view invoices</li>
        <li>Update invoice status using lifecycle actions</li>
        <li>Prove the full React UI → API → services → db flow</li>
      </ul>
    </div>
    </section>
  );
}