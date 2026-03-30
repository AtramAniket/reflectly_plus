from flask import Flask
from .extensions import db, login_manager, migrate

def create_app():

    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)


    from .routes.auth import auth
    from .routes.routes import main
    from .routes.journal import journal

    from .models.user import User
    from .models.journal import JournalEntry
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(journal)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app