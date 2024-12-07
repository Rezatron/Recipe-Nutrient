from flask import Flask, flash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from models import db, User, Recipe, Nutrient, RecipeNutrient, UserRecipe

class MyModelView(ModelView):
    can_delete = True
    can_create = False
    can_edit = False
    column_display_pk = True

    def is_accessible(self):
        return True

    def delete_model(self, model):
        try:
            # Custom logic to delete orphaned Nutrient records when a Recipe is deleted
            if isinstance(model, Recipe):  # Check if it's a Recipe being deleted
                self._delete_orphaned_nutrients()  # Delete orphaned nutrients related to the recipe
            
            # Proceed with the normal deletion
            self.session.delete(model)
            self.session.commit()
            flash('Record was successfully deleted.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to delete record: {str(ex)}', 'error')
            self.session.rollback()

    def _delete_orphaned_nutrients(self):
        # Clean up orphaned Nutrient records that are no longer linked to any RecipeNutrient
        unreferenced_nutrients = db.session.query(Nutrient).outerjoin(RecipeNutrient).filter(RecipeNutrient.id == None).all()
        for nutrient in unreferenced_nutrients:
            db.session.delete(nutrient)
        db.session.commit()

def create_admin(app):
    admin = Admin(app, name='Admin', template_mode='bootstrap3')
    admin.add_view(MyModelView(User, db.session))
    admin.add_view(MyModelView(Recipe, db.session))
    admin.add_view(MyModelView(Nutrient, db.session))
    admin.add_view(MyModelView(RecipeNutrient, db.session))
    admin.add_view(MyModelView(UserRecipe, db.session))

if __name__ == '__main__':
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
    app.config['SECRET_KEY'] = 'your_secret_key'
    db.init_app(app)
    create_admin(app)
    app.run(debug=True)
