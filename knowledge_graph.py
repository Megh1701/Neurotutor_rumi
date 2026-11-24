import json
import os
import ollama


GRAPH_FILE = "memory/knowledge_graph.json"



def load_graph():

    if not os.path.exists(GRAPH_FILE):
        return {}

    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_graph(graph):

    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=4)


GRAPH = load_graph()


def build_graph(topic):
    
    if topic in GRAPH:
        return

    prompt = f"""
You are building an educational knowledge graph.

Topic:
{topic}

Return ONLY valid JSON.

Format:

{{
    "topic":"",

    "prerequisites":[
        ""
    ],

    "concepts":[
        ""
    ],

    "related":[
        ""
    ],

    "difficulty":1,

    "estimated_lessons":6
}}

Rules:

- Return ONLY JSON.
- No markdown.
- No explanations.
- Concepts should be ordered from easiest to hardest.
- Prerequisites must contain ONLY direct prerequisites.
- Related should contain closely related academic topics.
- difficulty is an integer from 1 to 5.
- estimated_lessons is the number of lessons required to learn the topic.
"""

    response = ollama.chat(
        model="llama3.2",
        keep_alive="30m",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )["message"]["content"]

    import json

    try:

        GRAPH[topic]=json.loads(response)
        save_graph(GRAPH)

    except:

        GRAPH[topic]={
            "topic":topic,
            "prerequisites":[],
            "concepts":[],
            "related":[],
            "difficulty": 3,
            "estimated_lessons": 6
        }
        save_graph(GRAPH)

def get_topic_graph(topic):
    
    if topic not in GRAPH:
        build_graph(topic)

    return GRAPH[topic]


def get_prerequisites(topic):
    

    return get_topic_graph(topic).get(
        "prerequisites",
        []
    )

def get_related_topics(topic):

    return get_topic_graph(topic).get(
        "related",
        []
    )


def get_learning_path(topic):
    

    graph = get_topic_graph(topic)

    concepts = graph.get("concepts", [])

    prerequisites = graph.get("prerequisites", [])

    return prerequisites + concepts



def graph_exists(topic):
    
    return topic in GRAPH


def get_concepts(topic):
    

    build_graph(topic)

    return GRAPH[topic]["concepts"]


def concept_exists(topic, concept):

    build_graph(topic)

    return concept in GRAPH[topic]["concepts"]


def next_concept(topic, completed):

    build_graph(topic)

    for concept in GRAPH[topic]["concepts"]:

        if concept not in completed:

            return concept

    return None


def get_difficulty(topic):
    
    graph = get_topic_graph(topic)

    return graph.get("difficulty", 3)


def get_estimated_lessons(topic):

    graph = get_topic_graph(topic)

    return graph.get("estimated_lessons", 6)