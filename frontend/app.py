
import os
import sys
import sqlite3
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "data" / "simulation.db"
HISTORY_DB_PATH = ROOT / "data" / "simulation_history.db"

SHOCK_OPTIONS = {
    "Monsoon Deficit": "MONSOON_DEFICIT",
    "NBFC Crisis": "NBFC_CRISIS",
    "FII Pullout": "FII_PULLOUT",
    "Yes Bank Spiral": "YES_BANK_SPIRAL",
}

st.set_page_config(
    page_title="Indian Macro Financial Stress Tester",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# LIGHT CORPORATE THEME + INTRO ANIMATION
# ============================================================

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"] {
        background: #F5F7FA !important;
        color: #344054 !important;
    }

    h1, h2, h3, h4 {
        color: #243B53 !important;
        font-weight: 650 !important;
    }

    p, label, .stCaption {
        color: #667085;
    }

    [data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid #E0E5EB !important;
    }

    [data-testid="stSidebar"] * {
        color: #344054;
    }

    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E0E5EB !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: none !important;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {
        color: #667085 !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        color: #243B53 !important;
    }

    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        background: #FFFFFF !important;
        color: #344054 !important;
        border: 1px solid #D0D5DD !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        font-weight: 500 !important;
        transition: background-color 0.2s ease,
                    border-color 0.2s ease,
                    transform 0.15s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: #F0F2F5 !important;
        color: #243B53 !important;
        border-color: #98A2B3 !important;
    }

    .stButton > button:active {
        background: #E4E7EC !important;
        transform: scale(0.99);
    }

    .stButton > button:focus:not(:active) {
        box-shadow: 0 0 0 2px #D0D5DD !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        color: #344054 !important;
        border: 1px solid #D0D5DD !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] span,
    [data-testid="stSelectbox"] [data-baseweb="select"] input {
        color: #344054 !important;
        -webkit-text-fill-color: #344054 !important;
    }

    [data-testid="stSelectbox"] svg {
        color: #667085 !important;
        fill: #667085 !important;
    }

    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"],
    [role="option"] {
        background: #FFFFFF !important;
        color: #344054 !important;
    }

    [role="option"]:hover {
        background: #F0F2F5 !important;
    }

    [data-baseweb="input"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background: #FFFFFF !important;
        color: #344054 !important;
        border-color: #D0D5DD !important;
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        background: #FFFFFF !important;
        border: 1px solid #E0E5EB !important;
        border-radius: 9px !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }

    [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #E0E5EB !important;
        border-radius: 8px !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #667085 !important;
    }

    .stTabs [aria-selected="true"] {
        color: #243B53 !important;
        border-bottom-color: #98A2B3 !important;
    }

    hr {
        border-color: #E0E5EB !important;
    }

    .dashboard-subtitle {
        color: #667085;
        font-size: 15px;
        margin-top: -8px;
        margin-bottom: 24px;
    }

    .imfst-splash {
        position: fixed;
        inset: 0;
        width: 100vw;
        height: 100vh;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        background: #F5F7FA;
        pointer-events: none;
        animation: imfst-hide 3s ease-in-out forwards;
    }

    .imfst-logo {
        font-family: -apple-system, BlinkMacSystemFont,
                     "Segoe UI", sans-serif;
        font-size: clamp(56px, 10vw, 108px);
        font-weight: 800;
        letter-spacing: 0.18em;
        color: #243B53;
        opacity: 0;
        transform: scale(0.72);
        animation: imfst-expand 2.4s ease-out forwards;
    }

    .imfst-line {
        width: 0;
        height: 3px;
        margin-top: 20px;
        border-radius: 5px;
        background: #A9BDD3;
        animation: imfst-line-grow 1s ease 0.4s forwards;
    }

    .imfst-tagline {
        color: #667085;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.2em;
        margin-top: 17px;
        text-align: center;
        opacity: 0;
        animation: imfst-tagline-show 0.8s ease 0.5s forwards;
    }

    @keyframes imfst-expand {
        0% {
            opacity: 0;
            transform: scale(0.72);
        }
        55% {
            opacity: 1;
            transform: scale(1.08);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }

    @keyframes imfst-line-grow {
        to {
            width: min(260px, 65vw);
        }
    }

    @keyframes imfst-tagline-show {
        to {
            opacity: 1;
        }
    }

    @keyframes imfst-hide {
        0%, 78% {
            opacity: 1;
            visibility: visible;
        }
        100% {
            opacity: 0;
            visibility: hidden;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .imfst-splash,
        .imfst-logo,
        .imfst-line,
        .imfst-tagline {
            animation-duration: 0.01ms !important;
            animation-delay: 0ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# INTRO — SHOW ONCE PER SESSION
# ============================================================

if not st.session_state.get("imfst_intro_shown", False):
    st.session_state.imfst_intro_shown = True

    st.markdown(
        """
        <div class="imfst-splash">
            <div class="imfst-logo">IMFST</div>
            <div class="imfst-line"></div>
            <div class="imfst-tagline">
                INDIAN MACRO FINANCIAL STRESS TESTER
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_value(obj, *names, default=None):
    """Return the first available attribute or dictionary value."""
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]

        if obj is not None and hasattr(obj, name):
            return getattr(obj, name)

    return default


def safe_cell(value):
    """Convert nested/custom objects into safe table-cell values."""
    if value is None:
        return ""

    # Handle pandas/NumPy missing values without treating lists
    # or arrays as single Boolean values.
    if not isinstance(value, (dict, list, tuple, set)):
        try:
            missing = pd.isna(value)
            if isinstance(missing, bool) and missing:
                return ""
            if type(missing).__name__ == "bool_" and bool(missing):
                return ""
        except (TypeError, ValueError):
            pass

    # Convert custom objects such as Loan to dictionaries first.
    if hasattr(value, "__dict__") and not isinstance(
        value, (dict, list, tuple, set)
    ):
        try:
            value = vars(value)
        except (TypeError, ValueError):
            return str(value)

    # Recursively clean nested collections. This prevents
    # "Object of type Loan is not JSON serializable".
    if isinstance(value, dict):
        return json.dumps(
            {str(k): safe_cell(v) for k, v in value.items()},
            ensure_ascii=False,
            default=str,
        )

    if isinstance(value, (list, tuple, set)):
        return json.dumps(
            [safe_cell(item) for item in value],
            ensure_ascii=False,
            default=str,
        )

    if isinstance(value, (str, int, float, bool)):
        return value

    # NumPy scalar support.
    try:
        if hasattr(value, "item"):
            scalar = value.item()
            if scalar is not value:
                return safe_cell(scalar)
    except (TypeError, ValueError, OverflowError):
        pass

    # Dates, timestamps, and any remaining custom types.
    return str(value)


def clean_object_columns(df):
    """Sanitize object columns before passing them to Streamlit."""
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].map(safe_cell)

    return df


def to_dataframe(items):
    """Convert simulation entities or collections into a DataFrame."""
    if items is None:
        return pd.DataFrame()

    if isinstance(items, pd.DataFrame):
        return items.copy()

    if isinstance(items, dict):
        try:
            return pd.DataFrame(items)
        except (ValueError, TypeError):
            return pd.DataFrame([items])

    if isinstance(items, (list, tuple)):
        rows = []

        for item in items:
            if isinstance(item, dict):
                rows.append(item)
            elif hasattr(item, "__dict__"):
                rows.append(vars(item))
            else:
                rows.append({"Value": item})

        try:
            return pd.DataFrame(rows)
        except (ValueError, TypeError):
            return pd.DataFrame(
                {"Value": [safe_cell(item) for item in items]}
            )

    if hasattr(items, "__dict__"):
        return pd.DataFrame([vars(items)])

    return pd.DataFrame({"Value": [safe_cell(items)]})


def get_tables(db_path):
    """List SQLite tables if the database exists."""
    if not Path(db_path).exists():
        return []

    try:
        with sqlite3.connect(str(db_path)) as conn:
            rows = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()

        return [row[0] for row in rows]

    except sqlite3.Error:
        return []


def read_table(db_path, table_name, limit=None):
    """Read a known SQLite table safely."""
    if not table_name or not Path(db_path).exists():
        return pd.DataFrame()

    if table_name not in get_tables(db_path):
        return pd.DataFrame()

    query = f'SELECT * FROM "{table_name}"'

    if limit is not None:
        query += f" LIMIT {max(0, int(limit))}"

    try:
        with sqlite3.connect(str(db_path)) as conn:
            return pd.read_sql_query(query, conn)

    except (sqlite3.Error, pd.errors.DatabaseError, ValueError):
        return pd.DataFrame()


def find_table(db_path, candidates):
    """Return the first matching table name."""
    existing = get_tables(db_path)
    return next(
        (name for name in candidates if name in existing),
        None,
    )


def show_df(df, message="No data available yet.", height=None):
    """Display a DataFrame using the current Streamlit API."""
    if df is None or df.empty:
        st.info(message)
        return

    df = clean_object_columns(df)

    # Do not pass height=None; Streamlit requires a valid height.
    kwargs = {
        "width": "stretch",
        "hide_index": True,
    }

    if height is not None:
        kwargs["height"] = height

    st.dataframe(df, **kwargs)


def latest_value(df, candidates, default=None):
    """Return the last non-null value from a matching column."""
    if df is None or df.empty:
        return default

    for column in candidates:
        if column in df.columns:
            values = df[column].dropna()

            if not values.empty:
                return values.iloc[-1]

    return default


def fmt(value, suffix=""):
    """Format a numeric dashboard metric."""
    try:
        if value is None or pd.isna(value):
            return "N/A"

        return f"{float(value):.1f}{suffix}"

    except (ValueError, TypeError):
        return "N/A"


def get_banks(engine):
    """Get bank objects from the simulation engine."""
    banks = get_value(engine, "banks", default=[])

    if isinstance(banks, dict):
        return list(banks.values())

    return list(banks or [])


def get_msmes(engine):
    """Get MSME objects from the simulation engine."""
    msmes = get_value(engine, "msmes", default=[])

    if isinstance(msmes, dict):
        return list(msmes.values())

    return list(msmes or [])


def first_existing_column(df, candidates):
    """Find the first candidate column present in a DataFrame."""
    if df is None or df.empty:
        return None

    return next(
        (col for col in candidates if col in df.columns),
        None,
    )


def get_active_shocks(engine):
    """Read the active scenario names from WorldState."""
    ws = get_value(engine, "world_state", "ws", "state")

    active_method = get_value(ws, "active_shocks")

    if callable(active_method):
        try:
            return list(active_method())
        except Exception:
            pass

    # Fallback for WorldState implementations without active_shocks().
    shock_attributes = {
        "MONSOON_DEFICIT": "shock_monsoon",
        "NBFC_CRISIS": "shock_nbfc",
        "FII_PULLOUT": "shock_fii",
        "YES_BANK_SPIRAL": "shock_yes_bank",
    }

    return [
        name
        for name, attribute in shock_attributes.items()
        if bool(get_value(ws, attribute, default=False))
    ]


def calculate_latest_system_npa(npa_log):
    """Calculate average bank NPA for the latest logged month."""
    if npa_log is None or npa_log.empty:
        return None

    month_col = first_existing_column(
        npa_log,
        ["month", "simulation_month", "month_number"],
    )

    npa_col = first_existing_column(
        npa_log,
        ["npa_ratio", "npa_ratio_pct", "system_npa_pct", "system_npa"],
    )

    if npa_col is None:
        return None

    data = npa_log.copy()
    data[npa_col] = pd.to_numeric(data[npa_col], errors="coerce")
    data = data.dropna(subset=[npa_col])

    if data.empty:
        return None

    if month_col is not None:
        latest_month = data[month_col].max()
        latest_data = data[data[month_col] == latest_month]

        if not latest_data.empty:
            data = latest_data

    return data[npa_col].mean()


# ============================================================
# SIMULATION INITIALIZATION
# ============================================================

from simulation.engine import SimulationEngine

if "engine" not in st.session_state:
    try:
        st.session_state.engine = SimulationEngine(
            db_path=str(DB_PATH),
            use_llm=True,
        )
        st.session_state.engine_error = None

    except Exception as exc:
        st.session_state.engine = None
        st.session_state.engine_error = str(exc)

engine = st.session_state.engine


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.title("Indian Macro Financial Stress Tester")

st.markdown(
    """
    <div class="dashboard-subtitle">
        Explore macroeconomic shocks, banking-sector resilience,
        and MSME credit risk through interactive simulations.
    </div>
    """,
    unsafe_allow_html=True,
)

if engine is None:
    st.error("Could not initialize the simulation engine.")

    with st.expander("View initialization error"):
        st.code(
            st.session_state.get(
                "engine_error",
                "Unknown error",
            )
        )

    st.stop()

if "action_feedback" in st.session_state:
    level, message = st.session_state.pop("action_feedback")

    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    else:
        st.error(message)


# ============================================================
# SIDEBAR CONTROLS
# ============================================================

with st.sidebar:
    st.markdown("## Simulation Controls")
    st.caption(
        "Advance the economy or test a financial stress scenario."
    )

    if st.button(
        "Run One Month",
        width="stretch",
        key="run_month",
    ):
        try:
            with st.spinner("Advancing the simulation..."):
                engine.step()

            st.session_state.action_feedback = (
                "success",
                "Simulation advanced by one month.",
            )
            st.rerun()

        except Exception as exc:
            st.error(f"Could not advance simulation: {exc}")

    if st.button(
        "Reset Simulation",
        width="stretch",
        key="reset_simulation",
    ):
        try:
            with st.spinner("Resetting simulation..."):
                engine.reset()

            st.session_state.action_feedback = (
                "success",
                "Simulation reset successfully.",
            )
            st.rerun()

        except Exception as exc:
            st.error(f"Could not reset simulation: {exc}")

    st.divider()
    st.markdown("## Stress Scenarios")

    scenario_labels = ["None"] + list(SHOCK_OPTIONS.keys())

    selected_label = st.selectbox(
        "Select a scenario",
        options=scenario_labels,
        key="scenario_selection",
    )

    selected_scenario = SHOCK_OPTIONS.get(selected_label)

    if st.button(
        "Activate Stress Scenario",
        width="stretch",
        key="activate_stress",
    ):
        if selected_scenario is None:
            st.warning("Select a stress scenario first.")
        else:
            try:
                # This is the actual method in simulation/engine.py.
                engine.trigger_shock(selected_scenario)

                st.session_state.action_feedback = (
                    "success",
                    f"Activated {selected_label}.",
                )
                st.rerun()

            except Exception as exc:
                st.error(f"Could not activate scenario: {exc}")

    if st.button(
        "Clear Stress Scenarios",
        width="stretch",
        key="clear_stress",
    ):
        try:
            # The engine requires a shock name for each call.
            for shock_name in SHOCK_OPTIONS.values():
                engine.clear_shock(shock_name)

            st.session_state.action_feedback = (
                "success",
                "All stress scenarios have been cleared.",
            )
            st.rerun()

        except Exception as exc:
            st.error(f"Could not clear scenarios: {exc}")

    st.divider()
    st.markdown("## AI Agents")

    if os.getenv("GROQ_API_KEY"):
        st.caption("Groq API key detected.")
    else:
        st.caption(
            "Groq API key not detected in the environment. "
            "Check the project-root .env and how environment variables "
            "are loaded by the project."
        )


# ============================================================
# CURRENT STATE AND DATABASE LOGS
# ============================================================

ws = get_value(engine, "world_state", "ws", "state")

month = get_value(
    ws,
    "month",
    "current_month",
    "month_number",
    default=0,
)

bank_df = clean_object_columns(to_dataframe(get_banks(engine)))
msme_df = clean_object_columns(to_dataframe(get_msmes(engine)))

world_table = find_table(
    DB_PATH,
    ["world_state_log", "WORLD_STATE_LOG"],
)

npa_table = find_table(
    DB_PATH,
    ["npa_log", "NPA_LOG"],
)

decisions_table = find_table(
    DB_PATH,
    ["agent_decisions", "AGENT_DECISIONS"],
)

shap_table = find_table(
    DB_PATH,
    ["shap_log", "SHAP_LOG"],
)

world_log = read_table(DB_PATH, world_table)
npa_log = read_table(DB_PATH, npa_table)
decisions_log = read_table(DB_PATH, decisions_table)
shap_log = read_table(DB_PATH, shap_table)


# ============================================================
# MACROECONOMIC OVERVIEW
# ============================================================

gdp = get_value(
    ws,
    "gdp_growth_pct",
    "gdp_growth",
    "gdp_growth_rate",
)

inflation = get_value(
    ws,
    "cpi_inflation_pct",
    "cpi_inflation",
    "inflation_pct",
    "inflation",
)

repo = get_value(
    ws,
    "rbi_repo_rate_pct",
    "repo_rate_pct",
    "repo_rate",
)

exchange = get_value(
    ws,
    "inr_usd_rate",
    "inr_usd",
    "exchange_rate",
    "usd_inr",
)

if gdp is None:
    gdp = latest_value(
        world_log,
        ["gdp_growth_pct", "gdp_growth", "gdp_growth_rate"],
    )

if inflation is None:
    inflation = latest_value(
        world_log,
        [
            "cpi_inflation_pct",
            "cpi_inflation",
            "inflation_pct",
            "inflation",
            "cpi",
        ],
    )

if repo is None:
    repo = latest_value(
        world_log,
        ["rbi_repo_rate_pct", "repo_rate_pct", "repo_rate"],
    )

if exchange is None:
    exchange = latest_value(
        world_log,
        ["inr_usd", "inr_usd_rate", "exchange_rate", "usd_inr"],
    )

npa = get_value(
    ws,
    "avg_npa_pct",
    "system_npa_pct",
    "npa_ratio_pct",
)

if npa is None:
    npa = calculate_latest_system_npa(npa_log)

if npa is None and not bank_df.empty:
    npa_col = first_existing_column(
        bank_df,
        ["npa_ratio_pct", "npa_ratio", "npa_pct", "npa"],
    )

    if npa_col:
        npa = pd.to_numeric(
            bank_df[npa_col],
            errors="coerce",
        ).mean()

if npa is None:
    npa = 0

st.markdown("### Macroeconomic Overview")

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Simulation Month", str(month))
c2.metric("GDP Growth", fmt(gdp, "%"))
c3.metric("CPI Inflation", fmt(inflation, "%"))
c4.metric("RBI Repo Rate", fmt(repo, "%"))
c5.metric("System NPA", fmt(npa, "%"))
c6.metric(
    "INR / USD",
    f"₹{fmt(exchange)}" if exchange is not None else "N/A",
)

st.divider()


# ============================================================
# ACTIVE SCENARIOS
# ============================================================

active_scenarios = get_active_shocks(engine)

if active_scenarios:
    st.warning(
        "Active stress scenarios: "
        + ", ".join(active_scenarios)
    )
else:
    st.info("No active stress scenarios.")


# ============================================================
# BANKING SECTOR AND MSME TABLES
# ============================================================

left, right = st.columns([1, 1.5], gap="large")

with left:
    st.markdown("### Banking Sector")

    if not bank_df.empty:
        rename_map = {
            "name": "Bank",
            "bank_name": "Bank",
            "entity_id": "Bank ID",
            "npa_ratio": "NPA Ratio (%)",
            "npa_ratio_pct": "NPA Ratio (%)",
            "cash_reserves": "Cash Reserves",
            "loan_book": "Loan Book",
            "loans": "Loans",
            "capital": "Capital",
            "strategy": "Strategy",
            "risk_appetite": "Risk Appetite",
        }

        display_bank = bank_df.rename(
            columns={
                key: value
                for key, value in rename_map.items()
                if key in bank_df.columns
            }
        )

        # Keep the main table concise. Complex loan-book objects are
        # available in the underlying bank data but are not needed here.
        preferred = [
            "Bank",
            "Bank ID",
            "NPA Ratio (%)",
            "Cash Reserves",
            "Capital",
            "Risk Appetite",
        ]

        cols = [
            col for col in preferred
            if col in display_bank.columns
        ]

        if cols:
            display_bank = display_bank[cols]

        show_df(
            display_bank,
            message="No bank records are available.",
            height=280,
        )

    else:
        st.info("No bank records are available.")


with right:
    st.markdown("### MSME Population")

    if not msme_df.empty:
        st.caption(
            f"Total MSMEs in simulation: {len(msme_df)}. "
            "Showing the first 30 records."
        )

        rename_map = {
            "msme_id": "ID",
            "entity_id": "ID",
            "id": "ID",
            "sector": "Sector",
            "region": "Region",
            "cibil_score": "CIBIL Score",
            "credit_score": "CIBIL Score",
            "status": "Status",
            "active_loans": "Active Loans",
        }

        display_msme = msme_df.rename(
            columns={
                key: value
                for key, value in rename_map.items()
                if key in msme_df.columns
            }
        )

        preferred = [
            "ID",
            "Sector",
            "Region",
            "CIBIL Score",
            "Status",
            "Active Loans",
        ]

        cols = [
            col for col in preferred
            if col in display_msme.columns
        ]

        if cols:
            display_msme = display_msme[cols]

        show_df(
            display_msme.head(30),
            message="No MSME records are available.",
            height=440,
        )

    else:
        st.info("No MSME records are available.")


# ============================================================
# MACROECONOMIC TRENDS
# ============================================================

st.divider()
st.markdown("### Macroeconomic Trends")

if not world_log.empty:
    chart_df = world_log.copy()

    month_col = first_existing_column(
        chart_df,
        ["month", "simulation_month", "month_number", "step"],
    )

    if month_col is None:
        chart_df = chart_df.reset_index()
        month_col = "index"

    candidates = [
        "gdp_growth_pct",
        "gdp_growth",
        "cpi_inflation_pct",
        "cpi_inflation",
        "cpi",
        "inflation_pct",
        "rbi_repo_rate_pct",
        "repo_rate_pct",
        "repo_rate",
        "unemployment_rate",
        "exchange_rate",
        "inr_usd",
    ]

    indicators = [
        col for col in candidates
        if col in chart_df.columns
    ]

    if indicators:
        default_indicators = indicators[:3]

        selected = st.multiselect(
            "Select indicators",
            options=indicators,
            default=default_indicators,
            key="macro_indicators",
        )

        if selected:
            melted = chart_df.melt(
                id_vars=[month_col],
                value_vars=selected,
                var_name="Indicator",
                value_name="Value",
            )

            melted["Value"] = pd.to_numeric(
                melted["Value"],
                errors="coerce",
            )

            melted = melted.dropna(subset=["Value"])

            if not melted.empty:
                fig = px.line(
                    melted,
                    x=month_col,
                    y="Value",
                    color="Indicator",
                    markers=True,
                    template="plotly_white",
                )

                fig.update_layout(
                    paper_bgcolor="#F5F7FA",
                    plot_bgcolor="#FFFFFF",
                    font_color="#344054",
                    margin=dict(l=10, r=10, t=20, b=10),
                    legend_title_text="Indicator",
                )

                fig.update_xaxes(gridcolor="#E8ECF1")
                fig.update_yaxes(gridcolor="#E8ECF1")

                st.plotly_chart(
                    fig,
                    width="stretch",
                )

            else:
                st.info("No numeric trend data is available.")

    else:
        st.info(
            "No recognised macroeconomic indicators were found "
            "in the world-state history table."
        )

else:
    st.info(
        "Trend charts will appear when simulation history is available."
    )


# ============================================================
# ANALYSIS TABS
# ============================================================

st.divider()

tab_npa, tab_agents, tab_explanations = st.tabs(
    [
        "Bank NPA Analysis",
        "Agent Decisions",
        "Loan Explanations",
    ]
)


with tab_npa:
    st.markdown("#### Banking-sector asset quality")

    show_df(
        npa_log,
        "NPA history will appear when records are available.",
    )

    if not npa_log.empty:
        month_col = first_existing_column(
            npa_log,
            ["month", "simulation_month", "month_number"],
        )

        npa_col = first_existing_column(
            npa_log,
            [
                "system_npa_pct",
                "npa_ratio_pct",
                "npa_ratio",
                "system_npa",
            ],
        )

        if month_col and npa_col:
            plot_df = npa_log.copy()

            plot_df[npa_col] = pd.to_numeric(
                plot_df[npa_col],
                errors="coerce",
            )

            plot_df = plot_df.dropna(subset=[npa_col])

            if not plot_df.empty:
                # Aggregate bank-level NPA values by month if needed.
                plot_df = (
                    plot_df.groupby(month_col, as_index=False)[npa_col]
                    .mean()
                    .sort_values(month_col)
                )

                fig = px.line(
                    plot_df,
                    x=month_col,
                    y=npa_col,
                    markers=True,
                    template="plotly_white",
                    title="Average Bank NPA Trend",
                )

                fig.update_layout(
                    paper_bgcolor="#F5F7FA",
                    plot_bgcolor="#FFFFFF",
                    font_color="#344054",
                )

                fig.update_xaxes(gridcolor="#E8ECF1")
                fig.update_yaxes(gridcolor="#E8ECF1")

                st.plotly_chart(
                    fig,
                    width="stretch",
                )


with tab_agents:
    st.markdown("#### RBI and bank management decisions")

    show_df(
        decisions_log,
        "Agent decisions will appear here when logged.",
    )


with tab_explanations:
    st.markdown("#### Loan risk explanations")

    show_df(
        shap_log,
        "Loan explanations will appear here when available.",
    )


# ============================================================
# HISTORICAL SIMULATION DATABASE
# ============================================================

with st.expander("Original IMFS Simulation History"):
    history_tables = get_tables(HISTORY_DB_PATH)

    if history_tables:
        history_table = st.selectbox(
            "Choose historical table",
            history_tables,
            key="history_table",
        )

        history_df = read_table(
            HISTORY_DB_PATH,
            history_table,
            limit=500,
        )

        show_df(
            history_df,
            "This historical table is empty.",
        )

    else:
        st.info("No separate historical database was found.")


# ============================================================
# OPTIONAL MARKET SNAPSHOT
# ============================================================

with st.expander("Optional Market Snapshot"):
    st.caption(
        "Fetch a snapshot from the project's market-data module."
    )

    if st.button(
        "Fetch Market Snapshot",
        key="market_snapshot",
    ):
        try:
            from data.market_data import fetch_market_snapshot

            with st.spinner("Fetching market data..."):
                snapshot = fetch_market_snapshot()

            if isinstance(snapshot, pd.DataFrame):
                show_df(
                    snapshot,
                    "No market records were returned.",
                )

            elif isinstance(snapshot, (dict, list)):
                st.json(snapshot)

            elif snapshot is not None:
                st.write(safe_cell(snapshot))

            else:
                st.warning("No market snapshot was returned.")

        except Exception as exc:
            st.error(f"Could not fetch market data: {exc}")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Indian Macro Financial Stress Tester | Educational simulation "
    "for exploring macroeconomic and banking-sector risk. "
    "Outputs are simulated and are not financial advice."
)
