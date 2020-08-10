from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin.auth as firebase_auth
import firebase_admin.firestore as firestore
from scan_web import fireClient

info = Blueprint("info", __name__, template_folder="info_templates")

director_title_names = {
    "chairman": "Chairman of the Board",
    "vice_chairman": "Vice Chairman of the Board",
    "informatics": "Director of Informatics",
    "publicity": "Director of Publicity",
    "operations": "Director of Operations",
    "communications": "Director of Communications",
}

officer_title_names: {
    "communications": "Communications Officer",
    "publicity": "Publicity Officer",
    "executive": "Executive Officer",
    "informatics": "Informatics Officer",
    "operations": "Operations Officer"
}

ordered_director_roles = [
    "communications",
    "publicity",
    "chairman",
    "vice_chairman",
    "informatics",
    "operations"
]

ordered_officer_roles = [
    "communications",
    "publicity",
    "executive",
    "informatics",
    "operations"
]

@info.route("/")
def index():
    return {"success": True}

@info.route("/directory")
def display_directory():
    directory_ref = fireClient.collection("info").document("directory")
    directory = directory_ref.get().to_dict()
    directors = [(firebase_auth.get_user(directory["directors"][role]), role) for role in ordered_director_roles if role in directory["directors"]]

    #branches = directory["branches"]
    #for branch in branches:
    #    branches[branch] = [(firebase_auth.get_user(branches[branch][role]), role) for role in ordered_officer_roles if role in branches["branch"]]

    return render_template("directory.html", directors=directors, director_title_names=director_title_names)#, officer_title_names=officer_title_names, branches=branches)