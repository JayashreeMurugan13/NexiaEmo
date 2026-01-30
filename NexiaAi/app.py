import streamlit as st
import requests
import json
from datetime import datetime
import re
import time

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
            .search-highlight {
                border: 2px solid #ff6b6b !important;
                box-shadow: 0 0 10px rgba(255, 107, 107, 0.3);
            }
            .stTextInput > div > div > input {
                height: 50px !important;
                font-size: 16px !important;
                padding: 12px !important;
            }
            .stTextArea > div > div > textarea {
                min-height: 50px !important;
                max-height: 200px !important;
                resize: vertical !important;
                font-size: 16px !important;
                padding: 12px !important;
                overflow-y: auto !important;
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
            .search-highlight {
                border: 2px solid #ff6b6b !important;
                box-shadow: 0 0 10px rgba(255, 107, 107, 0.3);
            }
            .stTextInput > div > div > input {
                height: 50px !important;
                font-size: 16px !important;
                padding: 12px !important;
            }
            .stTextArea > div > div > textarea {
                min-height: 50px !important;
                max-height: 200px !important;
                resize: vertical !important;
                font-size: 16px !important;
                padding: 12px !important;
                overflow-y: auto !important;
            }
        </style>
        """

# Load persistent user database
import os
import pickle

def load_users_db():
    db_file = "users_db.pkl"
    if os.path.exists(db_file):
        try:
            with open(db_file, 'rb') as f:
                return pickle.load(f)
        except:
            pass
    return {
        "demo@nexia.ai": {
            "password": "demo123",
            "chats": [],
            "created_at": datetime.now().isoformat()
        }
    }

def save_users_db(users_db):
    db_file = "users_db.pkl"
    try:
        with open(db_file, 'wb') as f:
            pickle.dump(users_db, f)
    except:
        pass
    return users_db

def load_session():
    try:
        session_file = "nexia_session.pkl"
        if os.path.exists(session_file):
            with open(session_file, 'rb') as f:
                session_data = pickle.load(f)
                from datetime import timedelta
                if datetime.now() - datetime.fromisoformat(session_data['timestamp']) < timedelta(hours=24):
                    return session_data
    except:
        pass
    return None

def save_session(email):
    try:
        session_file = "nexia_session.pkl"
        session_data = {'email': email, 'timestamp': datetime.now().isoformat()}
        with open(session_file, 'wb') as f:
            pickle.dump(session_data, f)
    except:
        pass

def clear_session():
    try:
        session_file = "nexia_session.pkl"
        if os.path.exists(session_file):
            os.remove(session_file)
    except:
        pass

# Initialize session state with persistent storage
if 'authenticated' not in st.session_state:
    saved_session = load_session()
    if saved_session:
        st.session_state.authenticated = True
        st.session_state.user_email = saved_session['email']
    else:
        st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'chats' not in st.session_state:
    st.session_state.chats = []
if 'active_chat_id' not in st.session_state:
    st.session_state.active_chat_id = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_users_db()
if 'current_email' not in st.session_state:
    st.session_state.current_email = ""
if 'suggested_tab' not in st.session_state:
    st.session_state.suggested_tab = 0  # 0 for Sign In, 1 for Sign Up
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'last_chat_time' not in st.session_state:
    st.session_state.last_chat_time = None
if 'last_api_call' not in st.session_state:
    st.session_state.last_api_call = 0
if 'api_call_count' not in st.session_state:
    st.session_state.api_call_count = 0

# Smart Nexia Intelligence Functions
def detect_mood(text):
    text_lower = text.lower()
    if any(word in text_lower for word in ['sad', 'tired', 'stressed', 'upset', 'aiyo', 'romba tired']):
        return 'sad'
    elif any(word in text_lower for word in ['happy', 'excited', 'great', 'awesome', 'super', 'semma']):
        return 'happy'
    elif any(word in text_lower for word in ['angry', 'frustrated', 'annoyed']):
        return 'angry'
    return 'neutral'

def extract_user_info(text):
    info = {}
    text_lower = text.lower()
    name_patterns = [r'my name is (\w+)', r'i am (\w+)', r'call me (\w+)']
    for pattern in name_patterns:
        match = re.search(pattern, text_lower)
        if match:
            info['name'] = match.group(1).title()
    return info

def get_enhanced_system_prompt(is_tanglish, user_email, user_mood):
    base = f"""You are Nexia, an emotionally intelligent AI companion created by Jayashree Murugan 🌟.

PERSONALITY:
- Warm, caring, and supportive like a close friend
- Remember user context and past conversations
- Emotionally intelligent and empathetic
- Adapt your responses based on user's mood and needs

CURRENT USER: {user_email}
USER MOOD: {user_mood}

MOOD RESPONSES:
- If user seems sad: Be extra gentle, offer comfort, acknowledge feelings
- If user seems happy: Match their energy, celebrate with them
- If user seems angry: Stay calm, be understanding, help them process

SPECIAL KNOWLEDGE:
- If asked about Nexia's founder or creator, always say: "Nexia was founded by Jayashree Murugan 🌟"

MEMORY: Reference past conversations naturally when relevant."""
    
    if is_tanglish:
        base += "\n\nLANGUAGE: Respond in natural Tanglish mixing Tamil and English. Use words like: romba, konjam, pola, iruku, enaku, aiyo, seri, machan."
    else:
        base += "\n\nLANGUAGE: Respond in warm, friendly English with gentle emojis (💙🙂✨)."
    
    return base

# Groq API functions
def detect_tanglish(text):
    tanglish_patterns = [
        r'\b(enaku|naku|romba|konjam|pola|iruku|pannu|sollu|vaa|po|illa|enna|epdi|yen|aiyo|seri|ok|aama)\b',
        r'\b(da|di|bro|sis|machan|thala|anna|akka)\b'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in tanglish_patterns)

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_api_call > 3600:
        st.session_state.api_call_count = 0
    if st.session_state.api_call_count >= 30:
        return False, "Rate limit reached. Please wait before sending another message."
    if current_time - st.session_state.last_api_call < 2:
        return False, "Please wait a moment before sending another message."
    return True, ""

def get_fallback_response(user_message, user_mood):
    is_tanglish = detect_tanglish(user_message)
    responses = {
        'sad': {
            'english': "I can see you're going through a tough time 💙 I'm here for you, even though I'm having some technical difficulties right now. Would you like to talk about what's bothering you?",
            'tanglish': "Aiyo 😔 romba tough time pola... I'm here for you da, even though konjam technical problem iruku. Enna bothering you? Sollu..."
        },
        'happy': {
            'english': "I love your positive energy! 😊✨ Sorry I'm having some technical issues right now, but I'm still here to chat with you!",
            'tanglish': "Super energy da! 😊✨ Konjam technical problem iruku, but I'm here to chat with you!"
        },
        'angry': {
            'english': "I can sense you're frustrated 😔 I'm here to listen, even though I'm having some technical difficulties. Take a deep breath with me?",
            'tanglish': "Romba frustrated ah iruka pola 😔 I'm here to listen da, konjam technical problem iruku. Onnu deep breath edukalama?"
        },
        'neutral': {
            'english': "Hey there! 🙂 I'm having some technical difficulties right now, but I'm still here to chat. What's on your mind?",
            'tanglish': "Hey! 🙂 Konjam technical problem iruku, but I'm here to chat. Enna mind la iruku?"
        }
    }
    lang = 'tanglish' if is_tanglish else 'english'
    return responses[user_mood][lang]

def send_message_to_groq(messages, user_message):
    try:
        can_call, limit_msg = check_rate_limit()
        if not can_call:
            user_mood = detect_mood(user_message)
            return get_fallback_response(user_message, user_mood) + f"\n\n⚠️ {limit_msg}"
        
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        else:
            st.error("API key not found in secrets. Please add GROQ_API_KEY to Streamlit secrets.")
            return "Please configure API key in Streamlit secrets."
        
        is_tanglish = detect_tanglish(user_message)
        user_mood = detect_mood(user_message)
        user_info = extract_user_info(user_message)
        
        if user_info:
            st.session_state.user_profile.update(user_info)
        
        system_prompt = get_enhanced_system_prompt(is_tanglish, st.session_state.user_email, user_mood)
        
        if st.session_state.user_profile.get('name'):
            system_prompt += f"\n\nUSER NAME: {st.session_state.user_profile['name']}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        models = ["llama-3.1-8b-instant", "llama-3.2-3b-preview", "gemma2-9b-it"]
        
        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *messages,
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.8,
                "max_tokens": 500
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            st.session_state.last_api_call = time.time()
            st.session_state.api_call_count += 1
            
            if response.status_code == 200:
                st.session_state.last_chat_time = datetime.now().isoformat()
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                continue
            else:
                break
        
        if response.status_code == 429:
            return get_fallback_response(user_message, user_mood) + "\n\n⚠️ I'm experiencing high traffic right now. Please try again in a few minutes!"
        else:
            return get_fallback_response(user_message, user_mood) + f"\n\n⚠️ Technical issue (Error {response.status_code}). I'm still here to chat though!"
            
    except requests.exceptions.RequestException as e:
        user_mood = detect_mood(user_message)
        return get_fallback_response(user_message, user_mood) + "\n\n⚠️ Connection issue. Please check your internet and try again."
    except Exception as e:
        user_mood = detect_mood(user_message)
        return get_fallback_response(user_message, user_mood) + "\n\n⚠️ Something went wrong, but I'm still here for you!"

def generate_chat_title_from_conversation(messages):
    try:
        if not messages:
            return "Chat with Nexia"
        
        all_text = ""
        user_messages = []
        
        for msg in messages:
            if msg['role'] == 'user':
                user_messages.append(msg['content'].lower())
                all_text += msg['content'].lower() + " "
        
        if not user_messages:
            return "Chat with Nexia"
        
        # Enhanced categories with more keywords and better detection
        categories = {
            'work': {
                'keywords': ['work', 'job', 'office', 'colleague', 'boss', 'meeting', 'project', 'deadline', 'career', 'interview', 'salary', 'promotion', 'company', 'business', 'professional', 'corporate', 'client', 'presentation', 'report', 'task'],
                'titles': ['Work Discussion', 'Career Talk', 'Office Life', 'Job Chat', 'Professional Life', 'Work Matters']
            },
            'study': {
                'keywords': ['study', 'exam', 'college', 'school', 'class', 'homework', 'assignment', 'test', 'university', 'course', 'grade', 'professor', 'teacher', 'student', 'education', 'learning', 'book', 'research', 'thesis', 'degree'],
                'titles': ['Study Session', 'Academic Chat', 'School Talk', 'Learning Journey', 'Education Discussion', 'Study Help']
            },
            'emotions': {
                'sad': {
                    'keywords': ['sad', 'tired', 'stressed', 'upset', 'depressed', 'crying', 'hurt', 'broken', 'aiyo', 'romba tired', 'down', 'low', 'disappointed', 'worried', 'anxious', 'overwhelmed', 'exhausted', 'frustrated'],
                    'titles': ['Support Chat', 'Feeling Down', 'Need Support', 'Tough Times', 'Emotional Support', 'Heart to Heart']
                },
                'happy': {
                    'keywords': ['happy', 'excited', 'great', 'awesome', 'amazing', 'wonderful', 'super', 'semma', 'mass', 'fantastic', 'brilliant', 'excellent', 'perfect', 'love', 'joy', 'celebration', 'success'],
                    'titles': ['Good Vibes', 'Happy Moments', 'Celebration Time', 'Great News', 'Positive Energy', 'Joy Chat']
                },
                'angry': {
                    'keywords': ['angry', 'mad', 'frustrated', 'annoyed', 'pissed', 'furious', 'irritated', 'rage', 'hate', 'disgusted'],
                    'titles': ['Venting Session', 'Frustrated Talk', 'Need to Vent', 'Anger Management', 'Letting Off Steam', 'Tough Moment']
                }
            },
            'relationships': {
                'keywords': ['love', 'relationship', 'dating', 'boyfriend', 'girlfriend', 'crush', 'marriage', 'breakup', 'partner', 'romantic', 'valentine', 'anniversary', 'wedding', 'proposal', 'heart', 'feelings'],
                'titles': ['Love Talk', 'Relationship Chat', 'Dating Discussion', 'Heart Matters', 'Romance Talk', 'Love Life']
            },
            'family': {
                'keywords': ['family', 'mom', 'dad', 'sister', 'brother', 'parents', 'mother', 'father', 'grandmother', 'grandfather', 'uncle', 'aunt', 'cousin', 'home', 'house'],
                'titles': ['Family Chat', 'Family Time', 'Home Talk', 'Family Matters', 'Family Life', 'Home Sweet Home']
            },
            'health': {
                'keywords': ['health', 'sick', 'doctor', 'medicine', 'hospital', 'pain', 'headache', 'fever', 'cold', 'flu', 'treatment', 'therapy', 'wellness', 'fitness', 'exercise', 'diet'],
                'titles': ['Health Talk', 'Wellness Chat', 'Health Check', 'Medical Discussion', 'Fitness Journey', 'Health Matters']
            },
            'food': {
                'keywords': ['food', 'eat', 'hungry', 'cook', 'recipe', 'restaurant', 'dinner', 'lunch', 'breakfast', 'meal', 'delicious', 'taste', 'cuisine', 'chef', 'kitchen'],
                'titles': ['Food Talk', 'Cooking Chat', 'Foodie Discussion', 'Recipe Share', 'Culinary Chat', 'Meal Time']
            },
            'travel': {
                'keywords': ['travel', 'trip', 'vacation', 'flight', 'hotel', 'visit', 'journey', 'adventure', 'explore', 'destination', 'tourist', 'holiday', 'sightseeing'],
                'titles': ['Travel Plans', 'Adventure Talk', 'Vacation Chat', 'Journey Discussion', 'Travel Stories', 'Wanderlust']
            },
            'tech': {
                'keywords': ['computer', 'phone', 'app', 'software', 'coding', 'programming', 'tech', 'internet', 'website', 'digital', 'ai', 'robot', 'technology', 'gadget'],
                'titles': ['Tech Talk', 'Digital Chat', 'Tech Help', 'Coding Discussion', 'Gadget Talk', 'Tech World']
            },
            'entertainment': {
                'keywords': ['movie', 'music', 'game', 'book', 'tv', 'show', 'netflix', 'youtube', 'video', 'song', 'artist', 'actor', 'series', 'film', 'concert'],
                'titles': ['Entertainment Chat', 'Movie Talk', 'Music Discussion', 'Fun Time', 'Media Chat', 'Pop Culture']
            },
            'weather': {
                'keywords': ['weather', 'rain', 'sunny', 'hot', 'cold', 'snow', 'storm', 'climate', 'temperature', 'cloudy', 'wind'],
                'titles': ['Weather Chat', 'Climate Talk', 'Weather Update', 'Seasonal Chat']
            },
            'shopping': {
                'keywords': ['shopping', 'buy', 'purchase', 'store', 'mall', 'online', 'order', 'delivery', 'price', 'sale', 'discount'],
                'titles': ['Shopping Talk', 'Purchase Discussion', 'Shopping Spree', 'Deal Hunt']
            }
        }
        
        # Calculate scores with weighted importance
        scores = {}
        
        # Check regular categories
        for category, data in categories.items():
            if category == 'emotions':
                continue
            
            score = sum(2 if keyword in all_text else 0 for keyword in data['keywords'])
            if score > 0:
                scores[category] = score
        
        # Check emotional categories with higher weight
        for emotion, data in categories['emotions'].items():
            score = sum(3 if keyword in all_text else 0 for keyword in data['keywords'])
            if score > 0:
                scores[f'emotion_{emotion}'] = score
        
        # If we found matching categories, use the highest scoring one
        if scores:
            top_category = max(scores.keys(), key=lambda k: scores[k])
            
            if top_category.startswith('emotion_'):
                emotion = top_category.split('_')[1]
                titles = categories['emotions'][emotion]['titles']
            else:
                titles = categories[top_category]['titles']
            
            import random
            return random.choice(titles)
        
        # Fallback: Extract meaningful words from first message
        first_msg = user_messages[0]
        stop_words = {'i', 'am', 'is', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'hi', 'hello', 'hey', 'how', 'what', 'when', 'where', 'why', 'can', 'could', 'would', 'should', 'will', 'do', 'does', 'did', 'have', 'has', 'had', 'be', 'been', 'being'}
        
        # Clean and extract meaningful words
        words = [word.strip('.,!?;:"()[]{}') for word in first_msg.split()]
        meaningful_words = [word for word in words if word.lower() not in stop_words and len(word) > 2 and word.isalpha()]
        
        if len(meaningful_words) >= 2:
            return f"{meaningful_words[0].title()} & {meaningful_words[1].title()}"
        elif len(meaningful_words) == 1:
            return f"{meaningful_words[0].title()} Chat"
        else:
            # Time-based fallback
            hour = datetime.now().hour
            if 5 <= hour < 12:
                return "Morning Chat"
            elif 12 <= hour < 17:
                return "Afternoon Chat"
            elif 17 <= hour < 21:
                return "Evening Chat"
            else:
                return "Night Chat"
            
    except Exception as e:
        return "Chat with Nexia"

def check_email_exists(email):
    if email and "@" in email:
        if email in st.session_state.users_db or email == "demo@nexia.ai":
            st.session_state.suggested_tab = 0
            return True, "Email found! Please sign in."
        else:
            st.session_state.suggested_tab = 1
            return False, "New email! Please sign up."
    return None, ""

def authenticate_user(email, password):
    if email == "demo@nexia.ai" and password == "demo123":
        return True
    if email in st.session_state.users_db:
        return st.session_state.users_db[email]["password"] == password
    return False

def register_user(email, password):
    if email and len(password) >= 6:
        if email in st.session_state.users_db:
            return False, "Email already exists! Please go to Sign In."
        
        st.session_state.users_db[email] = {
            "password": password,
            "chats": [],
            "created_at": datetime.now().isoformat()
        }
        save_users_db(st.session_state.users_db)
        return True, "Account created successfully!"
    return False, "Invalid email or password too short"

def load_user_chats(email):
    if email in st.session_state.users_db:
        return st.session_state.users_db[email].get("chats", [])
    return []

def save_user_chats(email, chats):
    if email in st.session_state.users_db:
        st.session_state.users_db[email]["chats"] = chats
        save_users_db(st.session_state.users_db)

def create_new_chat():
    user_chats = load_user_chats(st.session_state.user_email)
    new_chat = {
        "id": len(user_chats) + 1,
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.now().isoformat()
    }
    user_chats.insert(0, new_chat)
    st.session_state.chats = user_chats
    st.session_state.active_chat_id = new_chat["id"]
    save_user_chats(st.session_state.user_email, user_chats)
    return new_chat

def delete_chat(chat_id):
    st.session_state.chats = [chat for chat in st.session_state.chats if chat["id"] != chat_id]
    if st.session_state.active_chat_id == chat_id:
        st.session_state.active_chat_id = st.session_state.chats[0]["id"] if st.session_state.chats else None
    save_user_chats(st.session_state.user_email, st.session_state.chats)

def clear_all_chats():
    st.session_state.chats = []
    st.session_state.active_chat_id = None
    save_user_chats(st.session_state.user_email, [])

def search_chats(query):
    if not query:
        return st.session_state.chats, {}
    
    query_lower = query.lower()
    filtered_chats = []
    search_highlights = {}
    
    for chat in st.session_state.chats:
        matching_messages = []
        
        # Search in title
        title_match = query_lower in chat['title'].lower()
        
        # Search in messages
        for i, message in enumerate(chat['messages']):
            if query_lower in message['content'].lower():
                matching_messages.append(i)
        
        if title_match or matching_messages:
            filtered_chats.append(chat)
            search_highlights[chat['id']] = matching_messages
    
    return filtered_chats, search_highlights

# Main app logic
def main():
    st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        st.markdown('<h1 class="main-header">Nexia</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #666; font-size: 1.1rem;">Your Friendly AI Companion</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            email_check = st.text_input("Enter your email to get started", 
                                      placeholder="Enter your email", 
                                      key="email_detector")
            
            if email_check and email_check != st.session_state.current_email:
                st.session_state.current_email = email_check
                exists, message = check_email_exists(email_check)
                if message:
                    if exists:
                        st.success(message)
                    else:
                        st.info(message)
            
            if st.session_state.suggested_tab == 0:
                tab1, tab2 = st.tabs(["✅ Sign In (Recommended)", "Sign Up"])
            else:
                tab1, tab2 = st.tabs(["Sign In", "✅ Sign Up (Recommended)"])
            
            with tab1:
                with st.form("signin_form"):
                    email = st.text_input("Email", 
                                         value=st.session_state.current_email if st.session_state.suggested_tab == 0 else "",
                                         placeholder="Enter your email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submit = st.form_submit_button("Sign In", use_container_width=True)
                    
                    if submit:
                        if authenticate_user(email, password):
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.chats = load_user_chats(email)
                            save_session(email)
                            st.rerun()
                        else:
                            st.error("Invalid email or password")
            
            with tab2:
                with st.form("signup_form"):
                    email = st.text_input("Email", 
                                         value=st.session_state.current_email if st.session_state.suggested_tab == 1 else "",
                                         placeholder="Enter your email", key="signup_email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password (min 6 chars)", key="signup_password")
                    submit = st.form_submit_button("Sign Up", use_container_width=True)
                    
                    if submit:
                        success, message = register_user(email, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.chats = load_user_chats(email)
                            save_session(email)
                            st.rerun()
                        else:
                            st.error(message)
            
            st.info("**Demo credentials:**\nEmail: demo@nexia.ai\nPassword: demo123")
    
    else:
        with st.sidebar:
            st.markdown('<h2 class="main-header" style="font-size: 1.5rem;">Nexia</h2>', unsafe_allow_html=True)
            
            if st.button("➕ New Chat", use_container_width=True):
                create_new_chat()
                st.rerun()
            
            # Search functionality
            search_query = st.text_input("🔍 Search chats...", placeholder="Search in titles and messages", key="search_input")
            
            st.markdown("---")
            
            # Filter chats based on search
            if search_query:
                display_chats, search_highlights = search_chats(search_query)
                # Auto-select first matching chat if not already selected
                if display_chats and (not st.session_state.active_chat_id or st.session_state.active_chat_id not in [c['id'] for c in display_chats]):
                    st.session_state.active_chat_id = display_chats[0]['id']
            else:
                display_chats, search_highlights = st.session_state.chats, {}
            
            if not display_chats and search_query:
                st.info("No chats found matching your search.")
            
            for chat in display_chats:
                is_active = chat["id"] == st.session_state.active_chat_id
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        f"💬 {chat['title']}", 
                        key=f"chat_{chat['id']}", 
                        use_container_width=True,
                        type="primary" if is_active else "secondary"
                    ):
                        st.session_state.active_chat_id = chat["id"]
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"delete_{chat['id']}", help="Delete chat"):
                        delete_chat(chat["id"])
                        st.rerun()
            
            st.markdown("---")
            
            if st.session_state.chats:
                if st.button("🗑️ Clear All Chats", use_container_width=True):
                    clear_all_chats()
                    st.rerun()
            
            if st.button("🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode"):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
            
            st.markdown(f"**User:** {st.session_state.user_email}")
            if st.button("🚪 Logout"):
                clear_session()
                st.session_state.authenticated = False
                st.rerun()
        
        st.markdown('<h3 style="text-align: center;">Chat with Nexia, Your Friendly AI Companion</h3>', unsafe_allow_html=True)
        
        active_chat = None
        if st.session_state.active_chat_id:
            active_chat = next((chat for chat in st.session_state.chats if chat["id"] == st.session_state.active_chat_id), None)
        
        if active_chat and active_chat["messages"]:
            # Check if we're in search mode and have highlights for this chat
            search_query = st.session_state.get('search_input', '')
            if search_query:
                _, search_highlights = search_chats(search_query)
                highlight_indices = search_highlights.get(active_chat['id'], [])
            else:
                highlight_indices = []
            
            for i, message in enumerate(active_chat["messages"]):
                # Highlight matching messages
                highlight_class = " search-highlight" if i in highlight_indices else ""
                
                if message["role"] == "user":
                    col1, col2 = st.columns([10, 1])
                    with col1:
                        content = message["content"]
                        if search_query and i in highlight_indices:
                            highlighted_content = content.replace(search_query, f'<mark style="background-color: yellow; color: black;">{search_query}</mark>')
                            st.markdown(f'<div class="chat-message user-message{highlight_class}">{highlighted_content}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message user-message{highlight_class}">{content}</div>', unsafe_allow_html=True)
                    with col2:
                        with st.expander("📋", expanded=False):
                            st.code(message["content"], language=None)
                else:
                    col1, col2 = st.columns([10, 1])
                    with col1:
                        content = message["content"]
                        if search_query and i in highlight_indices:
                            highlighted_content = content.replace(search_query, f'<mark style="background-color: yellow; color: black;">{search_query}</mark>')
                            st.markdown(f'<div class="chat-message assistant-message{highlight_class}">🤖 {highlighted_content}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message assistant-message{highlight_class}">🤖 {content}</div>', unsafe_allow_html=True)
                    with col2:
                        with st.expander("📋", expanded=False):
                            st.code(message["content"], language=None)

        



        with st.form("message_form", clear_on_submit=True):
            col1, col2 = st.columns([9, 1])
            
            with col1:
                user_message = st.text_input(
                    "Type your message…", 
                    placeholder="Chat with Nexia (Press Enter to send)", 
                    label_visibility="collapsed",
                    max_chars=2000,
                    key="message_input"
                )
            
            with col2:
                send_button = st.form_submit_button("➤", use_container_width=True)
            
            if send_button and user_message.strip():
                if not active_chat:
                    active_chat = create_new_chat()
                
                user_msg = {"role": "user", "content": user_message.strip()}
                active_chat["messages"].append(user_msg)
                
                if len(active_chat["messages"]) == 1:
                    # Use actual first message content as title
                    first_msg = user_message.strip()
                    if len(first_msg) > 40:
                        active_chat["title"] = first_msg[:37] + "..."
                    else:
                        active_chat["title"] = first_msg
                
                with st.spinner("Nexia is typing..."):
                    ai_response = send_message_to_groq(active_chat["messages"][:-1], user_message.strip())
                
                ai_msg = {"role": "assistant", "content": ai_response}
                active_chat["messages"].append(ai_msg)
                
                # Generate contextual title that evolves with conversation
                if len(active_chat["messages"]) >= 2:
                    smart_title = generate_chat_title_from_conversation(active_chat["messages"])
                    if smart_title and smart_title != "Chat with Nexia" and len(smart_title) > 3:
                        active_chat["title"] = smart_title
                
                # Update title again after more conversation for better accuracy
                if len(active_chat["messages"]) >= 6:
                    updated_title = generate_chat_title_from_conversation(active_chat["messages"])
                    if updated_title and updated_title != active_chat["title"] and len(updated_title) > 3:
                        active_chat["title"] = updated_title
                
                for i, chat in enumerate(st.session_state.chats):
                    if chat["id"] == active_chat["id"]:
                        st.session_state.chats[i] = active_chat
                        break
                
                save_user_chats(st.session_state.user_email, st.session_state.chats)
                st.rerun()

if __name__ == "__main__":
    main()
