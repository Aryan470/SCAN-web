from firebase_admin import credentials, firestore
import firebase_admin
import os
import json

cred = credentials.Certificate(json.loads(os.environ["PROJECT_AUTH"]))
firebase_admin.initialize_app(cred)
fireClient = firestore.client()

from flask import Flask, render_template, session, redirect, request, url_for
from scan_web.blueprints import bakesale, auth, sms
# from scan_web import product_management

def create_app():
    app = Flask(__name__)
    app.config["PREFERRED_URL_SCHEME"] = "https"
    if os.environ["CONTEXT"] == "PROD":
        app.config["SERVER_NAME"] = "sicklecellawareness.net"
    if "SECRET_KEY" in os.environ:
        app.secret_key = os.environ["SECRET_KEY"]
    else:
        app.secret_key = "DEVELOPMENT"

    app.register_blueprint(bakesale.bakesale, subdomain="bakesale")
    app.register_blueprint(bakesale.bakesale, url_prefix="/bakesale")
    app.register_blueprint(auth.auth, url_prefix="/auth")
    app.register_blueprint(sms.sms, url_prefix="/sms")

    @app.route("/")
    def index():
        return redirect(url_for("bakesale.index"))
    
    return app
