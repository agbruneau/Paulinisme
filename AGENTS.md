# Paulinisme

Ce dépôt réunit les études des treize épîtres de Paul dans l'ordre chronologique de leur rédaction selon John MacArthur (table et conventions générales dans `README.md`). Les dossiers `Galates/`, `1-Thessaloniciens/` et `2-Thessaloniciens/` servent d'implémentations de référence.

## Conventions du dépôt

- **Un sermon par chapitre.** Le plan de série d'un livre compte autant de prédications que le livre compte de chapitres (`N` chapitres = `N` sermons), regroupés selon les grands blocs structurels que dégage MacArthur. Ce découpage par chapitre prime sur le découpage par péricopes de la skill `sermon-series`.
- **Charnières.** Lorsqu'une unité de pensée du texte ou un sermon Grace to You (GTY) enjambe une frontière de chapitre (p. ex. `Galates 1.11-2.10` ou `1 Thessaloniciens 2.17-3.13`), la recherche et le plan en rendent compte dans l'introduction et la transition des chapitres concernés.
- **Livrables (`4 × N + 7` fichiers par dossier `<Livre>/`).** Recherche globale dans `Sommaire/`, recherches par chapitre dans `01-<Livre>-1/` à `<pad(N)>-<Livre>-<N>/` (le `.json` est l'unique source de vérité), plan de série `Plan-Serie-<Livre>-<Plage>.{md,pdf}` et portail autonome `index.html`.
- **Production et vérification.** Utiliser la skill locale `etude-livre` (`.agents/skills/etude-livre/SKILL.md` et son outil CLI `.agents/skills/etude-livre/scripts/etude_livre.py`), puis mettre à jour la table chronologique de `README.md`.
- **Publication Git.** À la fin de chaque livraison dans ce dépôt, commiter tous les fichiers produits ou modifiés et les pousser directement sur la branche `main` (`git push origin main`) sans demander de confirmation préalable.
