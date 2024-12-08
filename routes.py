import os
from flask import Flask, jsonify, request, render_template, url_for, redirect, flash
import requests
from urllib.parse import quote
from utils import clean_micro_nutrients
from units import nutrient_units
from rni import rni_data
import logging
from collections import defaultdict
import time
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import json
from models import *
from db_utils import add_recipe_to_user, get_saved_recipes, add_recipe_to_calendar
from flask_wtf.csrf import CSRFProtect
from admin import create_admin

load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

create_admin(app)  # Initialize the admin interface


    
logging.basicConfig(level=logging.INFO)
load_dotenv()

SEARCH_LIMIT = 1
TIME_WINDOW = 5
micro_nutrients_per_serving = {}
search_counts = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("=== DEBUGGING START ===")
        print(f"Form data: {request.form}")  # Print form data
        print(f"CSRF Token: {request.form.get('csrf_token')}")  # Print CSRF token
        print("=== DEBUGGING END ===")
        
        username = request.form['username']
        password = request.form['password']
        sex = request.form['sex']
        age = request.form['age']
        weight = request.form['weight']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, sex=sex, age=age, weight=weight)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("=== DEBUGGING START ===")
        print(f"Form data: {request.form}")  # Print form data
        print(f"CSRF Token: {request.form.get('csrf_token')}")  # Print CSRF token
        print("=== DEBUGGING END ===")
        
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        sex = request.form['sex']
        age = request.form['age']
        weight = request.form['weight']
        current_user.sex = sex
        current_user.age = age
        current_user.weight = weight
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('index.html', sex=current_user.sex, age=current_user.age, weight=current_user.weight)

def fetch_recipes_logic(ingredients, meal_type=None, diet_label=None, health_label=None):
    if not ingredients:
        return {'error': 'Ingredients not provided'}, 400

    edamam_app_id = os.getenv('EDAMAM_APP_ID')
    edamam_api_key = os.getenv('EDAMAM_API_KEY')

    encoded_ingredients = quote(ingredients)
    edamam_url = (f'https://api.edamam.com/api/recipes/v2?type=public&q={encoded_ingredients}'
                  f'&app_id={edamam_app_id}&app_key={edamam_api_key}')
    max_recipes_to_show = 20

    # Search filters
    if meal_type:
        edamam_url += f'&mealType={meal_type}'
    if diet_label:
        edamam_url += f'&diet={diet_label}'
    if health_label:
        edamam_url += f'&health={health_label}'

    try:
        edamam_response = requests.get(edamam_url)
        edamam_response.raise_for_status()
        edamam_recipes = edamam_response.json()

        # Sort recipes based on the number of missing ingredients
        sorted_recipes = sorted(
            edamam_recipes['hits'],
            key=lambda x: len(set(x['recipe']['ingredientLines']) - set(ingredients.split(',')))
        )

        # Limit results
        sorted_recipes = sorted_recipes[:max_recipes_to_show]

        filtered_recipes = []

        for hit in sorted_recipes:
            recipe = hit['recipe']
            label = recipe['label']
            ingredient_lines = recipe['ingredientLines']
            url = recipe.get('url')
            image = recipe.get('image')
            calories = recipe.get('calories')
            yield_value = recipe.get('yield', None)
            
            cleaned_micro_nutrients = clean_micro_nutrients(recipe.get('totalNutrients', {}))
            calories_per_serving = calories / yield_value if yield_value else None
            meal_type_response = recipe.get('mealType', ["Unspecified"])[0]
            if '/' in meal_type_response:
                meal_types = meal_type_response.split('/')  # ['lunch', 'dinner']
            else:
                meal_types = [meal_type_response]  # Single meal type

            # Debugging output
            print(f"Meal types found: {meal_types}")


            micro_nutrients_per_serving = {
                nutrient_label: nutrient_value / yield_value
                for nutrient_label, nutrient_value in cleaned_micro_nutrients.items()
                if nutrient_label != 'Water'  # Exclude water
            }
            
            comparison_to_rni = calculate_comparison_to_rni(micro_nutrients_per_serving)

            recipe_data = {
                'label': label,
                'ingredient_lines': ingredient_lines,
                'ingredients': ingredients,
                'url': url,
                'image': image,
                'calories_per_serving': calories_per_serving,
                'micro_nutrients_per_serving': micro_nutrients_per_serving,
                'nutrient_units': nutrient_units,
                'yield': yield_value,
                'comparison_to_rni': comparison_to_rni,
                'meal_type': meal_type_response  # Include meal type
            }
            #print(f"Recipe data: {recipe_data}") 
            filtered_recipes.append(recipe_data)

        # Remove duplicates
        unique_recipes = {recipe['label']: recipe for recipe in filtered_recipes}.values()

        return list(unique_recipes), 200

    except requests.RequestException as e:
        logging.error(f'Error fetching recipes: {e}')
        return {'error': f'Network Error: {e}'}, 500
    except Exception as e:
        logging.error(f'Error processing recipes: {e}')
        return {'error': 'Failed to process recipes'}, 500

    
    
