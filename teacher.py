import ollama
import time
from teaching_strategy import get_teaching_style


def explain_topic(
    topic,
    mastery
):

    style = get_teaching_style(topic, mastery)

    prompt = f"""
You are an excellent professor.

Topic:
{topic}

Teaching Strategy:

{style["strategy"]}

Teaching Instructions:

{style["instruction"]}

Teach the concept clearly.
"""
    start=time.time()
    response = ollama.chat(

        model="llama3.2",

        keep_alive="30m",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    print("explain_topic:", time.time() - start)

    return response["message"]["content"]