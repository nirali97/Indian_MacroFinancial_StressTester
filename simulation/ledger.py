"""Records money transfers so that payments between agents are tracked in one place."""

import sqlite3
from pathlib import Path

class Ledger:
    """Move money between two entities and record the transaction."""
    def __init__(self, db_path="data/simulation.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month INTEGER NOT NULL,
                    sender TEXT NOT NULL,
                    receiver TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount >= 0),
                    transaction_type TEXT NOT NULL
                )
            """)

    @staticmethod
    def _id(entity):
        return str(getattr(entity, "entity_id", getattr(entity, "name", "unknown")))

    def transfer(self, sender, receiver, amount, transaction_type, month=0):
        amount = float(amount)
        if amount < 0 or not amount == amount:
            raise ValueError("Transfer amount must be a non-negative finite number.")
        if amount == 0:
            return True
        if getattr(sender, "cash_reserves", 0.0) + 1e-9 < amount:
            return False
        sender.cash_reserves -= amount
        receiver.cash_reserves += amount
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO transactions(month,sender,receiver,amount,transaction_type) VALUES(?,?,?,?,?)",
                    (int(month), self._id(sender), self._id(receiver), amount, str(transaction_type))
                )
        except Exception:
            sender.cash_reserves += amount
            receiver.cash_reserves -= amount
            raise
        return True
