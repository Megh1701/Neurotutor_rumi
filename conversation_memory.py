def initialize_topic_memory():
    
    return {

        "main_topic": None,

        "concepts": [],

        "last_explanation": ""

    }


def set_main_topic(memory, topic):
    
    memory["main_topic"] = topic


def add_concept(memory, concept):
    
    if concept not in memory["concepts"]:

        memory["concepts"].append(concept)


def set_explanation(memory, explanation):
    
    memory["last_explanation"] = explanation


def get_main_topic(memory):

    return memory["main_topic"]


def get_concepts(memory):

    return memory["concepts"]


def get_last_explanation(memory):
    
    return memory["last_explanation"]


