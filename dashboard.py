"""Streamlit dashboard for the AI Smart Window System."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from ai_engine import EnvironmentalData, run_ai_workflow
from prompt import build_weather_suggestion_prompt
from utils import (
    build_auto_refresh_html,
    build_daily_report_text,
    build_location_permission_html,
    build_simple_pdf,
    fetch_groq_weather_suggestion,
    query_param_float,
)
from weather import get_current_weather, get_weather_for_location, infer_condition_from_readings, load_sample_dataset


BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"
WINDOW_PATH = BASE_DIR / "assets" / "window.png"
PREFERENCE_OPTIONS = ["Auto", "Prefer fresh air", "Prefer energy saving", "Prefer safety"]
SOURCE_OPTIONS = ["Device Location Weather", "Manual Input", "Sample Dataset", "Weather Snapshot"]


def run_dashboard() -> None:
    """Render the smart window dashboard."""
    st.set_page_config(page_title="AI Smart Window System", page_icon="🏠", layout="wide")
    _apply_theme()
    _init_state()

    if st.query_params.get("open_app") == "1":
        st.session_state["app_opened"] = True

    if not st.session_state["app_opened"]:
        _render_landing()
        return

    _render_header()
    data, settings = _render_input_tabs()

    if settings["auto_run"] and settings["source"] == "Device Location Weather":
        components.html(build_auto_refresh_html(settings["refresh_interval"]), height=0)

    result = run_ai_workflow(data)
    suggestion, suggestion_source = _build_weather_suggestion(result, settings["use_llm_suggestions"])
    _record_agent_result(result)

    _render_output_tabs(data, result, suggestion, suggestion_source)


def _init_state() -> None:
    st.session_state.setdefault("app_opened", False)
    st.session_state.setdefault("agent_log", [])


def _render_landing() -> None:
    logo = _image_data_uri(LOGO_PATH)
    window = _image_data_uri(WINDOW_PATH)
    components.html(
        f"""
        <style>
            body {{ margin: 0; font-family: Arial, sans-serif; }}
            .landing {{
                min-height: 720px;
                display: grid;
                grid-template-columns: 0.9fr 1.1fr;
                gap: 28px;
                align-items: center;
                padding: 42px 52px;
                background: linear-gradient(120deg, #ffffff 0%, #f4fbff 58%, #eef9f0 100%);
                color: #08264a;
            }}
            .logo {{
                width: 270px;
                display: block;
                margin-bottom: 42px;
                cursor: pointer;
            }}
            h1 {{
                font-size: 58px;
                line-height: 1.08;
                margin: 0 0 20px;
                letter-spacing: 0;
            }}
            .green {{ color: #1f9a3d; }}
            p {{
                font-size: 19px;
                line-height: 1.55;
                max-width: 560px;
                margin: 0 0 28px;
                color: #28476a;
            }}
            .cta {{
                display: inline-block;
                background: #082e5f;
                color: white;
                padding: 15px 24px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 700;
            }}
            .hero {{
                position: relative;
                min-height: 540px;
                background: rgba(255,255,255,0.78);
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 22px 55px rgba(7, 36, 72, 0.16);
            }}
            .hero img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }}
            .status {{
                position: absolute;
                right: 34px;
                top: 52px;
                width: 230px;
                background: white;
                border-radius: 8px;
                padding: 24px;
                box-shadow: 0 18px 40px rgba(10, 45, 83, 0.18);
                border-left: 5px solid #28a745;
            }}
            .status small {{ color: #395676; }}
            .status strong {{
                display: block;
                margin-top: 10px;
                color: #1f9a3d;
                font-size: 26px;
            }}
            @media (max-width: 900px) {{
                .landing {{ grid-template-columns: 1fr; padding: 28px; }}
                h1 {{ font-size: 40px; }}
                .hero {{ min-height: 360px; }}
            }}
        </style>
        <section class="landing">
            <div>
                <a href="?open_app=1"><img class="logo" src="{logo}" alt="AI Smart Window Control System"></a>
                <h1>AI-Powered<br><span class="green">Smart Window Control</span><br>for Homes</h1>
                <p>Real-time weather readings drive automatic open and close decisions for comfort, safety, and energy savings.</p>
                <a class="cta" href="?open_app=1">Open Dashboard</a>
            </div>
            <div class="hero">
                <img src="{window}" alt="Smart window">
                <div class="status">
                    <small>AI Recommendation</small>
                    <strong>AUTO READY</strong>
                    <p style="font-size:14px;margin-top:14px;">Click the logo or button to start live control.</p>
                </div>
            </div>
        </section>
        """,
        height=760,
    )
    if st.button("Open Dashboard", type="primary"):
        st.session_state["app_opened"] = True
        st.rerun()


def _render_header() -> None:
    logo_col, nav_col, button_col = st.columns([1.2, 3.3, 0.9], vertical_alignment="center")
    with logo_col:
        st.image(str(LOGO_PATH), width=245)
    with nav_col:
        st.markdown(
            "<div class='top-nav'><span>Home</span><span>Dashboard</span><span>Analytics</span>"
            "<span>Recommendations</span><span>Reports</span><span>Settings</span></div>",
            unsafe_allow_html=True,
        )
    with button_col:
        if st.button("Restart", use_container_width=True):
            st.session_state["app_opened"] = False
            st.query_params.clear()
            st.rerun()


def _render_input_tabs() -> tuple[EnvironmentalData, dict]:
    tab_home, tab_inputs, tab_settings = st.tabs(["Home", "Data Input", "Settings"])
    with tab_settings:
        source = st.selectbox("Weather Source", SOURCE_OPTIONS)
        auto_run = st.toggle("AI agent automatic operation", value=True)
        use_llm_suggestions = st.toggle("Groq AI weather suggestion", value=True)
        refresh_interval = st.slider("Live refresh seconds", 15, 300, 60, 15)
    with tab_inputs:
        data = _collect_environmental_data(source)
    with tab_home:
        st.markdown(
            "<div class='hero-strip'><div><h1>Smart weather-based window control</h1>"
            "<p>The AI agent reads weather, predicts the safest window state, and generates the actuator command.</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
    return data, {
        "source": source,
        "auto_run": auto_run,
        "use_llm_suggestions": use_llm_suggestions,
        "refresh_interval": refresh_interval,
    }


def _collect_environmental_data(source: str) -> EnvironmentalData:
    if source == "Sample Dataset":
        return _sample_dataset_inputs()
    if source == "Device Location Weather":
        return _device_location_inputs()
    if source == "Weather Snapshot":
        snapshot = get_current_weather()
        return EnvironmentalData(
            indoor_temp_c=st.number_input("Indoor Temperature (C)", -20.0, 60.0, 25.0, 0.5),
            outdoor_temp_c=float(snapshot["outdoor_temp_c"]),
            humidity_percent=float(snapshot["humidity_percent"]),
            rain_probability_percent=float(snapshot["rain_probability_percent"]),
            air_quality_index=float(snapshot["air_quality_index"]),
            wind_speed_kmh=float(snapshot["wind_speed_kmh"]),
            time_of_day=str(snapshot["time_of_day"]),
            user_preference=st.selectbox("User Preference", PREFERENCE_OPTIONS),
            weather_condition=str(snapshot.get("weather_condition", "Cloudy")),
        )
    return _manual_inputs()


def _device_location_inputs() -> EnvironmentalData:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        components.html(build_location_permission_html(), height=54)
        params = dict(st.query_params)
        latitude = query_param_float(params, "lat")
        longitude = query_param_float(params, "lon")
        latitude = st.number_input("Latitude", -90.0, 90.0, value=float(latitude or 17.3850), step=0.0001, format="%.6f")
        longitude = st.number_input("Longitude", -180.0, 180.0, value=float(longitude or 78.4867), step=0.0001, format="%.6f")
    with col2:
        provider = st.selectbox("Weather Provider", ["Open-Meteo", "AccuWeather"])
        indoor_temp = st.number_input("Indoor Temperature (C)", -20.0, 60.0, 25.0, 0.5)
    with col3:
        preference = st.selectbox("User Preference", PREFERENCE_OPTIONS)

    try:
        snapshot = get_weather_for_location(float(latitude), float(longitude), provider)
        st.success(f"Live weather loaded from {snapshot.get('provider', provider)}.")
    except Exception as exc:
        st.warning(f"Live weather unavailable. Using fallback snapshot. Details: {exc}")
        snapshot = get_current_weather()

    return EnvironmentalData(
        indoor_temp_c=float(indoor_temp),
        outdoor_temp_c=float(snapshot["outdoor_temp_c"]),
        humidity_percent=float(snapshot["humidity_percent"]),
        rain_probability_percent=float(snapshot["rain_probability_percent"]),
        air_quality_index=float(snapshot["air_quality_index"]),
        wind_speed_kmh=float(snapshot["wind_speed_kmh"]),
        time_of_day=str(snapshot["time_of_day"]),
        user_preference=preference,
        weather_condition=str(snapshot.get("weather_condition", "Cloudy")),
    )


def _manual_inputs() -> EnvironmentalData:
    row1 = st.columns(4)
    indoor_temp = row1[0].number_input("Indoor Temperature (C)", -20.0, 60.0, 25.0, 0.5)
    outdoor_temp = row1[1].number_input("Outdoor Temperature (C)", -20.0, 60.0, 34.0, 0.5)
    humidity = row1[2].slider("Humidity (%)", 0, 100, 62)
    rain = row1[3].slider("Rain Probability (%)", 0, 100, 20)
    row2 = st.columns(4)
    aqi = row2[0].slider("Air Quality Index", 0, 500, 80)
    wind = row2[1].slider("Wind Speed (km/h)", 0, 180, 12)
    weather_condition = row2[2].selectbox("Weather Condition", ["Sunny", "Cloudy", "Rainy"])
    time_value = row2[3].time_input("Time of Day", value=datetime.now().time().replace(second=0, microsecond=0))
    preference = st.selectbox("User Preference", PREFERENCE_OPTIONS)

    return EnvironmentalData(
        indoor_temp_c=float(indoor_temp),
        outdoor_temp_c=float(outdoor_temp),
        humidity_percent=float(humidity),
        rain_probability_percent=float(rain),
        air_quality_index=float(aqi),
        wind_speed_kmh=float(wind),
        time_of_day=time_value.strftime("%H:%M"),
        user_preference=preference,
        weather_condition=weather_condition,
    )


def _sample_dataset_inputs() -> EnvironmentalData:
    dataset = load_sample_dataset()
    labels = [f"{row.timestamp} | {row.weather_condition} | {row.outdoor_temp_c} C | AQI {row.air_quality_index}" for row in dataset.itertuples()]
    selected_label = st.selectbox("Scenario", labels)
    row = dataset.iloc[labels.index(selected_label)]
    weather_condition = str(
        row.get(
            "weather_condition",
            infer_condition_from_readings(
                float(row["rain_probability_percent"]),
                float(row["humidity_percent"]),
                float(row["wind_speed_kmh"]),
            ),
        )
    )
    return EnvironmentalData(
        indoor_temp_c=float(row["indoor_temp_c"]),
        outdoor_temp_c=float(row["outdoor_temp_c"]),
        humidity_percent=float(row["humidity_percent"]),
        rain_probability_percent=float(row["rain_probability_percent"]),
        air_quality_index=float(row["air_quality_index"]),
        wind_speed_kmh=float(row["wind_speed_kmh"]),
        time_of_day=str(row["time_of_day"]),
        user_preference=str(row.get("user_preference", "Auto")),
        weather_condition=weather_condition,
    )


def _render_output_tabs(data: EnvironmentalData, result, suggestion: str, suggestion_source: str) -> None:
    overview, recommendation, analytics, reports = st.tabs(["Dashboard", "AI Recommendation", "Analytics", "Reports"])
    with overview:
        _render_overview(data, result)
    with recommendation:
        _render_recommendation(data, result, suggestion, suggestion_source)
    with analytics:
        _render_analytics(data, result)
    with reports:
        _render_reports(data, result)


def _render_overview(data: EnvironmentalData, result) -> None:
    st.markdown("<div class='section-title'>Live Environmental Overview</div>", unsafe_allow_html=True)
    metrics = [
        ("Indoor Temp", f"{data.indoor_temp_c:.1f} C", "Comfort"),
        ("Outdoor Temp", f"{data.outdoor_temp_c:.1f} C", data.weather_condition),
        ("Humidity", f"{data.humidity_percent:.0f}%", "Moisture"),
        ("AQI", f"{data.air_quality_index:.0f}", "Air quality"),
        ("Rain", f"{data.rain_probability_percent:.0f}%", "Probability"),
        ("Wind", f"{data.wind_speed_kmh:.1f} km/h", "Speed"),
    ]
    cols = st.columns(6)
    for col, (label, value, hint) in zip(cols, metrics):
        col.markdown(f"<div class='metric-card'><small>{label}</small><strong>{value}</strong><span>{hint}</span></div>", unsafe_allow_html=True)

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown(
            f"""
            <div class='recommend-card'>
                <h3>AI Recommendation</h3>
                <h2>{result.recommendation.upper()}</h2>
                <p>{result.ai_suggestion}</p>
                <ul>
                    {''.join(f'<li>{reason}</li>' for reason in result.reasons[:4])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        card_cols = st.columns(2)
        card_cols[0].metric("Command", result.actuator_command)
        card_cols[1].metric("Position", f"{result.window_position_percent}%")
        card_cols[0].metric("Confidence", f"{result.confidence}%")
        card_cols[1].metric("Door", result.door_lock_action)
        card_cols[0].metric("Energy Saved", f"{result.energy_saved_percent}%")
        card_cols[1].metric("Monthly Saving", f"INR {result.monthly_saving_inr}")


def _render_recommendation(data: EnvironmentalData, result, suggestion: str, suggestion_source: str) -> None:
    cols = st.columns(4)
    cols[0].metric("Window Status", result.recommendation.upper())
    cols[1].metric("Actuator Command", result.actuator_command)
    cols[2].metric("Window Position", f"{result.window_position_percent}%")
    cols[3].metric("Weather", data.weather_condition)
    st.info(f"{suggestion_source}: {suggestion}")

    reason_cols = st.columns(2)
    with reason_cols[0]:
        st.write("Window Decision Reasons")
        for reason in result.reasons:
            st.write(f"- {reason}")
    with reason_cols[1]:
        st.write("Current Readings")
        st.dataframe(_readings_table(data, result), hide_index=True, use_container_width=True)


def _render_analytics(data: EnvironmentalData, result) -> None:
    chart_data = pd.DataFrame(
        {
            "Metric": ["Indoor Temp", "Outdoor Temp", "Humidity", "Rain", "AQI/5", "Wind"],
            "Value": [
                data.indoor_temp_c,
                data.outdoor_temp_c,
                data.humidity_percent,
                data.rain_probability_percent,
                data.air_quality_index / 5,
                data.wind_speed_kmh,
            ],
        }
    ).set_index("Metric")
    st.bar_chart(chart_data)
    if st.session_state["agent_log"]:
        st.write("Agent Activity")
        st.dataframe(pd.DataFrame(st.session_state["agent_log"][-8:]), hide_index=True, use_container_width=True)


def _render_reports(data: EnvironmentalData, result) -> None:
    report_text = build_daily_report_text(data, result)
    pdf_bytes = build_simple_pdf("AI Smart Window Report", report_text.splitlines())
    col1, col2 = st.columns(2)
    col1.download_button("Download Report", data=report_text, file_name="smart_window_report.txt", mime="text/plain", use_container_width=True)
    col2.download_button("Export PDF", data=pdf_bytes, file_name="smart_window_report.pdf", mime="application/pdf", use_container_width=True)
    with st.expander("Report Preview"):
        st.text(report_text)


def _build_weather_suggestion(result, use_llm_suggestions: bool) -> tuple[str, str]:
    if not result.valid or not use_llm_suggestions:
        return result.ai_suggestion, "Local AI"
    prompt = build_weather_suggestion_prompt(
        result.recommendation,
        result.actuator_command,
        result.window_position_percent,
        result.processed_data,
        result.reasons,
    )
    return fetch_groq_weather_suggestion(prompt, result.ai_suggestion)


def _record_agent_result(result) -> None:
    if not result.valid:
        return
    st.session_state["agent_log"].append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "window": result.recommendation,
            "command": result.actuator_command,
            "position": f"{result.window_position_percent}%",
            "confidence": result.confidence,
        }
    )


def _readings_table(data: EnvironmentalData, result) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Indoor Temp", f"{data.indoor_temp_c:.1f} C"],
            ["Outdoor Temp", f"{data.outdoor_temp_c:.1f} C"],
            ["Weather", data.weather_condition],
            ["Humidity", f"{data.humidity_percent:.0f}%"],
            ["Rain", f"{data.rain_probability_percent:.0f}%"],
            ["AQI", f"{data.air_quality_index:.0f}"],
            ["Wind", f"{data.wind_speed_kmh:.1f} km/h"],
            ["Command", result.actuator_command],
            ["Target Position", f"{result.window_position_percent}%"],
        ],
        columns=["Metric", "Value"],
    )


