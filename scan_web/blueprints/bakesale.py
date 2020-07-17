from flask import Blueprint, request, abort, jsonify, render_template
from scan_web import fireClient
from uuid import uuid4

bakesale = Blueprint("bakesale", __name__, template_folder="templates")

@bakesale.route("/", methods=["GET"])
def index():
    return render_template("orderform.html")