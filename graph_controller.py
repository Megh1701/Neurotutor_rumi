import time

from typing import TypedDict

from langgraph.graph import StateGraph, END

from routes import *

from topic import extract_topic

from student_profile import get_roadmap

from student_profile import get_mastery

from student_profile import get_completed_steps

from teaching_strategy import get_teaching_style

from knowledge_tracing import is_improving
from knowledge_tracing import is_struggling
from knowledge_tracing import get_accuracy

import ollama

from lesson_memory import save_lesson



class TutorState(TypedDict):

    question: str

    current_topic: str

    next_lesson: bool

    resumed_session: bool

    followup: bool

    route: str

    topic: str

    roadmap: list

    mastery: float

    completed_lessons: list

    strategy: dict

    current_lesson: str

    improving: bool

    struggling: bool

    accuracy: float

    history_text: str

    answer: str

    chat_history: list

    prompt: str

    roadmap_steps: list

    teaching_strategy: dict

    selected_step: int

    is_relearning: bool


# ---------------- Nodes ----------------

def controller_node(state: TutorState):

    # When a student has selected a lesson for relearning,
    # treat it as a followup (keep topic) unless explicitly asking for next lesson
    has_selected_lesson = state.get("selected_step") is not None

    if state["resumed_session"]:

        state["route"] = route_resume()

    elif state["next_lesson"]:

        state["route"] = route_next_lesson()

    elif state["current_topic"] is None:

        state["route"] = route_new_topic()

    elif has_selected_lesson:

        # Student is relearning — force FOLLOWUP route to prevent
        # the topic extractor from interpreting the question as a new topic
        state["route"] = route_followup()

        print(f"[CONTROLLER] Forced FOLLOWUP route: selected_step={state.get('selected_step')}")

    elif state["followup"]:

        state["route"] = route_followup()

    else:

        state["route"] = route_new_topic()

    return state


def topic_node(state: TutorState):
    
    if state["route"] == "NEW_TOPIC":

        state["topic"] = extract_topic(
            state["question"]
        )

    else:

        state["topic"] = state["current_topic"]

    return state



def roadmap_node(state: TutorState):
    
    state["roadmap"] = get_roadmap(
        state["topic"]
    )

    return state





def profile_node(state: TutorState):
    
    topic = state["topic"]

    roadmap = state["roadmap"]

    mastery = get_mastery(topic)

    completed = get_completed_steps(topic)

    state["mastery"] = mastery

    state["completed_lessons"] = completed

    state["strategy"] = get_teaching_style(
        topic,
        mastery
    )

    # Determine the normal sequential position
    if completed:

        sequential_current = min(
            max(completed) + 1,
            len(roadmap) - 1
        )

    else:

        sequential_current = 0

    # Check if student has selected a previous lesson for relearning
    selected = state.get("selected_step")

    if selected is not None and roadmap and 0 <= selected < len(roadmap):

        state["current_lesson"] = roadmap[selected]
        state["is_relearning"] = True

        print(f"[PROFILE] RELEARNING: selected_step={selected}, "
              f"current_lesson={roadmap[selected]}, "
              f"sequential_position={sequential_current}")

    elif roadmap:

        state["current_lesson"] = roadmap[sequential_current]
        state["is_relearning"] = False

        print(f"[PROFILE] NORMAL: sequential_position={sequential_current}, "
              f"current_lesson={roadmap[sequential_current]}")

    else:

        state["current_lesson"] = topic
        state["is_relearning"] = False

    return state


def tracing_node(state: TutorState):
    
    topic = state["topic"]

    state["improving"] = is_improving(topic)

    state["struggling"] = is_struggling(topic)

    state["accuracy"] = get_accuracy(topic)

    return state


def tutor_node(state: TutorState):
    
    history = ""

    for chat in state["chat_history"][-6:]:

        history += f"""
    Student:
    {chat["question"]}

    Tutor:
    {chat["answer"]}
    """

    state["history_text"] = history

    return state


