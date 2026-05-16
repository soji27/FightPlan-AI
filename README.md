# FightPlan AI — Système Multi-Agents d'Analyse Tactique MMA

> Projet Ydays — Analyse tactique UFC par intelligence artificielle multi-agents

**Auteurs :** MANMATHAN Sojivanan & DIKETE Timothée

---

## Présentation

FightPlan AI est un système d'intelligence artificielle multi-agents conçu pour les coachs et combattants UFC professionnels. Il analyse automatiquement les données historiques de combats pour générer un **Game Plan tactique** en PDF, en croisant les statistiques de performance, les failles détectées et les recommandations stratégiques.

### Problème résolu

Analyser manuellement des centaines de combats pour préparer un fighter prend des heures. FightPlan AI automatise cette analyse en quelques secondes en combinant recherche vectorielle (RAG), analyse Pandas et recherche web temps réel.

---

## Architecture du système

```
Utilisateur
    │
    ▼
┌─────────────────┐
│   Streamlit UI  │  ← Interface web (port 8501)
│   / CLI REPL    │  ← Interface terminal
└────────┬────────┘
         │ question validée
         ▼
┌─────────────────────────────────┐
│     Orchestrateur LangGraph     │
│                                 │
│  ┌─────────┐    ┌────────────┐  │
│  │  Router │───▶│ Agent RAG  │  │ ← Stats historiques, palmarès, failles
│  │  Node   │    └────────────┘  │
│  │         │    ┌────────────┐  │
│  │         │───▶│Agent Outils│  │ ← Calculs Pandas + Web DuckDuckGo
│  └─────────┘    └────────────┘  │
└─────────────────┬───────────────┘
                  │
         ┌────────┴────────┐
         ▼                 ▼
  ┌────────────┐    ┌──────────────┐
  │  ChromaDB  │    │    Ollama    │
  │ (vectordb) │    │ llama3.2:3b │
  └────────────┘    └──────────────┘
```

### Flux de décision du routeur

| Signal dans la question | Agent choisi | Exemples |
|------------------------|--------------|---------|
| stats, historique, record, faille, palmarès | **RAG** | "Quelles sont les stats de Jon Jones ?" |
| récent, actualité, compare, pattern, calcule | **Outils** | "Analyse le style de combat de Khabib" |
| Aucun signal clair | **RAG** (défaut) | Question générale |

---

## Stack technique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Orchestration | LangGraph | Routage multi-agents via StateGraph |
| LLM | Ollama + llama3.2:3b | Génération de réponses en langage naturel |
| VectorDB | ChromaDB | Recherche sémantique sur 6 012 combats |
| Embeddings | nomic-embed-text | Vectorisation des chunks CSV |
| Analyse données | Pandas | Calcul de stats, détection de patterns |
| Interface web | Streamlit | UI conversationnelle sur port 8501 |
| Export | FPDF2 | Génération de PDF Game Plan |
| Recherche web | DuckDuckGo | Infos récentes sans clé API |
| Conteneurisation | Docker Compose | Démarrage en une commande |

---

## Structure du projet

```
mma-gameplan/
├── docker-compose.yml          # 3 services : ollama, chromadb, app
├── Dockerfile
├── .env.example                # Variables d'environnement (à copier en .env)
├── requirements.txt
│
├── app/
│   ├── main.py                 # CLI REPL + validation anti-injection
│   ├── orchestrator.py         # LangGraph — router + nodes + graph
│   ├── ingest.py               # Ingestion ChromaDB (à lancer une fois)
│   ├── pdf_generator.py        # Générateur PDF Game Plan (FPDF2)
│   │
│   ├── agents/
│   │   ├── rag_agent.py        # RAG : ChromaDB + nomic-embed-text + citations
│   │   └── tools_agent.py      # Outils : Pandas + DuckDuckGo
│   │
│   ├── tools/
│   │   ├── stats_analyzer.py   # Analyse CSV : stats, failles, comparaisons
│   │   └── web_search.py       # Recherche DuckDuckGo (sans clé API)
│   │
│   ├── memory/
│   │   └── history.py          # Historique glissant — 3 derniers échanges
│   │
│   └── ui/
│       └── streamlit_app.py    # Interface Streamlit
│
├── data/
│   └── fighters/
│       └── ufc_data.csv        # 6 012 combats UFC, 120+ colonnes
│
├── output/                     # PDFs Game Plan générés
├── vectordb/                   # Volume persistant ChromaDB
│
└── tests/
    ├── rag_tests.md            # Cas nominal / limite / erreur (Agent RAG)
    ├── tools_tests.md          # Cas nominal / limite / erreur (Agent Outils)
    └── security.md             # Matrice de risques + tests injection
```

