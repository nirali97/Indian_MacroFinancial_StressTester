"""Runs the simulation one month at a time and connects all the other parts."""

import json, random, sqlite3
from pathlib import Path
from simulation.agents import Bank, MSME, Consumer, Loan
from simulation.ledger import Ledger
from simulation.world_state import WorldState
from simulation.shocks import apply_shocks
from agents.bank_ceo import BankCEOAgent

BANK_NAMES = ["SBI", "HDFC Bank", "ICICI Bank"]
SHOCK_ATTRS = {
    "MONSOON_DEFICIT":"shock_monsoon", "NBFC_CRISIS":"shock_nbfc",
    "FII_PULLOUT":"shock_fii", "YES_BANK_SPIRAL":"shock_yes_bank"
}

class SimulationEngine:
    """Controls the monthly steps and connects the agents, shocks, model and logs."""
    def __init__(self, n_banks=3, n_msmes=120, n_consumers=500,
                 ml_oracle=None, rbi_agent=None, bank_ceo_agent=None,
                 db_path="data/simulation.db", seed=42, use_llm=True):
        self.n_banks, self.n_msmes, self.n_consumers = n_banks, n_msmes, n_consumers
        self.ml_oracle, self.rbi_agent = ml_oracle, rbi_agent
        self.bank_ceo_agent = bank_ceo_agent
        self.use_llm = use_llm
        self.db_path = db_path
        self.seed = seed
        random.seed(seed)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.world_state = WorldState()
        self.ledger = Ledger(db_path)
        self.banks = [Bank(BANK_NAMES[i] if i < len(BANK_NAMES) else f"Bank {i+1}") for i in range(n_banks)]
        self.msmes = [MSME(i) for i in range(n_msmes)]
        self.consumers = [Consumer(i) for i in range(n_consumers)]
        # Each bank gets its own strategy agent; use_llm=False disables all Groq calls.
        self.bank_agents = {
            b.entity_id: (bank_ceo_agent if bank_ceo_agent and len(self.banks) == 1 and use_llm
                          else BankCEOAgent(b.name, enabled=use_llm))
            for b in self.banks
        }
        self._init_db()
        self._seed_initial_loans()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS world_state_log (
              month INTEGER PRIMARY KEY, gdp_growth REAL, repo_rate REAL, msme_default_rate REAL,
              avg_npa REAL, interbank_liquidity REAL, cpi REAL, inr_usd REAL, active_shocks TEXT);
            CREATE TABLE IF NOT EXISTS npa_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT, month INTEGER, bank_id TEXT, npa_ratio REAL);
            CREATE TABLE IF NOT EXISTS agent_decisions (
              id INTEGER PRIMARY KEY AUTOINCREMENT, month INTEGER, agent TEXT, decision TEXT,
              reasoning TEXT, source TEXT DEFAULT 'Unknown');
            CREATE TABLE IF NOT EXISTS shap_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT, month INTEGER, msme_id TEXT, decision TEXT,
              prob_default REAL, shap_json TEXT);
            """)
            # Older project databases don't have a source column yet, so add it safely.
            columns = {row[1] for row in c.execute("PRAGMA table_info(agent_decisions)")}
            if "source" not in columns:
                c.execute("ALTER TABLE agent_decisions ADD COLUMN source TEXT DEFAULT 'Unknown'")

    def _seed_initial_loans(self):
        for msme in self.msmes:
            if random.random() < 0.30:
                bank = random.choice(self.banks)
                amount = min(random.uniform(500, 1500), bank.cash_reserves * 0.02, msme.cash_reserves * 0.1 + 500)
                loan = self._create_loan(amount)
                if self.ledger.transfer(bank, msme, amount, "INITIAL_LOAN", 0):
                    bank.issue_loan(loan); msme.active_loans.append(loan)
        for consumer in self.consumers:
            if random.random() < 0.12:
                bank = random.choice(self.banks)
                amount = min(random.uniform(100, 600), bank.cash_reserves * 0.01)
                loan = self._create_loan(amount)
                if self.ledger.transfer(bank, consumer, amount, "INITIAL_LOAN", 0):
                    bank.issue_loan(loan); consumer.active_loans.append(loan)
        self._update_npa()

    def _create_loan(self, principal):
        rate = max(3.0, self.world_state.rbi_repo_rate_pct + random.uniform(2.0, 5.0))
        return Loan(principal, rate, random.choice([12, 18, 24, 36]))

    def _update_npa(self):
        for b in self.banks:
            b.calculate_npa_ratio()
        total = sum(sum(l.outstanding for l in b.loan_book) for b in self.banks)
        npa = sum(sum(l.outstanding for l in b.loan_book if l.is_npa) for b in self.banks)
        self.world_state.avg_npa_pct = 100*npa/total if total else 0.0
        self.world_state.total_credit_outstanding = total

    def trigger_shock(self, shock_name):
        key = shock_name.upper()
        if key not in SHOCK_ATTRS:
            raise ValueError(f"Unknown shock: {shock_name}")
        setattr(self.world_state, SHOCK_ATTRS[key], True)

    def clear_shock(self, shock_name):
        key = shock_name.upper()
        if key not in SHOCK_ATTRS:
            raise ValueError(f"Unknown shock: {shock_name}")
        setattr(self.world_state, SHOCK_ATTRS[key], False)

    def step(self):
        # One call represents one month in the toy economy.
        ws = self.world_state
        ws.month += 1

        # First apply any active shock, then let people and businesses make payments.
        apply_shocks(ws, self.banks)
        for consumer in self.consumers:
            consumer.pay_emis_and_spend(ws, self.ledger, self.banks)
        for msme in self.msmes:
            msme.check_default(ws, self.ledger, self.banks)

        # Update bank health before new lending so the decisions use the latest NPA values.
        self._update_npa()
        self._issue_new_loans()
        self._update_npa()
        msme_defaults = sum(m.status == "DEFAULT" for m in self.msmes)
        consumer_defaults = sum(c.status == "DEFAULT" for c in self.consumers)
        ws.msme_default_rate_pct = 100 * msme_defaults / max(1, len(self.msmes))
        ws.consumer_default_rate_pct = 100 * consumer_defaults / max(1, len(self.consumers))
        ws.gdp_growth_pct = max(-5, min(12, ws.gdp_growth_pct - 0.008*ws.msme_default_rate_pct))
        if self.rbi_agent and ws.month % 2 == 0:
            decision = self.rbi_agent.decide(ws)
            ws.rbi_repo_rate_pct = float(decision["new_repo_rate"])
            ws.rbi_last_reasoning = str(decision.get("reasoning", ""))
            self._log_decision("RBI Governor", "REPO_RATE", ws.rbi_last_reasoning, decision.get("source", "Unknown"))
        for bank in self.banks:
            agent = self.bank_agents.get(bank.entity_id)
            strategy = agent.decide_strategy(ws, bank.npa_ratio) if agent else {}
            bank.strategy = strategy
            if strategy:
                self._log_decision(bank.name, strategy.get("risk_appetite", "moderate"), strategy.get("reasoning", ""), strategy.get("source", "Unknown"))
        self._write_logs()
        return ws

    def _issue_new_loans(self):
        # Only active MSMEs with room for another loan can apply this month.
        candidates = [m for m in self.msmes if m.status == "ACTIVE" and len(m.active_loans) < 2]
        random.shuffle(candidates)
        for msme in candidates[:max(1, min(10, len(candidates)))]:
            bank = min(self.banks, key=lambda b: b.npa_ratio)
            if bank.is_under_prompt_action or bank.cash_reserves < 500:
                continue
            features = {
                "annual_revenue": msme.annual_revenue, "cibil_score": msme.cibil_score,
                "existing_debt": msme.existing_debt, "import_dependent": msme.import_dependent,
                "employee_count": msme.employee_count, "years_in_business": msme.years_in_business,
                "fixed_costs_monthly": msme.fixed_costs, "sector": msme.sector, "region": msme.region
            }
            # The ML model estimates default risk; the bank strategy adjusts the approval threshold.
            result = None
            if self.ml_oracle:
                try:
                    result = self.ml_oracle.assess(features)
                except Exception as exc:
                    self._log_decision("Loan Oracle", "FALLBACK", f"Oracle unavailable: {type(exc).__name__}", "Rule-based fallback")
            # If the model is unavailable, keep the demo usable with a simple CIBIL rule.
            if result:
                prob = float(result["prob_default"])
                threshold = float(result.get("threshold", 0.35))
                strategy = bank.strategy or {}
                appetite = strategy.get("risk_appetite", "moderate")
                threshold *= {"conservative":0.8, "moderate":1.0, "aggressive":1.2}.get(appetite, 1.0)
                approved = prob < min(0.8, max(0.1, threshold))
                decision = "APPROVED" if approved else "REJECTED"
                self._log_shap(msme.entity_id, decision, prob, result.get("shap", {}))
            else:
                prob = None
                approved = msme.cibil_score >= 620
                decision = "APPROVED" if approved else "REJECTED"
            self._log_decision("Loan Oracle", decision, f"{msme.entity_id}; estimated default probability={prob if prob is not None else 'n/a'}", "XGBoost" if result else "Rule-based fallback")
            if not approved:
                continue
            strategy_pct = float((bank.strategy or {}).get("max_loan_pct_of_capital", 0.10))
            amount = min(random.uniform(500, 1500), bank.cash_reserves * strategy_pct)
            if amount < 100:
                continue
            loan = self._create_loan(amount)
            if self.ledger.transfer(bank, msme, amount, "MSME_LOAN", self.world_state.month):
                bank.issue_loan(loan)
                msme.active_loans.append(loan)

    def _log_decision(self, agent, decision, reasoning, source="Unknown"):
        # I log the source beside the decision so I can tell Groq output from a fallback.
        with sqlite3.connect(self.db_path) as c:
            c.execute(
                "INSERT INTO agent_decisions(month,agent,decision,reasoning,source) VALUES(?,?,?,?,?)",
                (self.world_state.month, agent, decision, str(reasoning)[:1000], str(source)[:100]),
            )

    def _log_shap(self, msme_id, decision, prob, shap_data):
        with sqlite3.connect(self.db_path) as c:
            c.execute("INSERT INTO shap_log(month,msme_id,decision,prob_default,shap_json) VALUES(?,?,?,?,?)",
                      (self.world_state.month, msme_id, decision, prob, json.dumps(shap_data)))

    def _write_logs(self):
        ws = self.world_state
        with sqlite3.connect(self.db_path) as c:
            c.execute("""INSERT OR REPLACE INTO world_state_log
                (month,gdp_growth,repo_rate,msme_default_rate,avg_npa,interbank_liquidity,cpi,inr_usd,active_shocks)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (ws.month,ws.gdp_growth_pct,ws.rbi_repo_rate_pct,ws.msme_default_rate_pct,
                 ws.avg_npa_pct,ws.interbank_liquidity,ws.cpi_inflation_pct,ws.inr_usd_rate,
                 json.dumps(ws.active_shocks())))
            for b in self.banks:
                c.execute("INSERT INTO npa_log(month,bank_id,npa_ratio) VALUES(?,?,?)",
                          (ws.month,b.entity_id,b.npa_ratio))

    def reset(self, clear_history=False):
        for attr in ("shock_monsoon","shock_nbfc","shock_fii","shock_yes_bank"):
            setattr(self.world_state, attr, False)
        db_path = self.db_path
        args = (self.n_banks, self.n_msmes, self.n_consumers, self.ml_oracle, self.rbi_agent,
                self.bank_ceo_agent, db_path, self.seed, self.use_llm)
        if clear_history:
            with sqlite3.connect(db_path) as c:
                for table in ("world_state_log","npa_log","agent_decisions","shap_log","transactions"):
                    c.execute(f"DELETE FROM {table}")
        self.__init__(*args)
