from firebase_admin import credentials, firestore
import firebase_admin
import os
import json

cred = credentials.Certificate(json.loads(os.environ["PROJECT_AUTH"]))
firebase_admin.initialize_app(cred)
fireClient = firestore.client()

from flask import Flask, render_template, session, redirect, request, url_for
from scan_web.blueprints import bakesale, auth

def create_app(port):
    app = Flask(__name__)
    app.config["PREFERRED_URL_SCHEME"] = "https"
    if "SECRET_KEY" in os.environ:
        app.secret_key = os.environ["SECRET_KEY"]
    else:
        app.secret_key = "DEVELOPMENT"

    app.register_blueprint(bakesale.bakesale, url_prefix="/bakesale")
    app.register_blueprint(auth.auth, url_prefix="/auth")

    @app.route("/")
    def index():
        return redirect(url_for("bakesale.index"))
    
    return app