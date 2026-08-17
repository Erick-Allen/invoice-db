import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { CustomerDetailPage } from "./pages/CustomerDetailPage";
import { CustomersPage } from "./pages/CustomersPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InvoiceDetailPage } from "./pages/InvoiceDetailPage";
import { InvoicesPage } from "./pages/InvoicesPage";
import { ProductsPage } from "./pages/ProductsPage";
import { ReportingPage } from "./pages/ReportingPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="app-header">
          <div className="app-header-content">
            <h1 className="app-title">InvoiceDB</h1>

            <nav className="app-nav">
              <NavLink to="/" end>Dashboard</NavLink>
              <NavLink to="/customers">Customers</NavLink>
              <NavLink to="/invoices">Invoices</NavLink>
              <NavLink to="/products">Products</NavLink>
              <NavLink to="/reporting">Reporting</NavLink>
            </nav>
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="customers" element={<CustomersPage />} />
            <Route path="customers/:customerId" element={<CustomerDetailPage />} />
            <Route path="invoices" element={<InvoicesPage />} />
            <Route path="invoices/:invoiceId" element={<InvoiceDetailPage />} />
            <Route path="products" element={<ProductsPage />} />
            <Route path="reporting" element={<ReportingPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
