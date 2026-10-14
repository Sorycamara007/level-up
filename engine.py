"""Level UP scoring engine.

Everything the algorithm proposes is computed here, transparently:
  * 9-box placement (performance x potential) from weighted, inspectable components
  * engagement index + trend from monthly pulse surveys
  * flight-risk (established staff) and onboarding-risk (first 90 days) signals
  * career-path suggestions (rule-based on the 9-box cell)
  * succession matching for vacant roles

All functions take an `as_of` date, so the whole picture can be replayed month by
month over the simulated 12-month timeline. Nothing here executes a decision:
it only produces proposals that a manager / HR must confirm (see `decisions`).
"""
import calendar
import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import nlp

DB_PATH = Path(__file__).parent / "data" / "levelup.db"

LEVELS = {"Analyst": 1, "Consultant": 2, "Senior Consultant": 3, "Manager": 4, "Director": 5, "Partner": 6}
LEVEL_NAMES = {v: k for k, v in LEVELS.items()}
TRANSFERABLE = {"Project management", "Client relationship", "Team leadership", "Business development",
                "Data analytics", "Stakeholder management", "Workshop facilitation", "Change management"}

# ---------------------------------------------------------------------------
# Model parameters — shown verbatim on the Methodology page
# ---------------------------------------------------------------------------
PERF_WEIGHTS = {"Annual review rating": 0.45, "Objectives achieved": 0.25, "Check-in sentiment (AI)": 0.30}
PERF_WEIGHTS_NEW = {"Ramp-up speed (onboarding)": 0.60, "Check-in sentiment (AI)": 0.40}
PROVISIONAL_SHRINK = 0.5  # no annual review yet: performance is pulled halfway towards a neutral 50
POT_WEIGHTS = {"Manager feedback": 0.35, "Transferable skills": 0.25, "Desired mobility": 0.15,
               "Tenure & progression": 0.15, "Learning agility (Big Five openness)": 0.10}
BAND_LOW, BAND_HIGH = 50.0, 70.0  # score < 50 -> Low, 50-70 -> Moderate, >= 70 -> High
BAND_NAMES = ["Low", "Moderate", "High"]

FLIGHT_WEIGHTS = {"Low current engagement": 0.35, "Declining trend": 0.30, "Low intent to stay (survey)": 0.20,
                  "Warning signs in check-ins (AI)": 0.15}
ONBOARD_WEIGHTS = {"Expectation-vs-reality gap": 0.35, "Slow ramp-up": 0.30, "Early pulse engagement": 0.20,
                   "Missed / late 30-60-90 check-ins": 0.15}
RISK_HIGH, RISK_MED = 55.0, 30.0
ONBOARD_HIGH, ONBOARD_MED = 50.0, 32.0

SUCCESSION_WEIGHTS = {"9-box position": 0.40, "Skills match": 0.25, "Readiness (level gap)": 0.20,
                      "Aspiration & mobility fit": 0.15}

# (potential band, performance band) -> box
BOXES = {
    (2, 0): dict(name="Rough Diamond", n=7, color="#fdf0d5", desc="High potential, performance not yet showing"),
    (2, 1): dict(name="High Potential", n=8, color="#d9f0e3", desc="Strong potential, solid performance"),
    (2, 2): dict(name="Star", n=9, color="#b5e3c8", desc="Top performer with high potential"),
    (1, 0): dict(name="Inconsistent Performer", n=4, color="#fde2cf", desc="Moderate potential, under-delivering"),
    (1, 1): dict(name="Core Player", n=5, color="#fbf3c9", desc="Reliable contributor, moderate potential"),
    (1, 2): dict(name="High Performer", n=6, color="#d9f0e3", desc="Excellent results, moderate potential"),
    (0, 0): dict(name="Under Performer", n=1, color="#f9d3d0", desc="Low performance and low potential"),
    (0, 1): dict(name="Risk of Stagnation", n=2, color="#fde2cf", desc="Adequate results, little growth"),
    (0, 2): dict(name="Solid Performer", n=3, color="#fdf0d5", desc="Strong results, limited growth appetite"),
}
BOX_BY_NAME = {v["name"]: (k, v) for k, v in BOXES.items()}
BOX_ORDER = [v["name"] for k, v in sorted(BOXES.items(), key=lambda kv: -kv[1]["n"])]

