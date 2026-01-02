import streamlit as st
import database as db
import auth
import pandas as pd
import plotly.express as px  # NEW: For beautiful charts
import streamlit.components.v1 as components

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Okeb Nigeria", page_icon="🏢", layout="wide")

# CUSTOM CSS FOR MODERN UI
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Sidebar Styling - Dark Blue like your image */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    
    /* Card Styling for Metrics & Forms */
    div[data-testid="stMetric"], div.stForm {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* Input Fields Styling */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: #f1f5f9;
        border: none;
        border-radius: 5px;
        padding: 10px;
    }
    
    /* Button Styling */
    .stButton button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #2563eb;
        transform: scale(1.02);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #1e293b;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. HELPERS ---
def add_print_button():
    with st.sidebar:
        st.markdown("---")
        components.html("""<script>function printMain() { window.parent.print(); }</script><div style="text-align: center;"><button onclick="printMain()" style="background-color: #FF4B4B; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">🖨️ PRINT REPORT</button></div>""", height=60)

def manage_debtors(key_prefix):
    if f'{key_prefix}_debtors' not in st.session_state: st.session_state[f'{key_prefix}_debtors'] = [{"name": "", "amount": 0.0}]
    st.markdown("#### 📋 Debtors List")
    edited = st.data_editor(st.session_state[f'{key_prefix}_debtors'], num_rows="dynamic", column_config={"name": "Customer Name", "amount": st.column_config.NumberColumn("Amount (₦)", format="%d")}, key=f"{key_prefix}_editor", use_container_width=True)
    return edited, sum([r['amount'] for r in edited if r['amount']])

def clear_fuel():
    for k in ['read_p1_open', 'read_p1_close', 'read_p2_open', 'read_p2_close', 'fuel_cash', 'fuel_pos']: st.session_state[k] = 0.0
    st.session_state.fuel_debtors = [{"name": "", "amount": 0.0}]

def clear_farm():
    st.session_state.farm_cart = [{"Product": "Crates of Eggs", "Qty": 1, "Unit Price": 3500}]
    for k in ['farm_cust', 'farm_phone', 'farm_note']: st.session_state[k] = ""
    st.session_state.farm_paid = 0.0

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""
if 'dept' not in st.session_state: st.session_state.dept = ""

# --- 4. MAIN APP ---
if not st.session_state.logged_in:
    auth.login()
