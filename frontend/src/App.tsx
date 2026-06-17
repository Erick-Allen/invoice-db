import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { CustomersPage } from "./pages/CustomersPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InvoicesPage } from "./pages/InvoicesPage";
import { ProductsPage } from "./pages/ProductsPage";
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
            </nav>
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="customers" element={<CustomersPage />} />
            <Route path="invoices" element={<InvoicesPage />} />
            <Route path="products" element={<ProductsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
