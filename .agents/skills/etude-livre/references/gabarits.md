# Gabarits du plan de série et du portail HTML

Ce document précise la structure du fichier `Plan-Serie-<Livre>-1-<N>.md` et le schéma JSON attendu par la sous-commande `portal` de `scripts/etude_livre.py`.

---

## 1. Structure de `Plan-Serie-<Livre>-1-<N>.md`

Pour un livre à chapitre unique (Abdias, Philémon, 2 Jean, 3 Jean, Jude), remplacer `1-<N>` par `1` dans les noms de fichiers. Aucun tiret cadratin (`\u2014`) ne doit figurer dans le fichier; utiliser `:`, `;`, `,` ou `-`.

```markdown
# Plan de série : <Nom du livre> 1 à <N>

**<Sous-titre thématique du livre>**
*Série de <N> prédications expositives (un chapitre par sermon) selon la perspective de John MacArthur*

- **Texte biblique :** Nouvelle Édition de Genève 1979 (NEG79)
- **Recherche d'ensemble sur le livre :** [`Sommaire/Recherche-MacArthur-<Slug>-1-<N>.pdf`](Sommaire/Recherche-MacArthur-<Slug>-1-<N>.pdf) ([version HTML](Sommaire/Recherche-MacArthur-<Slug>-1-<N>.html) · [Markdown](Sommaire/Recherche-MacArthur-<Slug>-1-<N>.md))

---

## Vue d'ensemble de la série

- **Idée centrale de la série :** <1 paragraphe résumant la thèse théologique du livre selon MacArthur>
- **Phrase de la série :** *« <Formule mémorisable en une phrase> »*
- **Progression homilétique :**
  1. **<Titre du bloc I> (ch. <x> à <y>)** : <synthèse du bloc>
  2. **<Titre du bloc II> (ch. <y+1> à <z>)** : <synthèse du bloc>

### Tableau récapitulatif des <N> sermons

| # | Chapitre | Bloc structurel | Titre du sermon | Verset clé | Recherche du chapitre |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | <Livre> 1 | I. <Nom court du bloc> | *<Titre du sermon 1>* | <Abrév.> 1.<v> | [`01-<Slug>-1`](01-<Slug>-1/Recherche-MacArthur-<Slug>-1.pdf) |
```

Pour chaque bloc structurel, insérer un titre de niveau 2 (`## PREMIÈRE PARTIE : ... (CHAPITRES <x> À <y>)`), suivi d'une section par chapitre :

```markdown
### Sermon <n> : <Titre du sermon> (<Livre> <n>.1-<dernier_verset>)

- **Dossier de recherche :** [`0<n>-<Slug>-<n>/Recherche-MacArthur-<Slug>-<n>.pdf`](0<n>-<Slug>-<n>/Recherche-MacArthur-<Slug>-<n>.pdf) ([HTML](0<n>-<Slug>-<n>/Recherche-MacArthur-<Slug>-<n>.html) · [Markdown](0<n>-<Slug>-<n>/Recherche-MacArthur-<Slug>-<n>.md))
- **Sermons de référence de John MacArthur (Grace to You) :**
  - *<Titre anglais>* (`<code GTY>`, `<plage>`) - <Titre français traduit>
- **Textes d'appui (Ancien et Nouveau Testament) :** <liste de renvois commentés>
- **Verset clé :**
  > « <Citation exacte mot pour mot dans la NEG79> » (<Livre> <n>.<v>, NEG79)

#### Orientation homilétique

- **Idée centrale :** <1 phrase énonçant le thème exégétique du chapitre>
- **Phrase à faire retenir :** *« <1 phrase percutante destinée à l'auditoire> »*
- **But du sermon :** <objectif pastoral et doctrinal>

#### Étapes du sermon

1. **<Titre du point 1> (<n>.<a>-<b>)** : <résumé>
   - *Sous-points :* <détail des versets>
2. **<Titre du point 2> (<n>.<c>-<d>)** : <résumé>
   - *Sous-points :* <détail des versets>

#### Développement exégétique et homilétique

##### Introduction
<Mise en contexte historique, lien avec le chapitre précédent et prise en compte explicite de toute charnière inter-chapitres>

##### 1. <Titre du point 1> (<n>.<a>-<b>)
<Exposition verset par verset intégrant la syntaxe grecque ou hébraïque, les termes clés translittérés, l'exégèse de MacArthur et les citations exactes de la NEG79>

##### Application et pistes de réflexion pastorale
- **<Axe 1> :** <question et interpellation concrète>
- **<Axe 2> :** <question et interpellation concrète>

##### Transition vers le Sermon <n+1> (ou Conclusion de la série pour le dernier chapitre)
<Pont homilétique vers le chapitre suivant>
```

Pour un livre de l'Ancien Testament où Grace to You ne compte aucun sermon séquentiel de niveau 1 sur le chapitre, remplacer la ligne **Sermons de référence** par les sources de niveaux 2 à 5 effectivement vérifiées (*MacArthur Study Bible*, *MacArthur Bible Commentary*, sermons thématiques GTY avec leur code, ou ouvrages de MacArthur).

