from pybaseball import statcast_batter
import pandas as pd

def summarize_matchup(batter_id, pitcher_id, pitcher_name, batter_name, game_id, opponent_team_name, today):
    try:
        df = statcast_batter('2022-01-01', str(today), batter_id)
    except Exception:
        return None

    df = df[df['pitcher'] == pitcher_id]

    if df.empty:
        return None

    plate_appearances = df['pa'].nunique() if 'pa' in df.columns else df['game_pk'].nunique()
    hits = df['events'].fillna('').str.contains('single|double|triple|home_run').sum()
    home_runs = df['events'].fillna('').str.contains('home_run').sum()
    strikeouts = df['events'].fillna('').str.contains('strikeout').sum()
    walks = df['events'].fillna('').str.contains('walk|intent_walk').sum()

    # Basic rate stats
    at_bats = df['at_bat'].sum() if 'at_bat' in df.columns else plate_appearances - walks
    avg = f"{hits / at_bats:.3f}" if at_bats > 0 else ".000"
    obp = f"{(hits + walks) / plate_appearances:.3f}" if plate_appearances > 0 else ".000"
    total_bases = df['events'].map({
        'single': 1, 'double': 2, 'triple': 3, 'home_run': 4
    }).fillna(0).sum()
    slg = f"{total_bases / at_bats:.3f}" if at_bats > 0 else ".000"
    ops = f"{float(obp) + float(slg):.3f}" if at_bats > 0 else ".000"

    matchup = {
        "date": str(today),
        "game_id": game_id,
        "pitcher_name": pitcher_name,
        "pitcher_id": pitcher_id,
        "batter_name": batter_name,
        "batter_id": batter_id,
        "opposing_team": opponent_team_name,
        "plate_appearances": int(plate_appearances),
        "hits": int(hits),
        "home_runs": int(home_runs),
        "strikeouts": int(strikeouts),
        "walks": int(walks),
        "avg": avg,
        "obp": obp,
        "slg": slg,
        "ops": ops
    }

    print(matchup)
