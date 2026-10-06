import requests
import json
import os
import time
from collections import defaultdict
import heroes
import config

def get_player_stats(player_id, gamemode):
    """Effectue l'appel API Overfast pour récupérer les statistiques de carrière d'un joueur."""
    url = f"{config.BASE_URL}/{player_id}/stats/career"
    params = {"gamemode": gamemode}
    
    print(f" -> Récupération de {player_id} ({gamemode})...")
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"    [!] Profil introuvable pour {player_id}.")
        elif response.status_code == 403:
            print(f"    [!] Profil privé pour {player_id}.")
        else:
            print(f"    [!] Erreur API ({response.status_code}) pour {player_id}.")
    except Exception as e:
        print(f"    [!] Erreur de connexion : {e}")
    
    return None

def extract_stats(hero_data):
    """Aplatit les données du héros qu'elles soient en listes ou en dictionnaires."""
    flat = {}
    for category, content in hero_data.items():
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and 'key' in item and 'value' in item:
                    flat[item['key']] = item['value']
        elif isinstance(content, dict):
            for k, v in content.items():
                flat[k] = v
        else:
            flat[category] = content
            
    return {
        'time_played': flat.get('time_played', 0),
        'games_won': flat.get('games_won', 0),
        'games_played': flat.get('games_played', 0),
        'eliminations': flat.get('eliminations', 0),
        'assists': flat.get('assists', 0),
        'deaths': flat.get('deaths', 0),
        'damage_done': flat.get('hero_damage_done', flat.get('damage_done', flat.get('all_damage_done', flat.get('damage', 0)))),
        'healing_done': flat.get('healing_done', flat.get('healing', 0))
    }

def calculate_norm(val, min_v, max_v, is_inv=False):
    """Calcule la valeur normalisée (entre 0 et 1) pour une statistique donnée."""
    if min_v >= max_v:
        return 1.0 
    norm = (val - min_v) / (max_v - min_v)
    if is_inv:
        norm = 1.0 - norm
    return max(0.0, min(1.0, norm))

