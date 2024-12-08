from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Recipe
from db_utils import get_saved_recipes, add_recipe_to_calendar

# Define a Blueprint
routes = Blueprint('routes', __name__)

@routes.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@routes.route('/get_saved_recipes')
@login_required
def get_saved_recipes_route():
    # Fetch saved recipes using the utility function
    user_recipes = get_saved_recipes(current_user.id)
    saved_recipes = [
        {
            'id': ur.recipe.id,
            'label': ur.recipe.label,
            'date': ur.date,
            'meal_type': ur.meal_type
        }
        for ur in user_recipes
    ]
    return jsonify(saved_recipes)

@routes.route('/add_recipe_to_calendar', methods=['POST'])
@login_required
def add_recipe_to_calendar_route():
    data = request.form
    recipe_id = data.get('recipe_id')
    date = data.get('date')

    if not recipe_id or not date:
        return jsonify({'success': False, 'message': 'Invalid input'}), 400

    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'success': False, 'message': 'Recipe not found'}), 404

    add_recipe_to_calendar(current_user.id, recipe.id, date)  # Use utility function

    return jsonify({'success': True, 'message': 'Recipe added to calendar'})

