import CoursesDisplay from "./CoursesDisplay";

const CustomerDetail = ( { customer }) => {
  return (
    <div className="customer-detail">
      <h2>{customer.name}</h2>
      <p>Email: {customer.email}</p>
      <p>Phone: {customer.phone}</p>
      <CoursesDisplay courses={customer.id} />
    </div>
  );
};
