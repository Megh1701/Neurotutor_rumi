import ollama
import time
from topic_cache import TOPIC_CACHE, FOLLOWUP_CACHE


FOLLOWUP_MESSAGES = {

    "continue",
    "continue lesson",
    "continue learning",
    "resume",
    "resume lesson",
    "next",
    "next lesson",
    "go ahead",
    "proceed",
    "lets start",
    "let's start",
    "start",
    "teach",
    "teach me",
    "explain more",
    "more",
    "more detail",
    "in detail",
    "can you elaborate",
    "another example",
    "why",
    "how",
    "example"

}


def extract_topic(question):

    if question in TOPIC_CACHE:
        return TOPIC_CACHE[question]
    
    
    prompt = f"""
You are an AI tutor.

Your task is to identify the MOST SPECIFIC learning concept
while preserving its academic context.

Rules:

- Return ONLY the academic topic.
- Keep it short.
- Do NOT explain.
- Do NOT add greetings.
- Do NOT add punctuation.
- If the message is NOT asking about a topic,
  return ONLY

NONE

Examples:

Question:
What is kernel in SVM?
Topic:
Kernel Function in Support Vector Machines

Question:
Explain kernel in operating systems.
Topic:
Operating System Kernel

Question:
Explain CNNs.
Topic:
Convolutional Neural Networks

Question:
What is Gradient Descent?
Topic:
Gradient Descent

Question:
Explain activation function.
Topic:
Activation Function in Neural Networks

Question:
What is recursion?
Topic:
Recursion in Programming

Now identify the topic.

Question:
hello

Topic:
NONE

Question:
thanks

Topic:
NONE

Question:
lets start

Topic:
NONE

Question:
continue

Topic:
NONE

Question:
{question}

Return ONLY the topic.
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
    print("extract_topic:", time.time() - start)

    topic = response["message"]["content"].strip()

    TOPIC_CACHE[question] = topic

    return topic


def is_followup(previous_topic, question):

    key = (previous_topic, question)

    if key in FOLLOWUP_CACHE:
        return FOLLOWUP_CACHE[key]
    
    if previous_topic is None:
        return False
    
    text = question.lower().strip()

    if text in FOLLOWUP_MESSAGES:
        return True

    prompt = f"""
You are deciding whether a student's new message is a FOLLOW-UP to an existing lesson.

Current lesson topic:
{previous_topic}

Student message:
{question}

A FOLLOW-UP includes messages like:

- tell me more
- explain more
- continue
- why?
- how?
- example?
- another example
- explain in detail
- can you elaborate
- what next
- continue this topic
- explain this part
- i didn't understand
- why is that

Return YES if the student is continuing the same lesson, even if the message does not mention the topic name.

Return NO only if the student clearly starts learning a different topic.

Reply with ONLY one word:

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

    result = response["message"]["content"].strip().upper() == "YES"

    FOLLOWUP_CACHE[key] = result

    return result