# AI-Powered Sales CRM

A sales management application that uses Google Gemini AI to turn unstructured meeting notes into actionable CRM records. It helps sales teams manage leads, track deals, generate follow-up emails, and organize their daily tasks in one place.

## Problem Statement

Sales teams spend a lot of time manually entering meeting details into CRM systems, updating deal stages, and writing follow-up emails. This project reduces repetitive work by automating these steps and providing a central dashboard for tracking sales opportunities.

## Key Features

| Module | Functionality |
| --- | --- |
| Dashboard | Track total leads, pipeline value, high-priority deals, weighted revenue forecasts, and sales insights. |
| AI Studio | Extract lead details from meeting notes using Gemini 3.8 Flash and generate editable follow-up emails. |
| Leads & Pipeline | Search, filter, sort, add, delete, and update leads. View deal stages in a Kanban board and export data as CSV. |
| Tasks | Create and assign tasks, set deadlines, update status, and track overdue work. |
| Activity | View a timestamped history of CRM actions. |

## How It Works

1. Enter meeting notes in AI Studio.
2. Gemini extracts the client name, company, deal value, stage, requirements, priority, and recommended next action.
3. The structured lead is saved to the CRM.
4. The application calculates a lead score and estimated win probability using rule-based logic.
5. Gemini generates a personalized follow-up email that can be edited and downloaded.
6. The dashboard displays updated pipeline metrics and sales opportunities.

## Sales Analytics

- Lead scoring: based on deal priority and deal value.
- Win probability: estimated using deal stage and priority.
- Weighted revenue forecast: sum of each open deal's value multiplied by its estimated win probability.

The scores and forecasts are rule-based estimates, not predictions from a trained machine learning model.

## Tech Stack

- Python 3.11
- Streamlit — web application and dashboard
- Google Gemini 3.8 Flash — lead extraction and email generation
- Pandas — data processing
- Pydantic — structured lead data model
- CSV — local data storage
- HTML and CSS — custom user interface

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/tusharan23/AI-Powered-Sales-CRM.git
cd AI-Powered-Sales-CRM
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows, activate it with `venv\Scripts\activate`.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Gemini API key

Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your own key:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Never commit your `.env` file to GitHub. The non-AI parts of the CRM work without an API key.

### 5. Run the application

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Try the Demo

Use the sidebar to select **Replace data with demo set**, then click **Load demo data**. This replaces existing local lead and task records.

To test AI Studio, configure a Gemini API key and select **Use sample notes**, then click **Analyze meeting**.

## Project Structure

```text
AI-Powered-Sales-CRM/
├── app.py                  # Streamlit application and AI workflow
├── main.py                 # Demo data and activity logging
├── datastore/
│   └── database.py         # CSV data operations
├── ui/
│   ├── components.py       # Reusable UI and scoring functions
│   └── styles.css          # Dashboard styling
├── knowledge_base/         # Supporting project module
├── .streamlit/
│   └── config.toml         # Streamlit theme configuration
├── CRM_Leads.csv           # Lead records
├── Execution_Tasks.csv     # Task records
├── requirements.txt       # Python dependencies
├── .env.example            # API key configuration template
└── README.md
```

## Future Improvements

- Replace CSV storage with a relational database.
- Add user authentication and role-based access.
- Detect duplicate leads before saving.
- Integrate email services for sending follow-ups directly.
- Improve sales forecasts using historical deal outcomes.

## Author

Tushar Chaube
