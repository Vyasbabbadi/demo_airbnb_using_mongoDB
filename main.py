import re

from bson import ObjectId
from flask import Flask, session, render_template, redirect, request
from datetime import datetime
import pymongo
import os
from werkzeug.security import generate_password_hash, check_password_hash


App_root = os.path.dirname(os.path.abspath(__file__))
profile_pictures_path = App_root+ "/" + "static/profile_pictures"
property_images_path = App_root+ "/" + "static/property_images"

my_client = pymongo.MongoClient("mongodb://localhost:27017")
my_database = my_client["Airbnb"]
admin_collection = my_database["Admin"]
categories_collection = my_database["Categories"]
locations_collection = my_database["Location"]
state_collection = my_database["State"]
zipcode_collection = my_database["Zipcode"]
bookings_collection = my_database["Bookings"]
payment_details_collection = my_database["Payment Details"]
properties_collection = my_database["Properties"]
customer_collection = my_database["Customer"]
host_collection = my_database["Host"]
review_collection = my_database["Review"]

app = Flask(__name__)
app.secret_key = "airbnb"
admin_username = "admin"
admin_password = "admin"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/host_home")
def host_home():
    return render_template("host_home.html")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/customer_home")
def customer_home():
    return render_template("customer_home.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login_action", methods = ['post'])
def admin_login_action():
    username=request.form.get("username")
    password=request.form.get("password")
    if admin_username == username and admin_password == password :
        session['role'] = "Admin"
        return render_template("admin_home.html")
    else:
        return render_template("message.html", message = "Invalid Login Details")


@app.route("/host_login")
def host_login():
    return render_template("host_login.html")


@app.route("/host_login_action", methods = ['post'])
def host_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query={"email":email, "password":password}
    count=host_collection.count_documents(query)
    if count>0:
        host = host_collection.find_one(query)
        if host['status'] == "Active":
            session['role'] = "Host"
            session['property_host_id'] = str(host['_id'])
            session['first_name'] = str(host['first_name'])
            return render_template("host_home.html")
        else:
            return render_template("message.html", message = "Properties Host Not Authorized")
    else:
        return render_template("message.html", message = "Invalid Login Details")


@app.route("/host_registration")
def host_registration():
    return render_template("host_registration.html")


@app.route("/host_registration_action", methods = ['post'])
def host_registration_action():
    first_name = request.form.get("host_first_name")
    last_name = request.form.get("host_last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    if confirm_password != password:
        return render_template("message.html", message="Password Doesn't Match")
    query = {"email":email}
    count = host_collection.count_documents(query)
    if count>0:
        return render_template("message.html", message = "Email Id Already Registered" )
    query = {"phone":phone}
    count = host_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message = "Phone Number Already Registered")
    query = {"first_name":first_name, "last_name":last_name, "email":email, "phone":phone, "password":password, "status":"Not Active"}
    host_collection.insert_one(query)
    return render_template("message.html", message1 = "Properties Host Successfully Registered")


@app.route("/customer_login")
def user_home():
    return render_template("customer_login.html")

@app.route("/customer_login_action", methods = ['post'])
def customer_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email":email}
    customer = customer_collection.count_documents(query)
    if customer:
        if check_password_hash(customer['password'], password):
            session['role'] = "Customer"
            session['customer_id'] = str(customer['_id'])
            session['name'] = customer['first_name']
            return render_template("customer_home.html")
        else:
            return render_template("message.html", message="Invalid Password")
    else:
        return render_template("message.html", message = "Invalid Login Details")



@app.route("/customer_registration")
def customer_registration():
    return render_template("customer_registration.html")


