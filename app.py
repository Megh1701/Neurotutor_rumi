import streamlit as st
import ollama
import os
import time

from rag import process_pdf, ask_pdf
from teaching_strategy import get_teaching_style
from probe import generate_probe, evaluate_answer, explain_mistake
from topic import is_followup, extract_topic
from student_profile import (
    adjust_mastery,
    get_mastery,
    get_all_topics,
    save_roadmap,
    get_roadmap,
    complete_step,
    get_completed_steps,
    update_concept,
    get_weakest_concept,
    add_interaction,
)
from advisor import get_revision_plan
from knowledge_graph import get_related_topics, get_prerequisites, get_concepts, next_concept
from session import initialize_session
from adaptive_explanation import classify_response, choose_explanation_style, build_explanation_prompt
from knowledge_tracing import is_improving, is_struggling, get_accuracy
from lesson_memory import save_lesson, get_last_lesson, clear_lesson
from concepts import get_taught_concepts
from lesson_planner import create_lesson_plan, roadmap_to_list  
from graph_controller import graph
from visual_learning import explain_image, check_vision_model
from teaching_strategy import get_teaching_style as get_visual_teaching_style
from dashboard import render_dashboard, clean_topic_name

# ==================== Page Config ====================
st.set_page_config(
    page_title="NeuroTutor",
    page_icon="🧠",
    layout="wide"
)

if "learning_session" not in st.session_state:
    st.session_state.learning_session = initialize_session()

# ==================== Navigation ====================
if "nav_selection" not in st.session_state:
    st.session_state["nav_selection"] = "🎓 Tutor"

nav_options = ["🎓 Tutor", "📊 Dashboard"]
current_nav_idx = (
    nav_options.index(st.session_state["nav_selection"])
    if st.session_state.get("nav_selection") in nav_options
    else 0
)

selected_nav = st.sidebar.radio(
    "Navigation",
    nav_options,
    index=current_nav_idx,
    key="main_nav_radio"
)
st.session_state["nav_selection"] = selected_nav

# When dashboard is selected, hand off to dashboard renderer
if selected_nav == "📊 Dashboard":
    render_dashboard()
    st.stop()

