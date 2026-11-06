import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

import main
from main import MAX_SCHEDULES, minutes_until
from ztm_api import ZtmApiError

client = TestClient(main.app)

PARAMS = {"busStopId": "7009", "busStopNr": "01", "currentTimeInMinutes": 600}

@pytest.fixture(autouse=True)
def real_api_mode(monkeypatch):
    # A local .env may turn the demo mode on
    monkeypatch.delenv("MOCK", raising=False)

def test_ztm_error_returns_502(monkeypatch):
    def fail(*args):
        raise ZtmApiError("ZTM API error: test")

    monkeypatch.setattr(main, "get_stop_schedule_all_lines", fail)

    resp = client.get("/get_stop_schedule", params=PARAMS)
    assert resp.status_code == 502
    assert resp.json()["detail"] == "ZTM API error: test"

def test_result_is_limited_and_sorted(monkeypatch):
    # Every 5 minutes from 00:00, so some have already left at 10:00
    schedules = [
        {"linia": "131", "kierunek": "Dw. Centralny", "czas": f"{m // 60:02d}:{m % 60:02d}:00"}
        for m in range(0, 24 * 60, 5)
    ]
    # Out of order on purpose, plus a night departure past 24:00
    schedules.reverse()
    schedules.append({"linia": "N32", "kierunek": "Dw. Centralny", "czas": "24:10:00"})
    monkeypatch.setattr(main, "get_stop_schedule_all_lines", lambda *args: schedules)

    resp = client.get("/get_stop_schedule", params=PARAMS)
    assert resp.status_code == 200
    body = resp.json()

    waits = [minutes_until(s["czas"], PARAMS["currentTimeInMinutes"]) for s in body]
    assert len(body) == MAX_SCHEDULES
    assert waits == sorted(waits)
    assert body[0]["czas"] == "10:00:00"

def test_health(monkeypatch):
    def fail(*args):
        raise AssertionError("ZTM API called by the health check")

    monkeypatch.setattr(main, "get_stop_schedule_all_lines", fail)

    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
