# 🌱 AI-Based Smart Window Control System

> **AI-powered decision support for energy-efficient and sustainable homes**

An interactive **Streamlit-based smart home application** that analyzes environmental and weather conditions to recommend the optimal window position—**Open, Close, Partial, or No Change**. The system combines environmental data processing, AI-style pattern detection, classification, prediction, explainable decision support, agentic automation, sustainability scoring, and report generation.

The project is designed as a practical demonstration of how **Artificial Intelligence can support household energy efficiency, indoor comfort, and sustainable living**.

---

## 🎯 Project Objectives

- Reduce unnecessary household energy consumption.
- Support efficient use of natural ventilation.
- Improve indoor comfort using environmental conditions.
- Consider weather, AQI, humidity, wind, rainfall, and temperature.
- Provide explainable AI-based recommendations.
- Estimate energy savings and sustainability impact.
- Demonstrate a pathway toward future IoT-enabled smart-home automation.

---

## 🌍 SDG Alignment

### Primary SDG
**SDG 7 – Affordable and Clean Energy** ⚡  
Supports energy efficiency and reduced electricity consumption.

### Secondary SDGs
- **SDG 11 – Sustainable Cities and Communities** 🏙️
- **SDG 13 – Climate Action** 🌎

---

## ✨ Key Features

### 🌦️ Environmental & Weather Inputs
- Manual input
- Sample dataset
- Offline weather snapshots
- Device-location weather using browser geolocation
- Real-time weather through **Open-Meteo**
- Optional **AccuWeather** integration
- Weather states: Sunny, Cloudy, Rainy

### 🤖 AI & Decision Support
- Environmental input validation
- Data preprocessing
- Temperature-gap analysis
- Pattern detection for:
  - Heat
  - Cold
  - Humidity
  - Rain
  - Pollution
  - Wind
  - Comfort
- Environmental-state classification
- Window action prediction
- Confidence and explainable reasoning
- IBM Granite/LLM-ready prompt generation

### 🪟 Smart Window Actions
The system can recommend:

`Open` → `Close` → `Partial` → `No Change`

It can also generate actuator commands:

`OPEN_WINDOW` → `OPEN_WINDOW_PARTIAL` → `CLOSE_WINDOW` → `HOLD_POSITION`

### 🧠 Agentic Automation
The application can continuously refresh live weather data, recalculate environmental conditions, update recommendations, and refresh the dashboard at a selected interval.

### 🌱 Sustainability Analytics
- Energy-saving estimate
- Monthly electricity-cost saving estimate
- Carbon-reduction estimate
- Sustainability / green score

### 📊 Dashboard & Reports
- Environmental metrics
- Charts
- Agent activity log
- Decision explanations
- TXT report
- PDF export

---

## 🏗️ System Architecture

```text
┌─────────────────────────────┐
│ Environmental / Weather Data│
│ Temp • Humidity • AQI • Rain│
│ Wind • Weather • Time        │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Data Validation        │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Data Preprocessing     │
│ Temperature Gap • Time Data │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Pattern Detection     │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Classification & Prediction │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│    AI Decision Support      │
│ Confidence + Explanation    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Window Recommendation       │
│ Open / Close / Partial      │
│ / No Change                 │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Energy & Sustainability     │
│ Estimates                   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Streamlit Dashboard & Report│
└─────────────────────────────┘
```

---

## 🧠 AI Workflow

```text
Real-Time / Manual Weather Data
              ↓
       Data Validation
              ↓
      Data Preprocessing
              ↓
       Pattern Detection
              ↓
        Classification
              ↓
          Prediction
              ↓
      Decision Support
              ↓
 Explainable AI / Granite Prompt
              ↓
 Window + Door Recommendation
              ↓
      Actuator Command
              ↓
Energy Saving + Sustainability Score
              ↓
      Dashboard + Report
```

---

## 🔄 Agentic AI Workflow

```text
AI Agent Starts
      ↓
Read Device Location
      ↓
Fetch Current Weather
      ↓
Calculate Environmental Conditions
      ↓
Detect Weather Pattern
      ↓
Predict Window State
      ↓
Generate Actuator Command
      ↓
Update Dashboard & Report
      ↓
Wait for Refresh Interval
      ↓
Repeat
```

In **Device Location Weather** mode, the automatic AI-agent operation can refresh the selected data interval, retrieve current weather information, recalculate the decision, and update the dashboard.

---

## 🧪 Example Scenarios

