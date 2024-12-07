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
    recipes = db.relationship('UserRecipe', backref='user', lazy=True, cascade="all, delete-orphan")

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(150), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    ingredient_lines = db.Column(db.Text, nullable=False)  # New field
    url = db.Column(db.Text)
    image = db.Column(db.Text)
    calories_per_serving = db.Column(db.Float)
    yield_value = db.Column(db.Float)
    micro_nutrients_per_serving = db.Column(db.JSON)  # New field
    nutrient_units = db.Column(db.JSON)  # New field
    comparison_to_rni = db.Column(db.JSON)  # New field
    user_recipes = db.relationship('UserRecipe', backref='recipe', lazy=True, cascade="all, delete-orphan")
    recipe_nutrients = db.relationship('RecipeNutrient', backref='recipe', lazy=True, cascade="all, delete-orphan")


class Nutrient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    recipe_nutrients = db.relationship('RecipeNutrient', backref='nutrient', lazy=True, cascade="all, delete-orphan")

class RecipeNutrient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id', ondelete='CASCADE'), nullable=False)
    nutrient_id = db.Column(db.Integer, db.ForeignKey('nutrient.id', ondelete='CASCADE'), nullable=False)
    amount_per_serving = db.Column(db.Float, nullable=False)

class UserRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)