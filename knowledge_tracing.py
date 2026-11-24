from student_profile import get_profile


INITIAL_MASTERY = 0.20

CORRECT_GAIN = 0.08

WRONG_LOSS = 0.04

MAX_HISTORY = 20


def get_history(topic):

    profile = get_profile()

    if topic not in profile["topics"]:
        return []

    return profile["topics"][topic]["history"]


def get_accuracy(topic):

    history = get_history(topic)

    if not history:
        return 0.0

    return round(sum(history) / len(history), 2)


def get_recent_performance(topic, n=5):

    history = get_history(topic)

    return history[-n:]


def is_improving(topic):

    recent = get_recent_performance(topic)

    if len(recent) < 3:
        return False

    return recent[-3:] == [True, True, True]


def is_struggling(topic):

    recent = get_recent_performance(topic)

    if len(recent) < 3:
        return False

    return recent[-3:] == [False, False, False]


def predict_mastery(topic):
    
    history = get_history(topic)

    if not history:
        return INITIAL_MASTERY

    history = history[-MAX_HISTORY:]

    mastery = INITIAL_MASTERY

    learning_rate = 0.12

    confidence = 0.0

    for result in history:

        if result:

            mastery += learning_rate * (1 - mastery)

            confidence += 0.05

        else:

            mastery -= learning_rate * mastery

            confidence -= 0.03

        mastery = max(0.0, min(1.0, mastery))

    recent = history[-5:]

    if len(recent) == 5:

        accuracy = sum(recent) / 5

        if accuracy >= 0.8:

            mastery += 0.05

        elif accuracy <= 0.2:

            mastery -= 0.05

    mastery += confidence * 0.1

    mastery = max(0.0, min(1.0, mastery))

    return round(mastery, 2)



def should_increase_difficulty(topic):

    return predict_mastery(topic) >= 0.75


def should_decrease_difficulty(topic):

    return predict_mastery(topic) <= 0.35