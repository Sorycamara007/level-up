"""Seed script for the Level UP demo.

Generates a reproducible, fully fictional dataset for "Northvale Consulting"
(a fictional 250-person consulting firm) and writes it to data/levelup.db.

    python seed.py            # (re)build the database

Simulated timeline: 12 months, October 2025 -> September 2026 ("today" = 1 Oct 2026).
  * monthly pulse surveys
  * quarterly manager check-ins (Dec, Mar, Jun, Sep)
  * 30/60/90-day onboarding check-ins instead of quarterly ones during a new hire's first 90 days
  * annual review on each employee's start anniversary (history kept up to 5 years)
  * one annual engagement & career survey (Feb 2026) and a one-time Big Five personality test
"""
import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "levelup.db"
TODAY = date(2026, 10, 1)
WINDOW_START = date(2025, 10, 1)
QUARTER_DATES = [date(2025, 12, 12), date(2026, 3, 13), date(2026, 6, 12), date(2026, 9, 11)]
SURVEY_DATE = date(2026, 2, 16)
PERSONALITY_ROLLOUT = date(2025, 11, 10)
FIRM = "Northvale Consulting"
HEADCOUNT = 250

LEVELS = {"Analyst": 1, "Consultant": 2, "Senior Consultant": 3, "Manager": 4, "Director": 5, "Partner": 6}

PROJECTS = ["Atlas", "Helios", "Northstar", "Meridian", "Keystone", "Lighthouse", "Summit", "Orbit"]
COURSES = ["Prosci Change Management", "Lean Six Sigma Green Belt", "CFA Level I", "Advanced Financial Modelling",
           "Facilitation Mastery", "People Analytics"]
SKILL_LEARN = ["the client's data platform", "the valuation toolkit", "the new PMO tooling", "Power BI",
               "the org-design methodology"]

# ---------------------------------------------------------------------------
# Phrase banks used to write manager notes. Keys are (theme, polarity).
# ---------------------------------------------------------------------------
BANK = {
    ("delivery", 1): ["{n} delivered the workstream on time and to a high standard.",
                      "Deliverables on Project {proj} were consistently high quality with minimal edits.",
                      "Strong execution on the {proj} engagement — {n} hit every milestone."],
    ("delivery", -1): ["Several of {n}'s deliverables needed significant rework this quarter.",
                       "{n} missed two internal deadlines on the {proj} engagement.",
                       "Quality of analysis was inconsistent and required close review."],
    ("client", 1): ["Client feedback was excellent; the sponsor asked for {n} by name on the follow-on work.",
                    "{n} built strong trust with the client steering committee.",
                    "{n} handled a difficult client conversation with real maturity."],
    ("client", -1): ["The client raised concerns about responsiveness on Project {proj}.",
                     "{n} struggled to manage client expectations on scope.",
                     "The client sponsor flagged communication gaps in the weekly updates."],
    ("collaboration", 1): ["Great team player — colleagues across practices seek {n} out.",
                           "{n} collaborates well and shares knowledge generously with juniors."],
    ("collaboration", -1): ["Some friction with the project team this quarter.",
                            "{n} tends to work in isolation, which slowed the team down."],
    ("leadership", 1): ["{n} stepped up to coordinate two analysts — natural leadership emerging.",
                        "{n} took ownership of the workstream and mentored junior colleagues.",
                        "{n} led the client workshop independently and is ready for more scope."],
    ("leadership", -1): ["{n} prefers to execute rather than lead team topics.",
                         "{n} is reluctant to take on people management responsibilities.",
                         "Limited appetite to lead beyond own tasks so far."],
    ("learning", 1): ["{n} picked up {skill} very quickly — strong learning agility.",
                      "{n} proactively completed the {course} certification.",
                      "Curious, asks the right questions and applies feedback fast."],
    ("learning", -1): ["{n} has not engaged with the development plan agreed last year.",
                       "{n} is slow to apply feedback from previous reviews.",
                       "Shows little interest in new methods or tools."],
    ("ambition", 1): ["Clear ambition to move to the next level within 12-18 months.",
                      "{n} asked about the path to the next grade and what it would take."],
    ("ambition", -1): ["{n} seems comfortable in the current role, with no stated wish to progress.",
                       "{n} said progression is not a priority at this stage."],
    ("mobility", 1): ["{n} expressed interest in a rotation to the {other} practice.",
                      "{n} is open to an international assignment or a move to another practice."],
    ("mobility", -1): ["{n} prefers to stay within the current practice and client portfolio.",
                       "{n} is not looking for a change of scope at this stage."],
    ("workload", 1): ["Workload feels sustainable and well balanced.",
                      "Healthy balance between client work and internal initiatives."],
    ("workload", -1): ["{n} has been working very long hours; the current workload is not sustainable.",
                       "{n} mentioned feeling stretched thin across three engagements.",
                       "Visible signs of fatigue after back-to-back staffing."],
    ("motivation", 1): ["{n} is very motivated by the current engagement.",
                        "{n} is energised and enthusiastic about the practice's direction."],
    ("motivation", -1): ["{n} seemed less motivated than usual and quieter in team meetings.",
                         "{n} expressed frustration about the lack of interesting assignments.",
                         "{n} questioned whether the role still matches what they want.",
                         "{n} mentioned being approached by a competitor."],
    ("onboarding", 1): ["{n} is settling in well; the buddy programme is working.",
                        "{n} integrated quickly into the team and is ramping up quickly."],
    ("onboarding", -1): ["{n} is still finding their feet, with limited contact with the team so far.",
                         "{n} is unclear on how staffing decisions are made."],
    ("expectations", 1): ["So far the job matches what was described during recruitment."],
    ("expectations", -1): ["{n} feels the role differs from what was described during recruitment.",
                           "{n} expected more client exposure at this stage."],
}

