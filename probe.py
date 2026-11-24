import ollama
import time
from difficulty import get_question_difficulty
from probe_cache import PROBE_CACHE, EVALUATION_CACHE

def generate_probe(topic, mastery, lesson, concept):

    difficulty = get_question_difficulty(mastery)

    key = (topic, concept, difficulty)

    if key in PROBE_CACHE:
        return PROBE_CACHE[key]
    

    if mastery < 0.4:

        level = "easy"

    elif mastery < 0.7:

        level = "medium"

    else:

        level = "hard"


    prompt = f"""
You are NeuroTutor.

You have just finished teaching a student.

Below is the COMPLETE lesson that the student learned.

=========================
{lesson}
=========================

The concept to assess is:

{concept}

Generate the question ONLY about this concept.

Do NOT ask about any other concept mentioned in the lesson.

Student Mastery:
{mastery}

Question Difficulty:
{difficulty}

Your task is to generate ONE assessment question.

STRICT RULES:

1. The question MUST test ONLY information that appears in the lesson above.

2. If a fact is NOT explicitly written in the lesson,
DO NOT ask about it.

3. Do NOT use your own knowledge of {topic}.

4. Imagine the student has ONLY read the lesson above.

5. The question MUST assess ONLY the specified concept above.

6. Ignore every other concept in the lesson.

7. Never introduce new APIs, functions, keywords, libraries, versions, or advanced concepts that were not taught.

Difficulty Rules:

EASY
- definition
- recall
- identify

MEDIUM
- simple application using the lesson

HARD
- reasoning using ONLY the lesson

Return ONLY the question.
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
    print("generate_probe:", time.time() - start)

    probe = response["message"]["content"]
    PROBE_CACHE[key] = probe
    return probe



def evaluate_answer(
    topic,
    question,
    student_answer
):
    
    key = (topic, question, student_answer)

    if key in EVALUATION_CACHE:
        return EVALUATION_CACHE[key]

    prompt = f"""
You are an expert tutor.

Topic:
{topic}

Question:
{question}

Student Answer:
{student_answer}

Evaluate the answer.

Respond with ONLY one word:

CORRECT

or

INCORRECT
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
    print("evaluate_answer:", time.time() - start)

    result = response["message"]["content"].strip()

    EVALUATION_CACHE[key] = result

    return result

def explain_mistake(
    topic,
    question,
    student_answer
):
    prompt = f"""
You are NeuroTutor, an adaptive AI tutor.

Topic:
{topic}

Question:
{question}

Student Answer:
{student_answer}

The student's answer is INCORRECT.

Your task is NOT just to mark it wrong.

Teach the student.

Respond EXACTLY in this format:

## ❌ Why Your Answer is Incorrect
Explain what misconception the student has.

## ✅ Correct Answer
State the correct answer clearly.

## 📘 Detailed Explanation
Explain the concept thoroughly.
Use simple language.
Avoid repeating the same information.

## 💡 Example
Give one practical real-world example.

## 🧠 Tip to Remember
Give one short trick or memory tip that helps avoid this mistake in the future.

Keep the explanation educational and well-structured.
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
    print("explain_mistake:", time.time() - start)

    return response["message"]["content"]
