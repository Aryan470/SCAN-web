from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for, session
from datetime import datetime
from uuid import uuid4
from scan_web import fireClient
from uuid import uuid4

bakesale = Blueprint("bakesale", __name__, template_folder="templates")
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
                fulfillment[category][item] = 0
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
    
    return render_template("single_order.html", order=order_obj.to_dict(), names=nameLookup)

@bakesale.route("/vieworders", methods=["GET"])
def view_orders():
    # check login
#    if "authorized" not in session or not session["authorized"]:
#        return redirect(url_for("login"))
    
    # load in all pending orders
    pending_orders = fireClient.collection("orders").where("status.received", "==", True).order_by("UTC_timestamp").stream()

    # load in all baked orders
    baked_orders = fireClient.collection("orders").where("status.baked", "==", True).order_by("UTC_timestamp").stream()

    # load in all delivered orders
    delivered_orders = fireClient.collection("orders").where("status.delivered", "==", True).order_by("UTC_timestamp").stream()

    return render_template("view_orders.html", names=nameLookup, pending=[order.to_dict() for order in pending_orders], baked=[order.to_dict() for order in baked_orders], delivered=[order.to_dict() for order in delivered_orders])