OTHER_PRACTICE = {"Strategy": "Operations", "HR Consulting": "Strategy", "Finance & Transactions": "Strategy",
                  "Operations": "Finance & Transactions"}

SKILLS_TRANSFERABLE = {"Project management", "Client relationship", "Team leadership", "Business development",
                       "Data analytics", "Stakeholder management", "Workshop facilitation", "Change management"}

# ---------------------------------------------------------------------------
# Employee profiles. Reviews are listed oldest -> newest and aligned to the most
# recent start anniversaries. Check-in themes are listed per quarter
# (Dec 25, Mar 26, Jun 26, Sep 26); onboarding entries are (ramp 1-5, gap 0-10, themes, days late).
# Engagement / workload / sentiment shapes: (start, end, shape) on a 1-10 scale.
# ---------------------------------------------------------------------------
P, N = 1, -1
EMPLOYEES = [
    # ---- Senior / long tenure (4) ----
    dict(id="E01", name="Magnus Aasted", practice="Strategy", start="2012-09-03", cohort="Senior",
         manager=None, manager_ext="Managing Partner (outside pilot cohort)",
         titles=[("2012-09-03", "Senior Consultant"), ("2015-01-05", "Manager"), ("2017-09-04", "Director"),
                 ("2020-09-01", "Partner")],
         skills=["Corporate strategy", "Market analysis", "Business development", "Client relationship",
                 "Team leadership", "Stakeholder management"],
         reviews=[(4.5, 106, 3.5), (4.5, 110, 3.5), (4.0, 100, 3.5), (4.5, 108, 3.5), (4.5, 112, 3.5)],
         checkins=[[("delivery", P), ("client", P), ("leadership", P)], [("client", P), ("workload", N)],
                   [("delivery", P), ("collaboration", P)], [("client", P), ("delivery", P), ("mobility", N)]],
         eng=(8.0, 8.1, "flat"), wl=(7.4, 7.4, "flat"), sent=(8.0, 8.0, "flat"),
         survey=dict(satisfaction=4, growth=3, enps=8, stay=5, mobility=0, aspiration="Deepen expertise in current role"),
         big5=(70, 85, 80, 60, 25)),
    dict(id="E02", name="Marcus Okafor", practice="Finance & Transactions", start="2016-03-14", cohort="Senior",
         manager=None, manager_ext="F&T Practice Partner (outside pilot cohort)",
         titles=[("2016-03-14", "Consultant"), ("2018-03-01", "Senior Consultant"), ("2020-03-02", "Manager"),
                 ("2024-03-04", "Director")],
         skills=["Financial modelling", "Due diligence", "Valuation", "Team leadership", "Business development",
                 "Client relationship", "Stakeholder management"],
         reviews=[(4.0, 100, 4.0), (4.5, 108, 4.0), (4.5, 112, 4.5), (5.0, 118, 5.0), (4.5, 115, 5.0)],
         checkins=[[("delivery", P), ("leadership", P), ("client", P)], [("ambition", P), ("leadership", P)],
                   [("client", P), ("delivery", P), ("learning", P)],
                   [("leadership", P), ("delivery", P), ("collaboration", P)]],
         eng=(8.2, 8.4, "flat"), wl=(7.0, 7.0, "flat"), sent=(8.0, 8.2, "flat"),
         survey=dict(satisfaction=5, growth=4, enps=9, stay=5, mobility=1, aspiration="Partner track"),
         big5=(75, 80, 75, 55, 30)),
    dict(id="E03", name="Hélène Marchetti", practice="Operations", start="2015-06-01", cohort="Senior",
         manager=None, manager_ext="Operations Practice Partner (outside pilot cohort)",
         titles=[("2015-06-01", "Consultant"), ("2016-07-01", "Senior Consultant"), ("2018-06-04", "Manager")],
         skills=["Process improvement", "Lean / Six Sigma", "Supply chain", "Project management", "PMO"],
         reviews=[(3.5, 90, 3.0), (3.5, 88, 2.5), (3.0, 82, 2.0), (3.5, 85, 2.0), (3.0, 80, 2.0)],
         checkins=[[("delivery", P), ("mobility", N)], [("ambition", N), ("delivery", N)],
                   [("collaboration", P), ("learning", N)], [("delivery", P), ("ambition", N), ("motivation", N)]],
         eng=(6.2, 5.7, "linear"), wl=(6.0, 6.2, "flat"), sent=(6.2, 5.8, "linear"),
         survey=dict(satisfaction=3, growth=2, enps=6, stay=4, mobility=0, aspiration="Deepen expertise in current role"),
         big5=(40, 75, 45, 70, 45)),
    dict(id="E04", name="David Lindqvist", practice="HR Consulting", start="2017-02-06", cohort="Senior",
         manager="E05",
         titles=[("2017-02-06", "Consultant"), ("2019-02-04", "Senior Consultant")],
         skills=["Compensation & benefits", "Workforce analytics", "Data analytics", "HR policy"],
         reviews=[(4.0, 102, 2.5), (4.5, 110, 2.0), (4.0, 105, 2.0), (4.5, 108, 2.0), (4.5, 110, 2.0)],
         checkins=[[("delivery", P), ("client", P), ("ambition", N)], [("delivery", P), ("leadership", N)],
                   [("client", P), ("mobility", N)], [("delivery", P), ("collaboration", P), ("ambition", N)]],
         eng=(7.2, 7.1, "flat"), wl=(6.0, 6.0, "flat"), sent=(7.0, 7.0, "flat"),
         survey=dict(satisfaction=4, growth=3, enps=7, stay=5, mobility=0, aspiration="Deepen expertise in current role"),
         big5=(45, 88, 35, 65, 30)),
    # ---- Mid tenure (6) ----
    dict(id="E05", name="Priya Raman", practice="HR Consulting", start="2020-05-11", cohort="Mid-tenure",
         manager=None, manager_ext="HR Consulting Practice Partner (outside pilot cohort)",
         titles=[("2020-05-11", "Consultant"), ("2022-05-02", "Senior Consultant"), ("2024-05-06", "Manager")],
         skills=["Change management", "Org design", "Workshop facilitation", "Team leadership",
                 "Stakeholder management", "Client relationship", "Workforce analytics"],
         reviews=[(4.0, 100, 4.0), (4.5, 108, 4.5), (4.5, 110, 4.5), (4.5, 112, 5.0), (5.0, 118, 5.0)],
         checkins=[[("leadership", P), ("client", P)], [("delivery", P), ("learning", P), ("ambition", P)],
                   [("leadership", P), ("collaboration", P)], [("client", P), ("delivery", P), ("leadership", P)]],
         eng=(7.8, 8.6, "linear"), wl=(7.0, 7.0, "flat"), sent=(7.8, 8.4, "linear"),
         survey=dict(satisfaction=5, growth=5, enps=9, stay=5, mobility=1, aspiration="Director track"),
         big5=(82, 80, 70, 72, 25)),
    dict(id="E06", name="Julien Moreau", practice="Strategy", start="2022-01-10", cohort="Mid-tenure",
         manager="E01",
         titles=[("2022-01-10", "Consultant"), ("2024-01-08", "Senior Consultant")],
         skills=["Corporate strategy", "Market analysis", "Data analytics", "Workshop facilitation",
                 "Project management", "Change management"],
         reviews=[(3.5, 92, 4.0), (4.0, 100, 4.5), (3.5, 95, 4.5), (3.5, 93, 5.0)],
         checkins=[[("learning", P), ("ambition", P), ("delivery", N)], [("leadership", P), ("mobility", P)],
                   [("learning", P), ("client", P), ("delivery", N)], [("leadership", P), ("ambition", P), ("delivery", N)]],
         eng=(7.0, 8.0, "linear"), wl=(6.5, 6.5, "flat"), sent=(7.0, 7.8, "linear"),
         survey=dict(satisfaction=4, growth=4, enps=8, stay=4, mobility=1, aspiration="Move into management"),
         big5=(88, 65, 70, 60, 35)),
    dict(id="E07", name="Aisha Bello", practice="Finance & Transactions", start="2021-04-06", cohort="Mid-tenure",
         manager="E02",
         titles=[("2021-04-06", "Consultant"), ("2023-04-03", "Senior Consultant")],
         skills=["Financial modelling", "Due diligence", "Valuation", "Data analytics", "Client relationship",
                 "Stakeholder management"],
         reviews=[(3.5, 95, 3.5), (4.0, 102, 3.5), (4.0, 105, 3.5), (4.0, 104, 3.5), (5.0, 120, 4.5)],
         checkins=[[("delivery", P), ("client", N)], [("delivery", P), ("learning", P)],
                   [("leadership", P), ("client", P), ("ambition", P)], [("leadership", P), ("delivery", P), ("mobility", P)]],
         eng=(7.4, 8.1, "linear"), wl=(7.0, 7.2, "flat"), sent=(7.4, 8.0, "linear"),
         survey=dict(satisfaction=4, growth=4, enps=8, stay=4, mobility=1, aspiration="Move into management"),
         big5=(75, 85, 60, 65, 30)),
    dict(id="E08", name="Lukas Novak", practice="Operations", start="2023-03-20", cohort="Mid-tenure",
         manager="E03",
         titles=[("2023-03-20", "Analyst"), ("2024-09-02", "Consultant")],
         skills=["Process improvement", "Supply chain", "Data analytics", "Project management"],
         reviews=[(3.5, 90, 3.0), (3.5, 95, 3.0), (3.5, 92, 3.5)],
         checkins=[[("delivery", P), ("learning", P)], [("collaboration", P), ("delivery", N)],
                   [("delivery", P), ("workload", N)], [("delivery", P), ("ambition", P), ("client", N)]],
         eng=(7.0, 7.0, "flat"), wl=(6.5, 6.8, "flat"), sent=(7.0, 7.0, "flat"),
         survey=dict(satisfaction=4, growth=3, enps=7, stay=4, mobility=1, aspiration="Move into management"),
         big5=(60, 70, 55, 70, 40)),
    dict(id="E09", name="Sofia Esposito", practice="HR Consulting", start="2022-06-13", cohort="Mid-tenure",
         manager="E05",
         titles=[("2022-06-13", "Consultant"), ("2025-06-02", "Senior Consultant")],
         skills=["Change management", "Workshop facilitation", "Stakeholder management", "Org design",
                 "Data analytics", "Project management"],
         reviews=[(4.0, 100, 4.0), (4.0, 104, 4.0), (4.5, 110, 4.5), (2.5, 70, 4.5)],
         checkins=[[("delivery", N), ("learning", P)], [("client", N), ("leadership", P)],
                   [("delivery", N), ("learning", P), ("ambition", P)], [("delivery", N), ("leadership", P), ("mobility", P)]],
         eng=(6.9, 6.6, "flat"), wl=(7.6, 7.4, "flat"), sent=(6.6, 6.4, "flat"),
         survey=dict(satisfaction=3, growth=4, enps=7, stay=4, mobility=1, aspiration="Move to another practice"),
         big5=(85, 55, 75, 60, 50)),
    dict(id="E10", name="Ethan Clarke", practice="Finance & Transactions", start="2023-09-04", cohort="Mid-tenure",
         manager="E02",
         titles=[("2023-09-04", "Analyst"), ("2025-09-01", "Consultant")],
         skills=["Financial modelling", "Due diligence", "Data analytics"],
         reviews=[(3.5, 92, 3.5), (3.5, 90, 3.0), (2.5, 72, 3.0)],
         checkins=[[("delivery", P), ("collaboration", N)], [("delivery", N), ("learning", P)],
                   [("client", N), ("collaboration", P)], [("delivery", N), ("learning", P)]],
         eng=(6.6, 6.4, "flat"), wl=(6.0, 6.2, "flat"), sent=(6.5, 6.3, "flat"),
         survey=dict(satisfaction=3, growth=3, enps=6, stay=3, mobility=1, aspiration="Undecided"),
         big5=(65, 50, 60, 55, 55)),
    # ---- Early career (3) ----
    dict(id="E11", name="Camille Laurent", practice="Strategy", start="2024-11-04", cohort="Early-career",
         manager="E01",
         titles=[("2024-11-04", "Consultant")],
         skills=["Corporate strategy", "Market analysis", "Data analytics", "Workshop facilitation",
                 "Stakeholder management"],
         reviews=[(3.5, 95, 4.5)],
         checkins=[[("delivery", P), ("learning", P)], [("leadership", P), ("ambition", P), ("learning", P)],
                   [("client", N), ("learning", P)], [("client", P), ("leadership", P), ("mobility", P)]],
         eng=(7.4, 8.4, "linear"), wl=(7.0, 7.0, "flat"), sent=(7.6, 8.2, "linear"),
         survey=dict(satisfaction=5, growth=5, enps=9, stay=4, mobility=1, aspiration="Move into management"),
         big5=(90, 80, 65, 60, 30)),
    dict(id="E12", name="Omar Haddad", practice="Operations", start="2025-05-12", cohort="Early-career",
         manager="E03",
         titles=[("2025-05-12", "Analyst")],
         skills=["Process improvement", "Data analytics", "Supply chain"],
         reviews=[(3.5, 92, 3.0)],
         checkins=[[("delivery", P), ("learning", P)], [("collaboration", P)], [("delivery", P), ("client", N)],
                   [("delivery", N), ("ambition", P)]],
         eng=(7.2, 7.3, "flat"), wl=(6.0, 6.0, "flat"), sent=(7.0, 7.0, "flat"),
         survey=dict(satisfaction=4, growth=3, enps=7, stay=4, mobility=0, aspiration="Undecided"),
         big5=(55, 72, 50, 70, 40)),
    dict(id="E13", name="Mei Tanaka", practice="Finance & Transactions", start="2025-08-18", cohort="Early-career",
         manager="E02",
         titles=[("2025-08-18", "Analyst")],
         skills=["Financial modelling", "Valuation"],
         reviews=[(2.0, 60, 2.0)],
         onboarding=[(3.0, 4.0, [("onboarding", P), ("expectations", P)], 0),
                     (3.0, 5.0, [("onboarding", N), ("delivery", N)], 2),
                     (2.5, 5.5, [("delivery", N), ("expectations", N)], 0)],
         checkins=[[("delivery", N), ("learning", N)], [("delivery", N), ("collaboration", N)],
                   [("client", N), ("learning", N)], [("delivery", N), ("motivation", N)]],
         eng=(6.5, 5.9, "linear"), wl=(5.0, 5.2, "flat"), sent=(5.8, 5.4, "linear"),
         survey=dict(satisfaction=3, growth=2, enps=5, stay=3, mobility=0, aspiration="Undecided"),
         big5=(45, 45, 40, 60, 60)),
    # ---- New hires < 90 days (3) ----
    dict(id="E14", name="Lucas Fontaine", practice="Strategy", start="2026-07-06", cohort="New hire",
         manager="E01",
         titles=[("2026-07-06", "Analyst")],
         skills=["Market analysis", "Data analytics"],
         onboarding=[(4.0, 2.0, [("onboarding", P), ("expectations", P)], 0),
                     (4.0, 1.5, [("onboarding", P), ("learning", P), ("delivery", P)], 1)],
         eng=(8.0, 8.2, "flat"), wl=(6.0, 6.2, "flat"), sent=(8.0, 8.0, "flat"),
         big5=(78, 75, 70, 65, 30)),
    dict(id="E15", name="Zara Ahmed", practice="HR Consulting", start="2026-07-20", cohort="New hire",
         manager="E05",
         titles=[("2026-07-20", "Consultant")],
         skills=["Org design", "Change management", "Stakeholder management", "Client relationship"],
         onboarding=[(3.5, 6.0, [("expectations", N), ("onboarding", P)], 3),
                     (3.0, 7.5, [("expectations", N), ("motivation", N), ("workload", N)], 11)],
         eng=(7.0, 5.0, "linear"), wl=(7.0, 8.2, "linear"), sent=(6.6, 5.0, "linear"),
         big5=(70, 70, 55, 50, 55)),
    dict(id="E16", name="Noah Schmidt", practice="Operations", start="2026-08-24", cohort="New hire",
         manager="E03",
         titles=[("2026-08-24", "Analyst")],
         skills=["Supply chain", "Data analytics", "Project management"],
         onboarding=[(3.5, 3.0, [("onboarding", P), ("learning", P)], 0)],
         eng=(7.5, 7.5, "flat"), wl=(5.0, 5.0, "flat"), sent=(7.4, 7.4, "flat"),
         big5=(72, 68, 50, 70, 35)),
    # ---- Flight-risk / disengagement cases (2) ----
    dict(id="E17", name="Elena Petrova", practice="Strategy", start="2021-10-04", cohort="Mid-tenure",
         manager="E01", flight_story=True,
         titles=[("2021-10-04", "Consultant"), ("2023-10-02", "Senior Consultant")],
         skills=["Corporate strategy", "Market analysis", "Client relationship", "Stakeholder management",
                 "Change management"],
         reviews=[(4.0, 104, 4.0), (4.5, 110, 4.0), (4.5, 112, 3.5), (4.5, 110, 3.5)],
         checkins=[[("delivery", P), ("client", P), ("motivation", P)], [("delivery", P), ("ambition", P)],
                   [("client", P), ("workload", N), ("motivation", N)],
                   [("delivery", P), ("motivation", N), ("motivation", N)]],
         eng=(8.2, 4.4, "late"), wl=(7.0, 8.6, "late"), sent=(8.0, 4.6, "late"),
         survey=dict(satisfaction=2, growth=2, enps=4, stay=2, mobility=1, aspiration="Move into management"),
         big5=(60, 82, 55, 55, 45)),
    dict(id="E18", name="Ryan Mitchell", practice="Finance & Transactions", start="2023-09-11", cohort="Mid-tenure",
         manager="E02", flight_story=True,
         titles=[("2023-09-11", "Analyst"), ("2025-09-01", "Consultant")],
         skills=["Financial modelling", "Due diligence", "Data analytics", "Project management"],
         reviews=[(3.5, 95, 3.0), (3.5, 94, 3.0), (3.0, 82, 3.0)],
         checkins=[[("delivery", P), ("workload", N)], [("workload", N), ("motivation", N)],
                   [("delivery", N), ("workload", N)], [("motivation", N), ("client", N)]],
         eng=(7.5, 3.8, "late"), wl=(7.4, 9.4, "linear"), sent=(7.0, 4.0, "late"),
         survey=dict(satisfaction=2, growth=3, enps=3, stay=2, mobility=1, aspiration="Move to another practice"),
         big5=(60, 70, 50, 65, 60)),
]

