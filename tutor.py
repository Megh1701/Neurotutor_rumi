import ollama
import time


def generate_lesson(topic, question, strategy, mastery):

    prompt = f"""
You are NeuroTutor.

Student Mastery:
{mastery}

Teaching Style:
{strategy}

Topic:
{topic}

Student Question:
{question}

Respond EXACTLY in this format.

===LESSON===

(Write the lesson here.)

===CONCEPTS===

(Write one concept per line.)

Rules:

- Include 3 to 6 concepts.
- ONLY concepts explained in the lesson.
- No numbering.
- No bullets.
- No explanations under concepts.
- Never leave the concepts section empty.
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
    print("generate_lesson:", time.time() - start)

    text = response["message"]["content"]

    if "===CONCEPTS===" in text:

        lesson = text.split("===CONCEPTS===")[0]
        lesson = lesson.replace("===LESSON===", "").strip()

        concept_text = text.split("===CONCEPTS===")[1]

        concepts = [
            c.strip()
            for c in concept_text.split("\n")
            if c.strip()
        ]

    else:

        lesson = text
        concepts = []

    return lesson.strip(), concepts

'''
lesson, concepts = generate_lesson(
    "Python",
    "What is Python?",
    "Explain simply.",
    0.3
)

print(lesson)

print(concepts)
'''