CAREER_PATHS = {
    "Star": ("Acceleration / promotion",
             ["Put on the succession slate for the next-level roles", "Stretch assignment: lead a full engagement",
              "Executive mentoring with a Partner", "Discuss promotion timing at next calibration"]),
    "High Potential": ("Acceleration (development)",
                       ["Nominate for the Emerging Leaders programme", "Give a team-lead role on next engagement",
                        "Pair with a senior mentor to close delivery gaps"]),
    "High Performer": ("Lateral move to broaden scope",
                       ["Cross-practice rotation (6-12 months) to build breadth", "Lead an internal initiative",
                        "Explore expert / specialist track"]),
    "Rough Diamond": ("Targeted training & coaching",
                      ["Delivery-quality coaching plan (90 days)", "Review role fit and staffing",
                       "Monthly check-ins with clear milestones"]),
    "Core Player": ("Training & skill-building",
                    ["Certification in a core skill for the practice", "Gradually increase scope",
                     "Peer-learning / knowledge-sharing role"]),
    "Solid Performer": ("Lateral move / expert track",
                        ["Recognise as subject-matter expert", "Internal trainer / methodology owner role",
                         "Keep engaged with varied clients"]),
    "Inconsistent Performer": ("Training + performance support",
                               ["Clarify objectives and expectations", "Skills training on gap areas",
                                "Bi-weekly coaching check-ins"]),
    "Risk of Stagnation": ("Lateral move to re-energise",
                           ["Rotation to a new client sector or practice", "New responsibility (e.g. PMO lead)",
                            "Career conversation on long-term goals"]),
    "Under Performer": ("Performance improvement (supported)",
                        ["Structured improvement plan with HR support", "Role-fit review",
                         "Weekly manager check-ins"]),
}


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------
def _conn(db_path=DB_PATH):
    return sqlite3.connect(db_path)


def _dates(df, *cols):
    for c in cols:
        df[c] = pd.to_datetime(df[c]).dt.date
    return df


def load_data(db_path=DB_PATH):
    con = _conn(db_path)
    q = lambda sql: pd.read_sql_query(sql, con)
    emp = _dates(q("SELECT * FROM employees"), "start_date")
    emp["skills"] = emp["skills"].apply(json.loads)
    data = dict(
        employees=emp,
        titles=_dates(q("SELECT * FROM title_history"), "effective_date"),
        reviews=_dates(q("SELECT * FROM reviews ORDER BY review_date"), "review_date"),
        checkins=_dates(q("SELECT * FROM checkins ORDER BY checkin_date, id"), "checkin_date", "scheduled_date"),
        pulses=_dates(q("SELECT * FROM pulses ORDER BY pulse_date"), "pulse_date"),
        personality=_dates(q("SELECT * FROM personality"), "taken_date"),
        survey=_dates(q("SELECT * FROM annual_survey"), "survey_date"),
        vacancies=q("SELECT * FROM vacancies"),
        meta=dict(con.execute("SELECT key, value FROM meta").fetchall()),
    )
    con.close()
    data["vacancies"]["skills"] = data["vacancies"]["skills"].apply(json.loads)
    data["checkins"]["hits"] = data["checkins"]["notes"].apply(nlp.analyse_note)
    data["names"] = dict(zip(emp["id"], emp["name"]))
    data["emp_by_id"] = {r["id"]: r for _, r in emp.iterrows()}
    p = data["pulses"]
    p["engagement_index"] = p.apply(lambda r: engagement_index(r["engagement"], r["workload"], r["sentiment"]), axis=1)
    data["_cache"] = {}
    return data