@app.route("/customer_registration_action", methods = ['post'])
def customer_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    address = request.form.get("address")
    dob = request.form.get("dob")
    city = request.form.get("city")
    zipcode = request.form.get("zipcode")
    picture = request.files.get("picture")
    path = profile_pictures_path + "/" + picture.filename
    picture.save(path)
    if confirm_password != password:
        return render_template("message.html", message="Password Doesn't Match")
    query = {"email":email}
    count = customer_collection.count_documents(query)
    if count>0:
        return render_template("message.html", message = "Email Id Already Registered")
    query = {"phone": phone}
    count = customer_collection.count_documents(query)
    if count > 0:
        return render_template("message.html", message = "Phone Number Already Registered")
    hashed_password = generate_password_hash(password)
    query = {"first_name":first_name, "last_name":last_name, "phone":phone, "email":email, "password":hashed_password, "dob":dob, "address":address, "city":city, "zipcode":zipcode, "picture":picture.filename}
    customer_collection.insert_one(query)
    return render_template("message.html", message1 = "Customer Successfully Registered")


@app.route("/view_hosts")
def view_hosts():
    query = {}
    hosts = host_collection.find(query)
    hosts = reversed(list(hosts))
    return render_template("view_hosts.html", hosts = hosts)


@app.route("/verify_host")
def verify_host():
    property_host_id = request.args.get("property_host_id")
    query = {"_id":ObjectId(property_host_id)}
    query1 = {"$set":{"status":"Active"}}
    host_collection.update_one(query, query1)
    return redirect("/view_hosts")


@app.route("/un_verify_host")
def un_verify_host():
    property_host_id = request.args.get("property_host_id")
    query = {"_id": ObjectId(property_host_id)}
    query1 = {"$set": {"status": "Not Active"}}
    host_collection.update_one(query, query1)
    return redirect("/view_hosts")


@app.route("/categories")
def categories():
    query = {}
    categories = categories_collection.find(query)
    categories = list(categories)
    return render_template("categories.html", categories = categories)


@app.route("/add_category_action", methods = ['post'])
def add_category_action():
    category = request.form.get("category")
    query = {"categories_name":category}
    categories_collection.insert_one(query)
    return redirect("/categories")


@app.route("/update_category")
def update_category():
    category_id = request.args.get("category_id")
    query = {'_id':ObjectId(category_id)}
    category = categories_collection.find_one(query)
    return render_template("update_category.html", category = category)


@app.route("/update_category_action", methods=['post'])
def update_category_action():
    category_id = request.form.get("category_id")
    category = request.form.get("category")
    query = {'_id':ObjectId(category_id)}
    query1 = {"$set":{"categories_name":category}}
    categories_collection.update_one(query, query1)
    return redirect("/categories")


@app.route("/locations")
def locations():
    query = {}
    locations = locations_collection.find(query)
    locations = list(locations)
    return render_template("locations.html", locations = locations)
    # query = {}
    # states = state_collection.find(query)
    # states = list(states)
    # query = {}
    # zipcodes = zipcode_collection.find(query)
    # zipcodes = list(zipcodes)
    # return render_template("locations.html", locations = locations, states = states, zipcodes = zipcodes)


@app.route("/add_location_action", methods = ['post'])
def add_location_action():
    location_name = request.form.get("location_name")
    state_name = request.form.get("state_name")
    zipcode = request.form.get("zipcode")
    query = {"location_name":location_name, "state_name":state_name, "zipcode":zipcode}
    locations_collection.insert_one(query)
    return redirect("/locations")


# @app.route("/add_location_action", methods = ['post'])
# def add_location_action():
#     location_name = request.form.get("location_name")
#     query = {"location_name":location_name}
#     locations_collection.insert_one(query)
#     return redirect("/locations")
#
#
# @app.route("/add_state_action", methods = ['post'])
# def add_state_action():
#     state_name = request.form.get("state_name")
#     query = {"state_name":state_name}
#     state_collection.insert_one(query)
#     return redirect("/locations")
#
#
# @app.route("/add_zipcode_action", methods = ['post'])
# def add_zipcode_action():
#     zipcode = request.form.get("zipcode")
#     query = {"zipcode":zipcode}
#     zipcode_collection.insert_one(query)
#     return redirect("/locations")


