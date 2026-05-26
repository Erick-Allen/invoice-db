import {BrowserRouter, Link, Route, Routes} from "react-router-dom";
import { CustomersPage } from './pages/CustomersPage';
import { DashboardPage } from './pages/dashboardPage';
import { InvoicesPage } from './pages/InvoicesPage';
import "./App.css";

function App() {
return (
  <BrowserRouter>
  <div className="app-shell">
    <header className="app-header">
      <div className="app-header-content">
          <h1 className="app-title">Invoice DB</h1>
          <p className="app-subtitle">
            React frontend connected to Django API.
          </p>

          <nav className="app-nav">
            <Link to="/">Dashboard</Link>
            <Link to="/customers">Customers</Link>
            <Link to="/invoices">Invoices</Link>
          </nav>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="customers" element={<CustomersPage />} />
            <Route path="invoices" element={<InvoicesPage />} />
          </Routes>
        </main>
    </div>
    </header>
  </div>
  </BrowserRouter>

)

}
export default App
