import random
from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin.auth as firebase_auth
from scan_web import fireClient

sms = Blueprint("sms", __name__, template_folder="sms_templates")

officer_uids = [officer.to_dict()["uid"] for officer in fireClient.collection("users").where("tier", "==", "officer").stream()]

@sms.route("/")
def index():
    return redirect(url_for("sms.view_messages"))

@sms.route("/messages")
def view_messages():
    if "uid" not in session:
        return redirect(url_for("auth.login", redirect="sms.view_messages"))
    
    my_messages = [message.to_dict() for message in fireClient.collection("messages").where("sender", "==", session["uid"]).stream()]
    return render_template("messages.html", messages=my_messages)


access_property = {
    "FIRSTNAME": lambda user: user.display_name.split()[0],
    "LASTNAME": lambda user: user.display_name.split()[1],
    "EMAIL": lambda user: user.email,
    "PHONE": lambda user: user.phone_number
}

# find bracketed content, check to see if it exists in access_property, substitute
def render_message(template, user):
    properties = {property_name: access_property[property_name](user) for property_name in access_property}
    for property_name in properties:
        template.replace(property_name, properties[property_name])
    


@sms.route("/createmessage", methods=["GET", "POST"])
def create_message():
    if "uid" not in session:
        return redirect(url_for("auth.login", redirect="sms.create_message"))
    user_obj = fireClient.collection("users").document(session["uid"]).get()
    if not user_obj.exists or user_obj.to_dict().get("tier", "") != "officer":
        abort(401)
    if request.method == "GET":
        return render_template("create_message.html", available_data=access_property)
    template = request.form["template"]
    for user in firebase_auth.list_users().iterate_all():
        fireClient.collection("messages").add(render_message(template, user))