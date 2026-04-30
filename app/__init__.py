from flask import Flask
from .extensions import db, login_manager, migrate, csrf

def create_app():

    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from .routes.auth import auth
    from .routes.beta import demo
    from .routes.routes import main
    from .routes.habit import habit
    from .routes.tools import tools
    from .routes.insight import insight
    from .routes.journal import journal

    from .models.user import User
    from .models.habit import Habit
    from .models.habit_log import HabitLog
    from .models.journal import JournalEntry
    from .models.weekly_insight import WeeklyInsight
    from .models.mood_checklist import MoodChecklistResult
    from .models.journal_ai_analysis import JournalAIAnalysis
    from .models.procrastination_sheet import ProcrastinationSheet
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(demo)
    app.register_blueprint(habit)
    app.register_blueprint(tools)
    app.register_blueprint(journal)
    app.register_blueprint(insight)

    # CLI command for Render Cron / manual scheduled generation
    from .helper.weekly_insights_helper import generate_previous_weekly_insights_for_all_users

    @app.cli.command("generate-weekly-insights")
    def generate_weekly_insights_command():
        """Generate weekly insights for the completed previous week."""
        results = generate_previous_weekly_insights_for_all_users()
        print("Weekly insights generation complete")
        print(results)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app