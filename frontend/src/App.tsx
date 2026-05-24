import { CustomersPage } from './pages/CustomersPage';
import { InvoicesPage } from './pages/InvoicesPage';

function App() {
return (
  <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif "}}>
    <h1>Invoice DB</h1>
    <p>React frontend connected to Django API.</p>

    <CustomersPage />
    <InvoicesPage />
  </main>
)

}
export default App
