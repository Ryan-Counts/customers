# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from .database import db
from dotenv import load_dotenv
import os
from flask import Blueprint, render_template, request, jsonify, abort

customers_bp = Blueprint("customers", __name__, template_folder="templates")
imports_bp = Blueprint("imports", __name__, template_folder="templates")


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///customers.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(customers_bp, url_prefix="/app/customers")
    app.register_blueprint(imports_bp, url_prefix="/app/import")

    return app