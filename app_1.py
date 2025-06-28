from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient, uri_parser
from bson.objectid import ObjectId
import bcrypt
import json
from datetime import timedelta, datetime,time
import os
import certifi
from dotenv import load_dotenv
from functools import wraps # Import wraps for decorators
from collections import defaultdict
# Ensure environment variables are loaded first
load_dotenv()

app = Flask(__name__)
app.secret_key = "123355"
if not app.secret_key:
    print("CRITICAL: SECRET_KEY not found in environment variables. Using a highly insecure default.")
    app.secret_key = "very_insecure_default_key_for_testing_DO_NOT_USE_IN_PRODUCTION"

app.permanent_session_lifetime = timedelta(days=365)

MONGO_URI=os.environ["MONGO"]
print(MONGO_URI)
# Initialize global client, db, and collections to None
client = None
db = None
users_collection = None

if not MONGO_URI:
    print("CRITICAL: MONGO_URI environment variable not set. Application cannot connect to the database.")
    print("Please set the MONGO_URI environment variable (e.g., in a .env file) before running the application.")
else:
    uri_to_log = MONGO_URI
    if '@' in MONGO_URI:
        parts = MONGO_URI.split('@')
        uri_to_log = parts[0].rsplit(':', 1)[0] + ':***@' + parts[1]
    print(f"Attempting to connect to MongoDB with URI: {uri_to_log}")

    try:
        if "mongodb+srv" in MONGO_URI or ".mongodb.net" in MONGO_URI:
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        else:
            client = MongoClient(MONGO_URI)

        client.admin.command('ping')
        print("Successfully connected to MongoDB!")

        db_name_to_use = "expense"
        print(f"Using database '{db_name_to_use}' as requested.")
        db = client[db_name_to_use]
        users_collection = db.users

        try:
            users_collection.create_index("username", unique=True)
            print(f"Username index created/ensured on 'users' collection in database '{db.name}'.")
        except Exception as e_index:
            print(f"Warning: Could not create username index (might already exist or other DB issue): {e_index}")

    except Exception as e:
        print(f"CRITICAL ERROR: Could not connect to MongoDB: {e}")
        if "DNS operation timed out" in str(e) or "getaddrinfo failed" in str(e) or "resolution lifetime expired" in str(e):
            print("\n" + "="*60)
            print("This looks like a DNS RESOLUTION or NETWORK CONNECTIVITY issue.")
            print("Please check your network connection and DNS settings.")
            print("If using a remote MongoDB, ensure your IP address is whitelisted in your MongoDB Atlas security settings.")
            print("="*60 + "\n")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "info")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Category Items Data (Remains unchanged) ---
