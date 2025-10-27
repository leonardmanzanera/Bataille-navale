# BatailleNavale

## Aperçu technique
- **Architecture** : séparation stricte modèle/logique/IHM. Les modules `model.py`, `rules.py` et `game.py` décrivent le domaine, les entrées/sorties console sont dans `cli.py`, la GUI Tkinter dans `view_tk.py`, et `controller.py` sert de médiateur.
- **Invariants** : grilles carrées 8×8 à 12×12, navires rectilignes horizontaux/verticaux, absence de chevauchement. Chaque tir est unique et renvoie `manqué`, `touché` ou `coulé`.
- **Protocoles de tir** : IA basique = tir aléatoire sans répétition, IA chasseur = basique + file de priorités sur les voisins orthogonaux d'un impact jusqu'à destruction du navire.
- **Persistance macOS** : sauvegardes (`*.bn-save.json`) et statistiques (`stats.json`) stockées dans `~/Library/Application Support/BatailleNavale/`.

## Installation (macOS ≥ 13)
1. Installer Python 3.11 (par ex. via [python.org](https://www.python.org/downloads/mac-osx/)).
2. Cloner ce dépôt puis se placer dans le dossier `BatailleNavale`.
3. (Optionnel) Créer un environnement virtuel :
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
4. Installer les dépendances de test :
   ```bash
   python3 -m pip install pytest coverage
   ```

## MVP console
Lancer une partie déterministe :
```bash
python -m bataille_navale.cli --seed 123 --log-level INFO
```
Extrait de partie (seed 123) :
```
Bienvenue dans Bataille Navale !
Entrez des coordonnées (par ex. B7). Tapez 'quit' pour abandonner.

Grille du joueur
   A B C D E F G H I J
 1 ■ ■ ■ ~ ~ ~ ~ ~ ~ ~
 2 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 3 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 5 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 6 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 7 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 8 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 9 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
10 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

Grille de tir
   A B C D E F G H I J
 1 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
...
À vous de jouer : B7
Touché !
L'IA tire sur F4 : À l'eau...
```
Les récapitulatifs de fin indiquent tirs, touches et précision.

## Interface graphique Tkinter
Démarrage avec IA chasseur et grille 10×10 :
```bash
python -m bataille_navale.view_tk --ai-level chasseur --grid-size 10
```
Fonctionnalités principales :
- Placement manuel : clic gauche pour l'ancre du navire courant, touche **R** pour alterner horizontal/vertical, prévisualisation colorée (vert = valide, rouge = invalide).
- Commandes :
  - **N** nouvelle partie (placement manuel par défaut).
  - **S** sauvegarder (choix du fichier `.bn-save.json`).
  - **C** charger une sauvegarde existante.
  - **P** ouvrir les paramètres (taille, flotte, IA).
  - **Q** quitter l'application.
- Feedback visuel :
  - Manqué = point sombre.
  - Touché = croix rouge avec flash vert/rouge.
  - Coulé = silhouette rouge pleine.
- Panneau de statut : tours, nombre de tirs, précision, navires restants, statistiques globales.

## Sauvegardes & statistiques
- Sauvegarde (`*.bn-save.json`) : contient la grille, les tirs, le tour courant, la flotte, le niveau d'IA et l'état RNG (`random.getstate()` sérialisé).
- Statistiques (`stats.json`) : compte parties, victoires, tirs, touches, navires coulés et résultats par niveau d'IA.
- Emplacement par défaut : `~/Library/Application Support/BatailleNavale/` (créé automatiquement).

## Tests & couverture
Lancer la suite :
```bash
pytest
```
Mesurer la couverture (génère `coverage.xml`, seuil ≥ 85 %) :
```bash
python -m coverage run -m pytest
python -m coverage xml
```

## Dépannage
- **Aucun affichage GUI** : vérifier que Python utilise la version macOS officielle (Tk inclus) ou installer `python-tk` via Homebrew.
- **Permissions refusées sur App Support** : créer le dossier manuellement (`mkdir -p ~/Library/Application\ Support/BatailleNavale`).
- **Placement impossible** : se référer au message “Placement invalide”, utiliser R pour pivoter puis cliquer sur une zone dégagée.

## Licence
Distribué sous licence MIT (voir `LICENSE`).