VACANCIES = [
    dict(id="V1", title="Senior Consultant — Operations Excellence", level=3, practice="Operations",
         skills=["Process improvement", "Supply chain", "Project management", "Data analytics", "Client relationship"],
         hiring_manager="Hélène Marchetti", opened="2026-09-08",
         context="New 12-month supply-chain transformation engagement for a retail client; needs a Senior "
                 "Consultant to run the diagnostic workstream."),
    dict(id="V2", title="Manager — HR Consulting (Public Sector)", level=4, practice="HR Consulting",
         skills=["Change management", "Org design", "Team leadership", "Stakeholder management",
                 "Workforce analytics", "Client relationship"],
         hiring_manager="HR Consulting Practice Partner", opened="2026-08-25",
         context="Growth role: new public-sector portfolio (3 framework contracts). Manages a team of 4-6."),
    dict(id="V3", title="Director — Strategy & Transformation", level=5, practice="Strategy",
         skills=["Corporate strategy", "Team leadership", "Business development", "Change management",
                 "Stakeholder management"],
         hiring_manager="Magnus Aasted", opened="2026-09-15",
         context="Succession for a Director retiring in Q1 2027; owns a ~€6m book of business."),
]


def d(s):
    return date.fromisoformat(s)


def month_points(start):
    """Pulse survey dates (15th of each month) within the window, after the employee started."""
    out = []
    y, m = WINDOW_START.year, WINDOW_START.month
    while True:
        p = date(y, m, 15)
        if p >= TODAY:
            break
        if p >= start + timedelta(days=7):
            out.append(p)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def shape_value(spec, t):
    """spec=(start, end, shape); t in [0,1] across the 12-month window."""
    a, b, shape = spec
    if shape == "flat":
        return a + (b - a) * t
    if shape == "linear":
        return a + (b - a) * t
    if shape == "late":  # stable for ~5 months, then declines
        k = max(0.0, (t - 0.38) / 0.62)
        return a + (b - a) * k
    raise ValueError(shape)


