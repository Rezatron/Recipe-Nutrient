from models import db, UserRecipe

def get_saved_recipes(user_id):
    # Fetch saved recipes for the user from UserRecipe
    return UserRecipe.query.filter_by(user_id=user_id).all()

def add_recipe_to_calendar(user_id, recipe_id, date):
    # Add recipe to the user's calendar
    user_recipe = UserRecipe(user_id=user_id, recipe_id=recipe_id, date=date)
    db.session.add(user_recipe)
    db.session.commit()
