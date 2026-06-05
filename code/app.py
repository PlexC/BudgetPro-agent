import streamlit as st
import json
import pandas as pd
import time
import datetime
import calendar
import base64
import plotly.express as px
import os
api_key = os.environ.get("GCP_API_KEY")
import google.generativeai as genai

# Page Config
st.set_page_config(page_title="Econ101 - Student Survival Agent", page_icon="💸", layout="wide")
st.title("💸 Econ101: Financial Survival Agent")

#update session state at the top of the file to include the Date column
if "my_budget_db" not in st.session_state:
    st.session_state.my_budget_db = pd.DataFrame(columns=["Date", "Type", "Category", "Amount"])

if "roommate_names" not in st.session_state:
    st.session_state.roommate_names = ["You"]

# --- ELASTICSEARCH DATABASE CONNECTOR ---
def fetch_deals_from_database():
    """ Connects to Elastic Cloud for crowdsourced deals. Falls back to local list if no cloud is active. """
    try:
        from elasticsearch import Elasticsearch
        # In production, replace with real URL and API Key
        es = Elasticsearch("hhttps://my-elasticsearch-project-b17b38.es.us-central1.gcp.elastic.cloud:443", api_key="S1lpV2xaNEJMUDV3UDlGOEV3YVg6VFJNc1FYUkwtN2lTbjdPbVFOOHJCZw==")
        response = es.search(index="late-night-deals", query={"match_all": {}}, size=50)
        records = [hit['_source'] for hit in response['hits']['hits']]
        if records: return pd.DataFrame(records)
    except Exception:
        pass 
        
    # Local fallback so demo never breaks
    return pd.DataFrame({
        "Store": ["Campus Bakery", "Night Market Sushi", "7-11 Uni-Branch"], 
        "Deal": ["50% off fresh bread", "Discounted sushi boxes", "Buy 1 Get 1 Riceballs"], 
        "Time": ["09:00 PM", "10:00 PM", "11:00 PM"]
    })

# --- 1. SIDEBAR LOGIN & SETTINGS ---
# --- INITIALIZE SETTINGS MEMORY ---
if "app_settings" not in st.session_state:
    st.session_state.app_settings = {
        "theme": "Dark (Default)", "bg_url": "", 
        "text_scale": 100, "text_color": "#FFFFFF", "volume": 80
    }

