"""Basic objects used in the simulation, such as banks, loans, MSMEs and consumers."""

from dataclasses import dataclass
import math
import random

@dataclass
class Loan:
    """Stores the details of a loan and calculates its repayment values."""
    principal: float
    annual_rate_pct: float
    tenure_months: int
    months_paid: int = 0
    is_npa: bool = False
    outstanding_principal: float | None = None

    def __post_init__(self):
        self.principal = float(self.principal)
        if self.outstanding_principal is None:
            self.outstanding_principal = self.principal
        self.tenure_months = max(1, int(self.tenure_months))

    @property
    def emi(self):
        r = self.annual_rate_pct / 1200
        n = self.tenure_months
        if r == 0:
            return self.principal / n
        return self.principal * r * (1 + r) ** n / ((1 + r) ** n - 1)

    @property
    def outstanding(self):
        return max(0.0, float(self.outstanding_principal or 0.0))

    def apply_payment(self, amount):
        if self.outstanding <= 0:
            return 0.0
        r = self.annual_rate_pct / 1200
        interest = self.outstanding * r
        principal_paid = max(0.0, min(self.outstanding, float(amount) - interest))
        self.outstanding_principal = max(0.0, self.outstanding - principal_paid)
        self.months_paid += 1
        return principal_paid

class Bank:
    """Represents a bank, including its cash, loans and NPA ratio."""
    def __init__(self, name, cash_reserves=50000.0):
        self.name = name
        self.entity_id = f"bank_{name.replace(' ', '_')}"
        self.cash_reserves = float(cash_reserves)
        self.loan_book = []
        self.npa_ratio = 0.0
        self.total_loans_issued = 0
        self.is_under_prompt_action = False
        self.strategy = {"risk_appetite": "moderate", "max_loan_pct_of_capital": 0.10}

    def issue_loan(self, loan):
        self.loan_book.append(loan)
        self.total_loans_issued += 1

    def calculate_npa_ratio(self):
        total = sum(loan.outstanding for loan in self.loan_book)
        npa = sum(loan.outstanding for loan in self.loan_book if loan.is_npa)
        self.npa_ratio = (100.0 * npa / total) if total > 0 else 0.0
        self.is_under_prompt_action = self.npa_ratio >= 8.0
        return self.npa_ratio

class MSME:
    """Represents a small business that earns revenue and may repay or default on loans."""
    SECTORS = ["Manufacturing", "Retail", "Agriculture", "Services", "Construction"]
    REGIONS = ["Urban", "Rural", "Semi-Urban"]

    def __init__(self, idx):
        self.entity_id = f"msme_{idx:04d}"
        self.sector = random.choice(self.SECTORS)
        self.region = random.choice(self.REGIONS)
        self.cibil_score = random.randint(550, 850)
        self.cash_reserves = random.uniform(500, 5000)
        self.fixed_costs = random.uniform(50, 300)
        self.annual_revenue = random.uniform(1200, 24000)
        self.import_dependent = int(random.random() < 0.22)
        self.employee_count = random.randint(1, 250)
        self.years_in_business = random.randint(1, 30)
        self.existing_debt = random.uniform(0, 0.4 * self.annual_revenue)
        self.active_loans = []
        self.status = "ACTIVE"
        self.months_survived = 0

    def generate_revenue(self, world_state):
        monthly = self.annual_revenue / 12
        multiplier = max(0.2, 1 + (world_state.gdp_growth_pct - 6.5) / 100)
        if world_state.shock_monsoon and self.sector == "Agriculture":
            multiplier *= 0.72
        if world_state.shock_nbfc:
            multiplier *= 0.94
        if world_state.shock_fii and self.import_dependent:
            multiplier *= 0.88
        return max(0.0, monthly * multiplier * random.uniform(0.8, 1.2))

    def check_default(self, world_state, ledger, banks):
        if self.status != "ACTIVE":
            return
        self.months_survived += 1
        revenue = self.generate_revenue(world_state)
        emi_due = sum(l.emi for l in self.active_loans if not l.is_npa and l.outstanding > 0)
        required = self.fixed_costs + emi_due
        available = self.cash_reserves + revenue
        if available < required:
            self.cash_reserves += revenue
            self.status = "DEFAULT"
            for loan in self.active_loans:
                if loan.outstanding > 0:
                    loan.is_npa = True
            return
        self.cash_reserves += revenue
        self.cash_reserves -= self.fixed_costs
        remaining = emi_due
        for loan in self.active_loans:
            if remaining <= 0:
                break
            if loan.is_npa or loan.outstanding <= 0:
                continue
            payment = min(loan.emi, remaining, self.cash_reserves)
            bank = next((b for b in banks if loan in b.loan_book), None)
            if bank and payment > 0 and ledger.transfer(self, bank, payment, "MSME_EMI", world_state.month):
                loan.apply_payment(payment)
                remaining -= payment
            else:
                loan.is_npa = True

class Consumer:
    """Represents a customer who earns income and pays loan instalments."""
    def __init__(self, idx):
        self.entity_id = f"consumer_{idx:05d}"
        self.income = random.uniform(15, 100)
        self.cash_reserves = random.uniform(100, 2000)
        self.cibil_score = random.randint(500, 850)
        self.active_loans = []
        self.status = "ACTIVE"

    def pay_emis_and_spend(self, world_state, ledger, banks):
        if self.status != "ACTIVE":
            return
        self.cash_reserves += self.income
        for loan in self.active_loans:
            if loan.is_npa or loan.outstanding <= 0:
                continue
            bank = next((b for b in banks if loan in b.loan_book), None)
            payment = min(loan.emi, self.cash_reserves)
            if payment <= 0 or bank is None:
                loan.is_npa = True
                self.status = "DEFAULT"
                continue
            if ledger.transfer(self, bank, payment, "CONSUMER_EMI", world_state.month):
                loan.apply_payment(payment)
            else:
                loan.is_npa = True
                self.status = "DEFAULT"
        self.cash_reserves = max(0.0, self.cash_reserves - min(self.cash_reserves, random.uniform(5, 25)))