---

## Données

Le fichier `ufc_data.csv` contient **6 012 combats UFC** avec pour chaque fight :

- Identité : fighters (rouge/bleu), arbitre, date, lieu, catégorie de poids
- Résultat : gagnant, bout titre ou non
- Statistiques moyennes par fighter : knockdowns, précision frappes significatives, pourcentage takedowns, tentatives de soumissions, contrôle au sol, frappes tête/corps/jambes, distance/clinch/sol
- Bilan carrière : victoires, défaites, séries en cours, longueur de série, méthodes de victoire
- Physique : taille (cm), allonge (cm), poids (lbs), âge, stance (Orthodox/Southpaw/Switch)

---

## Installation et démarrage

### Prérequis

- Docker Desktop installé et lancé
- 4 Go de RAM minimum (llama3.2:3b = ~2 Go)
- 15 Go d'espace disque libre

### Démarrage en 5 étapes

```bash
# 1. Se placer dans le dossier
cd mma-gameplan

# 2. Copier les variables d'environnement
cp .env.example .env

# 3. Lancer tous les services Docker
docker compose up -d

# 4. Télécharger les modèles Ollama (une seule fois, ~3 Go)
docker exec fightplan-ollama ollama pull llama3.2:3b
docker exec fightplan-ollama ollama pull nomic-embed-text

# 5. Ingérer les données dans ChromaDB (une seule fois)
docker exec fightplan-app python app/ingest.py
```

### Accès

| Interface | URL / Commande |
|-----------|---------------|
| Interface web Streamlit | `http://localhost:8501` |
| CLI terminal | `docker exec -it fightplan-app python app/main.py` |
| ChromaDB API | `http://localhost:8000` |
| Ollama API | `http://localhost:11434` |

---

## Utilisation

### Interface CLI

```
=== FightPlan AI - Analyse Tactique MMA ===

Vous: Quelles sont les failles de Jon Jones ?

[Routeur] → Agent: RAG | Raison: Question contains 2 RAG keywords (faille, stats)
[RAG] Lignes consultées: [42, 891, 1203] | Scores: [0.94, 0.88, 0.82]
[Final] → Jon Jones présente une vulnérabilité aux takedowns répétés...

FightPlan AI: Jon Jones présente une vulnérabilité aux takedowns répétés
[source: ufc_data.csv, ligne 42] avec un taux de défense de 78%...
```

### Commandes spéciales

| Commande | Action |
|----------|--------|
| `quitter` / `exit` | Quitter l'application |
| `clear` | Effacer l'historique de conversation |
| `genere le game plan <nom>` | Générer un PDF pour ce fighter |
| `ingest` | Relancer l'ingestion ChromaDB |

### Générer un Game Plan PDF

```
Vous: genere le game plan Khabib Nurmagomedov

[Game Plan] Génération du game plan pour: Khabib Nurmagomedov
[Game Plan] PDF généré avec succès: output/gameplan_khabib_nurmagomedov_2026-05-16.pdf
```

Le PDF contient :
1. **Profil du Fighter** — stats clés (taille, poids, allonge, stance, bilan)
2. **Failles Détectées** — points faibles avec citations [source: ufc_data.csv, ligne X]
3. **Stratégie Recommandée** — plan d'attaque basé sur les données
4. **Stats Clés** — tableaux de métriques offensives/défensives

---

