"""Simulated LLM summarisation layer for Level UP.

In production this step would call a large language model with the manager's
free-text notes and a structured-output schema. For the demo it is a
deterministic, inspectable theme extractor: every sentence is matched against a
lexicon of themes, each hit is kept as *evidence*, and a short summary is
written from the extracted themes. The extracted signals (not the raw text)
feed the performance and potential scores.
"""
import re

# theme -> (label, group, positive cues, negative cues)
# group decides which score the theme feeds:
#   performance -> check-in sentiment (performance axis)
#   potential   -> manager-feedback signal (potential axis)
#   wellbeing   -> engagement / risk reading
#   career      -> mobility component (potential axis)
LEXICON = {
    "delivery": ("Delivery quality", "performance",
                 ["on time", "high standard", "high quality", "hit every milestone", "strong execution",
                  "exceeded", "excellent work", "solid delivery", "reliable delivery"],
                 ["rework", "missed", "deadline slipped", "inconsistent", "close review",
                  "below expectations", "errors", "late delivery", "poor quality"]),
    "client": ("Client impact", "performance",
               ["client feedback was excellent", "by name", "trust with the client", "real maturity",
                "client praised", "strong client"],
               ["client raised concerns", "client expectations", "communication gaps", "client complained",
                "escalation"]),
    "collaboration": ("Collaboration", "performance",
                      ["team player", "collaborates well", "shares knowledge", "supportive of colleagues"],
                      ["friction", "in isolation", "conflict with"]),
    "onboarding": ("Onboarding integration", "performance",
                   ["settling in well", "integrated quickly", "ramping up quickly", "buddy programme is working"],
                   ["finding their feet", "limited contact with the team", "unclear on", "lacks context"]),
    "leadership": ("Leadership", "potential",
                   ["leadership", "mentored", "mentoring", "took ownership", "led the", "ready for more scope",
                    "stepped up", "coached"],
                   ["prefers to execute", "reluctant", "limited appetite", "avoids responsibility"]),
    "learning": ("Learning agility", "potential",
                 ["learning agility", "picked up", "certification", "applies feedback fast", "curious",
                  "fast learner", "learns quickly"],
                 ["not engaged with the development plan", "slow to apply feedback", "little interest",
                  "resistant to feedback"]),
    "ambition": ("Career ambition", "potential",
                 ["ambition", "path to", "next level", "wants to progress", "promotion"],
                 ["comfortable in the current role", "no stated wish", "not a priority"]),
    "mobility": ("Mobility interest", "career",
                 ["rotation", "open to an international", "move to another practice", "open to relocation",
                  "new practice"],
                 ["prefers to stay", "not looking for a change"]),
    "workload": ("Workload & wellbeing", "wellbeing",
                 ["sustainable and well balanced", "healthy balance", "good balance"],
                 ["long hours", "not sustainable", "stretched thin", "fatigue", "burnout", "overloaded",
                  "exhausted"]),
    "motivation": ("Motivation", "wellbeing",
                   ["motivated by", "energised", "enthusiastic", "engaged and positive"],
                   ["less motivated", "frustration", "frustrated", "still matches", "approached by",
                    "disengaged", "quieter", "considering leaving", "demotivated"]),
    "expectations": ("Expectation vs reality", "wellbeing",
                     ["matches what was described", "as expected", "exceeds expectations of the role"],
                     ["differs from what was described", "expected more", "not what", "mismatch"]),
}

# Weak general sentiment cues, used only when no theme matched in a sentence.
GENERAL_POS = ["excellent", "great", "strong", "impressive", "outstanding", "well done", "good progress"]
GENERAL_NEG = ["poor", "weak", "concern", "disappointing", "struggl", "issue", "problem"]

_SENT_SPLIT = re.compile(r"(?<=[.!?;])\s+")


def _contains(text, cue):
    return cue in text


def analyse_note(text):
    """Return a list of hits: {theme, label, group, polarity, evidence}."""
    hits = []
    for sentence in _SENT_SPLIT.split(text.strip()):
        s = sentence.lower()
        if not s:
            continue
        matched = False
        for theme, (label, group, pos, neg) in LEXICON.items():
            # Negative cues take precedence ("not sustainable" contains "sustainable").
            if any(_contains(s, c) for c in neg):
                hits.append(dict(theme=theme, label=label, group=group, polarity=-1, evidence=sentence.strip()))
                matched = True
            elif any(_contains(s, c) for c in pos):
                hits.append(dict(theme=theme, label=label, group=group, polarity=1, evidence=sentence.strip()))
                matched = True
        if not matched:
            if any(c in s for c in GENERAL_NEG):
                hits.append(dict(theme="general", label="General tone", group="performance", polarity=-1,
                                 evidence=sentence.strip()))
            elif any(c in s for c in GENERAL_POS):
                hits.append(dict(theme="general", label="General tone", group="performance", polarity=1,
                                 evidence=sentence.strip()))
    return hits


