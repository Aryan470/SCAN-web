import random
from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin.auth as firebase_auth
import firebase_admin.firestore as firestore
from scan_web import fireClient
from datetime import datetime

sms = Blueprint("sms", __name__, template_folder="sms_templates")

ambassador_uids = [ambassador.id for ambassador in fireClient.collection("users").where("tier", "==", "ambassador").stream()]
officer_uids = [officer.id for officer in fireClient.collection("users").where("tier", "==", "officer").stream()]
director_uids = [director.id for director in fireClient.collection("users").where("tier", "==", "director").stream()]

@sms.route("/")
def index():
    return redirect(url_for("sms.view_messages"))

@sms.route("/messages")
def view_messages():
    if "uid" not in session:
        return redirect(url_for("auth.login", redirect=url_for("sms.view_messages")))
    
    my_messages = {message.id: message.to_dict() for message in fireClient.collection("messages").where("sender", "==", session["uid"]).where("sent", "==", False).stream()}
    return render_template("messages.html", messages=my_messages)


access_property = {
    "FIRSTNAME": lambda user, ctx: user.display_name.split()[0],
    "LASTNAME": lambda user, ctx: user.display_name.split()[-1],
    "EMAIL": lambda user, ctx: user.email,
    "PHONE": lambda user, ctx: user.phone_number,
    "INDIVIDUAL_SALES": lambda user, ctx: "$%0.2f" % (ctx["leaderboard"].get(access_property["FIRSTNAME"](user, ctx).lower() + "_" + access_property["LASTNAME"](user, ctx).lower(), 0))
}

def render_message(template, user, ctx):
    property_values = {property_name: access_property[property_name](user, ctx) for property_name in access_property}
    for property_name in property_values:
        template = template.replace("[" + property_name + "]", property_values[property_name])
    return template
    

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
    num_errors = 0
    error_threshold = 0.05
    ctx = {
        "leaderboard": fireClient.collection("statistics").document("sales").get().get("leaderboard")
    }
    for uid in template["recipients"]:
        # If the error rate for message generation exceeds 5%, stop it
        if num_errors / len(template["recipients"]) > error_threshold:
            break
        try:
            msg_ref = fireClient.collection("messages").document()
            user = firebase_auth.get_user(uid)
            msg = {
                "content": render_message(template["template"], user, ctx),
                "sender": random.choice(officer_uids),
                "recipient": uid,
                "phone": user.phone_number,
                "sent": False,
                "template_id": template_id
            }
            new_messages_batch.set(msg_ref, msg)
        except:
            num_errors += 1
    if num_errors / len(template["recipients"]) > error_threshold:
        abort(400, "The error rate for generating messages exceeded %0.2f%%, generation cancelled" % (100 * error_threshold))
    else:
        new_messages_batch.commit()
        template["generated"] = True
        template_ref.set(template)
        return redirect(url_for("sms.view_template", template_id=template_obj.id))


@sms.route("/createtemplate", methods=["GET", "POST"])
def create_template():
    if "user" not in session or "uid" not in session["user"]:
        return redirect(url_for("auth.login", redirect=url_for("sms.create_template")))
    user_obj = fireClient.collection("users").document(session["uid"]).get()
    if not user_obj.exists or user_obj.to_dict().get("tier", "") != "director":
        abort(401)
    if request.method == "GET":
        return render_template("create_template.html", available_data=access_property)
    template = {
        "template": request.form["template"],
        "author": {
            "uid": session["user"]["uid"],
            "name": session["user"]["display_name"]
        },
        "generated": False,
        "recipients": {user.uid: False for user in firebase_auth.list_users().iterate_all() if user.uid not in director_uids},
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

@sms.route("/marksent", methods=["POST"])
def mark_sent():
    sent_messages = request.form.getlist("sent")
    if len(sent_messages) < 1:
        return redirect(url_for("sms.view_messages"))
    for message_id in sent_messages:
        message_ref = fireClient.collection("messages").document(message_id)
        message_obj = message_ref.get()
        if not message_obj.exists:
            continue
        message = message_obj.to_dict()
        message["sent"] = True
        message_ref.set(message)

        template_ref = fireClient.collection("message_templates").document(message["template_id"])
        template_obj = template_ref.get()
        if not template_obj.exists:
            continue
        template = template_obj.to_dict()
        template["recipients"][message["recipient"]] = True
        template_ref.set(template)
    
    return redirect(url_for("sms.view_messages"))
