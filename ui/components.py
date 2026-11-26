"""Small HTML building blocks for the dashboard.

Every function returns a single-line HTML string (no indentation / blank lines)
so Streamlit's markdown renderer never mistakes it for a code block.
All user-provided text is escaped.
"""
import html as _html
import re
from datetime import datetime

STAGES = ["New", "Qualified", "Proposal", "Negotiation", "Closed"]
STAGE_COLORS = {
    "New": "#8B90B0",
    "Qualified": "#22D3EE",
    "Proposal": "#7C5CFF",
    "Negotiation": "#FBBF24",
    "Closed": "#34D399",
}
PRIORITY_COLORS = {"High": "#F87171", "Medium": "#FBBF24", "Low": "#34D399"}
TASK_COLORS = {"Pending": "#FBBF24", "In Progress": "#22D3EE", "Completed": "#34D399"}
AVATAR_COLORS = ["#7C5CFF", "#22D3EE", "#F472B6", "#34D399", "#FBBF24", "#60A5FA", "#FB923C"]

_STAGE_WIN = {"New": 15, "Qualified": 35, "Proposal": 55, "Negotiation": 75, "Closed": 100}
_PRIORITY_WIN = {"High": 10, "Medium": 0, "Low": -8}


# ---------- helpers ----------
def esc(value) -> str:
    """HTML-escape and neutralise '$' so Streamlit does not treat it as LaTeX."""
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return ""
    return _html.escape(text).replace("$", "&#36;")


def to_int(value) -> int:
    try:
        return int(float(re.sub(r"[^\d.]", "", str(value)) or 0))
    except Exception:
        return 0


def money(n) -> str:
    n = to_int(n)
    if n >= 1_000_000:
        s = f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    elif n >= 10_000:
        s = f"{n / 1_000:.0f}K"
    elif n >= 1_000:
        s = f"{n / 1_000:.1f}".rstrip("0").rstrip(".") + "K"
    else:
        s = str(n)
    return "&#36;" + s


def money_full(n) -> str:
    return "&#36;" + f"{to_int(n):,}"


def initials(name) -> str:
    parts = [p for p in re.split(r"\s+", str(name or "").strip()) if p]
    if not parts:
        return "?"
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()


def avatar_color(name) -> str:
    return AVATAR_COLORS[sum(ord(c) for c in str(name)) % len(AVATAR_COLORS)]


def win_probability(stage, priority) -> int:
    if stage == "Closed":
        return 100
    p = _STAGE_WIN.get(stage, 15) + _PRIORITY_WIN.get(priority, 0)
    return max(5, min(95, p))


