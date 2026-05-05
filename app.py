"""app.py — Flask application factory."""
from flask import Flask
from config import Config
from routes.public import threaded_function

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY
    threaded_function() # Call the manager function to handle the installation process
    from routes.public  import public_bp
    from routes.members import members_bp
    from routes.admin   import admin_bp
    from routes.api     import api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(members_bp, url_prefix="/members")
    app.register_blueprint(admin_bp,   url_prefix="/admin")
    app.register_blueprint(api_bp,     url_prefix="/api")

    return app


if __name__ == "__main__":
    create_app().run(debug=Config.DEBUG, port=5000)