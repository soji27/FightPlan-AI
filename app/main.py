"""
FightPlan AI - CLI Entry Point.
Interactive REPL for MMA tactical analysis.
"""

import os
import re
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()

MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))

BANNER = """
╔══════════════════════════════════════════════════════╗
║     FightPlan AI - Analyse Tactique MMA              ║
║     Powered by LangGraph + RAG + Ollama              ║
╚══════════════════════════════════════════════════════╝

Commandes disponibles:
  quitter / exit           → Quitter l'application
  clear                    → Effacer l'historique de conversation
  genere le game plan <nom>→ Générer un PDF game plan pour un fighter
  ingest                   → Lancer l'ingestion des données dans ChromaDB

Posez vos questions sur les fighters UFC !
"""

# Injection patterns to block
_DANGEROUS_PATTERN = re.compile(
    r'(ignore previous|forget instructions|you are now|système:|<\|.*?\|>)',
    re.IGNORECASE
)


def validate_input(text: str, max_len: int = MAX_INPUT_LENGTH) -> str:
    """Validate and sanitize user input.

    Args:
        text: Raw user input.
        max_len: Maximum allowed length.

    Returns:
        Stripped, validated text.

    Raises:
        ValueError: If input is too long or contains dangerous patterns.
    """
    if len(text) > max_len:
        raise ValueError(f"Input trop long ({len(text)} > {max_len})")
    if _DANGEROUS_PATTERN.search(text):
        raise ValueError("Input potentiellement malveillant détecté")
    return text.strip()


def handle_game_plan(fighter_name: str, history_obj) -> None:
    """Generate a PDF game plan for a fighter.

    Args:
        fighter_name: Name of the fighter.
        history_obj: ConversationHistory instance.
    """
    print(f"\n[Game Plan] Génération du game plan pour: {fighter_name}")

    try:
        from app.tools.stats_analyzer import StatsAnalyzer
        from app.pdf_generator import generate_game_plan

        analyzer = StatsAnalyzer()
        analysis = analyzer.analyze_fighter(fighter_name)
        patterns = analyzer.detect_patterns(fighter_name)

        if not analysis.get("found"):
            # Try fuzzy search
            matches = analyzer.search_fighters(fighter_name)
            if matches:
                print(f"  Fighter '{fighter_name}' non trouvé. Suggestions: {', '.join(matches[:5])}")
                return
            else:
                print(f"  Fighter '{fighter_name}' non trouvé dans les données.")
                return

        # Combine analysis with patterns
        combined = {**analysis, "patterns": patterns, "weaknesses": []}

        # Auto-detect weaknesses
        striking = analysis.get("striking", {})
        grappling = analysis.get("grappling", {})

        try:
            if float(striking.get("avg_sig_str_accuracy_pct", 0)) < 0.40:
                combined["weaknesses"].append(
                    f"Précision de frappe faible ({float(striking.get('avg_sig_str_accuracy_pct', 0)):.1%}) "
                    "[source: ufc_data.csv]"
                )
        except (TypeError, ValueError):
            pass

        try:
            if float(grappling.get("avg_td_accuracy_pct", 0)) < 0.35:
                combined["weaknesses"].append(
                    f"Faible réussite takedowns ({float(grappling.get('avg_td_accuracy_pct', 0)):.1%}) "
                    "[source: ufc_data.csv]"
                )
        except (TypeError, ValueError):
            pass

        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        pdf_path = generate_game_plan(fighter_name, combined, output_dir)
        print(f"\n[Game Plan] PDF généré avec succès: {os.path.abspath(pdf_path)}")

    except Exception as exc:
        print(f"[Game Plan] Erreur: {exc}")


def run_ingestion() -> None:
    """Run the ChromaDB ingestion script."""
    print("\n[Ingest] Lancement de l'ingestion ChromaDB...")
    try:
        script_path = os.path.join(os.path.dirname(__file__), "ingest.py")
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[Ingest] Erreur: {exc}")
    except Exception as exc:
        print(f"[Ingest] Erreur inattendue: {exc}")


def main():
    """Main CLI REPL loop."""
    print(BANNER)

    from app.memory.history import ConversationHistory
    from app.orchestrator import run_query

    history = ConversationHistory()

    while True:
        try:
            user_input = input("\nVous: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAu revoir!")
            break

        if not user_input:
            continue

        # Handle special commands
        lower_input = user_input.lower()

        if lower_input in ("quitter", "exit", "quit"):
            print("Au revoir! Bonne analyse tactique.")
            break

        if lower_input == "clear":
            history.clear()
            print("[Historique effacé]")
            continue

        if lower_input == "ingest":
            run_ingestion()
            continue

        # Game plan command: "génère le game plan <fighter_name>"
        gameplan_match = re.match(
            r"^(génère|genere|génerer|generate)\s+le\s+game\s+plan\s+(.+)$",
            user_input,
            re.IGNORECASE,
        )
        if gameplan_match:
            fighter_name = gameplan_match.group(2).strip()
            handle_game_plan(fighter_name, history)
            continue

        # Validate input
        try:
            validated = validate_input(user_input)
        except ValueError as exc:
            print(f"[Validation] {exc}")
            continue

        # Run orchestrator
        print("\n[Analyse en cours...]\n")
        try:
            answer = run_query(validated, history)
            print(f"\nFightPlan AI: {answer}")

            # Add to history
            history.add("user", validated)
            history.add("assistant", answer)

        except Exception as exc:
            print(f"\n[Erreur] {exc}")
            print("Vérifiez que Ollama et ChromaDB sont en cours d'exécution.")


if __name__ == "__main__":
    main()
