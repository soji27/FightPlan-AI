"""
PDF Game Plan Generator for FightPlan AI.
Generates a structured PDF tactical analysis document using FPDF2.
"""

import os
from datetime import datetime
from typing import Any, Dict

from fpdf import FPDF


class GamePlanPDF(FPDF):
    """Custom PDF class with header and footer."""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_fill_color(30, 30, 30)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "FightPlan AI - Game Plan Tactique", border=0, align="C", fill=True)
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 10, f"Généré par FightPlan AI le {date_str} | Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        """Add a styled section title."""
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(220, 50, 50)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, border=0, align="L", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def body_text(self, text: str):
        """Add body text with word wrap."""
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def stat_row(self, label: str, value: str):
        """Add a label-value pair row."""
        self.set_font("Helvetica", "B", 10)
        self.cell(70, 7, f"  {label}:", border=0)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 7, str(value), border=0, new_x="LMARGIN", new_y="NEXT")

    def weakness_item(self, text: str):
        """Add a weakness bullet point."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(180, 0, 0)
        self.cell(10, 6, "  -")
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)


def generate_game_plan(fighter_name: str, analysis: Dict[str, Any], output_dir: str) -> str:
    """Generate a PDF tactical game plan for a fighter.

    Args:
        fighter_name: Name of the fighter being analyzed.
        analysis: Dict from StatsAnalyzer containing profile, record, striking, grappling data.
        output_dir: Directory where the PDF should be saved.

    Returns:
        Absolute path to the generated PDF file.
    """
    os.makedirs(output_dir, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in fighter_name)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gameplan_{safe_name.replace(' ', '_')}_{date_str}.pdf"
    output_path = os.path.join(output_dir, filename)

    pdf = GamePlanPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Title ──────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.ln(4)
    pdf.cell(0, 12, f"Game Plan: {fighter_name}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Section 1: Fighter Profile ─────────────────────────────────────────
    pdf.section_title("1. Profil du Fighter")

    profile = analysis.get("profile", {})
    record = analysis.get("record", {})

    if profile:
        pdf.stat_row("Catégorie de poids", str(profile.get("weight_class", "N/A")))
        pdf.stat_row("Taille", f"{profile.get('height_cms', 'N/A')} cm")
        pdf.stat_row("Allonge", f"{profile.get('reach_cms', 'N/A')} cm")
        pdf.stat_row("Poids", f"{profile.get('weight_lbs', 'N/A')} lbs")
        pdf.stat_row("Garde", str(profile.get("stance", "N/A")))
        pdf.stat_row("Âge", str(profile.get("age", "N/A")))

    if record:
        pdf.ln(2)
        pdf.stat_row("Bilan", f"{record.get('wins', 0)}V - {record.get('losses', 0)}D")
        pdf.stat_row("Combats totaux", str(record.get("total_fights", 0)))
        pdf.stat_row("Série de victoires", str(record.get("current_win_streak", 0)))

    pdf.ln(4)

    # ── Section 2: Detected Weaknesses ─────────────────────────────────────
    pdf.section_title("2. Failles Détectées")

    weaknesses = analysis.get("weaknesses", [])
    if weaknesses:
        for weakness in weaknesses:
            pdf.weakness_item(weakness)
    else:
        # Auto-detect from stats
        striking = analysis.get("striking", {})
        grappling = analysis.get("grappling", {})
        auto_weaknesses = []

        sig_pct = striking.get("avg_sig_str_accuracy_pct", 0)
        try:
            if float(sig_pct) < 0.40:
                auto_weaknesses.append(
                    f"Précision des frappes significatives faible ({float(sig_pct):.1%}) "
                    f"[source: ufc_data.csv, données agrégées]"
                )
        except (TypeError, ValueError):
            pass

        td_pct = grappling.get("avg_td_accuracy_pct", 0)
        try:
            if float(td_pct) < 0.35:
                auto_weaknesses.append(
                    f"Faible taux de réussite des takedowns ({float(td_pct):.1%}) — "
                    f"vulnérable aux sprawls [source: ufc_data.csv, données agrégées]"
                )
        except (TypeError, ValueError):
            pass

        ctrl = grappling.get("avg_ctrl_time_seconds", 0)
        try:
            if float(ctrl) < 30:
                auto_weaknesses.append(
                    f"Temps de contrôle au sol limité ({float(ctrl):.0f}s en moyenne) — "
                    f"dominance grappling limitée [source: ufc_data.csv, données agrégées]"
                )
        except (TypeError, ValueError):
            pass

        kd = striking.get("avg_knockdowns", 0)
        try:
            if float(kd) < 0.1:
                auto_weaknesses.append(
                    f"Peu de knockdowns marqués ({float(kd):.2f} en moyenne) — "
                    f"menace KO limitée [source: ufc_data.csv, données agrégées]"
                )
        except (TypeError, ValueError):
            pass

        if auto_weaknesses:
            for aw in auto_weaknesses:
                pdf.weakness_item(aw)
        else:
            pdf.body_text("Aucune faille majeure identifiée dans les données disponibles.")

    pdf.ln(4)

    # ── Section 3: Recommended Strategy ────────────────────────────────────
    pdf.section_title("3. Stratégie Recommandée")

    patterns = analysis.get("patterns", {})
    style = patterns.get("style", "Mixed Style")
    striking_score = patterns.get("striking_score", 0)
    grappling_score = patterns.get("grappling_score", 0)

    strategies = []

    if "Grappler" in style:
        strategies.append(
            "Adversaire: Maintenir la distance pour éviter les takedowns. "
            "Utiliser des strikes défensifs et pratiquer un sprawl actif."
        )
        strategies.append(
            f"Le combattant est principalement grappleur (score grappling: {grappling_score:.1f} vs striking: {striking_score:.1f}). "
            "Exploiter les opportunités de contre-frappe debout."
        )
    elif "Striker" in style:
        strategies.append(
            "Adversaire: Chercher les clinch et les projections pour neutraliser le jeu debout. "
            "Amener le combat au sol si possible."
        )
        strategies.append(
            f"Le combattant est principalement frappeur (score striking: {striking_score:.1f} vs grappling: {grappling_score:.1f}). "
            "Exploiter le manque de défense au sol."
        )
    else:
        strategies.append(
            "Combat polyvalent — adapter la stratégie en fonction des opportunités. "
            "Analyser les patterns de distance préférée (guard/clinch/distance)."
        )

    finishing_rate = patterns.get("finishing_rate", 0)
    try:
        if float(finishing_rate) > 0.6:
            strategies.append(
                f"Taux de finish élevé ({float(finishing_rate):.1%}) — "
                "ne pas s'exposer inutilement, gérer la garde en permanence."
            )
        elif float(finishing_rate) < 0.3:
            strategies.append(
                f"Faible taux de finish ({float(finishing_rate):.1%}) — "
                "le combat ira probablement aux juges, gérer les points et le volume."
            )
    except (TypeError, ValueError):
        pass

    for strategy in strategies:
        pdf.body_text(f"- {strategy}")

    pdf.ln(4)

    # ── Section 4: Key Stats ────────────────────────────────────────────────
    pdf.section_title("4. Stats Clés")

    striking = analysis.get("striking", {})
    grappling = analysis.get("grappling", {})

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Frappes:", new_x="LMARGIN", new_y="NEXT")

    def fmt(val, fmt_str=""):
        try:
            v = float(val)
            return format(v, fmt_str) if fmt_str else f"{v:.2f}"
        except (TypeError, ValueError):
            return str(val) if val else "N/A"

    pdf.stat_row("Knockdowns moyens", fmt(striking.get("avg_knockdowns"), ".2f"))
    pdf.stat_row("Précision frappes sig.", fmt(striking.get("avg_sig_str_accuracy_pct"), ".1%"))
    pdf.stat_row("Frappes tête (moy.)", fmt(striking.get("avg_head_strikes"), ".1f"))
    pdf.stat_row("Frappes corps (moy.)", fmt(striking.get("avg_body_strikes"), ".1f"))
    pdf.stat_row("Frappes jambes (moy.)", fmt(striking.get("avg_leg_strikes"), ".1f"))
    pdf.stat_row("Frappes distance (moy.)", fmt(striking.get("avg_distance_strikes"), ".1f"))

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Grappling:", new_x="LMARGIN", new_y="NEXT")
    pdf.stat_row("Précision takedowns", fmt(grappling.get("avg_td_accuracy_pct"), ".1%"))
    pdf.stat_row("Takedowns tentés (moy.)", fmt(grappling.get("avg_td_attempts"), ".1f"))
    pdf.stat_row("Takedowns réussis (moy.)", fmt(grappling.get("avg_td_landed"), ".1f"))
    pdf.stat_row("Tentatives soumission", fmt(grappling.get("avg_submission_attempts"), ".1f"))
    pdf.stat_row("Temps contrôle (moy.)", f"{fmt(grappling.get('avg_ctrl_time_seconds'), '.0f')}s")

    # Source citation
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        0, 5,
        "Sources: Toutes les statistiques proviennent de [source: ufc_data.csv] — "
        "données historiques UFC agrégées sur l'ensemble de la carrière du combattant."
    )
    pdf.set_text_color(0, 0, 0)

    # Save PDF
    pdf.output(output_path)
    print(f"[PDF] Game plan généré: {output_path}")
    return output_path
