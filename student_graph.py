from student_profile import get_all_topics
from knowledge_graph import get_prerequisites
from knowledge_graph import get_related_topics


def build_student_graph():

    profile = get_all_topics()

    graph = {}

    for topic, data in profile.items():

        concepts = data.get("concepts", {})

        weak = []
        medium = []
        strong = []

        for concept, info in concepts.items():

            mastery = info.get("mastery", 0.2)

            if mastery < 0.4:
                weak.append(concept)

            elif mastery < 0.75:
                medium.append(concept)

            else:
                strong.append(concept)

        graph[topic] = {

            "mastery": data.get("mastery", 0.2),

            "weak_concepts": weak,

            "medium_concepts": medium,

            "strong_concepts": strong,

            "prerequisites": get_prerequisites(topic),

            "related": get_related_topics(topic)

        }

    return graph


def get_weak_topics(threshold=0.5):

    graph = build_student_graph()

    weak_topics = []

    for topic, data in graph.items():

        if data["mastery"] < threshold:

            weak_topics.append(topic)

    return weak_topics


def get_strong_topics(threshold=0.8):

    graph = build_student_graph()

    strong_topics = []

    for topic, data in graph.items():

        if data["mastery"] >= threshold:

            strong_topics.append(topic)

    return strong_topics


def get_topic_state(topic):

    graph = build_student_graph()

    return graph.get(topic)


def get_next_revision_topics():

    graph = build_student_graph()

    revision = []

    for topic, data in graph.items():

        if len(data["weak_concepts"]) > 0:

            revision.append(topic)

    return revision