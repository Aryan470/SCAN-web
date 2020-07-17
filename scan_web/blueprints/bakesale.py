from flask import Blueprint, request, abort, jsonify, render_template
from socraticos import fireClient
from uuid import uuid4

bakesale = Blueprint("bakesale", __name__)

@bakesale.route("/", methods=["GET"])
def index():
    return render_template("orderform.html")