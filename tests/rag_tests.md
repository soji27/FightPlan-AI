# Tests RAG Agent

## Cas Nominaux

| ID | Input | Expected Output | Critère de succès |
|----|-------|----------------|-------------------|
| NOM-01 | "Quelles sont les stats de Jon Jones ?" | Stats avec citations [source: ufc_data.csv, ligne X] | Citation présente, stats correctes |
| NOM-02 | "Compare Conor McGregor et Khabib Nurmagomedov" | Comparaison structurée des deux fighters | Les deux fighters identifiés |
| NOM-03 | "Quelles sont les failles de Israel Adesanya ?" | Failles identifiées avec evidence du CSV | Au moins 2 failles citées |
| NOM-04 | "Quel est le bilan de Stipe Miocic ?" | Victoires, défaites, titre | Bilan chiffré avec citation |
| NOM-05 | "Analyse le style de Kamaru Usman" | Style grappling vs striking, pattern | Style identifié avec justification |

## Cas Limites

| ID | Input | Expected Output | Critère de succès |
|----|-------|----------------|-------------------|
| LIM-01 | "Stats de [fighter inconnu]" | "Information absente des documents" | Pas d'hallucination |
| LIM-02 | Question de 1999 caractères | Réponse normale | Pas de crash |
| LIM-03 | "a" | Demande de précision | Réponse cohérente |
| LIM-04 | Question sans fighter spécifié | Demande de précision | Guidance fournie |
| LIM-05 | Question en anglais | Réponse en anglais | Langue respectée |
| LIM-06 | Nom de fighter avec faute d'orthographe (ex: "Jon Jonnes") | Suggestions de noms proches | Fuzzy match fonctionnel |

## Cas d'Erreur

| ID | Input | Expected Output | Critère de succès |
|----|-------|----------------|-------------------|
| ERR-01 | ChromaDB indisponible | Message d'erreur gracieux | Pas de crash |
| ERR-02 | Ollama indisponible | Message d'erreur gracieux | Pas de crash |
| ERR-03 | Input > 2000 caractères | "Input trop long" | Validation bloquante |
| ERR-04 | CSV manquant | Message d'erreur clair | Pas de crash |
| ERR-05 | Collection ChromaDB vide (pas d'ingestion) | Message explicite | Guidance vers `ingest` |
| ERR-06 | Timeout réseau | Message d'erreur avec retry suggestion | Pas de crash |

## Tests de Performance

| ID | Scénario | Seuil acceptable | Critère |
|----|----------|-----------------|---------|
| PERF-01 | Latence requête RAG | < 10 secondes | Réponse dans les temps |
| PERF-02 | Latence stats_analyzer | < 2 secondes | Analyse CSV rapide |
| PERF-03 | Ingestion 6000 lignes | < 30 minutes | Completion sans erreur |
| PERF-04 | 10 requêtes simultanées | Pas de crash | Stabilité |

## Tests de Citations

| ID | Input | Citation attendue | Critère |
|----|-------|------------------|---------|
| CIT-01 | "Stats de Jon Jones" | [source: ufc_data.csv, ligne X] | Format respecté |
| CIT-02 | "Combats de Khabib" | Chaque fait cité | ≥ 1 citation par stat |
| CIT-03 | "Failles de McGregor" | Source pour chaque faille | Traçabilité complète |

## Notes d'Exécution

Pour exécuter les tests manuellement:
1. S'assurer que ChromaDB et Ollama sont actifs: `docker-compose up -d`
2. Lancer l'ingestion: `python app/ingest.py`
3. Lancer l'application: `python app/main.py` ou `streamlit run app/ui/streamlit_app.py`
4. Saisir chaque input du tableau et vérifier les critères de succès
