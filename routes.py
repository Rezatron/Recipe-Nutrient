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
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

logging.basicConfig(level=logging.INFO)
load_dotenv()

SEARCH_LIMIT = 1
TIME_WINDOW = 5
micro_nutrients_per_serving = {}
search_counts = {}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    sex = db.Column(db.String(10))
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    label = db.Column(db.String(150), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(300))
    image = db.Column(db.String(300))
    calories_per_serving = db.Column(db.Float)
    micro_nutrients_per_serving = db.Column(db.PickleType)
    nutrient_units = db.Column(db.PickleType)
    yield_value = db.Column(db.Float)
    comparison_to_rni = db.Column(db.PickleType)
    date = db.Column(db.Date, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
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
    # search filters
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
        sorted_recipes = sorted(edamam_recipes['hits'], key=lambda x: len(set(x['recipe']['ingredientLines']) - set(ingredients.split(','))))

        # Take only the required number of recipes to show
        sorted_recipes = sorted_recipes[:max_recipes_to_show]

        filtered_recipes = []

        for hit in sorted_recipes:
            recipe = hit['recipe']
            label = recipe['label']
            ingredient_lines = recipe['ingredientLines']
            url = recipe.get('url')
            image = recipe.get('image')
            calories = recipe.get('calories')
            micro_nutrients = recipe.get('totalNutrients', {})
            yield_value = recipe.get('yield', None)

            cleaned_micro_nutrients = clean_micro_nutrients(micro_nutrients)
            calories_per_serving = calories / yield_value

            micro_nutrients_per_serving = {}
            for nutrient_label, nutrient_value in cleaned_micro_nutrients.items():
                if nutrient_label != 'Water':  # Excluding
                    micro_nutrients_per_serving[nutrient_label] = nutrient_value / yield_value

            print(f"Micro Nutrients per Serving: {micro_nutrients_per_serving}")

            comparison_to_rni = calculate_comparison_to_rni(micro_nutrients_per_serving)
            print(f"Comparison to RNI: {comparison_to_rni}")

            filtered_recipes.append({
                'label': label,
                'ingredient_lines': ingredient_lines,
                'ingredients': ingredients,
                'url': url,
                'image': image,
                'calories_per_serving': calories_per_serving,
                'micro_nutrients_per_serving': micro_nutrients_per_serving,
                'nutrient_units': nutrient_units,
                'yield': yield_value,
                'comparison_to_rni': comparison_to_rni
            })

        return filtered_recipes, 200

    except requests.RequestException as e:
        logging.error(f'Error fetching recipes: {e}')
        return {'error': f'Network Error: {e}'}, 500
    except Exception as e:
        logging.error(f'Error processing recipes: {e}')
        return {'error': 'Failed to process recipes'}, 500

    except requests.RequestException as e:
        logging.error(f'Error fetching recipes: {e}')
        return jsonify({'error': f'Network Error: {e}'}), 500
    except Exception as e:
        logging.error(f'Error processing recipes: {e}')
        return jsonify({'error': 'Failed to process recipes'}), 500

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
                            print(f"Calculated RNI for {nutrient_label}: {comparison_to_rni[nutrient_label]}%")
        elif sex.lower() == 'female':
            if age_group in rni_data["Micronutrients"]["Females"]:
                global_rni = rni_data["Micronutrients"]["Females"][age_group]
                if global_rni:
                    for nutrient_label, nutrient_value in micro_nutrients_per_serving.items():
                        if nutrient_label in global_rni:
                            comparison_to_rni[nutrient_label] = nutrient_value / global_rni[nutrient_label] * 100
                            print(f"Calculated RNI for {nutrient_label}: {comparison_to_rni[nutrient_label]}%")

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

@app.route('/fetch_recipes', methods=['POST'])
@login_required
def fetch_recipes():
    ingredients = request.form['ingredients']
    recipes, status_code = fetch_recipes_logic(ingredients)
    if status_code == 200:
        return render_template('dashboard.html', user=current_user, recipes=recipes)
    else:
        flash(recipes['error'], 'danger')
        return redirect(url_for('dashboard'))
    
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

def get_saved_recipes(user_id):
    # Implement logic to fetch saved recipes for the user
    # This is a placeholder function and should be implemented with actual logic
    return []

@app.route('/add_recipe', methods=['POST'])
@login_required
def add_recipe():
    recipe_id = request.form['recipe_id']
    date = request.form['date']
    # Add recipe to calendar logic here
    add_recipe_to_calendar(current_user.id, recipe_id, date)
    return redirect(url_for('dashboard'))

def add_recipe_to_calendar(user_id, recipe_id, date):
    # Implement logic to add the recipe to the calendar
    # This is a placeholder function and should be implemented with actual logic
    pass

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