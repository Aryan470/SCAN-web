from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
from scan_web import fireClient

sms = Blueprint("sms", __name__, template_folder="sms_templates")

@sms.route("/")
def index():
    return redirect(url_for("sms.view_messages"))

@sms.route("/messages")
def view_messages():
    if "uid" not in session:
        return redirect(url_for("auth.login", redirect="sms.view_messages"))
    
    my_messages = [message.to_dict() for message in fireClient.collection("messages").where("sender", "==", session["uid"]).stream()]
    return render_template("messages.html", messages=my_messages)
