# Paulinisme

Ce dépôt réunit les études des treize épîtres de Paul dans l'ordre chronologique de leur rédaction selon John MacArthur (table et conventions générales dans `README.md`). Les dossiers `Galates/` et `1-Thessaloniciens/` servent d'implémentations de référence.

## Découpage d'une épître

- **Un sermon par chapitre.** Le plan de série d'une épître compte autant de prédications que l'épître compte de chapitres (`N` chapitres = `N` sermons), regroupés selon les grands blocs structurels que dégage MacArthur pour ce livre. Ce découpage par chapitre prime sur le découpage par péricopes de la skill `sermon-series`.
- **Charnières.** Lorsqu'une unité de pensée du texte ou un sermon Grace to You (GTY) enjambe une frontière de chapitre (p. ex. `Galates 1.11-2.10` ou `1 Thessaloniciens 4.16-5.3`), la recherche et le plan en rendent compte dans l'introduction et la transition des chapitres concernés.

## Livrables d'un dossier `<Épître>/`

Pour une épître de `N` chapitres, son dossier à la racine du dépôt contient `4 × N + 7` fichiers :

1. `Sommaire/Recherche-MacArthur-<Épître>-1-<N>.{json,md,html,pdf}` : recherche exégétique sur le livre entier (skill `sermon-research`, `"passage": "<Épître> 1-<N>"`), où `verses` réunit les versets clés représentatifs de l'épître.
2. `01-<Épître>-1/` à `0<N>-<Épître>-<N>/` : un sous-dossier par chapitre contenant `Recherche-MacArthur-<Épître>-<n>.{json,md,html,pdf}` (skill `sermon-research`, `"passage": "<Épître> <n>"`), où `verses` contient l'intégralité des versets du chapitre dans la NEG79.
3. `Plan-Serie-<Épître>-1-<N>.{md,pdf}` : plan de série homilétique en Markdown calqué sur `Galates/Plan-Serie-Galates-1-6.md` et `1-Thessaloniciens/Plan-Serie-1-Thessaloniciens-1-5.md` (idée et phrase de la série, progression par blocs, tableau récapitulatif, puis pour chaque chapitre : sermons GTY, textes d'appui, idée centrale, phrase à faire retenir, but, étapes, développement exégétique, application et transition).
4. `index.html` : portail autonome (CSS et JS en ligne, thème sombre noir et orange `#0a0a0a` / `#e8843c`, aucune ressource externe), calqué sur `Galates/index.html` et `1-Thessaloniciens/index.html` en adaptant la grille `.barre__puces` au nombre de chapitres (`repeat(N, minmax(0, 1fr))`) et la grille `.sommaire` au nombre de blocs de l'épître.

## Génération et vérification

- **Recherches (`sermon-research`).** Le fichier `.json` est l'unique source de vérité; `.md`, `.html` et `.pdf` sont générés par :
  `uv run --with reportlab python "C:\Users\agbru\.gemini\config\skills\sermon-research\assets\generate.py" <chemin.json>`
  Toute correction s'effectue dans le `.json` avant régénération.
- **PDF du plan de série.** Le fichier `Plan-Serie-<Épître>-1-<N>.pdf` est produit à partir de son `.md` via `pandoc -f markdown+lists_without_preceding_blankline -s --embed-resources` (feuille CSS Letter, marges `18mm 18mm 16mm`, police Georgia `11pt`, titres `#1A2A40`, filets `#B8862B` et `#d9c9a3`, `header#title-block-header { display: none; }`) puis rendu par Chrome ou Edge en mode `--headless --disable-gpu --no-pdf-header-footer`.
- **Contrôles de clôture.** Avant de livrer une épître :
  - vérifier par script l'existence et la non-vacuité des `4 × N + 7` fichiers, l'absence de tiret cadratin (`\u2014`) dans tous les fichiers `.json`, `.md` et `.html`, et la résolution de tous les liens relatifs et ancres (`#...`) dans `index.html` et `Plan-Serie-<Épître>-1-<N>.md`;
  - vérifier que toutes les citations bibliques de la NEG79 dans le plan et dans `index.html` correspondent mot pour mot au texte de référence;
  - mettre à jour l'état de l'épître dans la table chronologique de `README.md`.
