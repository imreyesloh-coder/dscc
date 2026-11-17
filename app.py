from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import limiter
from models import db
from routes import api
from seed import seed_demo_data
from ui_routes import ui


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    limiter.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"])
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(ui, url_prefix="/api")

    @app.errorhandler(429)
    def too_many_requests(_error):
        return jsonify({"error": "Too many requests. Please wait a bit and try again."}), 429

    with app.app_context():
        db.create_all()
        seed_demo_data()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
