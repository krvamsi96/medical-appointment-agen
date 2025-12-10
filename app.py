"""
Medical Appointment Scheduling Agent - Streamlit Application
Interactive chat interface for scheduling appointments
"""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduling_agent import create_agent
from faq_rag import get_rag_system

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Medical Appointment Scheduler",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #1f77b4;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .info-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #28a745;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1557a0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! 👋 Welcome to HealthCare Plus Clinic. I'm here to help you schedule an appointment or answer any questions you may have about our services. How can I assist you today?"
        })
    
    if "agent" not in st.session_state:
        with st.spinner("Initializing AI agent..."):
            try:
                st.session_state.agent = create_agent()
                st.success("✓ Agent initialized successfully!")
            except Exception as e:
                st.error(f"Error initializing agent: {e}")
                st.stop()
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if "rag_initialized" not in st.session_state:
        with st.spinner("Loading clinic knowledge base..."):
            try:
                st.session_state.rag_system = get_rag_system()
                st.session_state.rag_initialized = True
                st.success("✓ Knowledge base loaded!")
            except Exception as e:
                st.error(f"Error loading knowledge base: {e}")
                st.session_state.rag_initialized = False


def display_message(role: str, content: str):
    """Display a chat message with appropriate styling"""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>🏥 Assistant:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main application"""
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🏥 HealthCare Plus Clinic")
        st.markdown("---")
        
        st.markdown("#### 📞 Contact Information")
        st.markdown("""
        **Phone:** +1-555-123-4567  
        **Email:** info@healthcareplus.com  
        **Hours:** Mon-Fri, 9 AM - 5 PM
        """)
        
        st.markdown("---")
        
        st.markdown("#### 📅 Appointment Types")
        st.markdown("""
        - **General Consultation** (30 min)
        - **Follow-up** (15 min)
        - **Physical Exam** (45 min)
        - **Specialist Consultation** (60 min)
        """)
        
        st.markdown("---")
        
        st.markdown("#### ℹ️ Quick Tips")
        st.markdown("""
        - Have your insurance card ready
        - Arrive 15 minutes early
        - Bring photo ID
        - List current medications
        """)
        
        st.markdown("---")
        
        # Reset conversation button
        if st.button("🔄 Start New Conversation"):
            st.session_state.agent.reset_conversation(st.session_state.session_id)
            st.session_state.messages = []
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Hello! 👋 Welcome to HealthCare Plus Clinic. I'm here to help you schedule an appointment or answer any questions you may have about our services. How can I assist you today?"
            })
            st.rerun()
        
        st.markdown("---")
        
        # Example questions
        with st.expander("💡 Example Questions"):
            st.markdown("""
            **Scheduling:**
            - "I need to see a doctor"
            - "Can I book an appointment?"
            - "What times are available tomorrow?"
            
            **FAQs:**
            - "What insurance do you accept?"
            - "Where are you located?"
            - "What should I bring?"
            - "What's your cancellation policy?"
            """)
        
        st.markdown("---")
        st.markdown("*Powered by LangChain & Groq*")
    
    # Main content
    st.markdown('<div class="main-header">🏥 Medical Appointment Scheduler</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Book appointments and get answers to your questions</div>', unsafe_allow_html=True)
    
    # Display info box
    st.markdown("""
    <div class="info-box">
        <strong>💬 How to use:</strong><br>
        Simply type your message below to schedule an appointment or ask questions about our clinic.
        I can help you find available times, book appointments, and provide information about our services.
    </div>
    """, unsafe_allow_html=True)
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.messages:
            display_message(message["role"], message["content"])
    
    # User input
    user_input = st.chat_input("Type your message here...", key="user_input")
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with chat_container:
            display_message("user", user_input)
        
        # Get agent response
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.chat(
                    user_input,
                    session_id=st.session_state.session_id
                )
                
                # Add assistant message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                
                # Display assistant message
                with chat_container:
                    display_message("assistant", response)
                
            except Exception as e:
                error_message = f"I apologize, but I encountered an error: {str(e)}. Please try again or call our office at +1-555-123-4567."
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })
                
                with chat_container:
                    display_message("assistant", error_message)
        
        # Force rerun to update chat display
        st.rerun()


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        st.error("""
        ⚠️ **GROQ_API_KEY not found!**
        
        Please create a `.env` file in the project root with your Groq API key:
        
        ```
        GROQ_API_KEY=your_api_key_here
        ```
        
        Get your free API key from: https://console.groq.com
        """)
        st.stop()
    
    main()