def write_note(rng, emp, themes):
    first = emp["name"].split()[0]
    sentences = []
    for theme, pol in themes:
        options = BANK[(theme, pol)]
        tpl = rng.choice(options)
        sentences.append(tpl.format(n=first, proj=rng.choice(PROJECTS), skill=rng.choice(SKILL_LEARN),
                                    course=rng.choice(COURSES), other=OTHER_PRACTICE[emp["practice"]]))
    return " ".join(sentences)


def anniversaries(start, n):
    """Most recent n start anniversaries on or before TODAY (oldest first)."""
    out = []
    y = TODAY.year
    while len(out) < n:
        try:
            a = date(y, start.month, start.day)
        except ValueError:
            a = date(y, start.month, 28)
        if a <= TODAY and a > start:
            out.append(a)
        y -= 1
        if y < start.year:
            break
    return list(reversed(out))


def title_on(emp, when):
    t = emp["titles"][0][1]
    for s, title in emp["titles"]:
        if d(s) <= when:
            t = title
    return t


SCHEMA = """
CREATE TABLE employees (id TEXT PRIMARY KEY, name TEXT, title TEXT, level INTEGER, practice TEXT,
    manager_id TEXT, manager_ext TEXT, start_date TEXT, cohort TEXT, skills TEXT, scenario TEXT);
CREATE TABLE title_history (emp_id TEXT, effective_date TEXT, title TEXT, level INTEGER);
CREATE TABLE reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id TEXT, review_date TEXT, title_at_review TEXT,
    rating REAL, objectives_pct REAL, potential_rating REAL, notes TEXT);
CREATE TABLE checkins (id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id TEXT, checkin_date TEXT, kind TEXT,
    scheduled_date TEXT, author TEXT, notes TEXT, ramp_up REAL, expectation_gap REAL, source TEXT);
CREATE TABLE pulses (emp_id TEXT, pulse_date TEXT, engagement REAL, workload REAL, sentiment REAL);
CREATE TABLE personality (emp_id TEXT, taken_date TEXT, openness INTEGER, conscientiousness INTEGER,
    extraversion INTEGER, agreeableness INTEGER, neuroticism INTEGER);
CREATE TABLE annual_survey (emp_id TEXT, survey_date TEXT, satisfaction INTEGER, growth_opportunities INTEGER,
    enps INTEGER, intent_to_stay INTEGER, open_to_mobility INTEGER, aspiration TEXT);
CREATE TABLE vacancies (id TEXT PRIMARY KEY, title TEXT, level INTEGER, practice TEXT, skills TEXT,
    hiring_manager TEXT, opened TEXT, context TEXT);
CREATE TABLE decisions (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, actor TEXT, actor_role TEXT, kind TEXT,
    emp_id TEXT, vacancy_id TEXT, period TEXT, algo_value TEXT, final_value TEXT, status TEXT, reason TEXT);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
"""