def sentiment_index(hits, group="performance"):
    """0-100 index from the balance of positive vs negative hits in a group (50 = neutral)."""
    sel = [h for h in hits if h["group"] == group]
    if not sel:
        return 50.0
    pos = sum(1 for h in sel if h["polarity"] > 0)
    neg = len(sel) - pos
    return 50.0 + 50.0 * (pos - neg) / (pos + neg)


def signal_index(hits, group="potential", step=12.5):
    """0-100 index: 50 + step per net positive mention, clipped."""
    net = sum(h["polarity"] for h in hits if h["group"] == group)
    return max(0.0, min(100.0, 50.0 + step * net))


def _join(items):
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def summarise(first_name, notes):
    """Build the employee-level summary.

    notes: list of dicts {date, kind, text, hits} ordered oldest -> newest.
    Returns dict with summary text, theme table and tone trend.
    """
    if not notes:
        return dict(text=f"No manager notes available yet for {first_name}.", themes=[], tone=None,
                    tone_prev=None, n_notes=0)

    agg = {}
    for i, n in enumerate(notes):
        recency = 1.0 + i / max(1, len(notes) - 1)  # newer notes count more (1.0 -> 2.0)
        for h in n["hits"]:
            if h["theme"] == "general":
                continue
            a = agg.setdefault(h["theme"], dict(label=h["label"], group=h["group"], pos=0, neg=0, score=0.0,
                                                evidence=[]))
            if h["polarity"] > 0:
                a["pos"] += 1
            else:
                a["neg"] += 1
            a["score"] += h["polarity"] * recency
            a["evidence"].append((n["date"], h["polarity"], h["evidence"]))

    strengths = sorted([a for a in agg.values() if a["score"] > 0 and a["group"] in ("performance", "potential")],
                       key=lambda a: -a["score"])
    devs = sorted([a for a in agg.values() if a["score"] < 0 and a["group"] in ("performance", "potential")],
                  key=lambda a: a["score"])
    wellbeing_neg = [a for a in agg.values() if a["group"] == "wellbeing" and a["score"] < 0]
    wellbeing_pos = [a for a in agg.values() if a["group"] == "wellbeing" and a["score"] > 0]
    mobility = agg.get("mobility")

    all_hits = [h for n in notes for h in n["hits"]]
    latest = notes[-1]["hits"]
    prev = notes[-2]["hits"] if len(notes) > 1 else None
    tone = sentiment_index(latest)
    tone_prev = sentiment_index(prev) if prev is not None else None
    overall = sentiment_index(all_hits)

    tone_word = "positive" if overall >= 65 else ("mixed" if overall >= 40 else "concerning")
    parts = [f"Across {len(notes)} manager note{'s' if len(notes) > 1 else ''}, the overall tone on "
             f"{first_name}'s performance is **{tone_word}**."]
    if strengths:
        parts.append("Recurring strengths: " + _join(a["label"].lower() for a in strengths[:3]) + ".")
    if devs:
        parts.append("Development areas: " + _join(a["label"].lower() for a in devs[:3]) + ".")
    if wellbeing_neg:
        recent_neg = [a for a in wellbeing_neg if any(e[0] == notes[-1]["date"] and e[1] < 0 for e in a["evidence"])]
        lbl = _join(a["label"].lower() for a in wellbeing_neg)
        if recent_neg:
            parts.append(f"Watch-out: {lbl} flagged, including in the most recent note.")
        else:
            parts.append(f"Earlier mentions of {lbl} — not repeated recently.")
    elif wellbeing_pos:
        parts.append("Engagement signals in the notes are healthy.")
    if mobility:
        if mobility["score"] > 0:
            parts.append(f"{first_name} has expressed interest in mobility (rotation / new practice).")
        else:
            parts.append(f"{first_name} prefers to stay in the current scope for now.")
    if tone_prev is not None:
        delta = tone - tone_prev
        if delta >= 20:
            parts.append("The latest note is noticeably more positive than the previous one.")
        elif delta <= -20:
            parts.append("The latest note is noticeably more negative than the previous one.")

    themes = []
    for key, a in sorted(agg.items(), key=lambda kv: -abs(kv[1]["score"])):
        themes.append(dict(theme=a["label"], feeds={"performance": "Performance", "potential": "Potential",
                                                     "wellbeing": "Engagement risk", "career": "Potential (mobility)"}[a["group"]],
                           positive=a["pos"], negative=a["neg"],
                           direction="▲ positive" if a["score"] > 0 else ("▼ negative" if a["score"] < 0 else "■ neutral"),
                           evidence=a["evidence"]))
    return dict(text=" ".join(parts), themes=themes, tone=tone, tone_prev=tone_prev, overall=overall,
                n_notes=len(notes))
