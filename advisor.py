from prerequisite import get_prerequisites
from student_profile import get_mastery


def recommend_learning_path(topic):

    prerequisites = get_prerequisites(topic)

    # Convert text into a list
    concepts = [
        line.strip()
        for line in prerequisites.split("\n")
        if line.strip()
    ]

    weakest_topic = None
    lowest_mastery = 1.0

    for concept in concepts:

        mastery = get_mastery(concept)

        if mastery < lowest_mastery:

            lowest_mastery = mastery
            weakest_topic = concept

    if weakest_topic is None:

        return {
            "ready": True
        }

    if lowest_mastery >= 0.6:

        return {
            "ready": True
        }

    return {

        "ready": False,

        "recommended_topic": weakest_topic,

        "mastery": lowest_mastery,

        "prerequisites": concepts
    }


def get_revision_plan(topic):
    
    prerequisites = get_prerequisites(topic)

    concepts = [
        line.strip()
        for line in prerequisites.split("\n")
        if line.strip()
    ]

    revision_topics = []

    for prereq in concepts:

        mastery = get_mastery(prereq)

        if mastery < 0.7:

            revision_topics.append(
                {
                    "topic": prereq,
                    "mastery": mastery
                }
            )

    revision_topics.sort(
        key=lambda x: x["mastery"]
    )

    return revision_topics