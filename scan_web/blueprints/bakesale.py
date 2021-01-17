from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session, flash
from datetime import datetime
from uuid import uuid4
from scan_web import fireClient
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
exec_referral_links = [
    "Pranav_Kousik".lower(),
    "Harshini_ThangaRajMalini".lower(),
    "Krisha_Prabakaran".lower(),
    "Rupak_Kadiri".lower(),
    "Alekhya_Vattikuti".lower(),
    "Aryan_Khatri".lower()
]
admin_uids = {"lvWXZdOLvFOZVo8xiO1hKo1P1tu1", "cb1WKvzrlSXKOYv5sAjBz47A1Y62"}
branches = ["Frisco", "Allen"]

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
        return render_template("orderform.html", product_data=product_data, number_names=number_names, referral=request.args.get("referral"), branches=branches)
    return render_template("orderform.html", product_data=product_data, number_names=number_names, branches=branches)

@bakesale.route("/submit_order", methods=["POST"])
def submit_order():
    userInfo = {}
    for userVar in userVars:
        userInfo[userVar] = request.form.get(userVar, "N/A")

    quantities = {}
    fulfillment = {}
    categorySums = {}
    price = 0
    for category_id in product_data:
        quantities[category_id] = {}
        fulfillment[category_id] = {}
        for product_id in product_data[category_id]["products"]:
            if int(request.form.get(product_id, 0)) > 0:
                quantities[category_id][product_id] = int(request.form.get(product_id, 0))
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
        "branch": request.form.get("branch", "N/A"),
        "status": {
            "received": True,
            "invoiced": False,
            "baked": False,
            "delivered": False
        }
    }

    if "notes" in request.form:
        order["notes"] = request.form["notes"]
    
    if "referral" in request.form:
        order["referral"] = request.form["referral"].lower()
        if request.form["referral"] != "instagram":
            update_leaderboard(request.form["referral"].lower(), order["price"])
    

    fireClient.collection("orders").document(order["orderID"]).set(order)

    # DO NOT send confirmation email
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
    return render_template("leaderboard.html", leaderboard={referral: leaderboard[referral] for referral in leaderboard if referral.lower() not in exec_referral_links})

@bakesale.route("/order/<orderID>", methods=["GET"])
def show_order(orderID):
    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")
    
    view = request.args.get("view", default="customer")
    order_dict = order_obj.to_dict()

    if order_dict["status"]["delivered"]:
        order_dict["statusText"] = "Delivered"
    elif order_dict["status"]["baked"]:
        order_dict["statusText"] = "Baked"
    elif order_dict["status"]["invoiced"]:
        order_dict["statusText"] = "Invoiced"
    else:
        order_dict["statusText"] = "Received"

    if "uid" in session:
        if view == "finance":
            return render_template("single_order_finance.html", order=order_dict, product_data=product_data)
        elif view == "baker":
            return render_template("single_order_baker.html", order=order_dict, product_data=product_data)
        elif view == "delivery":
            return render_template("single_order_delivery.html", order=order_dict, product_data=product_data)
        elif view == "admin" and session["uid"] in admin_uids:
            return render_template("single_order_admin.html", order=order_dict, product_data=product_data)
    return render_template("single_order.html", order=order_dict, product_data=product_data)

@bakesale.route("/baker_view", methods=["GET"])
def baker_view():
    # check login
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    # load in all pending orders
    pending_orders = fireClient.collection("orders").where("status.invoiced", "==", True).where("status.baked", "==", False).order_by("UTC_timestamp").stream()

    return render_template("baker_view.html", product_data=product_data, pending=[order.to_dict() for order in pending_orders])


@bakesale.route("/finance_view", methods=["GET"])
def finance_view():
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    not_invoiced_orders = fireClient.collection("orders").where("status.invoiced", "==", False).order_by("UTC_timestamp").stream()

    return render_template("finance_view.html", not_invoiced_orders=[order.to_dict() for order in not_invoiced_orders])

@bakesale.route("/invoiceitem", methods=["GET", "POST"])
def invoice_item():
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    if request.method == "GET":
        return render_template("invoice_form.html", orderID=request.args.get("orderID"), price=request.args.get("price"))
    
    orderID = request.form["orderID"]
    invoiceLink = request.form["invoiceLink"]

    financeID = session["uid"]

    if not orderID or not financeID:
        abort(400, "Invoice request must include order ID and login")
    
    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")

    order_dict = order_obj.to_dict()

    if order_dict["status"]["invoiced"] or "invoice" in order_dict:
        abort(400, "Order already invoiced")

    order_dict["invoice"] = {
        "link": invoiceLink,
        "creator": financeID
    }

    order_dict["status"]["invoiced"] = True

    order_ref.set(order_dict)
    return redirect(url_for("bakesale.finance_view"))


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
    
    issue_orders = [order.to_dict() for order in fireClient.collection("orders").where("has_unresolved_issues", "==", True).order_by("UTC_timestamp").stream()]
    return render_template("admin_view.html", issue_orders=issue_orders)

@bakesale.route("/adminview/delivered", methods=["GET"])
def admin_delivered_view():
    delivered_orders = [order.to_dict() for order in fireClient.collection("orders").where("status.delivered", "==", True).order_by("UTC_timestamp").stream()]
    return render_template("admin_delivered_view.html", delivered=delivered_orders)


@bakesale.route("/profile/<uid>", methods=["GET"])
def view_profile(uid):
    user_ref = fireClient.collection("users").document(uid)
    user_obj = user_ref.get()
    if not user_obj.exists:
        abort(404, "User not found")
    user_dict = user_obj.to_dict()
    return render_template("view_profile.html", user=user_dict, rolenames=role_names)

def send_mail(recipient, subject, plain_content, html_content=None):
    if os.environ["CONTEXT"] != "PROD":
        # don't send emails if we are not in production
        return
    
    port = 465
    smtp_server = "smtp.dreamhost.com"

    sender_email = os.environ["EMAIL"]

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient
    message["Cc"] = ["info@sicklecellawareness.net"]

    message.attach(MIMEText(plain_content, "plain"))
    if html_content is not None:
        message.attach(MIMEText(str(html_content), "html"))
    
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender_email, os.environ["EMAIL_PASS"])
    server.sendmail(sender_email, recipient, message.as_string())
    server.quit()

def update_leaderboard(referral_link, amount):
    leaderboard_ref = fireClient.collection("statistics").document("sales")
    sales = leaderboard_ref.get().to_dict()
    sales["leaderboard"][referral_link] = sales["leaderboard"].get(referral_link, 0.0) + amount
    leaderboard_ref.set(sales)
