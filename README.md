# Level UP — AI-assisted employee trajectories (prototype)

A working prototype of an HR talent-management tool for **Northvale Consulting**, a fictional 250-person consulting
firm with four practices: Strategy, HR Consulting, Finance & Transactions, and Operations. It follows a pilot cohort
of 18 fictional employees over a simulated 12-month timeline (Oct 2025 → Sep 2026).

**Core principle: the algorithm proposes, people decide.** Every 9-box placement, risk flag, succession ranking and
career suggestion must be confirmed by a manager or HR, and each decision is logged next to the algorithm's
proposal.

All names, companies and data are fictional.

---

## How to run it (about 2 minutes)

You need **Python 3.9 or newer**.

```bash
# 1. Open a terminal in this folder, then create a virtual environment
python3 -m venv .venv

# 2. Install the dependencies
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip install -r requirements.txt

# 3. Start the app
.venv/bin/streamlit run app.py                   # Windows: .venv\Scripts\streamlit run app.py
```

The app opens in your browser at **http://localhost:8501**. On first launch it generates the fictional database
automatically (`data/levelup.db`).

To restore the original data at any time, use **Settings → Reset demo data** in the sidebar, or run
`python seed.py`.

---

## What to look at

On the welcome screen, enter as **HR** (Ibrahima Camara) or as **Manager** (Magnus Aasted).

| Page | What it shows |
|---|---|
| **Overview** (HR) | Risk flags to act on, engagement trend by practice, 9-box distribution |
| **9-box** (HR) | Automatic performance × potential placement for every employee, with validation status |
| **My team** (Manager) | Team 9-box, validation queue, team risk flags |
| **Profiles** | Per-employee page: animated 9-box trajectory, transparent score breakdown, AI summary of manager notes, review history, engagement trend, career-path suggestion, survey answers, onboarding 30/60/90 tracking, PDF talent-card export |
| **Succession** (HR) | Ranked internal candidates for 3 vacant roles, with rationale and readiness |
| **Engagement** (HR) | Monthly engagement heatmap and trends (improving / stable / declining) |
| **Surveys** | The questionnaires employees receive (monthly pulse, onboarding, annual survey, Big Five), how each answer feeds the model, and live "try it" simulators |
| **Decisions** | Audit trail of every human decision, plus a **calibration** view comparing managers' overrides |
| **Method & ethics** | Every weight and threshold of the model, plus GDPR / EU AI Act considerations and a live bias check |

The **timeline slider** in the sidebar replays the year: scores, boxes and trends recompute from the data available
at each date.

## Suggested 5-minute walkthrough

1. **Welcome → Enter as HR.** On **Overview**, two employees have a high flight risk (Elena, Ryan) and one new hire
   is flagged by the onboarding model (Zara). Log an action on Elena's flag.
2. **Timeline:** drag the slider back to Mar 2026 and then forward to Sep 2026. The alerts appear as engagement
   declines.
3. **9-box:** all nine cells are filled. A gold dot means the placement is still awaiting manager validation.
4. **Switch to Manager (Magnus Aasted) → My team.** Confirm Julien's placement, then open Elena and click
   **▶ Replay trajectory**. Use **Adjust placement** to override her box (a written reason is required).
5. **Back to HR → Succession → Manager — HR Consulting.** Candidates are ranked with explanations. Elena's flight risk
   turns the promotion into a possible retention lever. Shortlist one candidate.
6. **Surveys → Monthly pulse → Try it live:** move the sliders to see how answers become the engagement index.
7. **Decisions → Calibration**, then **Method & ethics → Ethics & GDPR.**

## Project structure

| File | Role |
|---|---|
| `app.py` | Streamlit interface (HR and Manager views) |
| `engine.py` | Scoring model: 9-box, engagement index & trend, flight / onboarding risk, career paths, succession matching, decision log |
| `nlp.py` | Simulated LLM step: extracts themes from manager notes (with evidence sentences) and writes the AI summary |
| `seed.py` | Generates the reproducible fictional dataset (SQLite) |
| `report.py` | One-page PDF talent card |
| `.streamlit/config.toml` | Visual theme |

## Notes and limitations

- **The AI summary is simulated.** It uses transparent theme extraction from a keyword lexicon. In production this
  step would call a large language model with a fixed output format; it was kept deterministic here so results are
  reproducible.
- **The weights are working hypotheses,** to be calibrated on real data.
- **The Big Five questionnaire is illustrative,** written for this demo rather than a validated instrument.
- **The regulatory section is framing for discussion,** not legal advice.
