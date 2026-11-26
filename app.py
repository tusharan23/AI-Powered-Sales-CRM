import os
import sys
import json
from datetime import date

from dotenv import load_dotenv
from pydantic import BaseModel

import pandas as pd
import streamlit as st

try:
    from google import genai
except Exception:  # keeps the dashboard usable even if the SDK is missing
    genai = None

# ==========================================================
# SETUP
# ==========================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

load_dotenv()

st.set_page_config(
    page_title="AI Sales CRM",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from datastore import database  # noqa: E402
from main import seed_demo_data, log_action  # noqa: E402
from ui import components as ui  # noqa: E402

API_KEY = os.getenv("GEMINI_API_KEY")
AI_READY = bool(API_KEY) and API_KEY != "YOUR_GEMINI_API_KEY" and genai is not None
client = genai.Client(api_key=API_KEY) if AI_READY else None

with open(os.path.join(ROOT_DIR, "ui", "styles.css"), encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def html(markup: str):
    st.markdown(markup, unsafe_allow_html=True)


# ==========================================================
# DATA MODEL
# ==========================================================

class Lead(BaseModel):
    client_name: str
    company: str
    deal_value: str = "0"
    deal_stage: str = "New"
    technical_requirements: str = ""
    priority: str = "Low"
    next_action: str = ""


LEAD_COLUMNS = [
    "client_name", "company", "deal_value", "deal_stage",
    "technical_requirements", "priority", "next_action",
]

# ==========================================================
# AI ENGINE (same prompts / model as before)
# ==========================================================

LEAD_EXTRACTION_PROMPT = """
You are an expert AI Sales CRM assistant.

Your job is to analyze meeting notes and extract structured CRM data.

Return ONLY valid JSON.

Schema:

{
    "client_name": "",
    "company": "",
    "deal_value": "",
    "deal_stage": "",
    "technical_requirements": "",
    "priority": "",
    "next_action": ""
}

Rules:

1. deal_value must contain only digits.
2. If deal value is missing return "0".

3. deal_stage must be one of:
- New
- Qualified
- Proposal
- Negotiation
- Closed

4. priority must be:
- High
- Medium
- Low

Decide priority using:
- Deal value
- Urgency
- Customer interest
- Decision maker involvement

5. next_action should be ONE short recommendation.

Examples:
- Send Proposal
- Schedule Demo
- Follow up after 3 days
- Call client tomorrow

Return ONLY valid JSON.

Meeting Notes:
"""

EMAIL_PROMPT = """
You are an expert B2B sales executive.

Write a professional follow-up email.

The email should:

• Thank the client for the meeting.
• Mention the discussed requirements.
• Mention the proposed solution.
• Mention the deal value if available.
• Mention the agreed next action.
• Sound professional and friendly.
• Be concise.
• Include a subject line.
"""


def clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text.replace("```json", "", 1)
    if text.startswith("```"):
        text = text.replace("```", "", 1)
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def extract_lead_info(text: str):
    if not text.strip() or client is None:
        return None
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=LEAD_EXTRACTION_PROMPT + "\n\n" + text,
        )
        try:
            data = json.loads(clean_json(response.text))
        except json.JSONDecodeError:
            st.error("Gemini returned invalid JSON. Please try again.")
            return None

        if not data.get("client_name") and not data.get("company"):
            return None

        return Lead(
            client_name=data.get("client_name", ""),
            company=data.get("company", ""),
            deal_value=str(data.get("deal_value", "0")),
            deal_stage=data.get("deal_stage", "New"),
            technical_requirements=data.get("technical_requirements", ""),
            priority=data.get("priority", "Low"),
            next_action=data.get("next_action", ""),
        )
    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ Gemini API quota exceeded. Check your key or billing in Google AI Studio.")
        else:
            st.error(f"AI error: {e}")
    return None


def generate_followup_email(lead: Lead) -> str:
    prompt = f"""
{EMAIL_PROMPT}

Client Name: {lead.client_name}
Company: {lead.company}
Technical Requirements: {lead.technical_requirements}
Deal Value: {lead.deal_value}
Current Stage: {lead.deal_stage}
Priority: {lead.priority}
Next Action: {lead.next_action}
"""
    response = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
    return response.text


# ==========================================================
# DATA HELPERS
# ==========================================================

def load_leads() -> list:
    rows = database.CRMLeadsDB.get_all()
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=LEAD_COLUMNS)
    for col in LEAD_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[LEAD_COLUMNS].fillna("")
    records = df.to_dict("records")
    for i, r in enumerate(records):
        r["_i"] = i
        r["deal_value"] = ui.to_int(r["deal_value"])
    return records


