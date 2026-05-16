"""
StatsAnalyzer: Loads and analyzes UFC fighter statistics from ufc_data.csv.
Provides fighter profiles, comparisons, pattern detection, and fuzzy search.
"""

import os
import json
import math
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def _safe_float(value, default: float = 0.0) -> float:
    """Convert value to float, returning default for NaN/None."""
    try:
        v = float(value)
        return default if math.isnan(v) else v
    except (TypeError, ValueError):
        return default


def _safe_str(value, default: str = "Unknown") -> str:
    """Convert value to str, returning default for NaN/None."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    return str(value).strip() or default


class StatsAnalyzer:
    """Analyzes UFC fight statistics from a CSV dataset."""

    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = csv_path or os.getenv("CSV_PATH", "./data/fighters/ufc_data.csv")
        self.df: pd.DataFrame = self._load_data()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_data(self) -> pd.DataFrame:
        """Load CSV into a DataFrame with graceful error handling."""
        try:
            df = pd.read_csv(self.csv_path, low_memory=False)
            print(f"[StatsAnalyzer] Loaded {len(df)} rows from {self.csv_path}")
            return df
        except FileNotFoundError:
            print(f"[StatsAnalyzer] ERROR: CSV not found at {self.csv_path}")
            return pd.DataFrame()
        except Exception as exc:
            print(f"[StatsAnalyzer] ERROR loading CSV: {exc}")
            return pd.DataFrame()

    def _get_fighter_rows(self, fighter_name: str) -> pd.DataFrame:
        """Return all rows where the fighter appears as R_fighter or B_fighter."""
        if self.df.empty:
            return pd.DataFrame()
        name_lower = fighter_name.strip().lower()
        mask = (
            self.df["R_fighter"].str.lower().str.strip() == name_lower
        ) | (
            self.df["B_fighter"].str.lower().str.strip() == name_lower
        )
        return self.df[mask].copy()

    def _agg_numeric(self, rows: pd.DataFrame, col_r: str, col_b: str, fighter_name: str) -> float:
        """Average a stat for a fighter appearing in either corner."""
        name_lower = fighter_name.strip().lower()
        values = []
        for _, row in rows.iterrows():
            if _safe_str(row.get("R_fighter", "")).lower() == name_lower:
                v = _safe_float(row.get(col_r))
                if v:
                    values.append(v)
            else:
                v = _safe_float(row.get(col_b))
                if v:
                    values.append(v)
        return round(sum(values) / len(values), 4) if values else 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_fighter(self, fighter_name: str) -> Dict[str, Any]:
        """Return aggregated stats for a fighter across all their fights.

        Args:
            fighter_name: Full name of the fighter.

        Returns:
            Structured dict with averages and profile data.
        """
        rows = self._get_fighter_rows(fighter_name)

        if rows.empty:
            result = {
                "fighter": fighter_name,
                "found": False,
                "message": f"No data found for '{fighter_name}' in the dataset.",
            }
            print(f"[Outil] stats_analyzer appelé → résultat brut: {json.dumps(result, ensure_ascii=False)}")
            return result

        name_lower = fighter_name.strip().lower()

        # Determine wins and losses
        total_fights = len(rows)
        wins = int((rows["Winner"].str.lower().str.strip() == name_lower).sum()) if "Winner" in rows.columns else 0
        losses = total_fights - wins

        # Win streak
        sorted_rows = rows.sort_values("date", ascending=False) if "date" in rows.columns else rows
        win_streak = 0
        for _, row in sorted_rows.iterrows():
            w = _safe_str(row.get("Winner", "")).lower()
            if w == name_lower:
                win_streak += 1
            else:
                break

        # Physical stats - take first non-null
        def first_val(col_r, col_b):
            for _, row in rows.iterrows():
                r_name = _safe_str(row.get("R_fighter", "")).lower()
                col = col_r if r_name == name_lower else col_b
                v = row.get(col)
                if v is not None and not (isinstance(v, float) and math.isnan(v)):
                    return str(v).strip()
            return "Unknown"

        # Aggregate numeric stats
        avg_kd = self._agg_numeric(rows, "R_avg_KD", "B_avg_KD", fighter_name)
        avg_sig_str_pct = self._agg_numeric(rows, "R_avg_SIG_STR_pct", "B_avg_SIG_STR_pct", fighter_name)
        avg_td_pct = self._agg_numeric(rows, "R_avg_TD_pct", "B_avg_TD_pct", fighter_name)
        avg_sub_att = self._agg_numeric(rows, "R_avg_SUB_ATT", "B_avg_SUB_ATT", fighter_name)
        avg_rev = self._agg_numeric(rows, "R_avg_REV", "B_avg_REV", fighter_name)
        avg_td_att = self._agg_numeric(rows, "R_avg_TD_att", "B_avg_TD_att", fighter_name)
        avg_td_landed = self._agg_numeric(rows, "R_avg_TD_landed", "B_avg_TD_landed", fighter_name)
        avg_ctrl = self._agg_numeric(rows, "R_avg_CTRL_time(seconds)", "B_avg_CTRL_time(seconds)", fighter_name)

        # Striking breakdown
        avg_head = self._agg_numeric(rows, "R_avg_HEAD_landed", "B_avg_HEAD_landed", fighter_name)
        avg_body = self._agg_numeric(rows, "R_avg_BODY_landed", "B_avg_BODY_landed", fighter_name)
        avg_leg = self._agg_numeric(rows, "R_avg_LEG_landed", "B_avg_LEG_landed", fighter_name)
        avg_distance = self._agg_numeric(rows, "R_avg_DISTANCE_landed", "B_avg_DISTANCE_landed", fighter_name)
        avg_clinch = self._agg_numeric(rows, "R_avg_CLINCH_landed", "B_avg_CLINCH_landed", fighter_name)
        avg_ground = self._agg_numeric(rows, "R_avg_GROUND_landed", "B_avg_GROUND_landed", fighter_name)

        # Physical profile
        height = first_val("R_Height_cms", "B_Height_cms")
        reach = first_val("R_Reach_cms", "B_Reach_cms")
        weight = first_val("R_Weight_lbs", "B_Weight_lbs")
        stance = first_val("R_Stance", "B_Stance")
        age = first_val("R_age", "B_age")
        weight_class = rows["weight_class"].mode()[0] if "weight_class" in rows.columns and not rows["weight_class"].isna().all() else "Unknown"

        result = {
            "fighter": fighter_name,
            "found": True,
            "profile": {
                "height_cms": height,
                "reach_cms": reach,
                "weight_lbs": weight,
                "stance": stance,
                "age": age,
                "weight_class": weight_class,
            },
            "record": {
                "total_fights": total_fights,
                "wins": wins,
                "losses": losses,
                "current_win_streak": win_streak,
            },
            "striking": {
                "avg_knockdowns": avg_kd,
                "avg_sig_str_accuracy_pct": avg_sig_str_pct,
                "avg_head_strikes": avg_head,
                "avg_body_strikes": avg_body,
                "avg_leg_strikes": avg_leg,
                "avg_distance_strikes": avg_distance,
                "avg_clinch_strikes": avg_clinch,
                "avg_ground_strikes": avg_ground,
            },
            "grappling": {
                "avg_td_accuracy_pct": avg_td_pct,
                "avg_td_attempts": avg_td_att,
                "avg_td_landed": avg_td_landed,
                "avg_submission_attempts": avg_sub_att,
                "avg_reversals": avg_rev,
                "avg_ctrl_time_seconds": avg_ctrl,
            },
        }

        print(f"[Outil] stats_analyzer appelé → résultat brut: {json.dumps(result, ensure_ascii=False, default=str)}")
        return result

    def compare_fighters(self, fighter1: str, fighter2: str) -> Dict[str, Any]:
        """Side-by-side comparison of two fighters with deltas and weaknesses.

        Args:
            fighter1: Name of the first fighter.
            fighter2: Name of the second fighter.

        Returns:
            Structured comparison dict.
        """
        stats1 = self.analyze_fighter(fighter1)
        stats2 = self.analyze_fighter(fighter2)

        if not stats1.get("found") or not stats2.get("found"):
            result = {
                "found": False,
                "fighter1": stats1,
                "fighter2": stats2,
                "message": "One or both fighters not found in dataset.",
            }
            print(f"[Outil] stats_analyzer appelé → résultat brut: {json.dumps(result, ensure_ascii=False, default=str)}")
            return result

        def delta(v1, v2):
            try:
                return round(float(v1) - float(v2), 4)
            except (TypeError, ValueError):
                return None

        # Identify weaknesses
        weaknesses1 = []
        weaknesses2 = []

        s1 = stats1["striking"]
        s2 = stats2["striking"]
        g1 = stats1["grappling"]
        g2 = stats2["grappling"]

        # Low sig str accuracy = striking accuracy gap
        if _safe_float(s1.get("avg_sig_str_accuracy_pct")) < 0.40:
            weaknesses1.append("Low striking accuracy (< 40%)")
        if _safe_float(s2.get("avg_sig_str_accuracy_pct")) < 0.40:
            weaknesses2.append("Low striking accuracy (< 40%)")

        # Low takedown accuracy = grappling weakness
        if _safe_float(g1.get("avg_td_accuracy_pct")) < 0.35:
            weaknesses1.append("Low takedown accuracy (< 35%) - can be sprawled frequently")
        if _safe_float(g2.get("avg_td_accuracy_pct")) < 0.35:
            weaknesses2.append("Low takedown accuracy (< 35%) - can be sprawled frequently")

        # Low control time = poor ground game
        if _safe_float(g1.get("avg_ctrl_time_seconds")) < 30:
            weaknesses1.append("Low ground control time - limited grappling dominance")
        if _safe_float(g2.get("avg_ctrl_time_seconds")) < 30:
            weaknesses2.append("Low ground control time - limited grappling dominance")

        # Few knockdowns = not a power striker
        if _safe_float(s1.get("avg_knockdowns")) < 0.1:
            weaknesses1.append("Rarely scores knockdowns - limited KO threat")
        if _safe_float(s2.get("avg_knockdowns")) < 0.1:
            weaknesses2.append("Rarely scores knockdowns - limited KO threat")

        # Low submission attempts
        if _safe_float(g1.get("avg_submission_attempts")) < 0.3:
            weaknesses1.append("Rarely attempts submissions - limited submission threat")
        if _safe_float(g2.get("avg_submission_attempts")) < 0.3:
            weaknesses2.append("Rarely attempts submissions - limited submission threat")

        result = {
            "found": True,
            "fighter1": {
                "name": fighter1,
                "stats": stats1,
                "weaknesses": weaknesses1,
            },
            "fighter2": {
                "name": fighter2,
                "stats": stats2,
                "weaknesses": weaknesses2,
            },
            "deltas": {
                "knockdowns_delta": delta(s1.get("avg_knockdowns"), s2.get("avg_knockdowns")),
                "sig_str_accuracy_delta": delta(s1.get("avg_sig_str_accuracy_pct"), s2.get("avg_sig_str_accuracy_pct")),
                "td_accuracy_delta": delta(g1.get("avg_td_accuracy_pct"), g2.get("avg_td_accuracy_pct")),
                "ctrl_time_delta": delta(g1.get("avg_ctrl_time_seconds"), g2.get("avg_ctrl_time_seconds")),
                "wins_delta": delta(stats1["record"].get("wins"), stats2["record"].get("wins")),
            },
            "tactical_notes": (
                f"{fighter1} has more knockdowns" if delta(s1.get("avg_knockdowns"), s2.get("avg_knockdowns")) and delta(s1.get("avg_knockdowns"), s2.get("avg_knockdowns")) > 0
                else f"{fighter2} has more knockdowns"
            ),
        }

        print(f"[Outil] stats_analyzer appelé → résultat brut: {json.dumps(result, ensure_ascii=False, default=str)}")
        return result

    def get_fighter_fights(self, fighter_name: str) -> List[Dict[str, Any]]:
        """Return a list of all fights for a given fighter.

        Args:
            fighter_name: Full name of the fighter.

        Returns:
            List of fight dicts.
        """
        rows = self._get_fighter_rows(fighter_name)
        fights = []
        for idx, row in rows.iterrows():
            fight = {
                "row_number": int(idx) + 2,  # +2 because CSV header is row 1
                "date": _safe_str(row.get("date")),
                "r_fighter": _safe_str(row.get("R_fighter")),
                "b_fighter": _safe_str(row.get("B_fighter")),
                "winner": _safe_str(row.get("Winner")),
                "weight_class": _safe_str(row.get("weight_class")),
                "title_bout": bool(row.get("title_bout", False)),
                "location": _safe_str(row.get("location")),
            }
            fights.append(fight)

        print(f"[Outil] stats_analyzer appelé → résultat brut: {json.dumps({'fighter': fighter_name, 'total_fights': len(fights)}, ensure_ascii=False)}")
        return fights

    def detect_patterns(self, fighter_name: str) -> Dict[str, Any]:
        """Detect tactical patterns for a fighter.

        Returns:
            Dict with striking_vs_grappling preference, finishing rate,
            decision rate, and average fight duration insights.
        """
        rows = self._get_fighter_rows(fighter_name)

        if rows.empty:
            result = {
                "fighter": fighter_name,
                "found": False,
                "message": f"No data found for '{fighter_name}'.",
            }
            print(f"[Outil] stats_analyzer appelé → résultat brut: {json.dumps(result, ensure_ascii=False)}")
            return result

        name_lower = fighter_name.strip().lower()

        avg_sub = self._agg_numeric(rows, "R_avg_SUB_ATT", "B_avg_SUB_ATT", fighter_name)
        avg_td = self._agg_numeric(rows, "R_avg_TD_landed", "B_avg_TD_landed", fighter_name)
        avg_kd = self._agg_numeric(rows, "R_avg_KD", "B_avg_KD", fighter_name)
        avg_ctrl = self._agg_numeric(rows, "R_avg_CTRL_time(seconds)", "B_avg_CTRL_time(seconds)", fighter_name)
        avg_distance = self._agg_numeric(rows, "R_avg_DISTANCE_landed", "B_avg_DISTANCE_landed", fighter_name)

        # Striking vs Grappling preference
        grappling_score = avg_td * 2 + avg_sub + avg_ctrl / 60
        striking_score = avg_distance + avg_kd * 5

        if grappling_score > striking_score * 1.5:
            style = "Predominantly Grappler"
        elif striking_score > grappling_score * 1.5:
            style = "Predominantly Striker"
        else:
            style = "Well-Rounded / Mixed Style"

        # Finishing rate (wins by KO or submission vs total wins)
        total_fights = len(rows)
        wins = int((rows["Winner"].str.lower().str.strip() == name_lower).sum()) if "Winner" in rows.columns else 0

        # Check finish method columns if available
        finishes = 0
        if "win_by" in rows.columns:
            win_rows = rows[rows["Winner"].str.lower().str.strip() == name_lower]
            finishes = int(win_rows["win_by"].str.lower().isin(["ko/tko", "submission"]).sum())
        finishing_rate = round(finishes / wins, 3) if wins > 0 else 0.0

        decisions = wins - finishes
        decision_rate = round(decisions / wins, 3) if wins > 0 else 0.0

        result = {
            "fighter": fighter_name,
            "found": True,
            "style": style,
            "grappling_score": round(grappling_score, 2),
            "striking_score": round(striking_score, 2),
            "finishing_rate": finishing_rate,
            "decision_rate": decision_rate,
            "total_wins": wins,
            "estimated_finishes": finishes,
            "avg_td_per_fight": avg_td,
            "avg_sub_att_per_fight": avg_sub,
            "avg_ctrl_seconds": avg_ctrl,
            "avg_distance_strikes": avg_distance,
            "avg_knockdowns": avg_kd,
            "tactical_summary": (
                f"{fighter_name} is a {style.lower()} with "
                f"{'high' if avg_kd > 0.3 else 'moderate' if avg_kd > 0.1 else 'low'} KO threat "
                f"and {'frequent' if avg_td > 2 else 'occasional' if avg_td > 0.5 else 'rare'} takedown attempts."
            ),
        }

        print(f"[Outil] stats_analyzer appelé → résultat brut: {json.dumps(result, ensure_ascii=False, default=str)}")
        return result

    def search_fighters(self, query: str) -> List[str]:
        """Fuzzy search for fighter names matching the query.

        Args:
            query: Partial or full fighter name to search.

        Returns:
            List of matching fighter names (deduplicated).
        """
        if self.df.empty:
            return []

        query_lower = query.strip().lower()
        all_fighters = set()

        if "R_fighter" in self.df.columns:
            all_fighters.update(self.df["R_fighter"].dropna().str.strip().tolist())
        if "B_fighter" in self.df.columns:
            all_fighters.update(self.df["B_fighter"].dropna().str.strip().tolist())

        matches = [
            name for name in all_fighters
            if query_lower in name.lower()
        ]
        matches_sorted = sorted(matches, key=lambda x: (not x.lower().startswith(query_lower), x))

        print(f"[Outil] stats_analyzer appelé → résultat brut: {json.dumps({'query': query, 'matches': matches_sorted[:20]}, ensure_ascii=False)}")
        return matches_sorted[:20]
