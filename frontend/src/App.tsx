import { CustomersPage } from './pages/CustomersPage';

function App() {
return (
  <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif "}}>
    <h1>Invoice DB</h1>
    <p>React frontend connected to Django API.</p>

    <CustomersPage />
  </main>
)

}
export default App