def today(data):
    return date.fromisoformat(data["meta"]["today"])


def periods(data):
    start = date.fromisoformat(data["meta"]["window_start"])
    end = today(data)
    out, y, m = [], start.year, start.month
    while date(y, m, 1) < end:
        out.append(f"{y}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def period_end(period):
    y, m = map(int, period.split("-"))
    return date(y, m, calendar.monthrange(y, m)[1])


def period_label(period):
    y, m = map(int, period.split("-"))
    return date(y, m, 1).strftime("%b %Y")


def quarter_periods(data, as_of):
    return [p for p in periods(data) if p.endswith(("-03", "-06", "-09", "-12")) and period_end(p) <= as_of]


def quarter_label(period):
    y, m = map(int, period.split("-"))
    return f"Q{(m - 1) // 3 + 1} {y}"


def is_active(emp, as_of):
    return emp["start_date"] <= as_of


def tenure_days(emp, as_of):
    return (as_of - emp["start_date"]).days


def tenure_label(emp, as_of):
    days = tenure_days(emp, as_of)
    if days < 0:
        return "not yet joined"
    if days < 90:
        return f"{days} days"
    months = days // 30.44
    if months < 24:
        return f"{int(months)} months"
    return f"{days / 365.25:.1f} years"


def tenure_band(emp, as_of):
    days = tenure_days(emp, as_of)
    if days < 90:
        return "New hire (<90 days)"
    if days < 730:
        return "Early-career"
    if days < 8 * 365:
        return "Mid-tenure"
    return "Senior / long tenure"


def title_on(data, emp_id, as_of):
    t = data["titles"]
    t = t[(t["emp_id"] == emp_id) & (t["effective_date"] <= as_of)].sort_values("effective_date")
    if t.empty:
        return data["emp_by_id"][emp_id]["title"], data["emp_by_id"][emp_id]["level"], None
    last = t.iloc[-1]
    return last["title"], int(last["level"]), last["effective_date"]


def _clip(x, lo=0.0, hi=100.0):
    return float(max(lo, min(hi, x)))


def _scale(v, lo, hi):
    return _clip((v - lo) / (hi - lo) * 100.0)


# ---------------------------------------------------------------------------
# Notes & AI summary
# ---------------------------------------------------------------------------
def notes_until(data, emp_id, as_of):
    c = data["checkins"]
    c = c[(c["emp_id"] == emp_id) & (c["checkin_date"] <= as_of)]
    r = data["reviews"]
    r = r[(r["emp_id"] == emp_id) & (r["review_date"] <= as_of)]
    return c, r


def ai_summary(data, emp_id, as_of, max_notes=6):
    c, r = notes_until(data, emp_id, as_of)
    notes = [dict(date=row["checkin_date"], kind=row["kind"], text=row["notes"], hits=row["hits"])
             for _, row in c.iterrows()]
    if not r.empty:
        last = r.iloc[-1]
        notes.append(dict(date=last["review_date"], kind="Annual review", text=last["notes"],
                          hits=nlp.analyse_note(last["notes"])))
    notes = sorted(notes, key=lambda n: n["date"])[-max_notes:]
    first = data["names"][emp_id].split()[0]
    out = nlp.summarise(first, notes)
    out["notes"] = notes
    return out


# ---------------------------------------------------------------------------
# 9-box placement
# ---------------------------------------------------------------------------
def band(score):
    return 0 if score < BAND_LOW else (1 if score < BAND_HIGH else 2)


def box_for(perf, pot):
    return BOXES[(band(pot), band(perf))]["name"]


def _component(name, weight, score, source):
    return dict(component=name, weight=weight, score=round(score, 1), contribution=round(weight * score, 1),
                source=source)


def placement(data, emp_id, as_of):
    key = ("placement", emp_id, as_of, data.get("_version", 0))
    if key in data["_cache"]:
        return data["_cache"][key]
    emp = data["emp_by_id"][emp_id]
    c, r = notes_until(data, emp_id, as_of)

    # --- Check-in sentiment (AI): last two notes, 60/40 recency weighting
    recent = c.tail(2)
    if recent.empty:
        sent, sent_src = 50.0, "No check-in yet — neutral 50"
    else:
        idx = [nlp.sentiment_index(h) for h in recent["hits"]]
        sent = idx[0] if len(idx) == 1 else 0.4 * idx[0] + 0.6 * idx[1]
        sent_src = f"AI tone of last {len(idx)} manager note(s): " + ", ".join(f"{v:.0f}" for v in idx)

    perf_comp, provisional = [], False
    if not r.empty:
        last = r.iloc[-1]
        rating = (last["rating"] - 1) / 4 * 100
        if len(r) > 1:
            prev = r.iloc[-2]
            rating = 0.7 * rating + 0.3 * (prev["rating"] - 1) / 4 * 100
            rsrc = f"{last['rating']}/5 ({last['review_date'].year}) blended 70/30 with {prev['rating']}/5"
        else:
            rsrc = f"{last['rating']}/5 ({last['review_date'].year}) — first annual review"
        obj = _scale(last["objectives_pct"], 50, 110)
        perf_comp = [
            _component("Annual review rating", PERF_WEIGHTS["Annual review rating"], rating, rsrc),
            _component("Objectives achieved", PERF_WEIGHTS["Objectives achieved"], obj,
                       f"{last['objectives_pct']:.0f}% of objectives (50% → 0, 110% → 100)"),
            _component("Check-in sentiment (AI)", PERF_WEIGHTS["Check-in sentiment (AI)"], sent, sent_src),
        ]
    else:
        provisional = True
        ob = c[c["ramp_up"].notna()]
        if ob.empty:
            ramp, rsrc = 50.0, "No onboarding rating yet — neutral 50"
        else:
            v = ob.iloc[-1]["ramp_up"]
            ramp, rsrc = (v - 1) / 4 * 100, f"Ramp-up {v}/5 at {ob.iloc[-1]['kind'].lower()} check-in"
        perf_comp = [
            _component("Ramp-up speed (onboarding)", PERF_WEIGHTS_NEW["Ramp-up speed (onboarding)"], ramp, rsrc),
            _component("Check-in sentiment (AI)", PERF_WEIGHTS_NEW["Check-in sentiment (AI)"], sent, sent_src),
        ]
    perf = sum(x["contribution"] for x in perf_comp)
    perf_raw = perf
    if provisional:
        perf = 50 + PROVISIONAL_SHRINK * (perf - 50)

    # --- Potential
    last4 = c.tail(4)
    hits4 = [h for hs in last4["hits"] for h in hs]
    sig = nlp.signal_index(hits4, "potential")
    if not r.empty:
        pr = r.iloc[-1]["potential_rating"]
        mf = 0.6 * (pr - 1) / 4 * 100 + 0.4 * sig
        mf_src = f"Manager potential rating {pr}/5 (60%) + AI leadership/learning/ambition signals {sig:.0f} (40%)"
    else:
        mf = sig
        mf_src = f"No review yet — AI leadership/learning/ambition signals only ({sig:.0f})"

    s = data["survey"]
    s = s[(s["emp_id"] == emp_id) & (s["survey_date"] <= as_of)]
    mob_sig = sum(h["polarity"] for h in hits4 if h["theme"] == "mobility")
    if s.empty:
        mob = _clip(50 + 15 * mob_sig)
        mob_src = "Annual survey not yet answered — neutral 50" + (" ± check-in mobility mentions" if mob_sig else "")
    else:
        sv = s.iloc[-1]
        asp_pts = {"Partner track": 35, "Director track": 35, "Move into management": 35,
                   "Move to another practice": 35, "Undecided": 15, "Deepen expertise in current role": 10}
        mob = _clip(50 * sv["open_to_mobility"] + asp_pts.get(sv["aspiration"], 15) + 15 * mob_sig)
        mob_src = (f"Survey: {'open' if sv['open_to_mobility'] else 'not open'} to mobility, aspiration "
                   f"“{sv['aspiration']}”" + (f"; check-in mobility signal {mob_sig:+d}" if mob_sig else ""))

    skills = emp["skills"]
    transferable = [x for x in skills if x in TRANSFERABLE]
    ts = _clip(15 * len(transferable) + 5 * (len(skills) - len(transferable)) + 10)
    ts_src = f"{len(transferable)} transferable of {len(skills)} skills ({', '.join(transferable) or 'none'})"

    title, level, since = title_on(data, emp_id, as_of)
    days = tenure_days(emp, as_of)
    if days < 365:
        tp, tp_src = 60.0, "Under 1 year tenure — neutral 60"
    else:
        yrs = (as_of - since).days / 365.25 if since else days / 365.25
        tp = _clip(100 - 15 * max(0.0, yrs - 1.5), 10)
        tp_src = f"{yrs:.1f} years since last promotion/role change (–15 pts per year beyond 1.5)"

    pers = data["personality"]
    pers = pers[(pers["emp_id"] == emp_id) & (pers["taken_date"] <= as_of)]
    if pers.empty:
        la, la_src = 50.0, "Personality test not yet taken — neutral 50"
    else:
        la, la_src = float(pers.iloc[0]["openness"]), f"Big Five openness = {pers.iloc[0]['openness']}"

    pot_comp = [
        _component("Manager feedback", POT_WEIGHTS["Manager feedback"], mf, mf_src),
        _component("Transferable skills", POT_WEIGHTS["Transferable skills"], ts, ts_src),
        _component("Desired mobility", POT_WEIGHTS["Desired mobility"], mob, mob_src),
        _component("Tenure & progression", POT_WEIGHTS["Tenure & progression"], tp, tp_src),
        _component("Learning agility (Big Five openness)", POT_WEIGHTS["Learning agility (Big Five openness)"], la,
                   la_src),
    ]
    pot = sum(x["contribution"] for x in pot_comp)
    out = dict(emp_id=emp_id, perf=round(perf, 1), perf_raw=round(perf_raw, 1), pot=round(pot, 1), box=box_for(perf, pot),
               perf_band=BAND_NAMES[band(perf)], pot_band=BAND_NAMES[band(pot)], provisional=provisional,
               perf_components=perf_comp, pot_components=pot_comp, title=title, level=level)
    data["_cache"][key] = out
    return out


def box_history(data, emp_id, as_of):
    emp = data["emp_by_id"][emp_id]
    rows = []
    for p in quarter_periods(data, as_of):
        pe = period_end(p)
        if not is_active(emp, pe):
            continue
        pl = placement(data, emp_id, pe)
        rows.append(dict(quarter=quarter_label(p), period=p, perf=pl["perf"], pot=pl["pot"], box=pl["box"],
                         provisional=pl["provisional"]))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Engagement & risk
# ---------------------------------------------------------------------------
def engagement_index(eng, workload, sentiment):
    """0-100. Engagement 50%, sentiment 30%, workload balance 20% (6/10 workload is healthy)."""
    e = (eng - 1) / 9 * 100
    s = (sentiment - 1) / 9 * 100
    wl = _clip(100 - 25 * max(0.0, workload - 6) - 10 * max(0.0, 4 - workload))
    return round(0.5 * e + 0.3 * s + 0.2 * wl, 1)


def engagement_series(data, emp_id, as_of):
    p = data["pulses"]
    return p[(p["emp_id"] == emp_id) & (p["pulse_date"] <= as_of)].copy()


def trend(series, window=6):
    s = series.tail(window)
    if len(s) < 4:
        return 0.0, "Too early"
    y = s["engagement_index"].to_numpy()
    slope = float(np.polyfit(np.arange(len(y)), y, 1)[0])
    label = "Improving" if slope > 1.5 else ("Declining" if slope < -1.5 else "Stable")
    return round(slope, 2), label


def risk(data, emp_id, as_of):
    key = ("risk", emp_id, as_of, data.get("_version", 0))
    if key in data["_cache"]:
        return data["_cache"][key]
    emp = data["emp_by_id"][emp_id]
    ser = engagement_series(data, emp_id, as_of)
    c, _ = notes_until(data, emp_id, as_of)
    slope, tlabel = trend(ser)
    latest_e = float(ser["engagement_index"].tail(3).mean()) if not ser.empty else None

    if tenure_days(emp, as_of) <= 90:
        ob = c[c["kind"].str.startswith("Onboarding")]
        if ob.empty:
            gap, ramp = 50.0, 50.0
            gsrc = rsrc = "No onboarding check-in yet — neutral 50"
        else:
            last = ob.iloc[-1]
            gap, gsrc = last["expectation_gap"] * 10, f"Gap {last['expectation_gap']}/10 at {last['kind'].lower()}"
            ramp, rsrc = (5 - last["ramp_up"]) / 4 * 100, f"Ramp-up {last['ramp_up']}/5"
        # 30/60/90 compliance
        cc_vals, cc_notes = [], []
        for k, days in ((30, 30), (60, 60), (90, 90)):
            sched = emp["start_date"] + timedelta(days=days)
            if sched > as_of:
                continue
            done = ob[ob["kind"] == f"Onboarding {k}-day"]
            if done.empty:
                if as_of > sched + timedelta(days=7):
                    cc_vals.append(100.0)
                    cc_notes.append(f"{k}-day missing")
                else:
                    cc_vals.append(0.0)
            else:
                late = (done.iloc[0]["checkin_date"] - sched).days
                cc_vals.append(60.0 if late > 5 else 0.0)
                cc_notes.append(f"{k}-day {'held ' + str(late) + ' days late' if late > 5 else 'on time'}")
        cc = float(np.mean(cc_vals)) if cc_vals else 0.0
        pe = 100 - latest_e if latest_e is not None else 50.0
        comps = [
            _component("Expectation-vs-reality gap", ONBOARD_WEIGHTS["Expectation-vs-reality gap"], gap, gsrc),
            _component("Slow ramp-up", ONBOARD_WEIGHTS["Slow ramp-up"], ramp, rsrc),
            _component("Early pulse engagement", ONBOARD_WEIGHTS["Early pulse engagement"], pe,
                       f"Avg engagement index {latest_e:.0f}/100" if latest_e is not None else "No pulse yet"),
            _component("Missed / late 30-60-90 check-ins", ONBOARD_WEIGHTS["Missed / late 30-60-90 check-ins"], cc,
                       "; ".join(cc_notes) or "None due yet"),
        ]
        score = sum(x["contribution"] for x in comps)
        level = "High" if score >= ONBOARD_HIGH else ("Medium" if score >= ONBOARD_MED else "Low")
        out = dict(model="Onboarding risk", score=round(score, 1), level=level, components=comps,
                   trend=tlabel, slope=slope, engagement=latest_e)
    else:
        low = 100 - latest_e if latest_e is not None else 50.0
        dec = _clip(-slope * 12)
        s = data["survey"]
        s = s[(s["emp_id"] == emp_id) & (s["survey_date"] <= as_of)]
        if s.empty:
            stay, ssrc = 50.0, "Annual survey not answered yet — neutral 50"
        else:
            v = s.iloc[-1]["intent_to_stay"]
            stay, ssrc = (5 - v) / 4 * 100, f"Intent to stay {v}/5 (Feb survey)"
        recent_hits = [h for hs in c.tail(2)["hits"] for h in hs]
        warn = [h for h in recent_hits if h["group"] == "wellbeing" and h["polarity"] < 0]
        w = _clip(35 * len(warn))
        comps = [
            _component("Low current engagement", FLIGHT_WEIGHTS["Low current engagement"], low,
                       f"Avg engagement index (last 3 pulses) {latest_e:.0f}/100" if latest_e is not None else "No pulse"),
            _component("Declining trend", FLIGHT_WEIGHTS["Declining trend"], dec,
                       f"Slope {slope:+.1f} pts/month over last 6 pulses ({tlabel.lower()})"),
            _component("Low intent to stay (survey)", FLIGHT_WEIGHTS["Low intent to stay (survey)"], stay, ssrc),
            _component("Warning signs in check-ins (AI)", FLIGHT_WEIGHTS["Warning signs in check-ins (AI)"], w,
                       f"{len(warn)} motivation/workload warning(s) in last 2 notes" if warn else "None in last 2 notes"),
        ]
        score = sum(x["contribution"] for x in comps)
        level = "High" if score >= RISK_HIGH else ("Medium" if score >= RISK_MED else "Low")
        out = dict(model="Flight risk", score=round(score, 1), level=level, components=comps, trend=tlabel,
                   slope=slope, engagement=latest_e)
    data["_cache"][key] = out
    return out


# ---------------------------------------------------------------------------
# Career paths
# ---------------------------------------------------------------------------
def career_suggestion(data, emp_id, as_of, box=None):
    pl = placement(data, emp_id, as_of)
    box = box or pl["box"]
    kind, actions = CAREER_PATHS[box]
    actions = list(actions)
    rk = risk(data, emp_id, as_of)
    rationale = f"Based on the **{box}** cell (performance {pl['perf']:.0f}, potential {pl['pot']:.0f})."
    if rk["level"] == "High":
        actions.insert(0, "Hold a stay / onboarding conversation before any move — risk signal is High")
        rationale += f" {rk['model']} is **High**, so a retention step comes first."
    if pl["provisional"]:
        rationale += " Placement is provisional (no annual review yet) — revisit after the first review."
    return dict(kind=kind, actions=actions, rationale=rationale, box=box)


# ---------------------------------------------------------------------------
# Succession
# ---------------------------------------------------------------------------
BOX_WEIGHT = {"Star": 1.0, "High Potential": 0.9, "High Performer": 0.8, "Rough Diamond": 0.55, "Core Player": 0.55,
              "Solid Performer": 0.5, "Inconsistent Performer": 0.25, "Risk of Stagnation": 0.2,
              "Under Performer": 0.05}
ASPIRATION_UP = {"Partner track", "Director track", "Move into management"}


def succession(data, vacancy, as_of, effective_boxes=None):
    rows = []
    for _, emp in data["employees"].iterrows():
        if not is_active(emp, as_of):
            continue
        pl = placement(data, emp["id"], as_of)
        box = (effective_boxes or {}).get(emp["id"], pl["box"])
        lvl = pl["level"]
        gap = vacancy["level"] - lvl
        if gap < 0 or gap > 2:
            continue
        if gap == 0 and emp["practice"] == vacancy["practice"]:
            continue  # same grade, same practice: not a career move
        rk = risk(data, emp["id"], as_of)
        eligible, note = True, ""
        if tenure_days(emp, as_of) < 180:
            eligible, note = False, "Not eligible: under 6 months tenure (still onboarding)"
        readiness = {1: 1.0, 0: 0.45, 2: 0.35}[gap]
        req = set(vacancy["skills"])
        have = set(emp["skills"])
        matched = sorted(req & have)
        skills = len(matched) / len(req)
        s = data["survey"]
        s = s[(s["emp_id"] == emp["id"]) & (s["survey_date"] <= as_of)]
        fit = 0.5
        if not s.empty:
            sv = s.iloc[-1]
            fit = 0.35 * sv["open_to_mobility"] + (0.4 if (sv["aspiration"] in ASPIRATION_UP and gap >= 1) else 0.15)
        if emp["practice"] == vacancy["practice"]:
            fit += 0.25
        elif not s.empty and s.iloc[-1]["open_to_mobility"]:
            fit += 0.1
        fit = min(1.0, fit)
        parts = {"9-box position": BOX_WEIGHT[box], "Skills match": skills, "Readiness (level gap)": readiness,
                 "Aspiration & mobility fit": fit}
        score = 100 * sum(SUCCESSION_WEIGHTS[k] * v for k, v in parts.items())
        if gap == 0:
            ready = "Lateral move"
        elif gap == 1:
            ready = "Ready now" if box in ("Star", "High Performer") else "Ready in 12-18 months"
        else:
            ready = "Ready in 2+ years"
        why = [f"{box} ({pl['perf']:.0f} perf / {pl['pot']:.0f} pot)",
               f"{len(matched)}/{len(req)} required skills" + (f" ({', '.join(matched)})" if matched else ""),
               f"currently {pl['title']} in {emp['practice']}"]
        if not s.empty:
            why.append(f"aspiration: {s.iloc[-1]['aspiration'].lower()}")
        flags = []
        if rk["level"] == "High":
            flags.append(f"{rk['model']} High — at risk of leaving: offering this role could help keep them. "
                         "Talk to them before deciding")
        elif rk["level"] == "Medium":
            flags.append(f"{rk['model']} Medium")
        if pl["provisional"]:
            flags.append("Provisional placement (no annual review yet)")
        if note:
            flags.append(note)
        rows.append(dict(emp_id=emp["id"], name=emp["name"], title=pl["title"], practice=emp["practice"], box=box,
                         score=round(score, 1) if eligible else 0.0, raw_score=round(score, 1), eligible=eligible,
                         readiness=ready, rationale="; ".join(why), flags=" · ".join(flags),
                         **{k: round(v * 100) for k, v in parts.items()}))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["eligible", "score"], ascending=[False, False]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Decisions (human-in-the-loop log)
# ---------------------------------------------------------------------------
def decisions(db_path=DB_PATH):
    con = _conn(db_path)
    df = pd.read_sql_query("SELECT * FROM decisions ORDER BY ts DESC, id DESC", con)
    con.close()
    return df


def log_decision(actor, actor_role, kind, emp_id=None, vacancy_id=None, period=None, algo_value=None,
                 final_value=None, status=None, reason=None, db_path=DB_PATH):
    con = _conn(db_path)
    con.execute("INSERT INTO decisions (ts, actor, actor_role, kind, emp_id, vacancy_id, period, algo_value, "
                "final_value, status, reason) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), actor, actor_role, kind, emp_id, vacancy_id, period,
                 algo_value, final_value, status, reason))
    con.commit()
    con.close()


def latest_decision(dec, kind, emp_id=None, period=None, vacancy_id=None):
    d = dec[dec["kind"] == kind]
    if emp_id is not None:
        d = d[d["emp_id"] == emp_id]
    if period is not None:
        d = d[d["period"] == period]
    if vacancy_id is not None:
        d = d[d["vacancy_id"] == vacancy_id]
    return None if d.empty else d.iloc[0]


def add_checkin(emp_id, when, author, text, db_path=DB_PATH):
    con = _conn(db_path)
    con.execute("INSERT INTO checkins (emp_id, checkin_date, kind, scheduled_date, author, notes, ramp_up, "
                "expectation_gap, source) VALUES (?,?,?,?,?,?,?,?,?)",
                (emp_id, when.isoformat(), "Ad-hoc check-in", when.isoformat(), author, text, None, None, "live demo"))
    con.commit()
    con.close()
