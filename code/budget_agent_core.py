import os
import json
api_key = os.environ.get("GCP_API_KEY")
import google.generativeai as genai
from PIL import Image

# 1. Initialize the Free AI Studio Client
# Put your free key in a .env file as GEMINI_API_KEY=your_key
genai.configure(api_key)

products_path = r"C:\Users\Main\Desktop\BudgetPro\BudgetPro-agent\mockdata\mock_products.json"
geo_path = r"C:\Users\Main\Desktop\BudgetPro\BudgetPro-agent\mockdata\mock_geo_listings.json"

# Load your mock data 
with open(products_path, "r") as f:
    products_db = json.load(f)
with open(geo_path, "r") as f:
    geo_db = json.load(f)

# --- FEATURE 2: Price Comparison (The "Honey" tool) ---
def compare_item_prices(item_name: str) -> str:
    """Searches the database for an item and compares prices across stores."""
    results = [p for p in products_db if item_name.lower() in p["name"].lower()]
    
    if not results:
        return f"No price data found for '{item_name}' in the database."
    
    # Sort by cheapest price
    results.sort(key=lambda x: x["price"])
    
    response = f"📊 Price Comparison for '{item_name}':\n"
    for r in results:
        response += f"- **{r['store']}**: ${r['price']:.2f} ({r['category']})\n"
    
    response += f"\n🏆 Cheapest option: {results[0]['store']} at ${results[0]['price']:.2f}!"
    return response

# --- FEATURE 3: Geospatial Search with Google Maps ---
def find_cheap_housing_and_food(location_type: str, max_price: int) -> str:
    """Finds apartments, restaurants, or markets under a specific price."""
    # Filter by type and max price
    results = [
        loc for loc in geo_db 
        if loc["type"].lower() == location_type.lower() and loc["price_indicator"] <= max_price
    ]
    
    if not results:
        return f"Could not find any {location_type}s under ${max_price}."
    
    # Sort by highest rating
    results.sort(key=lambda x: x["rating"], reverse=True)
    top_results = results[:3] # Return top 3 to the agent
    
    response = f"🗺️ Top {location_type}s under ${max_price}:\n"
    for r in top_results:
        lat, lon = r["location"]["lat"], r["location"]["location" if "location" in r else "lon"] # Handle JSON key mapping
        lon = r["location"]["lon"]
        # Generate the clickable Google Maps link
        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        
        response += f"- **{r['name']}** (⭐ {r['rating']}/5)\n"
        response += f"  Cost Indicator: ${r['price_indicator']}\n"
        response += f"  Details: {r['description']}\n"
        response += f"  📍 [Open in Google Maps]({maps_link})\n\n"
        
    return response

# --- SYSTEM INITIALIZATION ---
# Give the agent its persona and attach the tools
system_instruction = """
You are a financial survival agent. Your job is to help users save money.
When users ask for prices, use the compare_item_prices tool.
When users ask for local housing or food, use the find_cheap_housing_and_food tool.
Always maintain the markdown formatting returned by the tools, especially the Google Maps links.
"""

agent = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    tools=[compare_item_prices, find_cheap_housing_and_food],
    system_instruction=system_instruction
)

# --- FEATURE 2 ADD-ON: The Vision / Image Fallback ---
def handle_user_query(text_prompt: str, image_path: str = None):
    """Processes the query, optionally using Vision if an image is provided."""
    print(f"\nUser: {text_prompt}")
    
    inputs = [text_prompt]
    if image_path:
        print(f"[Attached Image: {image_path}]")
        img = Image.open(image_path)
        # Instruct Gemini to analyze the image and THEN use its tools
        vision_instruction = "Look at this image. Identify the product, then use your price comparison tool to find local deals for it."
        inputs = [vision_instruction, img]
        
    response = agent.generate_content(inputs)
    print(f"Agent:\n{response.text}")

# --- TEST RUNNER ---
if __name__ == "__main__":
    # Test Feature 3: Geo Search
    handle_user_query("I need a cheap apartment under $900.")
    
    # Test Feature 2: Text Price Comparison
    handle_user_query("What's the cheapest place to buy the Algorithmic Design Manual?")
    
    # Test Feature 2 Fallback: Image Upload 
    # (To test this, save any picture of ramen as 'ramen.jpg' in your folder)
    # handle_user_query("Can you find this for me cheap?", image_path="ramen.jpg")