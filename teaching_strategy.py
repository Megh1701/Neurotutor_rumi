from knowledge_tracing import (
    is_improving,
    is_struggling,
    get_accuracy
)


def get_teaching_style(topic, mastery):

    accuracy = get_accuracy(topic)

    improving = is_improving(topic)

    struggling = is_struggling(topic)


    # -------------------------------
    # Student is struggling
    # -------------------------------

    if struggling:

        return {

    "level": "Recovery",

    "strategy": "RETEACH",

    "instruction": """
The student has recently struggled.

Repair misconceptions first.

Explain slowly.

Use multiple explanations.

Finish with one short conceptual check.
"""
}


    # -------------------------------
    # Beginner
    # -------------------------------

    if mastery < 0.30 or accuracy < 0.40:

        return {

            "level": "Beginner",

            "strategy": "FOUNDATION",

            "instruction": """
Teach from first principles.

Use simple but mature language.

Avoid childish analogies.

Introduce terminology carefully.

Build intuition first.
"""

        }


    # -------------------------------
    # Intermediate
    # -------------------------------

    if mastery < 0.70 and accuracy >= 0.40:

        return {

            "level": "Intermediate",

            "strategy": "BUILD",

            "instruction": """
Assume basic understanding.

Explain why concepts work.

Connect ideas together.

Use engineering examples.

Mention implementation intuition.
"""

        }


    # -------------------------------
    # Advanced
    # -------------------------------

    if mastery >= 0.70 and improving:

        return {

            "level": "Challenge",

            "strategy": "CHALLENGE",

            "instruction": """
Student is performing well.

Increase technical depth.

Discuss edge cases.

Mention mathematical intuition.

Relate to interview questions.

Encourage critical thinking.
"""

        }


    return {

        "level": "Advanced",

        "strategy": "ADVANCED",

        "instruction": """
Provide concise technical explanations.

Assume fundamentals are known.

Focus on implementation and reasoning.
"""

    }