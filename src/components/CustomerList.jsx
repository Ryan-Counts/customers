import React from 'react';

const CustomerList = ({ customers, selectedCustomer, handleSelectCustomer }) => {

    

    return (
        <div className="customer-list">
            <h2>Customer List</h2>
            <ul>
                {customers.length > 0 ? (
                    customers.map((customer) => (
                        <li key={customer.id}>
                            <strong>{customer.name}</strong>
                            <button onClick={() => handleSelectCustomer(customer)}>View Details</button>
                        </li>
                    ))
                ) : (
                    <p>No customers found.</p>
                )}
            </ul>
        </div>
    );
};

export default CustomerList;