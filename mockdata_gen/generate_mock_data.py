import json
import random
from datetime import datetime, timedelta

# Configuration for reproducibility
random.seed(42)

# --- 1. SPENDING & LOAN TRANSACTIONS (500+ records) ---
def generate_transactions(num_records=550):
    categories = {
        "Food/Dining": ["Ramen House", "Campus Cafeteria", "Starbucks", "Boba Tea", "Trader Joe's", "McDonalds"],
        "Housing/Utilities": ["Monthly Rent Payment", "Electric Bill", "Water Utility", "Internet Service"],
        "Education": ["University Bookstore", "Tuition Installment", "Lab Fees", "Online Course Sub"],
        "Entertainment": ["Netflix", "Spotify", "Steam Games", "Movie Theater", "Concert Ticket"],
        "Transportation": ["Uber/Lyft", "Gas Station", "Subway Pass", "Train Ticket"],
        "Income/Passive": ["Part-time Job Stipend", "Freelance Coding Contract", "Allowance", "Stock Dividend"]
    }
    
    transactions = []
    start_date = datetime.now() - timedelta(days=90)
    
    # Base loan tracking record
    transactions.append({
        "transaction_id": "tx_loan_001",
        "date": (datetime.now() - timedelta(days=85)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "merchant": "Student Loan Corp",
        "category": "Education",
        "amount": -15000.00,  # Negative for debt/loan balance
        "type": "loan",
        "description": "Subsidized federal student loan disbursement balance",
        "location": {"lat": 42.3601, "lon": -71.0589} # Default campus area
    })

    for i in range(num_records):
        category = random.choice(list(categories.keys()))
        merchant = random.choice(categories[category])
        
        # Determine amount logic
        if category == "Income/Passive":
            amount = round(random.uniform(50, 1200), 2)
            type_field = "income"
        elif category == "Housing/Utilities" and "Rent" in merchant:
            amount = 850.00  # Standard flat rent
            type_field = "expense"
        else:
            amount = round(random.uniform(4.50, 150), 2)
            type_field = "expense"
            
        random_days = random.randint(0, 90)
        tx_date = start_date + timedelta(days=random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        # Simulate a fraudulent transaction far away for testing
        is_fraud = (i == 42)
        lat = random.uniform(51.4, 51.6) if is_fraud else random.uniform(42.34, 42.38)
        lon = random.uniform(-0.2, -0.1) if is_fraud else random.uniform(-71.08, -71.04)
        
        transactions.append({
            "transaction_id": f"tx_{i:03d}",
            "date": tx_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "merchant": "Unrecognized London Shop" if is_fraud else merchant,
            "category": "Uncategorized" if is_fraud else category,
            "amount": 499.99 if is_fraud else amount,
            "type": "expense" if is_fraud else type_field,
            "description": "Suspicious international transaction alert" if is_fraud else f"Purchase at {merchant} under {category}",
            "location": {"lat": lat, "lon": lon}
        })
        
    return transactions

# --- 2. APARTMENTS, RESTAURANTS & MARKETS (100+ records) ---
def generate_geo_listings(num_records=120):
    listing_types = ["Apartment", "Restaurant", "Market"]
    adjectives = ["Cozy", "Budget", "Luxury", "Student-friendly", "Cheap", "Quiet", "Local"]
    
    listings = []
    for i in range(num_records):
        l_type = random.choice(listing_types)
        adj = random.choice(adjectives)
        
        if l_type == "Apartment":
            name = f"{adj} Campus Studio #{random.randint(10, 500)}"
            price = random.randint(650, 1400)
            desc = f"A {adj.lower()} 1-bedroom setup near university. Includes free Wi-Fi, laundry facilities, and a study lounge. Perfect for student budgets."
        elif l_type == "Restaurant":
            name = f"{adj} Eaters {random.choice(['Diner', 'Noodle Bar', 'Bistro', 'Kitchen'])}"
            price = random.randint(8, 25) # Avg meal cost
            desc = f"Great {adj.lower()} food options with excellent student discounts. Popular for late-night study sessions."
        else:
            name = f"{adj} {random.choice(['Groceries', 'Foods', 'Wholesale', 'Corner Store'])}"
            price = random.randint(5, 50) # Budget rating indicator
            desc = f"Affordable wholesale bulk grocery options, fresh vegetables, and cheap ramen supply."

        listings.append({
            "listing_id": f"list_{i:03d}",
            "name": name,
            "type": l_type,
            "price_indicator": price,
            "rating": round(random.uniform(3.2, 5.0), 1),
            "description": desc,
            "location": {
                "lat": random.uniform(42.34, 42.38),
                "lon": random.uniform(-71.08, -71.04)
            }
        })
    return listings

# --- 3. ONLINE PRODUCT PRICE COMPARISON (50+ records) ---
def generate_products():
    base_products = [
        {"name": "Introduction to Computer Systems Textbook", "category": "Books"},
        {"name": "Algorithmic Design Manual 3rd Edition", "category": "Books"},
        {"name": "15-inch Student Productivity Laptop", "category": "Electronics"},
        {"name": "Ergonomic Mesh Study Chair", "category": "Furniture"},
        {"name": "Noise Cancelling Wireless Headphones", "category": "Electronics"},
        {"name": "Pack of 24 Chicken Flavor Instant Ramen", "category": "Groceries"},
        {"name": "Stainless Steel Thermal Water Bottle", "category": "Gear"}
    ]
    
    stores = ["EduMart", "Amezon", "GlobalStore", "CampusShop"]
    products_dataset = []
    
    idx = 0
    for bp in base_products:
        # Create records across multiple stores to let the agent compare them
        base_price = random.uniform(15.0, 900.0) if bp["category"] == "Electronics" else random.uniform(10.0, 150.0)
        
        for store in stores:
            price_variance = random.uniform(-0.20, 0.20) # Up to 20% price difference
            final_price = round(base_price * (1 + price_variance), 2)
            
            products_dataset.append({
                "product_id": f"prod_{idx:03d}",
                "name": bp["name"],
                "category": bp["category"],
                "store": store,
                "price": final_price,
                "description": f"Official {bp['name'].lower()} item available at {store}. Check eligibility for standard student financing options."
            })
            idx += 1
            
    return products_dataset

# Save all data to json
if __name__ == "__main__":
    with open("mock_transactions.json", "w") as f:
        json.dump(generate_transactions(), f, indent=2)
        
    with open("mock_geo_listings.json", "w") as f:
        json.dump(generate_geo_listings(), f, indent=2)
        
    with open("mock_products.json", "w") as f:
        json.dump(generate_products(), f, indent=2)
        
    print("Successfully generated mock_transactions.json, mock_geo_listings.json, and mock_products.json!")