def load_tasks() -> list:
    rows = database.ExecutionTasksDB.get_all()
    out = []
    for i, r in enumerate(rows):
        r = {k: ("" if str(v) == "nan" else v) for k, v in r.items()}
        r["_i"] = i
        out.append(r)
    return out


def load_activity_log() -> str:
    path = os.path.join(ROOT_DIR, "activity_log.txt")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def add_new_lead(lead: Lead):
    database.CRMLeadsDB.add(
        lead.client_name, lead.company, lead.deal_value, lead.deal_stage,
        lead.technical_requirements, lead.priority, lead.next_action,
    )
    log_action(f"Lead created: {lead.client_name} | {lead.company} | {lead.priority}")


def overdue_tasks(tasks) -> list:
    today = pd.Timestamp(date.today())
    result = []
    for t in tasks:
        if t["status"] == "Completed":
            continue
        d = pd.to_datetime(t["deadline"], errors="coerce")
        if pd.notna(d) and d < today:
            result.append(t)
    return result


SAMPLE_NOTES = (
    "Met Rahul Sharma from ABC Technologies today. They want an AI chatbot for customer "
    "support on their website, budget around $50,000. CTO joined the call and is keen to "
    "deploy within two weeks. He asked for a detailed proposal by Friday."
)

# ==========================================================
# SIDEBAR
# ==========================================================

def load_demo():
    seed_demo_data()
    log_action("Loaded demo CRM data")
    st.session_state.confirm_demo = False


NAV_ITEMS = ["📊  Dashboard", "🧠  AI Studio", "👥  Leads & Pipeline", "✅  Tasks", "🕑  Activity"]

with st.sidebar:
    html('<div class="brand"><div class="brand-logo">🤖</div><div><div class="brand-name">AI Sales CRM</div>'
         '<div class="brand-sub">Powered by Gemini</div></div></div>')
    html('<div class="side-label">Menu</div>')
    page = st.radio("Navigation", NAV_ITEMS, key="nav", label_visibility="collapsed")

    html('<div class="side-label">System</div>')
    if AI_READY:
        html('<div class="status-pill"><span class="dot on"></span>Gemini connected</div>')
    else:
        html('<div class="status-pill"><span class="dot off"></span>Gemini key missing<br>AI features off</div>')

    html('<div class="side-label">Data</div>')
    confirm = st.checkbox("Replace data with demo set", key="confirm_demo")
    st.button("Load demo data", use_container_width=True, disabled=not confirm, on_click=load_demo)

leads = load_leads()
tasks = load_tasks()

# ==========================================================
# PAGE: DASHBOARD
# ==========================================================

