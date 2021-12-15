from itsdangerous import URLSafeTimedSerializer

from flask import current_app as app

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])