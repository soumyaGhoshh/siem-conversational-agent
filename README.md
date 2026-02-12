# SIEM Conversational Agent

An AI-powered Security Information and Event Management (SIEM) assistant designed for security analysts to interact with Wazuh/Elasticsearch data using natural language.

## 🚀 Features

- **Natural Language to DSL**: Convert plain English queries into complex Elasticsearch DSL.
- **Visual Attack Chains**: Automatically reconstructs potential attack narratives from log sequences.
- **Proactive Alerting**: Real-time scanning for high-severity threats (Level 10+).
- **Remediation Suggestions**: AI-driven actionable steps to mitigate detected threats.
- **Interactive Dashboard**: Modern UI with risk scoring and event distribution.

## 🛠️ Prerequisites

- Python 3.10+
- Node.js 18+
- Elasticsearch (or Wazuh Indexer)
- Google Gemini API Key

## ⚙️ Installation

### 1. Backend Setup
```bash
# Navigate to the root directory
cd siem-conversational-agent-main

# Install dependencies
pip install -r requirements.txt

# Generate a JWT secret
python src/gen_secret.py
```

### 2. Frontend Setup
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install
```

## 🏃 Running the Application

### Start the Backend
```bash
# From the root directory
$env:PYTHONPATH="src"
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload
```

### Start the Frontend
```bash
# From the frontend directory
npm run dev
```

Access the application at [http://localhost:3000](http://localhost:3000).

## 🔑 Environment Variables

Create a `.env` file in the root directory. Use `.env.example` as a template.

| Variable | Description |
| :--- | :--- |
| `GOOGLE_API_KEY` | Your Gemini API Key for LLM processing |
| `ELASTIC_URL` | URL of your Elasticsearch/Wazuh Indexer |
| `DEMO_MODE` | Set to `true` to use mock data if ES is unavailable |
| `JWT_SECRET` | Secret key for session authentication |

## 🛡️ Default Credentials
- **Username**: `analyst1`
- **Password**: `password123`
