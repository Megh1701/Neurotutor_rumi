import ollama
import time


def create_lesson_plan(topic, mastery):

    prompt = f"""
You are creating a teaching roadmap.

IMPORTANT:

Generate the roadmap ONLY for this topic:

{topic}

Ignore any previous conversation.

Do NOT create a roadmap for related subjects.

Do NOT expand into prerequisite or advanced fields.

Student mastery:
{mastery}

Rules:

- Produce ONLY a roadmap for "{topic}".
- Break it into 5-8 ordered learning steps.
- Each step teaches ONE concept.
- Stay inside the topic.
- Do not mention any other subject.
- Return ONLY a numbered list.

Example:

1. Definition
2. Purpose
3. Basic concepts
4. Simple examples
5. Common mistakes
6. Advanced usage
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

    return response["message"]["content"]

    print("create_lesson_plan:", time.time() - start)

def roadmap_to_list(roadmap):
    
    steps = []

    for line in roadmap.split("\n"):

        line = line.strip()

        if not line:
            continue

        if line[0].isdigit():

            parts = line.split(".", 1)

            if len(parts) == 2:

                steps.append(parts[1].strip())

    return steps