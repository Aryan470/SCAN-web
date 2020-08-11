from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin.auth as firebase_auth
import firebase_admin.firestore as firestore
from scan_web import fireClient

info = Blueprint("info", __name__, template_folder="info_templates")

director_titles = {
    "chairman": "Chairman of the Board",
    "vice_chairman": "Vice Chairman of the Board",
    "finance": "Director of Finance",
    "publicity": "Director of Publicity",
    "operations": "Director of Operations",
    "communications": "Director of Communications",
}

officer_titles = {
    "communications": "Communications Officer",
    "publicity": "Publicity Officer",
    "executive": "Executive Officer",
    "finance": "Financial Officer",
    "operations": "Operations Officer"
}

director_roles = [
    "communications",
    "publicity",
    "chairman",
    "vice_chairman",
    "finance",
    "operations"
]

officer_roles = [
    "communications",
    "publicity",
    "executive",
    "finance",
    "operations"
]

user_lookup_methods = {
    "phone": lambda phone: [firebase_auth.get_user_by_phone_number(phone if "+" in phone else "+1" + phone)],
    "email": lambda email: [firebase_auth.get_user_by_email(email)],
    "name": lambda name: [firebase_auth.get_user(user.id) for user in fireClient.collection("users").where("name_array", "array_contains_any", name.lower().split()).stream()]
}

def is_verified(uid):
    try:
        firebase_auth.get_user(uid)
    except:
        return False
    try:
        return fireClient.collection("users").document(uid).get().get("tier") == "director"
    except:
        return False

@info.route("/")
def index():
    return redirect(url_for("info.display_directory"))

@info.route("/directory")
def display_directory():
    directory_ref = fireClient.collection("info").document("directory")
    directory = directory_ref.get().to_dict()
    directors = [(firebase_auth.get_user(directory["directors"][role]), role) for role in director_roles if role in directory["directors"]]
    chapters_dict = fireClient.collection("info").document("chapter_info").get().to_dict()["chapters"]
    chapters = sorted(chapters_dict.items(), key=lambda entry: entry[1])

    return render_template("directory.html", directors=directors, director_names=director_titles, chapters=chapters)

@info.route("/addchapter", methods=["GET", "POST"])
def add_chapter():
    if "uid" not in session or not is_verified(session["uid"]):
        return redirect(url_for("auth.login", redirect=url_for("info.add_chapter")))
    if request.method == "GET":
        return render_template("create_chapter.html")
    if not request.json or "name" not in request.json or "officers" not in request.json or any(role not in request.json["officers"] for role in officer_roles):
        abort(400, "Malformed chapter creation request")
    try:
        for role in officer_roles:
            firebase_auth.get_user(request.json["officers"][role])
    except:
        abort(404, "Officer UIDs not found")
    chapters_info_obj = fireClient.collection("info").document("chapter_info").get()
    chapter_id = chapters_info_obj.get("id_counter")
    chapter_id = str(chapter_id)
    while len(chapter_id) < 3:
        chapter_id = "0" + chapter_id
    
    chapter_dict = chapters_info_obj.get("chapters")
    chapter_dict[request.json["name"]] = chapter_id
    fireClient.collection("info").document("chapter_info").set(
        {
            "id_counter": int(chapter_id) + 1,
            "chapters": chapter_dict
        }
    )

    chapter_ref = fireClient.collection("info").document("chapter_info").collection("chapters").document(chapter_id)

    try:
        officers = request.json["officers"]
        chapter = {
            "name": request.json["name"],
            "officers": {
                role: officers[role] for role in officer_roles
            },
            "ambassadors": []
        }
    except KeyError:
        abort(400, "Malformed chapter creation request")

    chapter_ref.set(chapter)
    return redirect(url_for("info.view_chapter", chapter_id=chapter_id))

@info.route("/viewchapter/<chapter_id>")
def view_chapter(chapter_id):
    chapter_ref = fireClient.collection("info").document("chapter_info").collection("chapters").document(chapter_id)
    chapter_obj = chapter_ref.get()
    if not chapter_obj.exists:
        abort(404, "Chapter not found")
    officers = [(firebase_auth.get_user(chapter_obj.get("officers")[role]), role) for role in officer_roles]
    
    return render_template("chapter_directory.html", chapter=chapter_obj.to_dict(), chapter_id=chapter_id, officers=officers, officer_titles=officer_titles)


@info.route("/userlookup", methods=["GET", "POST"])
def user_lookup():
    if request.method == "GET":
        return render_template("user_lookup.html")
    if not request.form:
        abort(400, "No form data attached")
    method = request.form.get("method", "")
    if method not in user_lookup_methods:
        abort(400, "Invalid lookup method")
    if "data" not in request.form:
        abort(400, "No lookup information provided")
    try:
        results = user_lookup_methods[method](request.form["data"])
        return render_template("user_lookup_results.html", results=results)
    except:
        abort(404, "User not found")


@info.route("/editprofile", methods=["GET", "POST"])
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
        if user.display_name and request.form["name"] != user.display_name:
            user_ref = fireClient.collection("users").document(user.uid)
            user_dict = user_ref.get().to_dict()
            user_dict["name_array"] = request.form["name"].lower().split()
            user_ref.set(user_dict)
        firebase_auth.update_user(
            uid=session["uid"],
            display_name=request.form["name"],
            email=request.form["email"],
            phone_number=phone
        )
    except Exception as e:
        abort(400, "Malformed edit profile request: " + str(e))
        
    return redirect(url_for("info.view_profile", uid=session["uid"]))


@info.route("/user/<uid>", methods=["GET"])
def view_profile(uid):
    try:
        user = firebase_auth.get_user(uid)
    except:
        abort(404, "User not found")

    return render_template("view_profile.html", user=user)