# --- SIDEBAR: LOGIN, SETTINGS & DATA ---
with st.sidebar:
    st.header("👤 Account")
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        if st.button("🌐 Sign in with Google"):
            st.session_state.logged_in = True; st.rerun()
    else:
        st.success("✅ Logged in as user@ntnu.edu.tw")
        if st.button("Sign Out"):
            st.session_state.logged_in = False; st.rerun()
            
    st.divider()
    
    # --- 1. APP SETTINGS (Tied to Save Data) ---
    with st.expander("⚙️ App Settings"):
        st.markdown("**Appearance**")
        theme_opts = ["Dark (Default)", "Light", "Custom Image (Link)", "Custom Image (Upload)"]
        
        # Sync the widget key with our app settings dictionary
        if "theme_choice" not in st.session_state:
            st.session_state.theme_choice = st.session_state.app_settings["theme"]
        
        # Using key="theme_choice" instead of index=theme_idx completely eliminates the glitch!
        theme = st.selectbox("Theme", theme_opts, key="theme_choice")
        
        bg_url = st.session_state.app_settings["bg_url"]
        if theme == "Custom Image (Link)":
            bg_url = st.text_input("Paste Image URL:", value=bg_url)
        elif theme == "Custom Image (Upload)":
            bg_file = st.file_uploader("Upload Background", type=["png", "jpg", "jpeg"], key="bg_image_uploader")
            if bg_file:
                import base64
                base64_img = base64.b64encode(bg_file.read()).decode()
                bg_url = f"data:{bg_file.type};base64,{base64_img}"
        elif theme in ["Dark (Default)", "Light"]:
            bg_url = "" 
        
        text_scale = st.slider("Text Scale (%)", 80, 150, st.session_state.app_settings["text_scale"])
        
        # Intelligent color snapping logic
        current_color = st.session_state.app_settings["text_color"]
        if theme == "Light" and (current_color == "#FFFFFF" or current_color == "#000000"): 
            current_color = "#CC9900" 
        elif theme == "Dark (Default)" and (current_color == "#CC9900" or current_color == "#000000"):
            current_color = "#FFFFFF" 
            
        text_color = st.color_picker("Text Color", current_color)
        
        st.markdown("**Audio**")
        volume = st.slider("Alert Volume (%)", 0, 100, st.session_state.app_settings["volume"])
        
        # Keep everything stored in the master dictionary
        st.session_state.app_settings = {
            "theme": theme, "bg_url": bg_url, 
            "text_scale": text_scale, "text_color": text_color, "volume": volume
        }

    # --- 2. DATA MANAGEMENT (Now includes Settings!) ---
    st.divider()
    st.header("💾 Data Management")
    
    uploaded_file = st.file_uploader("Import Save File (JSON)", type="json", key="json_data_uploader")
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.deals_db = pd.DataFrame(data.get('deals', []))
            st.session_state.roommate_db = pd.DataFrame(data.get('roommates', []))
            st.session_state.saved_places_db = pd.DataFrame(data.get('places', []))
            st.session_state.my_budget_db = pd.DataFrame(data.get('budget', []))
            
            if 'settings' in data:
                st.session_state.app_settings = data['settings']
                # ADD THIS LINE: Updates the dropdown widget immediately upon JSON import
                st.session_state.theme_choice = data['settings']['theme']
                
            st.success("Data & Settings fully restored!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error("Invalid file format.")

    if "deals_db" in st.session_state:
        export_data = {
            "deals": st.session_state.deals_db.to_dict('records'),
            "roommates": st.session_state.roommate_db.to_dict('records'),
            "places": st.session_state.saved_places_db.to_dict('records'),
            "budget": st.session_state.get("my_budget_db", pd.DataFrame()).to_dict('records'),
            "settings": st.session_state.app_settings # EXPORT THE SETTINGS
        }
        json_string = json.dumps(export_data, indent=2, default=str)
        st.download_button(label="⬇️ Export Save Data", file_name="econ101_backup.json", mime="application/json", data=json_string, use_container_width=True)

    # --- 3. DEEP CSS INJECTION (Fixes the Selectbox Bug) ---
    custom_css = f"""
    <style>
        /* Base scaling and coloring */
        html, body, [class*="css"] {{ font-size: {text_scale}% !important; }}
        p, h1, h2, h3, h4, h5, h6, span, label, li, .stMarkdown {{ color: {text_color} !important; }}
        
        /* THE FIX: Force Streamlit's hidden baseweb dropdowns to obey your color */
        div[data-baseweb="select"] * {{ color: {text_color} !important; }}
        
        /* Force the popup menu backgrounds to be safe (Black on Light, White on Dark) */
        ul[data-baseweb="menu"] {{ background-color: {"#FFFFFF" if theme == "Light" else "#262730"} !important; }}
        ul[data-baseweb="menu"] li * {{ color: {"#000000" if theme == "Light" else "#FFFFFF"} !important; }}
    """
    
    if theme == "Light":
        custom_css += """
        .stApp { background-color: #FFFFFF !important; }
        [data-testid="stSidebar"] { background-color: #F0F2F6 !important; }
        """
    elif theme == "Dark (Default)":
        custom_css += """
        .stApp { background-color: #0E1117 !important; }
        [data-testid="stSidebar"] { background-color: #262730 !important; }
        """
    elif "Custom Image" in theme and bg_url:
        custom_css += f"""
        .stApp {{ background-image: url("{bg_url}"); background-size: cover; background-attachment: fixed; background-position: center; }}
        [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.75) !important; }}
        """
        
    custom_css += "</style>"
    st.markdown(custom_css, unsafe_allow_html=True)
    
    
    # --- 4. LIVE OMNIPRESENT AI AGENT ---
    st.sidebar.divider()
    st.sidebar.header("💬 Econ101 AI Agent")
    st.sidebar.markdown("*Powered by Gemini 1.5. I can log your expenses if you tell me what you bought!*")
    
    # Text input for the API key so it's secure and not hardcoded
    AI_STUDIO_KEY = st.sidebar.text_input(
    "🔑 Enter Gemini API Key:", 
    type="password", 
    value=api_key, 
    key="agent_api_key_input"
)
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    for msg in st.session_state.chat_history:
        with st.sidebar.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.sidebar.chat_input("E.g., 'Log $15 for lunch'", disabled=not AI_STUDIO_KEY):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.sidebar.chat_message("user"):
            st.markdown(prompt)
            
        with st.sidebar.chat_message("assistant"):
            with st.spinner("Agent thinking..."):
                try:
                    # Set up the real AI connection
                    genai.configure(api_key=AI_STUDIO_KEY)
                    # Set up the real AI connection
                    genai.configure(api_key=AI_STUDIO_KEY)
                    model = genai.GenerativeModel(
                        model_name='gemini-2.5-flash', 
                        system_instruction="You are Econ101, an expert financial agent for a college student. Keep answers short, sharp, and highly protective of their budget."
                    )
                    
                    # Feed the AI the user's live budget data so it knows their situation
                    live_data = st.session_state.get('my_budget_db', pd.DataFrame()).to_dict('records')
                    context_primer = f"Current User Ledger: {live_data}\n\nUser Prompt: {prompt}"
                    
                    response = model.generate_content(context_primer)
                    reply = response.text
                    
                    # --- ACTION PARSER: Let the AI actually click buttons and log data for the user! ---
                    lowered_p = prompt.lower()
                    import re
                    amounts = re.findall(r"\d+(?:\.\d+)?", lowered_p)
                    
                    if ("add" in lowered_p or "log" in lowered_p or "spent" in lowered_p) and amounts:
                        target_amount = float(amounts[0])
                        b_type = "Income" if ("income" in lowered_p or "earned" in lowered_p) else "Expense"
                        b_cat = "Uncategorized"
                        if "for " in lowered_p: 
                            b_cat = prompt.split("for ")[-1].capitalize()
                        elif "on " in lowered_p: 
                            b_cat = prompt.split("on ")[-1].capitalize()
                        elif "as " in lowered_p: 
                            b_cat = prompt.split("as ")[-1].capitalize()
                        import datetime
                        new_entry = pd.DataFrame({"Date": [datetime.date.today()], "Type": [b_type], "Category": [b_cat], "Amount": [target_amount]})
                        st.session_state.my_budget_db = pd.concat([st.session_state.my_budget_db, new_entry], ignore_index=True)
                        
                        reply += f"\n\n⚙️ *[Agent Action: Automatically logged {b_type} of ${target_amount:.2f} for {b_cat}.]*"
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        time.sleep(1.5)
                        st.rerun() # Refresh app to show the new graph!
                    else:
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        
                except Exception as e:
                    # This will print the EXACT error Google is returning
                    st.error(f"API Error: {str(e)}")
                    st.session_state.chat_history.append({"role": "assistant", "content": f"System Error: {str(e)}"})
    


# --- LOAD MOCK BANK DATA ---
@st.cache_data
def load_data():
    try:
        file_path = r"C:\Users\Main\Desktop\BudgetPro\BudgetPro-agent\mockdata\mock_transactions.json"
        with open(file_path, "r") as f:
            return pd.DataFrame(json.load(f))
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

# --- INITIALIZE SESSION STATES ---
if "deals_db" not in st.session_state:
    st.session_state.deals_db = pd.DataFrame({
        "Store": ["Campus Bakery", "Night Market Sushi"], 
        "Deal": ["50% off bread", "Discounted boxes"], 
        "Time": ["09:00 PM", "10:00 PM"]
    })
if "roommate_db" not in st.session_state:
    st.session_state.roommate_db = pd.DataFrame(columns=["Payer", "Description", "Amount"])
if "saved_places_db" not in st.session_state:
    st.session_state.saved_places_db = pd.DataFrame(columns=["Name", "Type", "Note"])

# --- THE 4 MASTER TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "💰 Wealth & Splitter", 
    "🛍️ Deals Tracker", 
    "🗺️ Local Geo-Scout",
    "🛡️ Security Scanner"
])


