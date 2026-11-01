# (line, direction, minutes to the first departure, minutes between departures)
ROUTES = [
    ("131", "Dw. Centralny", 3, 10),
    ("131", "Metro Marymont", 6, 12),
    ("175", "Lotnisko Chopina", 8, 15),
    ("523", "Dw. Wschodni", 2, 20),
]

# ZTM writes night departures past 24:00 of the same service day
NIGHT_DEPARTURE = {"linia": "N32", "kierunek": "Dw. Centralny", "czas": "24:10:00"}
DEPARTURES_PER_ROUTE = 3

def format_time(minutes: int) -> str:
    hours, mins = divmod(minutes, 60)
    return f"{hours:02d}:{mins:02d}:00"

# Sample departures for the demo mode, relative to the given time of day
def get_mock_schedule(current_time_in_minutes: int):
    schedules = [
        {
            "linia": line,
            "kierunek": direction,
            "czas": format_time(current_time_in_minutes + first + n * interval),
        }
        for line, direction, first, interval in ROUTES
        for n in range(DEPARTURES_PER_ROUTE)
    ]
    schedules.append(dict(NIGHT_DEPARTURE))
    return schedules
