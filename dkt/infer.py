#infer.py
import torch

from .model import DKTModel


MODEL_PATH = __file__.replace(
    "infer.py",
    "dkt_model.pt"
)


model = DKTModel()

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location="cpu"
    )
)

model.eval()


def predict_mastery_dkt(topic):
    """
    Predict mastery using the DKT model.
    Blends DKT predictions with simple history for more reliable results.
    """
    from profile import get_profile

    profile = get_profile()

    if topic not in profile["topics"]:
        return 0.20

    interactions = profile["topics"][topic].get("interactions", [])
    history = profile["topics"][topic].get("history", [])

    # If no interactions but we have history, use simple average
    if len(interactions) == 0:
        if len(history) > 0:
            recent = history[-5:]
            return sum(recent) / len(recent)
        return 0.20

    # Use last 10 interactions for recency (not all)
    recent_interactions = interactions[-10:]
    
    sequence = []

    for item in recent_interactions:
        difficulty = {
            "easy": 0.2,
            "medium": 0.5,
            "hard": 0.8
        }.get(
            item.get("difficulty", "medium"),
            0.5
        )

        sequence.append([
            float(item.get("correct", False)),
            difficulty
        ])

    # If very few interactions, use simple history
    if len(sequence) < 3:
        if len(history) > 0:
            recent = history[-5:]
            return sum(recent) / len(recent)
        return 0.20

    x = torch.tensor(
        sequence,
        dtype=torch.float32
    ).unsqueeze(0)

    with torch.no_grad():
        logits = model(x)
        probabilities = torch.sigmoid(logits)

    predictions = probabilities[0]
    
    # Use last 3 predictions for recency
    recent_count = min(3, len(predictions))
    recent_predictions = predictions[-recent_count:]

    dkt_mastery = float(recent_predictions.mean().item())
    
    # If we have history, blend DKT with simple history
    if len(history) > 0:
        recent_history = history[-5:]
        simple_mastery = sum(recent_history) / len(recent_history)
        # DKT gets 50% weight, simple gets 50%
        mastery = 0.5 * dkt_mastery + 0.5 * simple_mastery
    else:
        mastery = dkt_mastery

    return round(
        max(0.0, min(1.0, mastery)),
        2
    )