else:
    all_prices = db.get_prices()
    if 'fuel_staff' not in st.session_state: st.session_state.fuel_staff = st.session_state.user.upper()
    if 'p1_setup' not in st.session_state: st.session_state.p1_setup = "Pump 1"
    if 'p2_setup' not in st.session_state: st.session_state.p2_setup = "Pump 2"
    current_fuel_price = all_prices.get("Fuel Unit Price", 700.0)

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/900/900782.png", width=50) # Placeholder Logo
        st.title("OKEB NIGERIA")
        st.caption("Enterprise Portal")
        st.write(f"User: **{st.session_state.user.upper()}**")
        
        if st.session_state.role == "ADMIN":
            menu = ["Dashboard", "POS Dept", "Fuel Dept", "Bakery Dept", "Farm Dept", "Debt Recovery", "⚙️ Price Settings", "🔧 Database Admin"]
        else:
            menu = [st.session_state.dept + " Dept"]
        selection = st.radio("", menu) # Empty label for cleaner look
        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    add_print_button()

    # === MODULE A: DASHBOARD (WITH CHART & INSIGHTS) ===
    if selection == "Dashboard":
        st.title("Executive Dashboard")
        st.caption(f"Overview for {db.datetime.now().strftime('%B %Y')}")
        
        rev, exp, net, debt, recent = db.get_dashboard_metrics()
        
        # 1. METRIC CARDS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"₦{rev:,.2f}", "+")
        c2.metric("Total Expenses", f"₦{exp:,.2f}", "-")
        c3.metric("Net Cash Position", f"₦{net:,.2f}")
        c4.metric("Outstanding Debt", f"₦{debt:,.2f}", "high", delta_color="inverse")
        
        st.markdown("---")
        
        # 2. CHART & RECOMMENDATIONS
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.subheader("📊 Revenue Trends")
            # Fetch daily data for chart
            conn = db.sqlite3.connect(db.DB_NAME)
            try:
                chart_df = pd.read_sql_query("SELECT date, department, gross_revenue FROM daily_sales", conn)
                if not chart_df.empty:
                    fig = px.bar(chart_df, x='date', y='gross_revenue', color='department', title="Daily Revenue by Department", barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for charts yet.")
            except:
                st.error("Could not load chart data.")
            conn.close()

        with c_right:
            st.subheader("🤖 AI Insights")
            recommendations = []
            if debt > 50000:
                recommendations.append("🚨 **High Debt Alert:** Outstanding debt is over ₦50k. Focus on Debt Recovery this week.")
            if net < 0:
                recommendations.append("⚠️ **Cash Flow Warning:** Expenses exceed Revenue. Review spending immediately.")
            if rev > 0 and (net/rev) > 0.2:
                recommendations.append("✅ **Healthy Margins:** You are retaining >20% of revenue as cash.")
            else:
                recommendations.append("ℹ️ **Tip:** Monitor POS charges daily to ensure commissions cover bank fees.")
            
            if not recommendations:
                st.success("Operations are running smoothly.")
            else:
                for rec in recommendations:
                    st.write(rec)

        st.markdown("---")
        st.subheader("📋 Recent Debtors List")
        st.dataframe(recent, use_container_width=True)

    # === MODULE B: POS ===
    elif selection == "POS Dept":
        st.markdown("## 🏧 POS Terminal Operations")
        staff = st.text_input("Staff Name", value=st.session_state.user.upper(), key="pos_st")
        
        with st.form("pos_form"):
            st.markdown("### 1. Opening Balance")
            c1, c2, c3 = st.columns(3)
            with c1: mach = st.text_input("Terminal Name")
            with c2: op_cash = st.number_input("Opening Cash", step=1000.0)
            with c3: op_wall = st.number_input("Opening Wallet", step=1000.0)
            cap = st.number_input("Capital Given", step=1000.0)
            
            st.markdown("### 2. Transaction Volume")
            c1, c2, c3, c4 = st.columns(4)
            with c1: dep = st.number_input("Deposits", min_value=0.0)
            with c2: wit = st.number_input("Withdrawals", min_value=0.0)
            with c3: other = st.number_input("Utility/Bill Txns", min_value=0.0)
            with c4: free_vol = st.number_input("Free/Exempted", min_value=0.0)
            
            total_vol = dep + wit + other
            chargeable = total_vol - free_vol
            st.info(f"📊 Volume: **₦{total_vol:,.2f}** | Chargeable: **₦{chargeable:,.2f}**")
            
            st.markdown("### 3. Profit Analysis")
            exp_comm = chargeable * 0.02
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Std Commission (2%)", f"₦{exp_comm:,.2f}")
            with c2: act_comm = st.number_input("Actual Charges Collected", min_value=0.0)
            with c3: bank = st.number_input("Bank Charges", min_value=0.0)
            
            net_profit = act_comm - bank
            st.metric("NET PROFIT", f"₦{net_profit:,.2f}", delta=f"{act_comm - exp_comm:,.2f} vs Std")
            
            st.markdown("### 4. Closing")
            c1, c2, c3 = st.columns(3)
            with c1: cl_cash = st.number_input("Closing Cash", min_value=0.0)
            with c2: cl_wall = st.number_input("Closing Wallet", min_value=0.0)
            with c3: remit = st.number_input("Remitted Cash", min_value=0.0)
            
            if st.form_submit_button("CLOSE ACCOUNT", type="primary"):
                start = op_cash + op_wall + cap
                end = cl_cash + cl_wall + remit
                expected_end = start + net_profit
                diff = end - expected_end
                status = "✅ BALANCED" if abs(diff) < 50 else ("⚠️ SURPLUS" if diff > 0 else "🚨 SHORTAGE")
                
                db.save_pos_entry({"date": db.datetime.now().strftime("%Y-%m-%d %H:%M"), "staff": staff, "machine": mach, "open_cash": op_cash, "open_wallet": op_wall, "capital": cap, "deposits": dep, "withdrawals": wit, "free": free_vol, "volume": total_vol, "expected": exp_comm, "actual": act_comm, "bank": bank, "profit": net_profit, "close_cash": cl_cash, "close_wallet": cl_wall, "balance": diff, "status": status})
                st.success(f"Saved! Status: {status}")
        
        with st.expander("View History"): st.dataframe(db.get_pos_history(), use_container_width=True)

    # === MODULE C: FUEL ===
    elif selection == "Fuel Dept":
        st.markdown("## ⛽ Fuel Operations")
        c1, c2 = st.columns([3, 1])
        with c1: staff = st.text_input("Staff Name", value=st.session_state.user.upper(), key="fuel_staff")
        with c2: 
            if st.button("🔄 Start New Shift"): clear_fuel(); st.rerun()
        
        with st.container():
            st.markdown(f"**{st.session_state.p1_setup}**")
            c1, c2 = st.columns(2)
            p1_op = c1.number_input("Opening", key="read_p1_open")
            p1_cl = c2.number_input("Closing", key="read_p1_close")
            
            st.markdown(f"**{st.session_state.p2_setup}**")
            c1, c2 = st.columns(2)
            p2_op = c1.number_input("Opening", key="read_p2_open")
            p2_cl = c2.number_input("Closing", key="read_p2_close")
        
        tot_lit = (p1_cl - p1_op) + (p2_cl - p2_op)
        price = st.number_input("Price/Liter", value=current_fuel_price, disabled=True)
        exp_rev = tot_lit * price
        st.info(f"Target: **{tot_lit:.1f}L** | **₦{exp_rev:,.2f}**")
        
        c1, c2 = st.columns(2)
        with c1: cash = st.number_input("Cash", key="fuel_cash")
        with c2: pos = st.number_input("POS", key="fuel_pos")
        
        debtors, credit = manage_debtors("fuel")
        st.metric("Total Credit", f"₦{credit:,.2f}")
        
        diff = (cash + pos + credit) - exp_rev
        if (cash + pos + credit) > 0:
            if abs(diff) < 50: st.success("✅ Balanced!")
            elif diff > 0: st.warning(f"⚠️ Surplus: {diff:.2f}")
            else: st.error(f"🚨 Shortage: {diff:.2f}")
            
        if st.button("💾 SAVE RECORD", type="primary"):
            db.save_fuel_entry({"date": db.datetime.now().strftime("%Y-%m-%d %H:%M"), "staff": staff, "p1_name": st.session_state.p1_setup, "pA_open": p1_op, "pA_close": p1_cl, "p2_name": st.session_state.p2_setup, "pB_open": p2_op, "pB_close": p2_cl, "total_liters": tot_lit, "price": price, "expected": exp_rev, "cash": cash, "pos": pos, "credit": credit, "diff": diff, "debtors_list": debtors})
            st.success("Saved!")
        with st.expander("History"): st.dataframe(db.get_fuel_history(), use_container_width=True)

    # === MODULE D: BAKERY ===
    elif selection == "Bakery Dept":
        st.markdown("## 🍞 Bakery Operations")
        staff = st.text_input("Staff Name", value=st.session_state.user.upper(), key="bakery_staff_key")
        
        h1, h2, h3, h4, h5, h6, h7 = st.columns([1.5, 1, 1, 1, 1, 1, 1])
        h1.markdown("**TYPE**"); h2.markdown("**OPEN**"); h3.markdown("**PROD**"); h4.markdown("**GIVEN**"); h5.markdown("**UNSOLD**"); h6.markdown("**BAD**"); h7.markdown("**SOLD**")
        
        total_exp = 0; total_sold = 0; inputs = {}
        bakery_items = {k:v for k,v in all_prices.items() if "Fuel" not in k}
        
        for b, p in bakery_items.items():
            c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 1, 1, 1, 1, 1, 1])
            with c1: st.markdown(f"**{b}**\n<small>₦{p:,.0f}</small>", unsafe_allow_html=True)
            with c2: op = st.number_input(f"o{b}", 0, label_visibility="collapsed")
            with c3: pr = st.number_input(f"p{b}", 0, label_visibility="collapsed")
            with c4: gv = st.number_input(f"g{b}", 0, label_visibility="collapsed")
            with c5: rt = st.number_input(f"r{b}", 0, label_visibility="collapsed")
            with c6: dm = st.number_input(f"d{b}", 0, label_visibility="collapsed")
            sold = (op + pr) - (gv + rt + dm)
            rev = sold * p
            total_exp += rev; total_sold += sold
            inputs[b] = {"dm": dm}
            with c7: st.write(f"**{sold}**")
            
        st.info(f"Target: ₦{total_exp:,.2f}")
        c1, c2 = st.columns(2)
        with c1: cash = st.number_input("Cash", key="b_cash")
        with c2: pos = st.number_input("POS", key="b_pos")
        
        debtors, credit = manage_debtors("bakery")
        diff = (cash + pos + credit) - total_exp
        
        if st.button("💾 SAVE BAKERY", type="primary"):
            db.save_bakery_entry({"date": db.datetime.now().strftime("%Y-%m-%d %H:%M"), "staff": staff, "sold_qty": total_sold, "damaged_qty": sum(i['dm'] for i in inputs.values()), "expected": total_exp, "actual": cash+pos+credit, "diff": diff, "note": "", "credit": credit, "debtors_list": debtors})
            if diff < -50: st.warning(f"Shortage: ₦{abs(diff):,.2f}")
            else: st.success("Saved!")
        with st.expander("History"): st.dataframe(db.get_bakery_history(), use_container_width=True)

    # === MODULE E: FARM ===
    elif selection == "Farm Dept":
        st.markdown("## 🚜 Farm Operations")
        c1, c2 = st.columns([3, 1])
        with c1: staff = st.text_input("Staff Name", value=st.session_state.user.upper(), key="farm_st")
        with c2: 
            if st.button("🔄 Next Customer"): clear_farm(); st.rerun()
        
        c1, c2 = st.columns([2, 1])
        with c1: cust = st.text_input("Customer", key="farm_cust")
        with c2: ph = st.text_input("Phone", key="farm_phone")
        
        if 'farm_cart' not in st.session_state: st.session_state.farm_cart = [{"Product": "Eggs", "Qty": 1, "Unit Price": 0}]
        cart = st.data_editor(st.session_state.farm_cart, num_rows="dynamic", use_container_width=True, key="farm_ed")
        
        total = sum([r.get("Qty",0)*r.get("Unit Price",0) for r in cart])
        st.markdown(f"<h3 style='text-align: right; color: #0d47a1;'>TOTAL: ₦{total:,.2f}</h3>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1: paid = st.number_input("Amount Paid", key="farm_paid")
        with c2: mode = st.selectbox("Mode", ["Cash", "POS", "Transfer", "Credit"], key="farm_mode")
        with c3: bal = total - paid; st.metric("Balance", f"₦{bal:,.2f}")
        note = st.text_input("Note", key="farm_note")
        
        if st.button("💾 SAVE SALE", type="primary"):
            items = ", ".join([f"{r['Qty']}x {r['Product']}" for r in cart if r.get("Product")])
            db.save_farm_entry({"date": db.datetime.now().strftime("%Y-%m-%d %H:%M"), "staff": staff, "customer": cust, "items": items, "total": total, "paid": paid, "mode": mode, "balance": bal, "note": note})
            st.success("Saved!")
        with st.expander("History"): st.dataframe(db.get_farm_history(), use_container_width=True)

    # === MODULE F: DEBT RECOVERY ===
    elif selection == "Debt Recovery":
        st.markdown("## 💰 Debt Recovery")
        debts = db.get_unpaid_debts()
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Outstanding Debts")
            if not debts.empty: st.dataframe(debts, use_container_width=True)
            else: st.success("No debts!")
        with c2:
            st.subheader("Record Repayment")
            with st.form("repay_form", clear_on_submit=True):
                r_id = st.number_input("Debt ID", min_value=0, step=1)
                r_amt = st.number_input("Amount (₦)", min_value=0.0)
                if st.form_submit_button("PROCESS PAYMENT", type="primary"):
                    if r_id > 0 and r_amt > 0:
                        success, msg = db.process_debt_repayment(r_id, r_amt, st.session_state.user)
                        if success: st.success(msg); st.rerun()
                        else: st.error(msg)
                    else: st.warning("Enter details.")

    # === MODULE G: SETTINGS ===
    elif selection == "⚙️ Price Settings":
        st.markdown("## ⚙️ Product Price Settings")
        current_prices = db.get_prices()
        with st.form("price_update_form"):
            cols = st.columns(3)
            updated_prices = {}
            i = 0
            for item, price in current_prices.items():
                with cols[i % 3]: 
                    new_val = st.number_input(f"{item}", value=float(price), step=50.0)
                    updated_prices[item] = new_val
                i += 1
            if st.form_submit_button("UPDATE PRICES", type="primary"):
                for item, new_price in updated_prices.items():
                    if new_price != current_prices[item]: db.update_price(item, new_price)
                st.success("✅ Prices Updated!")
                st.rerun()

    # === MODULE H: DATABASE ADMIN (NEW!) ===
    elif selection == "🔧 Database Admin":
        st.markdown("## 🔧 Database Administrator")
        st.warning("⚠️ Be careful! Changes here are permanent.")
        
        # 1. Select Table
        table = st.selectbox("Select Table to Edit", ["daily_sales", "pos_records", "fuel_records", "bakery_records", "farm_records", "debts"])
        
        # 2. Load Data
        conn = db.sqlite3.connect(db.DB_NAME)
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        conn.close()
        
        # 3. Edit Data
        st.markdown(f"### Editing: {table}")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"editor_{table}")
        
        # 4. Save Changes
        if st.button("💾 SAVE CHANGES TO DATABASE", type="primary"):
            conn = db.sqlite3.connect(db.DB_NAME)
            c = conn.cursor()
            
            # Dangerous but effective: Wipe table and replace with edited data
            try:
                c.execute(f"DELETE FROM {table}") # Clear old data
                edited_df.to_sql(table, conn, if_exists='append', index=False) # Write new data
                conn.commit()
                st.success("Database Updated Successfully!")
            except Exception as e:
                st.error(f"Error updating database: {e}")
            conn.close()