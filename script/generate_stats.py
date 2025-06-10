#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import sys
import os
from datetime import datetime

# === FONCTIONS CLÉS DE TON SCRIPT ORIGINAL ===

def verifier_dependances():
    try:
        import requests
        print("✅ Dépendances OK")
        return True
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        return False

def obtenir_headers_nba():
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'stats.nba.com',
        'Referer': 'https://www.nba.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-nba-stats-origin': 'stats',
        'x-nba-stats-token': 'true'
    }

def appel_api_nba(endpoint, params):
    url = f"https://stats.nba.com/stats/{endpoint}"
    headers = obtenir_headers_nba()
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erreur API {response.status_code} pour {endpoint}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion pour {endpoint}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON pour {endpoint}: {e}")
        return None

def calculer_efficiency(pts, reb, ast, stl, blk, fgm, ftm, fga, fta, tov):
    try:
        eff = (pts + reb + ast + stl + blk) - (fga - fgm) - (fta - ftm) - tov
        return eff
    except:
        return 0

def recuperer_toutes_stats():
    print("\n🏀 RÉCUPÉRATION COMPLÈTE DES STATS NBA")
    print("=" * 60)

    params_base = {
        'College': '', 'Conference': '', 'Country': '', 'DateFrom': '', 'DateTo': '',
        'Division': '', 'DraftPick': '', 'DraftYear': '', 'GameScope': '',
        'GameSegment': '', 'Height': '', 'LastNGames': '0', 'LeagueID': '00',
        'Location': '', 'MeasureType': 'Base', 'Month': '0', 'OpponentTeamID': '0',
        'Outcome': '', 'PORound': '0', 'PaceAdjust': 'N', 'PerMode': 'Totals',
        'Period': '0', 'PlayerExperience': '', 'PlayerPosition': '', 'PlusMinus': 'N',
        'Rank': 'N', 'Season': '2024-25', 'SeasonSegment': '', 'SeasonType': 'Regular Season',
        'ShotClockRange': '', 'StarterBench': '', 'TeamID': '0', 'TwoWay': '0',
        'VsConference': '', 'VsDivision': '', 'Weight': ''
    }

    data_base = appel_api_nba('leaguedashplayerstats', params_base)
    if not data_base:
        return None

    time.sleep(2)

    params_adv = params_base.copy()
    params_adv['MeasureType'] = 'Advanced'
    data_adv = appel_api_nba('leaguedashplayerstats', params_adv)

    players_data = []
    if data_base and 'resultSets' in data_base:
        result_base = data_base['resultSets'][0]
        headers_base = result_base['headers']
        rows_base = result_base['rowSet']

        indices = {col: headers_base.index(col) if col in headers_base else None for col in [
            'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN',
            'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV',
            'FGM', 'FGA', 'FG_PCT', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT'
        ]}

        stats_adv_dict = {}
        if data_adv and 'resultSets' in data_adv:
            result_adv = data_adv['resultSets'][0]
            headers_adv = result_adv['headers']
            rows_adv = result_adv['rowSet']
            try:
                pid_idx = headers_adv.index('PLAYER_ID')
                for row in rows_adv:
                    stats_adv_dict[row[pid_idx]] = {
                        'off_rating': row[headers_adv.index('OFF_RATING')],
                        'def_rating': row[headers_adv.index('DEF_RATING')],
                        'net_rating': row[headers_adv.index('NET_RATING')],
                        'ts_pct': row[headers_adv.index('TS_PCT')],
                        'usg_pct': row[headers_adv.index('USG_PCT')],
                        'pie': row[headers_adv.index('PIE')]
                    }
            except:
                pass

        for row in rows_base:
            try:
                gp = row[indices['GP']] or 0
                if gp < 16:
                    continue

                player_id = row[indices['PLAYER_ID']]
                eff = calculer_efficiency(
                    row[indices['PTS']], row[indices['REB']], row[indices['AST']], row[indices['STL']],
                    row[indices['BLK']], row[indices['FGM']], row[indices['FTM']],
                    row[indices['FGA']], row[indices['FTA']], row[indices['TOV']]
                )

                stats_adv = stats_adv_dict.get(player_id, {})
                players_data.append({
                    'player_id': player_id,
                    'joueur': row[indices['PLAYER_NAME']],
                    'equipe': row[indices['TEAM_ABBREVIATION']],
                    'gp': gp,
                    'minutes': round(row[indices['MIN']] / gp, 1) if gp else 0,
                    'points': round(row[indices['PTS']] / gp, 1),
                    'rebounds': round(row[indices['REB']] / gp, 1),
                    'assists': round(row[indices['AST']] / gp, 1),
                    'steals': round(row[indices['STL']] / gp, 1),
                    'blocks': round(row[indices['BLK']] / gp, 1),
                    'turnovers': round(row[indices['TOV']] / gp, 1),
                    'fg_pct': round(row[indices['FG_PCT']], 3),
                    'fg3_pct': round(row[indices['FG3_PCT']], 3),
                    'ft_pct': round(row[indices['FT_PCT']], 3),
                    'efficiency': round(eff / gp, 1) if gp else 0,
                    'off_rating': round(stats_adv.get('off_rating', 0), 1),
                    'def_rating': round(stats_adv.get('def_rating', 0), 1),
                    'net_rating': round(stats_adv.get('net_rating', 0), 1),
                    'ts_pct': round(stats_adv.get('ts_pct', 0), 3),
                    'usg_pct': round(stats_adv.get('usg_pct', 0), 3),
                    'pie': round(stats_adv.get('pie', 0), 3)
                })
            except:
                continue

    players_data.sort(key=lambda x: x['efficiency'], reverse=True)
    return players_data

# === FONCTION JSON ===

def enregistrer_json(players_data, dossier="data_output"):
    if not players_data:
        print("❌ Aucune donnée à enregistrer.")
        return None

    os.makedirs(dossier, exist_ok=True)
    filepath = os.path.join(dossier, "nba_stats.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(players_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Données enregistrées dans {filepath}")
    return filepath

# === MAIN ===

def main():
    print("🔥 NBA STATS JSON GENERATOR")
    if not verifier_dependances():
        sys.exit(1)

    players_data = recuperer_toutes_stats()
    if players_data:
        enregistrer_json(players_data)
    else:
        print("❌ Erreur traitement données : 'NoneType' object is not subscriptable")

if __name__ == "__main__":
    main()