def prompt_builder_node(state):

    is_relearning = state.get("is_relearning", False)

    if is_relearning:

        relearning_instruction = f"""
                    RELEARNING MODE:

                    The student has selected a previously completed lesson for relearning.

                    Selected lesson for relearning:
                    {state["current_lesson"]}

                    You MUST answer the student's question in the context of this selected lesson: {state["current_lesson"]}

                    Do NOT switch to another roadmap lesson.

                    Do NOT teach a different lesson.

                    Do NOT infer a new topic from the student's question if the question is a follow-up such as:
                    "Explain this again."
                    "Explain this lesson."
                    "Tell me more."
                    "Give another example."
                    "What does this mean?"
                    "I still don't understand this."
                    "Explain it with an example."
                    "Give me a more detailed explanation."

                    Treat "this", "this lesson", "it", "again", and similar follow-up references as referring to the selected lesson: {state["current_lesson"]}

                    The student already completed this lesson before but wants to review it.
                    Explain it thoroughly as if teaching it fresh.
"""

        lesson_instruction = f"""
                    Teach the selected lesson: {state["current_lesson"]}
                    This is a relearning/review session for a previously completed lesson.
                    Explain this lesson thoroughly.
"""

    else:

        relearning_instruction = ""

        lesson_instruction = """
                    The student is CONTINUING this course.

                    Never restart the topic.

                    Never explain previous completed lessons.

                    Assume the student already understands every completed lesson.

                    Teach ONLY the current lesson.

                    If the student asks a general question, answer it ONLY in the context of the current lesson.

                    Continue naturally from where the student stopped.
"""

    state["prompt"] = f"""
                    You are NeuroTutor, an expert adaptive AI tutor.
    
                    Student Mastery:
                    {state["mastery"]}
    
                    Teaching Style:
                    {state["strategy"]["instruction"]}
    
                    Previous conversation:
                    {state["history_text"]}
    
                    Current course:
                    {state["topic"]}
    
                    Roadmap: 
                    {state["roadmap"]}
    
                    Current lesson:  
                    {state["current_lesson"]}
    
                    Completed lessons:
                    {state["completed_lessons"]}
    
                    {relearning_instruction}

                    IMPORTANT:
    
                    {lesson_instruction}

                    Never begin with introductions like
                    "Let's begin",
                    "Welcome",
                    "Machine Learning is..."
    
                    Student's question:
    
                    {state["question"]}
    
                    Instructions:
    
                    - Focus on the current lesson: {state["current_lesson"]}
                    - Never restart the topic.
                    - Assume the student is a university Computer Engineering student.
                    - Maintain an academic and professional tone.
                    - Explain concepts clearly without oversimplifying.
                    - Prefer technical intuition over childish analogies.
                    - Use proper terminology, then explain it in simple words.
                    - Build explanations from fundamentals to intuition.
                    - Use examples from Computer Science, AI, mathematics or real engineering systems.
                    - Avoid stories involving children, sandwiches, toys, animals or cartoons.
                    - Only use analogies when they genuinely improve understanding.
                    - If the student asks for more detail, increase the technical depth instead of changing the analogy.
                    - End naturally after answering the student's question.
    
                    Your goal is to teach like an excellent university professor who explains difficult concepts clearly.
    
                    """

    print(f"[PROMPT] topic={state['topic']}, "
          f"current_lesson={state['current_lesson']}, "
          f"is_relearning={is_relearning}")


    
    return state

def answer_node(state: TutorState):

    start=time.time()

    response = ollama.chat(

        model="llama3.2",

        keep_alive="30m",

        messages=[
            {
                "role": "user",
                "content": state["prompt"]
            }
        ]
    )

    print("Tutor1:", time.time() - start)

    state["answer"] = response["message"]["content"]

    return state


# ---------------- Graph ----------------

builder = StateGraph(TutorState)

builder.add_node(
    "controller",
    controller_node
)

builder.add_node(
    "topic",
    topic_node
)

builder.add_node(
    "roadmap",
    roadmap_node
)


builder.add_node(
    "profile",
    profile_node
)

builder.add_node(
    "tracing",
    tracing_node
)

builder.add_node(
    "tutor",
    tutor_node
)

builder.add_node(
    "prompt_builder",
    prompt_builder_node
)

builder.add_node(
    "answer",
    answer_node
)

builder.set_entry_point("controller")

builder.add_edge(
    "controller",
    "topic"
)

builder.add_edge(
    "topic",
    "roadmap"
)

builder.add_edge(
    "roadmap",
    "profile"
)


builder.add_edge(
    "profile",
    "tracing"
)

builder.add_edge(
    "tracing",
    "tutor"
)

builder.add_edge(
    "tutor",
    "prompt_builder"
)

builder.add_edge(
    "prompt_builder",
    "answer"
)

builder.add_edge(
    "answer",
    END
)


graph = builder.compile()