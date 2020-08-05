from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
import firebase_admin
from firebase_admin.auth import verify_id_token
from datetime import datetime
from uuid import uuid4
from scan_web import fireClient
from uuid import uuid4
import csv

users = Blueprint("users", __name__, template_folder="users_templates")
admin_uids = ["lvWXZdOLvFOZVo8xiO1hKo1P1tu1"]