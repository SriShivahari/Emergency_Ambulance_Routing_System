from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    CORS(app)

    from app.routes.routing import routing_bp
    from app.routes.ml_api import ml_bp

    app.register_blueprint(routing_bp)
    app.register_blueprint(ml_bp)

    return app