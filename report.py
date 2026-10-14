"""One-page "talent card" PDF for an employee (used by the Export button on the profile page)."""
from datetime import date

from fpdf import FPDF

import engine

EMERALD = (31, 138, 91)
DEEP = (11, 36, 26)
SILVER = (120, 135, 128)
INK = (25, 30, 28)
LIGHT = (236, 243, 239)

_REPL = {"—": "-", "–": "-", "→": "->", "×": "x", "“": '"', "”": '"', "’": "'", "‘": "'", "≤": "<=", "≥": ">=",
         "·": "-", "…": "...", "▲": "+", "▼": "-", "■": "=", "↗": "^", "€": "EUR", "✓": "v"}


def clean(text):
    text = str(text)
    for k, v in _REPL.items():
        text = text.replace(k, v)
    return text.replace("**", "").encode("latin-1", "replace").decode("latin-1")


class Card(FPDF):
    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*SILVER)
        self.cell(0, 5, clean(f"Level UP - Northvale Consulting (fictional data) - generated {date.today():%d %b %Y}. "
                              "Algorithmic proposals require manager / HR validation."), align="C")


def _section(pdf, title):
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*EMERALD)
    pdf.cell(0, 6, clean(title.upper()), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*EMERALD)
    pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(2)


def _table(pdf, rows, widths, header=None, size=8.5):
    pdf.set_font("Helvetica", "B", size)
    if header:
        pdf.set_fill_color(*LIGHT)
        pdf.set_text_color(*INK)
        for h, w in zip(header, widths):
            pdf.cell(w, 6, clean(h), border=0, fill=True)
        pdf.ln()
    pdf.set_font("Helvetica", "", size)
    for row in rows:
        y0 = pdf.get_y()
        x0 = pdf.l_margin
        heights = []
        for i, (val, w) in enumerate(zip(row, widths)):
            pdf.set_xy(x0 + sum(widths[:i]), y0)
            pdf.multi_cell(w, 4.6, clean(val), new_x="RIGHT", new_y="TOP", align="L")
        # compute row height from the tallest cell
        for val, w in zip(row, widths):
            lines = pdf.multi_cell(w, 4.6, clean(val), dry_run=True, output="LINES", align="L")
            heights.append(len(lines) * 4.6)
        pdf.set_xy(x0, y0 + max(heights) + 1)
        pdf.set_draw_color(225, 230, 227)
        pdf.line(x0, pdf.get_y() - 0.5, pdf.w - pdf.r_margin, pdf.get_y() - 0.5)


def talent_card(data, emp_id, as_of, row, summary, suggestion):
    emp, pl, rk = row["emp"], row["pl"], row["rk"]
    mgr = data["names"].get(emp["manager_id"]) or emp["manager_ext"]
    pdf = Card(format="A4")
    pdf.set_auto_page_break(True, margin=16)
    pdf.add_page()

    # Header band
    pdf.set_fill_color(*DEEP)
    pdf.rect(0, 0, pdf.w, 38, "F")
    pdf.set_fill_color(*EMERALD)
    pdf.rect(0, 38, pdf.w, 1.2, "F")
    pdf.set_xy(14, 8)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(127, 227, 180)
    pdf.cell(0, 4, clean(f"LEVEL UP - TALENT CARD - DATA AS OF {as_of:%d %b %Y}".upper()), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(14)
    pdf.set_font("Times", "B", 22)
    pdf.set_text_color(242, 246, 244)
    pdf.cell(0, 11, clean(emp["name"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(199, 208, 203)
    pdf.cell(0, 5, clean(f"{pl['title']} - {emp['practice']} - reports to {mgr} - joined {emp['start_date']:%d %b %Y} "
                         f"({engine.tenure_label(emp, as_of)})"))
    pdf.set_y(44)

    # Key figures
    status = {"pending": "Awaiting manager validation", "confirmed": f"Confirmed by {row['actor']}",
              "overridden": f"Adjusted by {row['actor']}"}.get(row["status"], row["status"])
    tiles = [("9-BOX (FINAL)", row["box"]), ("PERFORMANCE", f"{pl['perf']:.0f}/100 ({pl['perf_band']})"),
             ("POTENTIAL", f"{pl['pot']:.0f}/100 ({pl['pot_band']})"),
             (rk["model"].upper(), f"{rk['score']:.0f}/100 ({rk['level']})")]
    w = (pdf.w - 28 - 9) / 4
    y = pdf.get_y()
    for i, (k, v) in enumerate(tiles):
        x = 14 + i * (w + 3)
        pdf.set_fill_color(*LIGHT)
        pdf.rect(x, y, w, 17, "F")
        pdf.set_xy(x + 3, y + 2.5)
        pdf.set_font("Helvetica", "B", 6.8)
        pdf.set_text_color(*SILVER)
        pdf.cell(w - 6, 4, clean(k))
        pdf.set_xy(x + 3, y + 7.5)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(*INK)
        pdf.cell(w - 6, 6, clean(v))
    pdf.set_y(y + 20)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*SILVER)
    extra = f" Algorithm proposed: {pl['box']}." if row["box"] != pl["box"] else ""
    pdf.multi_cell(0, 4.5, clean(f"Validation status: {status}.{extra}"
                                 + (f' Reason: "{row["reason"]}"' if row.get("reason") and row["status"] != "pending" else "")
                                 + (" Provisional placement (no annual review yet)." if pl["provisional"] else "")))

    _section(pdf, "AI summary of manager notes")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*INK)
    pdf.multi_cell(0, 5, clean(summary["text"]))

    _section(pdf, "Suggested career path - " + suggestion["kind"])
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*INK)
    pdf.multi_cell(0, 5, clean(suggestion["rationale"]))
    for a in suggestion["actions"]:
        pdf.set_x(pdf.l_margin + 3)
        pdf.multi_cell(0, 5, clean(f"- {a}"))

    for title, comps, total in (("Performance score", pl["perf_components"], pl["perf_raw"]),
                                ("Potential score", pl["pot_components"], pl["pot"]),
                                (rk["model"], rk["components"], rk["score"])):
        _section(pdf, f"{title} - {total:.1f}")
        _table(pdf, [(c["component"], f"{c['weight']:.0%}", f"{c['score']:.0f}", f"{c['contribution']:.1f}", c["source"])
                     for c in comps], [48, 14, 14, 14, pdf.w - 28 - 90],
               header=["Component", "Weight", "Score", "Points", "Source"])

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*SILVER)
    pdf.multi_cell(0, 4.2, clean("Confidential - for talent review only. Level UP proposes; managers and HR decide. "
                                 "Scores are weighted sums of the components above; see the Methodology page."))
    return bytes(pdf.output())
