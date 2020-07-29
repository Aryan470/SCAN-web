from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin
from firebase_admin.auth import verify_id_token
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
        verified_dict = verify_id_token(idToken)
        uid = verified_dict["uid"]
    except:
        abort(400, "Invalid ID token")
    
    session["uid"] = uid
    session["name"] = "Click to setup profile"
    try:
        session["name"] = fireClient.collection("users").document(uid).get().to_dict()["name"]
    except:
        return redirect(url_for("bakesale.edit_profile"))
    print(request.json)
    if "redirect" in request.json:
        return redirect(url_for(request.json["redirect"]))
    else:
        print("NO REDIRECT")
        return redirect(url_for("bakesale.index"))

@auth.route("/logout", methods=["GET"])
def logout():
    if "uid" in session:
        session.pop("uid")
    if "name" in session:
        session.pop("name")
    return redirect(url_for("bakesale.index"))
