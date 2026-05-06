from flask import Flask, jsonify, request
from ..models import Customer
from ..models import CoursesTaken

app = Flask(__name__)

@app.route("/customers/getCustomers", methods=["GET"])
def get_customers():
    customers = Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers])

@app.route("/customers/getCustomerCourses/<int:customer_id>", methods=["GET"])
def get_courses(customer_id):
    courses = CoursesTaken.query.filter_by(customer_id=customer_id).all()
    return jsonify([course.to_dict() for course in courses])