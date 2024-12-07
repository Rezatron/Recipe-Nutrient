from flask_admin.actions import action
from flask import request, Flask
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from models import db, User, Recipe, Nutrient, RecipeNutrient, UserRecipe

class MyModelView(ModelView):
    can_delete = True  # Enable deletion
    can_create = False  # Disable creation if not needed
    can_edit = False  # Disable editing if not needed
    column_display_pk = True  # Display primary keys in the list view

    def is_accessible(self):
        # Add your authentication logic here
        return True
    
    @action('delete_selected', 'Delete Selected', 'Are you sure you want to delete selected records?')
    def action_delete_selected(self, ids):
        try:
            # Delete the selected records in bulk
            ids = [int(i) for i in ids]
            records = self.session.query(self.model).filter(self.model.id.in_(ids)).all()
            for record in records:
                self.session.delete(record)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            return str(e)

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
