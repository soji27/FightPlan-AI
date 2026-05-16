"""
FightPlan AI - Streamlit Web Interface.
"""

import os
import re
import sys

import streamlit as st
from dotenv import load_dotenv

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()

MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))

# ── Validation ────────────────────────────────────────────────────────────────

_DANGEROUS_PATTERN = re.compile(
    r'(ignore previous|forget instructions|you are now|système:|<\|.*?\|>)',
    re.IGNORECASE,
)


def validate_input(text: str) -> str:
    """Validate user input. Raises ValueError on invalid input."""
    if len(text) > MAX_INPUT_LENGTH:
        raise ValueError(f"Message trop long ({len(text)} > {MAX_INPUT_LENGTH} caractères)")
    if _DANGEROUS_PATTERN.search(text):
        raise ValueError("Contenu potentiellement malveillant détecté")
    return text.strip()


# ── Session state initialization ──────────────────────────────────────────────

def init_session():
    """Initialize Streamlit session state."""
    if "history_obj" not in st.session_state:
        from app.memory.history import ConversationHistory
        st.session_state.history_obj = ConversationHistory()

    if "messages" not in st.session_state:
        st.session_state.messages = []  # [{role, content, traces}]

    if "last_pdf_path" not in st.session_state:
        st.session_state.last_pdf_path = None

    if "agent_traces" not in st.session_state:
        st.session_state.agent_traces = []


# ── Helper functions ──────────────────────────────────────────────────────────

def get_stats_analyzer():
    """Lazily initialize and cache StatsAnalyzer."""
    if "stats_analyzer" not in st.session_state:
        from app.tools.stats_analyzer import StatsAnalyzer
        st.session_state.stats_analyzer = StatsAnalyzer()
    return st.session_state.stats_analyzer


def search_fighters_cached(query: str):
    """Search fighters with caching."""
    if not query or len(query) < 2:
        return []
    analyzer = get_stats_analyzer()
    return analyzer.search_fighters(query)


def generate_pdf_for_fighter(fighter_name: str):
    """Generate a PDF game plan and store path in session state."""
    try:
        from app.tools.stats_analyzer import StatsAnalyzer
        from app.pdf_generator import generate_game_plan

        analyzer = StatsAnalyzer()

        # Resolve partial name to full name (e.g. "Khabib" -> "Khabib Nurmagomedov")
        matches = analyzer.search_fighters(fighter_name.strip())
        resolved_name = matches[0] if matches else fighter_name.strip()

        analysis = analyzer.analyze_fighter(resolved_name)
        patterns = analyzer.detect_patterns(resolved_name)

        if not analysis.get("found"):
            st.error(f"Fighter '{fighter_name}' non trouvé dans les données.")
            return

        combined = {**analysis, "patterns": patterns, "weaknesses": []}

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

        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")
        pdf_path = generate_game_plan(resolved_name, combined, output_dir)
        st.session_state.last_pdf_path = os.path.abspath(pdf_path)
        st.success(f"Game plan PDF généré!")

    except Exception as exc:
        st.error(f"Erreur lors de la génération du PDF: {exc}")


