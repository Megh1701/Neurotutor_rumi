import ollama
import time


def get_taught_concepts(lesson):

    if not lesson.strip():
        return []

    prompt = f"""
You are an educational assistant.

Lesson:
{lesson}

Extract ONLY the important concepts that were explicitly taught.

Rules:
- Return between 2 and 5 concepts.
- One concept per line.
- No numbering.
- No explanations.
- Do NOT invent concepts.
"""

    start = time.time()
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
    print("get_taught_concepts:", time.time() - start)

    concepts = []

    for line in response["message"]["content"].split("\n"):

        line = line.strip("- ").strip()

        if line:

            concepts.append(line)

    return concepts