"""Prompt templates for explainable AI smart-window decisions."""


SYSTEM_PROMPT = """
You are an explainable AI assistant for a sustainable smart window controller.
Explain recommendations in short, clear language using environmental readings,
energy-saving impact, comfort, safety, and SDG 7 alignment.
"""


GRANITE_EXPLANATION_PROMPT = """
Explain why the smart window should {action}.

Environmental context:
- Indoor temperature: {indoor_temp_c} C
- Outdoor temperature: {outdoor_temp_c} C
- Humidity: {humidity_percent}%
- Rain probability: {rain_probability_percent}%
- AQI: {air_quality_index}
- Wind speed: {wind_speed_kmh} km/h
- Detected patterns: {patterns}
- Classification: {classifications}
- Estimated energy saved: {energy_saved_percent}%

Keep the response concise and include responsible-AI reasoning.
"""


def build_granite_prompt(action: str, features: dict, patterns: list[str], classifications: list[str], energy_saved_percent: int) -> str:
    """Build an IBM Granite-ready explanation prompt."""
    return GRANITE_EXPLANATION_PROMPT.format(
        action=action.lower(),
        patterns=", ".join(patterns),
        classifications=", ".join(classifications),
        energy_saved_percent=energy_saved_percent,
        **features,
    )


def build_weather_suggestion_prompt(
    action: str,
    actuator_command: str,
    window_position_percent: int,
    features: dict,
    reasons: list[str],
) -> str:
    """Build a prompt for real-time weather suggestions."""
    return f"""
You are the AI agent for an automatic smart window control system.
Give a clear, practical suggestion for the home owner based on the weather readings.

Current condition: {features.get("weather_condition", "Unknown")}
Indoor temperature: {features.get("indoor_temp_c")} C
Outdoor temperature: {features.get("outdoor_temp_c")} C
Humidity: {features.get("humidity_percent")}%
Rain probability: {features.get("rain_probability_percent")}%
AQI: {features.get("air_quality_index")}
Wind speed: {features.get("wind_speed_kmh")} km/h
Window action: {action}
Actuator command: {actuator_command}
Target window position: {window_position_percent}%
Reasoning signals: {", ".join(reasons)}

Response format:
1. Weather summary in one sentence.
2. Window operation suggestion in one sentence.
3. Comfort or safety suggestion in one sentence.
Keep it short and specific.
"""