def page_dashboard():
    html(ui.page_header(f"{ui.greeting()},", "here's your pipeline",
                        "A live view of your deals, priorities and next steps.",
                        chip=f"📅 {date.today().strftime('%A, %d %B %Y')}"))

    if not leads:
        html(ui.empty_state("📭", "Your CRM is empty",
                            "Head to AI Studio to analyze a meeting, or load the demo data from the sidebar."))
        return

    open_leads = [r for r in leads if r["deal_stage"] != "Closed"]
    total_value = sum(r["deal_value"] for r in leads)
    open_value = sum(r["deal_value"] for r in open_leads)
    high = sum(1 for r in leads if r["priority"] == "High")
    forecast = sum(r["deal_value"] * ui.win_probability(r["deal_stage"], r["priority"]) / 100 for r in open_leads)
    avg = total_value // len(leads) if leads else 0

    html(ui.kpi_grid([
        ui.kpi("📋", "Total leads", str(len(leads)), f"{len(open_leads)} still open", "#7C5CFF"),
        ui.kpi("💰", "Pipeline value", ui.money_full(total_value), f"Avg deal {ui.money_full(avg)}", "#22D3EE"),
        ui.kpi("🔥", "High priority", str(high), "Needs attention first", "#F87171"),
        ui.kpi("📈", "Weighted forecast", ui.money_full(forecast), "Value × win probability", "#34D399"),
    ]))

    stage_values = {s: sum(r["deal_value"] for r in leads if r["deal_stage"] == s) for s in ui.STAGES}
    stage_counts = {s: sum(1 for r in leads if r["deal_stage"] == s) for s in ui.STAGES}
    prio_counts = {p: sum(1 for r in leads if r["priority"] == p) for p in ["High", "Medium", "Low"]}

    html(ui.section("Pipeline overview"))
    c1, c2 = st.columns([1.6, 1])
    with c1:
        html(ui.card(ui.funnel(stage_values, stage_counts), "Deal funnel", "Value and number of deals per stage"))
    with c2:
        html(ui.card(ui.donut(prio_counts, ui.PRIORITY_COLORS), "Priority mix", "How urgent your leads are"))

    html(ui.section("Focus areas"))
    c3, c4 = st.columns([1.6, 1])
    with c3:
        top = sorted(open_leads or leads, key=lambda r: r["deal_value"], reverse=True)[:5]
        html(ui.card(ui.opportunities(top), "Top opportunities", "Biggest open deals by value"))
    with c4:
        insights = []
        if open_leads:
            best = max(open_leads, key=lambda r: r["deal_value"])
            insights.append(f"🚀 <b>Best opportunity:</b> {ui.esc(best['client_name'])} "
                            f"({ui.esc(best['company'])}) at {ui.money_full(best['deal_value'])}. "
                            f"Next: {ui.esc(best['next_action'])}.")
        risky = [r for r in open_leads if r["priority"] == "High" and r["deal_stage"] in ("New", "Qualified")]
        if risky:
            names = ", ".join(ui.esc(r["client_name"]) for r in risky[:3])
            insights.append(f"⚡ <b>Move faster:</b> high-priority leads still early in the funnel: {names}.")
        late = overdue_tasks(tasks)
        if late:
            insights.append(f"⏰ <b>{len(late)} overdue task{'s' if len(late) != 1 else ''}</b> need a new date or a follow-up.")
        if not insights:
            insights.append("✅ Nothing urgent. Your pipeline looks healthy.")
        body = "".join(f'<div style="margin-bottom:14px;font-size:13.5px;line-height:1.5">{i}</div>' for i in insights)
        html(ui.card(body, "🤖 AI Sales Coach", "Suggestions based on your current data"))


# ==========================================================
# PAGE: AI STUDIO
# ==========================================================

def use_sample():
    st.session_state.notes = SAMPLE_NOTES


def page_ai_studio():
    html(ui.page_header("AI", "Studio", "Paste raw meeting notes and get a structured lead, a score and a ready-to-send email."))

    if not AI_READY:
        st.warning("Add your `GEMINI_API_KEY` to the `.env` file and restart to enable AI features. "
                   "The rest of the CRM works without it.")

    left, right = st.columns([1.5, 1])
    with left:
        st.text_area("Meeting notes", key="notes", height=260,
                     placeholder="Met Rahul from ABC Pvt Ltd. Budget is $50,000. Needs an AI chatbot. "
                                 "Requested a proposal by Friday...",
                     label_visibility="collapsed")
        b1, b2 = st.columns([1, 1])
        analyze = b1.button("✨ Analyze meeting", type="primary", use_container_width=True, disabled=not AI_READY)
        b2.button("Use sample notes", on_click=use_sample, use_container_width=True)
    with right:
        html(ui.card(
            '<div style="font-size:13.5px;line-height:1.9">'
            '👤 Client &amp; company<br>💰 Deal value<br>📍 Deal stage<br>🔧 Technical requirements<br>'
            '🔥 Priority &amp; AI score<br>🚀 Recommended next action<br>📧 Follow-up email</div>',
            "What the AI extracts", "Everything is saved to your CRM automatically"))

    if analyze:
        notes = st.session_state.get("notes", "")
        if not notes.strip():
            st.warning("Please enter some meeting notes first.")
        else:
            with st.status("Analyzing meeting notes…", expanded=True) as status:
                st.write("🔍 Detecting client and company")
                lead = extract_lead_info(notes)
                if lead is None:
                    status.update(label="Could not extract CRM data", state="error")
                else:
                    st.write("💾 Saving lead to CRM")
                    add_new_lead(lead)
                    st.session_state.latest_lead = lead
                    st.write("📧 Writing follow-up email")
                    try:
                        st.session_state.email = generate_followup_email(lead)
                    except Exception:
                        st.session_state.email = ""
                        st.error("The AI service is busy right now. Click **Analyze meeting** again in a few seconds.")
                    status.update(label="Analysis complete", state="complete", expanded=False)

    lead = st.session_state.get("latest_lead")
    if lead:
        score = ui.lead_score(lead.priority, lead.deal_value)
        win = ui.win_probability(lead.deal_stage, lead.priority)
        facts = (
            f'<div class="fact"><small>Client</small><div>{ui.esc(lead.client_name)}</div></div>'
            f'<div class="fact"><small>Company</small><div>{ui.esc(lead.company)}</div></div>'
            f'<div class="fact"><small>Deal value</small><div>{ui.money_full(lead.deal_value)}</div></div>'
            f'<div class="fact"><small>Win probability</small><div>{win}%</div></div>'
            f'<div class="fact"><small>Stage</small><div>{ui.stage_badge(lead.deal_stage)}</div></div>'
            f'<div class="fact"><small>Priority</small><div>{ui.priority_badge(lead.priority)}</div></div>'
            f'<div class="fact" style="grid-column:1/-1"><small>Requirements</small>'
            f'<div style="font-weight:500">{ui.esc(lead.technical_requirements)}</div></div>')
        inner = (f'<div class="result-grid">{ui.score_ring(score)}<div><div class="facts">{facts}</div></div></div>'
                 f'<div class="callout">🚀 <b>Recommended next action:</b> {ui.esc(lead.next_action)}</div>')
        html(ui.section("Latest analysis"))
        html(ui.card(inner, "Lead added to your CRM", "Score reflects priority and deal size"))

    if "email" in st.session_state and st.session_state.email:
        html(ui.section("Follow-up email"))
        st.session_state.email = st.text_area("Generated email (editable)", value=st.session_state.email, height=320)
        st.download_button("📥 Download email", st.session_state.email, file_name="followup_email.txt")


