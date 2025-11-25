"""
Authentication module using streamlit-authenticator
Provides login, signup, and session management
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

def load_config():
    """Load authentication configuration"""
    config_path = 'config.yaml'
    if not os.path.exists(config_path):
        # Create default config with demo users
        # Pre-hash passwords for demo accounts
        demo_passwords = stauth.Hasher(['demo123', 'admin123']).generate()
        
        default_config = {
            'credentials': {
                'usernames': {
                    'demo_user': {
                        'email': 'demo@openanalyst.com',
                        'name': 'Demo User',
                        'password': demo_passwords[0]
                    },
                    'admin': {
                        'email': 'admin@openanalyst.com',
                        'name': 'Administrator',
                        'password': demo_passwords[1]
                    }
                }
            },
            'cookie': {
                'expiry_days': 30,
                'key': 'openanalyst_auth_key_2024',
                'name': 'openanalyst_auth_cookie'
            },
            'preauthorized': {
                'emails': []
            }
        }
        with open(config_path, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
    
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Ensure demo users exist (upgrade path for existing configs)
    if 'demo_user' not in config['credentials']['usernames']:
        demo_passwords = stauth.Hasher(['demo123', 'admin123']).generate()
        config['credentials']['usernames']['demo_user'] = {
            'email': 'demo@openanalyst.com',
            'name': 'Demo User',
            'password': demo_passwords[0]
        }
        config['credentials']['usernames']['admin'] = {
            'email': 'admin@openanalyst.com',
            'name': 'Administrator',
            'password': demo_passwords[1]
        }
        save_config(config)
    
    return config

def save_config(config):
    """Save authentication configuration"""
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

def initialize_authenticator():
    """Initialize the authenticator"""
    config = load_config()
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    return authenticator, config

def render_login():
    """Render login form and handle authentication"""
    
    authenticator, config = initialize_authenticator()
    
    # Create tabs for login and signup
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        # Try Demo button at the top
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 Try Demo", use_container_width=True, type="primary"):
                # Auto-login as demo user
                st.session_state['authenticated'] = True
                st.session_state['username'] = 'demo_user'
                st.session_state['name'] = 'Demo User'
                st.success("✅ Logged in as Demo User!")
                st.rerun()
        
        st.markdown("**─── or login manually ───**")
        
        try:
            # Updated API for streamlit-authenticator 0.3.1+
            name, authentication_status, username = authenticator.login(
                location='main',
                fields={'Form name': 'Login', 'Username': 'Username', 'Password': 'Password', 'Login': 'Login'}
            )
            
            if authentication_status:
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.session_state['name'] = name
                st.rerun()
            elif authentication_status == False:
                st.error('❌ Username/password is incorrect')
            elif authentication_status == None:
                st.info('👋 Please enter your username and password')
        except Exception as e:
            st.error(f"⚠️ Authentication system error: {str(e)}")
            st.info("Using fallback authentication. Please contact administrator.")
    
    with tab2:
        render_signup(authenticator, config)
    
    # Demo credentials info (always visible for reference)
    st.markdown("---")
    with st.expander("📝 Demo Credentials (for manual login)"):
        st.info("""
        **Demo Account:**
        - Username: `demo_user`
        - Password: `demo123`
        
        **Admin Account:**
        - Username: `admin`
        - Password: `admin123`
        
        💡 **Tip:** Click "🚀 Try Demo" button above for instant access!
        """)

def render_signup(authenticator, config):
    """Render signup form"""
    st.subheader("Create New Account")
    
    with st.form("signup_form"):
        new_email = st.text_input("Email")
        new_username = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_password = st.text_input("Password", type="password")
        new_password_confirm = st.text_input("Confirm Password", type="password")
        
        submit = st.form_submit_button("Create Account")
        
        if submit:
            # Validation
            import re
            if not all([new_email, new_username, new_name, new_password]):
                st.error("❌ All fields are required")
            elif new_password != new_password_confirm:
                st.error("❌ Passwords do not match")
            elif new_username in config['credentials']['usernames']:
                st.error("❌ Username already exists")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            elif not re.match(r'^[a-zA-Z0-9_.-]+$', new_username):
                st.error("❌ Username can only contain letters, numbers, underscores, dots, and hyphens")
            elif ' ' in new_username:
                st.error("❌ Username cannot contain spaces")
            else:
                try:
                    # Hash password
                    hashed_password = stauth.Hasher([new_password]).generate()[0]
                    
                    # Add new user
                    config['credentials']['usernames'][new_username] = {
                        'email': new_email,
                        'name': new_name,
                        'password': hashed_password
                    }
                    
                    # Save config
                    save_config(config)
                    
                    st.success("✅ Account created successfully! Please login.")
                except Exception as e:
                    st.error(f"❌ Error creating account: {e}")

def render_logout(authenticator):
    """Render logout button in sidebar"""
    with st.sidebar:
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"👤 {st.session_state.get('name', 'User')}")
        with col2:
            authenticator.logout('Logout', 'main')

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    return st.session_state['authenticated']