# ==================== Left Sidebar: Enrolled Topics & Inline Roadmap ====================
st.sidebar.markdown("""
<div style="margin-top: 4px; margin-bottom: 12px;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 22px;">🧠</span>
        <span style="font-weight: 700; font-size: 18px; color: #0F172A;">NeuroTutor</span>
    </div>
    <div style="font-size: 11px; color: #64748B; margin-left: 30px;">Adaptive Learning System</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<div style='font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; margin: 12px 0 8px 0;'>📊 ENROLLED TOPICS</div>", unsafe_allow_html=True)

topics = get_all_topics()
active_topic = st.session_state.learning_session.get("topic")

if len(topics) == 0:
    st.sidebar.caption("No enrolled topics yet. Ask a question to begin learning.")
else:
    for topic, data in topics.items():
        disp_name = clean_topic_name(topic)
        if not disp_name or disp_name.upper() == "NONE":
            continue
            
        mastery = data.get("mastery", 0.2)
        mastery_pct = int(mastery * 100)
        is_active = (topic == active_topic)
        
        # Topic Card
        if is_active:
            st.sidebar.markdown(f"""
            <div style="background: #FFFFFF; border: 1.5px solid #3B82F6; border-radius: 10px; padding: 10px 12px; margin-bottom: 4px;">
                <div style="font-weight: 700; color: #0F172A; font-size: 13.5px;">● {disp_name}</div>
                <div style="font-size: 11.5px; color: #64748B; margin: 2px 0 5px 0;">Mastery: {mastery_pct}%</div>
                <div style="height: 4px; background: #FEE2E2; border-radius: 2px; overflow: hidden;">
                    <div style="width: {mastery_pct}%; height: 100%; background: #EF4444; border-radius: 2px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.sidebar.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 12px; margin-bottom: 4px;">
                <div style="font-weight: 700; color: #0F172A; font-size: 13.5px;">{disp_name}</div>
                <div style="font-size: 11.5px; color: #64748B; margin: 2px 0 5px 0;">Mastery: {mastery_pct}%</div>
                <div style="height: 4px; background: #FEE2E2; border-radius: 2px; overflow: hidden;">
                    <div style="width: {mastery_pct}%; height: 100%; background: #EF4444; border-radius: 2px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Resume Button
        if st.sidebar.button(f"▶ Resume {disp_name}", key=f"resume_{topic}", use_container_width=True):
            st.session_state.learning_session = initialize_session()
            st.session_state.learning_session["topic"] = topic
            st.session_state.learning_session["resumed_session"] = True
            st.session_state.learning_session["selected_step"] = None

            roadmap = get_roadmap(topic)
            completed = get_completed_steps(topic)

            st.session_state.learning_session["roadmap_steps"] = roadmap
            st.session_state.learning_session["completed_steps"] = completed

            if completed:
                st.session_state.learning_session["current_step"] = min(
                    len(roadmap) - 1,
                    max(completed) + 1
                )
            else:
                st.session_state.learning_session["current_step"] = 0

            st.rerun()

        # If this is the active/resumed topic, display its Learning Roadmap IMMEDIATELY underneath
        if is_active:
            roadmap = get_roadmap(active_topic)
            completed = get_completed_steps(active_topic)
            current = st.session_state.learning_session.get("current_step", 0)
            selected = st.session_state.learning_session.get("selected_step", None)

            if roadmap:
                st.sidebar.markdown(f"""
                <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 8px 10px; margin: 6px 0 6px 0;">
                    <div style="font-size: 11px; font-weight: 700; color: #1E40AF; text-transform: uppercase;">📚 LEARNING ROADMAP</div>
                    <div style="font-size: 10.5px; color: #3B82F6;">Curriculum path for {disp_name}</div>
                </div>
                """, unsafe_allow_html=True)

                for i, step in enumerate(roadmap):
                    num = i + 1
                    if i in completed:
                        if selected is not None and i == selected:
                            # Relearning highlighted state
                            st.sidebar.markdown(f"""
                            <div style="background: #EFF6FF; border: 2px solid #3B82F6; border-radius: 8px; padding: 7px 10px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 700; color: #1E40AF; font-size: 12.5px;">🟣 {num}. {step}</span>
                                <span style="background: #DBEAFE; color: #1D4ED8; font-size: 9.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">RELEARNING</span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Clickable completed step for relearning
                            if st.sidebar.button(f"✅ {num}. {step}", key=f"lesson_{i}", use_container_width=True):
                                st.session_state.learning_session["selected_step"] = i
                                st.rerun()
                    elif i == current:
                        st.sidebar.markdown(f"""
                        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 7px 10px; margin-bottom: 4px; font-size: 12.5px; color: #334155;">
                            ● <b>{num}. {step} (Current)</b>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.sidebar.markdown(f"""
                        <div style="background: #F8FAFC; border: 1px solid #F1F5F9; border-radius: 8px; padding: 7px 10px; margin-bottom: 4px; font-size: 12.5px; color: #94A3B8;">
                            🔒 {num}. {step}
                        </div>
                        """, unsafe_allow_html=True)

                if selected is not None and selected != current:
                    if st.sidebar.button("↩️ Return to current lesson", use_container_width=True):
                        st.session_state.learning_session["selected_step"] = None
                        st.rerun()

# ==================== Derive Real Active Metrics ====================
active_name = clean_topic_name(active_topic) if active_topic else "General Learning"
active_data = topics.get(active_topic, {}) if active_topic else {}
active_mastery = active_data.get("mastery", 0.2)
active_roadmap = active_data.get("roadmap", [])
active_completed = get_completed_steps(active_topic) if active_topic else []
active_history = active_data.get("history", [])
active_corr = sum(1 for h in active_history if h is True)
active_att = len(active_history)
active_acc = (active_corr / active_att * 100) if active_att > 0 else 0.0

strat = get_teaching_style(active_topic or "General", active_mastery)
strat_code = strat.get("strategy", "FOUNDATION")
strat_level = strat.get("level", "Beginner")

# ==================== Main Page: Hero Section ====================
hero_c1, hero_c2 = st.columns([5, 1.2])

with hero_c1:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="background: #EFF6FF; border: 1.5px solid #DBEAFE; border-radius: 12px; width: 52px; height: 52px; display: flex; align-items: center; justify-content: center; font-size: 30px;">
                🧠
            </div>
            <div>
                <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 3px;">
                    <span style="font-size: 31px; font-weight: 850; background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.6px; line-height: 1.15; display: inline-flex; align-items: center;">NeuroTutor</span>
                    <span style="background: #F5F3FF; border: 1px solid #DDD6FE; color: #7C3AED; font-weight: 700; font-size: 11px; border-radius: 9999px; padding: 2px 9px;">✨ AI TUTOR</span>
                    <span style="background: #F0FDF4; border: 1px solid #BBF7D0; color: #15803D; font-weight: 600; font-size: 11px; border-radius: 9999px; padding: 2px 9px;">● Active Session</span>
                    <span style="background: #EFF6FF; border: 1px solid #BFDBFE; color: #1D4ED8; font-weight: 600; font-size: 11px; border-radius: 9999px; padding: 2px 9px;">📖 {active_name}</span>
                </div>
                <div style="font-size: 13.5px; font-weight: 600; color: #334155;">
                    Your Adaptive AI Study Assistant • <span style="font-size: 12px; color: #64748B; font-weight: 400;">Learn smarter, build deep mastery</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with hero_c2:
    st.write("")
    if st.button("🆕 New Chat", use_container_width=True):
        st.session_state.learning_session = initialize_session()
        st.rerun()

# ==================== Top 4 Statistics Tiles ====================
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #10B981; border-radius: 10px; padding: 12px 14px; margin-bottom: 2px;">
        <div style="font-size: 10.5px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase;">🎯 MASTERY</div>
        <div style="font-size: 26px; font-weight: 800; color: #0F172A; line-height: 1.2; margin: 3px 0 2px 0;">{int(active_mastery * 100)}%</div>
        <div style="font-size: 11.5px; color: #64748B;">Active: {active_name}</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(max(0.0, min(1.0, active_mastery)))

with m2:
    comp_c = len(active_completed)
    tot_c = len(active_roadmap)
    pct_c = int(comp_c / tot_c * 100) if tot_c > 0 else 0
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #3B82F6; border-radius: 10px; padding: 12px 14px; margin-bottom: 2px;">
        <div style="font-size: 10.5px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase;">📚 PROGRESS</div>
        <div style="font-size: 26px; font-weight: 800; color: #0F172A; line-height: 1.2; margin: 3px 0 2px 0;">{comp_c} / {tot_c}</div>
        <div style="font-size: 11.5px; color: #64748B;">lessons completed ({pct_c}%)</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(max(0.0, min(1.0, comp_c / tot_c if tot_c > 0 else 0.0)))

with m3:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #8B5CF6; border-radius: 10px; padding: 12px 14px; margin-bottom: 2px;">
        <div style="font-size: 10.5px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase;">📝 ACCURACY</div>
        <div style="font-size: 26px; font-weight: 800; color: #0F172A; line-height: 1.2; margin: 3px 0 2px 0;">{int(active_acc)}%</div>
        <div style="font-size: 11.5px; color: #64748B;">{active_corr} / {active_att} probes correct</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(max(0.0, min(1.0, active_acc / 100 if active_att > 0 else 0.0)))

with m4:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #F59E0B; border-radius: 10px; padding: 12px 14px; margin-bottom: 2px;">
        <div style="font-size: 10.5px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase;">⚡ STUDENT LEVEL</div>
        <div style="font-size: 26px; font-weight: 800; color: #0F172A; line-height: 1.2; margin: 3px 0 2px 0;">{strat_level}</div>
        <div style="font-size: 11.5px; color: #64748B;">Adaptive mode: {strat_code}</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(1.0)

# ==================== Unified Learning Material & Mode Component ====================
pdf_path = None

with st.container(border=True):
    cfg_col1, cfg_col2 = st.columns([1, 1.3])
    with cfg_col1:
        st.markdown("<div style='font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 4px;'>⚙️ Learning Mode</div>", unsafe_allow_html=True)
        mode = st.selectbox(
            "Learning Mode",
            ["General Tutor", "PDF Only", "Hybrid"],
            label_visibility="collapsed"
        )
        st.caption("AI pedagogical grounding source")
        
    with cfg_col2:
        st.markdown("<div style='font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 4px;'>📎 Upload Learning Material</div>", unsafe_allow_html=True)
        upload_choice = st.radio(
            "Upload Material Type",
            ["📄 PDF Document", "🖼️ Educational Image"],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.caption("Choose between PDF notes/slides or an educational diagram")
        
    st.markdown("---")
    
    if upload_choice == "📄 PDF Document":
        uploaded_file = st.file_uploader(
            "Upload PDF Document",
            type=["pdf"],
            label_visibility="collapsed",
            help="Supported: PDF up to 200MB"
        )
        if uploaded_file:
            pdf_path = os.path.join("uploads", uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            if st.button("Process PDF", key="btn_proc_pdf"):
                with st.spinner("Creating knowledge base..."):
                    chunks = process_pdf(pdf_path)
                st.success("PDF processed successfully!")
    else:
        # Educational Image / Visual Learning
        uploaded_image = st.file_uploader(
            "Upload Educational Image",
            type=["png", "jpg", "jpeg", "webp"],
            key="image_uploader",
            label_visibility="collapsed",
            help="Supported: PNG, JPG, JPEG, WEBP"
        )
        if uploaded_image:
            image_id = getattr(uploaded_image, "file_id", uploaded_image.name)
            if st.session_state.learning_session.get("visual_image_id") != image_id:
                st.session_state.learning_session["visual_context"] = None
                st.session_state.learning_session["visual_image_id"] = image_id

            image_bytes = uploaded_image.getvalue()
            st.image(image_bytes, caption=uploaded_image.name, use_container_width=True)

            vis_topic = active_topic
            vis_mastery = active_mastery
            vis_selected_lesson = None
            vis_roadmap = st.session_state.learning_session.get("roadmap_steps", [])
            vis_selected_step = st.session_state.learning_session.get("selected_step")
            vis_current_step = st.session_state.learning_session.get("current_step", 0)

            if vis_selected_step is not None and vis_roadmap and 0 <= vis_selected_step < len(vis_roadmap):
                vis_selected_lesson = vis_roadmap[vis_selected_step]
            elif vis_roadmap and 0 <= vis_current_step < len(vis_roadmap):
                vis_selected_lesson = vis_roadmap[vis_current_step]

            if vis_topic:
                ctx_parts = [f"📌 Topic: **{vis_topic}**"]
                if vis_selected_lesson:
                    ctx_parts.append(f"Lesson: **{vis_selected_lesson}**")
                ctx_parts.append(f"Mastery: **{int(vis_mastery * 100)}%**")
                st.caption(" | ".join(ctx_parts))

            explain_btn = st.button("🔍 Explain Image", key="btn_explain_img")
            if explain_btn:
                available, msg = check_vision_model()
                if not available:
                    st.warning(msg)
                else:
                    with st.spinner("Analyzing image with vision model..."):
                        vis_strategy = None
                        if vis_topic:
                            vis_strategy = get_visual_teaching_style(vis_topic, vis_mastery)

                        analysis, explanation = explain_image(
                            image_bytes,
                            vis_topic,
                            vis_mastery,
                            selected_lesson=vis_selected_lesson,
                            strategy=vis_strategy
                        )
                        analysis["explanation"] = explanation
                        st.session_state.learning_session["visual_context"] = analysis

            visual_ctx = st.session_state.learning_session.get("visual_context")
            if visual_ctx:
                vtype = visual_ctx.get("visual_type", "unknown")
                if vtype and vtype != "unknown":
                    st.caption(f"📐 Image type: {vtype}")
                vis_text = visual_ctx.get("visible_text", [])
                if vis_text:
                    st.write("**📝 Visible Text:**")
                    for t in vis_text:
                        st.write(f"• {t}")
                vis_concepts = visual_ctx.get("educational_concepts", [])
                if vis_concepts:
                    st.write("**📋 Extracted Concepts:**")
                    for c in vis_concepts:
                        st.write(f"• {c}")
                uncertainties = visual_ctx.get("uncertainties", [])
                if uncertainties:
                    st.caption(f"⚠️ Uncertain: {', '.join(str(u) for u in uncertainties)}")
                explanation_text = visual_ctx.get("explanation", "")
                if explanation_text:
                    st.markdown("---")
                    st.markdown("**📖 Explanation:**")
                    st.markdown(explanation_text)
        else:
            if st.session_state.learning_session.get("visual_context"):
                st.session_state.learning_session["visual_context"] = None
            if st.session_state.learning_session.get("visual_image_id"):
                st.session_state.learning_session["visual_image_id"] = None

# ==================== Compact Interactive Tutor Session ====================
st.markdown("<div style='font-size: 15px; font-weight: 700; color: #1E293B; margin-top: 10px; margin-bottom: 6px;'>💬 Interactive Tutor Session</div>", unsafe_allow_html=True)

# ==================== Chat History ====================
history = st.session_state.learning_session["chat_history"]

for chat in history:
    with st.chat_message("user"):
        st.write(chat["question"])
    with st.chat_message("assistant"):
        st.markdown(chat["answer"])

related = st.session_state.learning_session.get("related_topics", [])
if related:
    st.write("### 🔗 Related Concepts")
    for related_topic in related:
        st.write(f"• {related_topic}")

# ==================== Chat Input & Execution ====================
question = st.chat_input("Ask NeuroTutor...")
next_lesson = False

if question:
    text = question.lower()
    if any(x in text for x in [
        "next lesson",
        "next topic",
        "continue",
        "move ahead",
        "go ahead",
        "proceed",
        "next"
    ]):
        next_lesson = True

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.spinner("Thinking..."):
        # 1. GENERAL TUTOR
        if mode == "General Tutor":
            current_topic = st.session_state.learning_session.get("topic")
            state = graph.invoke({
                "question": question,
                "current_topic": current_topic,
                "next_lesson": next_lesson,
                "resumed_session": st.session_state.learning_session.get("resumed_session", False),
                "followup": is_followup(current_topic, question),
                "topic": None,
                "roadmap": [],
                "mastery": 0.0,
                "completed_lessons": [],
                "strategy": {},
                "current_lesson": "",
                "improving": False,
                "struggling": False,
                "accuracy": 0.0,
                "history_text": "",
                "answer": "",
                "chat_history": st.session_state.learning_session["chat_history"],
                "prompt": "",
                "selected_step": st.session_state.learning_session.get("selected_step"),
                "is_relearning": False,
            })
            print(state["question"])
            route = state["route"]

            if route in ["NEXT_LESSON", "FOLLOWUP", "RESUME"]:
                topic = current_topic
            else:
                clear_lesson(st.session_state.learning_session)
                st.session_state.learning_session["concepts"] = []
                st.session_state.learning_session["lesson_turns"] = 0
                st.session_state.learning_session["resumed_session"] = False

                new_topic = state["topic"]
                if new_topic == "NONE":
                    if current_topic is None:
                        with st.chat_message("assistant"):
                            st.markdown("Hello! 👋 What topic would you like to learn today?")
                        st.stop()
                    topic = current_topic
                else:
                    topic = new_topic

                st.session_state.learning_session["topic"] = topic
                roadmap_steps = state["roadmap"]
                if not roadmap_steps:
                    get_mastery(topic)
                    roadmap_steps = get_roadmap(topic)
                    st.session_state.learning_session["roadmap_steps"] = roadmap_steps
                    st.session_state.learning_session["completed_steps"] = get_completed_steps(topic)

                st.session_state.learning_session["roadmap_steps"] = roadmap_steps

            current_step = st.session_state.learning_session["current_step"]
            roadmap_steps = st.session_state.learning_session.get("roadmap_steps", [])

            if next_lesson and roadmap_steps:
                st.session_state.learning_session["selected_step"] = None
                if current_step < len(roadmap_steps):
                    complete_step(topic, current_step)
                if current_step < len(roadmap_steps) - 1:
                    current_step += 1
                    st.session_state.learning_session["current_step"] = current_step

            completed = get_completed_steps(topic)
            concepts = get_concepts(topic)
            answer = state["answer"]

        # 2. PDF ONLY
        elif mode == "PDF Only":
            if not pdf_path:
                answer = "Please upload and process a PDF document first for 'PDF Only' mode."
            else:
                answer = ask_pdf(question, pdf_path)

        # 3. HYBRID
        else:
            if not pdf_path:
                start = time.time()
                response = ollama.chat(
                    model="llama3.2",
                    keep_alive="30m",
                    messages=[{"role": "user", "content": question}]
                )
                print("Tutor2:", time.time() - start)
                answer = response["message"]["content"]
            else:
                pdf_answer = ask_pdf(question, pdf_path)
                if pdf_answer.strip() == "NOT_FOUND":
                    start = time.time()
                    response = ollama.chat(
                        model="llama3.2",
                        keep_alive="30m",
                        messages=[{"role": "user", "content": question}]
                    )
                    print("Tutor2:", time.time() - start)
                    answer = response["message"]["content"]
                else:
                    answer = pdf_answer

    with st.chat_message("assistant"):
        st.markdown(answer)

    if topic:
        save_lesson(st.session_state.learning_session, topic, answer)

    related_topics = get_related_topics(topic)
    st.session_state.learning_session["related_topics"] = related_topics
    st.session_state.learning_session["chat_history"].append({
        "question": question,
        "answer": answer,
        "topic": topic
    })

    st.session_state.learning_session["lesson_turns"] += 1
    st.session_state.learning_session["topic"] = topic
    st.session_state.learning_session["probe_question"] = None

# ==================== Probe / Test Understanding ====================
if (
    st.session_state.learning_session["lesson_turns"] >= 2
    and not st.session_state.learning_session["test_mode"]
):
    if st.button("📝 Test My Understanding"):
        if "topic" not in st.session_state.learning_session:
            st.warning("Please ask a question first.")
            st.stop()

        topic = st.session_state.learning_session["topic"]
        lesson = get_last_lesson(st.session_state.learning_session)
        mastery = get_mastery(topic)
        concepts = get_taught_concepts(lesson.get("lesson", ""))

        if not concepts:
            concepts = ["general_understanding"]

        current_concept = get_weakest_concept(topic, concepts)
        st.session_state.learning_session["concepts"] = concepts or []

        probe_question = generate_probe(
            topic,
            mastery,
            lesson,
            current_concept
        )

        st.session_state.learning_session["test_mode"] = True
        st.session_state.learning_session["probe_question"] = probe_question

if st.session_state.learning_session["probe_question"]:
    st.divider()
    st.subheader("📝 Test My Understanding")
    st.write(st.session_state.learning_session["probe_question"])

    student_answer = st.text_input("Your Answer:", key="student_test_answer")

    if st.button("Submit Answer"):
        result = evaluate_answer(
            st.session_state.learning_session["topic"],
            st.session_state.learning_session["probe_question"],
            student_answer
        )

        concepts = st.session_state.learning_session.get("concepts", [])
        correct = (result == "CORRECT")
        current_concept = get_weakest_concept(topic, concepts)

        add_interaction(
            topic=topic,
            concept=current_concept,
            correct=correct,
            difficulty="medium",
            response_time=0.0
        )

        for concept in concepts:
            update_concept(
                st.session_state.learning_session["topic"],
                concept,
                correct
            )

        mastery = adjust_mastery(
            st.session_state.learning_session["topic"],
            correct
        )

        if correct:
            st.success("✅ Correct!")
        else:
            st.error("❌ Incorrect")
            response_type = classify_response(student_answer)
            style = choose_explanation_style(mastery, response_type)
            prompt = build_explanation_prompt(
                st.session_state.learning_session["topic"],
                st.session_state.learning_session["probe_question"],
                student_answer,
                style
            )
            feedback = ollama.chat(
                model="llama3.2",
                messages=[{"role": "user", "content": prompt}]
            )["message"]["content"]
            st.markdown(feedback)

        st.session_state.learning_session["probe_question"] = None
        st.session_state.learning_session["test_mode"] = False