def main():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    player_totals = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    
    seuil_heures = getattr(config, 'MIN_HOURS_THRESHOLD', 0.0)
    print(f"=== DEBUT DU TRAITEMENT (Filtre visé: {seuil_heures} heures) ===")
    
    for player_id in config.PLAYERS:
        pseudo = player_id.split('-')[0]
        
        for mode in config.MODES:
            data = get_player_stats(player_id, mode)

            if not data:
                continue
            
            heroes_data_api = data.get("heroes_stats", data) 
            
            for hero_key, hero_data in heroes_data_api.items():
                if hero_key not in heroes.HERO_ROLES:
                    continue
                
                flat = extract_stats(hero_data)
                
                player_totals[pseudo][hero_key]['time_played'] += flat['time_played']
                player_totals[pseudo][hero_key]['games_won'] += flat['games_won']
                player_totals[pseudo][hero_key]['games_played'] += flat['games_played']
                player_totals[pseudo][hero_key]['eliminations'] += flat['eliminations']
                player_totals[pseudo][hero_key]['assists'] += flat['assists']
                player_totals[pseudo][hero_key]['deaths'] += flat['deaths']
                player_totals[pseudo][hero_key]['healing_done'] += flat['healing_done']
                player_totals[pseudo][hero_key]['damage_done'] += flat['damage_done']

            time.sleep(0.3) 
            
    # Stockage temporaire brut avant filtrage
    raw_roles_data = {"Tank": defaultdict(list), "Damage": defaultdict(list), "Support": defaultdict(list)}
    
    print("\n=== CALCUL DES MOYENNES ===")
    for pseudo, heroes_data in player_totals.items():
        for hero, totals in heroes_data.items():
            if totals['time_played'] <= 0:
                continue
                
            time_hours = totals['time_played'] / 3600
            time_10min = totals['time_played'] / 600
            
            winrate = (totals['games_won'] / totals['games_played'] * 100) if totals['games_played'] > 0 else 0.0
            
            deaths = totals['deaths'] if totals['deaths'] > 0 else 1
            kda = (totals['eliminations'] + totals['assists']) / deaths
            
            elims_avg = totals['eliminations'] / time_10min if time_10min > 0 else 0
            assists_avg = totals['assists'] / time_10min if time_10min > 0 else 0
            damage_avg = totals['damage_done'] / time_10min if time_10min > 0 else 0
            healing_avg = totals['healing_done'] / time_10min if time_10min > 0 else 0
            deaths_avg = totals['deaths'] / time_10min if time_10min > 0 else 0
            
            role = heroes.HERO_ROLES[hero]
            raw_roles_data[role][hero].append({
                "pseudo": pseudo,
                "Temps_Jeu_Heures": round(time_hours, 2),
                "Winrate_%": round(winrate, 2),
                "KDA": round(kda, 2),
                "Elims_Moyenne": round(elims_avg, 2),
                "Assists_Moyenne": round(assists_avg, 2),
                "Degats_Moyenne": round(damage_avg, 2),
                "Soins_Moyenne": round(healing_avg, 2),
                "Morts_Moyenne": deaths_avg
            })

    # Filtrage intelligent : on garantit au moins 2 joueurs si possible
    roles_data = {"Tank": defaultdict(list), "Damage": defaultdict(list), "Support": defaultdict(list)}
    
    print("=== FILTRAGE INTELLIGENT (Garantie de 2 joueurs min) ===")
    for role, heroes_dict in raw_roles_data.items():
        for hero, players_list in heroes_dict.items():
            # Tri préalable par temps de jeu
            players_list.sort(key=lambda x: x["Temps_Jeu_Heures"], reverse=True)
            
            # On applique le seuil
            filtered_players = [p for p in players_list if p["Temps_Jeu_Heures"] >= seuil_heures]
            
            # Si le filtre élimine trop de monde, on force l'ajout des top joueurs
            if len(filtered_players) < 2:
                filtered_players = players_list[:2]
                
            if filtered_players:
                roles_data[role][hero] = filtered_players

    final_json = {"Tank": {}, "Damage": {}, "Support": {}}
    print("\n=== CALCUL DES SCORES ET TRI ===")
    
    for role, heroes_dict in roles_data.items():
        coefs = config.ROLE_CONFIGS[role]
        total_coef = sum(coefs.values())
        
        for hero, players_list in heroes_dict.items():
            if not players_list:
                continue
                
            for p in players_list:
                score_total = 0
                for stat_name, coef in coefs.items():
                    if coef == 0 or stat_name not in p:
                        continue
                        
                    min_v = min(pl.get(stat_name, 0) for pl in players_list)
                    max_v = max(pl.get(stat_name, 0) for pl in players_list)
                    
                    val = p.get(stat_name, 0)
                    is_inv = stat_name in config.INVERTED_METRICS
                    
                    norm_val = calculate_norm(val, min_v, max_v, is_inv)
                    score_total += norm_val * coef
                
                p['score'] = round((score_total / total_coef) * 100, 2) if total_coef > 0 else 0.0

            # Tri par Score (décroissant), puis par Temps de jeu
            players_list.sort(key=lambda x: (x['score'], x['Temps_Jeu_Heures']), reverse=True)
            
            cleaned_list = []
            for p in players_list:
                cleaned_list.append({
                    "pseudo": p["pseudo"],
                    "score": p["score"],
                    "Temps_Jeu_Heures": p["Temps_Jeu_Heures"],
                    "Winrate_%": p["Winrate_%"],
                    "KDA": p["KDA"],
                    "Elims_Moyenne": p["Elims_Moyenne"],
                    "Assists_Moyenne": p["Assists_Moyenne"],
                    "Degats_Moyenne": p["Degats_Moyenne"],
                    "Soins_Moyenne": p["Soins_Moyenne"]
                })
                
            final_json[role][hero] = cleaned_list

        # Tri alphabétique des héros
        final_json[role] = dict(sorted(final_json[role].items()))

    output_file = os.path.join(config.OUTPUT_DIR, "classement.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=2, ensure_ascii=False)
        
    print(f"\n[SUCCES] JSON généré avec succès dans : {output_file}")

if __name__ == "__main__":
    main()