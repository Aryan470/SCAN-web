from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session, flash
from datetime import datetime
from uuid import uuid4
from scan_web import fireClient
from uuid import uuid4
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

bakesale = Blueprint("bakesale", __name__, template_folder="bakesale_templates")
userVars = [
    "name",
    "phone",
    "address",
    "email"
]
role_names = {
    "baker": "Baker",
    "delivery": "Delivery",
    "both": "Baker and Delivery",
}
number_names = {
    1: "one",
    6: "a half dozen",
    12: "a dozen"
}
admin_uids = ["lvWXZdOLvFOZVo8xiO1hKo1P1tu1"]

@bakesale.route("/reloadproducts")
def load_product_data():
    new_product_data = {}
    categories = fireClient.collection("categories").stream()
    for category_obj in categories:
        category = category_obj.to_dict()
        category_id = category["category_id"]
        new_product_data[category_id] = category.copy()
        # make a copy of keys to prevent concurrent modification, reason being we need to convert string key to numbers
        prices = list(new_product_data[category_id]["prices"].keys())
        for price in prices:
            new_product_data[category_id]["prices"][float(price)] = new_product_data[category_id]["prices"][price]
            new_product_data[category_id]["prices"].pop(price)
        new_product_data[category_id]["products"] = {}

        products = fireClient.collection("categories").document(category_id).collection("products").stream()
        for product_obj in products:
            product = product_obj.to_dict()
            product_id = product["product_id"]
            new_product_data[category_id]["products"][product_id] = product.copy()

    global product_data
    product_data = new_product_data
    return product_data

product_data = load_product_data()

@bakesale.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@bakesale.route("/report_issue", methods=["GET", "POST"])
def report_issue():
    if request.method == "GET":
        return render_template("issue_form.html", orderID=request.args.get("orderID"), view=request.args.get("view"))

    issue = {
        "description": request.form["description"],
        "UTC_timestamp": str(datetime.utcnow()),
        "resolved": False
    }

    orderID = request.form["orderID"]
    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")
    
    order_dict = order_obj.to_dict()
    if "issues" in order_dict:
        order_dict["issues"].append(issue)
    else:
        order_dict["issues"] = [issue]
    order_dict["has_unresolved_issues"] = True
    
    order_ref.set(order_dict)
    flash("We are sorry that you had an issue with this order, a member of the SCAN team will look at it as soon as possible. Thank you.")
    return redirect(url_for("bakesale.show_order", orderID=orderID, view=request.form["view"]))

@bakesale.route("/orderform", methods=["GET"])
def orderform():
    if "referral" in request.args:
        return render_template("orderform.html", product_data=product_data, number_names=number_names, referral=request.args.get("referral"))
    return render_template("orderform.html", product_data=product_data, number_names=number_names)

