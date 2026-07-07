"""
Construction Progress Monitoring Automation Tool
QS4040 - Automation of Repetitive Construction & QS Activities
Author: Nirmal | Dept. of Building Economics, University of Moratuwa

Repetitive tasks automated:
1. Data entry & storage (site inspection records)
2. Automatic photograph renaming/labelling
3. Progress estimation + Gantt chart (planned vs actual)
4. Cost progress monitoring (planned vs actual cost, variance)
5. Automated PDF report generation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from fpdf import FPDF
import os
import io
import zipfile
from PIL import Image

# ---------------------------------------------------------------
# PAGE CONFIG & MODERN STYLING
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Construction Progress Monitor",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes pulseGlow {
        0% { box-shadow: 0 2px 10px rgba(30,58,95,0.15); }
        50% { box-shadow: 0 4px 20px rgba(76,141,255,0.35); }
        100% { box-shadow: 0 2px 10px rgba(30,58,95,0.15); }
    }

    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9eef5 50%, #eef4ff 100%);
    }
    .stApp {
        font-family: 'Segoe UI', sans-serif;
    }
    .block-container {
        animation: fadeInUp 0.6s ease-out;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff, #f0f5ff);
        border: 1px solid #dde5f0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(30,58,95,0.15);
    }
    h1, h2, h3 {
        background: linear-gradient(90deg, #1e3a5f, #2c5580, #3d7ab8);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 6s ease infinite;
    }
    .stButton>button {
        border-radius: 8px;
        background: linear-gradient(90deg, #1e3a5f, #2c5580, #3d7ab8);
        background-size: 200% auto;
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.5em 1.2em;
        transition: background-position 0.4s ease, transform 0.15s ease;
    }
    .stButton>button:hover {
        background-position: right center;
        transform: translateY(-2px) scale(1.02);
        color: white;
        animation: pulseGlow 1.4s ease infinite;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 10px 18px;
        border: 1px solid #e0e4e9;
        transition: all 0.25s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #eef4ff, #dce8fb);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #1e3a5f, #3d7ab8) !important;
        color: white !important;
    }
    div[data-testid="stForm"] {
        border-radius: 14px;
        border: 1px solid #dde5f0;
        padding: 1.2em;
        background: linear-gradient(135deg, #ffffff, #f8fbff);
        animation: fadeInUp 0.5s ease-out;
    }
    div[data-testid="stAlert"] {
        animation: fadeInUp 0.4s ease-out;
        border-radius: 10px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------
# LOGIN GATE
# ---------------------------------------------------------------
APP_USERNAME = "group10"
APP_PASSWORD = "qs4040"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    LOGIN_CSS = """
    <style>
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .stApp {
            background: linear-gradient(-45deg, #1e3a5f, #2c5580, #3d7ab8, #1e3a5f);
            background-size: 400% 400%;
            animation: gradientBG 12s ease infinite;
        }
    </style>
    """
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    login_col1, login_col2, login_col3 = st.columns([1, 1.2, 1])
    with login_col2:
        st.markdown(
            """
            <div style="background: rgba(255,255,255,0.95); padding: 2.2em 2em;
                        border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.25);
                        margin-top: 8vh; text-align:center;">
                <h1 style="-webkit-text-fill-color:#1e3a5f; background:none;">SITE LOGIN</h1>
                <p style="color:#555;">Construction Progress Monitoring System</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Log In")

            if login_submitted:
                if username_input == APP_USERNAME and password_input == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    st.stop()

# ---------------------------------------------------------------
# SESSION STATE INITIALISATION
# (acts as our in-memory "database" - a list of dictionaries)
# ---------------------------------------------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = []          # list of dicts -> task records
if "photo_log" not in st.session_state:
    st.session_state.photo_log = []      # list of dicts -> renamed photo records
if "next_id" not in st.session_state:
    st.session_state.next_id = 1


