from __future__ import annotations

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from indigo.config.settings import get_settings
from indigo.util.logging import configure_logging
from indigo.api.blueprints.health import bp as health_bp


def create_app() -> Flask:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Store settings on app config so blueprints can access
    app.config["INDIGO_SETTINGS"] = settings

    # Register API blueprints
    app.register_blueprint(health_bp)

    # UI mounting will be added later (ENABLE_UI gate + assets exist)

    return app


def run_dev() -> None:
    """
    Convenience entrypoint for local development.
    """
    app = create_app()
    settings = app.config["INDIGO_SETTINGS"]
    app.run(host=settings.host, port=settings.port, debug=True)