def calculate_comparison_to_rni(micro_nutrients_per_serving):
    sex = request.args.get('sex')
    age = request.args.get('age')
    weight = request.args.get('weight')

    comparison_to_rni = {}
    if sex and age and weight:
        age = int(age)
        weight = float(weight)

        protein_rni = 0.75 * weight
        age_group = get_age_group(age)

        # Calculate Vitamin K Adequate Intake (1 mcg per kg of weight)
        vitamin_k_ai = weight * 1  # in micrograms, assuming weight is in kg
        
        if sex.lower() == 'male':
            if age_group in rni_data["Micronutrients"]["Males"]:
                global_rni = rni_data["Micronutrients"]["Males"][age_group]
                if global_rni:
                    for nutrient_label, nutrient_value in micro_nutrients_per_serving.items():
                        if nutrient_label in global_rni:
                            comparison_to_rni[nutrient_label] = nutrient_value / global_rni[nutrient_label] * 100
                            #print(f"Calculated RNI for {nutrient_label}: {comparison_to_rni[nutrient_label]}%")
        elif sex.lower() == 'female':
            if age_group in rni_data["Micronutrients"]["Females"]:
                global_rni = rni_data["Micronutrients"]["Females"][age_group]
                if global_rni:
                    for nutrient_label, nutrient_value in micro_nutrients_per_serving.items():
                        if nutrient_label in global_rni:
                            comparison_to_rni[nutrient_label] = nutrient_value / global_rni[nutrient_label] * 100
                            #print(f"Calculated RNI for {nutrient_label}: {comparison_to_rni[nutrient_label]}%")

        # Adding Vitamin K AI to comparison (with asterisk notation for AI)
        vitamin_k_intake = micro_nutrients_per_serving.get('Vitamin K', 0)
        if vitamin_k_intake != 0:
            vitamin_k_percentage = (vitamin_k_intake / vitamin_k_ai) * 100
            comparison_to_rni['Vitamin K'] = {
                'percentage': vitamin_k_percentage,
                'ai_value': vitamin_k_ai,
                'note': 'AI* (Adequate Intake, not RNI)'  # Asterisk notation for AI
            }
        
        # Protein intake calculation (similar as before)
        protein_intake = micro_nutrients_per_serving.get('Protein', 0)
        if protein_intake != 0:
            protein_rni_percentage = (protein_intake / protein_rni) * 100
            comparison_to_rni['Protein'] = protein_rni_percentage
        comparison_to_rni['Protein_RNI'] = protein_rni

    return comparison_to_rni


    
@app.route('/recipes', methods=['GET'])
def recipes():
    ingredients = request.args.get('ingredients')
    meal_type = request.args.get('meal_type')
    diet_label = request.args.get('diet_label')
    health_label = request.args.get('health_label')
    sex = request.args.get('sex')
    age = request.args.get('age')
    weight = request.args.get('weight')

    recipes, status_code = fetch_recipes_logic(ingredients, meal_type, diet_label, health_label)
    if status_code == 200:
        return render_template('index.html', recipes=recipes, sex=sex, age=age, weight=weight)
    else:
        return render_template('index.html', error=recipes['error'], sex=sex, age=age, weight=weight)

