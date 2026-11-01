#pragma once
#include <Arduino.h>
#include <vector>

struct ScheduleEntry {
    String line;
    String direction;
    String time; // "HH:MM"
};

// Network Fetch, returns false if the data could not be fetched
bool fetchScheduleFromServer(const String& busStopId, const String& busStopNr, std::vector<ScheduleEntry> &schedules);

// Removes buses from the vector that have already departed (based on current time)
void removePastSchedules(std::vector<ScheduleEntry> &schedules);

// Converts "14:00" to "5 min" for display
std::vector<ScheduleEntry> convertScheduleTimesToMinutesLeft(const std::vector<ScheduleEntry> &schedules);