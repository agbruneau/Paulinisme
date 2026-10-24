---
name: etude-livre
description: "Produire le dossier d'étude complet d'un livre de la Bible (Ancien ou Nouveau Testament, 4×N+7 fichiers) selon la théologie de John MacArthur : recherche exégétique sur le livre entier (Sommaire), recherches chapitre par chapitre (01 à N), plan de série homilétique à raison d'un sermon par chapitre (.md et .pdf), et portail HTML autonome sombre et orange (index.html)."
---

# Étude complète d'un livre de la Bible (`etude-livre`)

## Vue d'ensemble

Cette skill orchestre la production complète d'un dossier `<Livre>/` pour n'importe lequel des 66 livres de la Bible (Ancien ou Nouveau Testament, de la Genèse à l'Apocalypse), conformée à l'exégèse et à la théologie de John MacArthur.

Pour un livre comptant `N` chapitres (`<Plage>` vaut `1-<N>`, ou `1` pour un livre à chapitre unique comme Abdias, Philémon, 2 Jean, 3 Jean et Jude; le préfixe numérique des sous-dossiers est sur 2 chiffres `01` à `99`, ou 3 chiffres `001` à `150` pour les Psaumes), le dossier `<Livre>/` réunit exactement `4 × N + 7` fichiers :

1. `Sommaire/Recherche-MacArthur-<Livre>-<Plage>.{json,md,html,pdf}` : recherche exégétique sur le livre entier (`"passage": "<Nom du livre> <Plage>"`), où `"verses"` regroupe les versets clés représentatifs du livre.
2. `01-<Livre>-1/` à `<pad(N)>-<Livre>-<N>/` : un sous-dossier par chapitre contenant `Recherche-MacArthur-<Livre>-<n>.{json,md,html,pdf}` (`"passage": "<Nom du livre> <n>"`), où `"verses"` contient l'intégralité des versets du chapitre dans la NEG79.
3. `Plan-Serie-<Livre>-<Plage>.{md,pdf}` : plan de série homilétique comptant autant de prédications que le livre compte de chapitres (`N` chapitres = `N` sermons), regroupés selon les grands blocs structurels que dégage MacArthur.
4. `index.html` : portail autonome (CSS et JS en ligne, thème sombre `#0a0a0a` et orange `#e8843c`, aucune ressource externe) donnant accès au plan de série, à la recherche globale et aux `N` recherches par chapitre.

---

## Dépendances et compétences liées

- **`sermon-research`** (`C:\Users\agbru\.gemini\config\skills\sermon-research\SKILL.md`) : définit le schéma JSON à 9 sections des fichiers `Recherche-MacArthur-*.json`, l'échelle de couverture MacArthur (niveaux 1 à 5 et `∅`), l'encadré méthodologique sur les variantes textuelles et le générateur `generate.py`. Lire ses instructions avant de rédiger les fichiers `.json`.
- **`uv`** : utilisé pour exécuter `generate.py` avec `reportlab` (`uv run --with reportlab python ...`).
- **`pandoc` et Chrome/Edge headless** : pilotés par la sous-commande `render` de `scripts/etude_livre.py` pour produire `Plan-Serie-<Livre>-<Plage>.pdf`.

---

## Démarrage rapide

```powershell
# 1. Collecter les textes (NEG79, LSG, S21, Darby, NBS), variantes, morphologie et sermons GTY
uv run python .agents/skills/etude-livre/scripts/etude_livre.py collect `
  --book "Philémon" `
  --max-sermons 10 `
  --output-dir "$env:APPDATA\..\Local\Temp\collect_phm"

# 2. Récupérer les entrées lexicales Thayer (grec) ou BDB (hébreu)
uv run python .agents/skills/etude-livre/scripts/etude_livre.py lexicon `
  --lang greek `
  --strong "4698,2842,3685,1677,4355" `
  --output "$env:APPDATA\..\Local\Temp\collect_phm\lexicon.json"

# 3. Générer .md, .html et .pdf pour chaque fichier Recherche-MacArthur-*.json
uv run --with reportlab python "C:\Users\agbru\.gemini\config\skills\sermon-research\assets\generate.py" `
  Philémon/Sommaire/Recherche-MacArthur-Philemon-1.json

# 4. Rendre le PDF du plan de série à partir du Markdown
uv run python .agents/skills/etude-livre/scripts/etude_livre.py render `
  --plan-md Philémon/Plan-Serie-Philemon-1.md

# 5. Générer le portail autonome index.html à partir de sa spécification JSON
uv run python .agents/skills/etude-livre/scripts/etude_livre.py portal `
  --spec "$env:APPDATA\..\Local\Temp\collect_phm\portal_spec.json" `
  --output Philémon/index.html

# 6. Vérifier l'intégrité complète des 4*N+7 fichiers du dossier
uv run python .agents/skills/etude-livre/scripts/etude_livre.py verify `
  --book "Philémon" `
  --book-dir Philémon `
  --verses "$env:APPDATA\..\Local\Temp\collect_phm\verses_data.json" `
  --output "$env:APPDATA\..\Local\Temp\collect_phm\verify_report.json"
```

---

## Commandes du script CLI (`scripts/etude_livre.py`)

Le script `scripts/etude_livre.py` intègre la table canonique des 66 livres de la Bible (noms français, slugs de dossier, codes USFM, slugs BibleHub, slugs d'apparat SBLGNT, slugs MyOpenBible et nombres de chapitres) et expose cinq sous-commandes :

1. **`collect`** : télécharge pour une plage de chapitres (`--chapter-start`, `--chapter-end`) :
   - `verses_data.json` : texte NEG79 (BibleGateway et BibleAudio), LSG, Segond 21, Darby, NBS, texte original grec ou hébreu et éditions parallèles BibleHub.
   - `apparatus_ch<n>.html` : apparat critique SBLGNT (Nouveau Testament) ou panneau textuel BibleHub (Ancien Testament).
   - `interlinear_ch<n>.json` : mots originaux, numéros Strong, translittérations et codes morphologiques verset par verset.
   - `intro_macarthur.txt` : introduction du livre par John MacArthur sur MyOpenBible (lorsqu'elle est publiée).
   - `gty_sermons.json` et `sermon_<code>.txt` : transcriptions intégrales des sermons Grace to You (`--max-sermons` sonde les codes séquentiels `<num_livre>-1..M`; `--sermon-codes` permet d'ajouter des codes hors séquence comme la série `90-*` pour l'Ancien Testament ou des codes à 4 chiffres).
2. **`lexicon`** : récupère les définitions Thayer (`--lang greek`) ou Brown-Driver-Briggs (`--lang hebrew`) sur BibleHub pour une liste de numéros Strong (`--strong "1234,5678"`) et les sauvegarde dans `--output`.
3. **`render`** : nettoie tout tiret cadratin éventuel dans `Plan-Serie-<Livre>-<Plage>.md` et génère `Plan-Serie-<Livre>-<Plage>.pdf` via `pandoc` et Chrome/Edge headless (format Letter, marges `18mm 18mm 16mm`, police Georgia `11pt`, titres `#1A2A40`, filets `#B8862B`).
4. **`portal`** : génère `<Livre>/index.html` à partir d'un fichier JSON de spécification (`--spec`), en ajustant automatiquement `--n-puces` au nombre de chapitres et `--n-blocs` au nombre de blocs structurels.
5. **`verify`** : contrôle l'existence et la non-vacuité des `4 × N + 7` fichiers, l'absence de tiret cadratin (`\u2014`) dans tous les `.json`, `.md` et `.html`, la conformité mot pour mot des versets avec la NEG79 (`--verses`), et la résolution de tous les liens relatifs et ancres (`#...`) dans `index.html` et `Plan-Serie-<Livre>-<Plage>.md`.

---

## Déroulement en cinq étapes

### Étape 1 : Collecte des sources primaires
- Exécuter `etude_livre.py collect` dans un répertoire de travail temporaire (`scratch/<slug>`). Pour un livre volumineux (p. ex. Isaïe ou Psaumes), procéder par tranches avec `--chapter-start` et `--chapter-end`.
- Pour un livre de l'Ancien Testament où la série séquentielle `<num_livre>-*` sur `gty.org` est absente ou partielle, chercher les sermons de MacArthur portant sur ce livre (souvent indexés sous `90-*` ou des codes à 4 chiffres) et les passer via `--sermon-codes`. S'appuyer également sur l'échelle de couverture à 5 niveaux de `sermon-research` (niveau 2 : *MacArthur Study Bible* / *MacArthur Bible Commentary*; niveaux 3 à 5 : sermons thématiques et ouvrages de MacArthur).
- Extraire les numéros Strong des termes structurants à partir de `interlinear_ch<n>.json` et lancer `etude_livre.py lexicon` (`--lang greek` pour le NT, `--lang hebrew` pour l'AT).

### Étape 2 : Recherche exégétique globale (`Sommaire/`)
- Créer `<Livre>/Sommaire/Recherche-MacArthur-<Livre>-<Plage>.json` conformément au schéma de `sermon-research` (`"passage": "<Nom du livre> <Plage>"`).
- Inclure dans `"verses"` les versets clés représentatifs de l'ensemble des chapitres (texte exact de `NEG79_BG`), couvrir la paternité, la date, les destinataires, l'occasion, la structure macro-littéraire selon MacArthur, les variantes majeures du livre, les mots-clés transversaux et la synthèse doctrinale, puis exécuter `generate.py`.

### Étape 3 : Recherches exégétiques par chapitre (`01` à `N`)
- Pour chaque chapitre `n` de `1` à `N`, créer `<Livre>/<pad(n)>-<Livre>-<n>/Recherche-MacArthur-<Livre>-<n>.json` (`"passage": "<Nom du livre> <n>"`).
- Mettre dans `"verses"` la totalité des versets du chapitre (`1` au dernier verset) extraits de `verses_data.json` (`NEG79_BG` nettoyé).
- Documenter toute charnière inter-chapitres (lorsqu'une péricope ou un sermon GTY enjambe deux chapitres) dans la section `context` et la section `commentators`.
- Exécuter `generate.py` sur chaque fichier `.json` pour produire les `.md`, `.html` et `.pdf`.

### Étape 4 : Plan de série (`Plan-Serie-<Livre>-<Plage>.{md,pdf}`) et portail (`index.html`)
- Rédiger `<Livre>/Plan-Serie-<Livre>-<Plage>.md` en suivant le gabarit détaillé dans [`references/gabarits.md`](references/gabarits.md) (`1 chapitre = 1 sermon`, regroupés par blocs structurels, avec introduction et transition rendant compte des charnières).
- Générer le PDF avec `etude_livre.py render --plan-md <Livre>/Plan-Serie-<Livre>-<Plage>.md`.
- Construire le fichier `portal_spec.json` selon le schéma documenté dans [`references/gabarits.md`](references/gabarits.md) et générer `<Livre>/index.html` avec `etude_livre.py portal`.

### Étape 5 : Vérification de clôture et publication
- Exécuter `etude_livre.py verify` et corriger toute anomalie dans les fichiers sources (`.json`, `.md` ou `portal_spec.json`) avant de régénérer les livrables dérivés.
- Si le dépôt contient une table d'avancement (comme `README.md`), mettre à jour l'état du livre étudié.
- Commiter l'ensemble des fichiers produits ou mis à jour et pousser directement sur la branche `main` (`git push origin main`).

---

## Limitation de débit et gestion réseau

Le client HTTP intégré à `scripts/etude_livre.py` applique une limitation de débit par hôte avec `time.monotonic()` (`--rate-limit 2.0` requêtes/seconde par défaut), un backoff exponentiel sur les erreurs 5xx et erreurs de transport, et lève `RateLimitError` sur HTTP 429 en indiquant le délai `Retry-After`. Ne pas paralléliser plusieurs instances de `collect` ou `lexicon` contre les mêmes domaines (`biblehub.com`, `gty.org`, `biblegateway.com`).

---

## Erreurs courantes à éviter

- **Modifier directement un `.md` ou `.html` de recherche** : pour les fichiers `Recherche-MacArthur-*`, le `.json` est la seule source de vérité; toute modification se fait dans le `.json` suivie d'une exécution de `generate.py`.
- **Omettre des versets dans un dossier de chapitre** : le tableau `"verses"` de `Recherche-MacArthur-<Livre>-<n>.json` contient tous les versets du chapitre `n`, tandis que celui du `Sommaire` réunit une sélection des versets clés du livre.
- **Laisser des tirets cadratins (`—`, `\u2014`)** : `generate.py` et `verify` rejettent le caractère `\u2014`. Utiliser `-`, `:`, `;` ou `,`.
- **Altérer un mot de la NEG79** : copier les citations de la NEG79 depuis `verses_data.json` (`NEG79_BG`) sans reformulation de mémoire.
