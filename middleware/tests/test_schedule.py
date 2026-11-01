import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main
from main import MAX_SCHEDULES, minutes_until

def test_minutes_until_same_day():
    assert minutes_until("10:30:00", 600) == 30

def test_minutes_until_past_time_wraps_to_next_day():
    assert minutes_until("10:00:00", 660) == 1380

def test_minutes_until_across_midnight():
    # 23:50 -> 00:15
    assert minutes_until("00:15:00", 23 * 60 + 50) == 25

def test_minutes_until_after_24h_time():
    # 24:10 is 00:10 of the next day
    assert minutes_until("24:10:00", 23 * 60 + 50) == 20

def test_minutes_until_late_night_time():
    # 29:02 is 05:02 of the next day
    assert minutes_until("29:02:00", 23 * 60 + 50) == 312

def test_mock_mode_needs_no_api(monkeypatch):
    def fail(*args):
        raise AssertionError("ZTM API called in mock mode")

    monkeypatch.setenv("MOCK", "1")
    monkeypatch.setattr(main, "get_stop_schedule_all_lines", fail)

    current = 23 * 60 + 50
    schedules = main.get_stop_schedule("7009", "01", current)

    waits = [minutes_until(s["czas"], current) for s in schedules]
    assert 0 < len(schedules) <= MAX_SCHEDULES
    assert waits == sorted(waits)
    assert len({s["linia"] for s in schedules}) > 1
    assert any(s["czas"].startswith("24:") for s in schedules)
    assert all(set(s) == {"linia", "kierunek", "czas"} for s in schedules)
