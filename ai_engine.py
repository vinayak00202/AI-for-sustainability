"""AI-style decision pipeline for smart window automation.

The engine is intentionally deterministic for classroom/internship demos:
it exposes the same stages used in an AI product workflow--validation,
preprocessing, pattern detection, classification, prediction, decision support,
explanation, and sustainability scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


VALIDATION_RANGES = {
    "indoor_temp_c": (-20.0, 60.0),
    "outdoor_temp_c": (-20.0, 60.0),
    "humidity_percent": (0.0, 100.0),
    "rain_probability_percent": (0.0, 100.0),
    "air_quality_index": (0.0, 500.0),
    "wind_speed_kmh": (0.0, 180.0),
}


@dataclass(frozen=True)
class EnvironmentalData:
    """Normalized inputs expected by the smart window engine."""

    indoor_temp_c: float
    outdoor_temp_c: float
    humidity_percent: float
    rain_probability_percent: float
    air_quality_index: float
    wind_speed_kmh: float
    time_of_day: str
    user_preference: str = "Auto"
    weather_condition: str = "Unknown"


@dataclass(frozen=True)
class DecisionResult:
    """Complete AI workflow output for dashboards and reports."""

    valid: bool
    errors: list[str]
    processed_data: dict[str, Any]
    patterns: list[str]
    classifications: list[str]
    prediction: str
    recommendation: str
    actuator_command: str
    window_position_percent: int
    door_lock_action: str
    door_reasons: list[str]
    confidence: int
    reasons: list[str]
    explanation: str
    ai_suggestion: str
    energy_saved_percent: int
    monthly_saving_inr: int
    carbon_reduction_kg: float
    sustainability_score: int
    sustainability_level: str
    sdg_alignment: str


def validate_environmental_data(data: EnvironmentalData) -> list[str]:
    """Return validation errors for invalid environmental readings."""
    errors: list[str] = []
    values = data.__dict__

    for field, (minimum, maximum) in VALIDATION_RANGES.items():
        value = values[field]
        if value < minimum or value > maximum:
            label = field.replace("_", " ").title()
            errors.append(f"{label} must be between {minimum:g} and {maximum:g}.")

    if not data.time_of_day.strip():
        errors.append("Time of day is required.")

    return errors


def preprocess_environmental_data(data: EnvironmentalData) -> dict[str, Any]:
    """Convert raw inputs into model-ready features."""
    time_value = _parse_time(data.time_of_day)
    hour = time_value.hour if time_value else 12
    temp_gap = data.outdoor_temp_c - data.indoor_temp_c

    return {
        "indoor_temp_c": round(data.indoor_temp_c, 1),
        "outdoor_temp_c": round(data.outdoor_temp_c, 1),
        "humidity_percent": round(data.humidity_percent, 1),
        "rain_probability_percent": round(data.rain_probability_percent, 1),
        "air_quality_index": round(data.air_quality_index, 0),
        "wind_speed_kmh": round(data.wind_speed_kmh, 1),
        "hour": hour,
        "time_period": _time_period(hour),
        "temperature_gap_c": round(temp_gap, 1),
        "user_preference": data.user_preference,
        "weather_condition": data.weather_condition,
    }


def detect_patterns(features: dict[str, Any]) -> list[str]:
    """Detect environmental patterns from preprocessed features."""
    patterns: list[str] = []

    outdoor_temp = features["outdoor_temp_c"]
    humidity = features["humidity_percent"]
    rain = features["rain_probability_percent"]
    aqi = features["air_quality_index"]
    wind = features["wind_speed_kmh"]
    temp_gap = features["temperature_gap_c"]
    condition = features["weather_condition"]

    if condition != "Unknown":
        patterns.append(f"{condition} weather")

    if outdoor_temp >= 38:
        patterns.append("Very hot outside")
    elif outdoor_temp >= 32:
        patterns.append("Hot outside")
    elif outdoor_temp <= 12:
        patterns.append("Cold outside")
    elif 20 <= outdoor_temp <= 30:
        patterns.append("Comfortable outdoor temperature")

    if temp_gap >= 5:
        patterns.append("Outdoor air is warmer than indoor air")
    elif temp_gap <= -4:
        patterns.append("Outdoor air can provide natural cooling")

    if humidity >= 75:
        patterns.append("High humidity")
    if rain >= 70:
        patterns.append("Rain coming")
    elif rain >= 40:
        patterns.append("Moderate rain risk")
    if aqi >= 151:
        patterns.append("Poor air quality")
    elif aqi >= 101:
        patterns.append("Moderate pollution")
    if wind >= 40:
        patterns.append("Strong wind")
    if features["time_period"] in {"Night", "Late night"}:
        patterns.append("Night safety mode")

    return patterns or ["Comfortable weather"]


def classify_environment(features: dict[str, Any], patterns: list[str]) -> list[str]:
    """Classify conditions into user-facing AI categories."""
    classes: list[str] = []

    if any("Comfortable" in pattern for pattern in patterns):
        classes.append("Comfortable")
    if features["outdoor_temp_c"] >= 32:
        classes.append("Hot")
    if features["outdoor_temp_c"] <= 12:
        classes.append("Cold")
    if features["rain_probability_percent"] >= 70:
        classes.append("Rain Expected")
    if features["air_quality_index"] >= 151:
        classes.append("High Pollution")
    elif features["air_quality_index"] >= 101:
        classes.append("Dust Risk")
    if features["wind_speed_kmh"] >= 40:
        classes.append("Wind Alert")
    if features["weather_condition"] in {"Sunny", "Cloudy", "Rainy"}:
        classes.append(features["weather_condition"])
    if features["temperature_gap_c"] >= 5 or features["outdoor_temp_c"] >= 34:
        classes.append("Energy Saving Mode")

    return classes or ["Comfortable"]


def predict_window_action(features: dict[str, Any], classes: list[str]) -> tuple[str, int, list[str]]:
    """Predict a window action using weighted decision support."""
    close_score = 0
    open_score = 0
    partial_score = 0
    reasons: list[str] = []

    if "Rain Expected" in classes:
        close_score += 45
        reasons.append("Rain probability is high, so closing prevents water entry.")
    elif features["rain_probability_percent"] >= 40:
        partial_score += 15
        reasons.append("Rain risk is moderate, so a partial opening is safer.")

    if "High Pollution" in classes:
        close_score += 35
        reasons.append("AQI is unhealthy, so closing reduces polluted air intake.")
    elif "Dust Risk" in classes:
        partial_score += 15
        reasons.append("AQI is elevated, so limited ventilation is preferred.")

    if "Wind Alert" in classes:
        close_score += 25
        reasons.append("Wind speed is high, so closing protects the window and room.")

    if features["outdoor_temp_c"] >= 34:
        close_score += 25
        reasons.append("Outdoor temperature is high, so closing reduces cooling loss.")
    elif features["temperature_gap_c"] <= -4 and features["air_quality_index"] < 101:
        open_score += 25
        reasons.append("Outdoor air is cooler and clean enough for natural cooling.")

    if features["humidity_percent"] >= 75:
        close_score += 15
        reasons.append("Humidity is high, so closing improves indoor comfort.")

    if "Night safety mode" in classes or features["time_period"] in {"Night", "Late night"}:
        partial_score += 12
        reasons.append("Night-time operation favors limited ventilation for safety.")

    preference = features["user_preference"]
    if preference == "Prefer fresh air":
        open_score += 12
        reasons.append("User preference gives extra weight to fresh-air ventilation.")
    elif preference == "Prefer energy saving":
        close_score += 12
        reasons.append("User preference gives extra weight to energy conservation.")
    elif preference == "Prefer safety":
        partial_score += 10
        close_score += 5
        reasons.append("User preference gives extra weight to safety.")

    if close_score == 0 and partial_score == 0:
        open_score += 35
        reasons.append("Weather, air quality, and wind are within comfort limits.")

    scores = {
        "Close": close_score,
        "Open": open_score,
        "Partial": partial_score,
    }
    action = max(scores, key=scores.get)
    sorted_scores = sorted(scores.values(), reverse=True)
    confidence = min(96, 58 + sorted_scores[0] - sorted_scores[1])

    if action == "Partial" and close_score >= partial_score + 15:
        action = "Close"
    if action == "Open" and partial_score >= open_score:
        action = "Partial"

    return action, max(50, confidence), reasons


def generate_explanation(action: str, reasons: list[str], classes: list[str], features: dict[str, Any]) -> str:
    """Generate a concise explainable-AI response similar to an LLM summary."""
    main_reason = reasons[0] if reasons else "The readings are balanced for comfort and efficiency."
    class_text = ", ".join(classes)
    return (
        f"The AI recommends {action.lower()} because {main_reason} "
        f"The detected class is {class_text}. This decision supports SDG 7 by balancing "
        f"natural ventilation with reduced heating or cooling loss. Current AQI is "
        f"{int(features['air_quality_index'])}, rain probability is "
        f"{features['rain_probability_percent']:.0f}%, and the outdoor temperature is "
        f"{features['outdoor_temp_c']:.1f} C."
    )


def calculate_energy_savings(action: str, classes: list[str], features: dict[str, Any]) -> tuple[int, int, float]:
    """Estimate energy, cost, and carbon benefits from the decision."""
    saved = 6

    if action == "Close":
        saved += 8
    elif action == "Partial":
        saved += 5
    else:
        saved += 3

    if "Energy Saving Mode" in classes:
        saved += 7
    if features["temperature_gap_c"] <= -4 and action in {"Open", "Partial"}:
        saved += 5
    if features["outdoor_temp_c"] >= 34 and action == "Close":
        saved += 6
    if features["air_quality_index"] >= 151 and action == "Close":
        saved += 3

    saved = min(32, saved)
    monthly_saving = int(round(saved * 15))
    carbon_reduction = round(saved * 0.18, 2)
    return saved, monthly_saving, carbon_reduction


def generate_sustainability_score(
    action: str,
    confidence: int,
    energy_saved_percent: int,
    classes: list[str],
) -> tuple[int, str]:
    """Create a green score from confidence, efficiency, and risk handling."""
    score = 50 + round(energy_saved_percent * 1.2) + round((confidence - 50) * 0.35)

    if action == "Close" and {"Rain Expected", "High Pollution"}.intersection(classes):
        score += 8
    if action in {"Open", "Partial"} and "Comfortable" in classes:
        score += 6

    score = max(0, min(100, score))
    if score >= 90:
        level = "Excellent"
    elif score >= 70:
        level = "Good"
    elif score >= 50:
        level = "Average"
    else:
        level = "Poor"
    return score, level


def run_ai_workflow(data: EnvironmentalData) -> DecisionResult:
    """Run the complete AI workflow and return dashboard-ready output."""
    errors = validate_environmental_data(data)
    if errors:
        return DecisionResult(
            valid=False,
            errors=errors,
            processed_data={},
            patterns=[],
            classifications=[],
            prediction="No Change",
            recommendation="No Change",
            actuator_command="HOLD_POSITION",
            window_position_percent=0,
            door_lock_action="No Change",
            door_reasons=[],
            confidence=0,
            reasons=[],
            explanation="Correct the highlighted input values before running the AI workflow.",
            ai_suggestion="Correct the invalid readings before the AI agent can provide a weather suggestion.",
            energy_saved_percent=0,
            monthly_saving_inr=0,
            carbon_reduction_kg=0.0,
            sustainability_score=0,
            sustainability_level="Not available",
            sdg_alignment="SDG 7 - Affordable and Clean Energy",
        )

    features = preprocess_environmental_data(data)
    patterns = detect_patterns(features)
    classes = classify_environment(features, patterns)
    action, confidence, reasons = predict_window_action(features, classes)
    actuator_command, window_position_percent = build_window_actuator_command(action, features)
    door_action, door_reasons = predict_door_lock_action(features, classes)
    explanation = generate_explanation(action, reasons, classes, features)
    ai_suggestion = generate_weather_suggestion(action, actuator_command, features, reasons)
    energy_saved, monthly_saving, carbon_reduction = calculate_energy_savings(action, classes, features)
    green_score, green_level = generate_sustainability_score(action, confidence, energy_saved, classes)

    return DecisionResult(
        valid=True,
        errors=[],
        processed_data=features,
        patterns=patterns,
        classifications=classes,
        prediction=action,
        recommendation=action,
        actuator_command=actuator_command,
        window_position_percent=window_position_percent,
        door_lock_action=door_action,
        door_reasons=door_reasons,
        confidence=confidence,
        reasons=reasons,
        explanation=explanation,
        ai_suggestion=ai_suggestion,
        energy_saved_percent=energy_saved,
        monthly_saving_inr=monthly_saving,
        carbon_reduction_kg=carbon_reduction,
        sustainability_score=green_score,
        sustainability_level=green_level,
        sdg_alignment="SDG 7 - Affordable and Clean Energy",
    )


def generate_weather_suggestion(
    action: str,
    actuator_command: str,
    features: dict[str, Any],
    reasons: list[str],
) -> str:
    """Create a clear local AI-style suggestion from weather readings."""
    condition = features["weather_condition"]
    temp = features["outdoor_temp_c"]
    rain = features["rain_probability_percent"]
    humidity = features["humidity_percent"]
    aqi = features["air_quality_index"]
    wind = features["wind_speed_kmh"]
    main_reason = reasons[0] if reasons else "conditions are balanced"

    if action == "Open":
        comfort = "Use natural ventilation while the outdoor air is favorable."
    elif action == "Partial":
        comfort = "Keep the window partially open to balance ventilation and protection."
    else:
        comfort = "Keep the window closed to protect comfort, safety, and energy efficiency."

    return (
        f"Weather is {condition.lower()} with {temp:.1f} C outside, {humidity:.0f}% humidity, "
        f"{rain:.0f}% rain probability, AQI {int(aqi)}, and {wind:.1f} km/h wind. "
        f"The AI agent selected {actuator_command} because {main_reason} {comfort}"
    )


def build_window_actuator_command(action: str, features: dict[str, Any]) -> tuple[str, int]:
    """Convert AI recommendation into a simple actuator command."""
    if action == "Open":
        return "OPEN_WINDOW", 100
    if action == "Partial":
        if features["rain_probability_percent"] >= 40 or features["wind_speed_kmh"] >= 25:
            return "OPEN_WINDOW_PARTIAL", 35
        return "OPEN_WINDOW_PARTIAL", 50
    if action == "Close":
        return "CLOSE_WINDOW", 0
    return "HOLD_POSITION", 0


def predict_door_lock_action(features: dict[str, Any], classes: list[str]) -> tuple[str, list[str]]:
    """Recommend door lock state from real weather and safety conditions."""
    lock_score = 0
    unlock_score = 0
    reasons: list[str] = []

    if "Rain Expected" in classes:
        lock_score += 30
        reasons.append("Rain risk is high, so the door should stay locked to protect the home.")
    if "Wind Alert" in classes:
        lock_score += 25
        reasons.append("Strong wind is detected, so locking improves safety.")
    if "High Pollution" in classes:
        lock_score += 15
        reasons.append("Poor AQI favors keeping outside access sealed.")
    if features["time_period"] in {"Night", "Late night"}:
        lock_score += 25
        reasons.append("Night-time operation favors locking for home security.")
    if features["rain_probability_percent"] < 30 and features["wind_speed_kmh"] < 20 and features["air_quality_index"] < 101:
        unlock_score += 20
        reasons.append("Weather is calm and clean enough to allow normal door access.")
    if features["user_preference"] == "Prefer safety":
        lock_score += 15
        reasons.append("User preference gives extra weight to door safety.")

    if lock_score >= unlock_score:
        return "Lock", reasons or ["Safety-first mode keeps the door locked."]
    return "Unlock", reasons


def recommend_window_state(
    temperature_c: float,
    humidity_percent: float,
    rain_expected: bool,
    air_quality_index: float,
) -> tuple[str, str]:
    """Backward-compatible helper for older callers."""
    data = EnvironmentalData(
        indoor_temp_c=25,
        outdoor_temp_c=temperature_c,
        humidity_percent=humidity_percent,
        rain_probability_percent=90 if rain_expected else 10,
        air_quality_index=air_quality_index,
        wind_speed_kmh=8,
        time_of_day="12:00",
    )
    result = run_ai_workflow(data)
    return result.recommendation.lower(), result.explanation


def _parse_time(value: str) -> datetime | None:
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _time_period(hour: int) -> str:
    if 5 <= hour < 12:
        return "Morning"
    if 12 <= hour < 17:
        return "Afternoon"
    if 17 <= hour < 21:
        return "Evening"
    if 21 <= hour <= 23:
        return "Night"
    return "Late night"
