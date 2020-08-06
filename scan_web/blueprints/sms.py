import random
from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin.auth as firebase_auth
import firebase_admin.firestore as firestore
from scan_web import fireClient
from datetime import datetime

sms = Blueprint("sms", __name__, template_folder="sms_templates")

ambassador_uids = [officer.to_dict()["uid"] for officer in fireClient.collection("users").where("tier", "==", "ambassador").stream()]
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

def render_message(template, user):
    property_values = {property_name: access_property[property_name](user) for property_name in access_property}
    for property_name in property_values:
        template.replace(property_name, property_values[property_name])
    

@sms.route("/generatetemplate/<template_id>", methods=["POST"])
def generate_template(template_id):
    template_ref = fireClient.collection("message_templates").document(template_id)
    template_obj = template_ref.get()
    if not template_obj.exists:
        abort(404, "Template not found")
    template = template_obj.to_dict()
    if template["generated"]:
        abort(410, "Template's messages have already been generated")
    new_messages_batch = fireClient.batch()
    for uid in template["recipients"]:
        try:
            msg_ref = fireClient.collection("messages").document()
            user = firebase_auth.get_user(uid)
            msg = {
                "content": render_message(template["template"], user),
                "sender": random.choice(officer_uids),
                "phone": user.phone_number
            }
            new_messages_batch.set(msg_ref, msg)
    new_messages_batch.commit()


@sms.route("/createtemplate", methods=["GET", "POST"])
def create_template():
    if "uid" not in session:
        return redirect(url_for("auth.login", redirect="sms.create_message"))
    user_obj = fireClient.collection("users").document(session["uid"]).get()
    if not user_obj.exists or user_obj.to_dict().get("tier", "") != "officer":
        abort(401)
    if request.method == "GET":
        return render_template("create_template.html", available_data=access_property)
    template = {
        "template": request.form["template"],
        "author": {
            "uid": session["uid"],
            "name": session["name"]
        },
        "generated": False,
        "recipients": {user.uid: False for user in firebase_auth.list_users().iterate_all() if user.uid not in officer_uids and user.uid not in ambassador_uids},
        "UTC_timestamp": str(datetime.utcnow())
    }
    template_obj = fireClient.collection("message_templates").document()
    fireClient.collection("message_templates").document(template_obj.id).set(template)
    return redirect(url_for("sms.view_template", template_id=template_obj.id))

@sms.route("/viewtemplates")
def view_templates():
    message_templates = [template for template in fireClient.collection("message_templates").order_by("UTC_timestamp", direction=firestore.Query.DESCENDING).stream()]
    return render_template("view_templates.html", templates=message_templates)

@sms.route("/viewtemplate/<template_id>")
def view_template(template_id):
    template_ref = fireClient.collection("message_templates").document(template_id)
    template_obj = template_ref.get()
    if not template_obj.exists:
        abort(404, "Template not found")
    return render_template("view_template.html", template=template_obj.to_dict(), template_obj=template_obj)