@app.route("/add_properties")
def add_properties():
    location_id = request.args.get("location_id")
    if location_id == None or location_id == "":
        query = {}
        locations = locations_collection.find(query)
        locations = list(locations)
    else:
        query = {'_id':ObjectId(location_id)}
        locations = locations_collection.find(query)
        locations = list(locations)
    query = {}
    categories = categories_collection.find(query)
    categories = list(categories)
    return render_template("add_properties.html", locations=locations, categories=categories, location_id = location_id, str = str)
    # query = {}
    # states = state_collection.find(query)
    # states = list(states)
    # query = {}
    # zipcodes = zipcode_collection.find(query)
    # zipcodes = list(zipcodes)
    # return render_template("add_properties.html", locations = locations, categories = categories, states = states, zipcodes = zipcodes)


@app.route("/add_property_action", methods = ['post'])
def add_property_action():
    host_id = session['property_host_id']
    first_name = session['first_name']
    location_id = request.form.get("location_id")
    category_id = request.form.get("category_id")
    properties_name = request.form.get("properties_name")
    properties_detail = request.form.get("properties_detail")
    services = request.form.get("services")
    property_address = request.form.get("property_address")
    rent_per_day = request.form.get("rent_per_day")
    service_charges = request.form.get("service_charges")
    area_occupied = request.form.get("area_occupied")
    picture_of_property = request.files.get("picture_of_property")
    path = property_images_path + "/" + picture_of_property.filename
    picture_of_property.save(path)
    query = {"host_id":ObjectId(host_id),"category_id":ObjectId(category_id), "location_id":ObjectId(location_id), "first_name":first_name ,"properties_name":properties_name, "properties_detail":properties_detail, "services":services, "rent_per_day":rent_per_day, "service_charges":service_charges, "area_occupied":area_occupied, "picture_in_property":picture_of_property.filename, "property_address":property_address, "status":"Not Approved" }
    properties_collection.insert_one(query)
    return render_template("message.html", message1 = "Property Added Successfully")


