from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    sex = db.Column(db.String(10))
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)
    recipes = db.relationship('UserRecipe', backref='user', lazy=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(150), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(300))
    image = db.Column(db.String(300))
    calories_per_serving = db.Column(db.Float)
    yield_value = db.Column(db.Float)
    user_recipes = db.relationship('UserRecipe', backref='recipe', lazy=True)
    nutrients = db.relationship('RecipeNutrient', backref='recipe', lazy=True)

class Nutrient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    unit = db.Column(db.String(50), nullable=False)

class RecipeNutrient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    nutrient_id = db.Column(db.Integer, db.ForeignKey('nutrient.id'), nullable=False)
    amount_per_serving = db.Column(db.Float, nullable=False)

class UserRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)  # e.g., breakfast, lunch, dinner, snack