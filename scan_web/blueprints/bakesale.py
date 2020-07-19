from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
from datetime import datetime
from uuid import uuid4
from scan_web import fireClient
from uuid import uuid4

bakesale = Blueprint("bakesale", __name__, template_folder="bakesale_templates")
categories = {
    "cookie": [
        "cookie_chocchip",
        "cookie_oatmeal",
        "cookie_sugar",
        "cookie_snickerdoodle"
    ],
    "cupcake": [
        "cupcake_redvelvet",
        "cupcake_chocolate",
        "cupcake_vanilla",
    ],
    "muffin": [
        "muffin_blueberry",
        "muffin_chocchip",
        "muffin_bananawalnut"
    ],
    "brownie": [
        "brownies_brownie"
    ]
}
prices = {
    "cookie": {
        1: 0.75,
        12: 8.00
    },
    "cupcake": {
        1: 1.75,
        12: 20.00,
    },
    "muffin": {
        1: 1.50,
        12: 16.00,
    },
    "brownie": {
        1: 1.00,
        6: 5.00
    }
}
userVars = [
    "name",
    "phone",
    "address"
]
nameLookup = {
    "cookie": "Cookies",
    "cupcake": "Cupcakes",
    "muffin": "Muffins",
    "brownie": "Brownies",

    "cookie_chocchip": "Chocolate Chip",
    "cookie_oatmeal": "Oatmeal",
    "cookie_sugar": "Sugar Cookie",
    "cookie_snickerdoodle": "Snickerdoodle",

    "cupcake_redvelvet": "Red Velvet",
    "cupcake_chocolate": "Chocolate",
    "cupcake_vanilla": "Vanilla",

    "muffin_blueberry": "Blueberry",
    "muffin_chocchip": "Chocolate Chip",
    "muffin_bananawalnut": "Banana Walnut",

    "brownies_brownie": "Brownie"
}


@bakesale.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@bakesale.route("/orderform", methods=["GET"])
def orderform():
    return render_template("orderform.html")

@bakesale.route("/submitorder", methods=["GET"])
def submitOrder():
    userInfo = {}
    for userVar in userVars:
        userInfo[userVar] = request.args.get(userVar, default="N/A")

    quantities = {}
    fulfillment = {}
    categorySums = {}
    price = 0
    for category in categories:
        quantities[category] = {}
        fulfillment[category] = {}
        for item in categories[category]:
            if request.args.get(item, default=0, type=int) > 0:
                quantities[category][item] = request.args.get(item, default=0, type=int)
                fulfillment[category][item] = {
                    "count": 0,
                    "bakers": {}
                }
        categorySum = sum(quantities[category].values())
        for count in sorted(prices[category], reverse=True):
            if categorySum <= 0:
                break
            price += (categorySum // count) * prices[category][count]
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
        }
    }

    fireClient.collection("orders").document(order["orderID"]).set(order)
    return redirect(url_for("bakesale.showOrder", orderID=order["orderID"]))

@bakesale.route("/order/<orderID>", methods=["GET"])
def showOrder(orderID):
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
    else:
        order_dict["statusText"] = "Received"

    if "uid" in session and view == "baker":
        return render_template("single_order_baker.html", order=order_dict, names=nameLookup)
    elif "uid" in session and view == "delivery":
        return render_template("single_order_delivery.html", order=order_dict, names=nameLookup)
    else:
        return render_template("single_order.html", order=order_dict, names=nameLookup)

@bakesale.route("/bakerview", methods=["GET"])
def baker_view():
    # check login
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    # load in all pending orders
    pending_orders = fireClient.collection("orders").where("status.received", "==", True).where("status.baked", "==", False).order_by("UTC_timestamp").stream()

    # load in all delivered orders
    # delivered_orders = fireClient.collection("orders").where("status.delivered", "==", True).order_by("UTC_timestamp").stream()

    return render_template("baker_view.html", names=nameLookup, pending=[order.to_dict() for order in pending_orders])

@bakesale.route("/bakeitem", methods=["GET", "POST"])
def bake_item():
    if "uid" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("bake_form.html", names=nameLookup,
        orderID=request.args.get("orderID"), itemCategory=request.args.get("itemCategory"),
        itemID=request.args.get("itemID"), qtyMax=request.args.get("qtyMax"))
    orderID = request.form["orderID"]
    itemCategory = request.form["itemCategory"]
    itemID = request.form["itemID"]
    quantity = int(request.form["quantity"])
    bakerID = session["uid"]

    if orderID is None or itemCategory is None or itemID is None or quantity is None \
        or itemCategory not in categories or itemID in categories or itemID not in nameLookup:
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
    
    order_dict["status"]["baked"] = allMet
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
        "UTC_timestamp": datetime.utcnow()
    }

    order_ref.set(order_dict)
    return redirect(url_for("bakesale.delivery_view"))

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
        return render_template("profile.html", user=user_dict)
    else:
        try:
            user_dict = {}
            user_dict["uid"] = request.form["uid"]
            user_dict["name"] = request.form["name"]
            user_dict["role"] = request.form["role"]
        except:
            abort(400, "Malformed edit profile request")
        
        user_ref.set(user_dict)
        return redirect(url_for("bakesale.index"))

@bakesale.route("/deliveryview", methods=["GET"])
def delivery_view():
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    baked_orders = fireClient.collection("orders").where("status.baked", "==", True).where("status.delivered", "==", False).order_by("UTC_timestamp").stream()
    return render_template("delivery_view.html", baked=[order.to_dict() for order in baked_orders])

@bakesale.route("/adminview", methods=["GET"])
def admin_view():
    if "uid" not in session:
        return redirect(url_for("auth.login"))
    
    return "work in progress"

@bakesale.route("/profile/<uid>", methods=["GET"])
def view_profile(uid):
    user_ref = fireClient.collection("users").document(uid)
    user_obj = user_ref.get()
    if not user_obj.exists:
        abort(404, "User not found")
    user_dict = user_obj.to_dict()
    return render_template("view_profile.html", user=user_dict)