def lead_score(priority, deal_value) -> int:
    base = {"High": 78, "Medium": 58, "Low": 38}.get(priority, 38)
    bonus = min(20, to_int(deal_value) // 10_000)
    return max(0, min(100, base + bonus))


def avatar(name, size_class="") -> str:
    return (f'<div class="avatar {size_class}" style="background:{avatar_color(name)}">'
            f'{esc(initials(name))}</div>')


def badge(text, color) -> str:
    return f'<span class="badge" style="--b:{color}">{esc(text)}</span>'


def stage_badge(stage) -> str:
    return badge(stage, STAGE_COLORS.get(stage, "#8B90B0"))


def priority_badge(priority) -> str:
    return badge(priority, PRIORITY_COLORS.get(priority, "#8B90B0"))


# ---------- layout pieces ----------
def page_header(title_plain, title_accent, subtitle, chip="") -> str:
    chip_html = f'<div class="chip">{chip}</div>' if chip else ""
    return (f'<div class="page-head"><div><h1 class="page-title">{esc(title_plain)} '
            f'<span>{esc(title_accent)}</span></h1><div class="page-sub">{esc(subtitle)}</div></div>'
            f'{chip_html}</div>')


def section(title) -> str:
    return f'<div class="section-title">{esc(title)}</div>'


def empty_state(icon, title, text) -> str:
    return f'<div class="empty"><div style="font-size:34px">{icon}</div><b>{esc(title)}</b>{esc(text)}</div>'


def kpi(icon, label, value_html, foot, accent="#7C5CFF") -> str:
    return (f'<div class="card kpi" style="--accent:{accent}"><div class="kpi-icon">{icon}</div>'
            f'<div class="kpi-label">{esc(label)}</div><div class="kpi-value">{value_html}</div>'
            f'<div class="kpi-foot">{esc(foot)}</div></div>')


def kpi_grid(cards) -> str:
    return '<div class="kpi-grid">' + "".join(cards) + "</div>"


def card(inner, title="", sub="") -> str:
    head = ""
    if title:
        head += f'<div class="card-title">{esc(title)}</div>'
    if sub:
        head += f'<div class="card-sub">{esc(sub)}</div>'
    return f'<div class="card">{head}{inner}</div>'


# ---------- charts ----------
def funnel(stage_values: dict, stage_counts: dict) -> str:
    peak = max(stage_values.values()) if stage_values and max(stage_values.values()) > 0 else 1
    rows = []
    for stage in STAGES:
        val = stage_values.get(stage, 0)
        pct = max(3, round(val / peak * 100)) if val else 2
        rows.append(
            f'<div class="bar-row"><div class="bar-name">{stage}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%;--c:{STAGE_COLORS[stage]}"></div></div>'
            f'<div class="bar-val">{money(val)} &middot; {stage_counts.get(stage, 0)}</div></div>')
    return "".join(rows)


def donut(counts: dict, colors: dict, center_label="leads") -> str:
    total = sum(counts.values())
    if total == 0:
        return '<div class="muted">No data yet.</div>'
    stops, angle = [], 0.0
    for key, val in counts.items():
        if not val:
            continue
        sweep = val / total * 360
        stops.append(f'{colors.get(key, "#8B90B0")} {angle:.2f}deg {angle + sweep:.2f}deg')
        angle += sweep
    legend = "".join(
        f'<div><i style="background:{colors.get(k, "#8B90B0")}"></i>{esc(k)}<b>{v}</b></div>'
        for k, v in counts.items())
    return (f'<div class="donut-wrap"><div class="donut" style="background:conic-gradient({", ".join(stops)})">'
            f'<div class="donut-center"><div><b>{total}</b><small>{esc(center_label)}</small></div></div></div>'
            f'<div class="legend">{legend}</div></div>')


def score_ring(score: int, label="AI score") -> str:
    color = "#34D399" if score >= 75 else "#FBBF24" if score >= 55 else "#F87171"
    deg = int(score * 3.6)
    return (f'<div class="ring" style="background:conic-gradient({color} {deg}deg, rgba(255,255,255,.08) {deg}deg)">'
            f'<div class="ring-inner"><b>{score}</b><small>{esc(label)}</small></div></div>')


# ---------- lists ----------
def opportunities(rows) -> str:
    """rows: list of dict-like leads (already sorted)."""
    if not rows:
        return empty_state("🎯", "No opportunities yet", "Analyze a meeting to add your first lead.")
    out = []
    for r in rows:
        out.append(
            f'<div class="opp">{avatar(r["client_name"])}'
            f'<div class="opp-main"><div class="opp-name">{esc(r["client_name"])}</div>'
            f'<div class="opp-sub">{esc(r["company"])} &middot; {esc(r["next_action"])}</div></div>'
            f'<div class="opp-val">{money_full(r["deal_value"])}<small>{stage_badge(r["deal_stage"])}</small></div></div>')
    return "".join(out)


def leads_table(rows) -> str:
    if not rows:
        return empty_state("🔍", "No leads match", "Try clearing the search or filters.")
    body = []
    for r in rows:
        body.append(
            '<tr>'
            f'<td><div class="cell-person">{avatar(r["client_name"])}<div><b>{esc(r["client_name"])}</b>'
            f'<div class="muted" style="font-size:12px">{esc(r["company"])}</div></div></div></td>'
            f'<td class="num">{money_full(r["deal_value"])}</td>'
            f'<td>{stage_badge(r["deal_stage"])}</td>'
            f'<td>{priority_badge(r["priority"])}</td>'
            f'<td class="muted">{esc(r["technical_requirements"])}</td>'
            f'<td>{esc(r["next_action"])}</td></tr>')
    head = "".join(f"<th>{h}</th>" for h in ["Client", "Value", "Stage", "Priority", "Requirements", "Next action"])
    return f'<div class="tbl-wrap"><table class="crm"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def kanban(rows) -> str:
    cols = []
    for stage in STAGES:
        items = [r for r in rows if r["deal_stage"] == stage]
        total = sum(to_int(r["deal_value"]) for r in items)
        cards = "".join(
            f'<div class="kcard" style="--c:{STAGE_COLORS[stage]}"><b>{esc(r["client_name"])}</b>'
            f'<small>{esc(r["company"])}</small><div class="row"><span class="num">{money_full(r["deal_value"])}</span>'
            f'{priority_badge(r["priority"])}</div></div>' for r in items)
        if not cards:
            cards = '<div class="muted" style="font-size:12px;padding:6px">Empty</div>'
        cols.append(f'<div class="kcol"><div class="kcol-head"><div>{stage}</div><span>{len(items)} &middot; {money(total)}</span></div>'
                    f'{cards}</div>')
    return '<div class="kanban">' + "".join(cols) + "</div>"


def task_card(task) -> str:
    status = task["status"]
    return (f'<div class="task"><div class="task-main"><div class="task-name">{esc(task["task_description"])}</div>'
            f'<div class="task-sub">👤 {esc(task["assignee"])} &nbsp;·&nbsp; 🏢 {esc(task["linked_client"])} '
            f'&nbsp;·&nbsp; 📅 {esc(task["deadline"])}</div></div>{badge(status, TASK_COLORS.get(status, "#8B90B0"))}</div>')


def timeline(entries) -> str:
    """entries: list of (timestamp, text)."""
    if not entries:
        return '<div class="muted">No activity yet.</div>'
    items = "".join(f'<div class="tl-item"><div class="tl-time">{esc(t)}</div><div class="tl-text">{esc(x)}</div></div>'
                    for t, x in entries)
    return f'<div class="tl">{items}</div>'


def parse_log(text: str, limit=40):
    """Parse '[timestamp] message' lines, newest first."""
    entries = []
    for line in text.splitlines():
        m = re.match(r"\[(.+?)\]\s*(.*)", line)
        if m:
            entries.append((m.group(1), m.group(2)))
    return list(reversed(entries))[:limit]


def greeting() -> str:
    h = datetime.now().hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"
