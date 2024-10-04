# app/__init__.py
from flask import Flask

app = Flask(__name__)

# Import  ontology
from app.ontology import onto

from app import routes