# ==========================================================
# PAGE: LEADS & PIPELINE
# ==========================================================

def page_leads():
    html(ui.page_header("Leads &", "Pipeline", "Search, filter, move deals between stages and add leads manually.",
                        chip=f"{len(leads)} leads"))

    f1, f2, f3, f4 = st.columns([2, 1.2, 1.2, 1.2])
    search = f1.text_input("Search", placeholder="🔍  Search client or company", label_visibility="collapsed")
    stage_f = f2.multiselect("Stage", ui.STAGES, placeholder="All stages", label_visibility="collapsed")
    prio_f = f3.multiselect("Priority", ["High", "Medium", "Low"], placeholder="All priorities", label_visibility="collapsed")
    sort_by = f4.selectbox("Sort", ["Value: high → low", "Value: low → high", "Name A–Z", "Newest first"],
                           label_visibility="collapsed")

    rows = list(leads)
    if search:
        q = search.lower()
        rows = [r for r in rows if q in str(r["client_name"]).lower() or q in str(r["company"]).lower()]
    if stage_f:
        rows = [r for r in rows if r["deal_stage"] in stage_f]
    if prio_f:
        rows = [r for r in rows if r["priority"] in prio_f]
    if sort_by == "Value: high → low":
        rows.sort(key=lambda r: r["deal_value"], reverse=True)
    elif sort_by == "Value: low → high":
        rows.sort(key=lambda r: r["deal_value"])
    elif sort_by == "Name A–Z":
        rows.sort(key=lambda r: str(r["client_name"]).lower())
    else:
        rows.sort(key=lambda r: r["_i"], reverse=True)

    st.write("")
    tab_table, tab_board, tab_manage = st.tabs(["Table", "Pipeline board", "Manage"])

    with tab_table:
        html(ui.leads_table(rows))
        if leads:
            csv = pd.DataFrame(leads)[LEAD_COLUMNS].to_csv(index=False)
            st.download_button("📤 Export CSV", csv, file_name="crm_leads.csv", mime="text/csv")

    with tab_board:
        html(ui.kanban(rows))

    with tab_manage:
        m1, m2 = st.columns(2)
        with m1:
            with st.form("add_lead", clear_on_submit=True):
                st.markdown("**➕ Add a lead**")
                name = st.text_input("Client name")
                company = st.text_input("Company")
                value = st.number_input("Deal value ($)", min_value=0, step=1000, value=0)
                a, b = st.columns(2)
                stage = a.selectbox("Stage", ui.STAGES)
                prio = b.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                reqs = st.text_input("Technical requirements")
                nxt = st.text_input("Next action")
                if st.form_submit_button("Add lead", type="primary"):
                    if not name.strip() or not company.strip():
                        st.warning("Client name and company are required.")
                    else:
                        add_new_lead(Lead(client_name=name.strip(), company=company.strip(), deal_value=str(int(value)),
                                          deal_stage=stage, technical_requirements=reqs, priority=prio, next_action=nxt))
                        st.rerun()
        with m2:
            with st.container(border=True):
                st.markdown("**✏️ Update or remove a lead**")
                if not leads:
                    st.caption("No leads yet.")
                else:
                    labels = {r["_i"]: f"{r['client_name']} · {r['company']} ({r['deal_stage']})" for r in leads}
                    chosen = st.selectbox("Lead", list(labels.keys()), format_func=lambda i: labels[i])
                    new_stage = st.selectbox("Move to stage", ui.STAGES, key="move_stage")
                    u1, u2 = st.columns(2)
                    if u1.button("Update stage", use_container_width=True):
                        database.CRMLeadsDB.update_stage(chosen, new_stage)
                        log_action(f"Stage changed to {new_stage}: {labels[chosen]}")
                        st.rerun()
                    if u2.button("Delete lead", use_container_width=True):
                        database.CRMLeadsDB.delete(chosen)
                        log_action(f"Lead deleted: {labels[chosen]}")
                        st.rerun()


