import { useEffect, useState } from "react";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { getCurrentUser, logout, type AuthUser } from "./api/auth";
import { AuthPage } from "./pages/AuthPage";
import { CategoryDetailPage } from "./pages/CategoryDetailPage";
import { CustomerDetailPage } from "./pages/CustomerDetailPage";
import { CustomersPage } from "./pages/CustomersPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InvoiceDetailPage } from "./pages/InvoiceDetailPage";
import { InvoicesPage } from "./pages/InvoicesPage";
import { LocationDetailPage } from "./pages/LocationDetailPage";
import { LocationsPage } from "./pages/LocationsPage";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { ProductsPage } from "./pages/ProductsPage";
import { ReportingPage } from "./pages/ReportingPage";
import { SupplierDetailPage } from "./pages/SupplierDetailPage";
import { SuppliersPage } from "./pages/SuppliersPage";
import { TagDetailPage } from "./pages/TagDetailPage";
import "./App.css";

function App() {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    async function loadCurrentUser() {
      try {
        const response = await getCurrentUser();
        setCurrentUser(response.user);
      } catch {
        setCurrentUser(null);
      }
    }

    loadCurrentUser();
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setCurrentUser(null);
    }
  }

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
              <NavLink to="/suppliers">Suppliers</NavLink>
              <NavLink to="/products">Products</NavLink>
              <NavLink to="/locations">Locations</NavLink>
              <NavLink to="/reporting">Reporting</NavLink>
              {currentUser ? (
                <div className="auth-session">
                  <span>{currentUser.name || currentUser.email}</span>
                  <button type="button" onClick={handleLogout}>Sign Out</button>
                </div>
              ) : (
                <NavLink className="auth-nav-link" to="/auth">Sign In / Sign Up</NavLink>
              )}
            </nav>
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="customers" element={<CustomersPage />} />
            <Route path="customers/:customerId" element={<CustomerDetailPage />} />
            <Route path="locations" element={<LocationsPage />} />
            <Route path="locations/:locationId" element={<LocationDetailPage />} />
            <Route path="invoices" element={<InvoicesPage />} />
            <Route path="invoices/:invoiceId" element={<InvoiceDetailPage />} />
            <Route path="suppliers" element={<SuppliersPage />} />
            <Route path="suppliers/:supplierId" element={<SupplierDetailPage />} />
            <Route path="tags/:tagId" element={<TagDetailPage />} />
            <Route path="categories/:categoryId" element={<CategoryDetailPage />} />
            <Route path="products" element={<ProductsPage />} />
            <Route path="products/:productId" element={<ProductDetailPage />} />
            <Route path="reporting" element={<ReportingPage />} />
            <Route path="auth" element={<AuthPage onAuthSuccess={setCurrentUser} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
