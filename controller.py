from routes import *

def decide_route(

    question,

    current_topic,

    next_lesson,

    resumed_session,

    is_followup

):
    """
    Central routing logic.
    """

    if resumed_session:

        return route_resume

    if next_lesson:

        return route_next_lesson

    if current_topic is None:

        return route_new_topic

    if is_followup:

        return route_followup

    return route_new_topic