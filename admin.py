from flask import Flask, flash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import db, User, Recipe, Nutrient, RecipeNutrient, UserRecipe
from flask_admin.actions import action

class MyModelView(ModelView):
    can_delete = True
    can_create = False
    can_edit = False
    column_display_pk = True

    def is_accessible(self):
        return True

    def delete_model(self, model):
        try:
            # Perform the deletion like in action_delete_selected
            if isinstance(model, Recipe):
                # Delete the recipe first
                self.session.delete(model)
                self.session.commit()

                # Now check and delete orphaned nutrients (similar to bulk delete)
                self._delete_orphaned_nutrients()

            flash('Record was successfully deleted.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to delete record: {str(ex)}', 'error')
            self.session.rollback()

    def _delete_orphaned_nutrients(self):
        # This function removes nutrients that are not linked to any recipe
        unreferenced_nutrients = db.session.query(Nutrient).outerjoin(RecipeNutrient).filter(RecipeNutrient.id == None).all()
        for nutrient in unreferenced_nutrients:
            db.session.delete(nutrient)
        db.session.commit()

    @action('delete_selected', 'Delete Selected', 'Are you sure you want to delete selected records?')
    def action_delete_selected(self, ids):
        try:
            ids = [int(i) for i in ids]
            records = self.session.query(self.model).filter(self.model.id.in_(ids)).all()
            for record in records:
                self.session.delete(record)
            self.session.commit()

            # Ensure orphaned nutrients are also deleted for the bulk deletion
            self._delete_orphaned_nutrients()

            flash('Records were successfully deleted.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to delete records. {str(ex)}', 'error')
            self.session.rollback()

def create_admin(app):
    admin = Admin(app, name='Admin', template_mode='bootstrap3')
    admin.add_view(MyModelView(User, db.session))
    admin.add_view(MyModelView(Recipe, db.session))
    admin.add_view(MyModelView(Nutrient, db.session))
    admin.add_view(MyModelView(RecipeNutrient, db.session))
    admin.add_view(MyModelView(UserRecipe, db.session))