# ---------------------------------------------------------------
# VALIDATION HELPER FUNCTIONS
# ---------------------------------------------------------------
def validate_task_input(task_name, start_date, end_date, planned_qty, unit_cost):
    """Returns (is_valid: bool, message: str). Basic error handling / validation."""
    errors = []

    if not task_name or task_name.strip() == "":
        errors.append("Task name cannot be empty.")

    if end_date < start_date:
        errors.append("End date cannot be before start date.")

    if planned_qty <= 0:
        errors.append("Planned quantity must be greater than zero.")

    if unit_cost < 0:
        errors.append("Unit cost cannot be negative.")

    # Duplicate task name check
    existing_names = [t["Task Name"].lower() for t in st.session_state.tasks]
    if task_name.strip().lower() in existing_names:
        errors.append(f"Task '{task_name}' already exists. Use a unique name.")

    if errors:
        return False, " | ".join(errors)
    return True, "OK"


def calculate_duration(start_date, end_date):
    """Duration in days (inclusive)."""
    return (end_date - start_date).days + 1


# ---------------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------------
st.sidebar.title("🏗️ Site Control Panel")
st.sidebar.markdown("Construction Progress Monitoring Tool")
st.sidebar.markdown("---")
project_name = st.sidebar.text_input("Project Name", value="Green Heights Mixed Development")
site_location = st.sidebar.text_input("Site Location", value="Colombo, Sri Lanka")
st.sidebar.markdown("---")
st.sidebar.caption("QS4040 Automation Coursework")

# ---------------------------------------------------------------
# MAIN TITLE
# ---------------------------------------------------------------
st.title("🏗️ Construction Progress Monitoring System")
st.markdown(f"**Project:** {project_name}  |  **Location:** {site_location}")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Task Data Entry",
    "📷 Photo Renaming",
    "📊 Progress & Gantt Chart",
    "💰 Cost Monitoring",
    "📄 Final Report"
])