category_items = {
    "Housing Costs": [
        "Mortgage Payment (Monthly loan repayment to lender)", "Rent (Monthly payment to landlord)",
        "Property Taxes (Annual or quarterly taxes to local government)",
        "Homeowner's Insurance (Insurance covering damage and liability)",
        "Private Mortgage Insurance (PMI) (Insurance if down payment < 20%)",
        "HOA Fees (Homeowners association fees for maintenance and amenities)",
        "Home Warranty (Annual service contract for home systems/appliances)",
        "Landlord Insurance (Insurance for renters to protect belongings)",
        "Real Estate Agent Fees (Fees paid when buying or selling home)",
        "Refinancing Fees (Costs associated with refinancing mortgage)"
    ],
    "Revenue": [
    "Salary or Wages (Regular income received from an employer for work performed)",
    "Business Income (Net profits generated from owning or operating a business)",
    "Rental Income (Payments received from tenants for use of residential or commercial property)",
    "Interest Income (Earnings from interest-bearing accounts like savings, CDs, or bonds)",
    "Dividend Income (Periodic payments from shares of stock or mutual funds held)",
    "Capital Gains (Profits from selling assets such as stocks, real estate, or other investments)",
    "Royalty Income (Payments received for use of intellectual property, patents, copyrights, or creative works)",
    "Freelance or Consulting Fees (Income earned from providing freelance services or professional consulting)",
    "Government Benefits (Social Security payments, unemployment benefits, pensions, or other welfare payments)",
    "Alimony or Child Support (Court-ordered payments received from a former spouse or partner)",
    "Annuity Payments (Regular payments from an insurance or investment annuity contract)",
    "Sale of Goods or Services (Revenue from selling products or services outside of a formal business)",
    "Bonus or Commission Income (Additional earnings based on performance, sales, or targets met)",
    "Tips and Gratuities (Cash received directly from customers or clients as appreciation for services)",
    "Scholarships or Grants (Funds received for education that may count as income in some cases)",
    "Licensing Fees (Income from granting permission to use software, technology, or trademarks)",
    "Affiliate Marketing Income (Revenue earned by promoting third-party products or services)",
    "Crowdfunding or Donations (Funds raised through platforms like Patreon, GoFundMe, or donations)",
    "Miscellaneous Income (Any other irregular or one-time income sources)"
],

    "Utilities": [
        "Electricity (Power for lights, appliances, and electronics)", "Water (Household water usage)",
        "Sewer (Wastewater disposal fees)", "Gas / Heating Oil (Fuel for heating and cooking)",
        "Trash Collection (Garbage pickup services)", "Recycling Fees (Costs for recycling pickup)",
        "Internet Service (Broadband or fiber-optic connection)",
        "Cable / Streaming Subscriptions (TV and streaming services)",
        "Landline / Home Phone (Telephone line expenses)", "Mobile Phone (Home-related mobile plans or devices)",
        "Water Softener Service (Maintenance and salt for water softeners)",
        "Solar Panel Maintenance (Cleaning and repairs for solar panels)"
    ],
    "Maintenance & Repairs": [
        "Plumbing Repairs (Fixing leaks, clogs, and pipes)", "Electrical Repairs (Wiring, outlets, circuit issues)",
        "Roof Maintenance (Inspections, leaks, and cleaning)", "HVAC Servicing (Heating and cooling system maintenance)",
        "Appliance Repairs (Fixing or replacing home appliances)",
        "Gutter Cleaning (Clearing debris to prevent water damage)", "Pest Control (Treatment for insects and rodents)",
        "Chimney Cleaning (Cleaning and inspection of fireplaces)", "Septic Tank Maintenance (Cleaning and inspections)",
        "Foundation Repairs (Fixing structural issues with foundation)",
        "Window & Door Repairs (Fixing or replacing frames and glass)",
        "Painting Touch-ups (Minor interior or exterior painting)", "Drain Cleaning (Unclogging sinks and drains)",
        "Smoke Alarm Battery Replacement (Replacing batteries in alarms)",
        "Fence Repairs (Fixing or replacing damaged fencing)", "Driveway Repairs (Patching cracks or resurfacing)"
    ],
    "Household Essentials": [
        "Cleaning Supplies (Soaps, mops, disinfectants, etc.)", "Toiletries (Toilet paper, soap, shampoo, etc.)",
        "Laundry Supplies (Detergent, softener, dryer sheets)", "Kitchen Supplies (Dish soap, sponges, paper towels)",
        "Light Bulbs & Batteries (Regular replacements)", "Air Filters for HVAC (Filters to improve air quality)",
        "Garbage Bags (For trash disposal)", "Dishwasher Detergent (Cleaning agents for dishwasher)",
        "Cooking Gas or Charcoal (Fuel for cooking)", "Water Filters (Filters for drinking water)"
    ],
    "Furnishing & Home Improvement": [
        "Furniture (Beds, couches, tables, chairs)", "Home Décor (Curtains, rugs, wall art, decorations)",
        "Home Renovation (Major upgrades and remodeling)", "Painting & Wallpaper (Interior/exterior decoration)",
        "Smart Home Devices (Thermostats, cameras, assistants)", "Window Treatments (Curtains, blinds, shades)",
        "Flooring (Carpet, tile, hardwood installation)", "Lighting Fixtures (Indoor and outdoor lights)",
        "Home Office Setup (Desks, chairs, monitors, accessories)", "Security Cameras (Surveillance equipment)",
        "Outdoor Furniture (Patio tables, chairs, loungers)",
        "Shelving & Storage Solutions (Closet organizers, shelves)"
    ],
    "Outdoor & Lawn Care": [
        "Lawn Mowing (Cutting grass or paying service fees)", "Gardening Supplies (Seeds, soil, fertilizer, tools)",
        "Tree Trimming (Safety and appearance maintenance)", "Snow Removal (Shoveling or plowing service)",
        "Fence Repairs (Maintenance or replacement)", "Sprinkler System Maintenance (Repairs and timer adjustments)",
        "Landscape Lighting (Outdoor decorative and security lighting)",
        "Pool Maintenance (Cleaning, chemicals, repairs)", "Pest Control for Yard (Treatments for outdoor pests)",
        "Composting Supplies (Bins and materials for composting)",
        "Outdoor Pest Repellents (Sprays or devices to deter pests)"
    ],
    "Safety & Security": [
        "Security System (Alarm systems and sensors)", "Monitoring Subscription (Professional monitoring fees)",
        "Fire Extinguishers (Purchase or refills)", "Smoke/Carbon Monoxide Detectors (Devices and batteries)",
        "First Aid Supplies (Kits and medical essentials)", "Emergency Preparedness Kits (Supplies for disasters)",
        "Locks and Deadbolts (Installation or replacement)", "Outdoor Lighting for Security (Motion sensors, floodlights)"
    ],
    "Other Home Expenses": [
        "Moving Costs (Hiring movers or renting trucks)", "Storage Unit Rent (For extra storage space)",
        "Pet Expenses (Food, vet visits, accessories)", "Home Office Supplies (Stationery, electronics)",
        "Subscription Services (Cleaning, maintenance apps)", "Holiday Decorations (Seasonal decor and lights)",
        "Gifts for Neighbors (Welcome or holiday gifts)", "Event Hosting Supplies (Party supplies, catering)",
        "Home Insurance Deductibles (Out-of-pocket insurance costs)", "Legal Fees (Property disputes, contracts)",
        "Property Management Fees (If using a manager for rentals)"
    ]
}


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(stored_password_hash, provided_password):
    if not stored_password_hash or not provided_password:
        return False
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password_hash.encode('utf-8'))


