def initialize_session():
    
    return {

        # Current learning topic
        "topic": None,

        # Conversation history
        "chat_history": [],

        # Related topics
        "related_topics": [],

        # Current lesson
        "lesson": "",

        # Concepts taught
        "concepts": [],

        # Testing
        "probe_question": None,
        "current_concept": None,
        "test_mode": False,

        # Teaching progress
        "lesson_turns": 0,

        # Roadmap
        "roadmap_steps": [],
        "current_step": 0,

        # NEW
        "completed_steps": [],

        "resumed_session": False,

        # Selected lesson for relearning (None = use normal sequential position)
        "selected_step": None,

        # Visual Learning context (None = no image active)
        "visual_context": None,
        "visual_image_id": None,

    }