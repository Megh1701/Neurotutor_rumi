import json
import os
from lesson_planner import create_lesson_plan
from lesson_planner import roadmap_to_list
from dkt.infer import predict_mastery_dkt



PROFILE_FILE = "memory/student_profile.json"
PROFILE = None


def load_profile():

    global PROFILE

    if PROFILE is not None:
        return PROFILE

    if not os.path.exists(PROFILE_FILE):
        PROFILE = {"topics": {}}
        return PROFILE

    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        PROFILE = json.load(f)

    return PROFILE

def save_profile(profile):
    
    global PROFILE

    PROFILE = profile

    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4)


def get_profile():

    return load_profile()


def initialize_topic(topic):
    
    profile = load_profile()

    if topic in profile["topics"]:
        return

    roadmap = roadmap_to_list(

        create_lesson_plan(
            topic,
            0.2
        )

    )

    concepts = {}

    for concept in roadmap:

        concepts[concept] = {

            "mastery": 0.2,

            "history": [],

            "completed": False

        }

    profile["topics"][topic] = {

        "mastery": 0.2,

        "history": [],

        "interactions": [],

        "roadmap": roadmap,

        "completed_steps": [],

        "concepts": concepts

    }

    save_profile(profile)



def get_mastery(topic):

    initialize_topic(topic)

    profile = load_profile()

    return profile["topics"][topic]["mastery"]


def update_topic(
    topic,
    mastery,
    roadmap=None
):

    profile = load_profile()

    if topic not in profile["topics"]:

        profile["topics"][topic] = {
            "mastery": mastery,
            "history": [],
            "interactions": [],
            "concepts": {},
            "roadmap": [],
            "completed_steps": []
        }

    profile["topics"][topic]["mastery"] = mastery

    if roadmap is not None:

        profile["topics"][topic]["roadmap"] = roadmap

    save_profile(profile)


def add_attempt(topic, correct):

    initialize_topic(topic)

    profile = load_profile()

    profile["topics"][topic]["history"].append(correct)

    save_profile(profile)

def add_interaction(
    topic,
    concept,
    correct,
    difficulty,
    response_time
):
    initialize_topic(topic)

    profile = load_profile()

    interaction = {

        "concept": concept,

        "correct": correct,

        "difficulty": difficulty,

        "response_time": response_time

    }

    profile["topics"][topic]["interactions"].append(interaction)

    save_profile(profile)



def adjust_mastery(topic, correct):
    """
    Update mastery based on student's answer.
    Uses a blend of simple moving average (for immediate feedback)
    and DKT prediction (for long-term pattern recognition).
    """
    # Ensure topic exists
    initialize_topic(topic)
    
    # Load profile
    profile = load_profile()
    
    # Add to history
    profile["topics"][topic]["history"].append(correct)
    
    # Calculate mastery from recent history (simple moving average)
    history = profile["topics"][topic]["history"]
    recent = history[-8:]  # Last 8 attempts for more stability
    simple_mastery = sum(recent) / len(recent) if recent else 0.2
    
    # Get DKT prediction for blending
    dkt_mastery = predict_mastery_dkt(topic)
    
    # Blend: 50% simple moving average, 50% DKT
    mastery = 0.5 * simple_mastery + 0.5 * dkt_mastery
    
    # Ensure mastery stays within bounds
    mastery = max(0.0, min(1.0, mastery))
    mastery = round(mastery, 2)
    
    # Update the profile
    profile["topics"][topic]["mastery"] = mastery
    save_profile(profile)
    
    return mastery



def update_concept(topic, concept, correct):
    
    initialize_topic(topic)

    profile = load_profile()

    concepts = profile["topics"][topic]["concepts"]

    if concept not in concepts:
        return

    if correct:
        concepts[concept]["mastery"] += 0.1
    else:
        concepts[concept]["mastery"] -= 0.05

    concepts[concept]["mastery"] = max(
        0.0,
        min(1.0, concepts[concept]["mastery"])
    )

    concepts[concept]["history"].append(correct)

    if concepts[concept]["mastery"] >= 0.8:
        concepts[concept]["completed"] = True

    save_profile(profile)


def get_concepts(topic):

    initialize_topic(topic)

    profile = load_profile()

    return profile["topics"][topic]["concepts"]


def get_all_topics():

    profile = load_profile()

    return profile["topics"]


def get_weakest_concept(topic, lesson_concepts):
    
    profile = load_profile()

    if topic not in profile["topics"]:
        return None

    concepts = profile["topics"][topic].get(
        "concepts",
        {}
    )

    weakest = None
    lowest = 2.0

    for concept in lesson_concepts:

        if concept in concepts:

            score = concepts[concept]["mastery"]

        else:

            score = 0.2

        if score < lowest:

            lowest = score
            weakest = concept

    return weakest


def get_completed_steps(topic):

    initialize_topic(topic)

    concepts = get_concepts(topic)

    completed = []

    roadmap = load_profile()["topics"][topic]["roadmap"]

    for i, concept in enumerate(roadmap):

        if concepts[concept]["completed"]:

            completed.append(i)

    return completed

def save_roadmap(topic, roadmap):
    
    profile = load_profile()

    if topic not in profile["topics"]:

        profile["topics"][topic] = {
            "mastery": 0.2,
            "history": [],
            "interactions": [],
            "concepts": {},
            "roadmap": [],
            "completed_steps": []
        }

    profile["topics"][topic]["roadmap"] = roadmap

    save_profile(profile)


def get_roadmap(topic):

    profile = load_profile()

    if topic not in profile["topics"]:

        return []

    return profile["topics"][topic].get(
        "roadmap",
        []
    )


def complete_step(topic, step):

    profile = load_profile()

    if topic not in profile["topics"]:

        return

    completed = profile["topics"][topic].setdefault(
        "completed_steps",
        []
    )

    if step not in completed:

        completed.append(step)

    save_profile(profile)


def get_completed_steps(topic):

    profile = load_profile()

    if topic not in profile["topics"]:

        return []

    return profile["topics"][topic].get(
        "completed_steps",
        [])