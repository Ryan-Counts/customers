import sqlite3

connection = sqlite3.connect('backend/customers.db')

connection.close()