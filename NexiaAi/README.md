# Nexia - Friendly AI Companion (Streamlit)

A modern AI chat application with premium UI/UX and emotionally intelligent conversational behavior, built with Streamlit for easy deployment.

## 🚀 Quick Start

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud Deployment
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in dashboard:
   ```
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
4. Deploy!

## ✨ Features

**🔐 Authentication System**
- Clean login/signup interface
- Demo credentials: `demo@nexia.ai` / `demo123`
- Session-based authentication

**🎨 Premium UI/UX**
- Light/Dark mode toggle
- Gradient designs and smooth styling
- Fully responsive layout
- Clean message bubbles

**🤖 AI Companion**
- Powered by Groq API (Llama3-8B)
- Emotionally intelligent responses
- Tanglish language auto-detection
- Auto-generated chat titles

**💬 Chat Features**
- Real-time messaging
- Chat history with sidebar
- Typing indicators
- Persistent conversations

## 🌟 Language Intelligence

Nexia automatically detects and responds in:
- **English** (default)
- **Tanglish** (Tamil-English mix)

Example:
- User: "Enaku romba tired ah iruku today"
- Nexia: "Aiyo 😔 romba tired ah? Today romba heavy day pola. Konjam rest eduthutu pesalama?"

## 🔧 Configuration

### API Key Setup
For local development, add to `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_api_key_here"
```

For Streamlit Cloud, add in the secrets dashboard.

### Demo Credentials
- **Email:** demo@nexia.ai
- **Password:** demo123

## 📁 Project Structure

```
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/
│   ├── config.toml       # Streamlit configuration
│   └── secrets.toml      # API keys (local only)
└── README.md             # This file
```

## 🎯 Deployment Ready

This Streamlit version is optimized for:
- ✅ Streamlit Cloud deployment
- ✅ Stable API integration
- ✅ Session management
- ✅ Responsive design
- ✅ Production performance

## 🔒 Security

- API keys stored in Streamlit secrets
- No hardcoded credentials
- Session-based authentication
- Input validation

## 📱 Mobile Friendly

Fully responsive design that works perfectly on:
- Desktop computers
- Tablets
- Mobile phones

## 🎨 Customization

To modify Nexia's personality, edit the system prompts in the `get_system_prompt()` function.

To change colors and styling, update the CSS in the `st.markdown()` section.

## 🚀 Live Demo

After deployment, your app will be available at:
`https://your-app-name.streamlit.app`

## 📄 License

MIT License - feel free to use this project for learning and development!