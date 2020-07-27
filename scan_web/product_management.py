from scan_web import fireClient

def add_vegan_products():
    for category_obj in fireClient.collection("categories").stream():
        category = category_obj.to_dict()
        category_id = category["category_id"]
        if category_id.startswith("r_"):
            continue
        # copying gluten free products: gf_
        new_category_id = "p_" + category_id[3:]

        new_category_data = {
            "name": category["name"].replace("Gluten Free", "Vegan"),
            "category_id": new_category_id,
            "prices": category["prices"].copy()
        }
        
        # fireClient.collection("categories").document(new_category_id).set(new_category_data)
        # print(new_category_id)

        for product_obj in fireClient.collection("categories").document(category_id).collection("products").stream():
            product = product_obj.to_dict()
            new_product = product.copy()
            new_product["product_id"] = "p_" + new_product["product_id"][3:]
            # print(new_product["product_id"])
            # fireClient.collection("categories").document(new_category_id).collection("products").document(new_product["product_id"]).set(new_product)
add_vegan_products()