@app.route("/view_properties")
def view_properties():
    query = {}
    categories = categories_collection.find(query)
    categories = list(categories)
    query = {}
    locations = locations_collection.find(query)
    locations = list(locations)
    category_id = request.args.get("category_id")
    location_id = request.args.get("location_id")
    properties_name = request.args.get("properties_name")
    if category_id == None:
        category_id = ""
    if location_id == None:
        location_id = ""
    if properties_name == None:
        properties_name = ""
    if session['role'] == "Host":
        property_id = session['property_host_id']
        query = {"host_id":ObjectId(property_id)}
        if category_id == "" and location_id == "" and properties_name == "":
            query = {"host_id":ObjectId(property_id)}
        elif category_id != "" and location_id == "" and properties_name == "":
            query = {"category_id": ObjectId(category_id), "host_id":ObjectId(property_id)}
        elif category_id == "" and location_id != "" and properties_name == "":
            query = {"location_id": ObjectId(location_id), "host_id":ObjectId(property_id)}
        elif category_id == "" and location_id == "" and properties_name != "":
            keyword2 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword2, "host_id":ObjectId(property_id)}
        elif category_id == "" and location_id != "" and properties_name != "":
            keyword2 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword2, "host_id": ObjectId(property_id), "location_id": ObjectId(location_id)}
        elif category_id != "" and location_id == "" and properties_name != "":
            keyword2 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword2, "host_id": ObjectId(property_id), "category_id": ObjectId(category_id)}
        elif category_id != "" and location_id != "" and properties_name == "":
            query = {"location_id": ObjectId(location_id), "host_id": ObjectId(property_id), "category_id": ObjectId(category_id)}
        elif category_id != "" and location_id != "" and properties_name != "":
            keyword2 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword2, "host_id": ObjectId(property_id), "location_id": ObjectId(location_id), "category_id": ObjectId(category_id)}
    elif session['role'] == "Admin":
        host_first_name = request.args.get("host_first_name")
        if host_first_name == None:
            host_first_name = ""
        query = {}
        if category_id == "" and location_id == "" and host_first_name == ""  and properties_name == "":
            query = {}
        elif category_id == "" and location_id == "" and host_first_name == ""  and properties_name != "":
            keyword3 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword3}
        elif category_id == "" and location_id == "" and host_first_name != ""  and properties_name == "":
            keyword2 = re.compile(".*" + str(host_first_name) + ".*", re.IGNORECASE)
            query = {"host_first_name": keyword2}
        elif category_id == "" and location_id == "" and host_first_name != ""  and properties_name != "":
            keyword3 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            keyword2 = re.compile(".*" + str(host_first_name) + ".*", re.IGNORECASE)
            query = {"host_first_name": keyword2, "properties_name": keyword3}
        elif category_id == "" and location_id != "" and host_first_name == ""  and properties_name == "":
            query = {"location_id": ObjectId(location_id)}
        elif category_id == "" and location_id != "" and host_first_name == ""  and properties_name != "":
            keyword3 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword3, "location_id": ObjectId(location_id)}
        elif category_id == "" and location_id != "" and host_first_name != ""  and properties_name == "":
            keyword2 = re.compile(".*" + str(host_first_name) + ".*", re.IGNORECASE)
            query = {"location_id": ObjectId(location_id), "host_first_name": keyword2}
        elif category_id == "" and location_id != "" and host_first_name != ""  and properties_name != "":
            keyword3 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            keyword2 = re.compile(".*" + str(host_first_name) + ".*", re.IGNORECASE)
            query = {"location_id": ObjectId(location_id), "host_first_name": keyword2, "properties_name": keyword3}
        elif category_id != "" and location_id == "" and host_first_name == ""  and properties_name == "":
            query = {"category_id": ObjectId(category_id)}
        elif category_id != "" and location_id == "" and host_first_name == ""  and properties_name != "":
            keyword3 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"category_id": ObjectId(category_id), "properties_name": keyword3}
        elif category_id != "" and location_id == "" and host_first_name != ""  and properties_name == "":
            keyword2 = re.compile(".*" + str(host_first_name) + ".*", re.IGNORECASE)
            query = {"category_id": ObjectId(category_id), "host_first_name": keyword2}
        elif category_id != "" and location_id == "" and host_first_name != "" and properties_name != "":
            keyword2 = re.compile(".*" + str(host_first_name) + ".*", re.IGNORECASE)
            keyword3 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"category_id": ObjectId(category_id), "host_first_name": keyword2, "properties_name": keyword3}
        elif category_id != "" and location_id != "" and host_first_name == ""  and properties_name == "":
            query = {"category_id": ObjectId(category_id), "location_id": ObjectId(location_id)}
        elif category_id != "" and location_id != "" and host_first_name == ""  and properties_name != "":
            keyword3 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"category_id": ObjectId(category_id), "location_id": ObjectId(location_id), "properties_name": keyword3}
        elif category_id != "" and location_id != "" and host_first_name != "" and properties_name == "":
            keyword2 = re.compile(".*" + str(host_first_name) + ".*", re.IGNORECASE)
            query = {"category_id": ObjectId(category_id), "location_id": ObjectId(location_id), "host_first_name": keyword2}
        elif category_id != "" and location_id != "" and host_first_name != ""  and properties_name != "":
            keyword2 = re.compile(".*" + str(host_first_name) + ".*", re.IGNORECASE)
            keyword3 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"category_id": ObjectId(category_id), "location_id": ObjectId(location_id), "host_first_name": keyword2, "properties_name": keyword3}
    elif session['role'] == "Customer":
        query = {}
        if category_id == "" and location_id == "" and properties_name == "":
            query = {}
        elif category_id != "" and location_id == "" and properties_name == "":
            query = {"category_id": ObjectId(category_id)}
        elif category_id == "" and location_id != "" and properties_name == "":
            query = {"location_id": ObjectId(location_id)}
        elif category_id == "" and location_id == "" and properties_name != "":
            keyword2 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword2}
        elif category_id == "" and location_id != "" and properties_name != "":
            keyword2 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword2, "location_id": ObjectId(location_id)}
        elif category_id != "" and location_id == "" and properties_name != "":
            keyword2 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword2, "category_id": ObjectId(category_id)}
        elif category_id != "" and location_id != "" and properties_name == "":
            query = {"location_id": ObjectId(location_id), "category_id": ObjectId(category_id)}
        elif category_id != "" and location_id != "" and properties_name != "":
            keyword2 = re.compile(".*" + str(properties_name) + ".*", re.IGNORECASE)
            query = {"properties_name": keyword2, "location_id": ObjectId(location_id), "category_id": ObjectId(category_id)}
    properties = properties_collection.find(query)
    properties = reversed(list(properties))
    return render_template("view_properties.html", categories = categories, locations = locations, properties = properties, category_id = category_id, location_id = location_id, get_host_by_host_id = get_host_by_host_id, get_category_by_category_id = get_category_by_category_id, get_location_by_location_id = get_location_by_location_id, str = str)


