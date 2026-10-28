# Code style notes

- Keep names and function signatures straightforward and consistent with the surrounding code.
- Use short docstrings for modules/classes/functions where they explain purpose or behaviour.
- Prefer small changes that can be tested independently.
- Keep feature order and encoder artifacts in sync with the trained model.
- Label fallbacks honestly; do not describe global feature importance as a per-applicant SHAP explanation.
- Preserve `data/simulation_history.db`; write new runs to `data/simulation.db`.
- Comments should explain why a choice exists, not repeat what the next line says.

- Put credentials in `.env`; never hard-code API keys or commit `.env`.
- Record the source of decisions when an external model can fall back to local rules.
- For LLM code, test response parsing with mocked clients so the test suite does not need a real API key.
- Comments at major steps should explain the reason for the step in plain language, rather than narrating every line.
