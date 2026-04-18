import streamlit as st
from config import supabase
from logic import generate_project_plan
import time
from datetime import datetime, timedelta
from streamlit_calendar import calendar 
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import base64
import os
from PIL import Image

# --- IMAGE ENCODER ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- APP CONFIG & FAVICON ---
try:
    img = Image.open("logo.png")
    st.set_page_config(page_title="Code2Plan AI", layout="wide", page_icon=img)
except Exception:
    st.set_page_config(page_title="Code2Plan AI", layout="wide", page_icon="🏗️")

# --- PDF Generate
def generate_project_pdf(project, tasks):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    brand_blue = colors.HexColor("#3D52A0")
    
    # --- HEADER SECTION (Top of Page) ---
    # Draw Background Bar for Header
    p.setFillColor(brand_blue)
    p.rect(0, height - 1.2*inch, width, 1.2*inch, fill=1, stroke=0)
    
    # 1. Logo and "Code2Plan" text on the LEFT
    try:
        # Logo Icon
        p.drawImage("logo.png", 0.5*inch, height - 0.95*inch, width=0.5*inch, preserveAspectRatio=True, mask='auto')
        # Brand Name next to logo
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(1.1*inch, height - 0.75*inch, "Code2Plan")
    except:
        # Fallback if logo is missing
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(0.5*inch, height - 0.75*inch, "Code2Plan")

    # 2. Report Title and Project Name on the RIGHT
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 18)
    p.drawRightString(width - 0.5*inch, height - 0.65*inch, "Project Roadmap Report")
    
    p.setFont("Helvetica", 10)
    # This aligns the Project Name to the right edge of the page
    p.drawRightString(width - 0.5*inch, height - 0.9*inch, f"Project: {project['title'].upper()}")
    # --- BODY CONTENT ---
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1*inch, height - 1.8*inch, "Project Overview")
    
    p.setFont("Helvetica", 10)
    p.drawString(1*inch, height - 2.1*inch, f"Tech Stack: {project['tech_stack']}")
    p.drawString(1*inch, height - 2.3*inch, f"Total Duration: {project['duration']}")
    p.drawString(1*inch, height - 2.5*inch, f"Lead: {project['user_email']}")

    # Progress Section
    done = len([t for t in tasks if t['is_completed']])
    total = len(tasks)
    percent = int((done/total)*100) if total > 0 else 0
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1*inch, height - 3.0*inch, "Overall Completion Status")
    
    # Progress Bar UI
    p.setFillColor(colors.HexColor("#F0F2F6"))
    p.roundRect(1*inch, height - 3.4*inch, 4*inch, 0.2*inch, 4, fill=1, stroke=0)
    p.setFillColor(brand_blue)
    p.roundRect(1*inch, height - 3.4*inch, (percent/100)*4*inch, 0.2*inch, 4, fill=1, stroke=0)
    
    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(colors.black)
    p.drawString(5.2*inch, height - 3.35*inch, f"{percent}% Complete")

    # --- TASK TABLE ---
    p.setFillColor(colors.HexColor("#F8F9FA"))
    p.rect(1*inch, height - 4.1*inch, width - 2*inch, 0.3*inch, fill=1, stroke=0)
    
    p.setFillColor(brand_blue)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(1.1*inch, height - 4.0*inch, "PHASE")
    p.drawString(2.5*inch, height - 4.0*inch, "TASK DESCRIPTION")
    p.drawString(width - 2*inch, height - 4.0*inch, "STATUS")

    y_position = height - 4.4*inch
    p.setFont("Helvetica", 9)
    for t in tasks:
        if y_position < 1.5*inch:
            p.showPage()
            y_position = height - 1*inch
            
        status_text = "COMPLETED" if t['is_completed'] else "PENDING"
        p.setFillColor(colors.darkgreen if t['is_completed'] else colors.grey)
        p.drawString(1.1*inch, y_position, t['phase'][:15])
        
        p.setFillColor(colors.black)
        p.drawString(2.5*inch, y_position, t['task_name'][:55])
        p.drawRightString(width - 1.1*inch, y_position, status_text)
        
        p.setStrokeColor(colors.lightgrey)
        p.line(1*inch, y_position - 0.05*inch, width - 1*inch, y_position - 0.05*inch)
        y_position -= 0.3*inch

    # --- FOOTER SECTION (Bottom of Page) ---
    p.setStrokeColor(brand_blue)
    p.setLineWidth(1)
    p.line(0.5*inch, 0.8*inch, width - 0.5*inch, 0.8*inch)
    
    p.setFont("Helvetica-Oblique", 8)
    p.setFillColor(colors.grey)
    footer_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    p.drawCentredString(width/2, 0.5*inch, f"Generated by Code2Plan AI | {footer_date}")
    p.drawCentredString(width/2, 0.35*inch, "Built for Engineers, by Engineers")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- PERSISTENT LOGIN LOGIC ---
