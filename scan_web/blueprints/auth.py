from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin
import firebase_admin.auth as firebase_auth
from datetime import datetime
from uuid import uuid4
from scan_web import fireClient
from uuid import uuid4

auth = Blueprint("auth", __name__, template_folder="auth_templates")

def serialize_userrecord(record: firebase_auth.UserRecord):
    return {
        "uid": record.uid,
        "photo_url": record.photo_url,
        "phone_number": record.phone_number,
        "email_verified": record.email_verified,
        "email": record.email,
        "display_name": record.display_name,
        "disabled": record.disabled,
        "custom_claims": record.custom_claims,
    }

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "redirect" in request.args:
            return render_template("login.html", redirect=request.args.get("redirect"))
        return render_template("login.html")
    
    try:
        idToken = request.json["idToken"]
    except KeyError:
        abort(400, "Request must include id token from login page")
    
    try:
        verified_dict = firebase_auth.verify_id_token(idToken)
        uid = verified_dict["uid"]
    except:
        abort(400, "Invalid ID token")
    
    session["uid"] = uid
    user_info = firebase_auth.get_user(uid)
    session["user"] = serialize_userrecord(user_info)

    print(session)
    if user_info.display_name:
        session["name"] = user_info.display_name
    else:
        session["name"] = "Click to setup profile"

    if "redirect" in request.json:
        return redirect(request.json["redirect"])
    else:
        return redirect(url_for("bakesale.index"))

@auth.route("/logout", methods=["GET"])
def logout():
    if "uid" in session:
        session.pop("uid")
    if "name" in session:
        session.pop("name")
    return redirect(url_for("bakesale.index"))

@auth.route("/createuser", methods=["POST"])
def create_user():
    if not request.form:
        abort(400, "Request must include form data")
    try:
        new_user = {
            "email": request.form["email"],
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "grade": request.form["grade"],
            "school": request.form["school"],
            "phone": request.form["phone"]
        }
    except:
        abort(400, "Malformed form data")
    if not new_user["phone"]:
        new_user.pop("phone")
    elif "+" not in new_user["phone"]:
        new_user["phone"] = "+1" + new_user["phone"]
    
    try:
        firebase_user = firebase_auth.create_user(
            email=new_user["email"],
            email_verified=False,
            phone_number=new_user.get("phone", None),
            password="members not allowed",
            display_name=str("%s %s" % (new_user["first_name"], new_user["last_name"]))
        )

        user_ref = fireClient.collection("users").document(firebase_user.uid)
        user_ref.set({
                "name_array": firebase_user.display_name.lower().split(),
                "tier": "member"
        })
    except BaseException as e:
        abort(400, "User could not be created: %s" % str(e))
    return {"success": True}