@app.route('/view_calendar')
@login_required
def view_calendar():
    # Fetch saved recipes for the calendar view
    saved_recipes = get_saved_recipes(current_user.id)
    return render_template('calendar.html', user=current_user, saved_recipes=saved_recipes)

@app.route('/add_recipe', methods=['POST'])
@login_required
def add_recipe():
    recipe_id = request.form['recipe_id']
    date = request.form['date']
    # Add recipe to calendar logic here
    add_recipe_to_calendar(current_user.id, recipe_id, date)
    return redirect(url_for('dashboard'))

@app.route('/save_recipe', methods=['POST'])
@login_required
def save_recipe():
    try:
        # Debugging logs
        print("=== DEBUGGING START ===")
        print(f"Headers: {request.headers}")  # Log request headers
        print(f"JSON payload (request.get_json()): {request.get_json(silent=True)}")  # JSON payload
        print("=== DEBUGGING END ===")

        # Get the JSON data sent via AJAX
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON payload'}), 400

        recipe_data = data.get('recipe_data')
        print(f"Recipe data: {recipe_data}")

        if not recipe_data:
            print("No recipe data provided")
            return jsonify({'success': False, 'error': 'No recipe data provided'}), 400

        # Extract and save recipe details
        label = recipe_data.get('label')
        url = recipe_data.get('url')
        image = recipe_data.get('image')
        calories_per_serving = recipe_data.get('calories_per_serving', 0)
        yield_value = recipe_data.get('yield', 1)
        ingredient_lines = recipe_data.get('ingredient_lines', [])
        ingredients = recipe_data.get('ingredients', '')

        # Convert ingredient_lines to a string if it's a list
        if isinstance(ingredient_lines, list):
            ingredient_lines = '\n'.join(ingredient_lines)

        print(f"Saving recipe: {label}")

        # Save the recipe in the database
        recipe = Recipe(
            label=label,
            url=url,
            image=image,
            calories_per_serving=calories_per_serving,
            yield_value=yield_value,
            ingredient_lines=ingredient_lines,
            ingredients=ingredients
        )
        db.session.add(recipe)
        db.session.flush()  # Save changes and get recipe ID for associations

        # Handle nutrients and associations
        micro_nutrients = recipe_data.get('micro_nutrients_per_serving', {})
        nutrient_units = recipe_data.get('nutrient_units', {})
        for nutrient_name, amount in micro_nutrients.items():
            unit = nutrient_units.get(nutrient_name, 'unit')  # Default to 'unit' if missing

            # Ensure the nutrient exists
            nutrient = Nutrient.query.filter_by(name=nutrient_name).first()
            if not nutrient:
                nutrient = Nutrient(name=nutrient_name, unit=unit)
                db.session.add(nutrient)
                db.session.flush()

            # Link nutrient to recipe
            recipe_nutrient = RecipeNutrient(
                recipe_id=recipe.id,
                nutrient_id=nutrient.id,
                amount_per_serving=amount
            )
            db.session.add(recipe_nutrient)

        # Link recipe to user
        date = recipe_data.get('date', time.strftime('%Y-%m-%d'))
        meal_type = recipe_data.get('meal_type', 'unspecified')
        if isinstance(meal_type, list):
            meal_type = '/'.join(meal_type) # Join meal types with '/' if it's a list, but API should already return this format


        user_recipe = UserRecipe(
            user_id=current_user.id,
            recipe_id=recipe.id,
            date=date,
            meal_type=meal_type
        )
        db.session.add(user_recipe)

        # Commit changes
        db.session.commit()

        print("Recipe saved successfully")
        # Return success response
        return jsonify({'success': True, 'message': 'Recipe saved successfully!'})

    except Exception as e:
        logging.error(f"Error saving recipe: {e}")
        print(f"Error saving recipe: {e}")  # Print the error message to the console
        db.session.rollback()  # Rollback on errors
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500    
    
def get_age_group(age):
    if 11 <= age <= 14:
        return "11-14 years"
    elif 15 <= age <= 18:
        return "15-18 years"
    elif 19 <= age <= 50:
        return "19-50 years"
    else:
        return "50+ years"

if __name__ == '__main__':
    app.run(debug=True)