def build(db_path=DB_PATH, seed=2026):
    rng = random.Random(seed)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    names = {e["id"]: e["name"] for e in EMPLOYEES}

    for e in EMPLOYEES:
        start = d(e["start"])
        title = title_on(e, TODAY)
        scenario = "Flight-risk case" if e.get("flight_story") else e["cohort"]
        con.execute("INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (e["id"], e["name"], title, LEVELS[title], e["practice"], e.get("manager"),
                     e.get("manager_ext"), e["start"], e["cohort"], json.dumps(e["skills"]), scenario))
        for s, t in e["titles"]:
            con.execute("INSERT INTO title_history VALUES (?,?,?,?)", (e["id"], s, t, LEVELS[t]))

        author = names.get(e.get("manager"), e.get("manager_ext") or "")

        # Annual reviews on start anniversaries
        revs = e.get("reviews", [])
        dates = anniversaries(start, len(revs))
        revs = revs[-len(dates):] if dates else []
        for (rating, obj, pot), rd in zip(revs, dates):
            tone = [("delivery", P if rating >= 3.5 else N), ("leadership", P if pot >= 3.5 else N)]
            note = (f"Annual review {rd.year}. Overall rating {rating}/5, {obj:.0f}% of objectives achieved. "
                    + write_note(rng, e, tone))
            con.execute("INSERT INTO reviews (emp_id, review_date, title_at_review, rating, objectives_pct, "
                        "potential_rating, notes) VALUES (?,?,?,?,?,?,?)",
                        (e["id"], rd.isoformat(), title_on(e, rd), rating, obj, pot, note))

        # Onboarding check-ins (30/60/90 days) for anyone whose first 90 days overlap the window
        onboarding_end = start + timedelta(days=90)
        for i, ob in enumerate(e.get("onboarding", [])):
            ramp, gap, themes, late = ob
            sched = start + timedelta(days=30 * (i + 1))
            actual = sched + timedelta(days=late)
            if actual >= TODAY:
                continue
            note = write_note(rng, e, themes)
            con.execute("INSERT INTO checkins (emp_id, checkin_date, kind, scheduled_date, author, notes, ramp_up, "
                        "expectation_gap, source) VALUES (?,?,?,?,?,?,?,?,?)",
                        (e["id"], actual.isoformat(), f"Onboarding {30 * (i + 1)}-day", sched.isoformat(), author,
                         note, ramp, gap, "seed"))

        # Quarterly check-ins (skipped while in the 90-day onboarding period)
        for qd, themes in zip(QUARTER_DATES, e.get("checkins", [])):
            if qd < onboarding_end or qd >= TODAY:
                continue
            note = write_note(rng, e, themes)
            con.execute("INSERT INTO checkins (emp_id, checkin_date, kind, scheduled_date, author, notes, ramp_up, "
                        "expectation_gap, source) VALUES (?,?,?,?,?,?,?,?,?)",
                        (e["id"], qd.isoformat(), "Quarterly check-in", qd.isoformat(), author, note, None, None,
                         "seed"))

        # Monthly pulse surveys
        span = (TODAY - WINDOW_START).days
        for p in month_points(start):
            t = (p - WINDOW_START).days / span
            vals = []
            for spec in (e["eng"], e["wl"], e["sent"]):
                v = shape_value(spec, t) + rng.gauss(0, 0.28)
                vals.append(round(max(1.0, min(10.0, v)), 1))
            con.execute("INSERT INTO pulses VALUES (?,?,?,?,?)", (e["id"], p.isoformat(), *vals))

        # Personality test (one-time)
        taken = max(PERSONALITY_ROLLOUT, start + timedelta(days=7))
        con.execute("INSERT INTO personality VALUES (?,?,?,?,?,?,?)", (e["id"], taken.isoformat(), *e["big5"]))

        # Annual engagement & career survey (one-time, Feb 2026)
        if e.get("survey") and start < SURVEY_DATE:
            s = e["survey"]
            con.execute("INSERT INTO annual_survey VALUES (?,?,?,?,?,?,?,?)",
                        (e["id"], SURVEY_DATE.isoformat(), s["satisfaction"], s["growth"], s["enps"], s["stay"],
                         s["mobility"], s["aspiration"]))

    for v in VACANCIES:
        con.execute("INSERT INTO vacancies VALUES (?,?,?,?,?,?,?,?)",
                    (v["id"], v["title"], v["level"], v["practice"], json.dumps(v["skills"]), v["hiring_manager"],
                     v["opened"], v["context"]))

    for k, v in dict(firm=FIRM, headcount=HEADCOUNT, today=TODAY.isoformat(), window_start=WINDOW_START.isoformat(),
                     seed=seed).items():
        con.execute("INSERT INTO meta VALUES (?,?)", (k, str(v)))
    con.commit()
    con.close()

    _seed_calibration_history(db_path)


