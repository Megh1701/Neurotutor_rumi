def save_lesson(session, topic, lesson):
    
    previous = session.get(
        "last_lesson",
        {
            "topic": topic,
            "lesson": ""
        }
    )

    if previous["topic"] == topic:

        previous["lesson"] += "\n\n" + lesson

        session["last_lesson"] = previous

    else:

        session["last_lesson"] = {

            "topic": topic,

            "lesson": lesson

        }


def get_last_lesson(session):

    return session.get(
        "last_lesson",
        {
            "topic": "",
            "lesson": ""
        }
    )


def clear_lesson(session):

    session["lesson"] = ""
    session["concepts"] = []