@app.route("/verify_property")
def verify_property():
    property_id = request.args.get("property_id")
    query = {'_id':ObjectId(property_id)}
    query1 = {"$set":{"status":"Approved"}}
    properties_collection.update_one(query, query1)
    return redirect("/view_properties")


@app.route("/un_verif_property")
def un_verif_property():
    property_id = request.args.get("property_id")
    query = {'_id': ObjectId(property_id)}
    query1 = {"$set": {"status": "Not Approved"}}
    properties_collection.update_one(query, query1)
    return redirect("/view_properties")


@app.route("/booking")
def booking():
    property_id = request.args.get("property_id")
    host_id = request.args.get("host_id")
    amount = request.args.get("amount")
    date = datetime.now()
    date = datetime.strftime(date, "%Y-%m-%dT%H:%M")
    return render_template("booking.html", property_id=property_id, host_id=host_id, amount=amount, date=date)


@app.route("/add_booking_action", methods=['post'])
def add_booking_action():
    customer_id = session['customer_id']
    property_id = request.form.get("property_id")
    host_id = request.form.get("host_id")
    date_of_checkin = request.form.get("date_of_checkin")
    date_of_checkout = request.form.get("date_of_checkout")
    number_of_guest = request.form.get("number_of_guest")
    date_of_checkin2 = datetime.strptime(date_of_checkin, "%Y-%m-%dT%H:%M")
    date_of_checkout2 = datetime.strptime(date_of_checkout, "%Y-%m-%dT%H:%M")
    date_of_checkin = datetime.strptime(str(date_of_checkin2),"%Y-%m-%d %H:%M:%S")
    date_of_checkout = datetime.strptime(str(date_of_checkout2), "%Y-%m-%d %H:%M:%S")
    query = {"$or": [{"date_of_checkin": {"$gte": date_of_checkin, "$lte": date_of_checkout},
                      "date_of_checkout": {"$gte": date_of_checkin, "$gte": date_of_checkout},
                      "status": {"$in": ['Booked', 'CheckedIn','Checkout Request']}},
                     {"date_of_checkin": {"$lte": date_of_checkin, "$lte": date_of_checkout},
                      "date_of_checkout": {"$gte": date_of_checkin, "$lte": date_of_checkout},
                      "status": {"$in": ['Booked', 'CheckedIn','Checkout Request']}},
                     {"date_of_checkin": {"$lte": date_of_checkin, "$lte": date_of_checkout},
                      "date_of_checkout": {"$gte": date_of_checkin, "$gte": date_of_checkout},
                      "status":{"$in": ['Booked', 'CheckedIn','Checkout Request']}},
                     {"date_of_checkin": {"$gte": date_of_checkin, "$lte": date_of_checkout},
                      "date_of_checkout": {"$gte": date_of_checkin, "$lte": date_of_checkout},
                      "status": {"$in": ['Booked', 'CheckedIn','Checkout Request']}},
                     ], "property_id": ObjectId(property_id)}
    count = bookings_collection.count_documents(query)
    if count>0:
        return render_template("message.html",message="Property Not Avaialble on these dates")


    if  date_of_checkout > date_of_checkin:
        diff = (date_of_checkout - date_of_checkin)
        days = diff.days
    elif date_of_checkout == date_of_checkin:
        days = 1
    else:
        return render_template("message.html", message="Check Out Date is before than Check In Date")
    amount = request.form.get("amount")
    payable_amount = ( int(days) *  int(amount) )
    query={"property_id":ObjectId(property_id), "customer_id":ObjectId(customer_id), "host_id":ObjectId(host_id), "date_of_checkin":date_of_checkin, "date_of_checkout":date_of_checkout, "status":"Payment Pending", "number_of_guest":number_of_guest, "payable_amount":payable_amount}
    result = bookings_collection.insert_one(query)
    booking_id = result.inserted_id

    return redirect("/payments?booking_id="+str(booking_id)+"&payable_amount="+str(payable_amount)+"&days="+str(days))


