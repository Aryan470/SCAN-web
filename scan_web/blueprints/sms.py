from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin
from firebase_admin.auth import verify_id_token
from datetime import datetime
from uuid import uuid4
from scan_web import fireClient
from uuid import uuid4

sms = Blueprint("sms", __name__, template_folder="sms_templates")

@sms.route("/")
def index():
    return redirect("sms.view_messages")

def view_messages():
    if "uid" not in session:
        return redirect("auth.login")
    
    my_messages = [message.to_dict() for message in fireClient.collection("messages").where("sender", "==", session["uid"]).stream()]
    return render_template("messages.html", messages=my_messages)
