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

@app.route('/')
def show_vanilla_home():
    #return render_template('index.html') #Loads Welcome Page
    return "Hello World"

@app.route('/fetchRecipe')
def fetchRecipe():
	recipe = fetch_recipe('http://allrecipes.com/recipe/219929/heathers-fried-chicken/')
	return str(recipe)



if __name__ == '__main__':
    #app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))
	app.run(debug=True)