# --- TAB 1: WEALTH & SPLITTER ---
with tab1:
    st.header("Financial Overview & Debt Ledger")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Bank Balance", "$1,450.22")
    col2.metric("Active Student Loans", "$12,500.00", delta="- Debt", delta_color="inverse")
    col3.metric("Monthly Spending", "$845.50")
    
    st.divider()
    
    st.subheader("📊 Dynamic Budget & Pie Chart")
    
    # Initialize the transaction memory if it's not there
    if "my_budget_db" not in st.session_state:
        st.session_state.my_budget_db = pd.DataFrame(columns=["Type", "Category", "Amount"])

    with st.form("budget_form", clear_on_submit=True):
        col_in1, col_in2, col_in3, col_in4 = st.columns(4)
        # Added native calendar picker!
        b_date = col_in1.date_input("Date")
        b_type = col_in2.selectbox("Type", ["Income", "Expense"])
        b_cat = col_in3.text_input("Category", placeholder="e.g., Salary, Rent")
        b_amount = col_in4.number_input("Amount ($)", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("Log Transaction") and b_cat and b_amount > 0:
            new_entry = pd.DataFrame({"Date": [b_date], "Type": [b_type], "Category": [b_cat], "Amount": [b_amount]})
            st.session_state.my_budget_db = pd.concat([st.session_state.my_budget_db, new_entry], ignore_index=True)
            st.rerun()

    # 2. Calculate Stats & Draw Pie Chart
    if not st.session_state.my_budget_db.empty:
        total_in = st.session_state.my_budget_db[st.session_state.my_budget_db["Type"] == "Income"]["Amount"].sum()
        total_out = st.session_state.my_budget_db[st.session_state.my_budget_db["Type"] == "Expense"]["Amount"].sum()
        net = total_in - total_out
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Income", f"${total_in:,.2f}")
        c2.metric("Total Spending", f"${total_out:,.2f}")
        c3.metric("Net Balance", f"${net:,.2f}")

        # Draw Pie Chart for Expenses
        expenses_only = st.session_state.my_budget_db[st.session_state.my_budget_db["Type"] == "Expense"]
        if not expenses_only.empty:
            fig = px.pie(expenses_only, values="Amount", names="Category", title="Spending Breakdown")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add income or expenses above to see your stats and chart!")
    
    st.subheader("🍕 Internal Debts (Roommate Ledger)")
    col_log, col_summary = st.columns([2, 1])
    with col_log:
        cols_rm = st.columns([3, 1])
        new_rm = cols_rm[0].text_input("Add a Roommate", placeholder="e.g., Sarah", label_visibility="collapsed")
        if cols_rm[1].button("Add Name") and new_rm:
            if new_rm not in st.session_state.roommate_names:
                st.session_state.roommate_names.append(new_rm)
                st.rerun()
                
        with st.form("expense_form", clear_on_submit=True):
            cols = st.columns(3)
            payer = cols[0].selectbox("Who paid?", st.session_state.roommate_names)
            desc = cols[1].text_input("For what?", placeholder="e.g., Electric Bill")
            amount = cols[2].number_input("Amount ($)", min_value=0.0, format="%.2f")
            
            # This is the only button allowed inside a form!
            if st.form_submit_button("Add to Ledger") and desc:
                new_expense = pd.DataFrame({"Payer": [payer], "Description": [desc], "Amount": [amount]})
                st.session_state.roommate_db = pd.concat([st.session_state.roommate_db, new_expense], ignore_index=True)
                st.rerun()
                
        st.dataframe(st.session_state.roommate_db, use_container_width=True, hide_index=True)

    with col_summary:
        if not st.session_state.roommate_db.empty:
            total = st.session_state.roommate_db["Amount"].sum()
            per_person = total / 3
            st.write(f"**Fair Share:** ${per_person:.2f} each")
            st.button("📱 Generate Venmo Requests", type="primary")
        else:
            st.info("No shared expenses.")
    
    st.divider()

    # --- 2. DAILY ACCOUNTING LEDGER ---
    # --- MONTHLY CALENDAR GRID ---
    st.markdown("**📅 Full Monthly Calendar**")
    
    # Process the budget data if it exists
    if not st.session_state.my_budget_db.empty:
        cal_df = st.session_state.my_budget_db.copy()
        cal_df['Date'] = pd.to_datetime(cal_df['Date']).dt.date
        
        daily = cal_df.groupby(['Date', 'Type'])['Amount'].sum().unstack(fill_value=0)
        if 'Income' not in daily.columns: daily['Income'] = 0.0
        if 'Expense' not in daily.columns: daily['Expense'] = 0.0
        daily['Net'] = daily['Income'] - daily['Expense']
        
        # Create a quick dictionary to look up dates instantly
        daily_dict = {idx: row['Net'] for idx, row in daily.iterrows()}
    else:
        daily_dict = {}

    # Setup the current month's calendar layout
    today = datetime.date.today()
    cal = calendar.monthcalendar(today.year, today.month)
    month_name = calendar.month_name[today.month]

    st.markdown(f"### {month_name} {today.year}")
    
    # Draw the Days of the Week Header
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, day in enumerate(days_of_week):
        header_cols[i].markdown(f"<center><b>{day}</b></center>", unsafe_allow_html=True)
        
    # Draw the dynamic grid
    for week in cal:
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            with week_cols[i]:
                if day == 0:
                    # Empty days before the 1st or after the 31st
                    st.write("") 
                else:
                    current_date = datetime.date(today.year, today.month, day)
                    
                    # Determine coloring based on spending
                    if current_date in daily_dict:
                        net = daily_dict[current_date]
                        box_color = "#2e7d32" if net > 0 else "#c62828" if net < 0 else "rgba(128,128,128,0.2)"
                        amount_str = f"${net:,.0f}"
                    else:
                        box_color = "rgba(128,128,128,0.05)"
                        amount_str = "-"
                        
                    # Render the individual calendar day cell
                    st.markdown(
                        f"""<div style='background-color:{box_color}; border: 1px solid rgba(128,128,128,0.3); 
                        padding:5px; border-radius:5px; text-align:center; min-height: 70px; margin-bottom:5px;'>
                        <small style='font-size: 14px;'>{day}</small><br>
                        <b>{amount_str}</b>
                        </div>""", 
                        unsafe_allow_html=True
                    )
    st.divider()
    
    st.subheader("📅 Daily Accounting Ledger")
    
    if not st.session_state.my_budget_db.empty:
        # The Calendar Filter
        filter_date = st.date_input("Filter by Specific Date", value=None, key="filter_cal")
        
        display_df = st.session_state.my_budget_db.copy()
        
        # Apply the calendar filter if a date is picked
        if filter_date:
            # Convert both to datetime to ensure matching
            display_df['Date'] = pd.to_datetime(display_df['Date']).dt.date
            display_df = display_df[display_df['Date'] == filter_date]
            
        if display_df.empty:
            st.info("No transactions logged on this date.")
        else:
            st.markdown("*Tip: Select a row and press 'Delete' to remove it.*")
            # Update the session state ONLY if they aren't actively filtering, 
            # otherwise deleting a filtered row gets complex in Streamlit
            if not filter_date:
                st.session_state.my_budget_db = st.data_editor(
                    st.session_state.my_budget_db, 
                    num_rows="dynamic", 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- TAB 2: DEALS TRACKER (RESTORED FEATURES!) ---
with tab2:
    st.header("⏰ Late-Night Local Deals")
    # --- PASTE THIS AT THE TOP OF TAB 2 ---
    st.subheader("🔍 Honey-Style Price Scanner")
    search_item = st.text_input("What are you buying?", placeholder="e.g., Sony WH-1000XM4 Headphones")
    if st.button("Scan the Web for Best Price"):
        with st.spinner("Scraping online marketplaces..."):
            time.sleep(1.5)
            st.success(f"Found the best deals for **{search_item}**!")
            cols_price = st.columns(3)
            cols_price[0].metric("Marketplace A", "$249.00", delta="Best Price", delta_color="normal")
            cols_price[1].metric("Marketplace B", "$275.00", delta="Average", delta_color="off")
            cols_price[2].metric("Marketplace C", "$299.00", delta="Expensive", delta_color="inverse")
    st.divider()
    st.dataframe(st.session_state.deals_db, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # RESTORED: Add Custom Deal
    st.subheader("➕ Add a Custom Deal")
    with st.form("add_deal_form", clear_on_submit=True):
        col_form1, col_form2, col_form3 = st.columns(3)
        with col_form1:
            new_store = st.text_input("Store Name")
        with col_form2:
            new_deal = st.text_input("Deal Description")
        with col_form3:
            new_time = st.time_input("Deal Time (Starts at)")
            
        if st.form_submit_button("Save to Tracker") and new_store and new_deal:
            formatted_time = new_time.strftime("%I:%M %p")
            new_row = pd.DataFrame({"Store": [new_store], "Deal": [new_deal], "Time": [formatted_time]})
            st.session_state.deals_db = pd.concat([st.session_state.deals_db, new_row], ignore_index=True)
            st.rerun()
            
    # RESTORED: Delete Deal
    if not st.session_state.deals_db.empty:
        col_del1, col_del2 = st.columns([3, 1])
        with col_del1:
            deal_to_remove = st.selectbox("Remove a deal", st.session_state.deals_db["Store"].unique())
        with col_del2:
            st.write("") 
            st.write("") 
            if st.button("Delete Deal"):
                st.session_state.deals_db = st.session_state.deals_db[st.session_state.deals_db["Store"] != deal_to_remove].reset_index(drop=True)
                st.rerun()
    
    st.divider()
    # RESTORED: Smart Alarm System
    st.subheader("🔔 Set a Smart Reminder")
    if not st.session_state.deals_db.empty:
        colA, colB = st.columns(2)
        with colA:
            store_choice = st.selectbox("Select Store Deal for Alarm", st.session_state.deals_db["Store"])
        with colB:
            reminder_time = st.selectbox("Remind me...", ["15 minutes before", "30 minutes before", "1 hour before"])
            
        if st.button("Activate Agent Alarm"):
            st.success(f"Alarm set for {store_choice} at {reminder_time}!")
            
            # --- HACKATHON DEMO TRICK: INSTANT NOISE & POPUP ---
            # Plays a notification chime
            audio_html = """
            <audio autoplay>
            <source src="https://assets.mixkit.co/sfx/preview/mixkit-software-interface-start-2574.mp3" type="audio/mp3">
            </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
            # Slides a beautiful pop-up notification onto the screen
            st.toast(f"⏰ DEMO ALERT: Your {store_choice} deal is starting!", icon="🚨")
    else:
        st.warning("Add deals to set an alarm.")

# --- TAB 3: LOCAL GEO-SCOUT (NEW MAP & SAVES) ---
with tab3:
    st.header("🗺️ Dynamic Geo-Scout")
    
    # 1. Location Settings Toggle
    st.markdown("Finding student-budget friendly living and dining in your area.")
    use_gps = st.toggle("📍 Use Current Device Location (GPS)", value=False)
    
    if use_gps:
        st.success("GPS Location acquired: **West District, Taichung City**")
        current_loc = "Taichung"
    else:
        # --- MASSIVE COUNTRY/CITY DATABASE ---
        # --- MASSIVE COUNTRY/CITY DATABASE ---
        world_data = {
            "Taiwan": ["Taipei", "Taichung", "Kaohsiung", "Tainan", "Hsinchu"],
            "United States": ["New York", "Los Angeles", "Chicago", "Houston", "San Francisco"],
            "UK": ["London", "Manchester", "Birmingham", "Edinburgh"],
            "Japan": ["Tokyo", "Osaka", "Kyoto", "Sapporo"],
            "South Korea": ["Seoul", "Busan", "Incheon"]
        }
        
        # New Coordinate Dictionary for dynamic snapping!
        city_coords = {
            "Taipei": [25.0330, 121.5654], "Taichung": [24.1477, 120.6736], "Kaohsiung": [22.6273, 120.3014], "Tainan": [22.9997, 120.2270], "Hsinchu": [24.8138, 120.9675],
            "New York": [40.7128, -74.0060], "Los Angeles": [34.0522, -118.2437], "Chicago": [41.8781, -87.6298], "Houston": [29.7604, -95.3698], "San Francisco": [37.7749, -122.4194],
            "London": [51.5074, -0.1278], "Manchester": [53.4808, -2.2426], "Birmingham": [52.4862, -1.8904], "Edinburgh": [55.9533, -3.1883],
            "Tokyo": [35.6762, 139.6503], "Osaka": [34.6937, 135.5023], "Kyoto": [35.0116, 135.7681], "Sapporo": [43.0618, 141.3545],
            "Seoul": [37.5665, 126.9780], "Busan": [35.1796, 129.0756], "Incheon": [37.4563, 126.7052]
        }
        
        col_loc1, col_loc2 = st.columns(2)
        selected_country = col_loc1.selectbox("Country", list(world_data.keys()))
        current_loc = col_loc2.selectbox("City", world_data[selected_country])

    # 2. Dynamic Map (Snaps dynamically based on location)
    if current_loc == "Taichung":
        # Keep your detailed hackathon demo points for Taichung
        map_data = pd.DataFrame({
            'lat': [24.1480, 24.1550, 24.1450, 24.1400],
            'lon': [120.6550, 120.6600, 120.6650, 120.6700],
            'Name': ['Gongyi Rd Studio', 'Taiwan Blvd Flat', 'Local Dumpling Cart', 'Student Noodles']
        })
        zoom_level = 13
    else:
        # Dynamically grab the coordinates for whatever city they chose
        coords = city_coords.get(current_loc, [40.7128, -74.0060]) 
        map_data = pd.DataFrame({'lat': [coords[0]], 'lon': [coords[1]], 'Name': [current_loc]})
        zoom_level = 11 # Zoom out slightly for generic cities

    st.map(map_data, zoom=zoom_level, use_container_width=True)
    st.divider()
    
    col_explore, col_saved = st.columns([2, 1])
    
    with col_explore:
        st.subheader("🔍 Explore")
        # Global text input for your custom category!
        save_category = st.text_input("Save to Category (e.g., 'YouTube Saves', 'Must Try Food'):", "General")
        
        st.info("**Gongyi Road Studio** - $450/mo")
        if st.button("❤️ Save Studio"):
            new_save = pd.DataFrame({"Name": ["Gongyi Rd Studio"], "Category": [save_category], "Note": ["$450/mo"]})
            st.session_state.saved_places_db = pd.concat([st.session_state.saved_places_db, new_save], ignore_index=True)
            st.rerun()
            
        st.success("**Local Dumpling Cart** - Cheap, open late.")
        if st.button("❤️ Save Dumpling Cart"):
            new_save = pd.DataFrame({"Name": ["Local Dumpling Cart"], "Category": [save_category], "Note": ["Cheap Eats"]})
            st.session_state.saved_places_db = pd.concat([st.session_state.saved_places_db, new_save], ignore_index=True)
            st.rerun()

    with col_saved:
        st.subheader("📌 Your Bookmarks")
        if not st.session_state.saved_places_db.empty:
            # Let the user filter by their custom categories!
            all_cats = ["All"] + list(st.session_state.saved_places_db["Category"].unique())
            filter_cat = st.selectbox("Filter Category", all_cats)
            
            display_db = st.session_state.saved_places_db
            if filter_cat != "All":
                display_db = display_db[display_db["Category"] == filter_cat]
                
            st.dataframe(display_db, use_container_width=True, hide_index=True)
            if st.button("Clear Bookmarks"):
                st.session_state.saved_places_db = pd.DataFrame(columns=["Name", "Category", "Note"])
                st.rerun()
        else:
            st.info("No places saved yet.")


# --- TAB 4: SECURITY SCANNER ---
with tab4:
    st.header("🛡️ Fraud & Anomaly Scanner")
    st.markdown("Scanning your live budget, roommate ledgers, and location data for anomalies.")
    
    if st.button("🔍 Run Full Data Audit", type="primary"):
        with st.spinner("Cross-referencing databases..."):
            time.sleep(1.5)
            
            # 1. Scan Live Budget for Duplicates
            found_issue = False
            if "my_budget_db" in st.session_state and not st.session_state.my_budget_db.empty:
                budget = st.session_state.my_budget_db
                expenses = budget[budget["Type"] == "Expense"]
                
                # Check duplicates (same category & amount)
                duplicates = expenses[expenses.duplicated(subset=['Category', 'Amount'], keep=False)]
                if not duplicates.empty:
                    dup_val = duplicates.iloc[0]['Amount']
                    dup_cat = duplicates.iloc[0]['Category']
                    st.warning(f"**Duplicate Charges Detected!** You logged multiple charges for ${dup_val:.2f} in '{dup_cat}'. Was this an accident?")
                    found_issue = True
                    
                # Check for unusually high spending for a student
                high_spend = expenses[expenses['Amount'] > 500]
                if not high_spend.empty:
                    st.warning(f"**High Spending Alert!** A massive charge of ${high_spend.iloc[0]['Amount']:.2f} was detected in '{high_spend.iloc[0]['Category']}'.")
                    found_issue = True
            
            if not found_issue:
                st.success("✅ Your local budget logs look clean. No duplicate charges found.")

            st.divider()

            # 2. Geo-Anomaly (The Demo Trick)
            st.error("**URGENT: Geographical Anomaly Detected** \nCard present transaction at 'London, UK' for $85.00. \n\n*System Note: Your current active GPS location is Taichung City. This transaction is impossible.*")
            
            if st.button("🚨 Freeze Card Immediately"):
                st.success("Card frozen. A new virtual card has been issued to your mobile wallet.")