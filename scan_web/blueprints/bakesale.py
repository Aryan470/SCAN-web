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
    # TODO: return link to order
    return redirect(url_for("bakesale.showOrder", orderID=order["orderID"]))

@bakesale.route("/order/<orderID>", methods=["GET"])
def showOrder(orderID):
    order_ref = fireClient.collection("orders").document(orderID)
    order_obj = order_ref.get()
    if not order_obj.exists:
        abort(404, "Order not found")
    
    view = request.args.get("view", default="customer")

    if view == "baker":
        return render_template("single_order_baker.html", order=order_obj.to_dict(), names=nameLookup)
    elif view == "delivery":
        return render_template("single_order.html", order=order_obj.to_dict(), names=nameLookup)
    else:
        return render_template("single_order.html", order=order_obj.to_dict(), names=nameLookup)

@bakesale.route("/bakerview", methods=["GET"])
def baker_view():
    # check login
#    if "authorized" not in session or not session["authorized"]:
#        return redirect(url_for("login"))
    
    # load in all pending orders
    pending_orders = fireClient.collection("orders").where("status.received", "==", True).where("status.baked", "==", False).order_by("UTC_timestamp").stream()

    # load in all baked orders
    baked_orders = fireClient.collection("orders").where("status.baked", "==", True).where("status.delivered", "==", False).order_by("UTC_timestamp").stream()

    # load in all delivered orders
    delivered_orders = fireClient.collection("orders").where("status.delivered", "==", True).order_by("UTC_timestamp").stream()

    return render_template("baker_view.html", names=nameLookup, pending=[order.to_dict() for order in pending_orders], baked=[order.to_dict() for order in baked_orders], delivered=[order.to_dict() for order in delivered_orders])

@bakesale.route("/bakeitem", methods=["GET", "POST"])
def bake_item():
    if request.method == "GET":
        return render_template("bake_form.html", names=nameLookup,
        orderID=request.args.get("orderID"), itemCategory=request.args.get("itemCategory"),
        itemID=request.args.get("itemID"), qtyMax=request.args.get("qtyMax"))
    orderID = request.form["orderID"]
    itemCategory = request.form["itemCategory"]
    itemID = request.form["itemID"]
    quantity = int(request.form["quantity"])
    bakerID = "aryan"

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
        abort(400, "Quantity is too invalid")
    
    order_dict["fulfillment"][itemCategory][itemID]["count"] += quantity
    if bakerID in order_dict["fulfillment"][itemCategory][itemID]["bakers"]:
        order_dict["fulfillment"][itemCategory][itemID]["bakers"][bakerID] += quantity
    else:
        order_dict["fulfillment"][itemCategory][itemID]["bakers"][bakerID] = quantity

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