# =================================================================
# TAB 1 : TASK DATA ENTRY & STORAGE  (Repetitive Task #1)
# =================================================================
with tab1:
    st.header("Task Data Entry & Storage")
    st.caption("Replaces manual paper/spreadsheet data entry during daily site inspections.")

    with st.form("task_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input("Task / Activity Name*", placeholder="e.g., Foundation Works")
            start_date = st.date_input("Planned Start Date*", value=date.today())
            planned_qty = st.number_input("Planned Quantity (e.g., m³, m²)*", min_value=0.0, step=1.0)
        with col2:
            unit_cost = st.number_input("Unit Cost (LKR)*", min_value=0.0, step=100.0)
            end_date = st.date_input("Planned End Date*", value=date.today())
            unit_label = st.text_input("Unit of Measurement", value="m³")

        submitted = st.form_submit_button("➕ Add Task")

        if submitted:
            is_valid, message = validate_task_input(task_name, start_date, end_date, planned_qty, unit_cost)
            if is_valid:
                duration = calculate_duration(start_date, end_date)
                new_task = {
                    "ID": st.session_state.next_id,
                    "Task Name": task_name.strip(),
                    "Start Date": start_date,
                    "End Date": end_date,
                    "Duration (days)": duration,
                    "Unit": unit_label,
                    "Planned Qty": planned_qty,
                    "Actual Qty": 0.0,
                    "Actual %": 0.0,
                    "Unit Cost (LKR)": unit_cost,
                    "Planned Cost (LKR)": round(planned_qty * unit_cost, 2),
                    "Last Updated": None,
                }
                st.session_state.tasks.append(new_task)
                st.session_state.next_id += 1
                st.success(f"Task '{task_name}' added successfully.")
            else:
                st.error(message)

    st.markdown("#### Current Task Register")
    if st.session_state.tasks:
        df_tasks = pd.DataFrame(st.session_state.tasks)
        st.dataframe(df_tasks, use_container_width=True, hide_index=True)

        # Export option
        csv_data = df_tasks.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export Task Register (CSV)", csv_data, "task_register.csv", "text/csv")

        # Delete a task
        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            task_to_delete = st.selectbox(
                "Select task to remove (optional)",
                options=[t["Task Name"] for t in st.session_state.tasks],
                key="delete_select"
            )
        with del_col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Delete Task"):
                st.session_state.tasks = [t for t in st.session_state.tasks if t["Task Name"] != task_to_delete]
                st.rerun()
    else:
        st.info("No tasks added yet. Use the form above to begin the task register.")

# =================================================================
# TAB 2 : AUTOMATIC PHOTO RENAMING  (Repetitive Task #2)
# =================================================================
with tab2:
    st.header("Site Photo Upload")
    st.caption("Upload and organise site photographs linked to each task and inspection date.")

    if not st.session_state.tasks:
        st.warning("Please add at least one task in 'Task Data Entry' before labelling photos.")
    else:
        task_names = [t["Task Name"] for t in st.session_state.tasks]
        colA, colB = st.columns(2)
        with colA:
            selected_task = st.selectbox("Link photos to Task", options=task_names)
        with colB:
            photo_date = st.date_input("Date photos were taken", value=date.today())

        uploaded_photos = st.file_uploader(
            "Upload site photographs (multiple allowed)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        if uploaded_photos:
            if st.button("📤 Upload & Store Photos"):
                # Determine starting counter for this task+date combo
                existing_count = len([
                    p for p in st.session_state.photo_log
                    if p["Task"] == selected_task and p["Date"] == photo_date
                ])

                renamed_files = []
                counter = existing_count + 1

                for photo in uploaded_photos:
                    ext = photo.name.split(".")[-1].lower()
                    date_str = photo_date.strftime("%Y%m%d")
                    # sanitize task name for filename use
                    safe_task = "".join(c for c in selected_task if c.isalnum() or c in (" ", "_")).replace(" ", "")
                    new_filename = f"{safe_task}_{date_str}_{counter:03d}.{ext}"

                    image_bytes = photo.read()
                    renamed_files.append((new_filename, image_bytes))

                    st.session_state.photo_log.append({
                        "Original Name": photo.name,
                        "New Name": new_filename,
                        "Task": selected_task,
                        "Date": photo_date,
                        "Bytes": image_bytes
                    })
                    counter += 1

                # Package renamed photos into a downloadable ZIP
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for fname, fbytes in renamed_files:
                        zf.writestr(fname, fbytes)
                zip_buffer.seek(0)

                st.success(f"{len(renamed_files)} photo(s) uploaded successfully.")
                st.download_button(
                    "⬇️ Download Photos (ZIP)",
                    data=zip_buffer,
                    file_name=f"{selected_task}_{photo_date}_photos.zip",
                    mime="application/zip"
                )

                # Preview thumbnails
                preview_cols = st.columns(min(4, len(renamed_files)))
                for i, (fname, fbytes) in enumerate(renamed_files):
                    with preview_cols[i % len(preview_cols)]:
                        st.image(Image.open(io.BytesIO(fbytes)), caption=fname, use_container_width=True)

        st.markdown("#### Photo Log")
        if st.session_state.photo_log:
            df_photos = pd.DataFrame(st.session_state.photo_log)
            st.dataframe(df_photos, use_container_width=True, hide_index=True)
        else:
            st.info("No photos uploaded yet.")

# =================================================================
# TAB 3 : PROGRESS ESTIMATION + GANTT CHART (planned vs actual)
# (Repetitive Task #3)
# =================================================================
def calculate_progress_percent(actual_qty, planned_qty):
    """Automated % completion calculation, capped at 100%."""
    if planned_qty == 0:
        return 0.0
    pct = (actual_qty / planned_qty) * 100
    return round(min(pct, 100.0), 2)


def build_gantt_chart(tasks):
    """Builds a Plotly Gantt-style chart comparing planned duration vs actual progress."""
    rows = []
    for t in tasks:
        # Planned bar (full duration)
        rows.append(dict(
            Task=t["Task Name"], Start=t["Start Date"], Finish=t["End Date"],
            Type="Planned", Progress=100
        ))
        # Actual progress bar -> compute an "actual finish" proxy based on % complete
        total_days = max((t["End Date"] - t["Start Date"]).days, 1)
        actual_days = total_days * (t["Actual %"] / 100)
        actual_finish = t["Start Date"] + pd.Timedelta(days=actual_days)
        rows.append(dict(
            Task=t["Task Name"], Start=t["Start Date"], Finish=actual_finish,
            Type="Actual", Progress=t["Actual %"]
        ))

    df = pd.DataFrame(rows)
    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Task", color="Type",
        color_discrete_map={"Planned": "#b0c4d8", "Actual": "#1e3a5f"},
        title="Planned vs Actual Progress (Gantt Chart)"
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=120 + 60 * len(tasks), legend_title_text="")
    return fig


with tab3:
    st.header("Progress Estimation & Gantt Chart")
    st.caption("Update actual quantity completed - progress %, delay status and Gantt chart update automatically.")

    if not st.session_state.tasks:
        st.warning("Please add tasks first in the 'Task Data Entry' tab.")
    else:
        st.markdown("#### Update Actual Progress")
        for t in st.session_state.tasks:
            with st.expander(f"📌 {t['Task Name']}  ({t['Actual %']}% complete)"):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    new_actual_qty = st.number_input(
                        f"Actual Qty Completed ({t['Unit']})",
                        min_value=0.0, max_value=float(t["Planned Qty"]) * 2,
                        value=float(t["Actual Qty"]), step=1.0,
                        key=f"qty_{t['ID']}"
                    )
                with col2:
                    update_date = st.date_input("As of Date", value=date.today(), key=f"date_{t['ID']}")
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("Update", key=f"update_{t['ID']}"):
                        # Basic validation
                        if new_actual_qty < 0:
                            st.error("Actual quantity cannot be negative.")
                        else:
                            t["Actual Qty"] = new_actual_qty
                            t["Actual %"] = calculate_progress_percent(new_actual_qty, t["Planned Qty"])
                            t["Last Updated"] = update_date
                            st.success(f"{t['Task Name']} updated to {t['Actual %']}% complete.")
                            st.rerun()

        st.markdown("---")
        st.markdown("#### Schedule Variance Status")

        # Calculate expected (planned) progress based on today's date - conditional logic
        today = date.today()
        status_rows = []
        for t in st.session_state.tasks:
            total_days = max((t["End Date"] - t["Start Date"]).days, 1)
            elapsed_days = (min(today, t["End Date"]) - t["Start Date"]).days
            elapsed_days = max(elapsed_days, 0)
            planned_pct = round(min((elapsed_days / total_days) * 100, 100), 2)
            variance = round(t["Actual %"] - planned_pct, 2)

            # Conditional flagging logic
            if variance >= 0:
                status = "✅ On/Ahead of Schedule"
            elif variance >= -10:
                status = "⚠️ Slightly Behind"
            else:
                status = "🔴 Critical Delay"

            status_rows.append({
                "Task": t["Task Name"],
                "Planned %": planned_pct,
                "Actual %": t["Actual %"],
                "Variance %": variance,
                "Status": status
            })

        df_status = pd.DataFrame(status_rows)
        st.dataframe(df_status, use_container_width=True, hide_index=True)

        critical_tasks = [r["Task"] for r in status_rows if "Critical" in r["Status"]]
        if critical_tasks:
            st.error(f"🔴 Critical delay flagged for: {', '.join(critical_tasks)}")

        st.markdown("---")
        st.markdown("#### Gantt Chart: Planned vs Actual")
        gantt_fig = build_gantt_chart(st.session_state.tasks)
        st.plotly_chart(gantt_fig, use_container_width=True)

# =================================================================
# TAB 4 : COST PROGRESS MONITORING (Repetitive Task #4)
# =================================================================
def calculate_cost_variance(planned_cost, actual_cost):
    """Cost variance = Planned - Actual. Positive = under budget, Negative = over budget."""
    return round(planned_cost - actual_cost, 2)


with tab4:
    st.header("Cost Progress Monitoring")
    st.caption("Automated planned vs actual cost calculation, based on progress achieved.")

    if not st.session_state.tasks:
        st.warning("Please add tasks first in the 'Task Data Entry' tab.")
    else:
        cost_rows = []
        total_planned_cost = 0.0
        total_actual_cost = 0.0

        for t in st.session_state.tasks:
            planned_cost = t["Planned Cost (LKR)"]
            actual_cost = round(t["Actual Qty"] * t["Unit Cost (LKR)"], 2)
            variance = calculate_cost_variance(planned_cost, actual_cost)

            # Conditional cost status
            if actual_cost <= planned_cost * (t["Actual %"] / 100 if t["Actual %"] > 0 else 1):
                cost_status = "✅ Within Budget"
            elif variance < 0:
                cost_status = "🔴 Over Budget"
            else:
                cost_status = "🟡 Monitor"

            cost_rows.append({
                "Task": t["Task Name"],
                "Planned Cost (LKR)": planned_cost,
                "Actual Cost (LKR)": actual_cost,
                "Variance (LKR)": variance,
                "Cost Status": cost_status,
            })
            total_planned_cost += planned_cost
            total_actual_cost += actual_cost

        df_cost = pd.DataFrame(cost_rows)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Planned Cost", f"LKR {total_planned_cost:,.2f}")
        m2.metric("Total Actual Cost", f"LKR {total_actual_cost:,.2f}")
        m3.metric(
            "Overall Variance",
            f"LKR {total_planned_cost - total_actual_cost:,.2f}",
            delta=f"{total_planned_cost - total_actual_cost:,.2f}"
        )

        st.markdown("#### Cost Breakdown by Task")
        st.dataframe(df_cost, use_container_width=True, hide_index=True)

        # Cost chart
        cost_fig = go.Figure()
        cost_fig.add_trace(go.Bar(name="Planned Cost", x=df_cost["Task"], y=df_cost["Planned Cost (LKR)"], marker_color="#b0c4d8"))
        cost_fig.add_trace(go.Bar(name="Actual Cost", x=df_cost["Task"], y=df_cost["Actual Cost (LKR)"], marker_color="#1e3a5f"))
        cost_fig.update_layout(barmode="group", title="Planned vs Actual Cost by Task", height=420)
        st.plotly_chart(cost_fig, use_container_width=True)

        over_budget_tasks = [r["Task"] for r in cost_rows if "Over Budget" in r["Cost Status"]]
        if over_budget_tasks:
            st.error(f"🔴 Over budget: {', '.join(over_budget_tasks)}")

# =================================================================
# TAB 5 : AUTOMATED PDF REPORT GENERATION (Repetitive Task #5)
# =================================================================
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def build_gantt_chart_matplotlib(tasks):
    if not tasks:
        return None
    
    fig, ax = plt.subplots(figsize=(10, max(2, len(tasks) * 0.6)))
    tasks_reversed = list(reversed(tasks))
    y_ticks = []
    
    for idx, t in enumerate(tasks_reversed):
        start_num = mdates.date2num(t["Start Date"])
        end_num = mdates.date2num(t["End Date"])
        planned_duration = max(end_num - start_num, 1)
        
        # Planned Progress Bar
        ax.barh(idx + 0.15, planned_duration, left=start_num, height=0.25, color="#b0c4d8", align='center')
        
        # Actual Progress Bar
        actual_duration = planned_duration * (t["Actual %"] / 100)
        ax.barh(idx - 0.15, actual_duration, left=start_num, height=0.25, color="#1e3a5f", align='center')
        y_ticks.append(t["Task Name"])
        
    ax.set_yticks(range(len(tasks_reversed)))
    ax.set_yticklabels(y_ticks, fontsize=10, fontweight='bold', color="#1e3a5f")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#dde5f0')
    ax.spines['bottom'].set_color('#dde5f0')
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#b0c4d8', label='Planned'), Patch(facecolor='#1e3a5f', label='Actual')]
    ax.legend(handles=legend_elements, loc='upper right', frameon=True, facecolor='white', edgecolor='#dde5f0')
    ax.set_title("Planned vs Actual Progress (Gantt Chart Export)", fontsize=12, fontweight='bold', pad=15, color="#1e3a5f")
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
class ProgressReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 58, 95)
        self.cell(0, 10, "Construction Progress Report", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


if st.button("📄 Generate PDF Report", type="primary"):
            with st.spinner("Compiling report..."):
                today = date.today()
                status_rows, cost_rows = [], []
                for t in st.session_state.tasks:
                    total_days = max((t["End Date"] - t["Start Date"]).days, 1)
                    elapsed_days = max((min(today, t["End Date"]) - t["Start Date"]).days, 0)
                    planned_pct = round(min((elapsed_days / total_days) * 100, 100), 2)
                    variance = round(t["Actual %"] - planned_pct, 2)
                    status = "On/Ahead" if variance >= 0 else ("Slightly Behind" if variance >= -10 else "Critical Delay")
                    status_rows.append({
                        "Task": t["Task Name"], "Planned %": planned_pct,
                        "Actual %": t["Actual %"], "Variance %": variance, "Status": status
                    })

                    planned_cost = t["Planned Cost (LKR)"]
                    actual_cost = round(t["Actual Qty"] * t["Unit Cost (LKR)"], 2)
                    cost_rows.append({
                        "Task": t["Task Name"], "Planned Cost (LKR)": planned_cost,
                        "Actual Cost (LKR)": actual_cost,
                        "Variance (LKR)": calculate_cost_variance(planned_cost, actual_cost)
                    })

                # Compile Gantt Chart safely via matplotlib
                try:
                    gantt_png = build_gantt_chart_matplotlib(st.session_state.tasks)
                except Exception as e:
                    gantt_png = None
                    st.error(f"Gantt chart generation failed: {e}")

                pdf_bytes = generate_pdf_report(
                    project_name, site_location,
                    st.session_state.tasks, cost_rows, status_rows,
                    gantt_image_bytes=gantt_png,
                    photo_log=st.session_state.photo_log
                )

            st.success("Report generated successfully!")
            st.download_button(
                "⬇️ Download Progress Report (PDF)",
                data=pdf_bytes,
                file_name=f"{project_name.replace(' ', '_')}_Progress_Report.pdf",
                mime="application/pdf"
            )
# =================================================================
# PDF COMPILATION DEFINITIONS (Must be above Tab 5)
# =================================================================
class ProgressReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 58, 95)
        self.cell(0, 10, "Construction Progress Report", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def generate_pdf_report(project_name, site_location, tasks, cost_rows, status_rows, gantt_image_bytes=None, photo_log=None):
    pdf = ProgressReportPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Project: {project_name}", ln=True)
    pdf.cell(0, 8, f"Location: {site_location}", ln=True)
    pdf.ln(4)

    # --- Task Progress Table ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "1. Task Progress Summary", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    col_widths = [45, 25, 25, 25, 30]
    headers = ["Task", "Planned %", "Actual %", "Variance %", "Status"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for row in status_rows:
        status_clean = row["Status"].encode("latin-1", "ignore").decode("latin-1")
        pdf.cell(col_widths[0], 7, str(row["Task"])[:22], border=1)
        pdf.cell(col_widths[1], 7, str(row["Planned %"]), border=1)
        pdf.cell(col_widths[2], 7, str(row["Actual %"]), border=1)
        pdf.cell(col_widths[3], 7, str(row["Variance %"]), border=1)
        pdf.cell(col_widths[4], 7, status_clean[:16], border=1)
        pdf.ln()

    pdf.ln(6)

    # --- Cost Table ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "2. Cost Monitoring Summary", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    cost_widths = [45, 35, 35, 35]
    cost_headers = ["Task", "Planned Cost", "Actual Cost", "Variance"]
    for w, h in zip(cost_widths, cost_headers):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    total_planned, total_actual = 0.0, 0.0
    for row in cost_rows:
        pdf.cell(cost_widths[0], 7, str(row["Task"])[:22], border=1)
        pdf.cell(cost_widths[1], 7, f"{row['Planned Cost (LKR)']:,.2f}", border=1)
        pdf.cell(cost_widths[2], 7, f"{row['Actual Cost (LKR)']:,.2f}", border=1)
        pdf.cell(cost_widths[3], 7, f"{row['Variance (LKR)']:,.2f}", border=1)
        pdf.ln()
        total_planned += row["Planned Cost (LKR)"]
        total_actual += row["Actual Cost (LKR)"]

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(cost_widths[0], 7, "TOTAL", border=1)
    pdf.cell(cost_widths[1], 7, f"{total_planned:,.2f}", border=1)
    pdf.cell(cost_widths[2], 7, f"{total_actual:,.2f}", border=1)
    pdf.cell(cost_widths[3], 7, f"{total_planned - total_actual:,.2f}", border=1)
    pdf.ln(10)

    # --- Gantt chart image ---
    if gantt_image_bytes:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "3. Gantt Chart (Planned vs Actual)", ln=True)
        pdf.ln(2)
        pdf.image(io.BytesIO(gantt_image_bytes), w=180)
        pdf.ln(10)

    # --- Site Photographs Appendix ---
    if photo_log:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "4. Appendix: Site Photographs", ln=True)
        pdf.ln(4)
        for p in photo_log:
            if "Bytes" in p:
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 5, f"Task: {p['Task']} | Date: {p['Date'].strftime('%Y-%m-%d')}", ln=True)
                pdf.set_font("Helvetica", "I", 8)
                pdf.cell(0, 5, f"File Label: {p['New Name']}", ln=True)
                pdf.ln(2)
                try:
                    pdf.image(io.BytesIO(p["Bytes"]), w=130)
                except Exception as e:
                    pdf.cell(0, 5, f"[Error loading image: {str(e)}]", ln=True)
                pdf.ln(12)

    # --- Signatures ---
    if pdf.get_y() > 210:
        pdf.add_page()
    else:
        pdf.ln(15)

    sec_num = "5" if photo_log else "4"
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"{sec_num}. Approval & Sign-Off", ln=True)
    pdf.ln(14)

    sig_y = pdf.get_y()
    col_width = 85
    gap = 20

    pdf.line(pdf.get_x(), sig_y, pdf.get_x() + col_width, sig_y)
    pdf.set_xy(pdf.get_x(), sig_y + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(col_width, 6, "Quantity Surveyor", ln=0)

    pdf.set_xy(10 + col_width + gap, sig_y)
    pdf.line(pdf.get_x(), sig_y, pdf.get_x() + col_width, sig_y)
    pdf.set_xy(10 + col_width + gap, sig_y + 2)
    pdf.cell(col_width, 6, "Project Manager", ln=1)

    pdf.ln(10)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(col_width, 5, "Name & Date:", ln=0)
    pdf.set_x(10 + col_width + gap)
    pdf.cell(col_width, 5, "Name & Date:", ln=1)

    return bytes(pdf.output(dest="S"))
with tab5:
    st.header("Final Progress Report")
    st.caption("Compiles task progress, cost monitoring and the Gantt chart into one downloadable PDF.")

    if not st.session_state.tasks:
        st.warning("Please add tasks and update progress before generating a report.")
    else:
        st.info(
            "This report includes: task summary, schedule variance, cost variance, and the Gantt chart. "
            "Site photographs are appended to the end of the document."
        )

        if st.button("📄 Generate PDF Report", type="primary", key="final_report_pdf_btn"):
            with st.spinner("Compiling report..."):
                today = date.today()
                status_rows, cost_rows = [], []
                for t in st.session_state.tasks:
                    total_days = max((t["End Date"] - t["Start Date"]).days, 1)
                    elapsed_days = max((min(today, t["End Date"]) - t["Start Date"]).days, 0)
                    planned_pct = round(min((elapsed_days / total_days) * 100, 100), 2)
                    variance = round(t["Actual %"] - planned_pct, 2)
                    status = "On/Ahead" if variance >= 0 else ("Slightly Behind" if variance >= -10 else "Critical Delay")
                    status_rows.append({
                        "Task": t["Task Name"], "Planned %": planned_pct,
                        "Actual %": t["Actual %"], "Variance %": variance, "Status": status
                    })

                    planned_cost = t["Planned Cost (LKR)"]
                    actual_cost = round(t["Actual Qty"] * t["Unit Cost (LKR)"], 2)
                    cost_rows.append({
                        "Task": t["Task Name"], "Planned Cost (LKR)": planned_cost,
                        "Actual Cost (LKR)": actual_cost,
                        "Variance (LKR)": calculate_cost_variance(planned_cost, actual_cost)
                    })

                try:
                    gantt_png = build_gantt_chart_matplotlib(st.session_state.tasks)
                except Exception as e:
                    gantt_png = None
                    st.error(f"Gantt chart generation failed: {e}")

                pdf_bytes = generate_pdf_report(
                    project_name, site_location,
                    st.session_state.tasks, cost_rows, status_rows,
                    gantt_image_bytes=gantt_png,
                    photo_log=st.session_state.photo_log
                )

            st.success("Report generated successfully!")
            st.download_button(
                "⬇️ Download Progress Report (PDF)",
                data=pdf_bytes,
                file_name=f"{project_name.replace(' ', '_')}_Progress_Report.pdf",
                mime="application/pdf"
            )
