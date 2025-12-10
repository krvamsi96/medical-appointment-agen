# Medical Appointment Scheduling Agent

An intelligent conversational AI agent that helps patients schedule medical appointments using LangChain, Groq API, and Streamlit.

## 🌟 Features

- 🤖 **Natural Language Conversations** - Powered by Groq's LLM
- 📅 **Appointment Scheduling** - Book, check availability, manage appointments
- 🔍 **Smart FAQ System** - RAG-based knowledge retrieval with ChromaDB
- 💬 **Streamlit Chat Interface** - User-friendly web interface
- 🎯 **Multiple Appointment Types** - 15-60 minute slots
- 🔄 **Context Switching** - Seamlessly switch between scheduling and FAQs

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Groq API key (free from https://console.groq.com)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd medical-appointment-agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Groq API key
GROQ_API_KEY=your_actual_api_key_here
```

4. **Run the application**
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📋 Configuration

### Environment Variables

Edit `.env` file:

- `GROQ_API_KEY` - Your Groq API key (required)
- `LLM_MODEL` - Model to use (default: openai/gpt-oss-120b)
- `CLINIC_NAME` - Your clinic name
- `CLINIC_PHONE` - Contact phone number
- `CLINIC_EMAIL` - Contact email
- `BUSINESS_START` - Opening time (HH:MM format)
- `BUSINESS_END` - Closing time (HH:MM format)

### Clinic Information

Edit `data/clinic_info.json` to customize:
- FAQ content
- Insurance providers
- Clinic policies
- Services offered

## 💡 Usage

### Book an Appointment

```
You: I need to see a doctor
Agent: I'd be happy to help! What brings you in today?
You: I've been having headaches
Agent: I understand. When would you like to come in?
You: Tomorrow at 2pm
```

### Ask Questions

```
You: What insurance do you accept?
You: Where are you located?
You: What should I bring to my appointment?
```

## 🏗️ Project Structure

```
medical-appointment-agent/
├── app.py                  # Main Streamlit application
├── scheduling_agent.py     # Agent logic
├── agent_tools.py          # LangChain tools
├── prompts.py              # Agent prompts
├── faq_rag.py             # RAG system
├── mock_calendly.py       # Mock Calendly API
├── schemas.py             # Pydantic schemas
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── data/
│   ├── clinic_info.json   # FAQ data
│   └── appointments.json  # Bookings storage
└── chroma_db/             # Vector database (auto-generated)
```

## 🛠️ Tech Stack

- **Backend**: Python 3.10+
- **LLM**: Groq API (openai/gpt-oss-120b)
- **Framework**: LangChain
- **Vector Database**: ChromaDB
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Frontend**: Streamlit
- **Calendar API**: Mock Calendly implementation

## 📝 Appointment Types

- **General Consultation** (30 min) - New health concerns, check-ups
- **Follow-up** (15 min) - Ongoing treatment, test results
- **Physical Exam** (45 min) - Annual physical examination
- **Specialist Consultation** (60 min) - Complex conditions

## 🔧 Troubleshooting

### Application won't start
```bash
# Check if dependencies are installed
pip install -r requirements.txt

# Verify API key in .env
cat .env | grep GROQ_API_KEY
```

### Slow loading (first time)
Normal - downloading embedding model (~90MB). Subsequent runs are faster.

### ChromaDB errors
```bash
# Reset database
rm -rf chroma_db/
# Restart app - will rebuild automatically
```

## 🚀 Deployment

### Streamlit Cloud

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Add `GROQ_API_KEY` to secrets
4. Deploy!

### Docker

```bash
# Build
docker build -t medical-scheduler .

# Run
docker run -p 8501:8501 --env-file .env medical-scheduler
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/)
- Powered by [Groq](https://groq.com/)
- UI with [Streamlit](https://streamlit.io/)

## 📧 Support

For issues or questions, please create an issue in the repository.

---

**Note**: This is a demo application with a mock Calendly API. For production use, integrate with a real calendar service.
