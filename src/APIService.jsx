import './App.jsx';

export default class APIService {
    static async fetchCustomers() {
        try {
            const response = await fetch('/customers/getCustomers', {
                method: 'GET',
                headers: {}
            });
            const customers = await response.json();
            return customers;
        } catch (error) {
            console.error('Error fetching customers:', error);
            throw error;
        }
    }

    static async importCustomersEmail() {
        try {
            const response = await fetch('/imports/email', {
                method: 'GET',
                headers: {}
            });
            const emailImports = await response.json();
            return emailImports;
        } catch (error) {
            console.error('Error importing customers:', error);
            throw error;
        }
    }

    static importCustomersDB() {
        return fetch('/imports/db', {
            method: 'GET',
            headers: {}
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error importing customers:', error);
            throw error;
        });
    }

    static importCustomersDB() {
        return fetch('/imports/db', {
            method: 'GET',
            headers: {}
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error importing customers:', error);
            throw error;
        });
    }

    static importCustomersCSV() {
        return fetch('/imports/csv', {
            method: 'GET',
            headers: {}
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error importing customers:', error);
            throw error;
        });
    }

    static getCoursesForCustomer(customerId) {
        return fetch(`/customers/getCustomerCourses/${customerId}`, {
            method: 'GET',
            headers: {}
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error fetching courses:', error);
            throw error;
        });
    }
}