def _image_data_uri(path: Path) -> str:
    mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f7fbff; color: #08264a; }
        header { visibility: hidden; height: 0; }
        .block-container { padding-top: 1.2rem; max-width: 1480px; }
        .top-nav {
            display: flex;
            justify-content: center;
            gap: 32px;
            font-weight: 700;
            color: #08264a;
        }
        .top-nav span:first-child {
            background: #082e5f;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
        }
        .hero-strip {
            min-height: 180px;
            border-radius: 8px;
            background: linear-gradient(90deg, rgba(255,255,255,.94), rgba(255,255,255,.68)), url('assets/window.png');
            background-size: cover;
            background-position: center;
            padding: 34px 40px;
            box-shadow: 0 14px 38px rgba(7, 36, 72, 0.10);
        }
        .hero-strip h1 { margin: 0 0 10px; font-size: 42px; color: #08264a; letter-spacing: 0; }
        .hero-strip p { margin: 0; max-width: 650px; color: #28476a; font-size: 18px; }
        .section-title { font-weight: 800; font-size: 20px; margin: 12px 0 14px; color: #08264a; }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px 18px;
            box-shadow: 0 10px 28px rgba(7, 36, 72, 0.08);
            border: 1px solid #edf2f7;
            min-height: 118px;
        }
        .metric-card small { color: #496582; font-weight: 700; }
        .metric-card strong { display: block; font-size: 26px; margin-top: 10px; color: #08264a; }
        .metric-card span { color: #219642; font-size: 13px; font-weight: 700; }
        .recommend-card {
            margin-top: 18px;
            min-height: 282px;
            background: #082e5f;
            color: white;
            border-radius: 8px;
            padding: 28px;
            box-shadow: 0 16px 36px rgba(7, 36, 72, 0.16);
        }
        .recommend-card h3 { margin: 0 0 14px; color: white; }
        .recommend-card h2 { margin: 0 0 14px; color: #42e66a; font-size: 32px; letter-spacing: 0; }
        .recommend-card p, .recommend-card li { color: white; font-size: 15px; }
        div[data-baseweb="tab-list"] { gap: 10px; }
        button[data-baseweb="tab"] {
            background: white;
            border-radius: 8px;
            padding: 10px 18px;
            border: 1px solid #e5edf5;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: #082e5f;
            color: white;
        }
        div[data-testid="stMetric"] {
            background: white;
            border-radius: 8px;
            padding: 18px;
            border: 1px solid #edf2f7;
            box-shadow: 0 10px 28px rgba(7, 36, 72, 0.07);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