@app.route("/payments")
def payments():
    booking_id = request.args.get("booking_id")
    payable_amount = request.args.get("payable_amount")
    days = request.args.get("days")
    date = datetime.now().month
    return render_template("payments.html", booking_id=booking_id, payable_amount=payable_amount,days=days, date=date)


@app.route("/payment_action", methods=['post'])
def payment_action():
    booking_id = request.form.get("booking_id")
    customer_id = session['customer_id']
    days = request.form.get("days")
    card_number = request.form.get("card_number")
    holder_name = request.form.get("holder_name")
    expired_date = request.form.get("expire_date")
    cvv = request.form.get("cvv")
    date = datetime.now()
    amount = request.form.get("payable_amount")
    query = {"booking_id":ObjectId(booking_id), "customer_id":ObjectId(customer_id), "card_number":card_number, "holder_name":holder_name, "expired_date":expired_date, "cvv":cvv, "amount":amount, "status":"Payment Done", "date":date}
    payment_details_collection.insert_one(query)
    query = {"$set":{"status":'Booked',"days":days}}
    bookings_collection.update_one({"_id":ObjectId(booking_id)},query)
    return redirect("/view_bookings")


@app.route("/pay_extra_charges")
def pay_extra_charges():
    booking_id = request.args.get("booking_id")
    payable_amount = request.args.get("payable_amount")
    return render_template("pay_extra_charges.html",payable_amount=payable_amount,booking_id=booking_id)

@app.route("/pay_extra_charges_action", methods=['post'])
def pay_extra_charges_action():
    booking_id = request.form.get("booking_id")
    customer_id = session['customer_id']
    days = request.form.get("days")
    card_number = request.form.get("card_number")
    holder_name = request.form.get("holder_name")
    expired_date = request.form.get("expire_date")
    cvv = request.form.get("cvv")
    date = datetime.now()
    amount = request.form.get("payable_amount")
    query = {"booking_id":ObjectId(booking_id), "customer_id":ObjectId(customer_id), "card_number":card_number, "holder_name":holder_name, "expired_date":expired_date, "cvv":cvv, "amount":amount, "status":"Extra Charges Paid", "date":date}
    payment_details_collection.insert_one(query)
    query = {"$set":{"status":'Extra Charges Paid'}}
    bookings_collection.update_one({"_id":ObjectId(booking_id)},query)
    return redirect("/view_bookings")


@app.route("/view_bookings")
def view_bookings():
    if session['role'] == "Admin":
        query = {}
    elif session['role'] == "Host":
        property_host_id = session['property_host_id']
        query = {"host_id":ObjectId(property_host_id)}
    else:
        customer_id = session['customer_id']
        query = {"customer_id":ObjectId(customer_id)}
    bookings = bookings_collection.find(query)
    bookings = reversed(list(bookings))
    return render_template("view_bookings.html",int=int, bookings = bookings, get_property_by_property_id = get_property_by_property_id, get_customer_by_customer_id=get_customer_by_customer_id, get_location_by_location_id=get_location_by_location_id, get_host_by_host_id=get_host_by_host_id)


@app.route("/booking_confirm")
def booking_confirm():
    booking_id = request.args.get("booking_id")
    query = {'_id': ObjectId(booking_id)}
    query1 = {"$set": {"status":"CheckedIn"}}
    bookings_collection.update_one(query, query1)
    return render_template("message.html", message1 = "Customer Checked In")


@app.route("/booking_cancel")
def booking_cancel():
    booking_id = request.args.get("booking_id")
    query = {'_id': ObjectId(booking_id)}
    query1 = {"$set": {"status":"Cancelled"}}
    bookings_collection.update_one(query, query1)
    return render_template("message.html", message = "Booking Cancelled")


