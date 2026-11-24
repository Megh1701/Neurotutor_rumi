import ollama
import time


def get_prerequisites(topic):
    

    prompt = f"""
You are an expert professor.

List ONLY the prerequisite concepts needed before studying:

{topic}

Rules:
- Return ONLY prerequisite topic names.
- One topic per line.
- No numbering.
- No explanation.
- No headings.
- Maximum 5 topics.

Example:

Calculus
Linear Algebra
Gradient Descent
Neural Networks
Activation Functions
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
    print("get_prerequisites:", time.time() - start)

    return response["message"]["content"]