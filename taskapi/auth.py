import os
from functools import wraps

from flask import jsonify, request

# Was hardcoded; pulled from the environment so it isn't the same
# value in every deployment.
API_KEY = os.environ.get("TASKAPI_KEY", "dev-local-only-key")


def require_api_key(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if request.headers.get("X-Api-Key") != API_KEY:
            return jsonify({"error": "unauthorized"}), 401
        return view(*args, **kwargs)

    return wrapped
