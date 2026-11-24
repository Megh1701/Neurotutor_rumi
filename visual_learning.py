"""
NeuroTutor Visual Learning Module

Uses a two-model pipeline:
  1. moondream (vision) — describes what is actually visible in the image
  2. llama3.2 (text) — structures the description, generates explanations and questions

Design principles:
  - moondream receives SIMPLE, DIRECT prompts (it is a small model)
  - Structured analysis is done by llama3.2 from moondream's plain-text output
  - All outputs must be grounded in what the vision model actually reported
  - No invented components, text, or relationships
"""

import ollama
import json
import time
import base64

from config import VISION_MODEL, TEXT_MODEL


# ==================== Vision Model Utilities ====================

def _image_to_base64(image_bytes):
    """Convert raw image bytes to base64 string for Ollama."""
    return base64.b64encode(image_bytes).decode("utf-8")


def _vision_query(image_bytes, prompt):
    """
    Send a simple query to the vision model with an image.
    Returns the raw text response.
    
    moondream works best with short, direct questions.
    Do NOT ask it for JSON or complex structured output.
    """
    image_b64 = _image_to_base64(image_bytes)

    start = time.time()

    try:
        response = ollama.chat(
            model=VISION_MODEL,
            keep_alive="30m",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64]
                }
            ]
        )

        elapsed = time.time() - start
        result = response["message"]["content"].strip()
        print(f"[VISION] query ({elapsed:.1f}s): {prompt[:60]}...")
        print(f"[VISION] response: {result[:200]}...")

        return result

    except Exception as e:
        print(f"[VISION] error: {e}")
        return ""


