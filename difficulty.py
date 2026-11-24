def get_question_difficulty(mastery):
    
    if mastery < 0.3:

        return "EASY"

    elif mastery < 0.7:

        return "MEDIUM"

    else:

        return "HARD"