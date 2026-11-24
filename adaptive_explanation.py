def classify_response(answer):
    
    answer = answer.lower().strip()

    if answer == "":
        return "NO_RESPONSE"

    if "don't know" in answer:
        return "NO_RESPONSE"

    if "dont know" in answer:
        return "NO_RESPONSE"

    if "idk" in answer:
        return "NO_RESPONSE"

    return "ATTEMPT"


def choose_explanation_style(
    mastery,
    response_type
):

    if response_type == "NO_RESPONSE":

        return {
            "style": "BASIC",
            "instruction": (
                "Explain from the very beginning. "
                "Use simple language, analogies, and one easy example."
            )
        }

    if mastery < 0.4:

        return {
            "style": "BEGINNER",
            "instruction": (
                "Explain simply with one worked example. "
                "Avoid technical jargon."
            )
        }

    elif mastery < 0.7:

        return {
            "style": "INTERMEDIATE",
            "instruction": (
                "Give a conceptual explanation with an example "
                "and connect it to related concepts."
            )
        }

    else:

        return {
            "style": "ADVANCED",
            "instruction": (
                "Provide a technical explanation, include intuition, "
                "mathematical details if appropriate, and practical applications."
            )
        }
    

def build_explanation_prompt(
    topic,
    question,
    student_answer,
    style
):

    prompt = f"""
You are NeuroTutor.

Topic:
{topic}

Question:
{question}

Student's Answer:
{student_answer}

Teaching Style:
{style['instruction']}

Your task:

1. Explain why the student's answer is incorrect.
2. Give the correct answer.
3. Explain the concept according to the teaching style.
4. Give one simple example.
5. End with one small follow-up question to check understanding.

Do not make the explanation unnecessarily long.
"""

    return prompt