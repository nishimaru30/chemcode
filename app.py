import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from supabase import create_client
import json

# Page configuration
st.set_page_config(
    page_title="ChemCode - Chemistry Coding Challenges", 
    page_icon="⚗️",
    layout="wide"
)

# Initialize Supabase for user storage (instead of YAML file)
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

db = init_supabase()

# Load users from database
def load_user_credentials():
    """Load all users from Supabase"""
    response = db.table('users').select('*').execute()
    
    credentials = {'usernames': {}}
    for user in response.data:
        credentials['usernames'][user['username']] = {
            'email': user['email'],
            'name': user['name'],
            'password': user['password']
        }
    return credentials

# Save new user to database
def save_new_user(username, name, email, hashed_password):
    """Save new registered user to Supabase"""
    db.table('users').insert({
        'username': username,
        'name': name,
        'email': email,
        'password': hashed_password
    }).execute()

# Initialize authenticator
def setup_authentication():
    credentials = load_user_credentials()
    
    config = {
        'credentials': credentials,
        'cookie': {
            'name': 'chemcode_cookie',
            'key': 'random_signature_key_12345',  # Change this!
            'expiry_days': 30
        }
    }
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    return authenticator

def main():
    st.title("⚗️ ChemCode - Chemistry Coding Challenges")
    
    authenticator = setup_authentication()
    
    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        # Login widget
        try:
            authenticator.login()
        except Exception as e:
            st.error(e)
    
    with tab2:
        # Registration widget - ANYONE can register!
        try:
            email_of_registered_user, username_of_registered_user, name_of_registered_user = \
                authenticator.register_user(
                    location='main',
                    preauthorization=False  # Set to False to allow ANYONE to register
                )
            
            if email_of_registered_user:
                st.success('✅ Account created successfully! Please login.')
                
                # Save to database
                hashed_password = stauth.Hasher([username_of_registered_user]).generate()[0]
                save_new_user(
                    username_of_registered_user,
                    name_of_registered_user,
                    email_of_registered_user,
                    hashed_password
                )
                
        except Exception as e:
            st.error(e)
    
    # Check if user is logged in
    if st.session_state.get('authentication_status'):
        # User is logged in - show the app!
        username = st.session_state['username']
        name = st.session_state['name']
        
        # Logout button in sidebar
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.write(f"👋 Welcome **{name}**!")
        
        # YOUR EXISTING CHEMCODE APP GOES HERE
        # All the problem selection, code editor, etc.
        st.markdown("*Practice chemistry problems with Python - 15 minutes a day!*")
        
        problems = load_problems()
        if not problems:
            return
        
        st.sidebar.title("📚 Problems")
        selected_problem = st.sidebar.selectbox("Select Problem", list(problems.keys()))
        
        # ... rest of your existing code ...
        
        # Track progress per user
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Your Progress")
        
        # Query submissions for THIS user only
        user_submissions = db.table('submissions').select('*').eq('username', username).execute()
        
        if user_submissions.data:
            total_attempts = len(user_submissions.data)
            st.sidebar.write(f"📝 Your attempts: {total_attempts}")
        else:
            st.sidebar.write("No submissions yet. Start coding!")
        
    elif st.session_state.get('authentication_status') is False:
        st.error('❌ Username/password is incorrect')
    elif st.session_state.get('authentication_status') is None:
        st.info('👈 Please login or sign up to start coding!')

if __name__ == "__main__":
    main()
