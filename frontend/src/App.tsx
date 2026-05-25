import {BrowserRouter, Link, Route, Routes} from "react-router-dom";
import { CustomersPage } from './pages/CustomersPage';
import { DashboardPage } from './pages/dashboardPage';
import { InvoicesPage } from './pages/InvoicesPage';

function App() {
return (
  <BrowserRouter>
    <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif "}}>
      <header style={{ marginBottom: "2rem"}}>
        <h1>Invoice DB</h1>
        <p>React frontend connected to Django API.</p>

        <nav style={{ display: "flex", gap: "1rem"}}>
          <Link to="/">Dashboard</Link>
          <Link to="/customers">Customers</Link>
          <Link to="/invoices">Invoices</Link>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="invoices" element={<InvoicesPage />} />
      </Routes>
    </main>
  </BrowserRouter>

)

}
export default App
