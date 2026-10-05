import { useEffect, useState } from "react";
import { BrowserRouter, NavLink, Route, Routes, useNavigate } from "react-router-dom";
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

function AppShell() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    async function loadCurrentUser() {
      try {
        const response = await getCurrentUser();
        setCurrentUser(response.user);
      } catch {
        setCurrentUser(null);
      } finally {
        setIsCheckingAuth(false);
      }
    }

    loadCurrentUser();
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setCurrentUser(null);
      navigate("/");
    }
  }

  if (isCheckingAuth) {
    return (
      <div className="app-shell auth-only-shell">
        <main className="app-main">
          <section className="auth-page">
            <div className="auth-card">
              <div className="auth-copy">
                <h2>Checking account access...</h2>
              </div>
            </div>
          </section>
        </main>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="app-shell auth-only-shell">
        <main className="app-main">
          <AuthPage onAuthSuccess={setCurrentUser} />
        </main>
      </div>
    );
  }

  return (
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
            <div className="auth-session">
              <button
                className={currentUser.is_guest ? "guest-session-button" : ""}
                type="button"
                onClick={handleLogout}
                aria-label="Sign out"
              >
                <span>{currentUser.is_guest ? "Guest" : currentUser.name || currentUser.email} · Sign Out</span>
              </button>
            </div>
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
          <Route path="auth" element={<DashboardPage />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

export default App;
