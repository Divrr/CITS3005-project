# app/__init__.py
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = 'your-secret-key'

from app.ontology import onto
from app import routes