# ==========================================================
# PAGE: TASKS
# ==========================================================

def page_tasks():
    html(ui.page_header("Execution", "Tasks", "Track what needs to happen to move each deal forward.",
                        chip=f"{len(overdue_tasks(tasks))} overdue"))

    counts = {s: sum(1 for t in tasks if t["status"] == s) for s in ["Pending", "In Progress", "Completed"]}
    html(ui.kpi_grid([
        ui.kpi("⏳", "Pending", str(counts["Pending"]), "Not started", "#FBBF24"),
        ui.kpi("⚙️", "In progress", str(counts["In Progress"]), "Being worked on", "#22D3EE"),
        ui.kpi("✅", "Completed", str(counts["Completed"]), "Done", "#34D399"),
        ui.kpi("⏰", "Overdue", str(len(overdue_tasks(tasks))), "Past their deadline", "#F87171"),
    ]))

    html(ui.section("All tasks"))
    left, right = st.columns([1.6, 1])
    with left:
        status_f = st.multiselect("Status", ["Pending", "In Progress", "Completed"], placeholder="All statuses",
                                  label_visibility="collapsed")
        shown = [t for t in tasks if not status_f or t["status"] in status_f]
        if shown:
            html("".join(ui.task_card(t) for t in shown))
        else:
            html(ui.empty_state("🗂️", "No tasks", "Add one on the right."))
    with right:
        with st.form("add_task", clear_on_submit=True):
            st.markdown("**➕ New task**")
            desc = st.text_input("Task")
            who = st.text_input("Assignee")
            linked = st.selectbox("Linked company", sorted({str(r["company"]) for r in leads}) or ["—"])
            due = st.date_input("Deadline", value=date.today())
            stat = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
            if st.form_submit_button("Add task", type="primary"):
                if not desc.strip():
                    st.warning("Please describe the task.")
                else:
                    database.ExecutionTasksDB.add(desc.strip(), who.strip(), str(due), stat, linked)
                    log_action(f"Task added: {desc.strip()}")
                    st.rerun()
        if tasks:
            with st.container(border=True):
                st.markdown("**🔄 Update a task**")
                labels = {t["_i"]: t["task_description"] for t in tasks}
                chosen = st.selectbox("Task", list(labels.keys()), format_func=lambda i: labels[i])
                new_status = st.selectbox("New status", ["Pending", "In Progress", "Completed"], key="task_status")
                t1, t2 = st.columns(2)
                if t1.button("Update", use_container_width=True, key="task_upd"):
                    database.ExecutionTasksDB.update_status(chosen, new_status)
                    log_action(f"Task {new_status}: {labels[chosen]}")
                    st.rerun()
                if t2.button("Delete", use_container_width=True, key="task_del"):
                    database.ExecutionTasksDB.delete(chosen)
                    log_action(f"Task deleted: {labels[chosen]}")
                    st.rerun()


# ==========================================================
# PAGE: ACTIVITY
# ==========================================================

def page_activity():
    html(ui.page_header("Activity", "Log", "A transparent audit trail of everything that changed in your CRM."))
    entries = ui.parse_log(load_activity_log(), limit=60)
    if entries:
        html(ui.card(ui.timeline(entries), "Recent activity", "Newest first"))
    else:
        html(ui.empty_state("🕑", "No activity yet", "Actions like adding leads or loading demo data will show up here."))


# ==========================================================
# ROUTER
# ==========================================================

if page == NAV_ITEMS[0]:
    page_dashboard()
elif page == NAV_ITEMS[1]:
    page_ai_studio()
elif page == NAV_ITEMS[2]:
    page_leads()
elif page == NAV_ITEMS[3]:
    page_tasks()
else:
    page_activity()
