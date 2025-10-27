"""Messages localisés en français pour Bataille Navale."""

from __future__ import annotations

from typing import Dict

MESSAGES: Dict[str, str] = {
    "app_title": "Bataille Navale",
    "console_welcome": "Bienvenue dans Bataille Navale !",
    "console_instructions": (
        "Entrez des coordonnées (par ex. B7). Tapez 'quit' pour abandonner."
    ),
    "console_player_grid": "Grille du joueur",
    "console_target_grid": "Grille de tir",
    "console_invalid_input": "Entrée invalide : {detail}",
    "console_already_shot": "Vous avez déjà tiré sur {coord}",
    "console_hit": "Touché !",
    "console_miss": "À l'eau...",
    "console_sunk": "{ship} coulé !",
    "console_player_turn": "À vous de jouer : ",
    "console_ai_turn": "L'IA tire sur {coord} : {result}",
    "console_victory": "Victoire ! Vous avez coulé toute la flotte ennemie.",
    "console_defeat": "Défaite... Votre flotte est coulée.",
    "console_summary": "Tirs : {shots} | Touchés : {hits} | Précision : {accuracy:.1f}%",
    "console_quit": "Fin de la partie.",
    "status_turn_player": "À vous de jouer",
    "status_turn_ai": "Tour de l'IA",
    "status_shots": "Tirs : {shots} | Touches : {hits} | Précision : {accuracy:.1f}%",
    "status_remaining": "Navires restants : {count}",
    "menu_new_game": "Nouvelle partie",
    "menu_save": "Sauvegarder",
    "menu_load": "Charger",
    "menu_settings": "Paramètres",
    "menu_quit": "Quitter",
    "dialog_save_success": "Partie sauvegardée avec succès.",
    "dialog_save_error": "Erreur lors de la sauvegarde : {error}",
    "dialog_load_success": "Partie chargée.",
    "dialog_load_error": "Impossible de charger : {error}",
    "dialog_settings_title": "Paramètres",
    "dialog_settings_grid_size": "Taille de la grille",
    "dialog_settings_ai": "Niveau de l'IA",
    "dialog_settings_fleet": "Flotte",
    "dialog_settings_confirm": "Confirmer",
    "dialog_settings_cancel": "Annuler",
    "placement_instruction": "Placez vos navires : clic pour ancre, R pour pivoter",
    "placement_error": "Placement invalide",
    "placement_done": "Placement terminé",
    "ai_level_basic": "Basique",
    "ai_level_hunter": "Chasseur",
    "file_dialog_title": "Sélectionnez un fichier",
    "stats_updated": "Statistiques mises à jour.",
}


def tr(key: str, **kwargs: object) -> str:
    """Retourne le message localisé pour *key* formaté avec *kwargs*."""

    message = MESSAGES[key]
    if kwargs:
        return message.format(**kwargs)
    return message
