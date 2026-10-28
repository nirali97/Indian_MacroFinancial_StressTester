# Groq LLM setup

This project can use Groq for two simulated policy decisions:

- **RBI Governor:** suggests the repo rate from the current macroeconomic conditions.
- **Bank CEO agents:** suggest each bank's risk appetite and lending limit.

The XGBoost Oracle is separate. It estimates MSME default risk; it is not an LLM and does not need a Groq key.

## 1. Install the packages

Activate the project's virtual environment and install the requirements:

```bash
python -m pip install -r requirements.txt
```

## 2. Make your local settings file

From the project root, run:

```bash
cp .env.example .env
```

Open `.env` in VS Code and replace `put_your_key_here` with your key from [Groq Console](https://console.groq.com/keys). Do not include quotes unless the key itself requires them. The default model is set in `GROQ_MODEL`; if Groq retires that model, change it to a currently available model in your Groq account.

**Keep `.env private.** It is listed in `.gitignore`; do not upload it or paste your key into source files, screenshots, or GitHub.

## 3. Run a short test

```bash
python scripts/run_sim.py --months 2
```

The terminal output focuses on simulation indicators. To see the source and reasoning for individual decisions, open the dashboard:

```bash
streamlit run frontend/app.py
```

Click **Run one month**, then open the **Agent decisions** tab. The `source` column should say `Groq` when an LLM response was accepted. If it says `Rule-based fallback`, the simulation continued without a usable LLM response. The dashboard also shows whether a key was detected, but a detected key alone does not prove the API call succeeded.

## 4. Run without LLM calls

```bash
python scripts/run_sim.py --months 2 --no-llm
```

This disables Groq for both the RBI Governor and bank strategy agents. Rule-based decisions still allow the simulation to run. `--no-ml` separately disables XGBoost loan scoring.

## How fallback works

The app catches API, response-format and parsing errors. It then uses a simple rule-based decision and records the source as `Rule-based fallback`. This is intentional so a temporary network issue does not stop the simulation. During development, inspect the agent's `last_error` when diagnosing why Groq was not used; do not display API keys or full request headers in logs.

## What this does not mean

The agents are simulated decision-makers, not replicas of the real RBI or any named bank's actual internal policy. Groq responses are generated text, not verified financial advice. This project is for learning and experimentation, not real lending, investment, or regulatory decisions.
