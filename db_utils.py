from models import db, User, Recipe, UserRecipe, Nutrient, RecipeNutrient
from units import nutrient_units

def add_recipe_to_user(user_id, recipe_data, date, meal_type):
    recipe = Recipe.query.filter_by(label=recipe_data['label']).first()
    if not recipe:
        recipe = Recipe(
            label=recipe_data['label'],
            ingredients=recipe_data['ingredients'],
            url=recipe_data['url'],
            image=recipe_data['image'],
            calories_per_serving=recipe_data['calories_per_serving'],
            yield_value=recipe_data['yield']
        )
        db.session.add(recipe)
        db.session.commit()

        # Add nutrients to the recipe
        for nutrient_name, amount in recipe_data['micro_nutrients_per_serving'].items():
            nutrient = Nutrient.query.filter_by(name=nutrient_name).first()
            if not nutrient:
                nutrient = Nutrient(name=nutrient_name, unit=nutrient_units[nutrient_name])
                db.session.add(nutrient)
                db.session.commit()

            recipe_nutrient = RecipeNutrient(recipe_id=recipe.id, nutrient_id=nutrient.id, amount_per_serving=amount)
            db.session.add(recipe_nutrient)
            db.session.commit()

    user_recipe = UserRecipe(user_id=user_id, recipe_id=recipe.id, date=date, meal_type=meal_type)
    db.session.add(user_recipe)
    db.session.commit()

def get_saved_recipes(user_id):
    return UserRecipe.query.filter_by(user_id=user_id).all()

def add_recipe_to_calendar(user_id, recipe_id, date):
    user_recipe = UserRecipe(user_id=user_id, recipe_id=recipe_id, date=date)
    db.session.add(user_recipe)
    db.session.commit()