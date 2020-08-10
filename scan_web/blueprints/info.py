from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin.auth as firebase_auth
import firebase_admin.firestore as firestore
from scan_web import fireClient

info = Blueprint("info", __name__, template_folder="info_templates")

director_titles = {
    "chairman": "Chairman of the Board",
    "vice_chairman": "Vice Chairman of the Board",
    "informatics": "Director of Informatics",
    "publicity": "Director of Publicity",
    "operations": "Director of Operations",
    "communications": "Director of Communications",
}

officer_titles = {
    "communications": "Communications Officer",
    "publicity": "Publicity Officer",
    "executive": "Executive Officer",
    "informatics": "Informatics Officer",
    "operations": "Operations Officer"
}

director_roles = [
    "communications",
    "publicity",
    "chairman",
    "vice_chairman",
    "informatics",
    "operations"
]

officer_roles = [
    "communications",
    "publicity",
    "executive",
    "informatics",
    "operations"
]

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
    return {"success": True}

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
    officers = [(chapter_obj.get("officers")[role], role) for role in officer_roles]
    
    return render_template("chapter_directory.html", chapter=chapter_obj.to_dict(), chapter_id=chapter_id, officers=officers, officer_titles=officer_titles)