@bakesale.route("/submit_order", methods=["GET"])
def submit_order():
    userInfo = {}
    for userVar in userVars:
        userInfo[userVar] = request.args.get(userVar, default="N/A")

    quantities = {}
    fulfillment = {}
    categorySums = {}
    price = 0
    for category_id in product_data:
        quantities[category_id] = {}
        fulfillment[category_id] = {}
        for product_id in product_data[category_id]["products"]:
            if request.args.get(product_id, default=0, type=int) > 0:
                quantities[category_id][product_id] = request.args.get(product_id, default=0, type=int)
                fulfillment[category_id][product_id] = {
                    "count": 0,
                    "bakers": {}
                }
        categorySum = sum(quantities[category_id].values())
        for count in sorted(product_data[category_id]["prices"], reverse=True):
            if categorySum <= 0:
                break
            price += (categorySum // count) * product_data[category_id]["prices"][count]
            categorySum %= count
    if price <= 0:
        abort(400, "Price cannot be 0")
    
    order = {
        "userInfo": userInfo,
        "price": price,
        "quantities": quantities,
        "UTC_timestamp": str(datetime.utcnow()),
        "orderID": str(uuid4()),
        "fulfillment": fulfillment,
        "status": {
            "received": True,
            "baked": False,
            "delivered": False,
            "collected": False
        }
    }

    if "notes" in request.args:
        order["notes"] = request.args.get("notes")
    
    if "referral" in request.args:
        order["referral"] = request.args.get("referral")
        if request.args.get("referral") != "instagram":
            update_leaderboard(request.args.get("referral"), order["price"])
    
    increment_count("received")

    fireClient.collection("orders").document(order["orderID"]).set(order)

    # Send confirmation email now
    orderURL = url_for("bakesale.show_order", orderID=order["orderID"], _external=True)
    try:
        send_mail(userInfo["email"], "SCAN Order Confirmation",
            render_template("order_confirmation_email_plain.html", order=order, product_data=product_data, orderURL=orderURL),
            html_content=render_template("order_confirmation_email.html", order=order, product_data=product_data, orderURL=orderURL))
        flash("An email was sent to you containing a link to this order and its contents.")
    except BaseException as e:
        print("EMAIL ERROR:", e)
        flash("An error occurred while sending an email, please save this link to access your order.")
    return redirect(url_for("bakesale.show_order", orderID=order["orderID"]))

@bakesale.route("/leaderboard", methods=["GET"])
def display_leaderboard():
    leaderboard = fireClient.collection("statistics").document("sales").get().to_dict()["leaderboard"]
    return render_template("leaderboard.html", leaderboard=leaderboard)

@bakesale.route("/order/<orderID>", methods=["GET"])
def show_order(orderID):
    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")
    
    view = request.args.get("view", default="customer")
    order_dict = order_obj.to_dict()
    if view == "admin" and order_dict["status"]["collected"]:
        order_dict["statusText"] = "Collected"
    elif order_dict["status"]["delivered"]:
        order_dict["statusText"] = "Delivered"
    elif order_dict["status"]["baked"]:
        order_dict["statusText"] = "Baked"
    else:
        order_dict["statusText"] = "Received"

    if "uid" in session and view == "baker":
        return render_template("single_order_baker.html", order=order_dict, product_data=product_data)
    elif "uid" in session and view == "delivery":
        return render_template("single_order_delivery.html", order=order_dict, product_data=product_data)
    elif "uid" in session and view == "admin" and session["uid"] in admin_uids:
        return render_template("single_order_admin.html", order=order_dict, product_data=product_data)
    else:
        return render_template("single_order.html", order=order_dict, product_data=product_data)

@bakesale.route("/baker_view", methods=["GET"])
def baker_view():
    # check login
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    # load in all pending orders
    pending_orders = fireClient.collection("orders").where("status.received", "==", True).where("status.baked", "==", False).order_by("UTC_timestamp").stream()

    return render_template("baker_view.html", product_data=product_data, pending=[order.to_dict() for order in pending_orders])

@bakesale.route("/bakeitem", methods=["GET", "POST"])
def bake_item():
    if "uid" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("bake_form.html", product_data=product_data,
        orderID=request.args.get("orderID"), itemCategory=request.args.get("itemCategory"),
        itemID=request.args.get("itemID"), qtyMax=request.args.get("qtyMax"))
    orderID = request.form["orderID"]
    itemCategory = request.form["itemCategory"]
    itemID = request.form["itemID"]
    quantity = int(request.form["quantity"])
    bakerID = session["uid"]

    if orderID is None or itemCategory is None or itemID is None or quantity is None \
        or itemCategory not in product_data or not any([itemID in products for category in product_data for products in product_data[category]["products"]]):
        abort(400, "Bake request must include order ID, category, item, and quantity")
    
    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")
    order_dict = order_obj.to_dict()
    if itemID not in order_dict["fulfillment"][itemCategory]:
        abort(400, "Item not in order")
    
    if quantity <= 0 or quantity > (order_dict["quantities"][itemCategory][itemID] - order_dict["fulfillment"][itemCategory][itemID]["count"]):
        abort(400, "Quantity is invalid")
    
    order_dict["fulfillment"][itemCategory][itemID]["count"] += quantity
    if bakerID in order_dict["fulfillment"][itemCategory][itemID]["bakers"]:
        order_dict["fulfillment"][itemCategory][itemID]["bakers"][bakerID]["count"] += quantity
    else:
        user_name = session["name"]
        order_dict["fulfillment"][itemCategory][itemID]["bakers"][bakerID] = {
            "count": quantity,
            "name": user_name
        }

    # check to see if all quantities are met
    allMet = True
    for category in order_dict["quantities"]:
        for item in order_dict["quantities"][category]:
            if order_dict["fulfillment"][category][item]["count"] < order_dict["quantities"][category][item]:
                allMet = False
                break
    
    if allMet:
        order_dict["status"]["baked"] = allMet
        order_dict["baking"] = {
            "UTC_timestamp": str(datetime.utcnow()),
        }
        increment_count("baked")
        update_stats("received", "baked", order_dict["UTC_timestamp"], order_dict["baking"]["UTC_timestamp"])
    
    order_ref.set(order_dict)
    return redirect(url_for("bakesale.baker_view"))

@bakesale.route("/deliveritem", methods=["GET", "POST"])
def deliver_item():
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    if request.method == "GET":
        return render_template("delivery_form.html", orderID=request.args.get("orderID"),
        address=request.args.get("address"), price=request.args.get("price"))

    orderID = request.form["orderID"]
    uid = session["uid"]
    # simply mark as delivered
    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")
    
    order_dict = order_obj.to_dict()
    order_dict["status"]["delivered"] = True

    order_dict["delivery"] = {
        "deliveredBy": {
            "uid": uid,
            "name": session["name"]
        },
        "UTC_timestamp": str(datetime.utcnow())
    }

    increment_count("delivered")
    update_stats("received", "delivered", order_dict["UTC_timestamp"], order_dict["delivery"]["UTC_timestamp"])
    update_stats("baked", "delivered", order_dict["baking"]["UTC_timestamp"], order_dict["delivery"]["UTC_timestamp"])
    increment_product_counts(order_dict["quantities"])

    order_ref.set(order_dict)
    return redirect(url_for("bakesale.delivery_view"))

@bakesale.route("/resolveissue", methods=["GET", "POST"])
def resolve_issue():
    if "uid" not in session or session["uid"] not in admin_uids:
        return redirect(url_for("auth.login"))
    
    if request.method == "GET":
        return render_template("resolve_issue_form.html", orderID=request.args.get("orderID"),
        issue_description=request.args.get("issue_description"), issue_index=request.args.get("issue_index"))
    
    orderID = request.form["orderID"]
    issue_index = int(request.form["issue_index"])

    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")
    
    order = order_obj.to_dict()
    if issue_index < 0 or issue_index >= len(order["issues"]):
        abort(400, "Invalid issue index")
    order["issues"][issue_index]["resolved"] = True
    order["issues"][issue_index]["resolved_by"] = {
        "uid": session["uid"],
        "name": session["name"]
    }

    all_resolved = True
    for issue in order["issues"]:
        if not issue["resolved"]:
            all_resolved = False
    
    order["has_unresolved_issues"] = not all_resolved
    order_ref.set(order)
    return redirect(url_for("bakesale.admin_view"))

@bakesale.route("/collectitem", methods=["GET", "POST"])
def collect_item():
    if "uid" not in session or session["uid"] not in admin_uids:
        return redirect(url_for("auth.login"))
    
    if request.method == "GET":
        return render_template("collect_form.html", orderID=request.args.get("orderID"),
        price=request.args.get("price"), deliverer={
            "name": request.args.get("deliverer_name"),
            "uid": request.args.get("deliverer_id")
        })
    
    orderID = request.form["orderID"]
    uid = session["uid"]

    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")
    
    order_dict = order_obj.to_dict()
    order_dict["status"]["collected"] = True
    order_dict["collection"] = {
        "collector": {
            "uid": session["uid"],
            "name": session["name"]
        },
        "UTC_timestamp": str(datetime.utcnow())
    }
    increment_count("collected")
    update_stats("received", "collected", order_dict["UTC_timestamp"], order_dict["collection"]["UTC_timestamp"])
    update_stats("baked", "collected", order_dict["baking"]["UTC_timestamp"], order_dict["collection"]["UTC_timestamp"])
    update_stats("delivered", "collected", order_dict["delivery"]["UTC_timestamp"], order_dict["collection"]["UTC_timestamp"])

    order_ref.set(order_dict)
    return redirect(url_for("bakesale.admin_view"))

@bakesale.route("/editprofile", methods=["GET", "POST"])
def edit_profile():
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    uid = session["uid"]
    user_ref = fireClient.collection("users").document(uid)

    if request.method == "GET":
        user_obj = user_ref.get()
        if user_obj.exists:
            user_dict = user_obj.to_dict()
        else:
            user_dict = {"uid": uid}
        return render_template("edit_profile.html", user=user_dict, rolenames=role_names)
    else:
        try:
            user_dict = {}
            if session["uid"] != request.form["uid"]:
                abort(400, "UID does not match session")
            user_dict["uid"] = session["uid"]
            user_dict["name"] = request.form["name"]
            user_dict["role"] = request.form["role"]
            user_dict["phone"] = request.form["phone"]
        except:
            abort(400, "Malformed edit profile request")
        
        user_ref.set(user_dict)
        return redirect(url_for("bakesale.view_profile", uid=session["uid"]))

@bakesale.route("/deliveryview", methods=["GET"])
def delivery_view():
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    baked_orders = fireClient.collection("orders").where("status.baked", "==", True).where("status.delivered", "==", False).order_by("UTC_timestamp").stream()
    return render_template("delivery_view.html", baked=[order.to_dict() for order in baked_orders])

@bakesale.route("/adminview", methods=["GET"])
def admin_view():
    if "uid" not in session or session["uid"] not in admin_uids:
        return redirect(url_for("auth.login"))
    
    delivered_orders = [order.to_dict() for order in fireClient.collection("orders").where("status.delivered", "==", True).where("status.collected", "==", False).order_by("UTC_timestamp").stream()]
    issue_orders = [order.to_dict() for order in fireClient.collection("orders").where("has_unresolved_issues", "==", True).order_by("UTC_timestamp").stream()]
    return render_template("admin_view.html", delivered=delivered_orders, issue_orders=issue_orders)

@bakesale.route("/profile/<uid>", methods=["GET"])
def view_profile(uid):
    user_ref = fireClient.collection("users").document(uid)
    user_obj = user_ref.get()
    if not user_obj.exists:
        abort(404, "User not found")
    user_dict = user_obj.to_dict()
    return render_template("view_profile.html", user=user_dict, rolenames=role_names)

def send_mail(recipient, subject, plain_content, html_content=None):
    if os.environ["CONTEXT"] == "PROD":
        port = 465
        smtp_server = "smtp.gmail.com"

        sender_email = os.environ["EMAIL"]
        password = os.environ["EMAIL_PASS"]
        alias_email = os.environ["ALIAS_EMAIL"]

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = alias_email
        message["To"] = recipient

        message.attach(MIMEText(plain_content, "plain"))
        if html_content is not None:
            message.attach(MIMEText(str(html_content), "html"))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient, message.as_string())
        server.quit()

