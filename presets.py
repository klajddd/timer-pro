import random

PRESETS = [
    "Deep Work",
    "Quick Break",
    "Lunch",
    "Intermittent Fast",
    "Morning Run",
    "Reading",
    "Meditation",
    "Power Nap",
    "Stand Up",
    "Focus Sprint",
    "Coffee Break",
    "Exercise",
    "Evening Wind Down",
    "Study Block",
    "Creative Time",
    "Admin Tasks",
    "Planning",
    "Code Review",
    "Email Batch",
    "Side Project",
]


def random_label() -> str:
    return random.choice(PRESETS)
