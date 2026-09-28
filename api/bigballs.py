import requests

from config import BBS_API_KEY


BASE_URL = "https://api.bigballsdata.com/v1"


def _headers():
    if not BBS_API_KEY:
        raise ValueError("BBS_API_KEY non configurata.")

    return {
        "Authorization": f"Bearer {BBS_API_KEY}"
    }


def _get(path, params=None):
    response = requests.get(
        f"{BASE_URL}{path}",
        headers=_headers(),
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


def get_leagues(sport="football"):
    return _get(
        "/leagues",
        {
            "sport": sport
        }
    )


def get_matches(league="seriea", sport="football"):
    return _get(
        "/matches",
        {
            "sport": sport,
            "league": league
        }
    )

def get_match(match_id, sport="football"):
    return _get(
        f"/matches/{match_id}",
        {
            "sport": sport
        }
    )


def get_lineups(match_id):
    return _get(
        f"/stored/matches/{match_id}/lineups"
    )


def get_match_stats(match_id):
    return _get(
        f"/stored/matches/{match_id}/stats"
    )


def get_match_events(match_id, sport="football"):
    return _get(
        f"/matches/{match_id}/events",
        {
            "sport": sport
        }
    )


def get_injuries(league="seriea"):
    return _get(
        "/injuries",
        {
            "league": league
        }
    )