def _seed_calibration_history(db_path):
    """Log two past calibration rounds (Q1 and Q2 2026) so the audit trail and calibration view are not empty.

    Uses the scoring engine itself, so the logged algorithm placements are the real ones. A few manager
    overrides are scripted to show realistic calibration patterns (mostly lenient, one stricter manager).
    """
    import engine  # local import: engine reads the DB we just wrote

    data = engine.load_data(db_path)
    overrides = {
        "2026-03": {
            "E13": ("Inconsistent Performer", "Joined in August — too early to call this under-performance; "
                                              "give a full year with closer coaching."),
            "E08": ("High Potential", "Strong client feedback on the retail diagnostic that the data does not "
                                      "capture yet."),
        },
        "2026-06": {
            "E09": ("High Potential", "Recently promoted into a new HR-tech workstream; dip in delivery is a "
                                      "stretch effect, not a capability issue. Re-assess at Q3."),
            "E13": ("Inconsistent Performer", "Still ramping up after a difficult first engagement; maintain "
                                              "coaching plan."),
            "E11": ("Core Player", "Potential is real but delivery rigour must come first; revisit at Q3."),
        },
    }
    stamps = {"2026-03": ("2026-03-27T10:00:00", "2026-03-31T16:00:00"),
              "2026-06": ("2026-06-26T10:00:00", "2026-06-30T15:30:00")}
    con = sqlite3.connect(db_path)
    for period, ovr in overrides.items():
        as_of = engine.period_end(period)
        n_over = 0
        for _, emp in data["employees"].iterrows():
            if not engine.is_active(emp, as_of):
                continue
            pl = engine.placement(data, emp["id"], as_of)
            mgr = data["names"].get(emp["manager_id"]) or emp["manager_ext"]
            final, status, reason = pl["box"], "confirmed", "Agree with proposed placement."
            if emp["id"] in ovr and ovr[emp["id"]][0] != pl["box"]:
                final, reason = ovr[emp["id"]]
                status = "overridden"
                n_over += 1
            con.execute("INSERT INTO decisions (ts, actor, actor_role, kind, emp_id, vacancy_id, period, algo_value, "
                        "final_value, status, reason) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (stamps[period][0], mgr, "Manager", "9-box", emp["id"], None, period, pl["box"], final,
                         status, reason))
        q = engine.quarter_label(period)
        con.execute("INSERT INTO decisions (ts, actor, actor_role, kind, emp_id, vacancy_id, period, algo_value, "
                    "final_value, status, reason) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (stamps[period][1], "HR Business Partner", "HR", "Calibration", None, None, period,
                     f"{q} placements", "Calibrated", "closed",
                     f"{q} calibration session held with practice leads; {n_over} manager overrides reviewed "
                     "and accepted."))
    con.commit()
    con.close()


if __name__ == "__main__":
    build()
    print(f"Seeded {len(EMPLOYEES)} employees and {len(VACANCIES)} vacancies -> {DB_PATH}")
