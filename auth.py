import streamlit as st

# --- USER DATABASE ---
# Format: "email": ("password", "Role", "Department")
# I have updated passwords to be stronger to stop the Chrome warning.
users = {
    "admin@okeb.com": ("OkebAdmin@2026", "ADMIN", "All"),     # Was admin123
    "manager@okeb.com": ("Manager#Top24", "MANAGER", "All"),  # Was manager123
    "fuel@okeb.com": ("FuelStation$1", "STAFF", "Fuel"),
    "bakery@okeb.com": ("FreshBread!99", "STAFF", "Bakery"),
    "pos@okeb.com": ("MoneyPoint*7", "STAFF", "POS"),
    "farm@okeb.com": ("FarmHouse&5", "STAFF", "Farm")
}

def login():
    # --- CUSTOM CSS FOR LOGIN PAGE ---
    st.markdown("""
        <style>
        .stApp {
            background-color: #f1f5f9;
        }
        .login-container {
            max_width: 400px;
            margin: 80px auto;
            padding: 40px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            text-align: center;
        }
        input {
            border-radius: 8px !important;
            padding: 12px !important;
            border: 1px solid #e2e8f0 !important;
        }
        /* Login Button Styling */
        .stButton button {
            width: 100%;
            background-color: #0f172a !important; 
            color: white !important;
            border-radius: 8px !important;
            height: 50px;
            font-size: 16px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.1);
        }
        .stButton button:hover {
            background-color: #1e293b !important;
            box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.1);
        }
        h1 { font-family: 'Inter', sans-serif; color: #1e293b; font-size: 28px; margin-bottom: 5px; }
        p { color: #64748b; font-size: 14px; margin-bottom: 30px; }
        </style>
    """, unsafe_allow_html=True)

    # --- CENTERED LOGIN CARD ---
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.markdown("""
            <div style="text-align: center; margin-top: 50px; margin-bottom: 20px;">
                <img src="https://cdn-icons-png.flaticon.com/512/900/900782.png" width="70">
                <h1 style="margin-top: 15px;">OKEB NIGERIA</h1>
                <p>Enterprise Management Portal</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="name@okeb.com").lower().strip()
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            submitted = st.form_submit_button("Secure Login")
            
            if submitted:
                if email in users:
                    stored_pass, role, dept = users[email]
                    if password == stored_pass:
                        st.session_state.logged_in = True
                        st.session_state.user = email.split('@')[0]
                        st.session_state.role = role
                        st.session_state.dept = dept
                        st.success("Verifying credentials... Redirecting.")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect Password. Please try again.")
                else:
                    st.error("❌ Email not found in system.")

        # --- FORGOT PASSWORD SECTION ---
        with st.expander("Forgot Password?", expanded=False):
            st.info("🔐 **Recovery Instructions:**")
            st.write("Since this is a secure internal system, please contact the **Manager** or **IT Administrator** to reset your password.")
            st.caption("Support: admin@okeb.com")

    # Footer
    st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 12px; margin-top: 50px;'>© 2026 Okeb Nigeria Limited | System v2.0</div>", unsafe_allow_html=True)