| Environmental Condition | Example Recommendation |
|---|---|
| Heavy rain | 🔒 Close Window |
| Unhealthy AQI | 🔒 Close Window |
| Cool & clean outdoor air | 🪟 Open Window |
| Moderate rain risk | 🪟 Partial |
| Hot outdoor conditions | ⚡ Energy-saving mode |
| Strong wind | 🔒 Close / safety-oriented action |

The application also considers combinations of conditions rather than relying on a single environmental parameter.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core application and data processing |
| **Streamlit** | Interactive web dashboard |
| **Open-Meteo** | Real-time weather data |
| **AccuWeather API** | Optional weather provider |
| **Groq API** | Optional AI-generated weather suggestions |
| **IBM Granite / LLM Prompting** | Explainable AI prompt layer |
| **AI-style Rule Engine** | Offline pattern detection and decision logic |
| **PDF / TXT Reporting** | Report generation |

> **Note:** The current implementation uses deterministic AI-style scoring so the application can run offline and remain easy to explain during project review. The IBM Granite prompt can be connected to IBM watsonx.ai later when suitable cloud credentials are available.

---

## 📁 Project Structure

```text
AI-Based-Smart-Window-Control-System/
│
├── app.py
├── dashboard.py
├── ai_engine.py
├── weather.py
├── prompt.py
├── utils.py
├── requirements.txt
├── README.md
│
├── assets/
│   └── ...
│
└── data/
    └── sample_data.csv
```

### Main Files

- **`app.py`** — Starts the Streamlit application.
- **`dashboard.py`** — Builds the dashboard, workflow panels, charts, and report downloads.
- **`ai_engine.py`** — Handles validation, preprocessing, pattern detection, classification, prediction, decision support, explainability, and sustainability scoring.
- **`weather.py`** — Provides offline/sample weather data and live weather integrations.
- **`prompt.py`** — Contains the IBM Granite / LLM explanation prompt.
- **`utils.py`** — Shared reporting, PDF, and helper functions.
- **`data/sample_data.csv`** — Test scenarios.
- **`assets/`** — Project visual assets.

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Run the application

```bash
streamlit run app.py
```

The Streamlit application will open in your browser.

---

## 🔑 Optional API Configuration

### AccuWeather

Set your API key before starting the application:

```bash
export ACCUWEATHER_API_KEY="your_api_key_here"
streamlit run app.py
```

### Groq

For AI-generated weather suggestions:

```bash
export GROQ_API_KEY="your_groq_key_here"
streamlit run app.py
```

If `GROQ_API_KEY` is unavailable, the application continues using its local AI-style rule engine.

---

## 🔐 Responsible AI

The project is designed around responsible AI principles:

- **Transparency:** Recommendations include understandable reasoning.
- **Human Oversight:** Users can review and override recommendations.
- **Privacy:** The system focuses on environmental information required for analysis.
- **Reliability:** Inputs are validated before decision processing.
- **Safety:** Weather and environmental conditions are considered before window recommendations.
- **Explainability:** The system provides the factors behind its recommendation.

---

## 📈 Expected Impact

The project aims to:

- Reduce unnecessary electricity consumption.
- Improve household energy efficiency.
- Reduce dependence on cooling and heating systems where appropriate.
- Improve indoor comfort and ventilation.
- Support better indoor air-quality decisions.
- Encourage sustainable living.
- Provide a foundation for future smart-home and IoT integration.

The current project is a software prototype; physical automated window hardware is a potential future extension.

---

## 🔮 Future Scope

- IoT-enabled motorized window integration
- Real-time indoor sensors
- Smart-home platform integration
- Advanced machine-learning models
- Personalized user preferences
- Historical energy-consumption analytics
- Mobile application
- More sophisticated RAG knowledge base
- IBM Granite integration through watsonx.ai
- Automated model evaluation and performance monitoring

---

## 👨‍💻 Project Information

**Project:** AI-Based Smart Window Control System for Sustainable Homes  
**Student:** Vinayak Ojha  
**Department:** Data Science & AI  
**University:** Chandigarh University  
**Program:** AI for Sustainability Virtual Internship  
**Focus:** Artificial Intelligence • Sustainability • Smart Homes • Energy Efficiency

---

## 📜 Project Note

This project demonstrates how AI-based environmental analysis and decision support can be applied to a real-world sustainability problem. The current implementation prioritizes explainability, reproducibility, and offline operation while providing a pathway toward advanced LLM, RAG, agentic AI, and IoT integration.

---

## ⭐ If You Find This Project Useful

If this project helped you understand AI, sustainability, or smart-home automation, consider giving the repository a ⭐ on GitHub.