@app.route("/checkout_request")
def checkout_request():
    booking_id = request.args.get("booking_id")
    query = {'_id': ObjectId(booking_id)}
    query1 = {"$set": {"status": "Checkout Request"}}
    bookings_collection.update_one(query, query1)
    return render_template("message.html", message1 = "Check Out Request Sent")


@app.route("/checkout_accept")
def checkout_accept():
    booking_id = request.args.get("booking_id")
    return render_template("checkout_page.html", booking_id = booking_id)


@app.route("/check_out_action", methods=['post'])
def check_out_action():
    booking_id = request.form.get("booking_id")
    extra_charges = request.form.get("extra_charges")
    query = {'_id': ObjectId(booking_id)}
    query1 = {"$set": {"status": "Checkout", "extra_charges":extra_charges}}
    bookings_collection.update_one(query, query1)
    return render_template("message.html", message1 = "Check Out Request Accepted")


@app.route("/conversation")
def conversation():
    booking_id = request.args.get("booking_id")
    query = {'_id':ObjectId(booking_id)}
    booking = bookings_collection.find_one(query)
    user_id = None
    if session['role']=='Host':
        user_id = session['property_host_id']
    elif session['role']=='Customer':
        user_id = session['customer_id']
    return render_template("conversation.html",user_id=user_id,str=str, booking_id = booking_id, booking = booking,get_customer_by_customer_id=get_customer_by_customer_id,get_host_by_host_id=get_host_by_host_id)


@app.route("/add_conversation", methods=['post'])
def add_conversation():
    message = request.form.get("message")
    booking_id  = request.form.get("booking_id")
    booking = bookings_collection.find_one({"_id":ObjectId(booking_id)})

    message_by = None
    message_from_role = None
    message_to_role = None
    if session['role']=='Host':
        message_by = session['property_host_id']
        message_from_role = "host"
        message_to_role="customer"
    elif session['role']=='Customer':
        message_by = session['customer_id']
        message_from_role = "customer"
        message_to_role = "host"
    date = datetime.now()
    conversation = {
        "message": message,
        "message_by":ObjectId(message_by),
        "date":date,
        "message_from_role":message_from_role,
        "message_to_role":message_to_role
    }
    query = {'_id':ObjectId(booking_id)}
    query1 = {"$push":{"conversation":conversation}}
    bookings_collection.update_one(query, query1)
    return redirect("/conversation?booking_id="+booking_id)


@app.route("/view_payments")
def view_payments():
    booking_id = request.args.get("booking_id")
    payments = payment_details_collection.find({"booking_id":ObjectId(booking_id)})
    payments = reversed(list(payments))
    return render_template("view_payments.html",payments=payments)


@app.route("/review_bookings")
def review_bookings():
    booking_id = request.args.get("booking_id")
    query = {"booking_id":ObjectId(booking_id)}
    reviews = review_collection.find(query)
    reviews = list(reviews)
    return render_template("review_bookings.html", booking_id = booking_id, reviews = reviews)


@app.route("/review_action", methods=['post'])
def review_action():
    booking_id = request.form.get("booking_id")
    rating = request.form.get("rating")
    review = request.form.get("review")
    date = datetime.now()
    query = {"booking_id":ObjectId(booking_id), "rating":rating, "review":review, "date":date}
    review_collection.insert_one(query)
    return render_template("message.html", message1="Review Given")


def get_host_by_host_id(host_id):
    query = {'_id':ObjectId(host_id)}
    host = host_collection.find_one(query)
    return host


def get_category_by_category_id(category_id):
    query = {'_id':ObjectId(category_id)}
    category = categories_collection.find_one(query)
    return category


def get_location_by_location_id(location_id):
    query = {'_id':ObjectId(location_id)}
    location = locations_collection.find_one(query)
    return location


def get_property_by_property_id(property_id):
    query = {'_id':ObjectId(property_id)}
    property = properties_collection.find_one(query)
    return property


def get_customer_by_customer_id(customer_id):
    query = {'_id':ObjectId(customer_id)}
    customer = customer_collection.find_one(query)
    return customer


if __name__ == '__main__':
    app.run(debug=True)