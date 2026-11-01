from os import getenv

from mock_data import get_mock_schedule
from ztm_api import ZtmApiError, get_stop_schedule_all_lines

from fastapi import FastAPI, HTTPException
app = FastAPI()

MINUTES_PER_DAY = 1440
# The device keeps this many departures, a full timetable is over 50 KB
MAX_SCHEDULES = 15

def convert_time_to_int(time_str: str) -> int:
    hours, minutes, _ = map(int, time_str.split(":"))
    return hours * 60 + minutes

# ZTM writes night departures past 24:00 (up to 29:02), so wrap around the day
def minutes_until(time_str: str, current_time_in_minutes: int) -> int:
    return (convert_time_to_int(time_str) - current_time_in_minutes) % MINUTES_PER_DAY

@app.get("/get_stop_schedule")
def get_stop_schedule(busStopId: str, busStopNr: str, currentTimeInMinutes: int):
    # Demo mode, needs neither the API key nor the internet
    if getenv("MOCK") == "1":
        schedules = get_mock_schedule(currentTimeInMinutes)
    else:
        try:
            schedules = get_stop_schedule_all_lines(busStopId, busStopNr)
        except ZtmApiError as e:
            raise HTTPException(status_code=502, detail=str(e))
    schedules = sorted(schedules, key=lambda x: minutes_until(x['czas'], currentTimeInMinutes))
    return schedules[:MAX_SCHEDULES]
