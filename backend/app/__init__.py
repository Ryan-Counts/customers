# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from .database import db
from dotenv import load_dotenv
import os
from flask import Blueprint, render_template, request, jsonify, abort
from app.routes.imports import imports_bp
from app.routes.customers import customers_bp

#customers_bp = Blueprint("customers", __name__, template_folder="templates")
#imports_bp = Blueprint("imports", __name__, template_folder="templates")


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///customers.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config.from_object("config.config")

    CORS(app)
    db.init_app(app)

    with app.app_context():
        from .models import Customer
        from .models import CoursesTaken
        from .models import ContactMethod
        db.create_all()

    app.register_blueprint(imports_bp, url_prefix="/imports")
    app.register_blueprint(customers_bp, url_prefix="/customers")
    

    return app