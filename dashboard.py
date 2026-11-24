"""
NeuroTutor - Modern Interactive Student Learning Dashboard
Visual Intelligence Layer matching reference designs:
- Card-based metric tiles with colored accent borders
- Mastery by Topic horizontal multi-color bar chart
- Assessment Performance donut chart & difficulty tiers
- Topic Explorer with unified inspection metrics
- Topic-specific Learning Roadmap & Concept Mastery
- Cumulative Learning & Performance Trend
- Adaptive Teaching Activity & Recent Learning Activity
Strictly real data only, zero profile mutations.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import profile
from teaching_strategy import get_teaching_style
from knowledge_graph import get_prerequisites, get_concepts


# ==================== Semantic Color Constants ====================
COLOR_BLUE = "#3B82F6"
COLOR_GREEN = "#10B981"
COLOR_PURPLE = "#8B5CF6"
COLOR_AMBER = "#F59E0B"
COLOR_RED = "#EF4444"
COLOR_CYAN = "#00A8E8"


# ==================== Data Extraction (Read-Only) ====================

def clean_topic_name(topic: str) -> str:
    """Clean formatted display name without altering underlying data."""
    if not topic:
        return ""
    t = topic.strip()
    if t.lower().startswith("topic\n") or t.lower().startswith("topic \n"):
        t = t[6:].strip()
    return t


def is_displayable_topic(topic: str) -> bool:
    """Filter out non-educational or empty artifact topics for primary charts."""
    if not topic:
        return False
    t_clean = clean_topic_name(topic).strip()
    if not t_clean or t_clean.upper() == "NONE":
        return False
    lower = t_clean.lower()
    if lower.startswith("the image shows") or lower.startswith("the image presents") or lower.startswith("the diagram shows"):
        return False
    return True


def get_dashboard_summary():
    """
    Compute aggregate metrics across all topics in student profile.
    Strictly read-only; does not mutate any file or state.
    """
    all_topics = profile.get_all_topics()
    
    total_topics_count = len(all_topics)
    displayable_topics = {t: d for t, d in all_topics.items() if is_displayable_topic(t)}
    
    # 1. Average Mastery
    masteries = [d.get("mastery", 0.0) for d in all_topics.values()]
    avg_mastery = (sum(masteries) / len(masteries)) if masteries else 0.0
    
    # 2. Assessment Stats
    total_attempts = 0
    total_correct = 0
    diff_stats = {
        "easy": {"correct": 0, "total": 0},
        "medium": {"correct": 0, "total": 0},
        "hard": {"correct": 0, "total": 0}
    }
    
    for t, data in all_topics.items():
        history = data.get("history", [])
        total_attempts += len(history)
        total_correct += sum(1 for h in history if h is True)
        
        for interaction in data.get("interactions", []):
            diff = interaction.get("difficulty", "medium").lower()
            if diff in diff_stats:
                diff_stats[diff]["total"] += 1
                if interaction.get("correct"):
                    diff_stats[diff]["correct"] += 1
                    
    accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0.0
    
    # 3. Roadmap / Lessons Completed
    total_roadmap_steps = 0
    completed_steps_count = 0
    
    for t, data in all_topics.items():
        roadmap = data.get("roadmap", [])
        total_roadmap_steps += len(roadmap)
        completed = profile.get_completed_steps(t)
        completed_steps_count += len(completed)
        
    return {
        "all_topics": all_topics,
        "displayable_topics": displayable_topics,
        "total_topics_count": total_topics_count,
        "avg_mastery": avg_mastery,
        "total_attempts": total_attempts,
        "total_correct": total_correct,
        "total_incorrect": max(0, total_attempts - total_correct),
        "overall_accuracy": accuracy,
        "diff_stats": diff_stats,
        "total_roadmap_steps": total_roadmap_steps,
        "completed_steps_count": completed_steps_count
    }


def get_recent_activity_events(limit: int = 20):
    """
    Extract chronological list of recent student learning activities.
    Reads from interactions and roadmap completion.
    """
    all_topics = profile.get_all_topics()
    events = []
    
    for t, data in all_topics.items():
        t_name = clean_topic_name(t)
        if not is_displayable_topic(t):
            continue
            
        # Lesson completions
        roadmap = data.get("roadmap", [])
        completed = profile.get_completed_steps(t)
        for idx in completed:
            if idx < len(roadmap):
                events.append({
                    "type": "lesson_completed",
                    "topic": t_name,
                    "raw_topic": t,
                    "title": f"Completed lesson: '{roadmap[idx]}' — {t_name}",
                    "detail": f"Roadmap step {idx+1} of {len(roadmap)}",
                    "icon": "🟢"
                })
                
        # Probe assessment attempts & study interactions
        for inter in data.get("interactions", []):
            concept = inter.get("concept", "Concept")
            correct = inter.get("correct", False)
            diff = inter.get("difficulty", "medium").capitalize()
            res_str = "Correct" if correct else "Needs Review"
            events.append({
                "type": "probe_answered",
                "topic": t_name,
                "raw_topic": t,
                "title": f"Studied: \"{concept}\" — {t_name}",
                "detail": f"Live interactive lesson turn • {res_str} ({diff})",
                "icon": "💬" if correct else "⚠️"
            })
            
    events.reverse()
    return events[:limit]


# ==================== Interactive Dialogs ====================

@st.dialog("📋 All Topics Breakdown")
def show_all_topics_dialog(summary_data):
    """Full detail view for all topics."""
    st.subheader("📋 All Topics & Mastery Breakdown")
    all_topics = summary_data["all_topics"]
    
    rows = []
    for t, data in all_topics.items():
        display_name = clean_topic_name(t)
        m = data.get("mastery", 0.0)
        history = data.get("history", [])
        att = len(history)
        corr = sum(1 for h in history if h is True)
        acc = f"{(corr/att*100):.1f}%" if att > 0 else "N/A"
        
        roadmap = data.get("roadmap", [])
        completed = profile.get_completed_steps(t)
        prog = f"{len(completed)} / {len(roadmap)}" if roadmap else "0 / 0"
        status = "Mastered" if m >= 0.8 else ("In Progress" if (m > 0.2 or len(completed) > 0) else "Started")
        
        rows.append({
            "Topic": display_name,
            "Mastery": f"{int(m*100)}%",
            "Accuracy": acc,
            "Lessons Completed": prog,
            "Status": status
        })
        
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


@st.dialog("🗺️ Full Roadmap Details")
def show_roadmap_dialog(topic: str):
    """Full roadmap dialog for selected topic."""
    disp_name = clean_topic_name(topic)
    st.subheader(f"🗺️ Learning Roadmap: {disp_name}")
    
    roadmap = profile.get_roadmap(topic)
    completed = profile.get_completed_steps(topic)
    prereqs = get_prerequisites(topic)
    
    if prereqs:
        st.write("**Prerequisites:**", ", ".join(prereqs))
        st.markdown("---")
        
    if not roadmap:
        st.info("No roadmap generated for this topic yet.")
        return
        
    st.write(f"**Total Lessons:** {len(roadmap)} | **Completed:** {len(completed)}")
    st.progress(len(completed) / len(roadmap) if roadmap else 0.0)
    
    for i, step in enumerate(roadmap, 1):
        idx = i - 1
        if idx in completed:
            st.markdown(f"🟢 **{i}. {step}** *(Completed)*")
        elif completed and idx == min(max(completed) + 1, len(roadmap) - 1):
            st.markdown(f"🔵 **{i}. {step}** *(Current Lesson)*")
        elif not completed and idx == 0:
            st.markdown(f"🔵 **{i}. {step}** *(Current Lesson)*")
        else:
            st.markdown(f"🔒 **{i}. {step}** *(Upcoming)*")


@st.dialog("🧠 Full Concept Mastery Details")
def show_concepts_dialog(topic: str):
    """Full concept mastery dialog for selected topic."""
    disp_name = clean_topic_name(topic)
    st.subheader(f"🧠 Concept Mastery: {disp_name}")
    
    concepts_dict = profile.get_concepts(topic)
    if not concepts_dict:
        st.info("No concept-level mastery records found for this topic.")
        st.caption("Concepts will be tracked dynamically as you take topic probes.")
        return
        
    for concept, cdata in concepts_dict.items():
        m = cdata.get("mastery", 0.2)
        is_comp = cdata.get("completed", False)
        hist = cdata.get("history", [])
        
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.write(f"**{concept}**" + (" ✅" if is_comp else ""))
            st.progress(max(0.0, min(1.0, m)))
        with col_c2:
            st.metric("Mastery", f"{int(m*100)}%", delta=f"{len(hist)} attempts" if hist else None)
        st.markdown("---")


@st.dialog("🔄 Adaptive Strategy Details")
def show_strategy_dialog(topic: str, mastery: float):
    """Full pedagogical strategy detail dialog."""
    disp_name = clean_topic_name(topic)
    strat = get_teaching_style(topic, mastery)
    
    st.subheader(f"Pedagogical Guidance: {disp_name}")
    st.write(f"**Mastery Level:** {strat.get('level', 'Beginner')}")
    st.write(f"**Active Strategy Code:** `{strat.get('strategy', 'FOUNDATION')}`")
    st.write(f"**Current Mastery Score:** {int(mastery * 100)}%")
    
    st.markdown("### 📘 Tutor Instructions")
    st.markdown(strat.get("instruction", "No instructions."))
    st.caption("NeuroTutor dynamically selects this guidance based on recent attempt accuracy and mastery.")


@st.dialog("🎯 Complete Learning Activity History")
def show_all_activity_dialog():
    """Full activity history log."""
    st.subheader("Complete Learning Activity History")
    events = get_recent_activity_events(limit=50)
    
    if not events:
        st.info("No learning activities recorded yet.")
        return
        
    for ev in events:
        col_icon, col_txt = st.columns([1, 11])
        with col_icon:
            st.write(f"### {ev['icon']}")
        with col_txt:
            st.markdown(f"**{ev['title']}**")
            st.caption(ev['detail'])
        st.markdown("---")


# ==================== Main Dashboard Renderer ====================

def render_dashboard():
    """
    Renders the exact layout and visual design from reference images:
    1. Header: 'NeuroTutor Student Learning Dashboard' + 'Adaptive Mode Active' pill badge
    2. 4 Metric Cards with colored left borders (Blue, Green, Purple, Amber) + progress bars
    3. Mastery by Topic (horizontal multi-color bar chart) & Assessment Performance (donut + difficulty breakdown)
    4. Topic Explorer with 3-metric inspection header
    5. Learning Roadmap (with Completed, Selected for Relearning, Current, Upcoming) & Concept Mastery
    6. Learning & Performance Trend (spline curve with 80% dashed guide)
    7. Adaptive Teaching Activity & Recent Learning Activity
    """
    # ---------------- Styling ----------------
    st.markdown("""
    <style>
    /* Metric Card Styling with Left Accent Border */
    .metric-box-blue {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #3B82F6;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 6px;
    }
    .metric-box-green {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #10B981;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 6px;
    }
    .metric-box-purple {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #8B5CF6;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 6px;
    }
    .metric-box-amber {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #F59E0B;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 6px;
    }
    .metric-tag {
        font-size: 11px;
        font-weight: 700;
        color: #64748B;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-num {
        font-size: 28px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.15;
        margin-bottom: 2px;
    }
    .metric-desc {
        font-size: 12px;
        color: #64748B;
    }

    /* Pill Badges */
    .badge-adaptive {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #1D4ED8;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-strategy {
        background: #F5F3FF;
        border: 1px solid #DDD6FE;
        color: #7C3AED;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-level {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #2563EB;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
    }

    /* Concept notice box */
    .concept-notice-box {
        background: #EFF6FF;
        border: 1px solid #DBEAFE;
        border-radius: 8px;
        padding: 16px 20px;
        color: #1E40AF;
        font-size: 13px;
        font-weight: 500;
        margin-top: 10px;
    }

    /* Modern rounded styling for Plotly horizontal bars */
    .js-plotly-plot .bars path,
    .js-plotly-plot path.point {
        stroke-linejoin: round !important;
        stroke-linecap: round !important;
        paint-order: stroke fill !important;
    }
    </style>
    """, unsafe_allow_html=True)

    summary = get_dashboard_summary()
    all_topics = summary["all_topics"]
    displayable_topics = summary["displayable_topics"]
    
    # ---------------- 1. Top Header ----------------
    h_col1, h_col2 = st.columns([3.5, 1.2])
    with h_col1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 26px;">🧠</span>
            <span style="font-size: 24px; font-weight: 700; color: #1E293B;">NeuroTutor Student Learning Dashboard</span>
        </div>
        <div style="font-size: 13px; color: #64748B; margin-top: 2px; margin-bottom: 12px;">
            Real-time visual intelligence across knowledge mastery, roadmaps, and adaptive assessments.
        </div>
        """, unsafe_allow_html=True)
    with h_col2:
        st.markdown("""
        <div style="text-align: right; padding-top: 6px;">
            <span class="badge-adaptive"><span style="font-size: 8px;">●</span> Adaptive Mode Active</span>
        </div>
        """, unsafe_allow_html=True)

    # ---------------- 2. Top 4 Metric Cards ----------------
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-box-blue">
            <div class="metric-tag">📚 TOPICS IN PLAN</div>
            <div class="metric-num">{summary['total_topics_count']}</div>
            <div class="metric-desc">Active curriculum topics</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(1.0)

    with m2:
        avg_m = summary['avg_mastery']
        st.markdown(f"""
        <div class="metric-box-green">
            <div class="metric-tag">🎯 AVERAGE MASTERY</div>
            <div class="metric-num">{avg_m * 100:.1f}%</div>
            <div class="metric-desc">Across all enrolled topics</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, avg_m)))

    with m3:
        acc = summary['overall_accuracy']
        st.markdown(f"""
        <div class="metric-box-purple">
            <div class="metric-tag">📝 ASSESSMENT ACCURACY</div>
            <div class="metric-num">{acc:.1f}%</div>
            <div class="metric-desc">{summary['total_correct']} / {summary['total_attempts']} probes correct</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, acc / 100)))

    with m4:
        comp_l = summary['completed_steps_count']
        tot_l = summary['total_roadmap_steps']
        road_pct = (comp_l / tot_l * 100) if tot_l > 0 else 0.0
        st.markdown(f"""
        <div class="metric-box-amber">
            <div class="metric-tag">🏁 LESSONS COMPLETED</div>
            <div class="metric-num">{comp_l} / {tot_l}</div>
            <div class="metric-desc">{road_pct:.1f}% roadmap completed</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, comp_l / tot_l if tot_l > 0 else 0.0)))

    st.write("")

    # ---------------- 3. Mastery by Topic & Assessment Performance ----------------
    r1_col1, r1_col2 = st.columns(2)

    # Left: Mastery by Topic
    with r1_col1:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size: 16px; font-weight: 700; color: #1E293B; margin-bottom: 6px;">
                📊 Mastery by Topic
            </div>
            """, unsafe_allow_html=True)
            
            chart_items = []
            for t, d in displayable_topics.items():
                chart_items.append({
                    "topic": clean_topic_name(t),
                    "mastery": round(d.get("mastery", 0.0) * 100, 1)
                })
            chart_items.sort(key=lambda x: x["mastery"], reverse=True)
            top_chart = chart_items[:6]
            
            if top_chart:
                df_chart = pd.DataFrame(top_chart)
                # Multi-color bar palette matching reference image:
                bar_palette = ["#00A8E8", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6", "#3B82F6"]
                assigned_colors = [bar_palette[i % len(bar_palette)] for i in range(len(df_chart))]
                
                fig_m = go.Figure(go.Bar(
                    x=df_chart["mastery"],
                    y=df_chart["topic"],
                    orientation="h",
                    width=0.55,
                    text=[f"{v:.0f}%" for v in df_chart["mastery"]],
                    textposition="outside",
                    marker=dict(
                        color=assigned_colors,
                        line=dict(color=assigned_colors, width=5)
                    )
                ))
                fig_m.update_layout(
                    margin=dict(l=10, r=40, t=10, b=10),
                    height=255,
                    bargap=0.32,
                    xaxis=dict(range=[0, 105], dtick=20, showgrid=True, gridcolor="#F1F5F9"),
                    yaxis=dict(autorange="reversed"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="sans-serif", size=12, color="#334155")
                )
                st.plotly_chart(fig_m, use_container_width=True)
            else:
                st.info("No topic mastery data available yet.")
                
            if st.button("📖 View All Topics Breakdown", key="btn_view_all_topics", use_container_width=True):
                show_all_topics_dialog(summary)

    # Right: Assessment Performance
    with r1_col2:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size: 16px; font-weight: 700; color: #1E293B; margin-bottom: 6px;">
                🍩 Assessment Performance
            </div>
            """, unsafe_allow_html=True)
            
            if summary["total_attempts"] > 0:
                donut_col, legend_col = st.columns([1.1, 1.3])
                
                with donut_col:
                    d_fig = go.Figure(data=[go.Pie(
                        labels=["Correct", "Incorrect"],
                        values=[summary["total_correct"], summary["total_incorrect"]],
                        hole=0.70,
                        marker=dict(colors=["#10B981", "#EF4444"]),
                        textinfo="none",
                        hoverinfo="label+value+percent"
                    )])
                    d_fig.update_layout(
                        showlegend=False,
                        margin=dict(l=5, r=5, t=5, b=5),
                        height=160,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        annotations=[dict(
                            text=f"<b style='font-size:22px;color:#0F172A;'>{summary['overall_accuracy']:.0f}%</b><br><span style='font-size:11px;color:#64748B;'>Accuracy</span>",
                            x=0.5, y=0.5,
                            showarrow=False
                        )]
                    )
                    st.plotly_chart(d_fig, use_container_width=True)
                    
                with legend_col:
                    st.write("")
                    corr_p = (summary['total_correct'] / summary['total_attempts'] * 100)
                    inc_p = 100 - corr_p
                    st.markdown(f"""
                    <div style="font-size: 13px; line-height: 2.1; padding-top: 4px;">
                        <div>🟢 <b>Correct:</b> {summary['total_correct']} ({corr_p:.1f}%)</div>
                        <div>🔴 <b>Incorrect:</b> {summary['total_incorrect']} ({inc_p:.1f}%)</div>
                        <div>🎯 <b>Total Attempts:</b> {summary['total_attempts']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("<div style='font-size: 12px; color: #64748B; margin: 6px 0 4px 0;'>Performance by Difficulty Tier:</div>", unsafe_allow_html=True)
                diffs = summary["diff_stats"]
                dc1, dc2, dc3 = st.columns(3)
                
                with dc1:
                    e_c = diffs["easy"]["correct"]
                    e_t = diffs["easy"]["total"]
                    st.markdown(f"<div style='font-size: 12px; color: #334155;'>Easy ({e_c}/{e_t})</div>", unsafe_allow_html=True)
                    st.progress((e_c / e_t) if e_t > 0 else 0.0)
                with dc2:
                    m_c = diffs["medium"]["correct"]
                    m_t = diffs["medium"]["total"]
                    st.markdown(f"<div style='font-size: 12px; color: #334155;'>Medium ({m_c}/{m_t})</div>", unsafe_allow_html=True)
                    st.progress((m_c / m_t) if m_t > 0 else 0.0)
                with dc3:
                    h_c = diffs["hard"]["correct"]
                    h_t = diffs["hard"]["total"]
                    st.markdown(f"<div style='font-size: 12px; color: #334155;'>Hard ({h_c}/{h_t})</div>", unsafe_allow_html=True)
                    st.progress((h_c / h_t) if h_t > 0 else 0.0)
            else:
                st.info("No assessment attempts recorded yet.")

    st.write("")

    # ---------------- 4. Topic Explorer ----------------
    topic_options = list(displayable_topics.keys())
    if not topic_options:
        topic_options = list(all_topics.keys())
        
    current_session_topic = st.session_state.learning_session.get("topic")
    default_idx = 0
    if current_session_topic in topic_options:
        default_idx = topic_options.index(current_session_topic)

    with st.container(border=True):
        st.markdown("""
        <div style="font-size: 17px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">
            🔍 Topic Explorer
        </div>
        """, unsafe_allow_html=True)
        
        t_col_sel, t_col_m, t_col_acc, t_col_prog = st.columns([2.5, 1.2, 1.2, 1.2])
        with t_col_sel:
            explore_topic = st.selectbox(
                "Select Topic to Inspect:",
                options=topic_options,
                index=default_idx if topic_options else 0,
                format_func=clean_topic_name,
                key="dash_explorer_topic_main"
            )
            
        exp_data = all_topics.get(explore_topic, {})
        exp_mastery = exp_data.get("mastery", 0.2)
        exp_roadmap = exp_data.get("roadmap", [])
        exp_completed = profile.get_completed_steps(explore_topic)
        exp_history = exp_data.get("history", [])
        exp_corr = sum(1 for h in exp_history if h is True)
        exp_acc_str = f"{(exp_corr/len(exp_history)*100):.1f}%" if exp_history else "N/A"
        explore_name = clean_topic_name(explore_topic)
        
        with t_col_m:
            st.markdown(f"""
            <div style="font-size: 12px; color: #64748B; font-weight: 600;">🎯 Topic Mastery</div>
            <div style="font-size: 24px; font-weight: 700; color: #0F172A;">{exp_mastery * 100:.1f}%</div>
            """, unsafe_allow_html=True)
            
        with t_col_acc:
            st.markdown(f"""
            <div style="font-size: 12px; color: #64748B; font-weight: 600;">📝 Probe Accuracy</div>
            <div style="font-size: 24px; font-weight: 700; color: #0F172A;">{exp_acc_str}</div>
            """, unsafe_allow_html=True)
            
        with t_col_prog:
            st.markdown(f"""
            <div style="font-size: 12px; color: #64748B; font-weight: 600;">🏁 Lessons Progress</div>
            <div style="font-size: 24px; font-weight: 700; color: #0F172A;">{len(exp_completed)} / {len(exp_roadmap)}</div>
            """, unsafe_allow_html=True)

    # ---------------- 5. Learning Roadmap & Concept Mastery ----------------
    r2_c1, r2_c2 = st.columns(2)
    selected_relearn_step = st.session_state.learning_session.get("selected_step")

    with r2_c1:
        with st.container(border=True):
            st.markdown(f"""
            <div style="font-size: 16px; font-weight: 700; color: #1E293B;">
                🗺️ Learning Roadmap: <i>{explore_name}</i>
            </div>
            """, unsafe_allow_html=True)
            
            tot_steps = len(exp_roadmap)
            comp_steps = len(exp_completed)
            pct_steps = (comp_steps / tot_steps * 100) if tot_steps > 0 else 0.0
            st.caption(f"Progress: {comp_steps} / {tot_steps} lessons completed ({pct_steps:.1f}%)")
            st.progress(comp_steps / tot_steps if tot_steps > 0 else 0.0)
            
            if exp_roadmap:
                for idx, step in enumerate(exp_roadmap[:5]):
                    num = idx + 1
                    if idx in exp_completed:
                        if selected_relearn_step is not None and idx == selected_relearn_step and explore_topic == current_session_topic:
                            st.markdown(f"🟣 **{num}. {step}** *(Selected for Relearning)*")
                        else:
                            st.markdown(f"🟢 **{num}. {step}** *(Completed)*")
                    elif exp_completed and idx == min(max(exp_completed) + 1, tot_steps - 1):
                        st.markdown(f"🔵 **{num}. {step}** *(Current Lesson)*")
                    elif not exp_completed and idx == 0:
                        st.markdown(f"🔵 **{num}. {step}** *(Current Lesson)*")
                    else:
                        st.markdown(f"🔒 **{num}. {step}** *(Upcoming)*")
                        
                if len(exp_roadmap) > 5:
                    st.caption(f"... and {len(exp_roadmap) - 5} more lessons in this roadmap")
            else:
                st.info("No roadmap available for this topic.")
                
            if st.button("🗺️ View Full Roadmap Details", key="btn_view_roadmap_details", use_container_width=True):
                show_roadmap_dialog(explore_topic)

    with r2_c2:
        with st.container(border=True):
            st.markdown(f"""
            <div style="font-size: 16px; font-weight: 700; color: #1E293B;">
                🧠 Concept Mastery: <i>{explore_name}</i>
            </div>
            """, unsafe_allow_html=True)
            
            exp_concepts = exp_data.get("concepts", {})
            if exp_concepts:
                c_items = []
                for c_k, c_v in exp_concepts.items():
                    c_items.append({
                        "name": c_k,
                        "mastery": c_v.get("mastery", 0.2)
                    })
                c_items.sort(key=lambda x: x["mastery"], reverse=True)
                for ci in c_items[:4]:
                    m_val = ci["mastery"]
                    st.write(f"• **{ci['name']}**: `{int(m_val * 100)}%`")
                    st.progress(max(0.0, min(1.0, m_val)))
                if len(c_items) > 4:
                    st.caption(f"... and {len(c_items) - 4} more concepts")
            else:
                st.markdown("""
                <div class="concept-notice-box">
                    Concept-level mastery is not recorded yet for this topic.
                </div>
                """, unsafe_allow_html=True)
                
            st.write("")
            if st.button("🧠 View Full Concept Details", key="btn_view_concept_details", use_container_width=True):
                show_concepts_dialog(explore_topic)

    st.write("")

    # ---------------- 6. Learning & Performance Trend ----------------
    with st.container(border=True):
        st.markdown("""
        <div style="font-size: 16px; font-weight: 700; color: #1E293B; margin-bottom: 4px;">
            📈 Learning & Performance Trend
        </div>
        """, unsafe_allow_html=True)
        
        if exp_history and len(exp_history) >= 2:
            cumulative_rates = []
            running_correct = 0
            for idx, res in enumerate(exp_history, 1):
                if res is True:
                    running_correct += 1
                cumulative_rates.append(round(running_correct / idx * 100, 1))
                
            trend_fig = go.Figure()
            # Reference line at 80%
            trend_fig.add_shape(
                type="line",
                x0=1,
                x1=len(exp_history),
                y0=80,
                y1=80,
                line=dict(color="#CBD5E1", width=1.5, dash="dash")
            )
            trend_fig.add_trace(go.Scatter(
                x=list(range(1, len(exp_history) + 1)),
                y=cumulative_rates,
                mode="lines+markers",
                line=dict(color="#3B82F6", width=3, shape="spline"),
                marker=dict(size=7, color="#8B5CF6", line=dict(color="#3B82F6", width=2)),
                name="Performance Trend",
                hovertemplate="Event #%{x}: %{y:.1f}%<extra></extra>"
            ))
            trend_fig.update_layout(
                margin=dict(l=10, r=20, t=10, b=10),
                height=230,
                xaxis=dict(title="Interaction Event #", dtick=1, showgrid=True, gridcolor="#F1F5F9"),
                yaxis=dict(range=[0, 105], dtick=20, title="Cumulative Performance (%)", showgrid=True, gridcolor="#F1F5F9"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="sans-serif", size=12, color="#334155")
            )
            st.plotly_chart(trend_fig, use_container_width=True)
            st.caption(f"Showing actual cumulative assessment performance across interaction events for {explore_name}.")
        else:
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 24px; text-align: center; color: #64748B; margin: 8px 0;">
                No assessment interaction events recorded yet for {explore_name}. Complete probes in the Tutor to generate performance trends.
            </div>
            """, unsafe_allow_html=True)
            st.caption("Historical mastery snapshots are not recorded over time.")

    # ---------------- 7. Adaptive Teaching Activity & Recent Learning Activity ----------------
    r3_c1, r3_c2 = st.columns(2)
    strat = get_teaching_style(explore_topic, exp_mastery)
    strat_code = strat.get("strategy", "BUILD")
    level_name = strat.get("level", "Intermediate")

    with r3_c1:
        with st.container(border=True):
            st.markdown(f"""
            <div style="font-size: 16px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">
                🔄 Adaptive Teaching Activity
            </div>
            <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span class="badge-strategy">Strategy: {strat_code}</span>
                <span class="badge-level">Level: {level_name}</span>
            </div>
            <div style="font-size: 13px; line-height: 2.0; color: #334155;">
                <div>• <b>Active Topic:</b> <i>{explore_name}</i></div>
                <div>• <b>Current Mastery:</b> {exp_mastery * 100:.1f}%</div>
                <div>• <b>Assessment Accuracy:</b> {exp_acc_str}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            if st.button("🔄 View Strategy Details", key="btn_view_strategy_details", use_container_width=True):
                show_strategy_dialog(explore_topic, exp_mastery)

    with r3_c2:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size: 16px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">
                🎯 Recent Learning Activity
            </div>
            """, unsafe_allow_html=True)
            
            recent_events = get_recent_activity_events(limit=3)
            if recent_events:
                for ev in recent_events:
                    st.markdown(f"""
                    <div style="margin-bottom: 8px;">
                        <div style="font-size: 13px; font-weight: 600; color: #1E293B;">
                            {ev['icon']} {ev['title']}
                        </div>
                        <div style="font-size: 11px; color: #64748B; margin-left: 20px;">
                            {ev['detail']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No recent learning activity recorded yet.")
                
            if st.button("🎯 View Complete Activity History", key="btn_view_all_activity_details", use_container_width=True):
                show_all_activity_dialog()
