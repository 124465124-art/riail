"""Start Riail:  python app.py   then open http://127.0.0.1:5000"""

from flask import Flask

from riail.config import Config
from riail.gateway.routes import create_gateway
from riail.wiring import build_query_service


def create_app(config: Config | None = None, **overrides) -> Flask:
    """Build the app. Tests pass `store=` and `answerer=` overrides to avoid the real model and AI."""
    config = config or Config.from_env()
    query, feedback = build_query_service(config, **overrides)
    app = Flask(__name__)
    app.json.sort_keys = False
    app.register_blueprint(create_gateway(query, feedback, config.max_question_length))
    return app


if __name__ == "__main__":
    create_app().run(debug=False)
