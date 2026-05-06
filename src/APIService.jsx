import './App.jsx';

export default class APIService {
    static async fetchCustomers() {
        try {
            const response = await fetch('/backend/app/routes/customers/getCustomers', {
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

    static importCustomersEmail() {
        return fetch('/backend/app/routes/imports/email', {
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
        return fetch('/backend/app/routes/imports/db', {
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
        return fetch('/backend/app/routes/imports/csv', {
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
        return fetch(`/backend/app/routes/courses/${customerId}`, {
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