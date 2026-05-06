

const CustomerList = ({ customers, setSelectedCustomer }) => {

    const handleSelectCustomer = (customer) => {
        setSelectedCustomer(customer);
    }

    return (
        <div className="customer-list">
            <h2>Customer List</h2>
            <ul>
                {customers.map((customer) => (
                    <li key={customer.id}>
                        <strong>{customer.name}</strong>
                        <button onClick={() => handleSelectCustomer(customer)}>View Details</button>
                    </li>
                ))}
            </ul>
        </div>
    );
};
