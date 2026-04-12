import random

_MESSAGES = [
    "If you get up in the morning and think the future is going to be better, it is a bright day. Otherwise, it's not.",
    "When something is important enough, you do it even if the odds are not in your favor.",
    "Optimism, pessimism, f* that—we're going to make it happen.",
    "Try to be useful. Do things that are useful to your fellow human beings, to the world. It’s very hard to be useful—extraordinarily hard.",
    f"{1}% better every day.",
    f"Just get {1}% better than yesterday."
    "The quieter you become, the more you can hear.",
    "Almost everything will work again if you unplug it for a few minutes.",
    "Breathe. You are exactly where you need to be.",
    "Do less. Mean it more.",
    "The present moment always will have been.",
    "Rest is not idleness.",
    "You are allowed to be both a masterpiece and a work in progress.",
    "Slow down. The thing you're rushing toward will still be there.",
    "Not all those who wander are lost.",
    "Stillness is where creativity and solutions are found.",
    "One thing at a time. Right now. Completely.",
    "Your only obligation in any lifetime is to be true to yourself.",
    "There is nothing either good or bad but thinking makes it so.",
    "The day you plant the seed is not the day you eat the fruit.",
    "Begin anywhere.",
    "You have permission to rest.",
    "Comparison is the thief of joy.",
    "What you seek is seeking you.",
    "The goal is not to be better than the other person but your previous self.",
    "This too shall pass.",
    "Worry is a misuse of imagination.",
    "Progress, not perfection.",
    "The best time to plant a tree was twenty years ago. The second best time is now.",
    "A gentle reminder that you are doing enough.",
    "Focus on the step in front of you, not the whole staircase.",
    "Let go of what you cannot control.",
    "Your presence is your power.",
    "Small steps every day.",
]


def random_message() -> str:
    return random.choice(_MESSAGES)
