from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin
import firebase_admin.auth as firebase_auth
from datetime import datetime
from uuid import uuid4
from scan_web import fireClient
from uuid import uuid4

auth = Blueprint("auth", __name__, template_folder="auth_templates")

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
        new_user.pop("pheon")
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
    except BaseException as e:
        abort(400, "User could not be created: %s" % str(e))
    return {"success": True}

@auth.route("/editprofile", methods=["GET", "POST"])
def edit_profile():
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    uid = session["uid"]
    user = firebase_auth.get_user(session["uid"])
    if request.method == "GET":
        return render_template("edit_profile.html", user=user)
    
    try:
        if session["uid"] != request.form["uid"]:
            abort(400, "UID does not match session")
        phone = ''.join(c for c in request.form["phone"] if c.isdigit() or c == '+')
        if "+" not in phone:
            phone = "+1" + phone
        firebase_auth.update_user(
            uid=session["uid"],
            display_name=request.form["name"],
            email=request.form["email"],
            phone_number=phone
        )
    except Exception as e:
        abort(400, "Malformed edit profile request: " + str(e))
        
    return redirect(url_for("auth.view_profile", uid=session["uid"]))


@auth.route("/profile/<uid>", methods=["GET"])
def view_profile(uid):
    try:
        user = firebase_auth.get_user(uid)
    except:
        abort(404, "User not found")

    return render_template("view_profile.html", user=user)