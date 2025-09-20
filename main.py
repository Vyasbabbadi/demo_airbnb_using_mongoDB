import re
import os
from flask import Flask, session, render_template, redirect, request, jsonify
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# MongoDB imports - will be conditional for deployment
try:
    import pymongo
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'airbnb-secret-key-change-in-production')

# MongoDB connection - Use environment variable for production
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')

# Initialize MongoDB connection if available
if MONGODB_AVAILABLE:
    try:
        my_client = pymongo.MongoClient(MONGODB_URI)
        my_database = my_client["Airbnb"]
        admin_collection = my_database["Admin"]
        categories_collection = my_database["Categories"]
        locations_collection = my_database["Location"]
        bookings_collection = my_database["Bookings"]
        payment_details_collection = my_database["Payment Details"]
        properties_collection = my_database["Properties"]
        customer_collection = my_database["Customer"]
        host_collection = my_database["Host"]
        review_collection = my_database["Review"]
        print("MongoDB connected successfully")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        MONGODB_AVAILABLE = False
else:
    print("MongoDB not available - using demo mode")

# Admin credentials
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

@app.route("/admin_login_action", methods=['POST'])
def admin_login_action():
    if not MONGODB_AVAILABLE:
        return render_template("message.html", message="Database not available in demo mode")
    
    username = request.form.get("username")
    password = request.form.get("password")
    if admin_username == username and admin_password == password:
        session['role'] = "Admin"
        return render_template("admin_home.html")
    else:
        return render_template("message.html", message="Invalid Login Details")

@app.route("/host_login")
def host_login():
    return render_template("host_login.html")

@app.route("/host_login_action", methods=['POST'])
def host_login_action():
    if not MONGODB_AVAILABLE:
        return render_template("message.html", message="Database not available in demo mode")
    
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = host_collection.count_documents(query)
    if count > 0:
        host = host_collection.find_one(query)
        if host['status'] == "Active":
            session['role'] = "Host"
            session['property_host_id'] = str(host['_id'])
            session['first_name'] = str(host['first_name'])
            return render_template("host_home.html")
        else:
            return render_template("message.html", message="Properties Host Not Authorized")
    else:
        return render_template("message.html", message="Invalid Login Details")

@app.route("/customer_login")
def customer_login():
    return render_template("customer_login.html")

@app.route("/customer_login_action", methods=['POST'])
def customer_login_action():
    if not MONGODB_AVAILABLE:
        return render_template("message.html", message="Database not available in demo mode")
    
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email}
    customer = customer_collection.find_one(query)
    if customer:
        if check_password_hash(customer['password'], password):
            session['role'] = "Customer"
            session['customer_id'] = str(customer['_id'])
            session['name'] = customer['first_name']
            return render_template("customer_home.html")
        else:
            return render_template("message.html", message="Invalid Password")
    else:
        return render_template("message.html", message="Invalid Login Details")

# Simplified routes for demo purposes
@app.route("/categories")
def categories():
    if not MONGODB_AVAILABLE:
        # Return demo data
        demo_categories = [
            {"_id": "1", "categories_name": "Apartment"},
            {"_id": "2", "categories_name": "House"},
            {"_id": "3", "categories_name": "Villa"}
        ]
        return render_template("categories.html", categories=demo_categories)
    
    query = {}
    categories = categories_collection.find(query)
    categories = list(categories)
    return render_template("categories.html", categories=categories)

@app.route("/locations")
def locations():
    if not MONGODB_AVAILABLE:
        # Return demo data
        demo_locations = [
            {"_id": "1", "location_name": "Mumbai", "state_name": "Maharashtra", "zipcode": "400001"},
            {"_id": "2", "location_name": "Delhi", "state_name": "Delhi", "zipcode": "110001"},
            {"_id": "3", "location_name": "Bangalore", "state_name": "Karnataka", "zipcode": "560001"}
        ]
        return render_template("locations.html", locations=demo_locations)
    
    query = {}
    locations = locations_collection.find(query)
    locations = list(locations)
    return render_template("locations.html", locations=locations)

@app.route("/view_properties")
def view_properties():
    if not MONGODB_AVAILABLE:
        return render_template("message.html", message="Property viewing requires database connection")
    
    # Your existing view_properties logic here (simplified for demo)
    query = {}
    properties = properties_collection.find(query)
    properties = list(properties)
    return render_template("view_properties.html", properties=properties)

@app.route("/health")
def health_check():
    status = {
        "status": "healthy",
        "mongodb": "connected" if MONGODB_AVAILABLE else "not available",
        "environment": os.environ.get('VERCEL_ENV', 'development')
    }
    return jsonify(status)

# Helper functions
def get_host_by_host_id(host_id):
    if not MONGODB_AVAILABLE:
        return {"first_name": "Demo Host", "email": "demo@example.com"}
    query = {'_id': ObjectId(host_id)}
    host = host_collection.find_one(query)
    return host

def get_category_by_category_id(category_id):
    if not MONGODB_AVAILABLE:
        return {"categories_name": "Demo Category"}
    query = {'_id': ObjectId(category_id)}
    category = categories_collection.find_one(query)
    return category

def get_location_by_location_id(location_id):
    if not MONGODB_AVAILABLE:
        return {"location_name": "Demo Location"}
    query = {'_id': ObjectId(location_id)}
    location = locations_collection.find_one(query)
    return location

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template("message.html", message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("message.html", message="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Export for Vercel
app = app