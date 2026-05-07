import CoursesDisplay from "./CoursesDisplay";

const CustomerDetail = ( { customer }) => {
  return (
    <div className="customer-detail">
      {customer ? (
        <>
          <h2>{customer.name}</h2>
          <p>Email: {customer.email}</p>
          <p>Phone: {customer.phone}</p>
          <CoursesDisplay customer={customer} />
        </>
      ) : (
        <p>Customer not found.</p>
      )}
    </div>
  );
};

export default CustomerDetail;