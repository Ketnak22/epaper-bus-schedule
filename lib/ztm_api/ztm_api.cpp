#include "ztm_api.h"
#include "secrets.h"

#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <algorithm> // for std::remove_if

// Helper to get current minutes from midnight
int getCurrentMinutes() {
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo, 0)) return -1;
    return timeinfo.tm_hour * 60 + timeinfo.tm_min;
}

// Helper: Parse "HH:MM" to minutes
int parseTimeStr(String timeStr) {
    int h = timeStr.substring(0, 2).toInt();
    int m = timeStr.substring(3, 5).toInt();
    return h * 60 + m;
}

static const int MINUTES_PER_DAY = 1440;
// A departure further back than this counts as tomorrow's
static const int MAX_MINUTES_PAST = 120;

// Helper: Minutes until a departure, negative if it already left.
// ZTM writes night departures past 24:00 (up to 29:02), so wrap around the day.
int minutesUntil(const ScheduleEntry &entry, int currentMins) {
    int diff = (parseTimeStr(entry.time) - currentMins + MAX_MINUTES_PAST) % MINUTES_PER_DAY;
    if (diff < 0) diff += MINUTES_PER_DAY;
    return diff - MAX_MINUTES_PAST;
}

bool fetchScheduleFromServer(const String& busStopId, const String& busStopNr, std::vector<ScheduleEntry> &schedules) {
    schedules.clear();

    if (WiFi.status() != WL_CONNECTED) return false;

    int currentMins = getCurrentMinutes();
    if (currentMins == -1) return false;

    WiFiClient client;
    HTTPClient http;

    // Request goes to the middleware, not the ZTM API
    String url = String(SERVER_URL) + "/get_stop_schedule" + 
                 "?busStopId=" + busStopId + 
                 "&busStopNr=" + busStopNr + 
                 "&currentTimeInMinutes=" + String(currentMins);

    http.setTimeout(5000); 
    http.begin(client, url);

    bool success = false;
    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
        String payload = http.getString();
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, payload);

        if (!error) {
            success = true;
            JsonArray arr = doc.as<JsonArray>();
            for (JsonObject obj : arr) {
                ScheduleEntry entry;
                entry.line = obj["linia"].as<String>();
                entry.direction = obj["kierunek"].as<String>();
                // Middleware sends "16:41:00", keep "16:41"
                String fullTime = obj["czas"].as<String>();
                entry.time = fullTime.substring(0, 5); 
                schedules.push_back(entry);
                if(schedules.size() >= 15) break; 
            }
        }
    }
    http.end();
    return success;
}

void removePastSchedules(std::vector<ScheduleEntry> &schedules) {
    int currentMins = getCurrentMinutes();
    if (currentMins == -1) return;

    // Use erase-remove idiom to filter vector in place
    schedules.erase(std::remove_if(schedules.begin(), schedules.end(), [currentMins](const ScheduleEntry &entry) {
        return minutesUntil(entry, currentMins) < 0;
    }), schedules.end());
}

std::vector<ScheduleEntry> convertScheduleTimesToMinutesLeft(const std::vector<ScheduleEntry> &schedules) {
    std::vector<ScheduleEntry> updatedSchedules;
    int currentMins = getCurrentMinutes();
    if (currentMins == -1) return schedules;

    for (const auto &entry : schedules) {
        ScheduleEntry newEntry = entry;
        int diff = minutesUntil(entry, currentMins);

        if (diff > 1) {
             newEntry.time = String(diff) + " min";
             updatedSchedules.push_back(newEntry);
        } else if (diff >= 0) {
             newEntry.time = (diff == 0) ? "Teraz" : "<1 min";
             updatedSchedules.push_back(newEntry);
        }
    }
    return updatedSchedules;
}