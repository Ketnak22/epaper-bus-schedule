import requests

from functools import lru_cache
from os import getenv
from time import time
from dotenv import load_dotenv

load_dotenv()
ZTM_API_KEY = getenv("ZTM_API_KEY")

DEFAULT_HEADERS = {"Cache-Control": "no-cache"}

api_url = "https://api.um.warszawa.pl/api/action/dbtimetable_get/"
REQUEST_TIMEOUT_S = 10
CACHE_TTL_S = 3600

class ZtmApiError(Exception):
    pass

# Call the ZTM API and return its result list
def fetch_result(params):
    try:
        resp = requests.get(api_url,
            params={**params, "apikey": ZTM_API_KEY},
            headers=DEFAULT_HEADERS,
            timeout=REQUEST_TIMEOUT_S
        )
        resp.raise_for_status()
        body = resp.json()
    except requests.RequestException as e:
        # Only the type, the message contains the URL with the API key
        raise ZtmApiError(f"ZTM request failed: {type(e).__name__}") from None

    # Errors arrive with status 200 and a string in "result"
    if not isinstance(body.get('result'), list):
        raise ZtmApiError(f"ZTM API error: {body.get('error', body.get('result'))}")

    return body['result']

# Get available lines for a bus stop
def get_lines(bus_stop_id, bus_stop_nr):
    result = fetch_result({
        "id": "88cd555f-6f31-43ca-9de4-66c479ad5942",
        "busstopId": bus_stop_id,
        "busstopNr": bus_stop_nr
    })

    return [item['values'][0]['value'] for item in result]

# Get bus stop schedule for a specific line
def get_stop_schedule(bus_stop_id, bus_stop_nr, line):
    result = fetch_result({
        "id": "e923fa0e-d96c-43f9-ae6e-60518c9f3238",
        "busstopId": bus_stop_id,
        "busstopNr": bus_stop_nr,
        "line": line
    })

    formatted_resp = []
    for item in result:
        temp = {}
        for obj in item:
            if obj['key'] == 'kierunek':
                temp['kierunek'] = obj['value']
            if obj['key'] == 'czas':
                temp['czas'] = obj['value']
        if temp:
            temp['linia'] = line
            formatted_resp.append(temp)

    return formatted_resp

@lru_cache(maxsize=64)
def fetch_stop_schedule_all_lines(bus_stop_id, bus_stop_nr, cache_slot):
    lines = get_lines(bus_stop_id, bus_stop_nr)
    return [
        schedule 
        for line in lines 
        for schedule in get_stop_schedule(bus_stop_id, bus_stop_nr, line)
    ]

# Get bus stop schedule for all lines, cached since each fetch costs one request per line
def get_stop_schedule_all_lines(bus_stop_id, bus_stop_nr):
    return fetch_stop_schedule_all_lines(bus_stop_id, bus_stop_nr, int(time() // CACHE_TTL_S))