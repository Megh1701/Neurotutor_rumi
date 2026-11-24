from knowledge_tracing import is_improving
from knowledge_tracing import is_struggling

def choose_probe_level(topic, mastery):
    
    if is_struggling(topic):

        return "VERY_EASY"

    elif mastery < 0.4:

        return "EASY"

    elif mastery < 0.7:

        return "MEDIUM"

    elif is_improving(topic):

        return "HARD"

    else:

        return "MEDIUM"
    

def build_probe_prompt(topic, level):
    
    return f"""
You are an expert teacher.

Topic:
{topic}

Difficulty Level:
{level}

Generate ONE short assessment question.

Rules:

VERY_EASY
- Ask a simple definition question.
- Test basic recall only.

EASY
- Ask a straightforward conceptual question.

MEDIUM
- Ask a conceptual understanding question.
- Student should explain why.

HARD
- Ask an application-based question.
- Require reasoning.

Return ONLY the question.
"""