# ── Main Streamlit App ────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="FightPlan AI",
        page_icon="🥊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session()

    # ── CSS Styling ────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
        text-align: center;
    }
    .agent-trace {
        background-color: #f0f2f6;
        border-left: 4px solid #dc3545;
        padding: 10px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
    }
    .source-citation {
        background-color: #e8f4fd;
        border: 1px solid #bee3f8;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 11px;
        color: #2b6cb0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="main-header">
        <h1>FightPlan AI</h1>
        <p>Analyse Tactique MMA UFC • Powered by LangGraph + RAG + Ollama</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Recherche de Fighter")

        search_query = st.text_input(
            "Chercher un fighter",
            placeholder="Ex: Jon Jones, McGregor...",
            key="fighter_search",
        )

        if search_query:
            matches = search_fighters_cached(search_query)
            if matches:
                st.write("**Résultats:**")
                for name in matches[:10]:
                    if st.button(name, key=f"select_{name}", use_container_width=True):
                        st.session_state.selected_fighter = name
            else:
                st.info("Aucun fighter trouvé.")

        st.divider()

        # Game Plan Generator
        st.header("Game Plan PDF")
        gameplan_fighter = st.text_input(
            "Nom du fighter",
            value=st.session_state.get("selected_fighter", ""),
            key="gameplan_fighter_input",
            placeholder="Ex: Jon Jones",
        )

        if st.button("Générer Game Plan PDF", type="primary", use_container_width=True):
            if gameplan_fighter:
                with st.spinner(f"Génération du game plan pour {gameplan_fighter}..."):
                    generate_pdf_for_fighter(gameplan_fighter)
            else:
                st.warning("Entrez le nom d'un fighter.")

        # PDF Download
        if st.session_state.last_pdf_path and os.path.exists(st.session_state.last_pdf_path):
            with open(st.session_state.last_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="Télécharger le PDF",
                data=pdf_bytes,
                file_name=os.path.basename(st.session_state.last_pdf_path),
                mime="application/pdf",
                use_container_width=True,
            )

        st.divider()

        # Conversation History
        st.header("Historique")
        messages = st.session_state.history_obj.get_messages()
        if messages:
            for msg in messages[-6:]:  # Show last 3 exchanges
                role_icon = "You" if msg["role"] == "user" else "AI"
                st.caption(f"**{role_icon}:** {msg['content'][:80]}...")
        else:
            st.caption("Aucun historique pour le moment.")

        if st.button("Effacer l'historique", use_container_width=True):
            st.session_state.history_obj.clear()
            st.session_state.messages = []
            st.session_state.agent_traces = []
            st.rerun()

        st.divider()
        st.caption("FightPlan AI v1.0 • Données: ufc_data.csv")

    # ── Main Chat Area ─────────────────────────────────────────────────────
    col_main, col_traces = st.columns([2, 1])

    with col_main:
        st.subheader("Analyse Tactique")

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg["content"])
                        # Show sources if present
                        if msg.get("sources"):
                            with st.expander("Sources consultées", expanded=False):
                                for src in msg["sources"]:
                                    st.markdown(
                                        f'<span class="source-citation">'
                                        f'[source: {src.get("source", "ufc_data.csv")}, '
                                        f'ligne {src.get("row", "?")}] — '
                                        f'Score: {src.get("score", 0):.2f}'
                                        f'</span>',
                                        unsafe_allow_html=True,
                                    )

        # Chat input
        user_question = st.chat_input("Posez votre question sur un fighter UFC...")

        if user_question:
            # Validate
            try:
                validated = validate_input(user_question)
            except ValueError as exc:
                st.error(f"Validation: {exc}")
                st.stop()

            # Add user message to display
            st.session_state.messages.append({
                "role": "user",
                "content": validated,
            })

            # Run orchestrator
            with st.spinner("Analyse en cours..."):
                try:
                    from app.orchestrator import run_query
                    answer = run_query(validated, st.session_state.history_obj)

                    # Update conversation history
                    st.session_state.history_obj.add("user", validated)
                    st.session_state.history_obj.add("assistant", answer)

                    # Store assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": [],
                    })

                except Exception as exc:
                    error_msg = f"Erreur: {exc}. Vérifiez que Ollama et ChromaDB sont actifs."
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                    })

            st.rerun()

    # ── Agent Traces Panel ─────────────────────────────────────────────────
    with col_traces:
        st.subheader("Traces Agents")
        st.caption("Les traces s'affichent dans les logs du serveur (stdout).")

        with st.expander("Architecture du système", expanded=True):
            st.markdown("""
            **Pipeline d'agents:**

            1. **Router** → Analyse l'intention
               - RAG: stats/historique/record
               - Tools: récent/actualité/pattern

            2. **RAG Agent** → ChromaDB + Ollama
               - Recherche vectorielle (nomic-embed-text)
               - Top 5 chunks similaires
               - Génère avec citations

            3. **Tools Agent** → Analyse directe
               - StatsAnalyzer (CSV)
               - WebSearchTool (DDGS)

            4. **Response** → Réponse finale formatée
            """)

        with st.expander("Logs de la session", expanded=False):
            if st.session_state.messages:
                st.text(f"Messages: {len(st.session_state.messages)}")
                st.text(f"Historique: {len(st.session_state.history_obj)} msgs")
            else:
                st.text("Aucune interaction encore.")

        with st.expander("Exemples de questions", expanded=False):
            example_questions = [
                "Quelles sont les stats de Jon Jones ?",
                "Compare Conor McGregor et Khabib Nurmagomedov",
                "Quelles sont les failles de Israel Adesanya ?",
                "Quel est le bilan de Stipe Miocic ?",
                "Analyse le style de combat de Kamaru Usman",
                "Qui a le meilleur taux de takedown ?",
            ]
            for q in example_questions:
                st.caption(f"• {q}")


if __name__ == "__main__":
    main()
