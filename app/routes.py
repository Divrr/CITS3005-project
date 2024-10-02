from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Homepage')

@app.route('/search')
def search():
    return render_template('searchpage.html', title='Search')