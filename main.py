from recipe import *
from flask import Flask, request, session, g, redirect, url_for, \
		 abort, render_template, flash, jsonify

from jinja2 import Environment, FileSystemLoader
import os



# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# Routes
@app.route('/')
def show_vanilla_home():
	return render_template('index.html')

@app.route('/fetchRecipe', methods=['POST'])
def fetchRecipe():
	url = request.data
	recipe = fetch_recipe(url)
	return jsonify(recipe)

	
# Error Handlers
@app.errorhandler(500)
def internal_error(error):
	return "500 Internal Error"

@app.errorhandler(404)
def not_found(error):
	return "404 Error: Page not found", 404


if __name__ == '__main__':
		#app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))
	app.run(debug=True)
