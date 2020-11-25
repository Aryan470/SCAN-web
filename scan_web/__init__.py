from firebase_admin import credentials, firestore
import firebase_admin
import os
import json

cred = credentials.Certificate(json.loads(os.environ["PROJECT_AUTH"]))
firebase_admin.initialize_app(cred)
fireClient = firestore.client()

from flask import Flask, render_template, session, redirect, request, url_for
from scan_web.blueprints import bakesale, auth, sms, info
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
        
    @app.route("/tutoring")
    def tutoring_sheet_link():
        return redirect("https://docs.google.com/forms/d/e/1FAIpQLScBZWUHSAlzsarJKmxUgpK3Dc82Gt9vHFT3AonDk6Jr3hGx9g/viewform?usp=sf_link")
    
    @app.route("/xmas")
    def goodie_bag_volunteering_link():
        return redirect("https://docs.google.com/forms/d/e/1FAIpQLSe1izY7BgiuTWL9Pg8TW0kwMR59V85yLm4dYUXqd9xKCPqlqQ/viewform?usp=sf_link")

    if os.environ["CONTEXT"] == "PROD":
        app.register_blueprint(auth.auth, subdomain="auth")
        app.register_blueprint(sms.sms, subdomain="sms")
        app.register_blueprint(info.info, subdomain="info")
    app.register_blueprint(bakesale.bakesale, url_prefix="/bakesale")
    app.register_blueprint(auth.auth, url_prefix="/auth")
    app.register_blueprint(sms.sms, url_prefix="/sms")
    app.register_blueprint(info.info, url_prefix="/info")
    
    return app
