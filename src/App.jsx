import { useState, useEffect } from "react"
import APIService from "./APIService.jsx"

import "./App.css"
import CustomerList from "./components/CustomerList.jsx"
import CustomerDetail from "./components/CustomerDetail.jsx"
import ImportPanel from "./components/ImportPanel.jsx"

function App() {
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);

  useEffect(() => {
    APIService.fetchCustomers()
      .then(data => setCustomers(data))
      .catch(error => console.error('Error fetching customers:', error));
  }, []);

  const handleSelectCustomer = (customer) => {
    console.log('Selected customer:', customer);
    setSelectedCustomer(customer);
  }

  return (
    <div className="app-container">
      <h1>Customer Manager</h1>
      <div className="main-content">
        <CustomerList customers={customers} selectedCustomer={selectedCustomer} handleSelectCustomer={handleSelectCustomer} />
      </div>
      <CustomerDetail customer={selectedCustomer} />
      <ImportPanel></ImportPanel>
    </div>
  )
}

export default App