## Comportement des agents

### Agent RAG

- Recherche vectorielle sur ChromaDB (top 5 résultats les plus proches)
- Embeddings : nomic-embed-text (chunks de ~500 tokens, overlap 50)
- Chaque réponse cite obligatoirement ses sources : `[source: ufc_data.csv, ligne X]`
- Si l'information est absente : réponse explicite "Information non trouvée dans les données"
- System prompt renforcé contre le prompt injection

### Agent Outils

- **stats_analyzer** : charge ufc_data.csv avec Pandas, calcule moyennes, détecte patterns (finishing rate, style frappeur/grappeur, durée moyenne des combats)
- **web_search** : DuckDuckGo DDGS, aucune clé API requise, résultats formatés en JSON
- Sortie toujours structurée en JSON avant rendu en langage naturel

### Mémoire conversationnelle

Les 3 derniers échanges (question + réponse) sont injectés dans chaque prompt pour permettre les questions de suivi :

```
Vous: Parle-moi de Conor McGregor
FightPlan AI: [réponse]

Vous: Approfondis le point sur sa défense au sol
FightPlan AI: [réponse contextualisée sans re-demander qui est McGregor]
```

---

## Sécurité

| Menace | Contre-mesure |
|--------|---------------|
| Prompt injection | Validation regex Python + system prompt anti-injection |
| Input trop long | Limite MAX_INPUT_LENGTH=2000 caractères |
| Clés API exposées | Variables d'environnement uniquement (.env jamais commité) |
| DoS applicatif | Timeout Ollama + limite top_k ChromaDB |
| Injection CSV | Données traitées comme contexte, pas comme instructions |

Patterns bloqués côté Python :
```
"ignore previous instructions"
"forget instructions"
"you are now"
"système:"
"<|...|>"
```

---

## Tests

### tests/rag_tests.md
Tableau complet avec cas nominaux, cas limites et cas d'erreur couvrant :
- Questions sur fighters existants / inexistants
- Inputs à la limite de longueur
- Services indisponibles (ChromaDB/Ollama offline)
- Vérification des citations dans chaque réponse

### tests/security.md
Matrice de 5 menaces avec vecteurs d'attaque, contre-mesures implémentées et tests de validation.

---

## Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | URL du service Ollama |
| `CHROMA_HOST` | `http://localhost:8000` | URL du service ChromaDB |
| `OLLAMA_MODEL` | `llama3.2:3b` | Modèle LLM utilisé |
| `EMBED_MODEL` | `nomic-embed-text` | Modèle d'embeddings |
| `CSV_PATH` | `./data/fighters/ufc_data.csv` | Chemin vers les données |
| `MAX_INPUT_LENGTH` | `2000` | Limite de caractères en entrée |
| `CHROMA_COLLECTION` | `mma_fighters` | Nom de la collection ChromaDB |

---

## Dépendances principales

```
langgraph>=0.1.0          # Orchestration multi-agents
langchain>=0.2.0           # Framework LLM
chromadb>=0.5.0            # Base vectorielle
ollama>=0.2.0              # Client Ollama (llama3.2:3b + nomic-embed-text)
pandas>=2.0.0              # Analyse des données CSV
streamlit>=1.35.0          # Interface web
fpdf2>=2.7.0               # Génération PDF
duckduckgo-search>=6.0.0   # Recherche web sans API
python-dotenv>=1.0.0       # Gestion des variables d'environnement
```

---

## Affichage console (transparence)

À chaque requête, la console affiche dans l'ordre :

```
[Routeur] → Agent: RAG | Raison: ...
[RAG]    Lignes consultées: [2, 45, 102] | Scores: [0.92, 0.87, 0.81]
[Final]  → {début de la réponse}...

-- ou si Agent Outils --

[Routeur] → Agent: TOOLS | Raison: ...
[Outil]  stats_analyzer appelé → résultat brut: {...}
[Final]  → {début de la réponse}...
```

---

*FightPlan AI — MANMATHAN Sojivanan & DIKETE Timothée — Projet Ydays 2026*
