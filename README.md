# 🤖 AI Sales CRM

An intelligent, AI-powered Customer Relationship Management system that automates lead extraction, prioritization, and sales follow-up using Google's Gemini AI.

## Problem Statement

Traditional CRMs require manual data entry and lack intelligent insights. Sales teams spend valuable time updating records instead of closing deals. This project solves that by using AI to automatically extract structured lead information from meeting notes, prioritize opportunities, and generate personalized follow-up emails.

## Features

### 🎯 AI-Powered Lead Extraction
- Automatically extract structured CRM data from unstructured meeting notes
- Identifies client name, company, deal value, stage, technical requirements, priority, and next actions
- Uses Google Gemini 2.5 Flash for accurate information extraction

### 📊 Intelligent Dashboard
- Real-time pipeline metrics and analytics
- Total leads tracking and pipeline value calculation
- High-priority lead identification
- Visual analytics with deal stage and priority distribution charts

### 🧠 AI Sales Intelligence
- Automatic lead scoring based on priority
- Win probability estimation
- AI-reasoned recommendations for next actions
- Best opportunity identification

### 📧 Automated Follow-Up Emails
- AI-generated professional follow-up emails
- Context-aware content based on meeting details
- One-click email download

### 📝 Activity Logging
- Automatic audit trail of all CRM actions
- Timestamped activity history
- Transparent tracking of data changes

### 🔍 Smart Search
- Instant search across client names and companies
- Filter leads in real-time

## Screenshots

*Add screenshots of your application here*

```
Recommended screenshots:
1. Main dashboard with metrics
2. Meeting notes input and AI analysis
3. CRM leads table with search
4. Pipeline analytics charts
5. AI-generated follow-up email
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Google AI Studio API key ([Get one here](https://aistudio.google.com/app/apikey))

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd lemma-crm
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Your Google Gemini AI API key from Google AI Studio | Yes |

## Running the Project

### Initialize Demo Data
First, seed the database with sample data:
```bash
python main.py
```

### Launch the Application
Start the Streamlit web interface:
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Using the Application
1. **Load Demo Data**: Click "Load Demo Data" in the sidebar to populate sample leads
2. **Analyze Meeting Notes**: Paste meeting notes in the text area and click "Analyze Meeting"
3. **View Results**: AI will extract lead information and display it in the dashboard
4. **Generate Email**: After analysis, an AI-generated follow-up email will appear
5. **Search Leads**: Use the search bar to filter leads by client or company
6. **Download Email**: Click "Download Email" to save the generated follow-up

## Technologies Used

- **Python 3.8+** - Core programming language
- **Streamlit** - Web application framework
- **Google Generative AI (Gemini 2.5 Flash)** - AI/ML engine for lead extraction and email generation
- **Pandas** - Data manipulation and analysis
- **Pydantic** - Data validation and settings management
- **python-dotenv** - Environment variable management

## Future Improvements

- [ ] Multi-language support for global sales teams
- [ ] Integration with popular CRM platforms (Salesforce, HubSpot)
- [ ] Email sending integration (Gmail, Outlook)
- [ ] Advanced analytics and forecasting
- [ ] Lead scoring based on historical data
- [ ] Voice note transcription support
- [ ] Team collaboration features
- [ ] Mobile-responsive design
- [ ] Export leads to CSV/Excel
- [ ] Automated reminder scheduling

## Files to Exclude from GitHub

The following files should NOT be committed to GitHub (already in .gitignore):

- `__pycache__/` - Python bytecode cache
- `.env` - Contains sensitive API keys
- `activity_log.txt` - Runtime activity logs
- `test_api.py` - API testing script
- `test_flash.py` - Model testing script

## License

This project is licensed under the MIT License - feel free to use it for your hackathon projects and beyond.

---

**Built with ❤️ for Hackathon 2024**