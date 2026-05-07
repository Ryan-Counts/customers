from flask import Blueprint, Flask, jsonify, request
import sqlalchemy
from ..models import Customer
from ..models import CoursesTaken
from ..database import db

customers_bp = Blueprint("customers", __name__)

@customers_bp.route("/getCustomers", methods=["GET"])
def get_customers():
    print("Fetching customers from database...")
    customers = db.session.query(Customer).all()
    return jsonify([customer.to_dict() for customer in customers])

@customers_bp.route("/getCustomerCourses/<int:customer_id>", methods=["GET"])
def get_courses(customer_id):
    courses = db.session.query(CoursesTaken).filter_by(customer_id=customer_id).all()
    return jsonify([course.to_dict() for course in courses])