---

## 2. Schéma JSON pour `etude_livre.py portal`

La sous-commande `portal` prend un fichier JSON (`--spec`) et génère `<Livre>/index.html` avec la feuille de style sombre et orange (`#0a0a0a` / `#e8843c`), les grilles adaptatives `--n-puces` et `--n-blocs`, et le script `IntersectionObserver` :

```json
{
  "book": "2 Thessaloniciens",
  "date_fr": "19 avril 2026",
  "series_title": "Debout dans la vérité face au jour du Seigneur",
  "series_phrase": "Parce que le Seigneur Jésus-Christ manifestera sa juste rétribution lors de sa révélation glorieuse et anéantira l'homme du péché après l'apostasie, l'Église persécutée ne doit ni se laisser ébranler par les contrefaçons eschatologiques ni sombrer dans l'oisiveté, mais demeurer ferme dans la vérité apostolique et travailler dans la paix.",
  "sommaire": {
    "key_verse_text": "Ainsi donc, frères, demeurez fermes, et retenez les instructions que nous vous avons données, soit de vive voix, soit par notre lettre.",
    "key_verse_ref": "2\u00a0Thessaloniciens 2.15",
    "lead": "Synthèse historique, textuelle, lexicale et théologique de la deuxième épître (Corinthe, vers 51-52 apr.\u00a0J.-C.)\u00a0: la consolation dans la fournaise des persécutions, le programme prophétique du jour du Seigneur et la discipline fraternelle face aux désordonnés.",
    "meta": "10\u00a0sermons GTY (<span class=\"nw\">53-1</span> à <span class=\"nw\">53-10</span>) · 9\u00a0mots-clés grecs · 7\u00a0axes doctrinaux"
  },
  "movements": [
    {
      "ref": "Ch.\u00a01",
      "label": "<strong>La consolation eschatologique</strong> dans la persécution (la rétribution au retour de Christ)"
    },
    {
      "ref": "Ch.\u00a02",
      "label": "<strong>La correction doctrinale</strong> sur le jour du Seigneur (l'apostasie, l'homme du péché et l'élection)"
    },
    {
      "ref": "Ch.\u00a03",
      "label": "<strong>La conduite pratique</strong> dans l'attente du retour (la prière, la discipline et le travail paisible)"
    }
  ],
  "blocks": [
    {
      "ch_label": "Chapitre\u00a01",
      "short_title": "Consolation dans la persécution",
      "full_title": "La consolation eschatologique dans la persécution",
      "subtitle": "Chapitre\u00a01 · Sermons GTY <span class=\"nw\">53-1</span> à <span class=\"nw\">53-3</span> · L'endurance des saints et la juste rétribution de Christ",
      "sermons": [
        {
          "num": 1,
          "span_label": "2\u00a0Thessaloniciens 1.1-12",
          "verses_count": 12,
          "title": "La gloire de Dieu dans la fournaise de l'affliction",
          "key_verse_text": "C'est pourquoi aussi nous prions continuellement pour vous, afin que notre Dieu vous juge dignes de la vocation, et qu'il accomplisse par sa puissance tous les desseins bienveillants de sa bonté, et l'œuvre de votre foi",
          "key_verse_ref": "2\u00a0Thessaloniciens 1.11",
          "phrase": "Le feu de la persécution ne trahit jamais l'abandon de Dieu\u00a0: il révèle l'authenticité de notre foi aujourd'hui et prépare la révélation glorieuse de Christ qui rendra justice à son peuple.",
          "idea": "Dans l'attente de la révélation flamboyante du Seigneur Jésus, Dieu fait grandir la foi et la charité de son Église éprouvée, promettant le repos éternel aux croyants affligés et la juste rétribution à leurs persécuteurs afin que le nom de Christ soit glorifié en ses saints.",
          "steps": [
            {
              "title": "Une croissance spirituelle qui honore Dieu au cœur de la fournaise",
              "ref": "1.1-4"
            },
            {
              "title": "Une justice eschatologique qui rétribue chaque camp au retour de Christ",
              "ref": "1.5-10"
            },
            {
              "title": "Une intercession apostolique qui soutient l'Église jusqu'à la gloire",
              "ref": "1.11-12"
            }
          ],
          "gty_sermons": [
            {
              "code": "53-1",
              "title": "Thanking God for Persecuted Believers",
              "ref": "1.1-4"
            }
          ]
        }
      ]
    }
  ]
}
```

### Règles de formatage dans `spec.json`
- Le champ `"gty_sermons"` d'un sermon est optionnel (utile pour les chapitres de l'Ancien Testament sans sermon GTY séquentiel).
- Le nombre de sermons à travers l'ensemble de `"blocks"` doit être égal au nombre de chapitres du livre (`1` à `N` dans l'ordre).
- Les références bibliques ou codes susceptibles d'être coupés en fin de ligne peuvent utiliser `\u00a0` (espace insécable) ou `<span class="nw">...</span>`.