@app.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if users_collection is not None:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Username and password are required.', 'danger')
                return redirect(url_for('register'))
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return redirect(url_for('register'))

            existing_user = users_collection.find_one({'username': username})
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'warning')
                return redirect(url_for('register'))

            hashed_pw = hash_password(password)
            try:
                users_collection.insert_one({
                    'username': username,
                    'password': hashed_pw,
                })
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'An error occurred during registration: {e}', 'danger')
                print(f"Error during user insertion: {e}")
                return redirect(url_for('register'))
    else:
        flash('Database connection error. Cannot register users at this time. Please check server logs.', 'danger')
        return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if users_collection is not None:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Username and password are required.', 'danger')
                return redirect(url_for('login'))

            user = users_collection.find_one({'username': username})

            if user and verify_password(user.get('password'), password):
                session.permanent = True
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                flash(f'Welcome back, {user["username"]}!', 'success')
                next_url = request.args.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('login'))
    else:
        flash('Database connection error. Cannot log in at this time. Please check server logs.', 'danger')
        return render_template('login.html')

    return render_template('login.html')

@app.route('/index')
@login_required
def index():
    username = session['username']

    # === 1. DATE RANGE SETUP (Unchanged) ===
    # --- BUG FIX: Use datetime.utcnow() to match the timezone of the stored data ---
    today = datetime.utcnow() 
    # --- END OF FIX ---

    start_of_day = datetime.combine(today.date(), time.min)
    end_of_day = datetime.combine(today.date(), time.max)
    start_of_week = datetime.combine((today - timedelta(days=6)).date(), time.min)
    start_of_month = datetime.combine((today - timedelta(days=29)).date(), time.min)

    # === 2. EFFICIENT & ROBUST DATA FETCHING ===
    all_docs_cursor = db[username].find({})
    all_data = []
    for doc in all_docs_cursor:
        doc['_id'] = str(doc['_id'])
        doc['timestamp_dt'] = doc['timestamp']
        doc['timestamp'] = doc['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        all_data.append(doc)

    # === 3. PREPARE DATA FOR TABLES AND STATS (from the clean list) ===
    all_revenue_data = [doc for doc in all_data if doc['category'] == 'Revenue']
    all_expense_data = [doc for doc in all_data if doc['category'] != 'Revenue']

    # Calculate totals
    total_revenue = sum(doc.get('amount', 0) for doc in all_revenue_data)
    total_expense = sum(doc.get('amount', 0) for doc in all_expense_data)

    day_total_revenue = sum(doc.get('amount', 0) for doc in all_revenue_data if start_of_day <= doc['timestamp_dt'] <= end_of_day)
    day_total_expense = sum(doc.get('amount', 0) for doc in all_expense_data if start_of_day <= doc['timestamp_dt'] <= end_of_day)

    week_total_revenue = sum(doc.get('amount', 0) for doc in all_revenue_data if doc['timestamp_dt'] >= start_of_week)
    week_total_expense = sum(doc.get('amount', 0) for doc in all_expense_data if doc['timestamp_dt'] >= start_of_week)

    month_total_revenue = sum(doc.get('amount', 0) for doc in all_revenue_data if doc['timestamp_dt'] >= start_of_month)
    month_total_expense = sum(doc.get('amount', 0) for doc in all_expense_data if doc['timestamp_dt'] >= start_of_month)

    # === 4. PREPARE CHART DATA ===
    # a) Bar Chart (Today's Data)
    bar_chart = {
        "labels": ["Today"],
        "datasets": [
            {
                "label": "Revenue",
                "data": [day_total_revenue],
                "backgroundColor": "rgba(88, 166, 255, 0.7)",
                "borderColor": "rgba(88, 166, 255, 1)",
                "borderWidth": 1,
                "borderRadius": 4
            },
            {
                "label": "Expense",
                "data": [day_total_expense],
                "backgroundColor": "rgba(248, 81, 73, 0.7)",
                "borderColor": "rgba(248, 81, 73, 1)",
                "borderWidth": 1,
                "borderRadius": 4
            }
        ]
    }

    # b) Pie Chart (Weekly Expense Breakdown)
    week_expense_for_pie = [doc for doc in all_expense_data if doc['timestamp_dt'] >= start_of_week]
    category_totals = defaultdict(float)
    for doc in week_expense_for_pie:
        category_totals[doc['category']] += doc.get('amount', 0)
    pieChartData = {'labels': list(category_totals.keys()), 'values': list(category_totals.values())}

    # c) Line Chart (Monthly Data Aggregated by Day)
    month_revenue_for_chart = [doc for doc in all_revenue_data if doc['timestamp_dt'] >= start_of_month]
    month_expense_for_chart = [doc for doc in all_expense_data if doc['timestamp_dt'] >= start_of_month]
    
    labels = [(start_of_month.date() + timedelta(days=i)) for i in range(30)]
    revenue_by_date = defaultdict(float)
    for doc in month_revenue_for_chart:
        revenue_by_date[doc['timestamp_dt'].date()] += doc.get('amount', 0)
    expense_by_date = defaultdict(float)
    for doc in month_expense_for_chart:
        expense_by_date[doc['timestamp_dt'].date()] += doc.get('amount', 0)
        
    chart_data = {
        "labels": [day.strftime('%b %d') for day in labels],
        "datasets": [
            {"label": 'Revenue', "data": [revenue_by_date[d] for d in labels]},
            {"label": 'Expense', "data": [expense_by_date[d] for d in labels]}
        ]
    }

    # === 5. RENDER TO TEMPLATE ===
    return render_template('home.html',
                           user_name=username,
                           chart_data=chart_data,
                           pieChartData=pieChartData,
                           bar_chart=bar_chart,
                           revenue_data=all_revenue_data,
                           expenses_data=all_expense_data,
                           total_revenue=total_revenue,
                           total_expense=total_expense,
                           day_total_revenue=day_total_revenue,
                           day_total_expense=day_total_expense,
                           week_total_revenue=week_total_revenue,
                           week_total_expense=week_total_expense,
                           month_total_revenue=month_total_revenue,
                           month_total_expense=month_total_expense)

@app.route('/dashboard')
@login_required
def dashboard():
    categories = list(category_items.keys())
    user_expenses = []

    if db is not None and 'username' in session:
        try:
            user_expense_collection = db[session['username']]
            user_expenses = user_expense_collection.find({}).sort('timestamp', -1).limit(10)
            user_expenses = list(user_expenses)
        except Exception as e:
            flash(f"Could not retrieve your expenses from collection '{session['username']}': {e}", "warning")
            print(f"Error fetching expenses for {session.get('username')} from collection '{session['username']}': {e}")
    else:
        flash("Database or user session not available to display expenses. Please check server logs.", "warning")

    return render_template('index.html', categories=categories, user_expenses=user_expenses)


@app.route('/get_items', methods=['POST'])
@login_required
def get_items():
    category = request.form.get('category')
    items = category_items.get(category, [])
    return jsonify(items)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    if db is not None and 'username' in session:
        category = request.form.get("category")
        item = request.form.get("item")
        amount_str = request.form.get("amount")

        if not category or not item or not amount_str:
            flash("Category, item, and amount are required.", "danger")
            return redirect(url_for('dashboard'))

        try:
            amount = float(amount_str)
            if amount <= 0:
                flash("Amount must be a positive number.", "danger")
                return redirect(url_for('dashboard'))
        except ValueError:
            flash("Invalid amount. Please enter a numerical value.", "danger")
            return redirect(url_for('dashboard'))

        other_text = request.form.get("other_text")
        final_item = item
        if item == "Others":
            if other_text and other_text.strip():
                final_item = other_text.strip()
            else:
                flash("You selected 'Others' but did not specify a value.", "danger")
                return redirect(url_for('dashboard'))

        user_expense_collection = db[session['username']]
        expense_document = {
            'user_id': ObjectId(session['user_id']),
            'username': session['username'],
            'category': category,
            'item': final_item,
            'amount': amount,
            'timestamp': datetime.utcnow() # Storing as UTC
        }

        try:
            user_expense_collection.insert_one(expense_document)
            flash(f"Expense recorded: '{final_item}' (Amount: ${amount:.2f}) in category '{category}'.", "success")
        except Exception as e:
            flash(f"An error occurred while saving your expense to collection '{session['username']}': {e}", "danger")
            print(f"Error inserting expense for user {session['username']} into collection '{session['username']}': {e}")
    else:
        flash("Database or user session not available for submitting expenses. Please try again later.", "danger")

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
