# ==============================================================================
# PARAMÈTRES ET JOUEURS
# ==============================================================================
PLAYERS = [
    "Thieuthieu-21285",
    "Zenitude-21178",
    "Nao-21448",
    "leCongolais-21758",
    "badslayeur-2534",
    "Colbern-2193",
    "Jhonasse-2487",
    "lasthigh-21178",
    "Tomix-21443",
    "Aupif-21480",
]

BASE_URL = "https://overfast-api.tekrop.fr/players"
MODES = ["quickplay", "competitive"]

# Temps de jeu minimum (en heures) pour être inclus dans le classement
MIN_HOURS_THRESHOLD = 10.0

# Dossier de destination des exports
OUTPUT_DIR = "results"

# ==============================================================================
# COEFFICIENTS (Entre 0.0 et 1.0)
# ==============================================================================
COEFFICIENTS_TANK = {
    "Winrate_%": 0.5,
    "KDA": 0.8,
    "Morts_Moyenne": 0.0,
    "Elims_Moyenne": 0.7,
    "Assists_Moyenne": 0.3,
    "Degats_Moyenne": 0.7,
    "Soins_Moyenne": 0.0,
    "Temps_Jeu_Heures": 0.0,
    "Parties_Jouées": 0.0,
}

COEFFICIENTS_DAMAGE = {
    "Winrate_%": 0.5,
    "KDA": 0.5,
    "Morts_Moyenne": 0.0,
    "Elims_Moyenne": 0.9,
    "Assists_Moyenne": 0.3,
    "Degats_Moyenne": 0.7,
    "Soins_Moyenne": 0.1,
    "Temps_Jeu_Heures": 0.0,
    "Parties_Jouées": 0.0,
}

COEFFICIENTS_SUPPORT = {
    "Winrate_%": 0.5,
    "KDA": 0.2,
    "Morts_Moyenne": 0.0,
    "Elims_Moyenne": 0.5,
    "Assists_Moyenne": 0.7,
    "Degats_Moyenne": 0.3,
    "Soins_Moyenne": 1,
    "Temps_Jeu_Heures": 0.0,
    "Parties_Jouées": 0.0,
}

ROLE_CONFIGS = {
    "Tank": COEFFICIENTS_TANK,
    "Damage": COEFFICIENTS_DAMAGE,
    "Support": COEFFICIENTS_SUPPORT,
}

INVERTED_METRICS = {"Morts_Moyenne", "Morts_Total", "Parties_Perdues"}