def update_leaderboard(referral_link, amount):
    leaderboard_ref = fireClient.collection("statistics").document("sales")
    sales = leaderboard_ref.get().to_dict()
    sales["leaderboard"][referral_link] = sales["leaderboard"].get(referral_link, 0.0) + amount
    leaderboard_ref.set(sales)

def increment_count(category):
    count_ref = fireClient.collection("statistics").document("counts")
    count_dict = count_ref.get().to_dict()
    count_dict[category] += 1
    count_ref.set(count_dict)

def update_stats(start_category, end_category, start_timestamp, end_timestamp):
    fmt = "%Y-%m-%d %H:%M:%S.%f UTC"
    start_datetime = datetime.strptime(start_timestamp, fmt)
    end_datetime = datetime.strptime(end_timestamp, fmt)
    # total seconds divided by seconds in a day
    delta_days = (end_datetime - start_datetime).total_seconds() / (3600 * 24)

    times_ref = fireClient.collection("statistics").document("times")
    times = times_ref.get().to_dict()
    times[start_category][end_category] += delta_days
    times_ref.set(times)

def increment_product_counts(order_quantities):
    for category in order_quantities:
        category_freqs_ref = fireClient.collection("statistics").document("frequencies").collection("categories").document(category)
        category_obj = category_freqs_ref.get()
        if category_obj.exists:
            category_dict = category_obj.to_dict()
        else:
            category_dict = {}

        for product_id in order_quantities[category]:
            if order_quantities[category][product_id] > 0:
                if product_id in category_dict:
                    category_dict[product_id] += order_quantities[category][product_id]
                else:
                    category_dict[product_id] = order_quantities[category][product_id]
        
        category_freqs_ref.set(category_dict)
