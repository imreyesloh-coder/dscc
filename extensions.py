from flask import current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per hour"],
    storage_uri="memory://",
)

ai_limit = limiter.shared_limit(lambda: current_app.config["AI_RATE_LIMIT"], scope="claude-api")
