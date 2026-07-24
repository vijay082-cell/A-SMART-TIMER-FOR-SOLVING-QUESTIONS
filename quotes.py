"""
quotes.py
----------
A curated pool of dark, realist, motivational quotes (Machiavelli, Sun Tzu,
Nietzsche, Stoic, discipline / power themes).

get_daily_quote() returns one quote per calendar day. Because it is selected by
the day's ordinal number modulo the pool size, the quote changes every day and
only repeats after the entire pool has been shown (a "very long time").
"""

import datetime

QUOTES = [
    ("It is better to be feared than loved, if you cannot be both.", "Niccolò Machiavelli"),
    ("The ends justify the means.", "Niccolò Machiavelli"),
    ("Men are driven by two principal impulses, either by love or by fear.", "Niccolò Machiavelli"),
    ("He who wishes to be obeyed must know how to command.", "Niccolò Machiavelli"),
    ("Never attempt to win by force what can be won by deception.", "Niccolò Machiavelli"),
    ("Fortune is like water; it flows where the channel leads it.", "Niccolò Machiavelli"),
    ("Whoever desires constant success must change his conduct with the times.", "Niccolò Machiavelli"),
    ("The lion cannot protect himself from traps, and the fox cannot defend himself from wolves.", "Niccolò Machiavelli"),
    ("All the wizardry in the world is in vain without the muscle to back it.", "Robert Greene"),
    ("Master your emotions or they will master you.", "Robert Greene"),
    ("Absence diminishes minor passions and increases great ones.", "La Rochefoucauld"),
    ("The supreme art of war is to subdue the enemy without fighting.", "Sun Tzu"),
    ("Opportunities multiply as they are seized.", "Sun Tzu"),
    ("Attack him where he is unprepared, appear where you are not expected.", "Sun Tzu"),
    ("Keep your friends close and your enemies closer.", "Sun Tzu"),
    ("He who has a why to live can bear almost any how.", "Friedrich Nietzsche"),
    ("That which does not kill me makes me stronger.", "Friedrich Nietzsche"),
    ("And if you gaze long into an abyss, the abyss also gazes into you.", "Friedrich Nietzsche"),
    ("You must be ready to burn yourself in your own flame.", "Friedrich Nietzsche"),
    ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Aristotle"),
    ("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    ("You have power over your mind, not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    ("Waste no more time arguing about what a good man should be. Be one.", "Marcus Aurelius"),
    ("We suffer more often in imagination than in reality.", "Seneca"),
    ("Luck is what happens when preparation meets opportunity.", "Seneca"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Our greatest glory is not in never falling, but in rising every time we fall.", "Confucius"),
    ("Discipline is the bridge between goals and accomplishment.", "Jim Rohn"),
    ("Hard times create strong men. Comfort creates weakness.", "Anonymous"),
    ("The pain of discipline weighs ounces; the pain of regret weighs tons.", "Jim Rohn"),
    ("Do not pray for an easy life. Pray for the strength to endure a difficult one.", "Bruce Lee"),
    ("Knowing is not enough; we must apply. Willing is not enough; we must do.", "Goethe"),
    ("A winner is a dreamer who never gives up.", "Nelson Mandela"),
    ("The master has failed more times than the beginner has even tried.", "Stephen McCranie"),
    ("Fall seven times, stand up eight.", "Japanese Proverb"),
    ("Great things are done by a series of small things brought together.", "Vincent van Gogh"),
    ("Success is the sum of small efforts repeated day in and day out.", "Robert Collier"),
    ("Difficulties strengthen the mind, as labor does the body.", "Seneca"),
    ("The man who moves a mountain begins by carrying away small stones.", "Confucius"),
    ("Victory belongs to the most persevering.", "Napoleon Bonaparte"),
    ("Courage is not the absence of fear, but the triumph over it.", "Nelson Mandela"),
    ("Do one thing every day that scares you.", "Eleanor Roosevelt"),
    ("Your limitation—it's only your imagination.", "Anonymous"),
    ("Push yourself, because no one else is going to do it for you.", "Anonymous"),
    ("Dream big and dare to fail.", "Norman Vaughan"),
    ("The future depends on what you do today.", "Mahatma Gandhi"),
]


def get_daily_quote():
    """Return (quote_text, author) for today. Changes daily; repeats only
    after the full pool has cycled."""
    idx = datetime.date.today().toordinal() % len(QUOTES)
    return QUOTES[idx]