def _text_query(prompt, use_json=False):
    """
    Send a text-only query to the text model (llama3.2).
    Optionally request JSON format.
    """
    start = time.time()

    try:
        kwargs = {
            "model": TEXT_MODEL,
            "keep_alive": "30m",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        if use_json:
            kwargs["format"] = "json"

        response = ollama.chat(**kwargs)

        elapsed = time.time() - start
        result = response["message"]["content"].strip()
        print(f"[TEXT] query ({elapsed:.1f}s), json={use_json}")

        return result

    except Exception as e:
        print(f"[TEXT] error: {e}")
        return ""


# ==================== Image Analysis ====================

def analyze_image(image_bytes, context=None):
    """
    Analyze an educational image using multiple focused vision queries,
    then structure the results using the text model.

    Returns a dict:
        visual_type, description, visible_text, components,
        layout, relationships, educational_concepts, uncertainties
    """

    # --- Step 1: Get a plain description from moondream ---
    description = _vision_query(
        image_bytes,
        "Describe this image in detail. What do you see?"
    )

    if not description:
        return _empty_analysis("Vision model returned no response.")

    # --- Step 2: Ask moondream about visible text ---
    visible_text = _vision_query(
        image_bytes,
        "List all readable text, labels, headings, numbers and words visible in this image. If there is no readable text, say 'No readable text'."
    )

    # --- Step 3: Ask moondream about structure/layout ---
    structure = _vision_query(
        image_bytes,
        "What is the layout of this image? Describe the arrangement: are there boxes, arrows, rows, columns, a graph, a list, a table, a photograph, or something else?"
    )

    # --- Step 4: Use llama3.2 to create structured analysis ---
    # This is where we produce the JSON — using the TEXT model, not the vision model.
    structuring_prompt = f"""You are analyzing an educational image based on a vision model's observations.

VISION MODEL OBSERVATIONS:

Description:
{description}

Visible text and labels:
{visible_text}

Layout and structure:
{structure}

Based ONLY on these observations, produce a structured JSON analysis.

STRICT RULES:
- Only include information that the vision model actually reported.
- Do NOT invent text, labels, components, arrows, or relationships.
- If a field has no information, use an empty list [] or empty string "".
- Do NOT guess or assume.
- Do NOT add example values.
- visual_type must be one of: diagram, flowchart, table, chart, graph, list, equation, code, photograph, illustration, infographic, mixed, unknown

Return ONLY valid JSON:

{{
    "visual_type": "",
    "description": "",
    "visible_text": [],
    "components": [],
    "layout": "",
    "relationships": [],
    "educational_concepts": [],
    "uncertainties": []
}}
"""

    raw_json = _text_query(structuring_prompt, use_json=True)

    analysis = _parse_json_safe(raw_json)

    # Ensure required fields exist
    analysis.setdefault("visual_type", "unknown")
    analysis.setdefault("description", description)
    analysis.setdefault("visible_text", [])
    analysis.setdefault("components", [])
    analysis.setdefault("layout", "")
    analysis.setdefault("relationships", [])
    analysis.setdefault("educational_concepts", [])
    analysis.setdefault("uncertainties", [])

    # Store raw vision outputs for transparency
    analysis["_raw_description"] = description
    analysis["_raw_visible_text"] = visible_text
    analysis["_raw_structure"] = structure

    print(f"[ANALYSIS] type={analysis['visual_type']}, "
          f"concepts={len(analysis['educational_concepts'])}, "
          f"components={len(analysis['components'])}")

    return analysis


def _empty_analysis(error_msg):
    """Return an empty analysis dict with an error."""
    return {
        "visual_type": "unknown",
        "description": "",
        "visible_text": [],
        "components": [],
        "layout": "",
        "relationships": [],
        "educational_concepts": [],
        "uncertainties": [error_msg],
        "error": error_msg
    }


def _parse_json_safe(raw):
    """
    Safely parse JSON from a model response.
    Handles malformed output, markdown code blocks, and partial JSON.
    """
    if not raw:
        return {}

    # Try direct parse
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting from markdown code block
    if "```" in raw:
        for block in raw.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            if block.startswith("{"):
                try:
                    return json.loads(block)
                except (json.JSONDecodeError, ValueError):
                    pass

    # Try finding first { ... } substring
    start_idx = raw.find("{")
    end_idx = raw.rfind("}")

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(raw[start_idx:end_idx + 1])
        except (json.JSONDecodeError, ValueError):
            pass

    # Complete fallback
    return {"description": raw}


# ==================== Concept Extraction ====================

def extract_visual_concepts(image_bytes, context=None):
    """
    Extract educational concepts from an image.
    Returns a list of concept strings.
    """
    analysis = analyze_image(image_bytes, context)
    return analysis.get("educational_concepts", [])


# ==================== Image Explanation ====================

def explain_image(image_bytes, topic, mastery, selected_lesson=None, strategy=None):
    """
    Generate an adaptive educational explanation of an image.

    Pipeline:
      1. analyze_image() → grounded structured analysis
      2. Build explanation prompt using analysis + learning context
      3. llama3.2 generates mastery-adaptive explanation

    Returns: (analysis_dict, explanation_text)
    """

    context = {
        "topic": topic or "General",
        "current_lesson": selected_lesson or topic or "General"
    }

    # Step 1: Grounded analysis
    analysis = analyze_image(image_bytes, context)

    if analysis.get("error"):
        return analysis, f"⚠️ Could not analyze the image: {analysis['error']}"

    # Step 2: Build explanation prompt
    explanation = _generate_explanation(analysis, topic, mastery, selected_lesson, strategy)

    return analysis, explanation


def _generate_explanation(analysis, topic, mastery, selected_lesson, strategy):
    """
    Generate a grounded explanation from a completed image analysis.
    """
    description = analysis.get("description", "")
    visible_text = analysis.get("visible_text", [])
    components = analysis.get("components", [])
    relationships = analysis.get("relationships", [])
    concepts = analysis.get("educational_concepts", [])
    visual_type = analysis.get("visual_type", "unknown")
    uncertainties = analysis.get("uncertainties", [])

    # Determine teaching depth from mastery
    if mastery < 0.30:
        depth_instruction = """
Teaching depth: BEGINNER
- Explain from first principles using simple but mature language.
- Describe each visible component step by step.
- Explain what each part does and why it matters.
- Use clear examples where appropriate.
"""
    elif mastery < 0.70:
        depth_instruction = """
Teaching depth: INTERMEDIATE
- Assume basic understanding of the topic.
- Explain how the visible components work together.
- Connect the concepts shown to each other.
- Explain the flow, logic, or purpose of the image.
"""
    else:
        depth_instruction = """
Teaching depth: ADVANCED
- Provide deeper technical interpretation.
- Discuss design decisions, trade-offs, or implications.
- Connect to broader technical context.
- Be concise — the student already knows the basics.
"""

    strategy_text = ""
    if strategy and "instruction" in strategy:
        strategy_text = f"Teaching style guidance: {strategy['instruction']}"

    lesson_context = ""
    if selected_lesson:
        lesson_context = f"""
The student is currently studying: {selected_lesson}
Focus your explanation on how this image relates to: {selected_lesson}
"""
    elif topic:
        lesson_context = f"""
The student is currently studying: {topic}
Relate your explanation to this topic where relevant.
"""

    uncertainty_text = ""
    if uncertainties:
        uncertainty_text = f"""
Note: The following aspects of the image were uncertain or unreadable:
{uncertainties}
Do not guess about these uncertain elements.
"""

    visible_text_str = ""
    if visible_text:
        visible_text_str = f"""
Readable text visible in the image:
{visible_text}
"""

    prompt = f"""You are NeuroTutor, an expert adaptive AI tutor.

A student has uploaded an educational image. Here is what the image actually shows:

Image type: {visual_type}

Description of what is visible:
{description}
{visible_text_str}
Components visible:
{components if components else "None specifically identified"}

Relationships observed:
{relationships if relationships else "None specifically identified"}

Educational concepts present:
{concepts if concepts else "None specifically identified"}
{uncertainty_text}
{lesson_context}

Student mastery level: {mastery}

{strategy_text}

{depth_instruction}

EXPLANATION RULES:

1. WHAT THE IMAGE SHOWS: First describe what is actually visible in the image — the components, text, structure, and layout that were observed.

2. WHAT IT MEANS: Then explain the educational significance of what is shown. You may use your knowledge of the topic to teach, but clearly distinguish between what is visible and what you are explaining.

3. GROUNDING: Do NOT claim that the image shows components, arrows, labels, text, or relationships that were NOT reported in the analysis above. If something is uncertain, say so.

4. TEACHING: Adapt your explanation depth to the student's mastery level.

5. TONE: Assume the student is a university Computer Engineering student. Maintain an academic tone. Use proper terminology, then explain it clearly.

6. Do NOT begin with "Let's begin" or "Welcome".

7. End naturally after explaining the image.
"""

    result = _text_query(prompt)

    if not result:
        return "⚠️ Could not generate explanation. Please try again."

    return result


# ==================== Image Question Generation ====================

def generate_image_question(image_context, topic, mastery, selected_lesson=None):
    """
    Generate an adaptive educational question based on a completed image analysis.

    image_context: dict from analyze_image()
    """

    description = image_context.get("description", "")
    visible_text = image_context.get("visible_text", [])
    components = image_context.get("components", [])
    relationships = image_context.get("relationships", [])
    concepts = image_context.get("educational_concepts", [])
    visual_type = image_context.get("visual_type", "unknown")

    # Determine difficulty from mastery
    if mastery < 0.40:
        difficulty = "EASY"
        difficulty_instruction = """
Ask a basic conceptual question about what is visible.
Test identification or recall of a component or concept shown.
"""
    elif mastery < 0.70:
        difficulty = "MEDIUM"
        difficulty_instruction = """
Ask about how the visible components relate to each other.
Test understanding of the process, flow, or structure shown.
"""
    else:
        difficulty = "HARD"
        difficulty_instruction = """
Ask an analytical question requiring reasoning about what is shown.
Test deeper understanding of design choices or implications.
"""

    lesson_context = ""
    if selected_lesson:
        lesson_context = f"The student is currently studying: {selected_lesson}\nMake the question relevant to this lesson.\n"
    elif topic:
        lesson_context = f"The student is currently studying: {topic}\nMake the question relevant to this topic.\n"

    prompt = f"""You are NeuroTutor, an expert adaptive AI tutor.

A student has uploaded an educational image. Here is what the image actually shows:

Image type: {visual_type}

Description:
{description}

Readable text in image:
{visible_text if visible_text else "None identified"}

Components:
{components if components else "None specifically identified"}

Relationships:
{relationships if relationships else "None specifically identified"}

Educational concepts:
{concepts if concepts else "None specifically identified"}

{lesson_context}

Student mastery: {mastery}
Question difficulty: {difficulty}

{difficulty_instruction}

RULES:
- The question MUST be about something that was ACTUALLY observed in the image analysis above.
- Do NOT reference components, labels, arrows, text, or relationships that are NOT listed above.
- Do NOT invent image content.
- The question must be answerable based on the image and the student's knowledge of the topic.
- Return ONLY the question text. No answer. No explanation.
"""

    result = _text_query(prompt)

    if not result:
        return "⚠️ Could not generate a question. Please try again."

    return result


# ==================== Vision Model Check ====================

def check_vision_model():
    """
    Check if the configured vision model is available in Ollama.
    Returns (available: bool, message: str).
    """
    try:
        result = ollama.list()

        model_names = []

        # ollama 0.6+ returns a Pydantic ListResponse with .models
        models_list = result.models if hasattr(result, "models") else result.get("models", [])

        for m in models_list:
            name = m.model if hasattr(m, "model") else m.get("name", "")
            model_names.append(name)
            if ":" in name:
                model_names.append(name.split(":")[0])

        if VISION_MODEL in model_names:
            return True, f"Vision model '{VISION_MODEL}' is available."

        return False, (
            f"Visual Learning requires the '{VISION_MODEL}' model.\n\n"
            f"Please install it by running:\n\n"
            f"```\nollama pull {VISION_MODEL}\n```\n\n"
            f"Then restart NeuroTutor."
        )

    except Exception as e:
        return False, (
            f"Could not connect to Ollama: {e}\n\n"
            f"Please ensure Ollama is running."
        )