if "user_email" not in st.session_state:
    params = st.query_params
    if "user" in params:
        st.session_state.user_email = params["user"]

# --- LANDING PAGE / LOGIN ---
if 'user_email' not in st.session_state:
    try:
        logo_base64 = get_base64_image("logo.png")
        img_src = f"data:image/png;base64,{logo_base64}"
        logo_html = f'<img src="{img_src}" width="200" style="vertical-align: middle; margin-right: 20px;">'
    except Exception:
        logo_html = "🏗️ "

    st.markdown(f"""
        <div style="text-align: center; padding: 40px 0px;">
            <h1 style="font-size: 3.5rem; font-weight: 800; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; flex-wrap: wrap;">
                {logo_html}
                <span style="line-height: 1;">Code2Plan <span style="color: #3D52A0;">AI</span></span>
            </h1>
            <p style="font-size: 1.4rem; color: #888; font-style: italic;">The Intelligent Bridge Between Ideation and Implementation.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.markdown("### Why Code2Plan?")
        st.markdown("""
        - **Instant Roadmap:** Convert high-level ideas into actionable tasks in seconds.
        - **Resource Allocation:** Smart team sizing for Developers, Designers, and QA.
        - **Live Tracking:** Interactive Gantt calendars and progress dashboards.
        - **Professional Reports:** Export your project roadmap as a clean PDF for stakeholders.
        """) 
    with col2:
        with st.container(border=True):
            st.subheader("Secure Workspace Access")
            email = st.text_input("Professional Email Address", placeholder="name@company.com")
            st.caption("Enter your email to sync roadmaps across devices.")
            if st.button("Access Dashboard →", use_container_width=True, type="primary"):
                if email and "@" in email:
                    st.session_state.user_email = email
                    st.query_params["user"] = email
                    st.success("Welcome back! Loading workspace...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Please enter a valid email address.")

    st.markdown("""<div style="margin-top: 50px; text-align: center; color: #555; border-top: 1px solid #333; padding-top: 20px;">
    © 2026 Code2Plan AI | Built for Engineers, by Engineers</div>""", unsafe_allow_html=True)

else:
    # --- DASHBOARD APP ---
    st.sidebar.title("Settings")
    st.sidebar.write(f"Logged in: **{st.session_state.user_email}**")
    if st.sidebar.button("Logout"):
        st.query_params.clear()
        del st.session_state.user_email
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["💬 AI Consultant", "📊 My Roadmaps", "📅 Calendar", "📈 Progress Dashboard"])

    # Fetch projects globally for use in all tabs
    projects_resp = supabase.table("projects").select("*").eq("user_email", st.session_state.user_email).order("created_at", desc=True).execute()
    projects_data = projects_resp.data

    # --- TAB 1: GENERATE PLAN ---
    with tab1:
        st.header("Step 1: Explain your Vision")
        idea = st.text_area("What are you building?", placeholder="E.g., A food delivery app for pets")
        col1, col2 = st.columns(2)
        with col1: stack = st.text_input("Tech Stack", placeholder="React, Node, SQL")
        with col2: dur = st.number_input("Timeframe (in Days)", min_value=1, value=14, step=1)
        st.write("---")
        st.header("Step 2: Allocate your Team")
        available_roles = ["👩‍💻 Developers", "🎨 Designers", "🛡️ QA/Testing", "📋 Product/Project Manager", "☁️ DevOps Eng."]
        selected_roles = st.multiselect("Which roles are required?", available_roles, default=["👩‍💻 Developers"])
        
        role_counts = {}
        if selected_roles:
            col_list = st.columns(len(selected_roles))
            for idx, role in enumerate(selected_roles):
                with col_list[idx]:
                    count = st.number_input(f"{role}", min_value=0, value=1 if "Developers" in role else 0, step=1, key=f"count_{role}")
                    role_counts[role] = count
            total_team_members = sum(role_counts.values())
            
            if total_team_members > 0:
                st.write("---")
                col_sum_left, col_sum_right = st.columns([3, 1])
                with col_sum_left:
                    st.subheader("Total Team Composition")
                    breakdown_str = " | ".join([f"**{r}**: {c}" for r, c in role_counts.items() if c > 0])
                    st.write(f"Roles breakdown: {breakdown_str}")
                with col_sum_right:
                    st.metric(label="Total Members", value=total_team_members)

            if st.button("Generate Timeline ✨", use_container_width=True, type="primary"):
                if not idea or not stack or total_team_members == 0:
                    st.warning("Please provide an idea, tech stack, and at least one team member!")
                else:
                    with st.spinner("AI Agent is architecting your project..."):
                        clean_title = idea[:50]
                        breakdown_str_val = ", ".join([f"{r}: {c}" for r, c in role_counts.items() if c > 0])
                        tasks = generate_project_plan(idea, stack, dur, breakdown_str_val)
                        if tasks:
                            proj = supabase.table("projects").insert({
                                "user_email": st.session_state.user_email,
                                "title": clean_title,
                                "tech_stack": stack,
                                "duration": f"{dur} Days",
                                "team_size": total_team_members,
                                "role_breakdown": breakdown_str_val
                            }).execute()
                            proj_id = proj.data[0]['id']
                            days_per_task = max(1, dur // len(tasks))
                            start_date = datetime.now()
                            for i, t in enumerate(tasks):
                                content = t.get('task') or t.get('task_name') or "General Task"
                                t_start = start_date + timedelta(days=i * days_per_task)
                                t_end = t_start + timedelta(days=days_per_task)
                                supabase.table("tasks").insert({
                                    "project_id": proj_id,
                                    "phase": t.get('phase', 'General'),
                                    "task_name": content,
                                    "is_completed": False,
                                    "start_date": t_start.isoformat(),
                                    "end_date": t_end.isoformat()
                                }).execute()
                            st.balloons()
                            st.success(f"✅ Roadmap Created!")
                            time.sleep(1) 
                            st.rerun()

    # --- TAB 2: ROADMAPS ---
    with tab2:
        st.header("Active Roadmaps")
        if projects_data:
            for p in projects_data:
                with st.expander(f"📂 {p['title'].upper()} — ({p['tech_stack']})"):
                    task_resp = supabase.table("tasks").select("*").eq("project_id", p['id']).order("created_at").execute()
                    current_tasks = task_resp.data
                    completed_tasks = [t for t in current_tasks if t['is_completed']]
                    remaining_tasks = [t for t in current_tasks if not t['is_completed']]
                    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                    with col_btn1:
                        if st.button("🔄 Reset", key=f"reset_{p['id']}", use_container_width=True):
                            supabase.table("tasks").update({"is_completed": False, "completed_at": None}).eq("project_id", p['id']).execute()
                            st.rerun()
                    with col_btn2: 
                        if st.button("↩️ Undo", key=f"undo_{p['id']}", disabled=not len(completed_tasks) > 0, use_container_width=True):
                            supabase.table("tasks").update({"is_completed": False, "completed_at": None}).eq("id", completed_tasks[-1]['id']).execute()
                            st.rerun()
                    with col_btn3:
                        if st.button("🗑️ Delete", key=f"del_{p['id']}", use_container_width=True):
                            supabase.table("projects").delete().eq("id", p['id']).execute()
                            st.rerun()
                    with col_btn4:
                        pdf_data = generate_project_pdf(p, current_tasks)
                        st.download_button(label="📄 Report", data=pdf_data, file_name=f"Report_{p['title']}.pdf", mime="application/pdf", use_container_width=True, key=f"pdf_{p['id']}")
                    
                    st.divider()
                    if current_tasks:
                        st.progress(len(completed_tasks) / len(current_tasks))
                        st.write(f"**Completion:** {int((len(completed_tasks)/len(current_tasks))*100)}% ({len(completed_tasks)}/{len(current_tasks)} tasks)")
                        next_task_id = remaining_tasks[0]['id'] if remaining_tasks else None
                        for t in current_tasks:
                            is_db_done = t['is_completed']
                            is_disabled = is_db_done or (t['id'] != next_task_id)
                            icon = "✅" if is_db_done else ("🚀" if t['id'] == next_task_id else "🔒")
                            if st.checkbox(f"{icon} **[{t['phase']}]** {t['task_name']}", value=is_db_done, key=f"check_{t['id']}", disabled=is_disabled):
                                if not is_db_done:
                                    supabase.table("tasks").update({"is_completed": True, "completed_at": "now()"}).eq("id", t['id']).execute()
                                    st.toast(f"Phase {t['phase']} Completed!")
                                    time.sleep(0.4)
                                    st.rerun()
        else:
            st.info("No roadmaps found. Go to AI Consultant to create one.")

    # --- TAB 3: CALENDAR & MINDMAP ---
    with tab3:
        st.header("📅 Project Schedule & Mindmap")
        
        # Color palette for projects
        colors = ["#FF5733", "#2ECC71", "#3498DB", "#F1C40F", "#9B59B6", "#E67E22"]
        projects = projects_resp.data
        
        if projects:
            # Create a project-to-color map
            project_colors = {p['id']: colors[i % len(colors)] for i, p in enumerate(projects)}

            # --- MINDMAP LEGEND ---
            st.subheader("📌 Mindmap Legend")
            legend_cols = st.columns(len(projects))
            for i, p in enumerate(projects):
                with legend_cols[i]:
                    color = project_colors[p['id']]
                    st.markdown(f"""
                        <div style="padding:10px; border-radius:5px; background-color:{color}; color:white; text-align:center; font-weight:bold;">
                            {p['title'].upper()}
                        </div>
                    """, unsafe_allow_html=True)
            
            st.divider()

            # 2. Build Events (Filtered for incomplete tasks only)
            all_events = []
            for p in projects:
                tasks = supabase.table("tasks").select("*").eq("project_id", p['id']).execute()
                for t in tasks.data:
                    # NEW CONDITION: Only show tasks that are NOT completed
                    if t.get('start_date') and t.get('end_date') and not t['is_completed']:
                        display_name = t.get('phase', 'Task')
                        
                        all_events.append({
                            "id": str(t['id']),
                            "title": display_name, 
                            "start": t['start_date'],
                            "end": t['end_date'],
                            "color": project_colors[p['id']],
                            "allDay": True
                        })

            # 3. Calendar Configuration
            calendar_options = {
                "editable": True,
                "selectable": True,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek",
                },
                "initialView": "dayGridMonth",
            }

            state = calendar(
                events=all_events, 
                options=calendar_options, 
                key="project_calendar_v3" # Updated key for fresh state
            )

            # 4. Handle Drag and Drop Updates
            if state.get("eventChange"):
                event_data = state["eventChange"]["event"]
                supabase.table("tasks").update({
                    "start_date": event_data["start"],
                    "end_date": event_data["end"]
                }).eq("id", event_data["id"]).execute()
                st.toast(f"Updated {event_data['title']} schedule!")
        else:
            st.info("No projects active. Use the AI Consultant to start one!")

    # --- TAB 4: DASHBOARD ---
        with tab4:
            st.header("📊 Global Progress Dashboard")
            
            all_projects = projects_resp.data
            
            if all_projects:
                total_tasks = 0
                total_completed = 0
                project_stats = [] # To store individual project progress
                upcoming_tasks = []

                for p in all_projects:
                    t_resp = supabase.table("tasks").select("*").eq("project_id", p['id']).order("created_at").execute()
                    p_tasks = t_resp.data
                    
                    p_total = len(p_tasks)
                    p_done = len([t for t in p_tasks if t['is_completed']])
                    
                    total_tasks += p_total
                    total_completed += p_done
                    
                    # Save stats for the Workload chart
                    project_stats.append({"name": p['title'], "tasks": p_total})
                    
                    # Identify the "Next Up" task
                    remaining = [t for t in p_tasks if not t['is_completed']]
                    if remaining:
                        upcoming_tasks.append({
                            "project": p['title'],
                            "task": remaining[0]['task_name']
                        })

                # --- 1. METRICS ROW ---
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Projects", len(all_projects))
                m2.metric("Total Tasks", total_tasks)
                m3.metric("Completion Rate", f"{int((total_completed/total_tasks)*100) if total_tasks > 0 else 0}%")

                st.divider()

                # --- 2. THE PIE CHARTS ---
                col_left, col_right = st.columns(2)

                with col_left:
                    st.subheader("Global Task Status")
                    if total_tasks > 0:
                        pending = total_tasks - total_completed
                        fig_status = go.Figure(data=[go.Pie(
                            labels=['Completed', 'Pending'],
                            values=[total_completed, pending],
                            hole=.4,
                            marker_colors=['#2ECC71', '#FF5733']
                        )])
                        fig_status.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
                        st.plotly_chart(fig_status, use_container_width=True)

                with col_right:
                    st.subheader("Pending Tasks by Phase")
                    
                    # Filter for incomplete tasks across all projects
                    all_pending_tasks = []
                    for p in all_projects:
                        t_resp = supabase.table("tasks").select("phase").eq("project_id", p['id']).eq("is_completed", False).execute()
                        all_pending_tasks.extend([t['phase'] for t in t_resp.data])
                    
                    if all_pending_tasks:
                        # Count occurrences of each phase
                        phase_counts = {}
                        for phase in all_pending_tasks:
                            phase_counts[phase] = phase_counts.get(phase, 0) + 1
                        
                        fig_phase = go.Figure(data=[go.Pie(
                            labels=list(phase_counts.keys()),
                            values=list(phase_counts.values()),
                            hole=.4,
                            marker=dict(colors=['#3498DB', '#F1C40F', '#9B59B6', '#E67E22', '#1ABC9C'])
                        )])
                        fig_phase.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
                        st.plotly_chart(fig_phase, use_container_width=True)
                    else:
                        st.success("No pending tasks! Everything is complete.")
                st.divider()

                #-- Chart
                st.subheader("📈 Productivity Velocity (Work Consistency)")

                # 1. Fetch completion data
                # We look at the last 14 days to keep the chart clean
                fourteen_days_ago = (datetime.now() - timedelta(days=14)).isoformat()
                
                history_resp = supabase.table("tasks")\
                    .select("completed_at")\
                    .eq("is_completed", True)\
                    .gte("completed_at", fourteen_days_ago)\
                    .execute()

                if history_resp.data:
                    # 2. Process dates into a count per day
                    dates_list = []
                    for item in history_resp.data:
                        # Convert timestamp string to date object
                        date_obj = datetime.fromisoformat(item['completed_at'].split('T')[0]).date()
                        dates_list.append(date_obj)

                    # Create a range of the last 14 days to ensure 0s are shown
                    last_14_days = [(datetime.now().date() - timedelta(days=i)) for i in range(14)]
                    daily_counts = {d: dates_list.count(d) for d in last_14_days}
                    
                    # Sort by date for the chart
                    sorted_dates = sorted(daily_counts.keys())
                    counts = [daily_counts[d] for d in sorted_dates]

                    # 3. Create the Area Chart
                    fig_velocity = go.Figure()
                    fig_velocity.add_trace(go.Scatter(
                        x=sorted_dates, 
                        y=counts, 
                        fill='tozeroy',
                        line_color='#10B981', # Success Green
                        mode='lines+markers',
                        name='Tasks Completed'
                    ))

                    fig_velocity.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Tasks Finished",
                        margin=dict(t=20, b=20, l=0, r=0),
                        height=300,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white")
                    )
                    
                    st.plotly_chart(fig_velocity, use_container_width=True)
                    
                    # Fun insight message
                    avg_daily = sum(counts) / 14
                    if counts[-1] > avg_daily:
                        st.caption("🚀 You're outperforming your 14-day average today! Keep the momentum.")
                    elif counts[-1] == 0:
                        st.caption("⏸️ No tasks recorded today. A rest day is good for the brain, or time to tackle a 'Quick Win'!")
                else:
                    st.info("No completion history found for the last 14 days. Finish some tasks to see your velocity!")

                # --- 3. MASTER TO-DO LIST ---
                st.subheader("🚀 Next Actions (All Projects)")
                if upcoming_tasks:
                    for item in upcoming_tasks:
                        st.info(f"**{item['project']}**: {item['task']}")
                else:
                    st.success("All projects are 100% complete!")

            else:
                st.info("No projects found. Use the AI Consultant to create one.")
