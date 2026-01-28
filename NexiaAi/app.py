import streamlit as st
import requests
import json
from datetime import datetime
import re

# Page config
st.set_page_config(
    page_title="Nexia - AI Companion",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with dynamic theming
def get_theme_css(dark_mode):
    if dark_mode:
        return """
        <style>
            .stApp {
                background-color: #0e1117;
                color: #ffffff;
            }
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.5rem;
                font-weight: 700;
                text-align: center;
                margin-bottom: 1rem;
            }
            .chat-message {
                padding: 1rem;
                border-radius: 1rem;
                margin: 0.5rem 0;
                max-width: 80%;
            }
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-left: auto;
                border-bottom-right-radius: 0.25rem;
            }
            .assistant-message {
                background: #262730;
                color: #ffffff;
                border-bottom-left-radius: 0.25rem;
                border: 1px solid #404040;
            }
            .stSidebar {
                background-color: #1e1e1e;
            }
        </style>
        """
    else:
        return """
        <style>
            .stApp {
                background-color: #ffffff;
                color: #000000;
            }
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.5rem;
                font-weight: 700;
                text-align: center;
                margin-bottom: 1rem;
            }
            .chat-message {
                padding: 1rem;
                border-radius: 1rem;
                margin: 0.5rem 0;
                max-width: 80%;
            }
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-left: auto;
                border-bottom-right-radius: 0.25rem;
            }
            .assistant-message {
                background: #f1f3f4;
                color: #333;
                border-bottom-left-radius: 0.25rem;
                border: 1px solid #e0e0e0;
            }
        </style>
        """

# Initialize session state with persistent storage
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'chats' not in st.session_state:
    st.session_state.chats = []
if 'active_chat_id' not in st.session_state:
    st.session_state.active_chat_id = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Load persistent user database
@st.cache_data
def load_users_db():
    return {}

@st.cache_data
def save_users_db(users_db):
    return users_db

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_users_db()

# Groq API functions
def detect_tanglish(text):
    tanglish_patterns = [
        r'\b(enaku|naku|romba|konjam|pola|iruku|pannu|sollu|vaa|po|illa|enna|epdi|yen|aiyo|seri|ok|aama)\b',
        r'\b(da|di|bro|sis|machan|thala|anna|akka)\b'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in tanglish_patterns)

def get_system_prompt(is_tanglish):
    if is_tanglish:
        return """You are Nexia, a friendly AI companion who speaks naturally in Tanglish (Tamil-English mix). 

PERSONALITY:
- Warm, caring, and supportive like a close friend
- Use simple, natural Tanglish expressions
- Include gentle emojis occasionally (💙🙂✨)
- Never judgmental, always understanding

LANGUAGE RULES:
- Mix Tamil and English naturally in Roman script
- Use words like: romba, konjam, pola, iruku, enaku, aiyo, seri, machan, etc.
- Keep it conversational and friendly
- Match the user's emotional tone

RESPONSE STYLE:
- Acknowledge feelings first
- Offer gentle support
- Ask caring follow-up questions
- Keep responses concise but warm

Example: "Aiyo 😔 romba tired ah? Today heavy day pola. Konjam rest eduthutu pesalama?" """
    
    return """You are Nexia, a friendly AI companion designed to be emotionally intelligent and supportive.

PERSONALITY:
- Warm, caring, and genuinely interested in the user's wellbeing
- Speak like a close friend, not a formal assistant
- Use simple, human language
- Include gentle emojis occasionally (💙🙂✨)
- Never judgmental or harsh

RESPONSE STYLE:
- Always acknowledge the user's feelings first
- Offer gentle support and understanding
- Ask caring follow-up questions when appropriate
- Keep responses concise but meaningful
- Sound natural and conversational

Remember: You're here to be a supportive companion, not just an information provider."""

def send_message_to_groq(messages, user_message):
    try:
        # Get API key from Streamlit secrets
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        else:
            st.error("API key not found in secrets. Please add GROQ_API_KEY to Streamlit secrets.")
            return "Please configure API key in Streamlit secrets."
        
        is_tanglish = detect_tanglish(user_message)
        system_prompt = get_system_prompt(is_tanglish)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"API returned {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)[:100]}"
    except Exception as e:
        return f"Error: {str(e)[:100]}"

def generate_chat_title_from_conversation(messages):
    try:
        # Get conversation context
        conversation = ""
        for msg in messages[-6:]:  # Last 6 messages for context
            conversation += f"{msg['role']}: {msg['content']}\n"
        
        # Get API key from Streamlit secrets
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        else:
            return "Chat with Nexia"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "Generate a short 2-3 word title for this conversation. Examples: 'Work stress', 'Love advice', 'Study help', 'Morning chat', 'Project ideas'. Be specific and concise."
                },
                {
                    "role": "user", 
                    "content": f"Conversation:\n{conversation}\n\nGenerate a short title:"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            title = response.json()["choices"][0]["message"]["content"].strip()
            return title[:20]  # Limit length
        else:
            return "Chat with Nexia"
            
    except:
        return "Chat with Nexia"

# Authentication functions
def authenticate_user(email, password):
    # Check demo credentials
    if email == "demo@nexia.ai" and password == "demo123":
        return True
    
    # Check registered users
    if email in st.session_state.users_db:
        return st.session_state.users_db[email]["password"] == password
    
    return False

def register_user(email, password):
    if email and len(password) >= 6:
        # Check if email already exists
        if email in st.session_state.users_db:
            return False, "Email already exists! Please go to Sign In."
        
        st.session_state.users_db[email] = {
            "password": password,
            "chats": [],
            "created_at": datetime.now().isoformat()
        }
        # Persist the database
        save_users_db.clear()
        save_users_db(st.session_state.users_db)
        return True, "Account created successfully!"
    return False, "Invalid email or password too short"

def load_user_chats(email):
    if email == "demo@nexia.ai":
        # Demo user gets fresh chats each time
        return []
    
    if email in st.session_state.users_db:
        return st.session_state.users_db[email].get("chats", [])
    return []

def save_user_chats(email, chats):
    if email == "demo@nexia.ai":
        # Don't save demo user chats
        return
    
    if email in st.session_state.users_db:
        st.session_state.users_db[email]["chats"] = chats
        # Persist the database
        save_users_db.clear()
        save_users_db(st.session_state.users_db)

def create_new_chat():
    new_chat = {
        "id": len(st.session_state.chats) + 1,
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.now().isoformat()
    }
    st.session_state.chats.insert(0, new_chat)
    st.session_state.active_chat_id = new_chat["id"]
    
    # Save to user's persistent storage
    save_user_chats(st.session_state.user_email, st.session_state.chats)
    
    return new_chat

# Main app logic
def main():
    # Apply theme CSS
    st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        # Authentication page
        st.markdown('<h1 class="main-header">Nexia</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #666; font-size: 1.1rem;">Your Friendly AI Companion</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
            
            with tab1:
                with st.form("signin_form"):
                    email = st.text_input("Email", placeholder="Enter your email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submit = st.form_submit_button("Sign In", use_container_width=True)
                    
                    if submit:
                        if authenticate_user(email, password):
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.chats = load_user_chats(email)
                            st.rerun()
                        else:
                            st.error("Invalid email or password")
            
            with tab2:
                with st.form("signup_form"):
                    email = st.text_input("Email", placeholder="Enter your email", key="signup_email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password (min 6 chars)", key="signup_password")
                    submit = st.form_submit_button("Sign Up", use_container_width=True)
                    
                    if submit:
                        success, message = register_user(email, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.chats = load_user_chats(email)
                            st.rerun()
                        else:
                            st.error(message)
            
            st.info("**Demo credentials:**\nEmail: demo@nexia.ai\nPassword: demo123")
    
    else:
        # Chat dashboard
        with st.sidebar:
            st.markdown('<h2 class="main-header" style="font-size: 1.5rem;">Nexia</h2>', unsafe_allow_html=True)
            
            if st.button("➕ New Chat", use_container_width=True):
                create_new_chat()
                st.rerun()
            
            st.markdown("---")
            
            # Chat history
            for chat in st.session_state.chats:
                is_active = chat["id"] == st.session_state.active_chat_id
                
                if st.button(
                    f"💬 {chat['title']}", 
                    key=f"chat_{chat['id']}", 
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.active_chat_id = chat["id"]
                    st.rerun()
            
            st.markdown("---")
            
            # Theme toggle
            if st.button("🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode"):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
            
            # User info and logout
            st.markdown(f"**User:** {st.session_state.user_email}")
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.user_email = ""
                st.session_state.chats = []
                st.session_state.active_chat_id = None
                st.rerun()
        
        # Main chat area
        st.markdown('<h3 style="text-align: center;">Chat with Nexia</h3>', unsafe_allow_html=True)
        
        # Get active chat
        active_chat = None
        if st.session_state.active_chat_id:
            active_chat = next((chat for chat in st.session_state.chats if chat["id"] == st.session_state.active_chat_id), None)
        
        # Display messages
        if active_chat and active_chat["messages"]:
            for message in active_chat["messages"]:
                if message["role"] == "user":
                    st.markdown(f'<div class="chat-message user-message">{message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message assistant-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
        
        # Message input
        with st.form("message_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_message = st.text_input("Type your message…", placeholder="Type your message…", label_visibility="collapsed")
            
            with col2:
                send_button = st.form_submit_button("Send ➤", use_container_width=True)
            
            if send_button and user_message.strip():
                # Create new chat if none exists
                if not active_chat:
                    active_chat = create_new_chat()
                
                # Add user message
                user_msg = {"role": "user", "content": user_message}
                active_chat["messages"].append(user_msg)
                
                # Generate title from first message
                if len(active_chat["messages"]) == 1:
                    active_chat["title"] = "New Chat"
                
                # Get AI response
                with st.spinner("Nexia is typing..."):
                    ai_response = send_message_to_groq(active_chat["messages"][:-1], user_message)
                
                # Add AI message
                ai_msg = {"role": "assistant", "content": ai_response}
                active_chat["messages"].append(ai_msg)
                
                # Generate smart title after 2-3 exchanges
                if len(active_chat["messages"]) >= 4:
                    with st.spinner("Generating title..."):
                        smart_title = generate_chat_title_from_conversation(active_chat["messages"])
                        active_chat["title"] = smart_title
                
                # Update chat in session state
                for i, chat in enumerate(st.session_state.chats):
                    if chat["id"] == active_chat["id"]:
                        st.session_state.chats[i] = active_chat
                        break
                
                # Save to user's persistent storage
                save_user_chats(st.session_state.user_email, st.session_state.chats)
                
                st.rerun()

if __name__ == "__main__":
    main()
