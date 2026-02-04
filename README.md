# 🏥 DR-PACT: AI-Driven Contract Testing for Medical Devices

> Automatically generate contract tests between microservices to prevent integration errors in medical device software.

## 📋 The Problem

In medical device software, integration errors between services can be **life-threatening**. When a TypeScript frontend wrapper and a Python algorithm backend disagree on data formats (e.g., `mg/dL` vs `mmol/L` for glucose), patients can receive dangerous insulin doses.

## 💡 The Solution

**DR-PACT** (Doctor Pact) uses an AI agent to:
1. **Read** your TypeScript HTTP client code
2. **Analyze** the request/response structures
3. **Generate** Pact contract tests automatically
4. **Verify** the Python provider satisfies the contract

## 🏗️ Project Structure

```
dr-pact-demo/
├── agent/                  # 🤖 The AI "Brain"
│   ├── generator.py        # Main script - calls LLM API
│   ├── prompt.txt          # System prompt for the LLM
│   └── requirements.txt    # Python dependencies
│
├── consumer-ts/            # 📱 TypeScript Wrapper Service
│   ├── src/
│   │   └── insulinClient.ts   # HTTP client we want to test
│   ├── tests/
│   │   └── contract.spec.ts   # AI-generated Pact tests
│   ├── package.json
│   └── jest.config.js
│
├── provider-py/            # 🧮 Python Algorithm Service
│   ├── app.py              # Flask API (insulin calculations)
│   ├── tests/
│   │   └── test_pact.py    # Provider verification tests
│   └── requirements.txt
│
└── pacts/                  # 📄 Contract JSON files
    └── InsulinWrapperService-RiskAlgoService.json
```

## 🚀 Quick Start

### 1. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install agent dependencies
pip install -r agent/requirements.txt

# Install provider dependencies
pip install -r provider-py/requirements.txt
```

### 2. Setup TypeScript Consumer

```bash
cd consumer-ts
npm install
cd ..
```

### 3. Configure API Keys

```bash
# Copy the example env file
cp agent/.env.example agent/.env

# Edit and add your API key (choose one):
# - OPENAI_API_KEY for GPT-4o
# - ANTHROPIC_API_KEY for Claude 3.5 Sonnet
```

### 4. Run the Demo!

```bash
# Generate contract tests using AI
python agent/generator.py --provider openai --verify

# Or use Anthropic
python agent/generator.py --provider anthropic --verify
```

## 🧪 Testing Commands

```bash
# Start the Python provider
cd provider-py
python app.py

# In another terminal - run consumer contract tests
cd consumer-ts
npm test

# Verify provider against contracts
cd provider-py
pytest tests/test_pact.py -v
```

## � Contract Testing Flow

This project follows proper **Consumer-Driven Contract Testing** principles:

### 1. Consumer Tests Generate Pacts (Pact as Source of Truth)
```
consumer-ts/tests/contract.spec.ts
    ↓
Uses InsulinClient against Pact Mock Server
    ↓
Generates pacts/InsulinClient-RiskAlgoService.json
```

The consumer tests:
- Define expected interactions (request/response pairs)
- Test the **actual client code** (`InsulinClient`) against a **mock server**
- The mock server responses come from the Pact contract (source of truth)
- Generate a Pact JSON file capturing the consumer's expectations

### 2. Provider Verifies Against Pact Contract
```
pacts/InsulinClient-RiskAlgoService.json (SOURCE OF TRUTH)
    ↓
Pact Verifier reads ALL interactions from Pact file
    ↓
Replays requests against provider, verifies responses match contract
```

The provider tests:
- Read the Pact file (the ONLY source of truth)
- Pact Verifier replays each interaction from the contract
- Verify the provider's responses match the contract expectations
- NO manual HTTP requests - everything comes from the Pact file

### Key Principles:
- **Pact is the source of truth** - not the live server
- **Consumer tests don't hit live servers** - they use Pact mock server
- **Provider tests only reference the Pact file** - Verifier replays interactions
- **Provider tests verify against the contract** - ensuring compatibility

## �🔌 API Endpoints

### Health Check
```http
GET /health
```

### Calculate Bolus
```http
POST /calculate/bolus
Content-Type: application/json

{
  "patient_id": "patient-001",
  "current_glucose_mg_dl": 180,
  "carbs_grams": 45,
  "insulin_on_board_units": 1.5
}
```

### Calculate Basal Adjustment
```http
POST /calculate/basal-adjustment
Content-Type: application/json

{
  "patient_id": "patient-001",
  "glucose_readings": [120, 135, 150, 165, 180, 195],
  "current_basal_rate": 1.0
}
```

## ⚠️ Disclaimer

This is a **DEMONSTRATION PROJECT** for educational purposes only. 

**NOT FOR ACTUAL MEDICAL USE.**

Real insulin dosing algorithms require:
- FDA/CE certification
- Clinical validation
- Patient-specific parameters
- Professional medical oversight

## 📚 Learn More

- [Pact Documentation](https://docs.pact.io/)
- [Contract Testing](https://martinfowler.com/bliki/ContractTest.html)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic Claude](https://docs.anthropic.com/)

---

Built with ❤️ for patient safety.
