import ollama
import time


def is_followup(previous_topic, question):

    if previous_topic is None:
        return False

    prompt = f"""
Previous Topic:
{previous_topic}

New Student Message:
{question}

Is the student continuing the SAME discussion?

Answer ONLY:

YES

or

NO
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
    print("is_followup:", time.time() - start)

    return response["message"]["content"].strip() == "YES"