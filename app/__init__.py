from flask import Flask
from .extensions import db, login_manager, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from .routes.routes import main
    from .models.user import User
    app.register_blueprint(main)

    return app