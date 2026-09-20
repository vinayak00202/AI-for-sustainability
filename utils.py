"""Shared utility functions for the smart window system."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
import os
from typing import Iterable
from urllib.parse import urlencode

import requests

from ai_engine import DecisionResult, EnvironmentalData


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32


def normalize_bool(value: object) -> bool:
    """Convert common CSV/UI boolean values into a Python bool."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def build_daily_report_text(data: EnvironmentalData, result: DecisionResult) -> str:
    """Create a readable daily report body."""
    lines = [
        "AI-Based Smart Window Control System Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Environmental Data",
        f"Indoor Temperature: {data.indoor_temp_c:.1f} C",
        f"Outdoor Temperature: {data.outdoor_temp_c:.1f} C",
        f"Humidity: {data.humidity_percent:.0f}%",
        f"Rain Probability: {data.rain_probability_percent:.0f}%",
        f"AQI: {data.air_quality_index:.0f}",
        f"Wind Speed: {data.wind_speed_kmh:.1f} km/h",
        f"Weather Condition: {data.weather_condition}",
        f"Time of Day: {data.time_of_day}",
        f"User Preference: {data.user_preference}",
        "",
        "AI Workflow Output",
        f"Patterns: {', '.join(result.patterns)}",
        f"Classification: {', '.join(result.classifications)}",
        f"Prediction: {result.prediction}",
        f"Recommendation: {result.recommendation}",
        f"Actuator Command: {result.actuator_command}",
        f"Target Window Position: {result.window_position_percent}%",
        f"Door Action: {result.door_lock_action}",
        f"Door Reasons: {', '.join(result.door_reasons)}",
        f"Confidence: {result.confidence}%",
        "",
        "Explainable AI",
        result.explanation,
        "",
        "AI Weather Suggestion",
        result.ai_suggestion,
        "",
        "Sustainability",
        f"Estimated Energy Saved: {result.energy_saved_percent}%",
        f"Monthly Saving: INR {result.monthly_saving_inr}",
        f"Carbon Reduction: {result.carbon_reduction_kg:.2f} kg CO2/month",
        f"Green Score: {result.sustainability_score}/100 ({result.sustainability_level})",
        f"SDG Alignment: {result.sdg_alignment}",
    ]
    return "\n".join(lines)


def fetch_groq_weather_suggestion(prompt: str, fallback: str) -> tuple[str, str]:
    """Call Groq for a concise weather suggestion, falling back locally."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return fallback, "Local AI fallback"

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                "messages": [
                    {
                        "role": "system",
                        "content": "You provide clear weather-based smart home suggestions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 180,
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content or fallback, "Groq LLM"
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        return f"{fallback}\n\nLLM service unavailable: {exc}", "Local AI fallback"


def build_location_permission_html(button_label: str = "Use Device Location") -> str:
    """Return HTML/JS that asks the browser for location and writes it to query params."""
    params = urlencode({"location_status": "requesting"})
    return f"""
    <button onclick="getLocation()" style="
        width: 100%;
        padding: 0.6rem 0.75rem;
        border: 0;
        border-radius: 0.4rem;
        background: #ff4b4b;
        color: white;
        font-weight: 600;
        cursor: pointer;">
        {button_label}
    </button>
    <script>
    function getLocation() {{
        if (!navigator.geolocation) {{
            window.parent.location.search = "?location_status=unsupported";
            return;
        }}
        navigator.geolocation.getCurrentPosition(
            function(position) {{
                const params = new URLSearchParams(window.parent.location.search);
                params.set("lat", position.coords.latitude.toFixed(6));
                params.set("lon", position.coords.longitude.toFixed(6));
                params.set("location_status", "granted");
                window.parent.location.search = params.toString();
            }},
            function(error) {{
                window.parent.location.search = "?location_status=denied";
            }},
            {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }}
        );
    }}
    const params = new URLSearchParams(window.parent.location.search);
    if (!params.get("location_status")) {{
        params.set("location_status", "{params.split("=")[1]}");
    }}
    </script>
    """


def build_auto_refresh_html(interval_seconds: int) -> str:
    """Return HTML/JS that refreshes the Streamlit page on a fixed interval."""
    interval_ms = max(10, interval_seconds) * 1000
    return f"""
    <script>
    const refreshMs = {interval_ms};
    window.setTimeout(function() {{
        const params = new URLSearchParams(window.parent.location.search);
        params.set("agent_tick", Date.now().toString());
        window.parent.location.search = params.toString();
    }}, refreshMs);
    </script>
    """


def query_param_float(params: dict, key: str) -> float | None:
    """Read a float from Streamlit query params."""
    value = params.get(key)
    if isinstance(value, list):
        value = value[0] if value else None
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_simple_pdf(title: str, lines: Iterable[str]) -> bytes:
    """Build a small text-only PDF without external dependencies."""
    content_lines = ["BT", "/F1 12 Tf", "50 790 Td", "14 TL"]
    content_lines.append(f"({ _pdf_escape(title) }) Tj")
    content_lines.append("T*")
    content_lines.append("T*")
    for line in lines:
        wrapped = _wrap_text(line, 86) or [""]
        for chunk in wrapped:
            content_lines.append(f"({ _pdf_escape(chunk) }) Tj")
            content_lines.append("T*")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{index} 0 obj\n".encode("ascii"))
        buffer.write(obj)
        buffer.write(b"\nendobj\n")
    xref_offset = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    buffer.write(
        (
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return buffer.getvalue()


def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
