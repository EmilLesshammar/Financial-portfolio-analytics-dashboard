# ============================================================
# 1. IMPORTS
# ============================================================

import hashlib
import html
import io
import json
import re
import tomllib
from pathlib import Path
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from difflib import SequenceMatcher

TROY_OUNCE_GRAMS = 31.1034768

PRECIOUS_METALS = {
    "Gold": {
        "ticker": "XAU",
        "market_symbol": "XAUUSD=X",
    },
    "Silver": {
        "ticker": "XAG",
        "market_symbol": "XAGUSD=X",
    },
    "Platinum": {
        "ticker": "XPT",
        "market_symbol": "XPTUSD=X",
    },
}

import mysql.connector
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf


# ============================================================
# 2. STREAMLIT PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Investment Tracker",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <div class="app-header">
        <div class="app-eyebrow">Investment Tracker</div>
        <div class="app-subtitle">Personal portfolio dashboard</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 2B. DASHBOARD STYLING
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0b0b0b;
    }

    [data-testid="stAppViewContainer"] {
        background: #0b0b0b;
    }

    .main .block-container {
        max-width: 1280px;
        padding-top: 1.1rem;
        padding-bottom: 2rem;
    }

    .app-header {
        margin-bottom: 0.8rem;
    }

    .app-eyebrow {
        color: #f2eee2;
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.15rem;
    }

    .app-subtitle {
        color: rgba(242, 238, 226, 0.72);
        font-size: 0.98rem;
    }

    .portfolio-shell {
        background: #e8e3d7;
        border-radius: 28px;
        padding: 1rem 1.15rem 1.15rem 1.15rem;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 18px 60px rgba(0,0,0,0.25);
        margin-top: 0.8rem;
        margin-bottom: 1.0rem;
    }

    .shell-nav {
        display: inline-flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    .shell-pill {
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
        background: #f5f1e7;
        color: #36332c;
        font-size: 0.83rem;
        font-weight: 600;
        border: 1px solid #ddd5c6;
    }

    .shell-pill.is-active {
        background: #ffffff;
        box-shadow: inset 0 0 0 1px #d8d0c2;
    }

    .hero-total {
        color: #22201c;
        font-size: 2.15rem;
        font-weight: 700;
        line-height: 1.0;
        margin-top: 0.2rem;
    }

    .hero-delta {
        margin-top: 0.25rem;
        color: #8b9b49;
        font-size: 0.95rem;
        font-weight: 600;
    }

    .hero-subline {
        color: #7c7568;
        font-size: 0.85rem;
        margin-left: 0.25rem;
        font-weight: 500;
    }

    .section-title {
        color: #22201c;
        font-size: 1rem;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 0.65rem;
    }

    .account-card {
        background: #f5f1e7;
        border: 1px solid #ddd5c6;
        border-radius: 18px;
        padding: 0.95rem 1.05rem;
        margin-bottom: 0.7rem;
    }

    .account-card-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }

    .account-name {
        color: #27241f;
        font-size: 1rem;
        font-weight: 700;
        line-height: 1.2;
    }

    .account-meta {
        color: #7b7568;
        font-size: 0.83rem;
        margin-top: 0.18rem;
    }

    .account-value {
        color: #27241f;
        font-size: 1.04rem;
        font-weight: 700;
        text-align: right;
        line-height: 1.2;
    }

    .account-subvalue {
        color: #8b9b49;
        font-size: 0.84rem;
        text-align: right;
        margin-top: 0.18rem;
        font-weight: 600;
    }

    .account-breakdown {
        color: #6f6a60;
        font-size: 0.82rem;
        margin-top: 0.6rem;
    }

    /* Keep sidebar dark */
    [data-testid="stSidebar"] {
        background: #111111;
    }

    /* Radio pills for range selector */
    div[data-testid="stRadio"] > div {
        gap: 0.45rem;
        flex-wrap: wrap;
    }

    div[data-testid="stRadio"] label {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 0.35rem 0.85rem;
        transition: background 0.15s ease;
        color: #ece7da;
    }

    div[data-testid="stRadio"] label:hover {
        background: rgba(255,255,255,0.10);
    }

    /* Exposure card */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px;
    }

    div[data-testid="stRadio"] label p {
        font-weight: 600;
    }

    .exposure-title {
        font-size: 1.35rem;
        line-height: 1.2;
        font-weight: 700;
        margin: 0;
    }

    .exposure-updated {
        font-size: 0.78rem;
        color: #a9a9a9;
        text-align: right;
        padding-top: 0.2rem;
    }

    .exposure-list-row {
        margin: 0.72rem 0 0.92rem 0;
    }

    .exposure-list-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.38rem;
    }

    .exposure-list-name {
        font-size: 0.92rem;
        font-weight: 600;
        color: #f5f5f5;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .exposure-list-value {
        font-size: 0.92rem;
        font-weight: 650;
        color: #ffffff;
        white-space: nowrap;
    }

    .exposure-track {
        width: 100%;
        height: 13px;
        border-radius: 999px;
        background: #292929;
        overflow: hidden;
    }

    .exposure-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #cbd4f7 0%, #e8ecff 100%);
    }

    .exposure-dot {
        width: 11px;
        height: 11px;
        border-radius: 50%;
        display: inline-block;
        background: #dce4ff;
        margin-right: 0.45rem;
        vertical-align: -1px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. MYSQL CONNECTION
# ============================================================

def load_mysql_secrets():
    """
    Read MySQL credentials without storing them in Dashboard.py.

    Preferred:
        .streamlit/secrets.toml next to this Dashboard.py

    Streamlit's normal st.secrets is also supported.
    """

    # First try Streamlit's built-in secrets handling.
    try:
        if "mysql" in st.secrets:
            cfg = st.secrets["mysql"]

            return {
                "host": str(
                    cfg.get(
                        "host",
                        "127.0.0.1",
                    )
                ),
                "port": int(
                    cfg.get(
                        "port",
                        3306,
                    )
                ),
                "user": str(
                    cfg["user"]
                ),
                "password": str(
                    cfg["password"]
                ),
                "database": str(
                    cfg.get(
                        "database",
                        "investments",
                    )
                ),
            }
    except Exception:
        pass

    # Fallback: resolve secrets relative to Dashboard.py itself.
    local_secrets_path = (
        Path(__file__).resolve().parent
        / ".streamlit"
        / "secrets.toml"
    )

    if not local_secrets_path.exists():
        raise FileNotFoundError(
            "MySQL credentials were not found. "
            "Create .streamlit/secrets.toml in the same "
            "InvestmentTracker folder as Dashboard.py."
        )

    with local_secrets_path.open(
        "rb"
    ) as secrets_file:
        secrets_data = tomllib.load(
            secrets_file
        )

    if "mysql" not in secrets_data:
        raise KeyError(
            "The secrets file exists but has no [mysql] section."
        )

    cfg = secrets_data["mysql"]

    return {
        "host": str(
            cfg.get(
                "host",
                "127.0.0.1",
            )
        ),
        "port": int(
            cfg.get(
                "port",
                3306,
            )
        ),
        "user": str(
            cfg["user"]
        ),
        "password": str(
            cfg["password"]
        ),
        "database": str(
            cfg.get(
                "database",
                "investments",
            )
        ),
    }


try:
    mysql_config = load_mysql_secrets()

    # Security guardrail: this dashboard is intended to use a local DB only.
    allowed_mysql_hosts = {
        "127.0.0.1",
        "localhost",
        "::1",
    }

    if (
        mysql_config["host"]
        not in allowed_mysql_hosts
    ):
        raise ValueError(
            "For security, this dashboard only allows a local "
            "MySQL host (127.0.0.1 / localhost / ::1)."
        )

    connection = mysql.connector.connect(
        host=mysql_config["host"],
        port=mysql_config["port"],
        user=mysql_config["user"],
        password=mysql_config["password"],
        database=mysql_config["database"],
    )

    cursor = connection.cursor(
        dictionary=True
    )

except Exception as error:
    st.error(
        "Could not connect securely to MySQL. "
        f"{error}"
    )

    st.info(
        "Expected credentials: "
        ".streamlit/secrets.toml next to Dashboard.py. "
        "The dashboard no longer asks for or stores the MySQL "
        "password in the app interface."
    )

    st.stop()


# ============================================================
# 3B. SCHEMA COMPATIBILITY CHECK
# ============================================================

# The application account intentionally has no CREATE / ALTER / DROP
# privileges. Database structure changes should be done manually from
# MySQL Workbench using an administrator account.

try:
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'corporate_actions';
        """
    )

    corporate_action_columns = {
        row["COLUMN_NAME"]
        for row in cursor.fetchall()
    }

    required_columns = {
        "import_batch_id",
        "source",
    }

    missing_columns = (
        required_columns
        - corporate_action_columns
    )

    if missing_columns:
        st.error(
            "The database needs a one-time administrator schema "
            "upgrade before the restricted dashboard account can "
            "be used. Missing corporate_actions column(s): "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )
        st.stop()

    # Keep the old Nordnet import-undo backfill behaviour.
    # UPDATE is allowed for the restricted app user.
    cursor.execute(
        """
        SELECT id, asset_id
        FROM corporate_actions
        WHERE import_batch_id IS NULL
          AND notes LIKE 'Imported from Nordnet:%';
        """
    )

    legacy_nordnet_actions = (
        cursor.fetchall()
    )

    for legacy_action in legacy_nordnet_actions:
        cursor.execute(
            """
            SELECT DISTINCT import_batch_id
            FROM transactions
            WHERE asset_id = %s
              AND source = 'NORDNET'
              AND import_batch_id IS NOT NULL;
            """,
            (
                legacy_action[
                    "asset_id"
                ],
            ),
        )

        candidate_batches = [
            int(
                row[
                    "import_batch_id"
                ]
            )
            for row in cursor.fetchall()
            if row[
                "import_batch_id"
            ] is not None
        ]

        if len(
            candidate_batches
        ) == 1:
            cursor.execute(
                """
                UPDATE corporate_actions
                SET
                    import_batch_id = %s,
                    source = 'NORDNET'
                WHERE id = %s;
                """,
                (
                    candidate_batches[0],
                    legacy_action["id"],
                ),
            )

    connection.commit()

except Exception as error:
    connection.rollback()

    st.error(
        "Could not verify the database schema using the "
        "restricted MySQL account. "
        f"MySQL error: {error}"
    )

    st.stop()


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================


def query_dataframe(sql, params=None):
    """Run a SELECT query and return the result as a DataFrame."""
    cursor.execute(sql, params or ())
    rows = cursor.fetchall()
    return pd.DataFrame(rows)


def validate_position_history(asset_id, account_id):
    """Reject an edit/delete that would make historical shares go negative."""
    if account_id is None:
        account_clause = "account_id IS NULL"
        params = (asset_id,)
    else:
        account_clause = "account_id = %s"
        params = (asset_id, account_id)

    cursor.execute(
        f"""
        SELECT id, transaction_type, quantity, transaction_date
        FROM transactions
        WHERE asset_id = %s
          AND {account_clause}
        ORDER BY transaction_date, id;
        """,
        params,
    )
    tx_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, action_date, action_type, ratio_new, ratio_old
        FROM corporate_actions
        WHERE asset_id = %s
        ORDER BY action_date, id;
        """,
        (asset_id,),
    )
    action_rows = cursor.fetchall()

    events = []

    for action in action_rows:
        if str(action["action_type"]).upper() == "SPLIT":
            events.append(
                (
                    action["action_date"],
                    0,
                    int(action["id"]),
                    "SPLIT",
                    float(action["ratio_new"] or 0),
                    float(action["ratio_old"] or 0),
                )
            )

    for tx in tx_rows:
        events.append(
            (
                tx["transaction_date"],
                1,
                int(tx["id"]),
                str(tx["transaction_type"]).upper(),
                float(tx["quantity"]),
                None,
            )
        )

    events.sort(key=lambda item: (item[0], item[1], item[2]))
    shares = 0.0

    for event_date, _, _, event_type, value_1, value_2 in events:
        if event_type == "SPLIT":
            if value_1 > 0 and value_2 > 0:
                shares *= value_1 / value_2
        elif event_type == "BUY":
            shares += value_1
        elif event_type == "SELL":
            shares -= value_1
            if shares < -1e-9:
                raise ValueError(
                    f"This change would make the position negative on {event_date}. "
                    "Edit/delete the later SELL first, or correct the earlier BUY history."
                )

    return True


def recalculate_import_batch_count(batch_id):
    """Keep import_batches.row_count aligned after manual deletions."""
    if not batch_id:
        return

    total = 0
    for table_name in (
        "transactions",
        "dividends",
        "cash_movements",
        "corporate_actions",
    ):
        cursor.execute(
            f"SELECT COUNT(*) AS n FROM {table_name} WHERE import_batch_id = %s;",
            (batch_id,),
        )
        total += int(cursor.fetchone()["n"] or 0)

    cursor.execute(
        "UPDATE import_batches SET row_count = %s WHERE id = %s;",
        (total, batch_id),
    )


def as_date(value):
    """Convert common date-like values to datetime.date."""
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


def read_broker_csv(file_bytes):
    """Read a broker CSV while trying common Swedish/Windows encodings."""
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    last_error = None

    for encoding in encodings:
        try:
            text = file_bytes.decode(encoding)
            return pd.read_csv(io.StringIO(text), sep=None, engine="python")
        except Exception as error:
            last_error = error

    raise ValueError(f"Could not read CSV file: {last_error}")


def parse_number(value):
    """Parse Swedish or English-formatted numbers."""
    if pd.isna(value):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace("\xa0", "").replace(" ", "")
    text = re.sub(r"[^0-9,\.\-]", "", text)

    if not text:
        return 0.0

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    return float(text)


def normalize_transaction_type(value):
    """Normalize common English/Swedish BUY/SELL labels."""
    value = str(value).strip().upper()

    buy_values = {"BUY", "KÖP", "KOP", "KÖPT"}
    sell_values = {"SELL", "SÄLJ", "SALJ", "SÅLT", "SALT"}

    if value in buy_values:
        return "BUY"
    if value in sell_values:
        return "SELL"
    return None


def make_transaction_hash(
    account_id,
    asset_id,
    transaction_type,
    transaction_date,
    quantity,
    price,
    fees,
    external_id=None,
):
    """Create a stable fingerprint used for duplicate protection."""
    if external_id:
        hash_text = f"{account_id}|EXTERNAL|{external_id}"
    else:
        hash_text = (
            f"{account_id}|{asset_id}|{transaction_type}|{transaction_date}|"
            f"{float(quantity):.8f}|{float(price):.8f}|{float(fees):.8f}"
        )

    return hashlib.sha256(hash_text.encode("utf-8")).hexdigest()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fx_from_yahoo(currency, target_date):
    """Fetch historical FX from Yahoo and return (rate, actual_rate_date)."""
    target_date = as_date(target_date)

    if currency == "SEK":
        return 1.0, target_date

    fx_symbols = {
        "USD": "USDSEK=X",
        "EUR": "EURSEK=X",
        "GBP": "GBPSEK=X",
    }

    if currency not in fx_symbols:
        raise ValueError(f"No FX conversion configured for {currency}.")

    start_date = target_date - timedelta(days=10)
    end_date = target_date + timedelta(days=1)

    fx_data = yf.Ticker(fx_symbols[currency]).history(
        start=start_date,
        end=end_date,
    )

    if fx_data.empty:
        raise ValueError(f"Could not find {currency}/SEK data.")

    fx_data = fx_data[fx_data.index.date <= target_date]

    if fx_data.empty:
        raise ValueError(f"No FX rate available on or before {target_date}.")

    last_row = fx_data.iloc[-1]
    actual_rate_date = fx_data.index[-1].date()
    return float(last_row["Close"]), actual_rate_date


def get_fx_rate_to_sek(currency, target_date):
    """Use recent-enough DB FX first, otherwise fetch and store Yahoo FX."""
    target_date = as_date(target_date)

    if currency == "SEK":
        return 1.0

    cursor.execute(
        """
        SELECT rate_date, sek_per_unit
        FROM fx_rates
        WHERE currency = %s
          AND rate_date <= %s
          AND rate_date >= %s
        ORDER BY rate_date DESC
        LIMIT 1;
        """,
        (currency, target_date, target_date - timedelta(days=10)),
    )
    cached_rate = cursor.fetchone()

    if cached_rate:
        return float(cached_rate["sek_per_unit"])

    fx_rate, actual_rate_date = fetch_fx_from_yahoo(currency, target_date)

    cursor.execute(
        """
        INSERT INTO fx_rates (currency, rate_date, sek_per_unit)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sek_per_unit = VALUES(sek_per_unit);
        """,
        (currency, actual_rate_date, fx_rate),
    )
    connection.commit()
    return fx_rate



def download_yahoo_history(symbol, start_date, end_date=None):
    """
    Download daily Yahoo Finance history with both raw Close and adjusted close.

    Raw Close is used for historical valuation.
    Adjusted Close is stored for return/risk analytics such as beta and Sharpe.
    """
    start_date = as_date(start_date)
    end_date = as_date(end_date or (date.today() + timedelta(days=1)))

    history = yf.Ticker(str(symbol)).history(
        start=start_date,
        end=end_date,
        auto_adjust=False,
        actions=False,
    )

    if history.empty:
        return pd.DataFrame(columns=["price_date", "close_price", "adjusted_close_price"])

    if "Close" not in history.columns:
        return pd.DataFrame(columns=["price_date", "close_price", "adjusted_close_price"])

    history = history.copy()

    # Depending on yfinance/security type, Adj Close may not be returned.
    # In that case we safely fall back to raw Close.
    adjusted_column = "Adj Close" if "Adj Close" in history.columns else "Close"

    output = pd.DataFrame(
        {
            "price_date": [idx.date() for idx in history.index],
            "close_price": pd.to_numeric(history["Close"], errors="coerce").values,
            "adjusted_close_price": pd.to_numeric(
                history[adjusted_column], errors="coerce"
            ).values,
        }
    )

    output = output.dropna(subset=["close_price"])
    output["adjusted_close_price"] = output["adjusted_close_price"].fillna(
        output["close_price"]
    )

    return output




def download_stooq_metal_history(
    market_symbol,
    start_date,
    end_date=None,
):
    """
    Download daily spot precious-metal history from Stooq.

    Stooq symbols:
      XAUUSD = gold spot in USD/troy oz
      XAGUSD = silver spot in USD/troy oz
      XPTUSD = platinum spot in USD/troy oz

    Returns the same column layout as download_yahoo_history().
    """

    start_date = as_date(start_date)
    end_date = as_date(
        end_date
        or date.today()
    )

    symbol = (
        clean_text(market_symbol)
        .upper()
        .replace("=X", "")
        .lower()
    )

    url = (
        "https://stooq.com/q/d/l/"
        f"?s={symbol}"
        f"&d1={start_date.strftime('%Y%m%d')}"
        f"&d2={end_date.strftime('%Y%m%d')}"
        "&i=d"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64)"
            )
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:
            payload = response.read().decode(
                "utf-8",
                errors="replace",
            )
    except Exception as error:
        raise ValueError(
            f"Could not download Stooq spot data "
            f"for {market_symbol}: {error}"
        )

    if (
        not payload.strip()
        or payload.strip().lower()
        in {"no data", "nodata"}
    ):
        return pd.DataFrame(
            columns=[
                "price_date",
                "close_price",
                "adjusted_close_price",
            ]
        )

    try:
        raw = pd.read_csv(
            io.StringIO(payload)
        )
    except Exception as error:
        raise ValueError(
            f"Could not parse Stooq spot data "
            f"for {market_symbol}: {error}"
        )

    required = {"Date", "Close"}

    if not required.issubset(
        set(raw.columns)
    ):
        return pd.DataFrame(
            columns=[
                "price_date",
                "close_price",
                "adjusted_close_price",
            ]
        )

    raw["Date"] = pd.to_datetime(
        raw["Date"],
        errors="coerce",
    )

    raw["Close"] = pd.to_numeric(
        raw["Close"],
        errors="coerce",
    )

    raw = raw.dropna(
        subset=["Date", "Close"]
    )

    if raw.empty:
        return pd.DataFrame(
            columns=[
                "price_date",
                "close_price",
                "adjusted_close_price",
            ]
        )

    output = pd.DataFrame(
        {
            "price_date": raw["Date"].dt.date,
            "close_price": raw["Close"],
            "adjusted_close_price": raw["Close"],
        }
    )

    return (
        output
        .sort_values("price_date")
        .drop_duplicates(
            subset=["price_date"],
            keep="last",
        )
        .reset_index(drop=True)
    )


def convert_metal_history_to_sek_per_gram(
    history_df,
    start_date,
    end_date=None,
):
    """
    Convert Yahoo precious-metal quotes from USD/troy ounce to SEK/gram.

    The stored price then matches how physical metal is entered in the
    portfolio:
        quantity = grams
        transaction price = SEK per gram
        market price = SEK per gram
    """

    if history_df.empty:
        return history_df

    start_date = as_date(start_date)
    end_date = as_date(
        end_date
        or (date.today() + timedelta(days=1))
    )

    fx_history = yf.Ticker("USDSEK=X").history(
        start=start_date - timedelta(days=10),
        end=end_date,
        auto_adjust=False,
        actions=False,
    )

    if (
        fx_history.empty
        or "Close" not in fx_history.columns
    ):
        raise ValueError(
            "Could not download historical USD/SEK "
            "needed to value precious metals."
        )

    fx_frame = pd.DataFrame(
        {
            "price_date": [
                idx.date()
                for idx in fx_history.index
            ],
            "usdsek": pd.to_numeric(
                fx_history["Close"],
                errors="coerce",
            ).values,
        }
    ).dropna(subset=["usdsek"])

    metal = history_df.copy()

    metal["price_date"] = pd.to_datetime(
        metal["price_date"],
        errors="coerce",
    )

    fx_frame["price_date"] = pd.to_datetime(
        fx_frame["price_date"],
        errors="coerce",
    )

    metal = pd.merge_asof(
        metal.sort_values("price_date"),
        fx_frame.sort_values("price_date"),
        on="price_date",
        direction="backward",
    )

    if metal["usdsek"].isna().all():
        raise ValueError(
            "No matching USD/SEK history was found "
            "for the precious-metal prices."
        )

    metal["usdsek"] = metal["usdsek"].ffill()

    metal["close_price"] = (
        pd.to_numeric(
            metal["close_price"],
            errors="coerce",
        )
        * metal["usdsek"]
        / TROY_OUNCE_GRAMS
    )

    metal["adjusted_close_price"] = (
        pd.to_numeric(
            metal["adjusted_close_price"],
            errors="coerce",
        )
        * metal["usdsek"]
        / TROY_OUNCE_GRAMS
    )

    metal["price_date"] = (
        metal["price_date"].dt.date
    )

    return metal[
        [
            "price_date",
            "close_price",
            "adjusted_close_price",
        ]
    ].dropna(subset=["close_price"])



def fetch_metal_sek_per_ounce_from_exchange_api(
    metal_code,
):
    """
    Fetch the latest XAU/XAG/XPT -> SEK rate from the free
    fawazahmed0 exchange API.

    ISO precious-metal codes represent one troy ounce, so the
    returned SEK rate is SEK per troy ounce.
    """

    metal_code = clean_text(
        metal_code
    ).lower()

    if metal_code not in {
        "xau",
        "xag",
        "xpt",
    }:
        raise ValueError(
            f"Unsupported metal code: {metal_code}"
        )

    urls = [
        (
            "https://cdn.jsdelivr.net/npm/"
            "@fawazahmed0/currency-api@latest/"
            f"v1/currencies/{metal_code}.json"
        ),
        (
            "https://latest.currency-api.pages.dev/"
            f"v1/currencies/{metal_code}.json"
        ),
    ]

    last_error = None

    for url in urls:
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64)"
                    )
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=20,
            ) as response:
                payload = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            rates = payload.get(
                metal_code,
                {}
            )

            sek_per_ounce = pd.to_numeric(
                rates.get("sek"),
                errors="coerce",
            )

            if pd.isna(sek_per_ounce):
                raise ValueError(
                    "SEK rate missing from response."
                )

            api_date = pd.to_datetime(
                payload.get("date"),
                errors="coerce",
            )

            rate_date = (
                api_date.date()
                if pd.notna(api_date)
                else date.today()
            )

            return (
                float(sek_per_ounce),
                rate_date,
            )

        except Exception as error:
            last_error = error

    raise ValueError(
        "Could not fetch spot metal/SEK rate "
        f"for {metal_code.upper()}: "
        f"{last_error}"
    )



def metal_code_from_symbol(
    market_symbol,
):
    symbol = clean_text(
        market_symbol
    ).upper()

    if symbol.startswith("XAU"):
        return "xau"

    if symbol.startswith("XAG"):
        return "xag"

    if symbol.startswith("XPT"):
        return "xpt"

    raise ValueError(
        f"Unknown precious-metal symbol: "
        f"{market_symbol}"
    )


def fetch_historical_metal_sek_for_date(
    metal_code,
    requested_date,
):
    """
    Fetch one historical metal/SEK observation.

    The exchange API supports YYYY-MM-DD snapshots.
    One XAU/XAG/XPT represents one troy ounce, so the returned
    SEK rate is SEK per troy ounce.
    """

    requested_date = as_date(
        requested_date
    )

    date_text = requested_date.isoformat()

    urls = [
        (
            "https://cdn.jsdelivr.net/npm/"
            "@fawazahmed0/currency-api@"
            f"{date_text}/v1/currencies/"
            f"{metal_code}.min.json"
        ),
        (
            f"https://{date_text}."
            "currency-api.pages.dev/v1/"
            f"currencies/{metal_code}.min.json"
        ),
    ]

    for url in urls:
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64)"
                    )
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=12,
            ) as response:
                payload = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            rates = payload.get(
                metal_code,
                {}
            )

            sek_per_ounce = pd.to_numeric(
                rates.get("sek"),
                errors="coerce",
            )

            if pd.notna(
                sek_per_ounce
            ):
                return {
                    "price_date": requested_date,
                    "close_price": (
                        float(sek_per_ounce)
                        / TROY_OUNCE_GRAMS
                    ),
                    "adjusted_close_price": (
                        float(sek_per_ounce)
                        / TROY_OUNCE_GRAMS
                    ),
                }

        except Exception:
            continue

    return None


def download_historical_metal_sek_per_gram(
    market_symbol,
    start_date,
    end_date=None,
):
    """
    Download historical spot metal values directly in SEK/gram.

    This deliberately avoids:
      - COMEX futures
      - Yahoo XAUUSD history
      - a separate historical USD/SEK conversion

    Historical snapshots from this API are available from
    2024-03-02 onward, so older requests are clamped to that date.
    """

    start_date = as_date(
        start_date
    )

    end_date = as_date(
        end_date
        or date.today()
    )

    earliest_supported = date(
        2024,
        3,
        2,
    )

    start_date = max(
        start_date,
        earliest_supported,
    )

    if end_date < start_date:
        return pd.DataFrame(
            columns=[
                "price_date",
                "close_price",
                "adjusted_close_price",
            ]
        )

    metal_code = metal_code_from_symbol(
        market_symbol
    )

    # Portfolio analytics are based on trading days. Request weekdays
    # only; unavailable holiday dates are simply skipped.
    requested_dates = [
        timestamp.date()
        for timestamp in pd.date_range(
            start=start_date,
            end=end_date,
            freq="B",
        )
    ]

    if not requested_dates:
        return pd.DataFrame(
            columns=[
                "price_date",
                "close_price",
                "adjusted_close_price",
            ]
        )

    rows = []

    # The API documents no rate limit. A small worker pool keeps a
    # multi-year backfill practical without flooding the service.
    with ThreadPoolExecutor(
        max_workers=10
    ) as executor:
        futures = {
            executor.submit(
                fetch_historical_metal_sek_for_date,
                metal_code,
                requested_date,
            ): requested_date
            for requested_date
            in requested_dates
        }

        for future in as_completed(
            futures
        ):
            try:
                result = future.result()
            except Exception:
                result = None

            if result is not None:
                rows.append(
                    result
                )

    if not rows:
        return pd.DataFrame(
            columns=[
                "price_date",
                "close_price",
                "adjusted_close_price",
            ]
        )

    output = pd.DataFrame(
        rows
    )

    output["price_date"] = pd.to_datetime(
        output["price_date"],
        errors="coerce",
    ).dt.date

    for column in [
        "close_price",
        "adjusted_close_price",
    ]:
        output[column] = pd.to_numeric(
            output[column],
            errors="coerce",
        )

    return (
        output
        .dropna(
            subset=[
                "price_date",
                "close_price",
            ]
        )
        .sort_values(
            "price_date"
        )
        .drop_duplicates(
            subset=["price_date"],
            keep="last",
        )
        .reset_index(drop=True)
    )


def current_metal_price_sek_per_gram(
    market_symbol,
):
    """
    Return latest spot precious-metal value in SEK per gram.

    Current valuation does NOT use futures and does NOT need a
    separate USD/SEK conversion.

    It requests the metal directly in SEK:
        XAU/SEK, XAG/SEK or XPT/SEK

    Then:
        SEK/gram =
            SEK/troy ounce
            ÷ 31.1034768
    """

    metal_code = metal_code_from_symbol(
        market_symbol
    )

    sek_per_ounce, rate_date = (
        fetch_metal_sek_per_ounce_from_exchange_api(
            metal_code
        )
    )

    sek_per_gram = (
        float(sek_per_ounce)
        / TROY_OUNCE_GRAMS
    )

    return (
        sek_per_gram,
        rate_date,
    )


def ensure_spot_metal_symbols():
    """
    Automatically migrate existing Gold/Silver/Platinum assets from
    futures symbols to spot metal/USD symbols.
    """

    cursor.execute(
        """
        SELECT id, name, ticker, asset_type, market_symbol
        FROM assets
        WHERE UPPER(COALESCE(asset_type, '')) = 'METAL';
        """
    )

    metal_rows = cursor.fetchall()
    changed = False

    for row in metal_rows:
        asset_name = clean_text(row.get("name"))
        ticker = clean_text(row.get("ticker")).upper()

        matched_definition = None

        for metal_name, definition in PRECIOUS_METALS.items():
            if (
                asset_name.upper() == metal_name.upper()
                or ticker == definition["ticker"].upper()
            ):
                matched_definition = definition
                break

        if matched_definition is None:
            continue

        desired_symbol = matched_definition["market_symbol"]

        if clean_text(row.get("market_symbol")).upper() != desired_symbol.upper():
            cursor.execute(
                """
                UPDATE assets
                SET market_symbol = %s,
                    currency = 'SEK',
                    sector = 'Precious Metals',
                    country = 'Global / Commodity'
                WHERE id = %s;
                """,
                (
                    desired_symbol,
                    int(row["id"]),
                ),
            )
            changed = True

    if changed:
        connection.commit()


def historical_data_start_date():
    """Return the earliest date needed for portfolio history."""
    candidate_dates = []

    cursor.execute("SELECT MIN(transaction_date) AS d FROM transactions;")
    row = cursor.fetchone()
    if row and row["d"]:
        candidate_dates.append(as_date(row["d"]))

    cursor.execute("SELECT MIN(movement_date) AS d FROM cash_movements;")
    row = cursor.fetchone()
    if row and row["d"]:
        candidate_dates.append(as_date(row["d"]))

    cursor.execute("SELECT MIN(action_date) AS d FROM corporate_actions;")
    row = cursor.fetchone()
    if row and row["d"]:
        candidate_dates.append(as_date(row["d"]))

    return min(candidate_dates) if candidate_dates else None


def historical_schema_status():
    """Check that the SQL structures needed for historical analytics exist."""
    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'prices'
          AND COLUMN_NAME = 'adjusted_close_price';
        """
    )
    has_adjusted_close = int(cursor.fetchone()["n"] or 0) == 1

    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'benchmarks';
        """
    )
    has_benchmarks = int(cursor.fetchone()["n"] or 0) == 1

    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'benchmark_prices';
        """
    )
    has_benchmark_prices = int(cursor.fetchone()["n"] or 0) == 1

    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'risk_free_rates';
        """
    )
    has_risk_free = int(cursor.fetchone()["n"] or 0) == 1

    return {
        "adjusted_close_price": has_adjusted_close,
        "benchmarks": has_benchmarks,
        "benchmark_prices": has_benchmark_prices,
        "risk_free_rates": has_risk_free,
    }


def upsert_asset_history(asset_id, currency, history_df):
    """Insert/update one asset's daily price history."""
    if history_df.empty:
        return 0

    rows = [
        (
            int(asset_id),
            row["price_date"],
            float(row["close_price"]),
            float(row["adjusted_close_price"]),
            str(currency),
        )
        for _, row in history_df.iterrows()
        if pd.notna(row["close_price"])
    ]

    if not rows:
        return 0

    cursor.executemany(
        """
        INSERT INTO prices (
            asset_id,
            price_date,
            close_price,
            adjusted_close_price,
            currency
        )
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            close_price = VALUES(close_price),
            adjusted_close_price = VALUES(adjusted_close_price),
            currency = VALUES(currency);
        """,
        rows,
    )

    return len(rows)


def upsert_fx_history(currency, start_date, end_date=None):
    """Download and store daily historical FX to SEK."""
    currency = normalize_currency(currency)
    start_date = as_date(start_date)
    end_date = as_date(end_date or (date.today() + timedelta(days=1)))

    if currency == "SEK":
        # One SEK row per calendar day is unnecessary. A daily series is useful,
        # however, when we later align analytics, so store business/calendar dates
        # from start through today at exactly 1.
        days = pd.date_range(start_date, end_date - timedelta(days=1), freq="D")
        rows = [("SEK", d.date(), 1.0) for d in days]
    else:
        fx_symbols = {
            "USD": "USDSEK=X",
            "EUR": "EURSEK=X",
            "GBP": "GBPSEK=X",
        }

        symbol = fx_symbols.get(currency)
        if not symbol:
            raise ValueError(f"No historical FX symbol configured for {currency}.")

        history = yf.Ticker(symbol).history(
            start=start_date,
            end=end_date,
            auto_adjust=False,
            actions=False,
        )

        if history.empty or "Close" not in history.columns:
            raise ValueError(f"No historical {currency}/SEK data returned by Yahoo.")

        close = pd.to_numeric(history["Close"], errors="coerce")
        rows = [
            (currency, idx.date(), float(value))
            for idx, value in close.items()
            if pd.notna(value)
        ]

    if not rows:
        return 0

    cursor.executemany(
        """
        INSERT INTO fx_rates (
            currency,
            rate_date,
            sek_per_unit
        )
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sek_per_unit = VALUES(sek_per_unit);
        """,
        rows,
    )

    return len(rows)


def upsert_benchmark_history(benchmark_id, symbol, start_date, end_date=None):
    """Download/store daily benchmark prices."""
    history = download_yahoo_history(symbol, start_date, end_date)

    if history.empty:
        return 0

    rows = [
        (
            int(benchmark_id),
            row["price_date"],
            float(row["close_price"]),
            float(row["adjusted_close_price"]),
        )
        for _, row in history.iterrows()
        if pd.notna(row["close_price"])
    ]

    cursor.executemany(
        """
        INSERT INTO benchmark_prices (
            benchmark_id,
            price_date,
            close_price,
            adjusted_close_price
        )
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            close_price = VALUES(close_price),
            adjusted_close_price = VALUES(adjusted_close_price);
        """,
        rows,
    )

    return len(rows)



def upsert_risk_free_history(start_date, end_date=None):
    """
    Download the Swedish 3-month Treasury bill benchmark from Sveriges Riksbank.

    Series: SETB3MBENCH
    Stored as an annual decimal:
        2.50 percent -> 0.025
    """
    start_date = as_date(start_date)
    end_date = as_date(end_date or date.today())

    url = (
        "https://api.riksbank.se/swea/v1/Observations/"
        f"SETB3MBENCH/{start_date:%Y-%m-%d}/{end_date:%Y-%m-%d}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "InvestmentTracker/1.0",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            status_code = getattr(response, "status", 200)

            if status_code == 204:
                return 0

            payload = response.read().decode("utf-8")
            observations = json.loads(payload)

    except urllib.error.HTTPError as error:
        if error.code == 204:
            return 0
        raise ValueError(
            f"Riksbank API returned HTTP {error.code}."
        ) from error

    except urllib.error.URLError as error:
        raise ValueError(
            f"Could not connect to Sveriges Riksbank: {error.reason}"
        ) from error

    if isinstance(observations, dict):
        # Defensive handling in case the API wraps the list.
        observations = (
            observations.get("observations")
            or observations.get("data")
            or []
        )

    rows = []

    for observation in observations:
        obs_date = observation.get("date")
        value = observation.get("value")

        if obs_date is None or value is None:
            continue

        try:
            annual_decimal = float(value) / 100.0
        except (TypeError, ValueError):
            continue

        rows.append(
            (
                as_date(obs_date),
                annual_decimal,
                "Sveriges Riksbank - Swedish Treasury Bill 3M (SETB3MBENCH)",
            )
        )

    if not rows:
        return 0

    cursor.executemany(
        """
        INSERT INTO risk_free_rates (
            rate_date,
            annual_rate_decimal,
            source
        )
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            annual_rate_decimal = VALUES(annual_rate_decimal),
            source = VALUES(source);
        """,
        rows,
    )

    return len(rows)


def build_portfolio_history_series(transactions_df, cash_df, assets_df):
    """
    Build a daily SEK portfolio-value history.

    The series includes:
      - security market value
      - cash balances
      - stock splits from corporate_actions

    It also returns EXTERNAL cash flows (DEPOSIT/WITHDRAWAL) separately.
    Those flows are removed when calculating investment returns so that
    adding money does not look like investment performance.
    """

    price_history = query_dataframe(
        """
        SELECT
            asset_id,
            price_date,
            close_price,
            adjusted_close_price
        FROM prices
        ORDER BY asset_id, price_date;
        """
    )

    fx_history = query_dataframe(
        """
        SELECT
            currency,
            rate_date,
            sek_per_unit
        FROM fx_rates
        ORDER BY currency, rate_date;
        """
    )

    split_history = query_dataframe(
        """
        SELECT
            asset_id,
            action_date,
            ratio_new,
            ratio_old
        FROM corporate_actions
        WHERE UPPER(action_type) = 'SPLIT'
        ORDER BY asset_id, action_date, id;
        """
    )

    candidate_dates = []

    if not transactions_df.empty:
        dates = pd.to_datetime(
            transactions_df["transaction_date"],
            errors="coerce",
        ).dropna()
        if not dates.empty:
            candidate_dates.append(dates.min())

    if not cash_df.empty:
        dates = pd.to_datetime(
            cash_df["movement_date"],
            errors="coerce",
        ).dropna()
        if not dates.empty:
            candidate_dates.append(dates.min())

    if not price_history.empty:
        dates = pd.to_datetime(
            price_history["price_date"],
            errors="coerce",
        ).dropna()
        if not dates.empty:
            candidate_dates.append(dates.min())

    if not candidate_dates:
        return pd.DataFrame(
            columns=[
                "date",
                "security_value_sek",
                "cash_value_sek",
                "total_value_sek",
                "external_flow_sek",
            ]
        )

    start_date = min(candidate_dates).normalize()
    end_date = pd.Timestamp.today().normalize()

    calendar = pd.DataFrame(
        {"date": pd.date_range(start_date, end_date, freq="D")}
    )

    result = calendar.copy()
    result["security_value_sek"] = 0.0
    result["cash_value_sek"] = 0.0
    result["external_flow_sek"] = 0.0

    # --------------------------------------------------------
    # Prepare FX histories
    # --------------------------------------------------------

    fx = fx_history.copy()

    if not fx.empty:
        fx["rate_date"] = pd.to_datetime(
            fx["rate_date"],
            errors="coerce",
        ).dt.normalize()
        fx["currency"] = (
            fx["currency"]
            .fillna("SEK")
            .astype(str)
            .str.upper()
        )
        fx["sek_per_unit"] = pd.to_numeric(
            fx["sek_per_unit"],
            errors="coerce",
        )

    def daily_fx_series(currency):
        currency = normalize_currency(currency)

        if currency == "SEK":
            return pd.Series(
                1.0,
                index=result.index,
                dtype=float,
            )

        currency_fx = fx[fx["currency"] == currency].copy()

        if currency_fx.empty:
            return pd.Series(
                float("nan"),
                index=result.index,
                dtype=float,
            )

        currency_fx = (
            currency_fx
            .groupby("rate_date", as_index=False)["sek_per_unit"]
            .last()
            .rename(columns={"rate_date": "date"})
        )

        merged = calendar.merge(
            currency_fx,
            on="date",
            how="left",
        )

        return merged["sek_per_unit"].ffill()

    asset_meta = assets_df[
        ["id", "name", "currency"]
    ].copy()

    asset_meta["currency"] = (
        asset_meta["currency"]
        .fillna("SEK")
        .astype(str)
        .str.upper()
    )

    # --------------------------------------------------------
    # Security values
    # --------------------------------------------------------

    if not transactions_df.empty and not price_history.empty:
        tx = transactions_df.copy()

        tx["transaction_date"] = pd.to_datetime(
            tx["transaction_date"],
            errors="coerce",
        ).dt.normalize()

        tx["quantity"] = pd.to_numeric(
            tx["quantity"],
            errors="coerce",
        ).fillna(0.0)

        tx["transaction_type"] = (
            tx["transaction_type"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        tx = tx[
            tx["transaction_type"].isin(["BUY", "SELL"])
        ].copy()

        tx["signed_quantity"] = tx["quantity"]

        tx.loc[
            tx["transaction_type"] == "SELL",
            "signed_quantity",
        ] *= -1

        prices = price_history.copy()

        prices["price_date"] = pd.to_datetime(
            prices["price_date"],
            errors="coerce",
        ).dt.normalize()

        prices["close_price"] = pd.to_numeric(
            prices["close_price"],
            errors="coerce",
        )

        splits = split_history.copy()

        if not splits.empty:
            splits["action_date"] = pd.to_datetime(
                splits["action_date"],
                errors="coerce",
            ).dt.normalize()

            splits["ratio_new"] = pd.to_numeric(
                splits["ratio_new"],
                errors="coerce",
            )

            splits["ratio_old"] = pd.to_numeric(
                splits["ratio_old"],
                errors="coerce",
            )

        for asset_id in tx["asset_id"].dropna().unique():
            asset_tx = tx[
                tx["asset_id"] == asset_id
            ].copy()

            if asset_tx.empty:
                continue

            asset_prices = prices[
                prices["asset_id"] == asset_id
            ].copy()

            if asset_prices.empty:
                continue

            daily_trade_qty = (
                asset_tx
                .groupby("transaction_date")["signed_quantity"]
                .sum()
                .to_dict()
            )

            split_by_date = {}

            if not splits.empty:
                asset_splits = splits[
                    splits["asset_id"] == asset_id
                ].copy()

                for _, split in asset_splits.iterrows():
                    ratio_old = float(split["ratio_old"] or 0)
                    ratio_new = float(split["ratio_new"] or 0)

                    if ratio_old <= 0 or ratio_new <= 0:
                        continue

                    split_date = split["action_date"]

                    split_by_date.setdefault(
                        split_date,
                        [],
                    ).append(
                        ratio_new / ratio_old
                    )

            shares = 0.0
            shares_values = []

            for current_date in calendar["date"]:
                # Splits are applied before transactions on the effective date.
                for factor in split_by_date.get(
                    current_date,
                    [],
                ):
                    shares *= factor

                shares += float(
                    daily_trade_qty.get(
                        current_date,
                        0.0,
                    )
                )

                shares_values.append(shares)

            shares_series = pd.Series(
                shares_values,
                index=result.index,
                dtype=float,
            )

            asset_prices = (
                asset_prices
                .groupby("price_date", as_index=False)["close_price"]
                .last()
                .rename(columns={"price_date": "date"})
            )

            price_series = calendar.merge(
                asset_prices,
                on="date",
                how="left",
            )["close_price"].ffill()

            currency_match = asset_meta.loc[
                asset_meta["id"] == asset_id,
                "currency",
            ]

            currency = (
                currency_match.iloc[0]
                if not currency_match.empty
                else "SEK"
            )

            fx_series = daily_fx_series(currency)

            asset_value = (
                shares_series
                * price_series
                * fx_series
            )

            result["security_value_sek"] += (
                asset_value.fillna(0.0)
            )

    # --------------------------------------------------------
    # Cash balances + external cash flows
    # --------------------------------------------------------

    if not cash_df.empty:
        cash = cash_df.copy()

        cash["movement_date"] = pd.to_datetime(
            cash["movement_date"],
            errors="coerce",
        ).dt.normalize()

        cash["amount"] = pd.to_numeric(
            cash["amount"],
            errors="coerce",
        ).fillna(0.0)

        cash["fx_rate_to_sek"] = pd.to_numeric(
            cash["fx_rate_to_sek"],
            errors="coerce",
        )

        cash["currency"] = (
            cash["currency"]
            .fillna("SEK")
            .astype(str)
            .str.upper()
        )

        cash["movement_type"] = (
            cash["movement_type"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
        )

        for currency in cash["currency"].dropna().unique():
            currency_cash = cash[
                cash["currency"] == currency
            ].copy()

            daily_amount = (
                currency_cash
                .groupby("movement_date")["amount"]
                .sum()
                .rename("amount")
                .reset_index()
                .rename(columns={"movement_date": "date"})
            )

            cash_series = calendar.merge(
                daily_amount,
                on="date",
                how="left",
            )

            cash_series["amount"] = (
                cash_series["amount"]
                .fillna(0.0)
            )

            cash_series["cash_balance"] = (
                cash_series["amount"]
                .cumsum()
            )

            fx_series = daily_fx_series(currency)

            result["cash_value_sek"] += (
                cash_series["cash_balance"]
                * fx_series
            ).fillna(0.0)

        external = cash[
            cash["movement_type"].isin(
                ["DEPOSIT", "WITHDRAWAL"]
            )
        ].copy()

        if not external.empty:
            external["flow_sek"] = external.apply(
                lambda row: (
                    float(row["amount"])
                    if normalize_currency(row["currency"]) == "SEK"
                    else float(row["amount"])
                    * (
                        float(row["fx_rate_to_sek"])
                        if pd.notna(row["fx_rate_to_sek"])
                        else 0.0
                    )
                ),
                axis=1,
            )

            external_daily = (
                external
                .groupby("movement_date")["flow_sek"]
                .sum()
                .rename("external_flow_sek")
                .reset_index()
                .rename(columns={"movement_date": "date"})
            )

            result = result.drop(
                columns=["external_flow_sek"]
            ).merge(
                external_daily,
                on="date",
                how="left",
            )

            result["external_flow_sek"] = (
                result["external_flow_sek"]
                .fillna(0.0)
            )

    result["total_value_sek"] = (
        result["security_value_sek"]
        + result["cash_value_sek"]
    )

    return result


def build_benchmark_series(symbol="ACWI"):
    """Build one stored benchmark series in SEK."""

    benchmark = query_dataframe(
        """
        SELECT
            b.id AS benchmark_id,
            b.symbol,
            b.name,
            b.currency,
            bp.price_date,
            bp.adjusted_close_price,
            bp.close_price
        FROM benchmarks b
        JOIN benchmark_prices bp
          ON bp.benchmark_id = b.id
        WHERE b.symbol = %s
        ORDER BY bp.price_date;
        """,
        (symbol,),
    )

    if benchmark.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "benchmark_value_sek",
                "benchmark_return",
            ]
        )

    benchmark["date"] = pd.to_datetime(
        benchmark["price_date"],
        errors="coerce",
    ).dt.normalize()

    benchmark["adjusted_close_price"] = pd.to_numeric(
        benchmark["adjusted_close_price"],
        errors="coerce",
    )

    benchmark["close_price"] = pd.to_numeric(
        benchmark["close_price"],
        errors="coerce",
    )

    benchmark["benchmark_price"] = (
        benchmark["adjusted_close_price"]
        .fillna(benchmark["close_price"])
    )

    currency = normalize_currency(
        benchmark.iloc[0]["currency"]
    )

    if currency == "SEK":
        benchmark["fx"] = 1.0

    else:
        fx_history = query_dataframe(
            """
            SELECT
                rate_date,
                sek_per_unit
            FROM fx_rates
            WHERE currency = %s
            ORDER BY rate_date;
            """,
            (currency,),
        )

        if fx_history.empty:
            return pd.DataFrame(
                columns=[
                    "date",
                    "benchmark_value_sek",
                    "benchmark_return",
                ]
            )

        fx_history["date"] = pd.to_datetime(
            fx_history["rate_date"],
            errors="coerce",
        ).dt.normalize()

        fx_history["sek_per_unit"] = pd.to_numeric(
            fx_history["sek_per_unit"],
            errors="coerce",
        )

        benchmark = pd.merge_asof(
            benchmark.sort_values("date"),
            fx_history[
                ["date", "sek_per_unit"]
            ].sort_values("date"),
            on="date",
            direction="backward",
        )

        benchmark["fx"] = benchmark[
            "sek_per_unit"
        ]

    benchmark["benchmark_value_sek"] = (
        benchmark["benchmark_price"]
        * benchmark["fx"]
    )

    benchmark["benchmark_return"] = (
        benchmark["benchmark_value_sek"]
        .pct_change()
    )

    return benchmark[
        [
            "date",
            "benchmark_value_sek",
            "benchmark_return",
        ]
    ].dropna(
        subset=["date", "benchmark_value_sek"]
    )



def ensure_default_benchmarks():
    """
    Make sure the three benchmark definitions used by the dashboard exist.

    ACWI is kept for beta/risk analytics.
    ^GSPC is the S&P 500 price index.
    ^OMXSPI is OMX Stockholm PI.
    """
    schema_state = historical_schema_status()

    if not schema_state.get("benchmarks", False):
        return

    benchmark_definitions = [
        ("ACWI", "iShares MSCI ACWI ETF", "USD"),
        ("^GSPC", "S&P 500", "USD"),
        ("^OMXSPI", "OMX Stockholm PI", "SEK"),
    ]

    cursor.executemany(
        """
        INSERT INTO benchmarks (
            symbol,
            name,
            currency
        )
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            currency = VALUES(currency);
        """,
        benchmark_definitions,
    )

    connection.commit()


def filter_return_period(df, lookback):
    if df.empty:
        return df

    output = df.copy()

    output["date"] = pd.to_datetime(
        output["date"],
        errors="coerce",
    ).dt.normalize()

    output = output.dropna(subset=["date"])

    if output.empty or lookback == "ALL":
        return output

    end_date = output["date"].max()

    if lookback == "1Y":
        start_date = end_date - pd.DateOffset(years=1)
    elif lookback == "3Y":
        start_date = end_date - pd.DateOffset(years=3)
    elif lookback == "5Y":
        start_date = end_date - pd.DateOffset(years=5)
    else:
        return output

    return output[
        output["date"] >= start_date
    ].copy()


def normalized_return_index(
    returns_df,
    return_column,
    name,
    lookback,
):
    """Turn a daily return series into a growth-of-100 index."""

    if returns_df.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "Series",
                "Growth of 100",
            ]
        )

    data = returns_df[
        ["date", return_column]
    ].copy()

    data = filter_return_period(
        data,
        lookback,
    )

    data[return_column] = pd.to_numeric(
        data[return_column],
        errors="coerce",
    )

    data = data.dropna(
        subset=[return_column]
    )

    data = data[
        data[return_column].between(
            -0.95,
            5.0,
            inclusive="both",
        )
    ].copy()

    if data.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "Series",
                "Growth of 100",
            ]
        )

    growth = (
        1.0 + data[return_column]
    ).cumprod()

    if growth.empty or growth.iloc[0] == 0:
        return pd.DataFrame(
            columns=[
                "date",
                "Series",
                "Growth of 100",
            ]
        )

    data["Growth of 100"] = (
        growth / growth.iloc[0] * 100.0
    )

    data["Series"] = name

    return data[
        [
            "date",
            "Series",
            "Growth of 100",
        ]
    ]


def build_benchmark_comparison(
    portfolio_return_history,
    lookback,
):
    """
    Build normalized performance series for:
      - Your Portfolio
      - S&P 500 (^GSPC), converted to SEK
      - OMX Stockholm PI (^OMXSPI)
      - ACWI, converted to SEK
    """

    comparison_frames = []

    portfolio_index = normalized_return_index(
        portfolio_return_history,
        "portfolio_return",
        "Your Portfolio",
        lookback,
    )

    if not portfolio_index.empty:
        comparison_frames.append(
            portfolio_index
        )

    benchmark_specs = [
        ("^GSPC", "S&P 500"),
        ("^OMXSPI", "OMXSPI"),
        ("ACWI", "ACWI"),
    ]

    for symbol, display_name in benchmark_specs:

        benchmark = build_benchmark_series(
            symbol=symbol
        )

        if benchmark.empty:
            continue

        benchmark_index = normalized_return_index(
            benchmark,
            "benchmark_return",
            display_name,
            lookback,
        )

        if not benchmark_index.empty:
            comparison_frames.append(
                benchmark_index
            )

    if not comparison_frames:
        return pd.DataFrame(
            columns=[
                "date",
                "Series",
                "Growth of 100",
            ]
        )

    return pd.concat(
        comparison_frames,
        ignore_index=True,
    )


def build_risk_free_daily_series():
    """Convert annual Swedish 3M Treasury-bill yields into daily rates."""

    rf = query_dataframe(
        """
        SELECT
            rate_date,
            annual_rate_decimal,
            source
        FROM risk_free_rates
        ORDER BY rate_date;
        """
    )

    if rf.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "annual_rate_decimal",
                "daily_rf",
            ]
        )

    rf["date"] = pd.to_datetime(
        rf["rate_date"],
        errors="coerce",
    ).dt.normalize()

    rf["annual_rate_decimal"] = pd.to_numeric(
        rf["annual_rate_decimal"],
        errors="coerce",
    )

    rf = rf.dropna(
        subset=["date", "annual_rate_decimal"]
    )

    rf["daily_rf"] = rf[
        "annual_rate_decimal"
    ].apply(
        lambda annual: (
            (1.0 + float(annual)) ** (1.0 / 252.0) - 1.0
            if float(annual) > -1.0
            else float("nan")
        )
    )

    return rf[
        [
            "date",
            "annual_rate_decimal",
            "daily_rf",
        ]
    ]



def build_invested_portfolio_return_series(
    transactions_df,
    assets_df,
    benchmark_history,
):
    """
    Build a daily INVESTMENT return series that is independent of cash flows.

    This is the series used for Sharpe, beta, volatility and drawdown.

    Method:
      1. Reconstruct the shares held in each security on each day.
      2. Use adjusted security prices converted to SEK for daily asset returns.
      3. Weight each asset's return by its previous-day market value.
      4. Do NOT include cash, deposits, withdrawals, transfers or trade cash flows.

    This avoids false performance jumps when account cash-flow history is
    incomplete (for example, older recurring fund purchases whose matching
    deposits are not present in the source screenshots).
    """

    if (
        transactions_df.empty
        or assets_df.empty
        or benchmark_history.empty
    ):
        return pd.DataFrame(
            columns=["date", "portfolio_return", "invested_value_sek"]
        )

    prices = query_dataframe(
        """
        SELECT
            p.asset_id,
            p.price_date,
            p.close_price,
            p.adjusted_close_price
        FROM prices p
        ORDER BY p.asset_id, p.price_date;
        """
    )

    if prices.empty:
        return pd.DataFrame(
            columns=["date", "portfolio_return", "invested_value_sek"]
        )

    fx = query_dataframe(
        """
        SELECT
            currency,
            rate_date,
            sek_per_unit
        FROM fx_rates
        ORDER BY currency, rate_date;
        """
    )

    splits = query_dataframe(
        """
        SELECT
            asset_id,
            action_date,
            ratio_new,
            ratio_old
        FROM corporate_actions
        WHERE UPPER(action_type) = 'SPLIT'
        ORDER BY asset_id, action_date, id;
        """
    )

    benchmark_dates = (
        benchmark_history[["date"]]
        .dropna()
        .drop_duplicates()
        .sort_values("date")
        .copy()
    )

    benchmark_dates["date"] = pd.to_datetime(
        benchmark_dates["date"],
        errors="coerce",
    ).dt.normalize()

    benchmark_dates = benchmark_dates.dropna(
        subset=["date"]
    )

    if benchmark_dates.empty:
        return pd.DataFrame(
            columns=["date", "portfolio_return", "invested_value_sek"]
        )

    start_date = benchmark_dates["date"].min()
    end_date = benchmark_dates["date"].max()

    full_calendar = pd.DataFrame(
        {
            "date": pd.date_range(
                start_date,
                end_date,
                freq="D",
            )
        }
    )

    tx = transactions_df.copy()

    tx["transaction_date"] = pd.to_datetime(
        tx["transaction_date"],
        errors="coerce",
    ).dt.normalize()

    tx["quantity"] = pd.to_numeric(
        tx["quantity"],
        errors="coerce",
    ).fillna(0.0)

    tx["transaction_type"] = (
        tx["transaction_type"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    tx = tx[
        tx["transaction_type"].isin(["BUY", "SELL"])
    ].copy()

    tx["signed_quantity"] = tx["quantity"]

    tx.loc[
        tx["transaction_type"] == "SELL",
        "signed_quantity",
    ] *= -1.0

    prices = prices.copy()

    prices["price_date"] = pd.to_datetime(
        prices["price_date"],
        errors="coerce",
    ).dt.normalize()

    prices["close_price"] = pd.to_numeric(
        prices["close_price"],
        errors="coerce",
    )

    prices["adjusted_close_price"] = pd.to_numeric(
        prices["adjusted_close_price"],
        errors="coerce",
    )

    fx = fx.copy()

    if not fx.empty:
        fx["rate_date"] = pd.to_datetime(
            fx["rate_date"],
            errors="coerce",
        ).dt.normalize()

        fx["currency"] = (
            fx["currency"]
            .fillna("SEK")
            .astype(str)
            .str.upper()
        )

        fx["sek_per_unit"] = pd.to_numeric(
            fx["sek_per_unit"],
            errors="coerce",
        )

    splits = splits.copy()

    if not splits.empty:
        splits["action_date"] = pd.to_datetime(
            splits["action_date"],
            errors="coerce",
        ).dt.normalize()

        splits["ratio_new"] = pd.to_numeric(
            splits["ratio_new"],
            errors="coerce",
        )

        splits["ratio_old"] = pd.to_numeric(
            splits["ratio_old"],
            errors="coerce",
        )

    asset_meta = assets_df[
        ["id", "name", "ticker", "currency"]
    ].copy()

    asset_meta["currency"] = (
        asset_meta["currency"]
        .fillna("SEK")
        .astype(str)
        .str.upper()
    )

    def fx_on_full_calendar(currency):
        currency = normalize_currency(currency)

        if currency == "SEK":
            return pd.Series(
                1.0,
                index=full_calendar.index,
                dtype=float,
            )

        currency_fx = fx[
            fx["currency"] == currency
        ][
            ["rate_date", "sek_per_unit"]
        ].copy()

        if currency_fx.empty:
            return pd.Series(
                float("nan"),
                index=full_calendar.index,
                dtype=float,
            )

        currency_fx = (
            currency_fx
            .groupby("rate_date", as_index=False)["sek_per_unit"]
            .last()
            .rename(columns={"rate_date": "date"})
        )

        merged = full_calendar.merge(
            currency_fx,
            on="date",
            how="left",
        )

        return merged["sek_per_unit"].ffill()

    asset_daily_frames = []

    for asset_id in tx["asset_id"].dropna().unique():

        asset_tx = tx[
            tx["asset_id"] == asset_id
        ].copy()

        asset_prices = prices[
            prices["asset_id"] == asset_id
        ].copy()

        if asset_tx.empty or asset_prices.empty:
            continue

        meta_match = asset_meta[
            asset_meta["id"] == asset_id
        ]

        if meta_match.empty:
            continue

        currency = meta_match.iloc[0]["currency"]

        # -------------------------------
        # Reconstruct actual share count.
        # -------------------------------

        daily_trade_qty = (
            asset_tx
            .groupby("transaction_date")["signed_quantity"]
            .sum()
            .to_dict()
        )

        split_by_date = {}

        if not splits.empty:
            asset_splits = splits[
                splits["asset_id"] == asset_id
            ]

            for _, split in asset_splits.iterrows():
                old = float(split["ratio_old"] or 0)
                new = float(split["ratio_new"] or 0)

                if old <= 0 or new <= 0:
                    continue

                split_date = split["action_date"]

                split_by_date.setdefault(
                    split_date,
                    [],
                ).append(new / old)

        shares = 0.0
        shares_list = []

        for current_date in full_calendar["date"]:

            # Effective stock split first.
            for factor in split_by_date.get(
                current_date,
                [],
            ):
                shares *= factor

            # Then apply trades on the date.
            shares += float(
                daily_trade_qty.get(
                    current_date,
                    0.0,
                )
            )

            if abs(shares) < 1e-10:
                shares = 0.0

            shares_list.append(shares)

        asset_frame = full_calendar.copy()

        asset_frame["shares"] = pd.Series(
            shares_list,
            index=asset_frame.index,
            dtype=float,
        )

        # -------------------------------
        # Raw price for portfolio weights.
        # Adjusted price for investment returns.
        # -------------------------------

        asset_prices = (
            asset_prices
            .groupby("price_date", as_index=False)
            .agg(
                close_price=("close_price", "last"),
                adjusted_close_price=(
                    "adjusted_close_price",
                    "last",
                ),
            )
            .rename(columns={"price_date": "date"})
        )

        asset_frame = asset_frame.merge(
            asset_prices,
            on="date",
            how="left",
        )

        asset_frame["close_price"] = (
            asset_frame["close_price"]
            .ffill()
        )

        asset_frame["adjusted_close_price"] = (
            asset_frame["adjusted_close_price"]
            .fillna(asset_frame["close_price"])
            .ffill()
        )

        asset_frame["fx"] = fx_on_full_calendar(
            currency
        )

        asset_frame["market_value_sek"] = (
            asset_frame["shares"]
            * asset_frame["close_price"]
            * asset_frame["fx"]
        )

        asset_frame["return_price_sek"] = (
            asset_frame["adjusted_close_price"]
            * asset_frame["fx"]
        )

        # Only evaluate on the ACWI trading dates.
        asset_frame = benchmark_dates.merge(
            asset_frame[
                [
                    "date",
                    "shares",
                    "market_value_sek",
                    "return_price_sek",
                ]
            ],
            on="date",
            how="left",
        )

        asset_frame[
            "market_value_sek"
        ] = pd.to_numeric(
            asset_frame["market_value_sek"],
            errors="coerce",
        )

        asset_frame[
            "return_price_sek"
        ] = pd.to_numeric(
            asset_frame["return_price_sek"],
            errors="coerce",
        )

        asset_frame["asset_return"] = (
            asset_frame["return_price_sek"]
            .pct_change()
        )

        # IMPORTANT:
        # Today's return is weighted by yesterday's invested value.
        # Therefore a new purchase does not create a fake positive return.
        asset_frame["weight_value"] = (
            asset_frame["market_value_sek"]
            .shift(1)
        )

        asset_frame["weighted_return"] = (
            asset_frame["weight_value"]
            * asset_frame["asset_return"]
        )

        asset_frame["asset_id"] = int(
            asset_id
        )

        asset_daily_frames.append(
            asset_frame[
                [
                    "date",
                    "asset_id",
                    "weight_value",
                    "weighted_return",
                    "market_value_sek",
                ]
            ]
        )

    if not asset_daily_frames:
        return pd.DataFrame(
            columns=["date", "portfolio_return", "invested_value_sek"]
        )

    combined = pd.concat(
        asset_daily_frames,
        ignore_index=True,
    )

    combined["weight_value"] = pd.to_numeric(
        combined["weight_value"],
        errors="coerce",
    )

    combined["weighted_return"] = pd.to_numeric(
        combined["weighted_return"],
        errors="coerce",
    )

    combined["market_value_sek"] = pd.to_numeric(
        combined["market_value_sek"],
        errors="coerce",
    )

    # Only assets with a valid prior-day value AND return can
    # contribute to that day's portfolio return.
    valid_return_rows = combined[
        combined["weight_value"].notna()
        & combined["weighted_return"].notna()
        & (combined["weight_value"] > 0)
    ].copy()

    numerator = (
        valid_return_rows
        .groupby("date")["weighted_return"]
        .sum()
    )

    denominator = (
        valid_return_rows
        .groupby("date")["weight_value"]
        .sum()
    )

    portfolio_return = (
        numerator / denominator
    ).rename("portfolio_return")

    invested_value = (
        combined
        .groupby("date")["market_value_sek"]
        .sum(min_count=1)
        .rename("invested_value_sek")
    )

    output = benchmark_dates.copy()

    output = output.merge(
        portfolio_return.reset_index(),
        on="date",
        how="left",
    )

    output = output.merge(
        invested_value.reset_index(),
        on="date",
        how="left",
    )

    output = output.replace(
        [float("inf"), float("-inf")],
        float("nan"),
    )

    return output


def calculate_portfolio_risk_analytics(
    portfolio_return_history,
    benchmark_history,
    risk_free_history,
    lookback="3Y",
):
    """
    Calculate portfolio risk analytics from a holdings-weighted
    INVESTMENT return series.

    Cash, deposits, withdrawals and transfers do not enter this return
    series. This is intentional: Sharpe, beta and volatility should measure
    investment behaviour, not account funding activity.
    """

    if (
        portfolio_return_history.empty
        or benchmark_history.empty
    ):
        return None, pd.DataFrame()

    portfolio_returns = (
        portfolio_return_history[
            ["date", "portfolio_return"]
        ]
        .copy()
    )

    portfolio_returns["date"] = pd.to_datetime(
        portfolio_returns["date"],
        errors="coerce",
    ).dt.normalize()

    benchmark = benchmark_history[
        ["date", "benchmark_return"]
    ].copy()

    benchmark["date"] = pd.to_datetime(
        benchmark["date"],
        errors="coerce",
    ).dt.normalize()

    aligned = portfolio_returns.merge(
        benchmark,
        on="date",
        how="inner",
    )

    # Risk-free proxy.
    if risk_free_history.empty:
        aligned["daily_rf"] = float("nan")
        aligned["annual_rate_decimal"] = float("nan")
        rf_available = False

    else:
        rf = risk_free_history.copy()

        rf["date"] = pd.to_datetime(
            rf["date"],
            errors="coerce",
        ).dt.normalize()

        aligned = pd.merge_asof(
            aligned.sort_values("date"),
            rf.sort_values("date"),
            on="date",
            direction="backward",
        )

        aligned["daily_rf"] = (
            aligned["daily_rf"]
            .ffill()
        )

        rf_available = aligned[
            "daily_rf"
        ].notna().any()

    aligned = aligned.replace(
        [float("inf"), float("-inf")],
        float("nan"),
    )

    aligned = aligned.dropna(
        subset=[
            "portfolio_return",
            "benchmark_return",
        ]
    )

    if lookback != "ALL" and not aligned.empty:

        last_date = aligned["date"].max()

        if lookback == "1Y":
            start_date = (
                last_date
                - pd.DateOffset(years=1)
            )

        elif lookback == "3Y":
            start_date = (
                last_date
                - pd.DateOffset(years=3)
            )

        elif lookback == "5Y":
            start_date = (
                last_date
                - pd.DateOffset(years=5)
            )

        else:
            start_date = aligned[
                "date"
            ].min()

        aligned = aligned[
            aligned["date"] >= start_date
        ].copy()

    # A daily security portfolio return outside this band would almost
    # certainly indicate bad market/history data rather than a real return.
    aligned = aligned[
        aligned["portfolio_return"].between(
            -0.60,
            1.50,
            inclusive="both",
        )
    ].copy()

    n = len(aligned)

    if n < 30:
        return None, aligned

    portfolio_returns = (
        aligned["portfolio_return"]
        .astype(float)
    )

    benchmark_returns = (
        aligned["benchmark_return"]
        .astype(float)
    )

    annual_volatility = float(
        portfolio_returns.std(ddof=1)
        * (252.0 ** 0.5)
    )

    cumulative_growth = float(
        (1.0 + portfolio_returns)
        .prod()
    )

    annualized_return = (
        cumulative_growth
        ** (252.0 / n)
        - 1.0
        if cumulative_growth > 0
        else float("nan")
    )

    benchmark_variance = float(
        benchmark_returns.var(ddof=1)
    )

    beta = (
        float(
            portfolio_returns.cov(
                benchmark_returns
            )
        )
        / benchmark_variance
        if benchmark_variance > 0
        else float("nan")
    )

    correlation = float(
        portfolio_returns.corr(
            benchmark_returns
        )
    )

    wealth_index = (
        1.0 + portfolio_returns
    ).cumprod()

    running_peak = (
        wealth_index.cummax()
    )

    drawdown = (
        wealth_index
        / running_peak
        - 1.0
    )

    max_drawdown = float(
        drawdown.min()
    )

    sharpe = float("nan")

    if (
        rf_available
        and "daily_rf" in aligned.columns
    ):
        daily_rf = pd.to_numeric(
            aligned["daily_rf"],
            errors="coerce",
        )

        excess_returns = (
            portfolio_returns
            - daily_rf.fillna(0.0)
        )

        excess_std = float(
            excess_returns.std(ddof=1)
        )

        if excess_std > 0:
            sharpe = (
                float(
                    excess_returns.mean()
                )
                / excess_std
                * (252.0 ** 0.5)
            )

    metrics = {
        "observations": n,
        "annualized_return": annualized_return,
        "annualized_volatility": annual_volatility,
        "beta": beta,
        "correlation": correlation,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "risk_free_available": rf_available,
        "start_date": aligned["date"].min(),
        "end_date": aligned["date"].max(),
    }

    return metrics, aligned


def calculate_asset_risk_metrics(
    current_portfolio,
    benchmark_history,
    risk_free_history,
    lookback="3Y",
):
    """Calculate SEK-based beta/Sharpe/volatility for current holdings."""

    if (
        current_portfolio.empty
        or benchmark_history.empty
    ):
        return pd.DataFrame()

    price_history = query_dataframe(
        """
        SELECT
            p.asset_id,
            p.price_date,
            p.adjusted_close_price,
            p.close_price,
            a.name,
            a.ticker,
            a.currency
        FROM prices p
        JOIN assets a
          ON a.id = p.asset_id
        ORDER BY p.asset_id, p.price_date;
        """
    )

    if price_history.empty:
        return pd.DataFrame()

    fx_history = query_dataframe(
        """
        SELECT
            currency,
            rate_date,
            sek_per_unit
        FROM fx_rates
        ORDER BY currency, rate_date;
        """
    )

    price_history["date"] = pd.to_datetime(
        price_history["price_date"],
        errors="coerce",
    ).dt.normalize()

    price_history["adjusted_close_price"] = pd.to_numeric(
        price_history["adjusted_close_price"],
        errors="coerce",
    )

    price_history["close_price"] = pd.to_numeric(
        price_history["close_price"],
        errors="coerce",
    )

    price_history["analytics_price"] = (
        price_history["adjusted_close_price"]
        .fillna(price_history["close_price"])
    )

    fx_history["date"] = pd.to_datetime(
        fx_history["rate_date"],
        errors="coerce",
    ).dt.normalize()

    fx_history["currency"] = (
        fx_history["currency"]
        .astype(str)
        .str.upper()
    )

    fx_history["sek_per_unit"] = pd.to_numeric(
        fx_history["sek_per_unit"],
        errors="coerce",
    )

    current_asset_ids = set(
        pd.to_numeric(
            current_portfolio["asset_id"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .tolist()
    )

    results = []

    for asset_id in sorted(current_asset_ids):
        asset_prices = price_history[
            price_history["asset_id"] == asset_id
        ].copy()

        if asset_prices.empty:
            continue

        currency = normalize_currency(
            asset_prices.iloc[0]["currency"]
        )

        if currency == "SEK":
            asset_prices["fx"] = 1.0

        else:
            asset_fx = fx_history[
                fx_history["currency"] == currency
            ][
                ["date", "sek_per_unit"]
            ].copy()

            if asset_fx.empty:
                continue

            asset_prices = pd.merge_asof(
                asset_prices.sort_values("date"),
                asset_fx.sort_values("date"),
                on="date",
                direction="backward",
            )

            asset_prices["fx"] = (
                asset_prices["sek_per_unit"]
            )

        asset_prices["value_sek"] = (
            asset_prices["analytics_price"]
            * asset_prices["fx"]
        )

        asset_prices["asset_return"] = (
            asset_prices["value_sek"]
            .pct_change()
        )

        aligned = benchmark_history[
            ["date", "benchmark_return"]
        ].merge(
            asset_prices[
                ["date", "asset_return"]
            ],
            on="date",
            how="inner",
        )

        if not risk_free_history.empty:
            aligned = pd.merge_asof(
                aligned.sort_values("date"),
                risk_free_history[
                    ["date", "daily_rf"]
                ].sort_values("date"),
                on="date",
                direction="backward",
            )
        else:
            aligned["daily_rf"] = 0.0

        if lookback != "ALL" and not aligned.empty:
            last_date = aligned["date"].max()

            years = (
                1
                if lookback == "1Y"
                else 3
                if lookback == "3Y"
                else 5
            )

            aligned = aligned[
                aligned["date"]
                >= last_date - pd.DateOffset(years=years)
            ]

        aligned = aligned.dropna(
            subset=[
                "asset_return",
                "benchmark_return",
            ]
        )

        if len(aligned) < 30:
            continue

        asset_returns = aligned[
            "asset_return"
        ].astype(float)

        benchmark_returns = aligned[
            "benchmark_return"
        ].astype(float)

        annual_vol = float(
            asset_returns.std(ddof=1)
            * (252.0 ** 0.5)
        )

        growth = float(
            (1.0 + asset_returns).prod()
        )

        annual_return = (
            growth ** (
                252.0 / len(asset_returns)
            ) - 1.0
            if growth > 0
            else float("nan")
        )

        bench_var = float(
            benchmark_returns.var(ddof=1)
        )

        beta = (
            float(
                asset_returns.cov(
                    benchmark_returns
                )
            )
            / bench_var
            if bench_var > 0
            else float("nan")
        )

        sharpe = float("nan")

        if (
            "daily_rf" in aligned.columns
            and aligned["daily_rf"].notna().any()
        ):
            excess = (
                asset_returns
                - pd.to_numeric(
                    aligned["daily_rf"],
                    errors="coerce",
                ).fillna(0.0)
            )

            excess_std = float(
                excess.std(ddof=1)
            )

            if excess_std > 0:
                sharpe = (
                    float(excess.mean())
                    / excess_std
                    * (252.0 ** 0.5)
                )

        results.append(
            {
                "Investment": asset_prices.iloc[0]["name"],
                "Ticker": asset_prices.iloc[0]["ticker"],
                "Observations": len(aligned),
                "Annualized Return": annual_return * 100.0,
                "Volatility": annual_vol * 100.0,
                "Beta vs ACWI": beta,
                "Sharpe": sharpe,
                "Correlation": float(
                    asset_returns.corr(
                        benchmark_returns
                    )
                ),
            }
        )

    return pd.DataFrame(results)


def calculate_shares_as_of(asset_id, account_id, target_date):
    """Calculate shares held in one account, including stock splits."""
    target_date = as_date(target_date)

    cursor.execute(
        """
        SELECT id, transaction_type, quantity, transaction_date
        FROM transactions
        WHERE asset_id = %s
          AND account_id = %s
          AND transaction_date <= %s
        ORDER BY transaction_date, id;
        """,
        (asset_id, account_id, target_date),
    )
    tx_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, action_date, action_type, ratio_new, ratio_old
        FROM corporate_actions
        WHERE asset_id = %s
          AND action_date <= %s
        ORDER BY action_date, id;
        """,
        (asset_id, target_date),
    )
    action_rows = cursor.fetchall()

    events = []

    for action in action_rows:
        if str(action["action_type"]).upper() == "SPLIT":
            events.append(
                (
                    action["action_date"],
                    0,
                    int(action["id"]),
                    "SPLIT",
                    float(action["ratio_new"] or 0),
                    float(action["ratio_old"] or 0),
                )
            )

    for tx in tx_rows:
        events.append(
            (
                tx["transaction_date"],
                1,
                int(tx["id"]),
                str(tx["transaction_type"]).upper(),
                float(tx["quantity"]),
                None,
            )
        )

    events.sort(key=lambda x: (x[0], x[1], x[2]))
    shares = 0.0

    for _, _, _, event_type, value_1, value_2 in events:
        if event_type == "SPLIT":
            if value_1 <= 0 or value_2 <= 0:
                continue
            shares *= value_1 / value_2
        elif event_type == "BUY":
            shares += value_1
        elif event_type == "SELL":
            shares -= value_1

    return max(shares, 0.0)


def build_portfolio_states(transactions_df, actions_df):
    """
    Build current positions with average-cost accounting.
    Stock splits adjust quantity/average cost while total cost basis stays unchanged.
    """
    columns = [
        "account_key",
        "account_id",
        "account",
        "asset_id",
        "name",
        "ticker",
        "currency",
        "shares_after",
        "cost_basis_after_sek",
        "average_cost_after_sek",
        "total_realized_pl_sek",
    ]

    if transactions_df.empty:
        return pd.DataFrame(columns=columns)

    tx = transactions_df.copy()
    tx["account_key"] = tx["account_id"].fillna(0).astype(int)

    action_map = {}
    if not actions_df.empty:
        for asset_id, group in actions_df.groupby("asset_id"):
            action_map[int(asset_id)] = group.copy()

    state_rows = []

    for (account_key, asset_id), group in tx.groupby(["account_key", "asset_id"]):
        group = group.sort_values(["transaction_date", "id"]).copy()
        first = group.iloc[0]

        shares = 0.0
        cost_basis_sek = 0.0
        realized_pl_sek = 0.0
        events = []

        actions_for_asset = action_map.get(int(asset_id), pd.DataFrame())
        if not actions_for_asset.empty:
            for _, action in actions_for_asset.iterrows():
                if str(action["action_type"]).upper() != "SPLIT":
                    continue
                events.append(
                    {
                        "date": action["action_date"],
                        "order": 0,
                        "id": int(action["id"]),
                        "type": "SPLIT",
                        "ratio_new": float(action["ratio_new"]),
                        "ratio_old": float(action["ratio_old"]),
                    }
                )

        for _, row in group.iterrows():
            events.append(
                {
                    "date": row["transaction_date"],
                    "order": 1,
                    "id": int(row["id"]),
                    "type": str(row["transaction_type"]).upper(),
                    "quantity": float(row["quantity"]),
                    "price": float(row["price"]),
                    "fees": float(row["fees"] or 0),
                    "fx": float(row["fx_rate_to_sek"]),
                }
            )

        events.sort(key=lambda e: (e["date"], e["order"], e["id"]))

        for event in events:
            event_type = event["type"]

            if event_type == "SPLIT":
                ratio_new = event["ratio_new"]
                ratio_old = event["ratio_old"]
                if ratio_new <= 0 or ratio_old <= 0:
                    raise ValueError(
                        f"Invalid split ratio for {first['ticker']} on {event['date']}."
                    )
                shares *= ratio_new / ratio_old

            elif event_type == "BUY":
                purchase_cost_sek = (
                    event["quantity"] * event["price"] + event["fees"]
                ) * event["fx"]
                shares += event["quantity"]
                cost_basis_sek += purchase_cost_sek

            elif event_type == "SELL":
                quantity = event["quantity"]

                if shares <= 0 or quantity > shares + 1e-9:
                    raise ValueError(
                        f"Invalid transaction history for {first['ticker']} in "
                        f"{first['account']}: trying to sell {quantity:g} shares "
                        f"while only {shares:g} are owned."
                    )

                average_cost_sek = cost_basis_sek / shares
                sold_cost_basis_sek = quantity * average_cost_sek
                sale_proceeds_sek = (
                    quantity * event["price"] - event["fees"]
                ) * event["fx"]

                realized_pl_sek += sale_proceeds_sek - sold_cost_basis_sek
                shares -= quantity
                cost_basis_sek -= sold_cost_basis_sek

                if abs(shares) < 1e-9:
                    shares = 0.0
                    cost_basis_sek = 0.0

        average_cost_after_sek = cost_basis_sek / shares if shares > 0 else 0.0

        raw_account_id = first["account_id"]
        account_id = None if pd.isna(raw_account_id) else int(raw_account_id)

        state_rows.append(
            {
                "account_key": int(account_key),
                "account_id": account_id,
                "account": first["account"],
                "asset_id": int(asset_id),
                "name": first["name"],
                "ticker": first["ticker"],
                "currency": first["currency"],
                "shares_after": shares,
                "cost_basis_after_sek": cost_basis_sek,
                "average_cost_after_sek": average_cost_after_sek,
                "total_realized_pl_sek": realized_pl_sek,
            }
        )

    return pd.DataFrame(state_rows, columns=columns)




def clean_text(value):
    """Return a clean string for CSV values, treating NaN/None as blank."""
    if pd.isna(value):
        return ""
    value = str(value).strip()
    return "" if value.upper() in {"NAN", "NONE"} else value


def normalize_account_ref(value):
    """Normalize broker account references without exposing them elsewhere."""
    value = clean_text(value)
    if value.endswith(".0") and value[:-2].replace(" ", "").replace(",", "").isdigit():
        value = value[:-2]
    return value or "UNKNOWN"


def normalize_isin(value):
    """Normalize an ISIN from a broker export."""
    return clean_text(value).upper()


def normalize_currency(value, fallback="SEK"):
    """Normalize a three-letter currency code."""
    value = clean_text(value).upper()
    return value if value else fallback


def normalize_security_name(value):
    """Normalize an investment name for fuzzy Yahoo matching."""
    value = clean_text(value).upper()
    value = value.replace("&", " AND ")
    value = re.sub(r"[^A-Z0-9ÅÄÖ]+", " ", value)
    stop_words = {
        "AB", "PLC", "INC", "CORP", "CORPORATION", "LTD", "LIMITED",
        "CLASS", "CL", "SERIES", "ORD", "ORDINARY", "SHARE", "SHARES",
    }
    tokens = [token for token in value.split() if token not in stop_words]
    return " ".join(tokens).strip()


@st.cache_data(ttl=86400, show_spinner=False)
def yahoo_search_quotes(query):
    """Return Yahoo Finance search quotes as plain dictionaries."""
    query = clean_text(query)
    if not query:
        return []

    try:
        search = yf.Search(query, max_results=12)
        quotes = getattr(search, "quotes", []) or []
        return [dict(item) for item in quotes if isinstance(item, dict)]
    except Exception:
        return []


@st.cache_data(ttl=86400, show_spinner=False)
def validate_yahoo_symbol(symbol):
    """Check that Yahoo returns at least one non-null recent closing price."""
    symbol = clean_text(symbol).upper()
    if not symbol:
        return False

    try:
        history = yf.Ticker(symbol).history(period="5d")
        if history.empty or "Close" not in history.columns:
            return False
        return not history["Close"].dropna().empty
    except Exception:
        return False


def expected_yahoo_suffix(currency, isin):
    """Return a helpful exchange suffix preference for common holdings."""
    currency = normalize_currency(currency, "")
    country = normalize_isin(isin)[:2]

    if currency == "SEK":
        return ".ST"
    if country == "FI" and currency == "EUR":
        return ".HE"
    if country == "GB" and currency == "GBP":
        return ".L"
    return ""


def yahoo_asset_type_match(asset_type, quote_type):
    """Small score bonus when Yahoo quote type agrees with our asset type."""
    asset_type = clean_text(asset_type).upper()
    quote_type = clean_text(quote_type).upper()

    expected = {
        "STOCK": {"EQUITY"},
        "ETF": {"ETF"},
        "FUND": {"MUTUALFUND"},
        "METAL": {"FUTURE"},
        "OTHER": {"EQUITY", "ETF", "MUTUALFUND", "FUTURE"},
    }
    return quote_type in expected.get(
        asset_type,
        {"EQUITY", "ETF", "MUTUALFUND", "FUTURE"},
    )


def suggest_yahoo_symbol(name, isin, currency, asset_type):
    """Suggest and validate the most plausible Yahoo Finance symbol.

    The function searches by ISIN and by investment name, ranks candidates,
    then validates the best few against recent Yahoo price history. It never
    writes to MySQL by itself; the user reviews suggestions before saving.
    """
    name = clean_text(name)
    isin = normalize_isin(isin)
    currency = normalize_currency(currency, "")
    asset_type = clean_text(asset_type) or "Other"

    candidates = {}

    queries = []
    if isin:
        queries.append((isin, True))
    if name:
        queries.append((name, False))

    for query, is_isin_query in queries:
        for quote in yahoo_search_quotes(query):
            symbol = clean_text(quote.get("symbol", "")).upper()
            quote_type = clean_text(quote.get("quoteType", "")).upper()

            if not symbol or quote_type not in {"EQUITY", "ETF", "MUTUALFUND", "FUTURE"}:
                continue

            result_name = clean_text(
                quote.get("longname")
                or quote.get("shortname")
                or quote.get("name")
                or ""
            )
            result_currency = normalize_currency(quote.get("currency", ""), "")
            exchange = clean_text(quote.get("exchDisp") or quote.get("exchange") or "")

            candidate = candidates.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "name": result_name,
                    "currency": result_currency,
                    "exchange": exchange,
                    "quote_type": quote_type,
                    "isin_hit": False,
                },
            )

            if is_isin_query:
                candidate["isin_hit"] = True

            # Prefer the more descriptive name when duplicate results occur.
            if len(result_name) > len(candidate.get("name", "")):
                candidate["name"] = result_name

    if not candidates:
        return {
            "symbol": "",
            "candidate_name": "",
            "exchange": "",
            "confidence": "NO MATCH",
            "score": 0.0,
            "status": "No Yahoo candidates found",
        }

    target_name = normalize_security_name(name)
    suffix = expected_yahoo_suffix(currency, isin)
    country = isin[:2]

    ranked = []

    for candidate in candidates.values():
        candidate_name = normalize_security_name(candidate["name"])
        similarity = SequenceMatcher(None, target_name, candidate_name).ratio() if target_name and candidate_name else 0.0

        score = similarity * 45.0

        if candidate["isin_hit"]:
            score += 45.0

        if currency and candidate["currency"] == currency:
            score += 15.0

        if yahoo_asset_type_match(asset_type, candidate["quote_type"]):
            score += 8.0

        symbol = candidate["symbol"]

        if suffix and symbol.endswith(suffix):
            score += 15.0

        # US / Marshall Islands holdings normally use unsuffixed US symbols.
        if country in {"US", "MH"} and currency == "USD" and "." not in symbol:
            score += 10.0

        candidate["pre_score"] = score
        ranked.append(candidate)

    ranked.sort(key=lambda item: item["pre_score"], reverse=True)

    # Validate only the strongest candidates to keep the review reasonably fast.
    for candidate in ranked[:4]:
        candidate["valid_price"] = validate_yahoo_symbol(candidate["symbol"])
        candidate["score"] = candidate["pre_score"] + (20.0 if candidate["valid_price"] else -40.0)

    for candidate in ranked[4:]:
        candidate["valid_price"] = False
        candidate["score"] = candidate["pre_score"] - 10.0

    ranked.sort(key=lambda item: item["score"], reverse=True)
    best = ranked[0]

    if not best["valid_price"]:
        confidence = "NO MATCH"
        status = "Candidate found, but no valid Yahoo price"
        symbol = ""
    elif best["score"] >= 95:
        confidence = "HIGH"
        status = "Validated Yahoo quote"
        symbol = best["symbol"]
    elif best["score"] >= 70:
        confidence = "MEDIUM"
        status = "Validated — review before saving"
        symbol = best["symbol"]
    else:
        confidence = "LOW"
        status = "Weak match — review carefully"
        symbol = best["symbol"]

    return {
        "symbol": symbol,
        "candidate_name": best["name"],
        "exchange": best["exchange"],
        "confidence": confidence,
        "score": round(float(best["score"]), 1),
        "status": status,
    }



def fetch_yahoo_metadata(market_symbol, asset_type="Other"):
    """Fetch sector and issuer country from Yahoo Finance for one security.

    Yahoo coverage is strongest for listed equities. ETFs and mutual funds often
    do not expose a conventional company sector/country, so we keep those values
    conservative instead of inventing look-through exposure.
    """
    symbol = clean_text(market_symbol).upper()
    asset_type = clean_text(asset_type) or "Other"

    if asset_type.upper() == "METAL":
        return {
            "sector": "Precious Metals",
            "country": "Global / Commodity",
            "status": "Precious-metal classification",
        }

    if not symbol:
        return {
            "sector": "",
            "country": "",
            "status": "No Yahoo symbol",
        }

    try:
        ticker_obj = yf.Ticker(symbol)

        try:
            info = ticker_obj.get_info()
        except Exception:
            info = ticker_obj.info

        if not isinstance(info, dict):
            info = {}

        sector = clean_text(info.get("sector", ""))
        country = clean_text(info.get("country", ""))
        category = clean_text(info.get("category", ""))

        # Funds generally do not have a meaningful corporate sector.  If Yahoo
        # gives us a fund category, surface that as a clearly labelled category;
        # otherwise simply identify it as a fund rather than making up a sector.
        if not sector and asset_type.upper() in {"FUND", "ETF"}:
            sector = f"Fund / ETF — {category}" if category else "Fund / ETF"

        if sector or country:
            return {
                "sector": sector,
                "country": country,
                "status": "Yahoo metadata found",
            }

        return {
            "sector": sector,
            "country": country,
            "status": "Yahoo returned no sector/country",
        }

    except Exception as error:
        return {
            "sector": "",
            "country": "",
            "status": f"Could not fetch metadata: {error}",
        }


def avanza_security_action(value):
    """Return BUY, SELL, DIVIDEND, or None for an Avanza transaction label."""
    value = clean_text(value).strip().lower()
    mapping = {
        "köp": "BUY",
        "kop": "BUY",
        "sälj": "SELL",
        "salj": "SELL",
        "utdelning": "DIVIDEND",
    }
    return mapping.get(value)


def avanza_cash_type(value):
    """Normalize common Avanza cash movement labels."""
    raw = clean_text(value).strip().lower()
    mapping = {
        "köp": "BUY",
        "kop": "BUY",
        "sälj": "SELL",
        "salj": "SELL",
        "utdelning": "DIVIDEND",
        "utländsk källskatt": "WITHHOLDING_TAX",
        "utlandsk kallskatt": "WITHHOLDING_TAX",
        "preliminärskatt kapitalränta": "TAX",
        "preliminarskatt kapitalranta": "TAX",
        "inlåningsränta": "INTEREST",
        "inlaningsranta": "INTEREST",
        "autogiroinsättning": "DEPOSIT",
        "autogiroinsattning": "DEPOSIT",
        "insättning": "DEPOSIT",
        "insattning": "DEPOSIT",
        "uttag": "WITHDRAWAL",
        "överföring": "TRANSFER",
        "overforing": "TRANSFER",
    }
    if raw in mapping:
        return mapping[raw]
    if not raw:
        return "OTHER"
    cleaned = re.sub(r"[^A-Z0-9]+", "_", raw.upper()).strip("_")
    return cleaned[:50] or "OTHER"


def make_avanza_hash(kind, account_id, source_account, tx_date, tx_type, isin,
                     description, quantity, price, amount, currency, fees):
    """Create a stable row fingerprint for overlapping Avanza exports."""
    parts = [
        kind,
        str(account_id),
        normalize_account_ref(source_account),
        str(tx_date),
        clean_text(tx_type).upper(),
        normalize_isin(isin),
        clean_text(description).upper(),
        f"{float(quantity):.8f}",
        f"{float(price):.8f}",
        f"{float(amount):.8f}",
        normalize_currency(currency),
        f"{float(fees):.8f}",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def make_placeholder_ticker(description, isin, existing_tickers):
    """Create a unique temporary ticker for an automatically discovered asset."""
    base = re.sub(r"[^A-Z0-9]+", "", clean_text(description).upper())
    if not base:
        base = "ASSET"
    base = base[:14]
    suffix = normalize_isin(isin)[-4:] if normalize_isin(isin) else "NEW"
    candidate = base[:15]
    if candidate not in existing_tickers:
        return candidate
    candidate = f"{base[:15]}{suffix}"[:20]
    counter = 2
    while candidate in existing_tickers:
        candidate = f"{base[:14]}{counter}"[:20]
        counter += 1
    return candidate


def fetch_existing_hashes(table, hash_column, hashes):
    """Fetch existing hashes in chunks to avoid huge SQL IN clauses.

    SQL identifiers cannot be parameterized by mysql-connector, so only the
    explicitly supported table/column pairs are allowed here.
    """
    allowed_identifier_pairs = {
        ("transactions", "transaction_hash"),
        ("cash_movements", "transaction_hash"),
        ("dividends", "transaction_hash"),
    }

    if (table, hash_column) not in allowed_identifier_pairs:
        raise ValueError("Unsupported table/column pair for hash lookup.")

    hashes = [h for h in hashes if h]
    if not hashes:
        return set()

    found = set()
    chunk_size = 500
    for start in range(0, len(hashes), chunk_size):
        chunk = hashes[start:start + chunk_size]
        placeholders = ",".join(["%s"] * len(chunk))
        cursor.execute(
            f"SELECT {hash_column} FROM {table} WHERE {hash_column} IN ({placeholders});",
            tuple(chunk),
        )
        for row in cursor.fetchall():
            if row[hash_column]:
                found.add(row[hash_column])
    return found



# ============================================================
# 4B. NORDNET IMPORT HELPERS
# ============================================================


def read_nordnet_csv(file_bytes):
    """Read Nordnet's tab-separated UTF-16 transaction export."""
    encodings = ["utf-16", "utf-16-le", "utf-8-sig", "cp1252"]
    last_error = None

    for encoding in encodings:
        try:
            frame = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding,
                sep="\t",
                dtype=str,
            )
            frame.columns = [clean_text(c).lstrip("\ufeff") for c in frame.columns]
            frame = frame.dropna(how="all").reset_index(drop=True)
            if len(frame.columns) > 1:
                return frame
        except Exception as error:
            last_error = error

    raise ValueError(f"Could not read Nordnet CSV file: {last_error}")


def nordnet_component_hash(kind, account_id, source_depot, source_id):
    """Stable duplicate fingerprint using Nordnet's own row Id."""
    value = (
        f"NORDNET|{kind}|{int(account_id)}|"
        f"{normalize_account_ref(source_depot)}|{clean_text(source_id)}"
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def nordnet_cash_type(raw_type):
    """Map Nordnet labels to our normalized cash-movement labels."""
    value = clean_text(raw_type).upper()
    mapping = {
        "KÖPT": "BUY",
        "SÅLT": "SELL",
        "UTDELNING": "DIVIDEND",
        "KÄLLSKATT": "WITHHOLDING_TAX",
        "INSÄTTNING": "DEPOSIT",
        "REALTIDSINSÄTTNING": "DEPOSIT",
        "UTTAG": "WITHDRAWAL",
        "UTTAG INTERNT": "TRANSFER_OUT",
        "KAP RÄNTA": "INTEREST",
        "TECKNING LIKVID": "SUBSCRIPTION_PAYMENT",
        "DECIMALER LIKVID": "FRACTIONAL_CASH",
    }
    return mapping.get(value, value[:50] if value else "OTHER")


def nordnet_has_cash_effect(raw_type):
    """Only these Nordnet rows actually change the cash balance.

    Some Nordnet corporate-action rows repeat a non-zero Belopp even though
    Saldo does not move (e.g. TECKNING INLÄGG VP and DECIMALER UTTAG VP).
    """
    value = clean_text(raw_type).upper()
    return value in {
        "KÖPT",
        "SÅLT",
        "UTDELNING",
        "KÄLLSKATT",
        "INSÄTTNING",
        "REALTIDSINSÄTTNING",
        "UTTAG",
        "UTTAG INTERNT",
        "KAP RÄNTA",
        "TECKNING LIKVID",
        "DECIMALER LIKVID",
    }


def nordnet_country_currency(isin):
    """Infer likely trading currency when Nordnet reports an FX rate."""
    country = normalize_isin(isin)[:2]
    mapping = {
        "US": "USD",
        "MH": "USD",
        "FI": "EUR",
        "DE": "EUR",
        "NL": "EUR",
        "FR": "EUR",
        "IE": "EUR",
        "LU": "EUR",
        "BE": "EUR",
        "ES": "EUR",
        "IT": "EUR",
        "AT": "EUR",
        "GB": "GBP",
        "SE": "SEK",
    }
    return mapping.get(country, "SEK")


def nordnet_trade_currency(isin, exchange_rate):
    """Nordnet's Kurs is SEK when Växlingskurs is blank; otherwise local currency."""
    if float(exchange_rate or 0) > 0:
        return nordnet_country_currency(isin)
    return "SEK"


def nordnet_dividend_currency(transaction_text, isin):
    """Extract dividend currency from Nordnet's text, with ISIN fallback."""
    text = clean_text(transaction_text).upper()
    match = re.search(r"\b(USD|EUR|SEK|GBP|NOK|DKK|CAD|CHF)\b", text)
    if match:
        return match.group(1)
    return nordnet_country_currency(isin)


# ============================================================
# 5. LOAD REFERENCE DATA
# ============================================================

# Keep previously-added precious metals on spot symbols.
ensure_spot_metal_symbols()

assets = query_dataframe(
    """
    SELECT id, ticker, name, asset_type, currency, market_symbol, isin, sector, country
    FROM assets
    ORDER BY name;
    """
)

accounts = query_dataframe(
    """
    SELECT id, account_name, broker, account_type
    FROM accounts
    ORDER BY broker, account_name;
    """
)


# ============================================================
# 6. SIDEBAR: ADD / EDIT INVESTMENTS
# ============================================================

with st.sidebar.expander("➕ Add Investment"):
    with st.form("add_investment_form"):
        new_name = st.text_input("Investment name", placeholder="Microsoft")
        new_ticker = st.text_input("Ticker", placeholder="MSFT")
        new_market_symbol = st.text_input(
            "Yahoo Finance symbol",
            placeholder="MSFT (can be left blank for imported placeholders)",
        )
        new_isin = st.text_input("ISIN (optional)", placeholder="US5949181045")
        new_asset_type = st.selectbox("Asset type", ["Stock", "ETF", "Fund", "Metal", "Other"])
        new_currency = st.selectbox("Currency", ["SEK", "USD", "EUR", "GBP"])
        new_sector = st.text_input(
            "Sector (optional)",
            placeholder="Technology — can be auto-filled later",
        )
        new_country = st.text_input(
            "Country (optional)",
            placeholder="United States — can be auto-filled later",
        )
        add_investment = st.form_submit_button("Add Investment", use_container_width=True)

if add_investment:
    try:
        new_name = new_name.strip()
        new_ticker = new_ticker.strip().upper()
        new_market_symbol = new_market_symbol.strip().upper()
        new_isin = normalize_isin(new_isin) or None
        new_sector = new_sector.strip() or None
        new_country = new_country.strip() or None

        if not new_name:
            raise ValueError("Enter an investment name.")
        if not new_ticker:
            raise ValueError("Enter a ticker.")

        cursor.execute(
            """
            SELECT id
            FROM assets
            WHERE ticker = %s
               OR (%s IS NOT NULL AND isin = %s)
               OR (%s <> '' AND market_symbol = %s)
            LIMIT 1;
            """,
            (new_ticker, new_isin, new_isin, new_market_symbol, new_market_symbol),
        )
        if cursor.fetchone():
            raise ValueError("That investment already exists.")

        if new_market_symbol:
            test_data = yf.Ticker(new_market_symbol).history(period="5d")
            if test_data.empty:
                raise ValueError("Yahoo Finance could not find that market symbol.")

        cursor.execute(
            """
            INSERT INTO assets (
                ticker, name, asset_type, currency, market_symbol, isin, sector, country
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                new_ticker,
                new_name,
                new_asset_type,
                new_currency,
                new_market_symbol or None,
                new_isin,
                new_sector,
                new_country,
            ),
        )
        connection.commit()
        st.session_state["asset_added"] = f"✅ {new_name} added."
        st.rerun()

    except Exception as error:
        connection.rollback()
        st.sidebar.error(f"Could not add investment: {error}")

if "asset_added" in st.session_state:
    st.sidebar.success(st.session_state.pop("asset_added"))


with st.sidebar.expander("🪙 Add Precious Metal"):

    st.caption(
        "Physical metals are tracked in grams. "
        "Current market value uses direct spot metal/SEK rates converted to SEK per gram. "
        "Purchase prices are entered in SEK per gram."
    )

    with st.form(
        "add_precious_metal_form"
    ):
        metal_name = st.selectbox(
            "Metal",
            list(PRECIOUS_METALS.keys()),
        )

        add_metal = (
            st.form_submit_button(
                "Add Metal",
                use_container_width=True,
            )
        )

    if add_metal:
        try:
            definition = (
                PRECIOUS_METALS[metal_name]
            )

            cursor.execute(
                """
                SELECT id
                FROM assets
                WHERE ticker = %s
                   OR market_symbol = %s
                   OR name = %s
                LIMIT 1;
                """,
                (
                    definition["ticker"],
                    definition["market_symbol"],
                    metal_name,
                ),
            )

            if cursor.fetchone():
                raise ValueError(
                    f"{metal_name} already exists."
                )

            # Verify Yahoo quote before saving.
            if not validate_yahoo_symbol(
                definition["market_symbol"]
            ):
                raise ValueError(
                    "Yahoo Finance could not validate "
                    f"{definition['market_symbol']}."
                )

            cursor.execute(
                """
                INSERT INTO assets (
                    ticker,
                    name,
                    asset_type,
                    currency,
                    market_symbol,
                    isin,
                    sector,
                    country
                )
                VALUES (
                    %s,
                    %s,
                    'Metal',
                    'SEK',
                    %s,
                    NULL,
                    'Precious Metals',
                    'Global / Commodity'
                );
                """,
                (
                    definition["ticker"],
                    metal_name,
                    definition["market_symbol"],
                ),
            )

            connection.commit()

            st.session_state[
                "metal_added"
            ] = (
                f"✅ {metal_name} added. "
                "Enter your holding as grams under "
                "Add Transaction."
            )

            st.rerun()

        except Exception as error:
            connection.rollback()

            st.sidebar.error(
                f"Could not add metal: {error}"
            )

if "metal_added" in st.session_state:
    st.sidebar.success(
        st.session_state.pop(
            "metal_added"
        )
    )


with st.sidebar.expander("🧹 Rebuild Metal Prices"):
    st.caption(
        "Use this once if metal values were previously calculated "
        "from futures prices. It deletes only stored price history "
        "for Metal assets — it does NOT delete your metal transactions."
    )

    if st.button(
        "Clear Stored Metal Prices",
        key="clear_stored_metal_prices",
        use_container_width=True,
    ):
        cursor.execute(
            """
            DELETE p
            FROM prices p
            JOIN assets a
              ON a.id = p.asset_id
            WHERE UPPER(COALESCE(a.asset_type, '')) = 'METAL';
            """
        )
        deleted_rows = cursor.rowcount
        connection.commit()

        st.session_state["metal_prices_cleared"] = (
            f"✅ Cleared {deleted_rows} stored metal price row(s). "
            "Now click Refresh Prices, then run Historical Data → "
            "Update Historical Data."
        )
        st.rerun()

if "metal_prices_cleared" in st.session_state:
    st.sidebar.success(
        st.session_state.pop(
            "metal_prices_cleared"
        )
    )


with st.sidebar.expander("✏️ Edit Investment"):
    if assets.empty:
        st.caption("No investments yet.")
    else:
        edit_asset_options = {
            f"{row['name']} ({row['ticker']})": int(row["id"])
            for _, row in assets.iterrows()
        }
        edit_asset_label = st.selectbox(
            "Investment to edit",
            list(edit_asset_options.keys()),
            key="edit_asset_select",
        )
        edit_asset_id = edit_asset_options[edit_asset_label]
        selected_asset_row = assets[assets["id"] == edit_asset_id].iloc[0]

        with st.form("edit_investment_form"):
            edit_name = st.text_input("Name", value=str(selected_asset_row["name"]))
            edit_ticker = st.text_input("Ticker", value=str(selected_asset_row["ticker"]))
            edit_market_symbol = st.text_input(
                "Yahoo Finance symbol",
                value=clean_text(selected_asset_row.get("market_symbol", "")),
            )
            edit_isin = st.text_input(
                "ISIN",
                value=clean_text(selected_asset_row.get("isin", "")),
            )
            edit_sector = st.text_input(
                "Sector",
                value=clean_text(selected_asset_row.get("sector", "")),
            )
            edit_country = st.text_input(
                "Country",
                value=clean_text(selected_asset_row.get("country", "")),
            )
            asset_types = ["Stock", "ETF", "Fund", "Metal", "Other"]
            current_type = clean_text(selected_asset_row.get("asset_type", "Other")) or "Other"
            edit_asset_type = st.selectbox(
                "Asset type",
                asset_types,
                index=asset_types.index(current_type) if current_type in asset_types else 3,
            )
            currencies = ["SEK", "USD", "EUR", "GBP"]
            current_currency = normalize_currency(selected_asset_row.get("currency", "SEK"))
            edit_currency = st.selectbox(
                "Currency",
                currencies,
                index=currencies.index(current_currency) if current_currency in currencies else 0,
            )
            save_asset_changes = st.form_submit_button(
                "Save Changes",
                use_container_width=True,
            )

        if save_asset_changes:
            try:
                edit_name = edit_name.strip()
                edit_ticker = edit_ticker.strip().upper()
                edit_market_symbol = edit_market_symbol.strip().upper()
                edit_isin = normalize_isin(edit_isin) or None
                edit_sector = edit_sector.strip() or None
                edit_country = edit_country.strip() or None

                if not edit_name or not edit_ticker:
                    raise ValueError("Name and ticker are required.")

                cursor.execute(
                    """
                    SELECT id
                    FROM assets
                    WHERE id <> %s
                      AND (
                            ticker = %s
                         OR (%s IS NOT NULL AND isin = %s)
                         OR (%s <> '' AND market_symbol = %s)
                      )
                    LIMIT 1;
                    """,
                    (
                        edit_asset_id,
                        edit_ticker,
                        edit_isin,
                        edit_isin,
                        edit_market_symbol,
                        edit_market_symbol,
                    ),
                )
                if cursor.fetchone():
                    raise ValueError("Another investment already uses that ticker, ISIN or symbol.")

                if edit_market_symbol:
                    test_data = yf.Ticker(edit_market_symbol).history(period="5d")
                    if test_data.empty:
                        raise ValueError("Yahoo Finance could not find that market symbol.")

                cursor.execute(
                    """
                    UPDATE assets
                    SET name = %s,
                        ticker = %s,
                        market_symbol = %s,
                        isin = %s,
                        asset_type = %s,
                        currency = %s,
                        sector = %s,
                        country = %s
                    WHERE id = %s;
                    """,
                    (
                        edit_name,
                        edit_ticker,
                        edit_market_symbol or None,
                        edit_isin,
                        edit_asset_type,
                        edit_currency,
                        edit_sector,
                        edit_country,
                        edit_asset_id,
                    ),
                )
                connection.commit()
                st.session_state["asset_edited"] = "✅ Investment updated."
                st.rerun()

            except Exception as error:
                connection.rollback()
                st.sidebar.error(f"Could not update investment: {error}")

if "asset_edited" in st.session_state:
    st.sidebar.success(st.session_state.pop("asset_edited"))


# ============================================================
# 7. SIDEBAR: ADD / EDIT ACCOUNTS
# ============================================================

st.sidebar.divider()

with st.sidebar.expander("🏦 Add Account"):
    with st.form("add_account_form"):
        account_name = st.text_input("Account name", placeholder="ISK")
        broker = st.text_input("Broker", placeholder="Avanza")
        account_type = st.selectbox("Account type", ["ISK", "KF", "AF", "Pension", "Other"])
        add_account = st.form_submit_button("Add Account", use_container_width=True)

if add_account:
    try:
        account_name = account_name.strip()
        broker = broker.strip()

        if not account_name:
            raise ValueError("Enter an account name.")
        if not broker:
            raise ValueError("Enter a broker.")

        cursor.execute(
            """
            INSERT INTO accounts (account_name, broker, account_type, base_currency)
            VALUES (%s, %s, %s, 'SEK');
            """,
            (account_name, broker, account_type),
        )
        connection.commit()
        st.session_state["account_added"] = f"✅ {broker} — {account_name} added."
        st.rerun()

    except Exception as error:
        connection.rollback()
        st.sidebar.error(f"Could not add account: {error}")

if "account_added" in st.session_state:
    st.sidebar.success(st.session_state.pop("account_added"))


with st.sidebar.expander("✏️ Edit Account"):
    if accounts.empty:
        st.caption("No accounts yet.")
    else:
        edit_account_options = {
            f"{row['broker']} — {row['account_name']} ({row['account_type']})": int(row["id"])
            for _, row in accounts.iterrows()
        }
        edit_account_label = st.selectbox(
            "Account to edit",
            list(edit_account_options.keys()),
            key="edit_account_select",
        )
        edit_account_id = edit_account_options[edit_account_label]
        selected_account_row = accounts[accounts["id"] == edit_account_id].iloc[0]

        with st.form("edit_account_form"):
            edit_account_name = st.text_input(
                "Account name",
                value=str(selected_account_row["account_name"]),
            )
            edit_broker = st.text_input("Broker", value=str(selected_account_row["broker"]))
            account_types = ["ISK", "KF", "AF", "Pension", "Other"]
            current_account_type = clean_text(selected_account_row["account_type"]) or "Other"
            edit_account_type = st.selectbox(
                "Account type",
                account_types,
                index=(
                    account_types.index(current_account_type)
                    if current_account_type in account_types
                    else 4
                ),
            )
            save_account_changes = st.form_submit_button(
                "Save Changes",
                use_container_width=True,
            )

        if save_account_changes:
            try:
                edit_account_name = edit_account_name.strip()
                edit_broker = edit_broker.strip()
                if not edit_account_name or not edit_broker:
                    raise ValueError("Account name and broker are required.")

                cursor.execute(
                    """
                    UPDATE accounts
                    SET account_name = %s,
                        broker = %s,
                        account_type = %s
                    WHERE id = %s;
                    """,
                    (
                        edit_account_name,
                        edit_broker,
                        edit_account_type,
                        edit_account_id,
                    ),
                )
                connection.commit()
                st.session_state["account_edited"] = "✅ Account updated."
                st.rerun()

            except Exception as error:
                connection.rollback()
                st.sidebar.error(f"Could not update account: {error}")

if "account_edited" in st.session_state:
    st.sidebar.success(st.session_state.pop("account_edited"))


# ============================================================
# 8. SIDEBAR: STOCK SPLITS / CORPORATE ACTIONS
# ============================================================

with st.sidebar.expander("🔀 Stock Split"):
    if assets.empty:
        st.caption("Add an investment first.")
    else:
        split_asset_options = {
            f"{row['name']} ({row['ticker']})": int(row["id"])
            for _, row in assets.iterrows()
        }

        with st.form("stock_split_form"):
            split_asset_label = st.selectbox("Investment", list(split_asset_options.keys()))
            split_date = st.date_input("Split date", value=date.today(), max_value=date.today())
            ratio_new = st.number_input("New shares", min_value=0.000001, value=10.0, step=1.0)
            ratio_old = st.number_input("Old shares", min_value=0.000001, value=1.0, step=1.0)
            split_notes = st.text_input("Notes (optional)")
            save_split = st.form_submit_button("Save Split", use_container_width=True)

        if save_split:
            try:
                split_asset_id = split_asset_options[split_asset_label]

                cursor.execute(
                    """
                    SELECT id
                    FROM corporate_actions
                    WHERE asset_id = %s
                      AND action_date = %s
                      AND action_type = 'SPLIT'
                      AND ratio_new = %s
                      AND ratio_old = %s
                    LIMIT 1;
                    """,
                    (split_asset_id, split_date, ratio_new, ratio_old),
                )

                if cursor.fetchone():
                    raise ValueError("That stock split already exists.")

                cursor.execute(
                    """
                    INSERT INTO corporate_actions (
                        asset_id, action_date, action_type, ratio_new, ratio_old, notes
                    )
                    VALUES (%s, %s, 'SPLIT', %s, %s, %s);
                    """,
                    (split_asset_id, split_date, ratio_new, ratio_old, split_notes or None),
                )
                connection.commit()
                st.session_state["split_added"] = "✅ Stock split saved."
                st.rerun()

            except Exception as error:
                connection.rollback()
                st.sidebar.error(f"Could not save stock split: {error}")

if "split_added" in st.session_state:
    st.sidebar.success(st.session_state.pop("split_added"))


# ============================================================
# 9. SIDEBAR: REFRESH MARKET DATA
# ============================================================

st.sidebar.divider()
st.sidebar.subheader("Market Data")

if st.sidebar.button("🔄 Refresh Prices", use_container_width=True):
    with st.spinner("Updating market data..."):
        updated_assets = 0
        refresh_errors = []

        for _, asset in assets.iterrows():
            market_symbol = asset["market_symbol"]
            if pd.isna(market_symbol) or not str(market_symbol).strip():
                continue

            try:

                if (
                    clean_text(
                        asset.get(
                            "asset_type",
                            ""
                        )
                    ).upper()
                    == "METAL"
                ):

                    latest_price, latest_date = (
                        current_metal_price_sek_per_gram(
                            market_symbol
                        )
                    )

                else:
                    history = yf.Ticker(
                        str(market_symbol)
                    ).history(
                        period="5d"
                    )

                    if (
                        history.empty
                        or "Close"
                        not in history.columns
                    ):
                        st.warning(
                            f"No price data found for "
                            f"{asset['ticker']} "
                            f"({market_symbol})."
                        )
                        continue

                    valid_prices = (
                        history["Close"]
                        .dropna()
                    )

                    if valid_prices.empty:
                        st.warning(
                            f"No valid closing price "
                            f"found for "
                            f"{asset['ticker']} "
                            f"({market_symbol})."
                        )
                        continue

                    latest_price = float(
                        valid_prices.iloc[-1]
                    )

                    latest_date = (
                        valid_prices.index[-1]
                        .date()
                    )

                cursor.execute(
                    """
                    INSERT INTO prices (asset_id, price_date, close_price, currency)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        close_price = VALUES(close_price),
                        currency = VALUES(currency);
                    """,
                    (int(asset["id"]), latest_date, latest_price, asset["currency"]),
                )
                updated_assets += 1

            except Exception as error:
                refresh_errors.append(
                    f"{asset['ticker']}: {error}"
                )

        today = date.today()
        cursor.execute(
            """
            INSERT INTO fx_rates (currency, rate_date, sek_per_unit)
            VALUES ('SEK', %s, 1)
            ON DUPLICATE KEY UPDATE sek_per_unit = 1;
            """,
            (today,),
        )

        for currency in assets.get("currency", pd.Series(dtype=str)).dropna().unique():
            if currency == "SEK":
                continue
            try:
                fx_rate, fx_date = fetch_fx_from_yahoo(currency, today)
                cursor.execute(
                    """
                    INSERT INTO fx_rates (currency, rate_date, sek_per_unit)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sek_per_unit = VALUES(sek_per_unit);
                    """,
                    (currency, fx_date, fx_rate),
                )
            except Exception as error:
                refresh_errors.append(
                    f"{currency}/SEK: {error}"
                )

        connection.commit()
        st.session_state["prices_refreshed"] = (
            f"✅ Updated {updated_assets} asset(s)."
        )

        st.session_state[
            "price_refresh_errors"
        ] = refresh_errors

        st.rerun()

if "prices_refreshed" in st.session_state:
    st.sidebar.success(
        st.session_state.pop("prices_refreshed")
    )

if "price_refresh_errors" in st.session_state:
    saved_refresh_errors = (
        st.session_state.pop(
            "price_refresh_errors"
        )
    )

    if saved_refresh_errors:
        with st.sidebar.expander(
            "⚠️ Price refresh errors",
            expanded=True,
        ):
            for refresh_error in saved_refresh_errors:
                st.error(
                    refresh_error
                )


# ============================================================
# 10. SIDEBAR: ADD MANUAL BUY / SELL
# ============================================================

st.sidebar.divider()
st.sidebar.subheader("Add Transaction")

if assets.empty:
    st.sidebar.info("Add an investment before adding transactions.")
elif accounts.empty:
    st.sidebar.info("Create an account before adding transactions.")
else:
    asset_options = {
        f"{row['name']} ({row['ticker']})": {
            "id": int(row["id"]),
            "name": row["name"],
            "ticker": row["ticker"],
            "currency": row["currency"],
            "asset_type": row["asset_type"],
        }
        for _, row in assets.iterrows()
    }

    account_options = {
        f"{row['broker']} — {row['account_name']} ({row['account_type']})": int(row["id"])
        for _, row in accounts.iterrows()
    }

    with st.sidebar.form("transaction_form", clear_on_submit=False):
        selected_account_label = st.selectbox("Account", list(account_options.keys()))
        selected_label = st.selectbox("Investment", list(asset_options.keys()))
        selected_asset = asset_options[selected_label]
        transaction_type = st.selectbox(
            "Transaction Type",
            ["BUY", "SELL"]
        )

        is_metal_transaction = (
            clean_text(
                selected_asset.get(
                    "asset_type",
                    ""
                )
            ).upper()
            == "METAL"
        )

        quantity_label = (
            "Quantity (grams)"
            if is_metal_transaction
            else "Quantity"
        )

        price_label = (
            "Purchase price per gram (SEK)"
            if is_metal_transaction
            else (
                f"Price per unit "
                f"({selected_asset['currency']})"
            )
        )

        quantity = st.number_input(
            quantity_label,
            min_value=0.0,
            step=(
                0.1
                if is_metal_transaction
                else 1.0
            ),
            format="%.6f",
        )

        price = st.number_input(
            price_label,
            min_value=0.0,
            step=1.0,
            format="%.4f",
        )
        fees = st.number_input(
            f"Fees ({selected_asset['currency']})",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
        )
        transaction_date = st.date_input(
            "Transaction Date",
            value=date.today(),
            max_value=date.today(),
        )
        save_transaction = st.form_submit_button("Save Transaction", use_container_width=True)

    if save_transaction:
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero.")
            if price <= 0:
                raise ValueError("Price must be greater than zero.")

            account_id = account_options[selected_account_label]
            asset_id = selected_asset["id"]
            currency = selected_asset["currency"]

            if transaction_type == "SELL":
                shares_owned = calculate_shares_as_of(asset_id, account_id, transaction_date)
                if quantity > shares_owned + 1e-9:
                    unit_word = (
                        "grams"
                        if is_metal_transaction
                        else "units"
                    )
                    raise ValueError(
                        f"You only own "
                        f"{shares_owned:g} "
                        f"{unit_word} in this account."
                    )

            fx_rate = get_fx_rate_to_sek(currency, transaction_date)

            cursor.execute(
                """
                INSERT INTO transactions (
                    asset_id,
                    account_id,
                    transaction_type,
                    quantity,
                    price,
                    fees,
                    transaction_date,
                    fx_rate_to_sek,
                    source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'MANUAL');
                """,
                (
                    asset_id,
                    account_id,
                    transaction_type,
                    quantity,
                    price,
                    fees,
                    transaction_date,
                    fx_rate,
                ),
            )

            # Metals should become visible immediately after the
            # transaction is saved. Fetch/store a current SEK/gram
            # market quote now instead of requiring a separate
            # Refresh Prices click.
            metal_price_note = ""

            if is_metal_transaction:
                market_symbol = None

                cursor.execute(
                    """
                    SELECT market_symbol
                    FROM assets
                    WHERE id = %s;
                    """,
                    (asset_id,),
                )

                symbol_row = cursor.fetchone()

                if symbol_row:
                    market_symbol = symbol_row.get(
                        "market_symbol"
                    )

                if market_symbol:
                    try:
                        latest_metal_price, latest_metal_date = (
                            current_metal_price_sek_per_gram(
                                market_symbol
                            )
                        )

                        cursor.execute(
                            """
                            INSERT INTO prices (
                                asset_id,
                                price_date,
                                close_price,
                                adjusted_close_price,
                                currency
                            )
                            VALUES (
                                %s, %s, %s, %s, 'SEK'
                            )
                            ON DUPLICATE KEY UPDATE
                                close_price = VALUES(close_price),
                                adjusted_close_price =
                                    VALUES(adjusted_close_price),
                                currency = 'SEK';
                            """,
                            (
                                asset_id,
                                latest_metal_date,
                                latest_metal_price,
                                latest_metal_price,
                            ),
                        )

                        metal_price_note = (
                            f" Current metal price: "
                            f"{latest_metal_price:,.2f} SEK/g."
                        )

                    except Exception as metal_error:
                        metal_price_note = (
                            " Position saved, but the current "
                            "metal price could not be downloaded. "
                            "Use Refresh Prices. "
                            f"({metal_error})"
                        )

            connection.commit()

            st.session_state["manual_transaction_saved"] = (
                f"✅ {transaction_type} saved. "
                f"FX: {fx_rate:.4f}."
                f"{metal_price_note}"
            )
            st.rerun()

        except Exception as error:
            connection.rollback()
            st.sidebar.error(f"Could not save transaction: {error}")

if "manual_transaction_saved" in st.session_state:
    st.sidebar.success(st.session_state.pop("manual_transaction_saved"))


# ============================================================
# 11. LOAD TRANSACTIONS + AUTOMATIC HISTORICAL FX
# ============================================================

transactions = query_dataframe(
    """
    SELECT
        t.id,
        t.asset_id,
        t.account_id,
        COALESCE(
            CONCAT(ac.broker, ' — ', ac.account_name),
            'Unassigned'
        ) AS account,
        a.name,
        a.ticker,
        a.currency,
        t.transaction_type,
        t.quantity,
        t.price,
        t.fees,
        t.transaction_date,
        t.fx_rate_to_sek,
        t.source,
        t.external_transaction_id,
        t.transaction_hash,
        t.import_batch_id
    FROM transactions t
    JOIN assets a ON t.asset_id = a.id
    LEFT JOIN accounts ac ON t.account_id = ac.id
    ORDER BY t.asset_id, t.account_id, t.transaction_date, t.id;
    """
)

if not transactions.empty:
    missing_fx = transactions[transactions["fx_rate_to_sek"].isna()].copy()

    if not missing_fx.empty:
        with st.spinner(f"Updating historical FX for {len(missing_fx)} transaction(s)..."):
            try:
                for _, row in missing_fx.iterrows():
                    transaction_id = int(row["id"])
                    tx_date = as_date(row["transaction_date"])
                    fx_rate = get_fx_rate_to_sek(row["currency"], tx_date)

                    cursor.execute(
                        """
                        UPDATE transactions
                        SET fx_rate_to_sek = %s
                        WHERE id = %s;
                        """,
                        (fx_rate, transaction_id),
                    )

                    transactions.loc[
                        transactions["id"] == transaction_id,
                        "fx_rate_to_sek",
                    ] = fx_rate

                connection.commit()
                st.success("Historical FX rates updated.")

            except Exception as error:
                connection.rollback()
                st.error(f"Could not complete historical FX update: {error}")
                cursor.close()
                connection.close()
                st.stop()


# ============================================================
# 12. LOAD CORPORATE ACTIONS + BUILD PORTFOLIO LEDGER
# ============================================================

corporate_actions = query_dataframe(
    """
    SELECT
        id, asset_id, action_date, action_type, ratio_new, ratio_old, notes,
        import_batch_id, source
    FROM corporate_actions
    ORDER BY asset_id, action_date, id;
    """
)

try:
    current_positions = build_portfolio_states(transactions, corporate_actions)
except ValueError as error:
    st.error(str(error))
    cursor.close()
    connection.close()
    st.stop()

realized_pl_all = (
    pd.to_numeric(current_positions["total_realized_pl_sek"], errors="coerce")
    .fillna(0)
    .sum()
    if not current_positions.empty
    else 0.0
)


# ============================================================
# 13. LOAD LATEST MARKET PRICES + CURRENT FX
# ============================================================

latest_prices = query_dataframe(
    """
    SELECT p.asset_id, p.close_price, p.price_date
    FROM prices p
    JOIN (
        SELECT asset_id, MAX(price_date) AS latest_date
        FROM prices
        GROUP BY asset_id
    ) latest
      ON p.asset_id = latest.asset_id
     AND p.price_date = latest.latest_date;
    """
)

latest_fx = query_dataframe(
    """
    SELECT fx.currency, fx.sek_per_unit, fx.rate_date
    FROM fx_rates fx
    JOIN (
        SELECT currency, MAX(rate_date) AS latest_date
        FROM fx_rates
        GROUP BY currency
    ) latest
      ON fx.currency = latest.currency
     AND fx.rate_date = latest.latest_date;
    """
)

# SEK is always exactly 1, even before the first manual refresh.
if latest_fx.empty or "SEK" not in latest_fx.get("currency", pd.Series(dtype=str)).values:
    latest_fx = pd.concat(
        [
            latest_fx,
            pd.DataFrame(
                [{"currency": "SEK", "sek_per_unit": 1.0, "rate_date": date.today()}]
            ),
        ],
        ignore_index=True,
    )


# ============================================================
# 14. BUILD CURRENT PORTFOLIO
# ============================================================

if current_positions.empty:
    portfolio = pd.DataFrame()
else:
    portfolio = current_positions.merge(latest_prices, on="asset_id", how="left")
    portfolio = portfolio.merge(latest_fx, on="currency", how="left")

    numeric_columns = [
        "shares_after",
        "cost_basis_after_sek",
        "average_cost_after_sek",
        "total_realized_pl_sek",
        "close_price",
        "sek_per_unit",
    ]

    for column in numeric_columns:
        if column in portfolio.columns:
            portfolio[column] = pd.to_numeric(portfolio[column], errors="coerce")

    portfolio = portfolio[portfolio["shares_after"] > 1e-9].copy()

    portfolio["market_value_sek"] = (
        portfolio["shares_after"]
        * portfolio["close_price"]
        * portfolio["sek_per_unit"]
    )

    portfolio["unrealized_pl_sek"] = (
        portfolio["market_value_sek"] - portfolio["cost_basis_after_sek"]
    )


# ============================================================
# 15. LOAD DIVIDENDS
# ============================================================

dividend_data = query_dataframe(
    """
    SELECT
        asset_id,
        COALESCE(account_id, 0) AS account_key,
        SUM(dividend_per_share * shares_held * fx_rate_to_sek) AS dividends_sek
    FROM dividends
    GROUP BY asset_id, COALESCE(account_id, 0);
    """
)

if not dividend_data.empty:
    dividend_data["account_key"] = dividend_data["account_key"].astype(int)
    dividend_data["dividends_sek"] = pd.to_numeric(
        dividend_data["dividends_sek"], errors="coerce"
    ).fillna(0.0)
    total_dividends_all = float(dividend_data["dividends_sek"].sum())
else:
    total_dividends_all = 0.0

if not portfolio.empty:
    if dividend_data.empty:
        portfolio["dividends_sek"] = 0.0
    else:
        portfolio = portfolio.merge(
            dividend_data,
            on=["asset_id", "account_key"],
            how="left",
        )
        portfolio["dividends_sek"] = portfolio["dividends_sek"].fillna(0.0)


# ============================================================
# 15B. LOAD CURRENT CASH BALANCES
# ============================================================

cash_movements = query_dataframe(
    """
    SELECT
        cm.id,
        cm.account_id,
        CONCAT(ac.broker, ' — ', ac.account_name) AS account,
        cm.movement_date,
        cm.movement_type,
        cm.description,
        cm.amount,
        cm.currency,
        cm.fx_rate_to_sek,
        cm.source
    FROM cash_movements cm
    JOIN accounts ac ON cm.account_id = ac.id
    ORDER BY cm.movement_date, cm.id;
    """
)

cash_balances = pd.DataFrame(
    columns=["account_id", "account", "currency", "cash_amount", "current_fx", "cash_value_sek"]
)

total_cash_sek = 0.0

if not cash_movements.empty:
    cash_movements["amount"] = pd.to_numeric(
        cash_movements["amount"], errors="coerce"
    ).fillna(0.0)

    cash_balances = (
        cash_movements.groupby(["account_id", "account", "currency"], as_index=False)
        .agg(cash_amount=("amount", "sum"))
    )

    current_fx_values = {}
    for currency in cash_balances["currency"].dropna().unique():
        currency = normalize_currency(currency)
        if currency == "SEK":
            current_fx_values[currency] = 1.0
            continue

        fx_match = latest_fx[latest_fx["currency"] == currency]
        if not fx_match.empty:
            current_fx_values[currency] = float(fx_match.iloc[0]["sek_per_unit"])
        else:
            try:
                current_fx_values[currency] = get_fx_rate_to_sek(currency, date.today())
            except Exception as error:
                st.warning(f"Could not value {currency} cash in SEK: {error}")
                current_fx_values[currency] = None

    cash_balances["current_fx"] = cash_balances["currency"].map(current_fx_values)
    cash_balances["cash_value_sek"] = (
        cash_balances["cash_amount"]
        * pd.to_numeric(cash_balances["current_fx"], errors="coerce")
    )
    total_cash_sek = float(cash_balances["cash_value_sek"].sum(skipna=True))


# ============================================================
# 16. CALCULATE PORTFOLIO METRICS
# ============================================================

if portfolio.empty:
    portfolio_value = 0.0
    remaining_cost_basis = 0.0
    unrealized_pl = 0.0
    current_return_percent = 0.0
else:
    portfolio["total_gain_sek"] = (
        portfolio["total_realized_pl_sek"]
        + portfolio["unrealized_pl_sek"]
        + portfolio["dividends_sek"]
    )

    portfolio["return_percent"] = portfolio.apply(
        lambda row: (
            row["unrealized_pl_sek"] / row["cost_basis_after_sek"] * 100
            if row["cost_basis_after_sek"] > 0
            else 0.0
        ),
        axis=1,
    )

    portfolio_value = float(portfolio["market_value_sek"].sum(skipna=True))
    remaining_cost_basis = float(portfolio["cost_basis_after_sek"].sum(skipna=True))
    unrealized_pl = float(portfolio["unrealized_pl_sek"].sum(skipna=True))

    portfolio["weight_percent"] = (
        portfolio["market_value_sek"] / portfolio_value * 100
        if portfolio_value > 0
        else 0.0
    )

    current_return_percent = (
        unrealized_pl / remaining_cost_basis * 100
        if remaining_cost_basis > 0
        else 0.0
    )

total_gain = unrealized_pl + realized_pl_all + total_dividends_all
total_account_value = portfolio_value + total_cash_sek


# ============================================================
# 16B. HELPER FUNCTIONS FOR THE PORTFOLIO OVERVIEW
# ============================================================

def format_sek_compact(value):
    value = float(value or 0)
    return f"{value:,.0f} SEK"

def build_portfolio_timeseries(transactions_df, cash_df, assets_df, latest_fx_df):
    """
    Approximate daily portfolio value:
    - security value = cumulative shares * daily close * daily FX
    - cash value = cumulative cash movements * daily FX
    """
    price_history = query_dataframe(
        """
        SELECT asset_id, price_date, close_price
        FROM prices
        ORDER BY asset_id, price_date;
        """
    )

    fx_history = query_dataframe(
        """
        SELECT currency, rate_date, sek_per_unit
        FROM fx_rates
        ORDER BY currency, rate_date;
        """
    )

    if price_history.empty and cash_df.empty:
        return pd.DataFrame(columns=["date", "total_value_sek"])

    all_start_dates = []

    if not transactions_df.empty:
        tmp_tx_dates = pd.to_datetime(transactions_df["transaction_date"], errors="coerce").dropna()
        if not tmp_tx_dates.empty:
            all_start_dates.append(tmp_tx_dates.min())

    if not cash_df.empty:
        tmp_cash_dates = pd.to_datetime(cash_df["movement_date"], errors="coerce").dropna()
        if not tmp_cash_dates.empty:
            all_start_dates.append(tmp_cash_dates.min())

    if not price_history.empty:
        tmp_price_dates = pd.to_datetime(price_history["price_date"], errors="coerce").dropna()
        if not tmp_price_dates.empty:
            all_start_dates.append(tmp_price_dates.min())

    if not all_start_dates:
        return pd.DataFrame(columns=["date", "total_value_sek"])

    start_date = min(all_start_dates).normalize()
    end_date = pd.Timestamp.today().normalize()
    calendar = pd.DataFrame({"date": pd.date_range(start_date, end_date, freq="D")})

    total_series = pd.DataFrame({"date": calendar["date"], "total_value_sek": 0.0})

    # ---------- Holdings ----------
    if not transactions_df.empty and not price_history.empty:
        tx = transactions_df.copy()
        tx["transaction_date"] = pd.to_datetime(tx["transaction_date"], errors="coerce").dt.normalize()
        tx["quantity"] = pd.to_numeric(tx["quantity"], errors="coerce").fillna(0.0)
        tx["transaction_type"] = tx["transaction_type"].astype(str).str.upper().str.strip()
        tx = tx[tx["transaction_type"].isin(["BUY", "SELL"])].copy()

        if not tx.empty:
            tx["signed_quantity"] = tx["quantity"]
            tx.loc[tx["transaction_type"] == "SELL", "signed_quantity"] *= -1

            price_history_local = price_history.copy()
            price_history_local["price_date"] = pd.to_datetime(
                price_history_local["price_date"], errors="coerce"
            ).dt.normalize()
            price_history_local["close_price"] = pd.to_numeric(
                price_history_local["close_price"], errors="coerce"
            )

            asset_meta = assets_df[["id", "currency"]].copy()
            asset_meta["currency"] = asset_meta["currency"].fillna("SEK").astype(str).str.upper()

            fx_history_local = fx_history.copy()
            fx_history_local["rate_date"] = pd.to_datetime(
                fx_history_local["rate_date"], errors="coerce"
            ).dt.normalize()
            fx_history_local["currency"] = fx_history_local["currency"].fillna("SEK").astype(str).str.upper()
            fx_history_local["sek_per_unit"] = pd.to_numeric(
                fx_history_local["sek_per_unit"], errors="coerce"
            )

            if "SEK" not in fx_history_local["currency"].unique():
                fx_history_local = pd.concat(
                    [
                        fx_history_local,
                        pd.DataFrame(
                            {
                                "currency": ["SEK"],
                                "rate_date": [calendar["date"].min()],
                                "sek_per_unit": [1.0],
                            }
                        ),
                    ],
                    ignore_index=True,
                )

            for asset_id in tx["asset_id"].dropna().unique():
                asset_tx = tx[tx["asset_id"] == asset_id].copy()
                if asset_tx.empty:
                    continue

                shares_daily = (
                    asset_tx.groupby("transaction_date", as_index=False)["signed_quantity"]
                    .sum()
                    .rename(columns={"transaction_date": "date"})
                )

                shares_series = calendar.merge(shares_daily, on="date", how="left")
                shares_series["signed_quantity"] = shares_series["signed_quantity"].fillna(0.0)
                shares_series["shares_held"] = shares_series["signed_quantity"].cumsum()

                asset_prices = price_history_local[price_history_local["asset_id"] == asset_id].copy()
                if asset_prices.empty:
                    continue

                asset_prices = (
                    asset_prices.groupby("price_date", as_index=False)["close_price"]
                    .last()
                    .rename(columns={"price_date": "date"})
                )

                asset_series = shares_series.merge(asset_prices, on="date", how="left")
                asset_series["close_price"] = asset_series["close_price"].ffill()

                currency_match = asset_meta.loc[asset_meta["id"] == asset_id, "currency"]
                asset_currency = (
                    currency_match.iloc[0] if not currency_match.empty else "SEK"
                )

                if asset_currency == "SEK":
                    asset_series["sek_per_unit"] = 1.0
                else:
                    asset_fx = fx_history_local[fx_history_local["currency"] == asset_currency].copy()
                    asset_fx = (
                        asset_fx.groupby("rate_date", as_index=False)["sek_per_unit"]
                        .last()
                        .rename(columns={"rate_date": "date"})
                    )
                    asset_series = asset_series.merge(asset_fx, on="date", how="left")
                    asset_series["sek_per_unit"] = asset_series["sek_per_unit"].ffill()

                asset_series["market_value_sek"] = (
                    asset_series["shares_held"]
                    * asset_series["close_price"].ffill()
                    * asset_series["sek_per_unit"].fillna(1.0)
                )

                total_series["total_value_sek"] += asset_series["market_value_sek"].fillna(0.0)

    # ---------- Cash ----------
    if not cash_df.empty:
        cash_local = cash_df.copy()
        cash_local["movement_date"] = pd.to_datetime(
            cash_local["movement_date"], errors="coerce"
        ).dt.normalize()
        cash_local["amount"] = pd.to_numeric(cash_local["amount"], errors="coerce").fillna(0.0)
        cash_local["currency"] = cash_local["currency"].fillna("SEK").astype(str).str.upper()

        fx_history_local = fx_history.copy()
        fx_history_local["rate_date"] = pd.to_datetime(
            fx_history_local["rate_date"], errors="coerce"
        ).dt.normalize()
        fx_history_local["currency"] = fx_history_local["currency"].fillna("SEK").astype(str).str.upper()
        fx_history_local["sek_per_unit"] = pd.to_numeric(
            fx_history_local["sek_per_unit"], errors="coerce"
        )

        if "SEK" not in fx_history_local["currency"].unique():
            fx_history_local = pd.concat(
                [
                    fx_history_local,
                    pd.DataFrame(
                        {"currency": ["SEK"], "rate_date": [calendar["date"].min()], "sek_per_unit": [1.0]}
                    ),
                ],
                ignore_index=True,
            )

        for currency in cash_local["currency"].dropna().unique():
            currency_cash = cash_local[cash_local["currency"] == currency].copy()
            if currency_cash.empty:
                continue

            cash_daily = (
                currency_cash.groupby("movement_date", as_index=False)["amount"]
                .sum()
                .rename(columns={"movement_date": "date"})
            )

            cash_series = calendar.merge(cash_daily, on="date", how="left")
            cash_series["amount"] = cash_series["amount"].fillna(0.0)
            cash_series["cash_balance"] = cash_series["amount"].cumsum()

            if currency == "SEK":
                cash_series["sek_per_unit"] = 1.0
            else:
                currency_fx = fx_history_local[fx_history_local["currency"] == currency].copy()
                currency_fx = (
                    currency_fx.groupby("rate_date", as_index=False)["sek_per_unit"]
                    .last()
                    .rename(columns={"rate_date": "date"})
                )
                cash_series = cash_series.merge(currency_fx, on="date", how="left")
                cash_series["sek_per_unit"] = cash_series["sek_per_unit"].ffill()

            cash_series["cash_value_sek"] = (
                cash_series["cash_balance"] * cash_series["sek_per_unit"].fillna(1.0)
            )

            total_series["total_value_sek"] += cash_series["cash_value_sek"].fillna(0.0)

    return total_series


def filter_timeseries_window(df, period_key):
    if df.empty:
        return df

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    latest_date = df["date"].max()

    if pd.isna(latest_date):
        return df

    if period_key == "1M":
        start = latest_date - pd.DateOffset(months=1)
    elif period_key == "3M":
        start = latest_date - pd.DateOffset(months=3)
    elif period_key == "6M":
        start = latest_date - pd.DateOffset(months=6)
    elif period_key == "YTD":
        start = pd.Timestamp(year=latest_date.year, month=1, day=1)
    elif period_key == "1Y":
        start = latest_date - pd.DateOffset(years=1)
    else:
        start = df["date"].min()

    return df[df["date"] >= start].copy()



# ============================================================
# 17. PORTFOLIO OVERVIEW (STYLED LIKE THE REFERENCE)
# ============================================================

# Current account values
account_base = accounts[["id", "broker", "account_name"]].copy()
account_base["account_id"] = account_base["id"].astype(int)
account_base["Account"] = (
    account_base["broker"].astype(str)
    + " — "
    + account_base["account_name"].astype(str)
)

if not portfolio.empty:
    account_investments = (
        portfolio.groupby("account_id", as_index=False)
        .agg(
            Investments=("market_value_sek", "sum"),
            Holdings=("asset_id", "nunique"),
        )
    )
else:
    account_investments = pd.DataFrame(
        columns=["account_id", "Investments", "Holdings"]
    )

if not cash_balances.empty:
    account_cash = (
        cash_balances.groupby("account_id", as_index=False)
        .agg(Cash=("cash_value_sek", "sum"))
    )
else:
    account_cash = pd.DataFrame(
        columns=["account_id", "Cash"]
    )

account_values = (
    account_base[["account_id", "Account"]]
    .merge(account_investments, on="account_id", how="left")
    .merge(account_cash, on="account_id", how="left")
)

for col in ["Investments", "Cash", "Holdings"]:
    account_values[col] = pd.to_numeric(
        account_values[col], errors="coerce"
    ).fillna(0.0)

account_values["Total Worth"] = account_values["Investments"] + account_values["Cash"]
account_values = account_values.sort_values("Total Worth", ascending=False)

# Portfolio time series
portfolio_ts = build_portfolio_history_series(
    transactions_df=transactions,
    cash_df=cash_movements,
    assets_df=assets,
)

time_period = st.radio(
    "Overview range",
    ["1M", "3M", "6M", "YTD", "1Y", "ALL"],
    horizontal=True,
    key="portfolio_time_range",
    label_visibility="collapsed",
)

portfolio_ts_window = filter_timeseries_window(portfolio_ts, time_period)
if portfolio_ts_window.empty:
    overview_current_value = total_account_value
    overview_start_value = total_account_value
else:
    overview_current_value = float(portfolio_ts_window["total_value_sek"].iloc[-1])
    overview_start_value = float(portfolio_ts_window["total_value_sek"].iloc[0])

overview_change = overview_current_value - overview_start_value
overview_change_pct = (
    overview_change / overview_start_value * 100
    if overview_start_value not in (0, None)
    else 0.0
)

range_labels = {
    "1M": "past 1 month",
    "3M": "past 3 months",
    "6M": "past 6 months",
    "YTD": "year to date",
    "1Y": "past 1 year",
    "ALL": "full history",
}
range_label = range_labels.get(time_period, "selected period")

st.markdown(
    """
    <div class="portfolio-shell">
        <div class="shell-nav">
            <span class="shell-pill is-active">Investments</span>
            <span class="shell-pill">Accounts</span>
            <span class="shell-pill">Overview</span>
        </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero-total">{format_sek_compact(total_account_value)}</div>
    <div class="hero-delta">
        {overview_change:+,.0f} SEK
        <span class="hero-subline">{overview_change_pct:+.2f}% {range_label}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if portfolio_ts_window.empty:
    st.info("No historical portfolio data available yet for the overview chart.")
else:
    chart_df = portfolio_ts_window.copy()
    chart_df["date"] = pd.to_datetime(chart_df["date"], errors="coerce")

    overview_chart = px.area(
        chart_df,
        x="date",
        y="total_value_sek",
    )
    overview_chart.update_traces(
        line=dict(color="#95a449", width=2.5),
        fillcolor="rgba(149, 164, 73, 0.22)",
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f} SEK<extra></extra>",
    )
    overview_chart.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="",
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(color="#7d776b"),
        ),
        yaxis=dict(
            title="",
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(color="#7d776b"),
        ),
        showlegend=False,
        hovermode="x unified",
    )
    st.plotly_chart(overview_chart, use_container_width=True)

st.markdown('<div class="section-title">Accounts</div>', unsafe_allow_html=True)

if account_values.empty:
    st.info("Create an account in the sidebar to see the account list here.")
else:
    for _, row in account_values.iterrows():
        holdings_text = (
            f"{int(row['Holdings'])} holding{'s' if int(row['Holdings']) != 1 else ''}"
            if row["Holdings"] > 0
            else "No active holdings"
        )

        subvalue = (
            f"Investments {row['Investments']:,.0f} SEK • Cash {row['Cash']:,.2f} SEK"
        )
        safe_account_name = html.escape(clean_text(row["Account"]))

        st.markdown(
            f"""
            <div class="account-card">
                <div class="account-card-top">
                    <div>
                        <div class="account-name">{safe_account_name}</div>
                        <div class="account-meta">{holdings_text}</div>
                    </div>
                    <div>
                        <div class="account-value">{row['Total Worth']:,.0f} SEK</div>
                        <div class="account-subvalue">{subvalue}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# 17B. PORTFOLIO RISK ANALYTICS
# ============================================================

st.subheader("Portfolio Analytics — Investments Only")

ensure_default_benchmarks()

risk_lookback = st.radio(
    "Risk analytics period",
    ["1Y", "3Y", "5Y", "ALL"],
    horizontal=True,
    key="risk_analytics_period",
    label_visibility="collapsed",
)

benchmark_history = build_benchmark_series()
risk_free_history = build_risk_free_daily_series()

investment_return_history = build_invested_portfolio_return_series(
    transactions_df=transactions,
    assets_df=assets,
    benchmark_history=benchmark_history,
)

# Precious-metals-only return history.
metal_asset_ids = (
    assets.loc[
        assets["asset_type"]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq("METAL"),
        "id",
    ]
    .dropna()
    .astype(int)
    .tolist()
)

metal_assets_df = assets[
    assets["id"].isin(metal_asset_ids)
].copy()

metal_transactions_df = transactions[
    transactions["asset_id"].isin(metal_asset_ids)
].copy()

metal_return_history = build_invested_portfolio_return_series(
    transactions_df=metal_transactions_df,
    assets_df=metal_assets_df,
    benchmark_history=benchmark_history,
)

risk_metrics, risk_daily = calculate_portfolio_risk_analytics(
    portfolio_return_history=investment_return_history,
    benchmark_history=benchmark_history,
    risk_free_history=risk_free_history,
    lookback=risk_lookback,
)

# Historical coverage for CURRENT holdings.
current_asset_ids = (
    pd.to_numeric(
        portfolio.get(
            "asset_id",
            pd.Series(dtype=float),
        ),
        errors="coerce",
    )
    .dropna()
    .astype(int)
    .unique()
    .tolist()
    if not portfolio.empty
    else []
)

historical_coverage = query_dataframe(
    """
    SELECT
        a.id AS asset_id,
        a.name,
        a.ticker,
        COUNT(p.id) AS observations
    FROM assets a
    LEFT JOIN prices p
      ON p.asset_id = a.id
    GROUP BY a.id, a.name, a.ticker;
    """
)

if current_asset_ids and not historical_coverage.empty:
    current_coverage = historical_coverage[
        historical_coverage["asset_id"].isin(
            current_asset_ids
        )
    ].copy()

    covered_holdings = int(
        (
            pd.to_numeric(
                current_coverage["observations"],
                errors="coerce",
            ).fillna(0)
            >= 30
        ).sum()
    )

    total_holdings_for_coverage = len(
        current_asset_ids
    )

else:
    covered_holdings = 0
    total_holdings_for_coverage = 0

if risk_metrics is None:
    st.info(
        "Risk analytics need at least 30 overlapping daily observations "
        "for the portfolio and ACWI. If you just downloaded history, "
        "rerun/refresh the page once."
    )

else:
    m1, m2, m3, m4 = st.columns(4)

    sharpe_value = risk_metrics["sharpe"]

    m1.metric(
        "Sharpe Ratio",
        (
            f"{sharpe_value:.2f}"
            if pd.notna(sharpe_value)
            else "N/A"
        ),
    )

    m2.metric(
        "Beta vs ACWI",
        f"{risk_metrics['beta']:.2f}",
    )

    m3.metric(
        "Annualized Return",
        f"{risk_metrics['annualized_return'] * 100:+.2f}%",
    )

    m4.metric(
        "Annualized Volatility",
        f"{risk_metrics['annualized_volatility'] * 100:.2f}%",
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Max Drawdown",
        f"{risk_metrics['max_drawdown'] * 100:.2f}%",
    )

    m2.metric(
        "Correlation vs ACWI",
        f"{risk_metrics['correlation']:.2f}",
    )

    m3.metric(
        "Daily Observations",
        f"{risk_metrics['observations']:,}",
    )

    m4.metric(
        "Historical Coverage",
        (
            f"{covered_holdings}/{total_holdings_for_coverage}"
            if total_holdings_for_coverage
            else "N/A"
        ),
    )

    st.caption(
        f"Period: {risk_metrics['start_date']:%Y-%m-%d} to "
        f"{risk_metrics['end_date']:%Y-%m-%d}. "
        "Risk analytics use holdings-weighted investment returns only. "
        "Cash, deposits, withdrawals and transfers are excluded. "
        "Benchmark: iShares MSCI ACWI ETF (ACWI), converted to SEK."
    )

    if risk_metrics["risk_free_available"]:
        st.caption(
            "Sharpe risk-free proxy: Swedish 3-month Treasury bill "
            "(SETB3MBENCH). Source: Sveriges Riksbank."
        )
    else:
        st.warning(
            "Sharpe is unavailable until the Swedish 3-month Treasury-bill "
            "history has been downloaded. Open Tools & Imports → Historical Data "
            "and click Update Historical Data."
        )

    if (
        total_holdings_for_coverage
        and covered_holdings
        < total_holdings_for_coverage
    ):
        st.warning(
            "Not every current holding has at least 30 stored historical prices. "
            "Missing-price holdings are excluded from the return calculation on dates "
            "where no valid historical price exists, so results remain approximate until "
            "historical coverage is complete."
        )

    # --------------------------------------------------------
    # Portfolio vs market benchmarks
    # --------------------------------------------------------

    st.markdown("### Portfolio vs Benchmarks")

    comparison_data = build_benchmark_comparison(
        portfolio_return_history=investment_return_history,
        lookback=risk_lookback,
    )

    required_benchmarks = {
        "S&P 500",
        "OMXSPI",
    }

    present_series = set(
        comparison_data["Series"].unique()
    ) if not comparison_data.empty else set()

    missing_comparisons = (
        required_benchmarks
        - present_series
    )

    if comparison_data.empty:
        st.info(
            "No benchmark comparison data is stored yet. "
            "Go to Tools & Imports → Historical Data and click "
            "'Update Historical Data'."
        )

    else:
        comparison_chart = px.line(
            comparison_data,
            x="date",
            y="Growth of 100",
            color="Series",
            markers=False,
        )

        comparison_chart.update_layout(
            height=430,
            xaxis_title="",
            yaxis_title="Growth of 100",
            legend_title="",
            hovermode="x unified",
        )

        comparison_chart.update_traces(
            hovertemplate=(
                "%{x|%Y-%m-%d}<br>"
                "%{y:.2f}<extra>%{fullData.name}</extra>"
            )
        )

        st.plotly_chart(
            comparison_chart,
            use_container_width=True,
        )

        ending_values = (
            comparison_data
            .sort_values("date")
            .groupby("Series", as_index=False)
            .tail(1)
            .copy()
        )

        ending_values["Period Return"] = (
            ending_values["Growth of 100"]
            - 100.0
        )

        return_lookup = {
            row["Series"]: float(
                row["Period Return"]
            )
            for _, row in ending_values.iterrows()
        }

        c1, c2, c3 = st.columns(3)

        portfolio_period_return = (
            return_lookup.get(
                "Your Portfolio"
            )
        )

        sp500_period_return = (
            return_lookup.get(
                "S&P 500"
            )
        )

        omxspi_period_return = (
            return_lookup.get(
                "OMXSPI"
            )
        )

        c1.metric(
            "Your Portfolio",
            (
                f"{portfolio_period_return:+.2f}%"
                if portfolio_period_return is not None
                else "N/A"
            ),
        )

        c2.metric(
            "S&P 500",
            (
                f"{sp500_period_return:+.2f}%"
                if sp500_period_return is not None
                else "N/A"
            ),
            (
                f"{portfolio_period_return - sp500_period_return:+.2f} pp vs portfolio"
                if (
                    portfolio_period_return is not None
                    and sp500_period_return is not None
                )
                else None
            ),
            delta_color="off",
        )

        c3.metric(
            "OMXSPI",
            (
                f"{omxspi_period_return:+.2f}%"
                if omxspi_period_return is not None
                else "N/A"
            ),
            (
                f"{portfolio_period_return - omxspi_period_return:+.2f} pp vs portfolio"
                if (
                    portfolio_period_return is not None
                    and omxspi_period_return is not None
                )
                else None
            ),
            delta_color="off",
        )

        st.caption(
            "All series are normalized to 100 at the beginning of the selected "
            "period. S&P 500 is converted from USD into SEK, so the comparison "
            "also reflects USD/SEK movements. OMXSPI is already SEK-denominated."
        )

        st.caption(
            "S&P 500 and OMXSPI are price indices, so their index performance "
            "does not include reinvested dividends. Your portfolio investment "
            "return uses adjusted security prices where available."
        )

    if missing_comparisons:
        st.warning(
            "Missing stored history for: "
            + ", ".join(sorted(missing_comparisons))
            + ". Run 'Update Historical Data' once to download it."
        )

    # --------------------------------------------------------
    # Precious-metals performance
    # --------------------------------------------------------

    current_metal_positions = pd.DataFrame()

    if not portfolio.empty and metal_asset_ids:
        current_metal_positions = portfolio[
            portfolio["asset_id"].isin(
                metal_asset_ids
            )
        ].copy()

        current_metal_positions = current_metal_positions[
            pd.to_numeric(
                current_metal_positions["shares_after"],
                errors="coerce",
            ).fillna(0) > 1e-10
        ].copy()

    if not current_metal_positions.empty:
        st.markdown("### Precious Metals")

        metal_value_sek = float(
            pd.to_numeric(
                current_metal_positions[
                    "market_value_sek"
                ],
                errors="coerce",
            )
            .fillna(0.0)
            .sum()
        )

        invested_market_value = float(
            pd.to_numeric(
                portfolio[
                    "market_value_sek"
                ],
                errors="coerce",
            )
            .fillna(0.0)
            .sum()
        )

        metal_weight_pct = (
            metal_value_sek
            / invested_market_value
            * 100.0
            if invested_market_value > 0
            else 0.0
        )

        metal_unrealized = float(
            pd.to_numeric(
                current_metal_positions[
                    "unrealized_pl_sek"
                ],
                errors="coerce",
            )
            .fillna(0.0)
            .sum()
        )

        metal_cost_basis = float(
            pd.to_numeric(
                current_metal_positions[
                    "cost_basis_after_sek"
                ],
                errors="coerce",
            )
            .fillna(0.0)
            .sum()
        )

        metal_current_return_pct = (
            metal_unrealized
            / metal_cost_basis
            * 100.0
            if metal_cost_basis > 0
            else float("nan")
        )

        metals_by_name = (
            current_metal_positions
            .groupby(
                ["asset_id", "name", "ticker"],
                as_index=False,
            )
            .agg(
                market_value_sek=(
                    "market_value_sek",
                    "sum",
                ),
                quantity_grams=(
                    "shares_after",
                    "sum",
                ),
                unrealized_pl_sek=(
                    "unrealized_pl_sek",
                    "sum",
                ),
            )
        )

        mc1, mc2, mc3, mc4 = st.columns(4)

        mc1.metric(
            "Precious Metals Exposure",
            f"{metal_weight_pct:.2f}%",
        )

        mc2.metric(
            "Metals Value",
            f"{metal_value_sek:,.0f} SEK",
        )

        mc3.metric(
            "Current Metals Gain",
            f"{metal_unrealized:+,.0f} SEK",
        )

        mc4.metric(
            "Current Metals Return",
            (
                f"{metal_current_return_pct:+.2f}%"
                if pd.notna(
                    metal_current_return_pct
                )
                else "N/A"
            ),
        )

        # Compare the metal sleeve with the entire portfolio over the
        # same selected analytics period.
        metals_index = normalized_return_index(
            metal_return_history,
            "portfolio_return",
            "Precious Metals",
            risk_lookback,
        )

        portfolio_index_for_metals = (
            normalized_return_index(
                investment_return_history,
                "portfolio_return",
                "Your Portfolio",
                risk_lookback,
            )
        )

        metal_comparison_frames = []

        if not portfolio_index_for_metals.empty:
            metal_comparison_frames.append(
                portfolio_index_for_metals
            )

        if not metals_index.empty:
            metal_comparison_frames.append(
                metals_index
            )

        if metal_comparison_frames:
            metal_comparison = pd.concat(
                metal_comparison_frames,
                ignore_index=True,
            )

            metal_chart = px.line(
                metal_comparison,
                x="date",
                y="Growth of 100",
                color="Series",
            )

            metal_chart.update_layout(
                height=360,
                xaxis_title="",
                yaxis_title="Growth of 100",
                legend_title="",
                hovermode="x unified",
            )

            st.plotly_chart(
                metal_chart,
                use_container_width=True,
            )

            ending_metal_values = (
                metal_comparison
                .sort_values("date")
                .groupby(
                    "Series",
                    as_index=False,
                )
                .tail(1)
            )

            metal_return_lookup = {
                row["Series"]:
                    float(
                        row["Growth of 100"]
                        - 100.0
                    )
                for _, row
                in ending_metal_values.iterrows()
            }

            metal_period_return = (
                metal_return_lookup.get(
                    "Precious Metals"
                )
            )

            portfolio_period_for_metals = (
                metal_return_lookup.get(
                    "Your Portfolio"
                )
            )

            pm1, pm2 = st.columns(2)

            pm1.metric(
                f"Metals Return ({risk_lookback})",
                (
                    f"{metal_period_return:+.2f}%"
                    if metal_period_return
                    is not None
                    else "N/A"
                ),
            )

            pm2.metric(
                f"Portfolio Return ({risk_lookback})",
                (
                    f"{portfolio_period_for_metals:+.2f}%"
                    if portfolio_period_for_metals
                    is not None
                    else "N/A"
                ),
                (
                    f"{metal_period_return - portfolio_period_for_metals:+.2f} pp metals vs portfolio"
                    if (
                        metal_period_return
                        is not None
                        and portfolio_period_for_metals
                        is not None
                    )
                    else None
                ),
                delta_color="off",
            )

        else:
            st.info(
                "The precious-metals positions are visible in your "
                "portfolio, but there is not enough stored historical "
                "price data yet for a metals performance chart. "
                "Run Tools & Imports → Historical Data → "
                "Update Historical Data."
            )

        with st.expander(
            "🪙 Precious metals holdings"
        ):
            metal_display = (
                metals_by_name[
                    [
                        "name",
                        "ticker",
                        "quantity_grams",
                        "market_value_sek",
                        "unrealized_pl_sek",
                    ]
                ]
                .copy()
            )

            metal_display.columns = [
                "Metal",
                "Ticker",
                "Grams",
                "Market Value (SEK)",
                "Unrealized P/L (SEK)",
            ]

            st.dataframe(
                metal_display.style.format(
                    {
                        "Grams": "{:,.2f}",
                        "Market Value (SEK)": "{:,.0f}",
                        "Unrealized P/L (SEK)": "{:+,.0f}",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Precious-metals performance uses the same holdings-weighted "
            "investment-return method as the rest of Portfolio Analytics. "
            "Deposits, withdrawals and cash transfers are excluded."
        )

    with st.expander("📊 Risk metrics by current investment"):
        asset_metrics = calculate_asset_risk_metrics(
            current_portfolio=portfolio,
            benchmark_history=benchmark_history,
            risk_free_history=risk_free_history,
            lookback=risk_lookback,
        )

        if asset_metrics.empty:
            st.info(
                "No individual holdings have enough overlapping historical "
                "data yet."
            )
        else:
            st.dataframe(
                asset_metrics.style.format(
                    {
                        "Annualized Return": "{:+.2f}%",
                        "Volatility": "{:.2f}%",
                        "Beta vs ACWI": "{:.2f}",
                        "Sharpe": "{:.2f}",
                        "Correlation": "{:.2f}",
                    },
                    na_rep="N/A",
                ),
                use_container_width=True,
                hide_index=True,
            )


if not cash_balances.empty:
    with st.expander("💵 Cash by Account"):
        cash_display = cash_balances.copy()
        cash_display.columns = [
            "Account ID",
            "Account",
            "Currency",
            "Cash Balance",
            "Current FX to SEK",
            "Value (SEK)",
        ]
        st.dataframe(
            cash_display.style.format(
                {
                    "Cash Balance": "{:,.2f}",
                    "Current FX to SEK": "{:,.4f}",
                    "Value (SEK)": "{:,.0f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Cash is calculated by summing imported cash movements by currency, then "
            "converting the current remaining balance at the latest FX rate."
        )


# ============================================================
# 17B. PRECIOUS METAL POSITION STATUS
# ============================================================

metal_asset_status = assets[
    assets["asset_type"]
    .fillna("")
    .astype(str)
    .str.upper()
    .eq("METAL")
].copy()

if not metal_asset_status.empty:
    metal_tx_status = transactions[
        transactions["asset_id"].isin(
            metal_asset_status["id"]
        )
    ].copy()

    if not metal_tx_status.empty:
        metal_position_rows = []

        for _, metal_asset in metal_asset_status.iterrows():
            metal_id = int(metal_asset["id"])

            metal_asset_tx = metal_tx_status[
                metal_tx_status["asset_id"] == metal_id
            ].copy()

            if metal_asset_tx.empty:
                continue

            buys = pd.to_numeric(
                metal_asset_tx.loc[
                    metal_asset_tx[
                        "transaction_type"
                    ].astype(str).str.upper() == "BUY",
                    "quantity",
                ],
                errors="coerce",
            ).fillna(0.0).sum()

            sells = pd.to_numeric(
                metal_asset_tx.loc[
                    metal_asset_tx[
                        "transaction_type"
                    ].astype(str).str.upper() == "SELL",
                    "quantity",
                ],
                errors="coerce",
            ).fillna(0.0).sum()

            grams = float(buys - sells)

            if grams <= 1e-9:
                continue

            price_match = latest_prices[
                latest_prices["asset_id"] == metal_id
            ]

            current_price = None
            price_date = None

            if not price_match.empty:
                current_price = pd.to_numeric(
                    price_match.iloc[0]["close_price"],
                    errors="coerce",
                )
                price_date = price_match.iloc[0][
                    "price_date"
                ]

            market_value = (
                grams * float(current_price)
                if pd.notna(current_price)
                else None
            )

            metal_position_rows.append(
                {
                    "Metal": metal_asset["name"],
                    "Grams": grams,
                    "Current Price (SEK/g)": (
                        float(current_price)
                        if pd.notna(current_price)
                        else None
                    ),
                    "Market Value (SEK)": market_value,
                    "Price Date": price_date,
                    "Status": (
                        "Ready"
                        if pd.notna(current_price)
                        else "Missing current price"
                    ),
                }
            )

        if metal_position_rows:
            with st.expander(
                "🪙 Precious Metal Position Status",
                expanded=True,
            ):
                metal_status_df = pd.DataFrame(
                    metal_position_rows
                )

                st.caption(
                    "Market prices use Stooq spot XAU/USD, XAG/USD or XPT/USD "
                    "converted to SEK per gram."
                )

                st.dataframe(
                    metal_status_df.style.format(
                        {
                            "Grams": "{:,.2f}",
                            "Current Price (SEK/g)": "{:,.2f}",
                            "Market Value (SEK)": "{:,.0f}",
                        },
                        na_rep="—",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                if (
                    metal_status_df["Status"]
                    == "Missing current price"
                ).any():
                    st.warning(
                        "The metal transaction exists, but no current "
                        "market price is stored yet. Click Refresh Prices "
                        "in the sidebar. The position will appear in the "
                        "portfolio as soon as a price is available."
                    )


# ============================================================
# 18. DETAILED PORTFOLIO CHARTS
# ============================================================

st.divider()

if portfolio.empty:
    if transactions.empty:
        st.info("No transactions yet. Add one manually or import a CSV.")
    else:
        st.info("No current holdings are available to chart.")
else:
    missing_market_data = portfolio[
        portfolio["close_price"].isna() | portfolio["sek_per_unit"].isna()
    ]

    if not missing_market_data.empty:
        st.warning(
            "Some holdings are missing current price or FX data. "
            "Press 'Refresh Prices' in the sidebar."
        )
        st.dataframe(
            missing_market_data[["account", "name", "ticker", "currency"]],
            hide_index=True,
            use_container_width=True,
        )

    chart_portfolio = portfolio.dropna(subset=["market_value_sek"]).copy()

    if not chart_portfolio.empty:
        aggregated = (
            chart_portfolio.groupby(
                ["asset_id", "ticker", "name"],
                as_index=False
            )
            .agg(
                market_value_sek=("market_value_sek", "sum"),
                cost_basis_sek=("cost_basis_after_sek", "sum"),
                unrealized_pl_sek=("unrealized_pl_sek", "sum"),
            )
        )

        # ----------------------------------------------------
        # Build a complete gain history by investment.
        #
        # Total Gain =
        #   Realized P/L
        # + Unrealized P/L
        # + Dividends
        #
        # Deposits and withdrawals are never included.
        # ----------------------------------------------------

        realized_by_asset = (
            current_positions.groupby(
                "asset_id",
                as_index=False
            )
            .agg(
                realized_pl_sek=(
                    "total_realized_pl_sek",
                    "sum"
                )
            )
            if not current_positions.empty
            else pd.DataFrame(
                columns=[
                    "asset_id",
                    "realized_pl_sek"
                ]
            )
        )

        dividends_by_asset = (
            dividend_data.groupby(
                "asset_id",
                as_index=False
            )
            .agg(
                dividends_sek=(
                    "dividends_sek",
                    "sum"
                )
            )
            if not dividend_data.empty
            else pd.DataFrame(
                columns=[
                    "asset_id",
                    "dividends_sek"
                ]
            )
        )

        unrealized_by_asset = (
            aggregated[
                [
                    "asset_id",
                    "unrealized_pl_sek"
                ]
            ]
            .copy()
        )

        gain_breakdown = (
            assets[
                [
                    "id",
                    "ticker",
                    "name"
                ]
            ]
            .rename(
                columns={"id": "asset_id"}
            )
            .merge(
                realized_by_asset,
                on="asset_id",
                how="left"
            )
            .merge(
                unrealized_by_asset,
                on="asset_id",
                how="left"
            )
            .merge(
                dividends_by_asset,
                on="asset_id",
                how="left"
            )
        )

        for gain_column in [
            "realized_pl_sek",
            "unrealized_pl_sek",
            "dividends_sek",
        ]:
            gain_breakdown[gain_column] = (
                pd.to_numeric(
                    gain_breakdown[gain_column],
                    errors="coerce"
                )
                .fillna(0.0)
            )

        gain_breakdown["total_gain_sek"] = (
            gain_breakdown["realized_pl_sek"]
            + gain_breakdown["unrealized_pl_sek"]
            + gain_breakdown["dividends_sek"]
        )

        # Only show investments that have actually contributed
        # to one of the gain components.
        gain_breakdown = gain_breakdown[
            (
                gain_breakdown["realized_pl_sek"].abs()
                + gain_breakdown["unrealized_pl_sek"].abs()
                + gain_breakdown["dividends_sek"].abs()
            ) > 0.005
        ].copy()

        left_chart, right_chart = st.columns(2)

        with left_chart:
            st.subheader("Portfolio Allocation")
            allocation_chart = px.pie(
                aggregated,
                names="ticker",
                values="market_value_sek",
                hole=0.55,
            )
            allocation_chart.update_traces(
                textposition="inside",
                textinfo="percent+label"
            )
            st.plotly_chart(
                allocation_chart,
                use_container_width=True
            )

        with right_chart:
            st.subheader("Gain by Investment")

            gain_view = st.radio(
                "Gain view",
                [
                    "Current Gain",
                    "Total Gain",
                    "Dividends"
                ],
                horizontal=True,
                key="gain_chart_view",
                label_visibility="collapsed",
            )

            if gain_view == "Current Gain":
                st.caption(
                    "Unrealized P/L on investments you currently own. "
                    "Realized gains and dividends are shown separately in "
                    "the other views."
                )

                chart_data = aggregated.copy()
                chart_value = "unrealized_pl_sek"
                chart_title = "Current Gain"
                hover_data = {
                    "name": True,
                    "market_value_sek": ":,.0f",
                    "cost_basis_sek": ":,.0f",
                    "unrealized_pl_sek": ":,.0f",
                }

            elif gain_view == "Total Gain":
                st.caption(
                    "Lifetime investment gain: realized P/L + current "
                    "unrealized P/L + dividends. Deposits and withdrawals "
                    "are excluded."
                )

                chart_data = gain_breakdown.copy()
                chart_value = "total_gain_sek"
                chart_title = "Total Gain"
                hover_data = {
                    "name": True,
                    "realized_pl_sek": ":,.0f",
                    "unrealized_pl_sek": ":,.0f",
                    "dividends_sek": ":,.0f",
                    "total_gain_sek": ":,.0f",
                }

            else:
                st.caption(
                    "Total dividends received from each investment. "
                    "This is included in Total Gain."
                )

                chart_data = gain_breakdown[
                    gain_breakdown[
                        "dividends_sek"
                    ].abs() > 0.005
                ].copy()

                chart_value = "dividends_sek"
                chart_title = "Dividends"
                hover_data = {
                    "name": True,
                    "dividends_sek": ":,.0f",
                }

            if chart_data.empty:
                st.info(
                    f"No data available for {chart_title.lower()}."
                )

            else:
                gain_chart = px.bar(
                    chart_data.sort_values(chart_value),
                    x="ticker",
                    y=chart_value,
                    hover_data=hover_data,
                )

                gain_chart.update_layout(
                    xaxis_title="",
                    yaxis_title="SEK",
                )

                st.plotly_chart(
                    gain_chart,
                    use_container_width=True,
                )


# ============================================================
# 18C. EXPOSURE — REGIONS / SECTORS / HOLDINGS
# ============================================================

if not portfolio.empty:
    exposure_portfolio = portfolio.dropna(subset=["market_value_sek"]).copy()

    if not exposure_portfolio.empty:
        metadata_lookup = assets[["id", "sector", "country"]].copy()
        metadata_lookup = metadata_lookup.rename(columns={"id": "asset_id"})

        exposure_portfolio = exposure_portfolio.merge(
            metadata_lookup,
            on="asset_id",
            how="left",
        )

        exposure_portfolio["sector"] = (
            exposure_portfolio["sector"].fillna("").astype(str).str.strip()
        )
        exposure_portfolio["country"] = (
            exposure_portfolio["country"].fillna("").astype(str).str.strip()
        )

        exposure_portfolio.loc[
            exposure_portfolio["sector"] == "", "sector"
        ] = "Unknown"
        exposure_portfolio.loc[
            exposure_portfolio["country"] == "", "country"
        ] = "Unknown"

        invested_value = float(exposure_portfolio["market_value_sek"].sum())

        # Country / region exposure
        country_data = (
            exposure_portfolio.groupby("country", as_index=False)
            .agg(market_value_sek=("market_value_sek", "sum"))
            .sort_values("market_value_sek", ascending=False)
        )
        country_data["weight_percent"] = (
            country_data["market_value_sek"] / invested_value * 100
            if invested_value > 0
            else 0.0
        )

        # Sector exposure
        sector_data = (
            exposure_portfolio.groupby("sector", as_index=False)
            .agg(market_value_sek=("market_value_sek", "sum"))
            .sort_values("market_value_sek", ascending=False)
        )
        sector_data["weight_percent"] = (
            sector_data["market_value_sek"] / invested_value * 100
            if invested_value > 0
            else 0.0
        )

        # Holding exposure, aggregated across accounts.
        holding_data = (
            exposure_portfolio.groupby(["asset_id", "name", "ticker"], as_index=False)
            .agg(market_value_sek=("market_value_sek", "sum"))
            .sort_values("market_value_sek", ascending=False)
        )
        holding_data["weight_percent"] = (
            holding_data["market_value_sek"] / invested_value * 100
            if invested_value > 0
            else 0.0
        )
        holding_data["label"] = holding_data.apply(
            lambda row: (
                f"{row['name']} ({row['ticker']})"
                if clean_text(row.get("ticker", ""))
                else clean_text(row.get("name", ""))
            ),
            axis=1,
        )

        # Current precious-metals sleeve.
        exposure_type_lookup = (
            assets[
                ["id", "asset_type"]
            ]
            .rename(
                columns={"id": "asset_id"}
            )
        )

        exposure_with_type = (
            exposure_portfolio.merge(
                exposure_type_lookup,
                on="asset_id",
                how="left",
            )
        )

        precious_metals_value = float(
            pd.to_numeric(
                exposure_with_type.loc[
                    exposure_with_type[
                        "asset_type"
                    ]
                    .fillna("")
                    .astype(str)
                    .str.upper()
                    .eq("METAL"),
                    "market_value_sek",
                ],
                errors="coerce",
            )
            .fillna(0.0)
            .sum()
        )

        precious_metals_weight = (
            precious_metals_value
            / invested_value
            * 100.0
            if invested_value > 0
            else 0.0
        )

        if not latest_prices.empty and "price_date" in latest_prices.columns:
            exposure_dates = pd.to_datetime(
                latest_prices["price_date"], errors="coerce"
            ).dropna()
            exposure_updated = (
                exposure_dates.max().date()
                if not exposure_dates.empty
                else date.today()
            )
        else:
            exposure_updated = date.today()

        def render_exposure_rows(dataframe, label_column, max_rows=8):
            """Render compact percentage bars similar to a fund exposure card."""
            if dataframe.empty:
                st.info("No exposure data is available yet.")
                return

            for _, exposure_row in dataframe.head(max_rows).iterrows():
                label = html.escape(clean_text(exposure_row[label_column]) or "Unknown")
                pct = float(exposure_row["weight_percent"])
                value_sek = float(exposure_row["market_value_sek"])
                bar_width = max(0.0, min(100.0, pct))

                st.markdown(
                    f"""
                    <div class="exposure-list-row">
                        <div class="exposure-list-top">
                            <div class="exposure-list-name">
                                <span class="exposure-dot"></span>{label}
                            </div>
                            <div class="exposure-list-value">{pct:.2f}%</div>
                        </div>
                        <div class="exposure-track" title="{value_sek:,.0f} SEK">
                            <div class="exposure-fill" style="width:{bar_width:.2f}%"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()

        with st.container(border=True):

            if precious_metals_value > 0:
                metals_card_left, metals_card_right = (
                    st.columns([3, 2])
                )

                with metals_card_left:
                    st.metric(
                        "Precious Metals Exposure",
                        f"{precious_metals_weight:.2f}%",
                    )

                with metals_card_right:
                    st.metric(
                        "Precious Metals Value",
                        f"{precious_metals_value:,.0f} SEK",
                    )

                st.divider()

            header_left, header_right = st.columns([3, 1])

            with header_left:
                st.markdown(
                    '<div class="exposure-title">Exposure</div>',
                    unsafe_allow_html=True,
                )

            with header_right:
                st.markdown(
                    f'<div class="exposure-updated">Updated {exposure_updated}</div>',
                    unsafe_allow_html=True,
                )

            exposure_view = st.radio(
                "Exposure view",
                ["Regions", "Sectors", "Holdings"],
                horizontal=True,
                label_visibility="collapsed",
                key="exposure_view",
            )

            if exposure_view == "Regions":
                map_data = country_data[country_data["country"] != "Unknown"].copy()

                if map_data.empty:
                    st.info(
                        "No country metadata is available yet. Use 'Sector & Country "
                        "Metadata' in Tools & Imports at the end of the page."
                    )
                else:
                    country_map = px.choropleth(
                        map_data,
                        locations="country",
                        locationmode="country names",
                        color="weight_percent",
                        hover_name="country",
                        hover_data={
                            "market_value_sek": ":,.0f",
                            "weight_percent": ":.2f",
                            "country": False,
                        },
                        labels={
                            "market_value_sek": "Market Value (SEK)",
                            "weight_percent": "Portfolio Weight (%)",
                        },
                        color_continuous_scale=[
                            [0.00, "#70758a"],
                            [0.35, "#aeb9e8"],
                            [1.00, "#eef1ff"],
                        ],
                        projection="natural earth",
                    )

                    country_map.update_geos(
                        bgcolor="rgba(0,0,0,0)",
                        showframe=False,
                        showcoastlines=False,
                        showcountries=True,
                        countrycolor="#3a3a3a",
                        showland=True,
                        landcolor="#292929",
                        showocean=True,
                        oceancolor="#161616",
                    )
                    country_map.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        coloraxis_showscale=False,
                        margin=dict(l=0, r=0, t=5, b=0),
                        height=350,
                    )
                    st.plotly_chart(
                        country_map,
                        use_container_width=True,
                        config={"displayModeBar": False, "scrollZoom": False},
                    )

                    render_exposure_rows(country_data, "country", max_rows=7)

                    unknown_country_value = float(
                        country_data.loc[
                            country_data["country"] == "Unknown",
                            "market_value_sek",
                        ].sum()
                    )
                    if unknown_country_value > 0 and invested_value > 0:
                        unknown_pct = unknown_country_value / invested_value * 100
                        st.caption(
                            f"{unknown_pct:.1f}% of invested value currently has no "
                            "country metadata and is not shaded on the map."
                        )

            elif exposure_view == "Sectors":
                render_exposure_rows(sector_data, "sector", max_rows=10)

            else:
                render_exposure_rows(holding_data, "label", max_rows=10)

            st.caption(
                "Exposure is based on current invested market value and excludes cash. "
                "Country means issuer country; funds and ETFs are not yet looked through "
                "to their underlying geographic holdings."
            )


# ============================================================
# 19. HOLDINGS TABLE
# ============================================================

st.divider()
st.subheader("Holdings")

if portfolio.empty:
    st.caption("No current holdings.")
else:
    holdings_table = portfolio[
        [
            "account",
            "asset_id",
            "name",
            "ticker",
            "shares_after",
            "close_price",
            "currency",
            "average_cost_after_sek",
            "cost_basis_after_sek",
            "market_value_sek",
            "unrealized_pl_sek",
            "total_realized_pl_sek",
            "dividends_sek",
            "total_gain_sek",
            "return_percent",
            "weight_percent",
        ]
    ].copy()

    holdings_type_lookup = (
        assets[
            [
                "id",
                "asset_type"
            ]
        ]
        .rename(
            columns={"id": "asset_id"}
        )
    )

    holdings_table = (
        holdings_table
        .merge(
            holdings_type_lookup,
            on="asset_id",
            how="left",
        )
    )

    holdings_table["Unit"] = (
        holdings_table[
            "asset_type"
        ]
        .fillna("")
        .astype(str)
        .str.upper()
        .apply(
            lambda value: (
                "g"
                if value == "METAL"
                else "units"
            )
        )
    )

    holdings_table = holdings_table[
        [
            "account",
            "name",
            "ticker",
            "shares_after",
            "Unit",
            "close_price",
            "currency",
            "average_cost_after_sek",
            "cost_basis_after_sek",
            "market_value_sek",
            "unrealized_pl_sek",
            "total_realized_pl_sek",
            "dividends_sek",
            "total_gain_sek",
            "return_percent",
            "weight_percent",
        ]
    ]

    holdings_table.columns = [
        "Account",
        "Investment",
        "Ticker",
        "Quantity",
        "Unit",
        "Price / Unit",
        "Currency",
        "Avg Cost / Unit (SEK)",
        "Cost Basis (SEK)",
        "Market Value (SEK)",
        "Unrealized P/L",
        "Realized P/L",
        "Dividends",
        "Total Gain",
        "Return %",
        "Weight %",
    ]

    st.dataframe(
        holdings_table.style.format(
            {
                "Quantity": "{:,.4f}",
                "Price / Unit": "{:,.2f}",
                "Avg Cost / Unit (SEK)": "{:,.2f}",
                "Cost Basis (SEK)": "{:,.0f}",
                "Market Value (SEK)": "{:,.0f}",
                "Unrealized P/L": "{:+,.0f}",
                "Realized P/L": "{:+,.0f}",
                "Dividends": "{:,.0f}",
                "Total Gain": "{:+,.0f}",
                "Return %": "{:+.2f}%",
                "Weight %": "{:.2f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 20. TRANSACTION HISTORY
# ============================================================

with st.expander("Transaction History"):
    if transactions.empty:
        st.caption("No transactions yet.")
    else:
        transaction_display = transactions[
            [
                "transaction_date",
                "account",
                "name",
                "ticker",
                "transaction_type",
                "quantity",
                "price",
                "currency",
                "fees",
                "fx_rate_to_sek",
                "source",
            ]
        ].copy()

        transaction_display.columns = [
            "Date",
            "Account",
            "Investment",
            "Ticker",
            "Type",
            "Quantity",
            "Price / Unit",
            "Currency",
            "Fees",
            "FX to SEK",
            "Source",
        ]

        st.dataframe(
            transaction_display,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 20B. CASH MOVEMENT HISTORY
# ============================================================

with st.expander("Cash Movement History"):
    if cash_movements.empty:
        st.caption("No cash movements imported yet.")
    else:
        cash_history_display = cash_movements[
            [
                "movement_date",
                "account",
                "movement_type",
                "description",
                "amount",
                "currency",
                "source",
            ]
        ].copy()
        cash_history_display.columns = [
            "Date",
            "Account",
            "Type",
            "Description",
            "Amount",
            "Currency",
            "Source",
        ]
        st.dataframe(
            cash_history_display,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 21. CORPORATE ACTION HISTORY
# ============================================================

with st.expander("Corporate Actions"):
    if corporate_actions.empty:
        st.caption("No corporate actions saved.")
    else:
        action_display = corporate_actions.merge(
            assets[["id", "name", "ticker"]],
            left_on="asset_id",
            right_on="id",
            how="left",
            suffixes=("", "_asset"),
        )
        st.dataframe(
            action_display[
                [
                    "action_date",
                    "name",
                    "ticker",
                    "action_type",
                    "ratio_new",
                    "ratio_old",
                    "notes",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 22. DATABASE STATUS
# ============================================================

with st.expander("Database Status"):
    st.success("Connected to MySQL")
    st.write(f"Assets: {len(assets)}")
    st.write(f"Accounts: {len(accounts)}")
    st.write(f"Transactions: {len(transactions)}")
    st.write(f"Cash movements: {len(cash_movements)}")
    st.write(f"Current cash value: {total_cash_sek:,.0f} SEK")
    st.write(f"Current holdings: {len(portfolio)}")
    st.write(f"Corporate actions: {len(corporate_actions)}")


# ============================================================
# ============================================================
# 23. TOOLS & IMPORTS
# ============================================================

st.divider()
st.header("Tools & Imports")
st.caption(
    "Data maintenance, Yahoo enrichment and broker imports are kept here so the "
    "main dashboard stays focused on your portfolio."
)

# ============================================================
# 23A. HISTORICAL DATA
# ============================================================

with st.expander("📚 Historical Data"):
    st.caption(
        "Backfill daily prices, FX rates and benchmarks for portfolio analytics. "
        "Precious metals use direct historical spot metal/SEK observations. "
        "The current metal-history source provides dated observations from "
        "2024-03-02 onward."
    )

    schema_state = historical_schema_status()
    missing_schema = [
        name for name, present in schema_state.items() if not present
    ]

    if missing_schema:
        st.error(
            "Historical-data SQL setup is incomplete. Missing: "
            + ", ".join(missing_schema)
        )
        st.code(
            """USE investments;

-- prices must contain:
-- adjusted_close_price DECIMAL(18,6)

-- required tables:
-- benchmarks
-- benchmark_prices
-- risk_free_rates
""",
            language="sql",
        )
    else:
        history_start = historical_data_start_date()

        if history_start is None:
            st.info("Add at least one transaction before downloading historical data.")
        else:
            st.write(
                f"Historical backfill start date: **{history_start:%Y-%m-%d}**"
            )

            history_end = date.today() + timedelta(days=1)

            status_col1, status_col2, status_col3, status_col4 = st.columns(4)

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS n,
                    MIN(price_date) AS first_date,
                    MAX(price_date) AS last_date
                FROM prices;
                """
            )
            price_status = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS n,
                    MIN(price_date) AS first_date,
                    MAX(price_date) AS last_date
                FROM benchmark_prices;
                """
            )
            benchmark_status = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS n,
                    MIN(rate_date) AS first_date,
                    MAX(rate_date) AS last_date
                FROM fx_rates;
                """
            )
            fx_status = cursor.fetchone()

            status_col1.metric("Stored Asset Prices", f"{int(price_status['n'] or 0):,}")
            status_col2.metric(
                "Stored Benchmark Prices",
                f"{int(benchmark_status['n'] or 0):,}",
            )
            status_col3.metric("Stored FX Rates", f"{int(fx_status['n'] or 0):,}")

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS n,
                    MIN(rate_date) AS first_date,
                    MAX(rate_date) AS last_date
                FROM risk_free_rates;
                """
            )
            rf_status = cursor.fetchone()

            status_col4.metric(
                "Stored Risk-Free Rates",
                f"{int(rf_status['n'] or 0):,}",
            )

            st.caption(
                "The updater is safe to run again. Existing dates are updated rather "
                "than duplicated."
            )

            if st.button(
                "📈 Update Historical Data",
                type="primary",
                key="update_historical_data",
            ):
                ensure_default_benchmarks()

                historical_assets = assets[
                    assets["market_symbol"].notna()
                    & (assets["market_symbol"].astype(str).str.strip() != "")
                ].copy()

                benchmarks_df = query_dataframe(
                    """
                    SELECT id, symbol, name, currency
                    FROM benchmarks
                    ORDER BY id;
                    """
                )

                total_steps = len(historical_assets) + len(benchmarks_df)

                currencies_needed = set(
                    historical_assets["currency"]
                    .dropna()
                    .astype(str)
                    .str.upper()
                    .tolist()
                )
                if not benchmarks_df.empty:
                    currencies_needed.update(
                        benchmarks_df["currency"]
                        .dropna()
                        .astype(str)
                        .str.upper()
                        .tolist()
                    )

                total_steps += len(currencies_needed) + 1
                progress = st.progress(0)
                status = st.empty()

                completed = 0
                asset_rows_written = 0
                fx_rows_written = 0
                benchmark_rows_written = 0
                risk_free_rows_written = 0
                warnings = []

                try:
                    # --------------------------------------------
                    # Asset histories
                    # --------------------------------------------
                    for _, asset in historical_assets.iterrows():
                        symbol = str(asset["market_symbol"]).strip()
                        status.write(
                            f"Asset prices: {asset['name']} ({symbol})"
                        )

                        try:
                            is_metal_asset = (
                                clean_text(
                                    asset.get(
                                        "asset_type",
                                        ""
                                    )
                                ).upper()
                                == "METAL"
                            )

                            if is_metal_asset:
                                cursor.execute(
                                    """
                                    SELECT
                                        MIN(transaction_date)
                                        AS first_transaction_date
                                    FROM transactions
                                    WHERE asset_id = %s;
                                    """,
                                    (
                                        int(asset["id"]),
                                    ),
                                )

                                first_metal_tx = (
                                    cursor.fetchone()
                                    or {}
                                ).get(
                                    "first_transaction_date"
                                )

                                metal_history_start = (
                                    as_date(first_metal_tx)
                                    if first_metal_tx
                                    else history_start
                                )

                                status.write(
                                    f"Spot metal history: "
                                    f"{asset['name']} "
                                    f"({metal_history_start} → "
                                    f"{history_end})"
                                )

                                history = (
                                    download_historical_metal_sek_per_gram(
                                        symbol,
                                        metal_history_start,
                                        history_end,
                                    )
                                )
                            else:
                                history = download_yahoo_history(
                                    symbol,
                                    history_start,
                                    history_end,
                                )

                            if history.empty:
                                warnings.append(
                                    f"{asset['name']} ({symbol}): "
                                    "no historical prices returned."
                                )
                            else:
                                asset_rows_written += (
                                    upsert_asset_history(
                                        asset["id"],
                                        normalize_currency(
                                            asset["currency"]
                                        ),
                                        history,
                                    )
                                )

                        except Exception as error:
                            warnings.append(
                                f"{asset['name']} ({symbol}): {error}"
                            )

                        completed += 1
                        progress.progress(
                            min(completed / max(total_steps, 1), 1.0)
                        )

                    # --------------------------------------------
                    # Historical FX
                    # --------------------------------------------
                    for currency in sorted(currencies_needed):
                        status.write(f"Historical FX: {currency}/SEK")

                        try:
                            fx_rows_written += upsert_fx_history(
                                currency,
                                history_start,
                                history_end,
                            )
                        except Exception as error:
                            warnings.append(f"{currency}/SEK: {error}")

                        completed += 1
                        progress.progress(
                            min(completed / max(total_steps, 1), 1.0)
                        )

                    # --------------------------------------------
                    # Benchmark histories
                    # --------------------------------------------
                    for _, benchmark in benchmarks_df.iterrows():
                        status.write(
                            f"Benchmark: {benchmark['name']} ({benchmark['symbol']})"
                        )

                        try:
                            benchmark_rows_written += upsert_benchmark_history(
                                benchmark["id"],
                                benchmark["symbol"],
                                history_start,
                                history_end,
                            )
                        except Exception as error:
                            warnings.append(
                                f"{benchmark['symbol']}: {error}"
                            )

                        completed += 1
                        progress.progress(
                            min(completed / max(total_steps, 1), 1.0)
                        )

                    # --------------------------------------------
                    # Swedish risk-free proxy
                    # --------------------------------------------
                    status.write(
                        "Risk-free rate: Swedish 3-month Treasury bill"
                    )

                    try:
                        risk_free_rows_written += upsert_risk_free_history(
                            history_start,
                            date.today(),
                        )
                    except Exception as error:
                        warnings.append(
                            f"Swedish Treasury Bill 3M: {error}"
                        )

                    completed += 1
                    progress.progress(
                        min(completed / max(total_steps, 1), 1.0)
                    )

                    connection.commit()
                    progress.progress(1.0)
                    status.empty()

                    st.success(
                        "Historical data updated: "
                        f"{asset_rows_written:,} asset-price rows, "
                        f"{fx_rows_written:,} FX rows, "
                        f"{benchmark_rows_written:,} benchmark rows, "
                        f"{risk_free_rows_written:,} risk-free rows processed."
                    )

                    if warnings:
                        with st.expander(
                            f"⚠️ {len(warnings)} item(s) could not be fully updated"
                        ):
                            for warning in warnings:
                                st.write(f"• {warning}")

                    st.info(
                        "Historical market data is stored in MySQL. "
                        "Refresh/rerun the dashboard once after this update and "
                        "the Portfolio Analytics section will use the new data."
                    )

                except Exception as error:
                    connection.rollback()
                    progress.empty()
                    status.empty()
                    st.error(
                        f"Historical data update failed and was rolled back: {error}"
                    )

            st.markdown("#### Historical coverage")

            coverage_assets = query_dataframe(
                """
                SELECT
                    a.name,
                    a.ticker,
                    a.market_symbol,
                    COUNT(p.id) AS observations,
                    MIN(p.price_date) AS first_date,
                    MAX(p.price_date) AS last_date
                FROM assets a
                LEFT JOIN prices p ON p.asset_id = a.id
                WHERE a.market_symbol IS NOT NULL
                  AND TRIM(a.market_symbol) <> ''
                GROUP BY a.id, a.name, a.ticker, a.market_symbol
                ORDER BY a.name;
                """
            )

            if not coverage_assets.empty:
                st.dataframe(
                    coverage_assets,
                    use_container_width=True,
                    hide_index=True,
                )

            risk_status = query_dataframe(
                """
                SELECT
                    COUNT(*) AS observations,
                    MIN(rate_date) AS first_date,
                    MAX(rate_date) AS last_date
                FROM risk_free_rates;
                """
            )

            if (
                not risk_status.empty
                and int(risk_status.iloc[0]["observations"] or 0) == 0
            ):
                st.warning(
                    "Risk-free rates are empty. Click 'Update Historical Data' "
                    "to download the Swedish 3-month Treasury-bill series used "
                    "for the Sharpe ratio."
                )


# ============================================================
# 23B. YAHOO FINANCE SYMBOL REVIEW
# ============================================================

with st.expander("🔎 Yahoo Finance Symbol Review"):
    st.caption(
        "Automatically search Yahoo Finance for investments that do not yet have a "
        "market symbol. Suggestions are validated against recent price data and are "
        "never saved until you approve them."
    )

    missing_symbols = assets[
        assets["market_symbol"].isna()
        | (assets["market_symbol"].astype(str).str.strip() == "")
    ].copy()

    if missing_symbols.empty:
        st.success("All investments already have a Yahoo Finance symbol.")
        st.session_state.pop("yahoo_symbol_suggestions", None)

    else:
        st.write(f"Investments missing a Yahoo symbol: **{len(missing_symbols)}**")

        if st.button(
            "🔍 Find Yahoo Symbols",
            type="primary",
            key="find_yahoo_symbols",
        ):
            suggestions = []
            progress = st.progress(0)
            status_box = st.empty()

            for position, (_, asset) in enumerate(missing_symbols.iterrows(), start=1):
                status_box.write(
                    f"Searching {position}/{len(missing_symbols)}: {asset['name']}"
                )

                suggestion = suggest_yahoo_symbol(
                    asset["name"],
                    asset.get("isin", ""),
                    asset.get("currency", ""),
                    asset.get("asset_type", "Other"),
                )

                suggestions.append(
                    {
                        "save": suggestion["confidence"] == "HIGH",
                        "asset_id": int(asset["id"]),
                        "investment": asset["name"],
                        "current_ticker": asset["ticker"],
                        "isin": clean_text(asset.get("isin", "")),
                        "currency": normalize_currency(asset.get("currency", ""), ""),
                        "suggested_symbol": suggestion["symbol"],
                        "yahoo_name": suggestion["candidate_name"],
                        "exchange": suggestion["exchange"],
                        "confidence": suggestion["confidence"],
                        "score": suggestion["score"],
                        "status": suggestion["status"],
                    }
                )

                progress.progress(position / len(missing_symbols))

            status_box.empty()
            progress.empty()
            st.session_state["yahoo_symbol_suggestions"] = suggestions

        suggestion_rows = st.session_state.get("yahoo_symbol_suggestions", [])

        if suggestion_rows:
            suggestion_df = pd.DataFrame(suggestion_rows)

            st.info(
                "HIGH-confidence matches are pre-selected. MEDIUM/LOW matches stay "
                "unchecked so you can review them first. You can also edit the suggested "
                "symbol directly in the table."
            )

            edited_suggestions = st.data_editor(
                suggestion_df,
                use_container_width=True,
                hide_index=True,
                disabled=[
                    "asset_id",
                    "investment",
                    "current_ticker",
                    "isin",
                    "currency",
                    "yahoo_name",
                    "exchange",
                    "confidence",
                    "score",
                    "status",
                ],
                column_config={
                    "save": st.column_config.CheckboxColumn(
                        "Save",
                        help="Save this Yahoo symbol to MySQL",
                    ),
                    "asset_id": None,
                    "investment": "Investment",
                    "current_ticker": "Current ticker",
                    "isin": "ISIN",
                    "currency": "Currency",
                    "suggested_symbol": st.column_config.TextColumn(
                        "Yahoo symbol",
                        help="You may correct the suggested Yahoo Finance symbol before saving.",
                    ),
                    "yahoo_name": "Yahoo result",
                    "exchange": "Exchange",
                    "confidence": "Confidence",
                    "score": st.column_config.NumberColumn("Score", format="%.1f"),
                    "status": "Status",
                },
                key="yahoo_symbol_review_editor",
            )

            selected_to_save = edited_suggestions[edited_suggestions["save"] == True].copy()

            col_save, col_clear = st.columns([1, 1])

            with col_save:
                save_yahoo_symbols = st.button(
                    f"💾 Save Selected Symbols ({len(selected_to_save)})",
                    use_container_width=True,
                    disabled=selected_to_save.empty,
                    key="save_yahoo_symbols",
                )

            with col_clear:
                clear_yahoo_suggestions = st.button(
                    "Clear Suggestions",
                    use_container_width=True,
                    key="clear_yahoo_suggestions",
                )

            if clear_yahoo_suggestions:
                st.session_state.pop("yahoo_symbol_suggestions", None)
                st.rerun()

            if save_yahoo_symbols:
                try:
                    saved = 0

                    for _, row in selected_to_save.iterrows():
                        symbol = clean_text(row["suggested_symbol"]).upper()

                        if not symbol:
                            continue

                        if not validate_yahoo_symbol(symbol):
                            raise ValueError(
                                f"Yahoo Finance returned no valid recent price for {symbol}."
                            )

                        cursor.execute(
                            """
                            SELECT id
                            FROM assets
                            WHERE id <> %s
                              AND market_symbol = %s
                            LIMIT 1;
                            """,
                            (int(row["asset_id"]), symbol),
                        )
                        duplicate_symbol = cursor.fetchone()

                        if duplicate_symbol:
                            raise ValueError(
                                f"Yahoo symbol {symbol} is already used by another investment."
                            )

                        cursor.execute(
                            """
                            UPDATE assets
                            SET market_symbol = %s
                            WHERE id = %s;
                            """,
                            (symbol, int(row["asset_id"])),
                        )
                        saved += cursor.rowcount

                    connection.commit()
                    st.session_state.pop("yahoo_symbol_suggestions", None)
                    st.session_state["yahoo_symbols_saved"] = (
                        f"✅ Saved {saved} Yahoo Finance symbol(s). "
                        "Press Refresh Prices to download current prices."
                    )
                    st.rerun()

                except Exception as error:
                    connection.rollback()
                    st.error(f"Could not save Yahoo symbols: {error}")

if "yahoo_symbols_saved" in st.session_state:
    st.success(st.session_state.pop("yahoo_symbols_saved"))


# ============================================================


# ============================================================
# 23B. SECTOR + COUNTRY METADATA REVIEW
# ============================================================

with st.expander("🌍 Sector & Country Metadata"):
    st.caption(
        "Fetch issuer sector and country automatically from Yahoo Finance. "
        "Nothing is saved until you review and approve it. Country exposure on the dashboard is issuer-country exposure; funds are not yet looked through to "
        "their underlying holdings."
    )

    metadata_candidates = assets[
        assets["market_symbol"].notna()
        & (assets["market_symbol"].astype(str).str.strip() != "")
        & (
            assets["sector"].isna()
            | (assets["sector"].astype(str).str.strip() == "")
            | assets["country"].isna()
            | (assets["country"].astype(str).str.strip() == "")
        )
    ].copy()

    if metadata_candidates.empty:
        st.success("All investments with Yahoo symbols already have sector/country metadata.")
        st.session_state.pop("yahoo_metadata_suggestions", None)
    else:
        st.write(
            f"Investments with a Yahoo symbol but missing sector or country: "
            f"**{len(metadata_candidates)}**"
        )

        if st.button(
            "🔎 Fetch Sector & Country",
            type="primary",
            key="fetch_yahoo_metadata",
        ):
            metadata_suggestions = []
            progress = st.progress(0)
            status_box = st.empty()

            for position, (_, asset) in enumerate(metadata_candidates.iterrows(), start=1):
                status_box.write(
                    f"Fetching {position}/{len(metadata_candidates)}: {asset['name']}"
                )

                result = fetch_yahoo_metadata(
                    asset.get("market_symbol", ""),
                    asset.get("asset_type", "Other"),
                )

                current_sector = clean_text(asset.get("sector", ""))
                current_country = clean_text(asset.get("country", ""))

                metadata_suggestions.append(
                    {
                        "Save": True,
                        "asset_id": int(asset["id"]),
                        "Investment": asset["name"],
                        "Symbol": clean_text(asset.get("market_symbol", "")),
                        "Sector": current_sector or result["sector"],
                        "Country": current_country or result["country"],
                        "Status": result["status"],
                    }
                )

                progress.progress(position / len(metadata_candidates))

            progress.empty()
            status_box.empty()
            st.session_state["yahoo_metadata_suggestions"] = metadata_suggestions

        metadata_suggestions = st.session_state.get("yahoo_metadata_suggestions")

        if metadata_suggestions:
            metadata_editor = pd.DataFrame(metadata_suggestions)

            edited_metadata = st.data_editor(
                metadata_editor[
                    [
                        "Save",
                        "asset_id",
                        "Investment",
                        "Symbol",
                        "Sector",
                        "Country",
                        "Status",
                    ]
                ],
                disabled=["asset_id", "Investment", "Symbol", "Status"],
                column_config={
                    "Save": st.column_config.CheckboxColumn(
                        "Save",
                        help="Uncheck anything you do not want written to MySQL.",
                    ),
                    "asset_id": None,
                    "Investment": "Investment",
                    "Symbol": "Yahoo Symbol",
                    "Sector": st.column_config.TextColumn(
                        "Sector",
                        help="You can correct Yahoo's sector before saving.",
                    ),
                    "Country": st.column_config.TextColumn(
                        "Country",
                        help="Use a normal country name such as Sweden, Finland or United States.",
                    ),
                    "Status": "Status",
                },
                hide_index=True,
                use_container_width=True,
                key="yahoo_metadata_editor",
            )

            selected_metadata = edited_metadata[edited_metadata["Save"] == True]

            if st.button(
                f"💾 Save Metadata ({len(selected_metadata)})",
                key="save_yahoo_metadata",
                disabled=selected_metadata.empty,
            ):
                try:
                    saved = 0

                    for _, row in selected_metadata.iterrows():
                        sector_value = clean_text(row.get("Sector", "")) or None
                        country_value = clean_text(row.get("Country", "")) or None

                        if not sector_value and not country_value:
                            continue

                        cursor.execute(
                            """
                            UPDATE assets
                            SET sector = %s,
                                country = %s
                            WHERE id = %s;
                            """,
                            (
                                sector_value,
                                country_value,
                                int(row["asset_id"]),
                            ),
                        )
                        saved += 1

                    connection.commit()
                    st.session_state.pop("yahoo_metadata_suggestions", None)
                    st.session_state["metadata_saved"] = (
                        f"✅ Saved sector/country metadata for {saved} investment(s)."
                    )
                    st.rerun()

                except Exception as error:
                    connection.rollback()
                    st.error(f"Could not save metadata: {error}")

if "metadata_saved" in st.session_state:
    st.success(st.session_state.pop("metadata_saved"))


# ============================================================


# ============================================================
# 23D. AVANZA CSV IMPORTER
# ============================================================

if "csv_import_success" in st.session_state:
    st.success(st.session_state.pop("csv_import_success"))

st.divider()

with st.expander("📥 Import Avanza CSV"):
    st.caption(
        "The importer reads Avanza's transaction export, maps each CSV account to "
        "one of your accounts, imports BUY/SELL transactions, dividends and every "
        "non-zero cash movement. Nothing is written until you press Import."
    )

    if accounts.empty:
        st.warning("Create your account(s) in the sidebar first.")
    else:
        uploaded_file = st.file_uploader(
            "Choose Avanza CSV file",
            type=["csv"],
            key="avanza_csv_upload",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            base_file_hash = hashlib.sha256(file_bytes).hexdigest()

            try:
                csv_data = read_broker_csv(file_bytes)
            except Exception as error:
                st.error(f"Could not read the file: {error}")
                csv_data = None

            required_columns = {
                "Datum",
                "Konto",
                "Typ av transaktion",
                "Värdepapper/beskrivning",
                "Antal",
                "Kurs",
                "Belopp",
                "Transaktionsvaluta",
                "Courtage",
                "Instrumentvaluta",
                "ISIN",
            }

            if csv_data is not None:
                missing_columns = sorted(required_columns - set(csv_data.columns))

                if missing_columns:
                    st.error(
                        "This does not look like the Avanza export expected by this importer. "
                        f"Missing columns: {', '.join(missing_columns)}"
                    )
                else:
                    st.write(f"Rows found: {len(csv_data)}")
                    st.subheader("Raw CSV Preview")
                    st.dataframe(
                        csv_data.head(20),
                        use_container_width=True,
                        hide_index=True,
                    )

                    # ------------------------------------------------------------
                    # 11A. MAP EACH AVANZA ACCOUNT TO A DATABASE ACCOUNT
                    # ------------------------------------------------------------

                    source_accounts = []
                    for value in csv_data["Konto"].tolist():
                        ref = normalize_account_ref(value)
                        if ref not in source_accounts:
                            source_accounts.append(ref)

                    database_account_options = {
                        f"{row['broker']} — {row['account_name']} ({row['account_type']})": int(row["id"])
                        for _, row in accounts.iterrows()
                    }
                    account_label_by_id = {
                        int(row["id"]): f"{row['broker']} — {row['account_name']} ({row['account_type']})"
                        for _, row in accounts.iterrows()
                    }

                    st.subheader("Match Avanza Accounts")
                    st.caption(
                        "Your export can contain several Avanza accounts. Choose which local "
                        "account each one belongs to."
                    )

                    source_to_account = {}
                    for idx_account, source_account in enumerate(source_accounts):
                        label = st.selectbox(
                            f"CSV account {source_account}",
                            list(database_account_options.keys()),
                            key=f"avanza_account_map_{idx_account}_{source_account}",
                        )
                        source_to_account[source_account] = database_account_options[label]

                    if len(set(source_to_account.values())) < len(source_to_account.values()):
                        st.warning(
                            "Two CSV accounts are mapped to the same local account. "
                            "That is allowed, but make sure it is intentional."
                        )

                    # ------------------------------------------------------------
                    # 11B. BUILD LOOKUPS FOR EXISTING INVESTMENTS
                    # ------------------------------------------------------------

                    assets_by_isin = {}
                    assets_by_name = {}
                    existing_tickers = set()

                    for _, asset_row in assets.iterrows():
                        asset_info = {
                            "id": int(asset_row["id"]),
                            "ticker": clean_text(asset_row["ticker"]).upper(),
                            "name": clean_text(asset_row["name"]),
                            "currency": normalize_currency(asset_row["currency"]),
                            "isin": normalize_isin(asset_row.get("isin", "")),
                        }
                        existing_tickers.add(asset_info["ticker"])

                        if asset_info["isin"]:
                            assets_by_isin[asset_info["isin"]] = asset_info

                        for key in {asset_info["ticker"], asset_info["name"].upper()}:
                            if key:
                                assets_by_name[key] = asset_info

                    # ------------------------------------------------------------
                    # 11C. PARSE EVERY ROW INTO A SAFE PREVIEW
                    # ------------------------------------------------------------

                    preview_rows = []
                    new_asset_candidates = {}

                    for row_number, row in csv_data.iterrows():
                        errors = []
                        notes = []

                        source_account = normalize_account_ref(row["Konto"])
                        account_id = source_to_account.get(source_account)
                        account_label = account_label_by_id.get(account_id, "Unmapped")

                        parsed_date = pd.to_datetime(
                            row["Datum"],
                            dayfirst=True,
                            errors="coerce",
                        )
                        tx_date = None if pd.isna(parsed_date) else parsed_date.date()
                        if tx_date is None:
                            errors.append("Invalid date")

                        raw_type = clean_text(row["Typ av transaktion"])
                        security_action = avanza_security_action(raw_type)
                        movement_type = avanza_cash_type(raw_type)
                        description = clean_text(row["Värdepapper/beskrivning"])
                        isin = normalize_isin(row["ISIN"])

                        try:
                            quantity_value = parse_number(row["Antal"])
                            price_value = parse_number(row["Kurs"])
                            amount_value = parse_number(row["Belopp"])
                            fees_value = parse_number(row["Courtage"])
                        except Exception:
                            quantity_value = 0.0
                            price_value = 0.0
                            amount_value = 0.0
                            fees_value = 0.0
                            errors.append("Invalid numeric value")

                        transaction_currency = normalize_currency(
                            row["Transaktionsvaluta"],
                            "SEK",
                        )
                        instrument_currency = normalize_currency(
                            row["Instrumentvaluta"],
                            transaction_currency,
                        )

                        asset = None
                        if isin and isin in assets_by_isin:
                            asset = assets_by_isin[isin]
                        elif description.upper() in assets_by_name:
                            asset = assets_by_name[description.upper()]

                        will_create_asset = False
                        if security_action in {"BUY", "SELL", "DIVIDEND"} and asset is None:
                            if isin:
                                will_create_asset = True
                                if isin not in new_asset_candidates:
                                    temp_ticker = make_placeholder_ticker(
                                        description or "Imported Asset",
                                        isin,
                                        existing_tickers | {
                                            item["ticker"] for item in new_asset_candidates.values()
                                        },
                                    )
                                    new_asset_candidates[isin] = {
                                        "isin": isin,
                                        "name": description or f"Imported {isin}",
                                        "ticker": temp_ticker,
                                        "currency": instrument_currency,
                                    }
                                notes.append("New investment will be created")
                            else:
                                errors.append("Security has no ISIN and is not in your investment list")

                        if security_action in {"BUY", "SELL"}:
                            if quantity_value <= 0:
                                errors.append("BUY/SELL quantity must be > 0")
                            if price_value <= 0:
                                errors.append("BUY/SELL price must be > 0")

                        has_cash_movement = abs(amount_value) > 1e-12
                        has_dividend_record = (
                            security_action == "DIVIDEND"
                            and quantity_value > 0
                            and price_value > 0
                        )

                        if security_action == "DIVIDEND" and not has_dividend_record:
                            notes.append("Dividend will count as cash only because shares/DPS are missing")

                        if security_action is None and not has_cash_movement:
                            notes.append("No cash or supported security action; row will be ignored")

                        asset_identifier = (
                            isin
                            or (asset["isin"] if asset else "")
                            or description.upper()
                        )

                        security_hash = None
                        if security_action in {"BUY", "SELL"} and tx_date and account_id:
                            security_hash = make_avanza_hash(
                                "SECURITY",
                                account_id,
                                source_account,
                                tx_date,
                                raw_type,
                                asset_identifier,
                                description,
                                quantity_value,
                                price_value,
                                amount_value,
                                instrument_currency,
                                fees_value,
                            )

                        cash_hash = None
                        if has_cash_movement and tx_date and account_id:
                            cash_hash = make_avanza_hash(
                                "CASH",
                                account_id,
                                source_account,
                                tx_date,
                                raw_type,
                                asset_identifier,
                                description,
                                quantity_value,
                                price_value,
                                amount_value,
                                transaction_currency,
                                fees_value,
                            )

                        dividend_hash = None
                        if has_dividend_record and tx_date and account_id:
                            dividend_hash = make_avanza_hash(
                                "DIVIDEND",
                                account_id,
                                source_account,
                                tx_date,
                                raw_type,
                                asset_identifier,
                                description,
                                quantity_value,
                                price_value,
                                amount_value,
                                instrument_currency,
                                fees_value,
                            )

                        preview_rows.append(
                            {
                                "row_number": row_number + 1,
                                "source_account": source_account,
                                "account_id": account_id,
                                "account": account_label,
                                "date": tx_date,
                                "raw_type": raw_type,
                                "security_action": security_action,
                                "movement_type": movement_type,
                                "description": description,
                                "isin": isin,
                                "asset_id": asset["id"] if asset else None,
                                "will_create_asset": will_create_asset,
                                "quantity": quantity_value,
                                "price": price_value,
                                "amount": amount_value,
                                "transaction_currency": transaction_currency,
                                "instrument_currency": instrument_currency,
                                "fees": fees_value,
                                "has_cash": has_cash_movement,
                                "has_dividend": has_dividend_record,
                                "security_hash": security_hash,
                                "cash_hash": cash_hash,
                                "dividend_hash": dividend_hash,
                                "error": "; ".join(errors) if errors else None,
                                "note": "; ".join(notes) if notes else None,
                            }
                        )

                    import_preview = pd.DataFrame(preview_rows)

                    # ------------------------------------------------------------
                    # 11D. DUPLICATE PROTECTION ACROSS OVERLAPPING EXPORTS
                    # ------------------------------------------------------------

                    existing_security_hashes = fetch_existing_hashes(
                        "transactions",
                        "transaction_hash",
                        import_preview["security_hash"].dropna().tolist(),
                    )
                    existing_cash_hashes = fetch_existing_hashes(
                        "cash_movements",
                        "transaction_hash",
                        import_preview["cash_hash"].dropna().tolist(),
                    )
                    existing_dividend_hashes = fetch_existing_hashes(
                        "dividends",
                        "transaction_hash",
                        import_preview["dividend_hash"].dropna().tolist(),
                    )

                    seen_security = set()
                    seen_cash = set()
                    seen_dividend = set()
                    component_rows = []

                    for _, preview_row in import_preview.iterrows():
                        sec_hash = preview_row["security_hash"]
                        cash_hash = preview_row["cash_hash"]
                        div_hash = preview_row["dividend_hash"]

                        security_needed = bool(sec_hash)
                        cash_needed = bool(cash_hash)
                        dividend_needed = bool(div_hash)

                        security_duplicate = False
                        cash_duplicate = False
                        dividend_duplicate = False

                        if sec_hash:
                            security_duplicate = (
                                sec_hash in existing_security_hashes or sec_hash in seen_security
                            )
                            seen_security.add(sec_hash)

                        if cash_hash:
                            cash_duplicate = cash_hash in existing_cash_hashes or cash_hash in seen_cash
                            seen_cash.add(cash_hash)

                        if div_hash:
                            dividend_duplicate = (
                                div_hash in existing_dividend_hashes or div_hash in seen_dividend
                            )
                            seen_dividend.add(div_hash)

                        security_to_import = security_needed and not security_duplicate
                        cash_to_import = cash_needed and not cash_duplicate
                        dividend_to_import = dividend_needed and not dividend_duplicate

                        if preview_row["error"]:
                            status = "❌ ERROR"
                        elif security_to_import or cash_to_import or dividend_to_import:
                            status = "➕ READY + NEW ASSET" if preview_row["will_create_asset"] else "✅ READY"
                        elif security_needed or cash_needed or dividend_needed:
                            status = "⚠️ DUPLICATE"
                        else:
                            status = "⏭ IGNORE"

                        component_rows.append(
                            {
                                "security_to_import": security_to_import,
                                "cash_to_import": cash_to_import,
                                "dividend_to_import": dividend_to_import,
                                "status": status,
                            }
                        )

                    components_df = pd.DataFrame(component_rows)
                    import_preview = pd.concat(
                        [import_preview.reset_index(drop=True), components_df],
                        axis=1,
                    )

                    # ------------------------------------------------------------
                    # 11E. SHOW WHAT WILL HAPPEN
                    # ------------------------------------------------------------

                    if new_asset_candidates:
                        st.subheader("New Investments Detected")
                        st.caption(
                            "These can be created automatically from ISIN/name data. Their Yahoo "
                            "Finance symbol will be blank until you set it under Edit Investment."
                        )
                        st.dataframe(
                            pd.DataFrame(new_asset_candidates.values())[
                                ["name", "ticker", "currency", "isin"]
                            ],
                            use_container_width=True,
                            hide_index=True,
                        )

                    st.subheader("Import Preview")
                    preview_display = import_preview[
                        [
                            "row_number",
                            "account",
                            "date",
                            "raw_type",
                            "description",
                            "isin",
                            "quantity",
                            "price",
                            "amount",
                            "transaction_currency",
                            "status",
                            "error",
                            "note",
                        ]
                    ].copy()
                    preview_display.columns = [
                        "Row",
                        "Account",
                        "Date",
                        "Avanza Type",
                        "Investment / Description",
                        "ISIN",
                        "Quantity",
                        "Price",
                        "Cash Amount",
                        "Cash Currency",
                        "Status",
                        "Error",
                        "Note",
                    ]
                    st.dataframe(
                        preview_display,
                        use_container_width=True,
                        hide_index=True,
                    )

                    ready_rows = import_preview[
                        import_preview["status"].isin(["✅ READY", "➕ READY + NEW ASSET"])
                    ]
                    error_rows = import_preview[import_preview["status"] == "❌ ERROR"]
                    duplicate_rows = import_preview[import_preview["status"] == "⚠️ DUPLICATE"]
                    ignored_rows = import_preview[import_preview["status"] == "⏭ IGNORE"]

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Ready", len(ready_rows))
                    c2.metric("Duplicates", len(duplicate_rows))
                    c3.metric("Ignored", len(ignored_rows))
                    c4.metric("Errors", len(error_rows))

                    if not error_rows.empty:
                        st.error(
                            "There are rows with errors. Fix the account/security data before importing."
                        )
                    elif ready_rows.empty:
                        st.info("There is nothing new to import from this file.")
                    else:
                        st.warning(
                            "Only press Import after the preview looks right. The cash balance is "
                            "correct only if your export includes the full relevant cash history "
                            "or you later add an opening-balance adjustment."
                        )

                        confirm_import = st.button(
                            f"Import {len(ready_rows)} Avanza Row(s)",
                            type="primary",
                        )

                        if confirm_import:
                            try:
                                # ------------------------------------------------
                                # Create one import batch per source account.
                                # This supports Avanza exports containing multiple accounts.
                                # ------------------------------------------------
                                batch_ids = {}
                                for source_account in ready_rows["source_account"].unique():
                                    account_id = source_to_account[source_account]
                                    account_file_hash = hashlib.sha256(
                                        f"{base_file_hash}|{source_account}".encode("utf-8")
                                    ).hexdigest()

                                    cursor.execute(
                                        """
                                        SELECT id
                                        FROM import_batches
                                        WHERE file_hash = %s
                                        LIMIT 1;
                                        """,
                                        (account_file_hash,),
                                    )
                                    existing_batch = cursor.fetchone()

                                    if existing_batch:
                                        batch_ids[source_account] = int(existing_batch["id"])
                                    else:
                                        cursor.execute(
                                            """
                                            INSERT INTO import_batches (
                                                account_id, file_name, file_hash, row_count
                                            )
                                            VALUES (%s, %s, %s, 0);
                                            """,
                                            (
                                                account_id,
                                                uploaded_file.name,
                                                account_file_hash,
                                            ),
                                        )
                                        batch_ids[source_account] = cursor.lastrowid

                                # ------------------------------------------------
                                # Create unknown assets from ISIN/name.
                                # ------------------------------------------------
                                created_asset_ids = {}
                                for isin, candidate in new_asset_candidates.items():
                                    cursor.execute(
                                        "SELECT id FROM assets WHERE isin = %s LIMIT 1;",
                                        (isin,),
                                    )
                                    existing_asset = cursor.fetchone()
                                    if existing_asset:
                                        created_asset_ids[isin] = int(existing_asset["id"])
                                        continue

                                    cursor.execute(
                                        """
                                        INSERT INTO assets (
                                            ticker,
                                            name,
                                            asset_type,
                                            currency,
                                            market_symbol,
                                            isin
                                        )
                                        VALUES (%s, %s, 'Other', %s, NULL, %s);
                                        """,
                                        (
                                            candidate["ticker"],
                                            candidate["name"],
                                            candidate["currency"],
                                            candidate["isin"],
                                        ),
                                    )
                                    created_asset_ids[isin] = cursor.lastrowid

                                # Fill missing ISINs on investments that were matched by name.
                                for _, mapped_row in ready_rows.iterrows():
                                    if pd.notna(mapped_row["asset_id"]):
                                        mapped_isin = normalize_isin(mapped_row["isin"])
                                        if mapped_isin:
                                            cursor.execute(
                                                """
                                                UPDATE assets
                                                SET isin = %s
                                                WHERE id = %s
                                                  AND (isin IS NULL OR isin = '');
                                                """,
                                                (mapped_isin, int(mapped_row["asset_id"])),
                                            )

                                # Refresh ISIN -> asset id lookup after creation.
                                cursor.execute("SELECT id, isin FROM assets WHERE isin IS NOT NULL;")
                                asset_id_by_isin = {
                                    normalize_isin(r["isin"]): int(r["id"])
                                    for r in cursor.fetchall()
                                    if normalize_isin(r["isin"])
                                }

                                inserted_transactions = 0
                                inserted_dividends = 0
                                inserted_cash = 0
                                batch_counts = {key: 0 for key in batch_ids}

                                for _, import_row in ready_rows.iterrows():
                                    source_account = import_row["source_account"]
                                    account_id = int(import_row["account_id"])
                                    import_batch_id = batch_ids[source_account]
                                    tx_date = import_row["date"]
                                    isin = normalize_isin(import_row["isin"])

                                    asset_id = None
                                    if pd.notna(import_row["asset_id"]):
                                        asset_id = int(import_row["asset_id"])
                                    elif isin:
                                        asset_id = asset_id_by_isin.get(isin)

                                    # --------------------------------------------
                                    # BUY / SELL security transaction
                                    # --------------------------------------------
                                    if import_row["security_to_import"]:
                                        if asset_id is None:
                                            raise ValueError(
                                                f"Could not resolve asset for row {int(import_row['row_number'])}."
                                            )

                                        asset_currency = normalize_currency(
                                            import_row["instrument_currency"],
                                            "SEK",
                                        )
                                        fx_rate = get_fx_rate_to_sek(asset_currency, tx_date)

                                        cursor.execute(
                                            """
                                            INSERT IGNORE INTO transactions (
                                                asset_id,
                                                account_id,
                                                transaction_type,
                                                quantity,
                                                price,
                                                fees,
                                                transaction_date,
                                                fx_rate_to_sek,
                                                transaction_hash,
                                                import_batch_id,
                                                source
                                            )
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'AVANZA');
                                            """,
                                            (
                                                asset_id,
                                                account_id,
                                                import_row["security_action"],
                                                float(import_row["quantity"]),
                                                float(import_row["price"]),
                                                float(import_row["fees"]),
                                                tx_date,
                                                fx_rate,
                                                import_row["security_hash"],
                                                import_batch_id,
                                            ),
                                        )
                                        inserted_transactions += cursor.rowcount
                                        batch_counts[source_account] += cursor.rowcount

                                    # --------------------------------------------
                                    # Dividend detail record
                                    # --------------------------------------------
                                    if import_row["dividend_to_import"]:
                                        if asset_id is None:
                                            raise ValueError(
                                                f"Could not resolve dividend asset for row {int(import_row['row_number'])}."
                                            )

                                        dividend_currency = normalize_currency(
                                            import_row["instrument_currency"],
                                            "SEK",
                                        )
                                        quantity_value = float(import_row["quantity"])
                                        dps_value = float(import_row["price"])
                                        cash_amount = abs(float(import_row["amount"]))

                                        if (
                                            normalize_currency(import_row["transaction_currency"]) == "SEK"
                                            and quantity_value > 0
                                            and dps_value > 0
                                            and cash_amount > 0
                                        ):
                                            dividend_fx = cash_amount / (quantity_value * dps_value)
                                        else:
                                            dividend_fx = get_fx_rate_to_sek(
                                                dividend_currency,
                                                tx_date,
                                            )

                                        cursor.execute(
                                            """
                                            INSERT IGNORE INTO dividends (
                                                asset_id,
                                                account_id,
                                                payment_date,
                                                dividend_per_share,
                                                shares_held,
                                                currency,
                                                fx_rate_to_sek,
                                                transaction_hash,
                                                import_batch_id,
                                                source
                                            )
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'AVANZA');
                                            """,
                                            (
                                                asset_id,
                                                account_id,
                                                tx_date,
                                                dps_value,
                                                quantity_value,
                                                dividend_currency,
                                                dividend_fx,
                                                import_row["dividend_hash"],
                                                import_batch_id,
                                            ),
                                        )
                                        inserted_dividends += cursor.rowcount
                                        batch_counts[source_account] += cursor.rowcount

                                    # --------------------------------------------
                                    # Exact cash movement from Avanza Belopp
                                    # --------------------------------------------
                                    if import_row["cash_to_import"]:
                                        cash_currency = normalize_currency(
                                            import_row["transaction_currency"],
                                            "SEK",
                                        )
                                        cash_fx = get_fx_rate_to_sek(cash_currency, tx_date)

                                        cursor.execute(
                                            """
                                            INSERT IGNORE INTO cash_movements (
                                                account_id,
                                                movement_date,
                                                movement_type,
                                                description,
                                                amount,
                                                currency,
                                                fx_rate_to_sek,
                                                transaction_hash,
                                                import_batch_id,
                                                source
                                            )
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'AVANZA');
                                            """,
                                            (
                                                account_id,
                                                tx_date,
                                                import_row["movement_type"],
                                                import_row["description"] or import_row["raw_type"],
                                                float(import_row["amount"]),
                                                cash_currency,
                                                cash_fx,
                                                import_row["cash_hash"],
                                                import_batch_id,
                                            ),
                                        )
                                        inserted_cash += cursor.rowcount
                                        batch_counts[source_account] += cursor.rowcount

                                for source_account, batch_id in batch_ids.items():
                                    cursor.execute(
                                        """
                                        UPDATE import_batches
                                        SET row_count = %s
                                        WHERE id = %s;
                                        """,
                                        (batch_counts[source_account], batch_id),
                                    )

                                connection.commit()

                                created_count = len(created_asset_ids)
                                st.session_state["csv_import_success"] = (
                                    f"✅ Import complete: {inserted_transactions} BUY/SELL, "
                                    f"{inserted_dividends} dividends, {inserted_cash} cash movements, "
                                    f"{created_count} new investment(s)."
                                )
                                st.rerun()

                            except Exception as error:
                                connection.rollback()
                                st.error(f"Import failed and was rolled back: {error}")




# ============================================================


# ============================================================
# 23E. NORDNET CSV IMPORTER
# ============================================================

st.divider()

with st.expander("📥 Import Nordnet CSV"):
    st.caption(
        "The Nordnet importer reads the UTF-16/tab-separated transaction export, "
        "maps each depot to one of your accounts, imports trades, dividends and "
        "true cash movements, and handles 1:1 security exchanges plus stock splits. "
        "Nothing is written until you press Import."
    )

    if accounts.empty:
        st.warning("Create your Nordnet account in the sidebar first.")
    else:
        nordnet_file = st.file_uploader(
            "Choose Nordnet CSV file",
            type=["csv"],
            key="nordnet_csv_upload",
        )

        if nordnet_file is not None:
            nordnet_bytes = nordnet_file.getvalue()
            nordnet_base_hash = hashlib.sha256(nordnet_bytes).hexdigest()

            try:
                nordnet_data = read_nordnet_csv(nordnet_bytes)
            except Exception as error:
                st.error(f"Could not read the Nordnet file: {error}")
                nordnet_data = None

            nordnet_required = {
                "Id",
                "Bokföringsdag",
                "Affärsdag",
                "Depå",
                "Transaktionstyp",
                "Värdepapper",
                "ISIN",
                "Antal",
                "Kurs",
                "Total Avgift",
                "Belopp",
                "Valuta.1",
                "Växlingskurs",
                "Transaktionstext",
                "Verifikationsnummer",
            }

            if nordnet_data is not None:
                nordnet_missing = sorted(nordnet_required - set(nordnet_data.columns))

                if nordnet_missing:
                    st.error(
                        "This does not look like the Nordnet export expected by this importer. "
                        f"Missing columns: {', '.join(nordnet_missing)}"
                    )
                else:
                    st.write(f"Rows found: {len(nordnet_data)}")
                    st.subheader("Raw Nordnet Preview")
                    st.dataframe(
                        nordnet_data.head(20),
                        use_container_width=True,
                        hide_index=True,
                    )

                    # ------------------------------------------------------------
                    # 11N-A. MAP EACH NORDNET DEPOT TO A DATABASE ACCOUNT
                    # ------------------------------------------------------------

                    source_depots = []
                    for value in nordnet_data["Depå"].tolist():
                        depot = normalize_account_ref(value)
                        if depot not in source_depots:
                            source_depots.append(depot)

                    nordnet_account_options = {
                        f"{row['broker']} — {row['account_name']} ({row['account_type']})": int(row["id"])
                        for _, row in accounts.iterrows()
                    }
                    nordnet_account_label_by_id = {
                        int(row["id"]): f"{row['broker']} — {row['account_name']} ({row['account_type']})"
                        for _, row in accounts.iterrows()
                    }

                    st.subheader("Match Nordnet Accounts")
                    source_depot_to_account = {}

                    for depot_index, source_depot in enumerate(source_depots):
                        account_label = st.selectbox(
                            f"CSV depot {source_depot}",
                            list(nordnet_account_options.keys()),
                            key=f"nordnet_account_map_{depot_index}_{source_depot}",
                        )
                        source_depot_to_account[source_depot] = nordnet_account_options[account_label]

                    if len(set(source_depot_to_account.values())) < len(source_depot_to_account.values()):
                        st.warning(
                            "Two Nordnet depots are mapped to the same local account. "
                            "That is allowed, but make sure it is intentional."
                        )

                    # ------------------------------------------------------------
                    # 11N-B. BUILD 1:1 SECURITY-EXCHANGE MAP
                    # ------------------------------------------------------------

                    exchange_map = {}
                    exchange_target_name = {}
                    manual_exchange_warnings = []

                    exchange_rows = nordnet_data[
                        nordnet_data["Transaktionstyp"].isin(["BYTE UTTAG VP", "BYTE INLÄGG VP"])
                    ]

                    for verification, group in exchange_rows.groupby(
                        "Verifikationsnummer",
                        dropna=False,
                    ):
                        outgoing = group[group["Transaktionstyp"] == "BYTE UTTAG VP"]
                        incoming = group[group["Transaktionstyp"] == "BYTE INLÄGG VP"]

                        if len(outgoing) == 1 and len(incoming) == 1:
                            old_isin = normalize_isin(outgoing.iloc[0]["ISIN"])
                            new_isin = normalize_isin(incoming.iloc[0]["ISIN"])
                            old_qty = parse_number(outgoing.iloc[0]["Antal"])
                            new_qty = parse_number(incoming.iloc[0]["Antal"])

                            if old_isin and new_isin and old_qty > 0 and new_qty > 0:
                                ratio = new_qty / old_qty
                                if abs(ratio - 1.0) < 1e-9:
                                    if old_isin != new_isin:
                                        exchange_map[old_isin] = new_isin
                                        exchange_target_name[old_isin] = clean_text(
                                            incoming.iloc[0]["Värdepapper"]
                                        )
                                else:
                                    manual_exchange_warnings.append(
                                        f"{clean_text(outgoing.iloc[0]['Värdepapper'])} → "
                                        f"{clean_text(incoming.iloc[0]['Värdepapper'])}: "
                                        f"ratio {new_qty:g}:{old_qty:g}"
                                    )

                    def canonical_nordnet_isin(isin):
                        isin = normalize_isin(isin)
                        seen = set()
                        while isin in exchange_map and isin not in seen:
                            seen.add(isin)
                            isin = exchange_map[isin]
                        return isin

                    if manual_exchange_warnings:
                        st.warning(
                            "Some non-1:1 security exchanges need manual review: "
                            + "; ".join(manual_exchange_warnings)
                        )

                    # ------------------------------------------------------------
                    # 11N-C. BUILD STOCK-SPLIT EVENTS
                    # ------------------------------------------------------------

                    split_events = []
                    split_rows = nordnet_data[
                        nordnet_data["Transaktionstyp"].isin(["SPLIT UTTAG VP", "SPLIT INLÄGG VP"])
                    ]

                    for verification, group in split_rows.groupby(
                        "Verifikationsnummer",
                        dropna=False,
                    ):
                        outgoing = group[group["Transaktionstyp"] == "SPLIT UTTAG VP"]
                        incoming = group[group["Transaktionstyp"] == "SPLIT INLÄGG VP"]

                        if len(outgoing) == 1 and len(incoming) == 1:
                            old_qty = parse_number(outgoing.iloc[0]["Antal"])
                            new_qty = parse_number(incoming.iloc[0]["Antal"])
                            split_isin = canonical_nordnet_isin(incoming.iloc[0]["ISIN"])
                            split_date_raw = incoming.iloc[0]["Affärsdag"]
                            split_date_parsed = pd.to_datetime(split_date_raw, errors="coerce")

                            if (
                                split_isin
                                and old_qty > 0
                                and new_qty > 0
                                and not pd.isna(split_date_parsed)
                            ):
                                split_events.append(
                                    {
                                        "isin": split_isin,
                                        "date": split_date_parsed.date(),
                                        "ratio_new": new_qty,
                                        "ratio_old": old_qty,
                                        "description": clean_text(incoming.iloc[0]["Värdepapper"]),
                                        "verification": clean_text(verification),
                                        "source_depot": normalize_account_ref(incoming.iloc[0]["Depå"]),
                                    }
                                )

                    # ------------------------------------------------------------
                    # 11N-D. EXISTING-ASSET LOOKUPS
                    # ------------------------------------------------------------

                    nordnet_assets_by_isin = {}
                    nordnet_assets_by_name = {}
                    nordnet_existing_tickers = set()

                    for _, asset_row in assets.iterrows():
                        asset_info = {
                            "id": int(asset_row["id"]),
                            "ticker": clean_text(asset_row["ticker"]).upper(),
                            "name": clean_text(asset_row["name"]),
                            "currency": normalize_currency(asset_row["currency"]),
                            "isin": normalize_isin(asset_row.get("isin", "")),
                        }
                        nordnet_existing_tickers.add(asset_info["ticker"])

                        if asset_info["isin"]:
                            nordnet_assets_by_isin[asset_info["isin"]] = asset_info

                        for key in {asset_info["ticker"], asset_info["name"].upper()}:
                            if key:
                                nordnet_assets_by_name[key] = asset_info

                    # ------------------------------------------------------------
                    # 11N-E. PARSE ROWS INTO PREVIEW
                    # ------------------------------------------------------------

                    nordnet_preview_rows = []
                    nordnet_new_assets = {}

                    security_types = {
                        "KÖPT": "BUY",
                        "SÅLT": "SELL",
                        "TECKNING INLÄGG VP": "BUY",
                        "UTDELNING INLÄGG VP": "BUY",
                        "DECIMALER UTTAG VP": "SELL",
                    }

                    for row_number, row in nordnet_data.iterrows():
                        errors = []
                        notes = []

                        source_id = clean_text(row["Id"])
                        source_depot = normalize_account_ref(row["Depå"])
                        account_id = source_depot_to_account.get(source_depot)
                        account_label = nordnet_account_label_by_id.get(account_id, "Unmapped")

                        book_parsed = pd.to_datetime(row["Bokföringsdag"], errors="coerce")
                        trade_parsed = pd.to_datetime(row["Affärsdag"], errors="coerce")
                        book_date = None if pd.isna(book_parsed) else book_parsed.date()
                        trade_date = (
                            book_date if pd.isna(trade_parsed) else trade_parsed.date()
                        )

                        if book_date is None:
                            errors.append("Invalid booking date")

                        raw_type = clean_text(row["Transaktionstyp"]).upper()
                        description = clean_text(row["Värdepapper"])
                        raw_isin = normalize_isin(row["ISIN"])
                        canonical_isin = canonical_nordnet_isin(raw_isin)
                        canonical_description = exchange_target_name.get(raw_isin, description)

                        try:
                            quantity_value = parse_number(row["Antal"])
                            price_value = parse_number(row["Kurs"])
                            amount_value = parse_number(row["Belopp"])
                            fee_sek = parse_number(row["Total Avgift"])
                            exchange_rate_value = parse_number(row["Växlingskurs"])
                            saldo_value = parse_number(row["Saldo"])
                        except Exception:
                            quantity_value = 0.0
                            price_value = 0.0
                            amount_value = 0.0
                            fee_sek = 0.0
                            exchange_rate_value = 0.0
                            saldo_value = 0.0
                            errors.append("Invalid numeric value")

                        security_action = security_types.get(raw_type)
                        free_security = raw_type in {"UTDELNING INLÄGG VP", "DECIMALER UTTAG VP"}
                        subscription_security = raw_type == "TECKNING INLÄGG VP"
                        dividend_record = raw_type == "UTDELNING"
                        cash_effect = nordnet_has_cash_effect(raw_type) and abs(amount_value) > 1e-12

                        trade_currency = nordnet_trade_currency(
                            canonical_isin or raw_isin,
                            exchange_rate_value,
                        )

                        # Existing asset: canonical ISIN first, then original ISIN, then name.
                        asset = None
                        if canonical_isin and canonical_isin in nordnet_assets_by_isin:
                            asset = nordnet_assets_by_isin[canonical_isin]
                        elif raw_isin and raw_isin in nordnet_assets_by_isin:
                            asset = nordnet_assets_by_isin[raw_isin]
                        elif canonical_description.upper() in nordnet_assets_by_name:
                            asset = nordnet_assets_by_name[canonical_description.upper()]
                        elif description.upper() in nordnet_assets_by_name:
                            asset = nordnet_assets_by_name[description.upper()]

                        needs_asset = security_action is not None or dividend_record
                        will_create_asset = False

                        if needs_asset and asset is None:
                            if canonical_isin:
                                will_create_asset = True
                                if canonical_isin not in nordnet_new_assets:
                                    candidate_currency = trade_currency
                                    if dividend_record:
                                        candidate_currency = nordnet_country_currency(canonical_isin)
                                        if canonical_isin.startswith("SE"):
                                            candidate_currency = "SEK"

                                    temp_ticker = make_placeholder_ticker(
                                        canonical_description or description or "Imported Asset",
                                        canonical_isin,
                                        nordnet_existing_tickers
                                        | {item["ticker"] for item in nordnet_new_assets.values()},
                                    )
                                    nordnet_new_assets[canonical_isin] = {
                                        "isin": canonical_isin,
                                        "name": canonical_description or description or f"Imported {canonical_isin}",
                                        "ticker": temp_ticker,
                                        "currency": candidate_currency,
                                    }
                                elif trade_currency != "SEK" and exchange_rate_value > 0:
                                    nordnet_new_assets[canonical_isin]["currency"] = trade_currency

                                notes.append("New investment will be created")
                            else:
                                errors.append("Security has no usable ISIN and is not in your investment list")

                        # Standard trades and paid subscriptions need positive quantity/price.
                        if raw_type in {"KÖPT", "SÅLT", "TECKNING INLÄGG VP"}:
                            if quantity_value <= 0:
                                errors.append("Security quantity must be > 0")
                            if price_value <= 0:
                                errors.append("Security price must be > 0")

                        # Free stock distributions / fractional removals have zero cost/proceeds.
                        transaction_price = 0.0 if free_security else price_value

                        # Nordnet reports Total Avgift in SEK. Convert it back to the
                        # instrument currency because our ledger multiplies fees by FX.
                        if trade_currency == "SEK":
                            transaction_fx = 1.0
                            transaction_fee = fee_sek
                        else:
                            if exchange_rate_value > 0:
                                transaction_fx = exchange_rate_value
                            else:
                                transaction_fx = None

                            transaction_fee = (
                                fee_sek / transaction_fx
                                if transaction_fx and transaction_fx > 0
                                else 0.0
                            )

                        # Dividend metadata.
                        dividend_currency = None
                        dividend_fx = None
                        has_dividend = False
                        if dividend_record and quantity_value > 0 and price_value > 0:
                            dividend_currency = nordnet_dividend_currency(
                                row["Transaktionstext"],
                                canonical_isin or raw_isin,
                            )
                            if abs(amount_value) > 1e-12:
                                dividend_fx = abs(amount_value) / (quantity_value * price_value)
                            has_dividend = True
                        elif dividend_record:
                            notes.append("Dividend will count as cash only because shares/DPS are missing")

                        security_hash = None
                        if security_action and trade_date and account_id and source_id:
                            security_hash = nordnet_component_hash(
                                "SECURITY",
                                account_id,
                                source_depot,
                                source_id,
                            )

                        cash_hash = None
                        if cash_effect and book_date and account_id and source_id:
                            cash_hash = nordnet_component_hash(
                                "CASH",
                                account_id,
                                source_depot,
                                source_id,
                            )

                        dividend_hash = None
                        if has_dividend and book_date and account_id and source_id:
                            dividend_hash = nordnet_component_hash(
                                "DIVIDEND",
                                account_id,
                                source_depot,
                                source_id,
                            )

                        if (
                            security_action is None
                            and not cash_effect
                            and not has_dividend
                            and raw_type not in {"SPLIT INLÄGG VP", "SPLIT UTTAG VP"}
                        ):
                            if raw_type in {
                                "BYTE INLÄGG VP",
                                "BYTE UTTAG VP",
                                "TECKNING UT RÄTTER",
                                "TILLDELNING INLÄGG",
                            }:
                                notes.append("Corporate-action bookkeeping row; handled/ignored safely")
                            else:
                                notes.append("No supported cash/security component; row will be ignored")

                        nordnet_preview_rows.append(
                            {
                                "row_number": row_number + 1,
                                "source_id": source_id,
                                "source_depot": source_depot,
                                "account_id": account_id,
                                "account": account_label,
                                "book_date": book_date,
                                "trade_date": trade_date,
                                "raw_type": raw_type,
                                "description": description,
                                "canonical_description": canonical_description,
                                "raw_isin": raw_isin,
                                "isin": canonical_isin,
                                "asset_id": asset["id"] if asset else None,
                                "will_create_asset": will_create_asset,
                                "security_action": security_action,
                                "quantity": quantity_value,
                                "price": transaction_price,
                                "raw_price": price_value,
                                "fees": transaction_fee,
                                "fee_sek": fee_sek,
                                "trade_currency": trade_currency,
                                "transaction_fx": transaction_fx,
                                "cash_amount": amount_value,
                                "cash_currency": normalize_currency(row["Valuta.1"], "SEK"),
                                "cash_effect": cash_effect,
                                "movement_type": nordnet_cash_type(raw_type),
                                "has_dividend": has_dividend,
                                "dividend_currency": dividend_currency,
                                "dividend_fx": dividend_fx,
                                "security_hash": security_hash,
                                "cash_hash": cash_hash,
                                "dividend_hash": dividend_hash,
                                "error": "; ".join(errors) if errors else None,
                                "note": "; ".join(notes) if notes else None,
                                "saldo": saldo_value,
                            }
                        )

                    nordnet_preview = pd.DataFrame(nordnet_preview_rows)

                    # ------------------------------------------------------------
                    # 11N-F. DUPLICATE PROTECTION
                    # ------------------------------------------------------------

                    nordnet_existing_security_hashes = fetch_existing_hashes(
                        "transactions",
                        "transaction_hash",
                        nordnet_preview["security_hash"].dropna().tolist(),
                    )
                    nordnet_existing_cash_hashes = fetch_existing_hashes(
                        "cash_movements",
                        "transaction_hash",
                        nordnet_preview["cash_hash"].dropna().tolist(),
                    )
                    nordnet_existing_dividend_hashes = fetch_existing_hashes(
                        "dividends",
                        "transaction_hash",
                        nordnet_preview["dividend_hash"].dropna().tolist(),
                    )

                    nordnet_seen_security = set()
                    nordnet_seen_cash = set()
                    nordnet_seen_dividend = set()
                    nordnet_components = []

                    for _, preview_row in nordnet_preview.iterrows():
                        sec_hash = preview_row["security_hash"]
                        cash_hash = preview_row["cash_hash"]
                        div_hash = preview_row["dividend_hash"]

                        security_needed = bool(sec_hash)
                        cash_needed = bool(cash_hash)
                        dividend_needed = bool(div_hash)

                        security_duplicate = False
                        cash_duplicate = False
                        dividend_duplicate = False

                        if sec_hash:
                            security_duplicate = (
                                sec_hash in nordnet_existing_security_hashes
                                or sec_hash in nordnet_seen_security
                            )
                            nordnet_seen_security.add(sec_hash)

                        if cash_hash:
                            cash_duplicate = (
                                cash_hash in nordnet_existing_cash_hashes
                                or cash_hash in nordnet_seen_cash
                            )
                            nordnet_seen_cash.add(cash_hash)

                        if div_hash:
                            dividend_duplicate = (
                                div_hash in nordnet_existing_dividend_hashes
                                or div_hash in nordnet_seen_dividend
                            )
                            nordnet_seen_dividend.add(div_hash)

                        security_to_import = security_needed and not security_duplicate
                        cash_to_import = cash_needed and not cash_duplicate
                        dividend_to_import = dividend_needed and not dividend_duplicate

                        if preview_row["error"]:
                            status = "❌ ERROR"
                        elif security_to_import or cash_to_import or dividend_to_import:
                            status = (
                                "➕ READY + NEW ASSET"
                                if preview_row["will_create_asset"]
                                else "✅ READY"
                            )
                        elif security_needed or cash_needed or dividend_needed:
                            status = "⚠️ DUPLICATE"
                        else:
                            status = "⏭ IGNORE"

                        nordnet_components.append(
                            {
                                "security_to_import": security_to_import,
                                "cash_to_import": cash_to_import,
                                "dividend_to_import": dividend_to_import,
                                "status": status,
                            }
                        )

                    nordnet_preview = pd.concat(
                        [
                            nordnet_preview.reset_index(drop=True),
                            pd.DataFrame(nordnet_components),
                        ],
                        axis=1,
                    )

                    # ------------------------------------------------------------
                    # 11N-G. CASH RECONCILIATION
                    # ------------------------------------------------------------

                    st.subheader("Cash Reconciliation")
                    st.caption(
                        "Nordnet includes some corporate-action rows where Belopp is non-zero "
                        "without changing Saldo. The importer excludes those from cash."
                    )

                    reconciliation_rows = []
                    for source_depot in source_depots:
                        depot_rows = nordnet_preview[
                            nordnet_preview["source_depot"] == source_depot
                        ].copy()
                        file_cash = depot_rows.loc[
                            depot_rows["cash_effect"], "cash_amount"
                        ].astype(float).sum()

                        raw_depot = nordnet_data[
                            nordnet_data["Depå"].apply(normalize_account_ref) == source_depot
                        ].copy()
                        raw_depot["_book"] = pd.to_datetime(
                            raw_depot["Bokföringsdag"],
                            errors="coerce",
                        )
                        raw_depot["_id_num"] = pd.to_numeric(
                            raw_depot["Id"],
                            errors="coerce",
                        )
                        raw_depot = raw_depot.sort_values(
                            ["_book", "_id_num"],
                            ascending=[True, True],
                        )
                        latest_saldo = 0.0
                        if not raw_depot.empty:
                            latest_saldo = parse_number(raw_depot.iloc[-1]["Saldo"])

                        difference = file_cash - latest_saldo
                        reconciliation_rows.append(
                            {
                                "Depot": source_depot,
                                "Imported cash movements (SEK)": file_cash,
                                "Latest Nordnet saldo (SEK)": latest_saldo,
                                "Difference (SEK)": difference,
                                "Check": "✅" if abs(difference) < 0.02 else "⚠️",
                            }
                        )

                    reconciliation_df = pd.DataFrame(reconciliation_rows)
                    st.dataframe(
                        reconciliation_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                    # ------------------------------------------------------------
                    # 11N-H. PREVIEW + SPLITS
                    # ------------------------------------------------------------

                    if nordnet_new_assets:
                        st.subheader("New Investments Detected")
                        st.caption(
                            "They will be created from Nordnet's ISIN/name data. "
                            "Yahoo Finance symbols stay blank until you set them under Edit Investment."
                        )
                        st.dataframe(
                            pd.DataFrame(nordnet_new_assets.values())[
                                ["name", "ticker", "currency", "isin"]
                            ],
                            use_container_width=True,
                            hide_index=True,
                        )

                    if split_events:
                        st.subheader("Stock Splits Detected")
                        st.dataframe(
                            pd.DataFrame(split_events)[
                                ["date", "description", "isin", "ratio_new", "ratio_old"]
                            ],
                            use_container_width=True,
                            hide_index=True,
                        )

                    st.subheader("Nordnet Import Preview")
                    nordnet_preview_display = nordnet_preview[
                        [
                            "row_number",
                            "account",
                            "book_date",
                            "trade_date",
                            "raw_type",
                            "canonical_description",
                            "isin",
                            "quantity",
                            "raw_price",
                            "cash_amount",
                            "status",
                            "error",
                            "note",
                        ]
                    ].copy()
                    nordnet_preview_display.columns = [
                        "Row",
                        "Account",
                        "Booking Date",
                        "Trade Date",
                        "Nordnet Type",
                        "Investment / Description",
                        "ISIN",
                        "Quantity",
                        "Price",
                        "Cash Amount",
                        "Status",
                        "Error",
                        "Note",
                    ]
                    st.dataframe(
                        nordnet_preview_display,
                        use_container_width=True,
                        hide_index=True,
                    )

                    nordnet_ready = nordnet_preview[
                        nordnet_preview["status"].isin(["✅ READY", "➕ READY + NEW ASSET"])
                    ]
                    nordnet_errors = nordnet_preview[nordnet_preview["status"] == "❌ ERROR"]
                    nordnet_duplicates = nordnet_preview[nordnet_preview["status"] == "⚠️ DUPLICATE"]
                    nordnet_ignored = nordnet_preview[nordnet_preview["status"] == "⏭ IGNORE"]

                    n1, n2, n3, n4 = st.columns(4)
                    n1.metric("Ready", len(nordnet_ready))
                    n2.metric("Duplicates", len(nordnet_duplicates))
                    n3.metric("Ignored", len(nordnet_ignored))
                    n4.metric("Errors", len(nordnet_errors))

                    reconciliation_ok = (
                        not reconciliation_df.empty
                        and reconciliation_df["Difference (SEK)"].abs().max() < 0.02
                    )

                    if not reconciliation_ok:
                        st.error(
                            "Cash does not reconcile to Nordnet's latest Saldo. "
                            "Do not import until the difference is understood."
                        )
                    elif not nordnet_errors.empty:
                        st.error("There are rows with errors. Do not import yet.")
                    elif manual_exchange_warnings:
                        st.error("A non-1:1 security exchange needs manual review before import.")
                    elif nordnet_ready.empty and not split_events:
                        st.info("There is nothing new to import from this Nordnet file.")
                    else:
                        st.success(
                            "Cash reconciles to Nordnet's latest Saldo. Review the securities, "
                            "then import when the preview looks right."
                        )

                        confirm_nordnet_import = st.button(
                            f"Import Nordnet History ({len(nordnet_ready)} row(s))",
                            type="primary",
                            key="confirm_nordnet_import",
                        )

                        if confirm_nordnet_import:
                            try:
                                # ------------------------------------------------
                                # One batch per Nordnet depot.
                                # ------------------------------------------------
                                nordnet_batch_ids = {}
                                for source_depot in source_depots:
                                    account_id = source_depot_to_account[source_depot]
                                    depot_file_hash = hashlib.sha256(
                                        f"{nordnet_base_hash}|NORDNET|{source_depot}".encode("utf-8")
                                    ).hexdigest()

                                    cursor.execute(
                                        "SELECT id FROM import_batches WHERE file_hash = %s LIMIT 1;",
                                        (depot_file_hash,),
                                    )
                                    existing_batch = cursor.fetchone()

                                    if existing_batch:
                                        nordnet_batch_ids[source_depot] = int(existing_batch["id"])
                                    else:
                                        cursor.execute(
                                            """
                                            INSERT INTO import_batches (
                                                account_id, file_name, file_hash, row_count
                                            )
                                            VALUES (%s, %s, %s, 0);
                                            """,
                                            (
                                                account_id,
                                                nordnet_file.name,
                                                depot_file_hash,
                                            ),
                                        )
                                        nordnet_batch_ids[source_depot] = cursor.lastrowid

                                # ------------------------------------------------
                                # Create unknown assets.
                                # ------------------------------------------------
                                nordnet_created_asset_ids = {}
                                for isin, candidate in nordnet_new_assets.items():
                                    cursor.execute(
                                        "SELECT id FROM assets WHERE isin = %s LIMIT 1;",
                                        (isin,),
                                    )
                                    existing_asset = cursor.fetchone()

                                    if existing_asset:
                                        nordnet_created_asset_ids[isin] = int(existing_asset["id"])
                                        continue

                                    cursor.execute(
                                        """
                                        INSERT INTO assets (
                                            ticker, name, asset_type, currency, market_symbol, isin
                                        )
                                        VALUES (%s, %s, 'Other', %s, NULL, %s);
                                        """,
                                        (
                                            candidate["ticker"],
                                            candidate["name"],
                                            candidate["currency"],
                                            candidate["isin"],
                                        ),
                                    )
                                    nordnet_created_asset_ids[isin] = cursor.lastrowid

                                cursor.execute("SELECT id, isin, name FROM assets;")
                                refreshed_assets = cursor.fetchall()
                                nordnet_asset_id_by_isin = {
                                    normalize_isin(r["isin"]): int(r["id"])
                                    for r in refreshed_assets
                                    if normalize_isin(r.get("isin", ""))
                                }
                                nordnet_asset_id_by_name = {
                                    clean_text(r["name"]).upper(): int(r["id"])
                                    for r in refreshed_assets
                                    if clean_text(r["name"])
                                }

                                inserted_transactions = 0
                                inserted_dividends = 0
                                inserted_cash = 0
                                inserted_splits = 0
                                batch_counts = {key: 0 for key in nordnet_batch_ids}

                                # ------------------------------------------------
                                # Insert split actions before ledger data.
                                # ------------------------------------------------
                                for split_event in split_events:
                                    split_asset_id = nordnet_asset_id_by_isin.get(split_event["isin"])
                                    if split_asset_id is None:
                                        split_asset_id = nordnet_asset_id_by_name.get(
                                            clean_text(split_event["description"]).upper()
                                        )
                                    if split_asset_id is None:
                                        raise ValueError(
                                            f"Could not resolve split asset {split_event['description']}."
                                        )

                                    cursor.execute(
                                        """
                                        SELECT id
                                        FROM corporate_actions
                                        WHERE asset_id = %s
                                          AND action_date = %s
                                          AND action_type = 'SPLIT'
                                          AND ratio_new = %s
                                          AND ratio_old = %s
                                        LIMIT 1;
                                        """,
                                        (
                                            split_asset_id,
                                            split_event["date"],
                                            split_event["ratio_new"],
                                            split_event["ratio_old"],
                                        ),
                                    )
                                    if cursor.fetchone() is None:
                                        cursor.execute(
                                            """
                                            INSERT INTO corporate_actions (
                                                asset_id,
                                                action_date,
                                                action_type,
                                                ratio_new,
                                                ratio_old,
                                                notes,
                                                import_batch_id,
                                                source
                                            )
                                            VALUES (%s, %s, 'SPLIT', %s, %s, %s, %s, 'NORDNET');
                                            """,
                                            (
                                                split_asset_id,
                                                split_event["date"],
                                                split_event["ratio_new"],
                                                split_event["ratio_old"],
                                                f"Imported from Nordnet: {split_event['description']}",
                                                nordnet_batch_ids.get(split_event.get("source_depot")),
                                            ),
                                        )
                                        inserted_splits += cursor.rowcount
                                        if cursor.rowcount:
                                            split_depot = split_event.get("source_depot")
                                            if split_depot in batch_counts:
                                                batch_counts[split_depot] += cursor.rowcount

                                # Oldest first so same-day transaction ids follow chronology.
                                nordnet_ready_sorted = nordnet_ready.copy()
                                nordnet_ready_sorted["_source_id_num"] = pd.to_numeric(
                                    nordnet_ready_sorted["source_id"],
                                    errors="coerce",
                                )
                                nordnet_ready_sorted = nordnet_ready_sorted.sort_values(
                                    ["trade_date", "_source_id_num"],
                                    ascending=[True, True],
                                )

                                for _, import_row in nordnet_ready_sorted.iterrows():
                                    source_depot = import_row["source_depot"]
                                    account_id = int(import_row["account_id"])
                                    import_batch_id = nordnet_batch_ids[source_depot]
                                    isin = normalize_isin(import_row["isin"])

                                    asset_id = None
                                    if pd.notna(import_row["asset_id"]):
                                        asset_id = int(import_row["asset_id"])
                                    elif isin:
                                        asset_id = nordnet_asset_id_by_isin.get(isin)
                                    if asset_id is None:
                                        asset_id = nordnet_asset_id_by_name.get(
                                            clean_text(import_row["canonical_description"]).upper()
                                        )

                                    # --------------------------------------------
                                    # Security BUY/SELL (including subscription/free shares)
                                    # --------------------------------------------
                                    if import_row["security_to_import"]:
                                        if asset_id is None:
                                            raise ValueError(
                                                f"Could not resolve asset for Nordnet row "
                                                f"{int(import_row['row_number'])}."
                                            )

                                        tx_fx = import_row["transaction_fx"]
                                        if pd.isna(tx_fx) or not tx_fx or float(tx_fx) <= 0:
                                            tx_fx = get_fx_rate_to_sek(
                                                normalize_currency(import_row["trade_currency"]),
                                                import_row["trade_date"],
                                            )

                                        tx_fee = float(import_row["fees"])
                                        if (
                                            normalize_currency(import_row["trade_currency"]) != "SEK"
                                            and float(import_row["fee_sek"]) > 0
                                            and float(tx_fx) > 0
                                        ):
                                            tx_fee = float(import_row["fee_sek"]) / float(tx_fx)

                                        cursor.execute(
                                            """
                                            INSERT IGNORE INTO transactions (
                                                asset_id,
                                                account_id,
                                                transaction_type,
                                                quantity,
                                                price,
                                                fees,
                                                transaction_date,
                                                fx_rate_to_sek,
                                                external_transaction_id,
                                                transaction_hash,
                                                import_batch_id,
                                                source
                                            )
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'NORDNET');
                                            """,
                                            (
                                                asset_id,
                                                account_id,
                                                import_row["security_action"],
                                                float(import_row["quantity"]),
                                                float(import_row["price"]),
                                                tx_fee,
                                                import_row["trade_date"],
                                                float(tx_fx),
                                                f"NORDNET:{import_row['source_id']}",
                                                import_row["security_hash"],
                                                import_batch_id,
                                            ),
                                        )
                                        inserted_transactions += cursor.rowcount
                                        batch_counts[source_depot] += cursor.rowcount

                                    # --------------------------------------------
                                    # Cash dividend detail
                                    # --------------------------------------------
                                    if import_row["dividend_to_import"]:
                                        if asset_id is None:
                                            raise ValueError(
                                                f"Could not resolve dividend asset for Nordnet row "
                                                f"{int(import_row['row_number'])}."
                                            )

                                        div_fx = import_row["dividend_fx"]
                                        if pd.isna(div_fx) or not div_fx or float(div_fx) <= 0:
                                            div_fx = get_fx_rate_to_sek(
                                                normalize_currency(import_row["dividend_currency"]),
                                                import_row["book_date"],
                                            )

                                        cursor.execute(
                                            """
                                            INSERT IGNORE INTO dividends (
                                                asset_id,
                                                account_id,
                                                payment_date,
                                                dividend_per_share,
                                                shares_held,
                                                currency,
                                                fx_rate_to_sek,
                                                transaction_hash,
                                                import_batch_id,
                                                source
                                            )
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'NORDNET');
                                            """,
                                            (
                                                asset_id,
                                                account_id,
                                                import_row["book_date"],
                                                float(import_row["raw_price"]),
                                                float(import_row["quantity"]),
                                                normalize_currency(import_row["dividend_currency"]),
                                                float(div_fx),
                                                import_row["dividend_hash"],
                                                import_batch_id,
                                            ),
                                        )
                                        inserted_dividends += cursor.rowcount
                                        batch_counts[source_depot] += cursor.rowcount

                                    # --------------------------------------------
                                    # Exact Nordnet cash movement
                                    # --------------------------------------------
                                    if import_row["cash_to_import"]:
                                        cash_currency = normalize_currency(
                                            import_row["cash_currency"],
                                            "SEK",
                                        )
                                        cash_fx = get_fx_rate_to_sek(
                                            cash_currency,
                                            import_row["book_date"],
                                        )

                                        cursor.execute(
                                            """
                                            INSERT IGNORE INTO cash_movements (
                                                account_id,
                                                movement_date,
                                                movement_type,
                                                description,
                                                amount,
                                                currency,
                                                fx_rate_to_sek,
                                                transaction_hash,
                                                import_batch_id,
                                                source
                                            )
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'NORDNET');
                                            """,
                                            (
                                                account_id,
                                                import_row["book_date"],
                                                import_row["movement_type"],
                                                import_row["canonical_description"]
                                                or import_row["raw_type"],
                                                float(import_row["cash_amount"]),
                                                cash_currency,
                                                cash_fx,
                                                import_row["cash_hash"],
                                                import_batch_id,
                                            ),
                                        )
                                        inserted_cash += cursor.rowcount
                                        batch_counts[source_depot] += cursor.rowcount

                                for source_depot, batch_id in nordnet_batch_ids.items():
                                    cursor.execute(
                                        "UPDATE import_batches SET row_count = %s WHERE id = %s;",
                                        (batch_counts[source_depot], batch_id),
                                    )

                                connection.commit()

                                st.session_state["csv_import_success"] = (
                                    f"✅ Nordnet import complete: {inserted_transactions} security "
                                    f"transactions, {inserted_dividends} dividends, "
                                    f"{inserted_cash} cash movements, {inserted_splits} split(s), "
                                    f"{len(nordnet_created_asset_ids)} new investment(s)."
                                )
                                st.rerun()

                            except Exception as error:
                                connection.rollback()
                                st.error(f"Nordnet import failed and was rolled back: {error}")



# ============================================================
# 23E. MANAGE DATA + UNDO IMPORTS
# ============================================================

with st.expander("🛠 Manage Data / Undo Imports"):
    st.caption(
        "Edit or remove individual records, or undo an entire broker import. "
        "For imported broker data, Undo Import is usually safer because a trade "
        "can have a matching cash movement and dividend/tax records."
    )

    manage_tx_tab, manage_div_tab, manage_cash_tab, undo_import_tab = st.tabs(
        ["Transactions", "Dividends", "Cash Movements", "Undo Import"]
    )

    # --------------------------------------------------------
    # 23E-1. EDIT / DELETE TRANSACTION
    # --------------------------------------------------------
    with manage_tx_tab:
        managed_transactions = query_dataframe(
            """
            SELECT
                t.id,
                t.asset_id,
                t.account_id,
                t.transaction_type,
                t.quantity,
                t.price,
                t.fees,
                t.transaction_date,
                t.fx_rate_to_sek,
                t.source,
                t.import_batch_id,
                a.name,
                a.ticker,
                a.currency,
                COALESCE(CONCAT(ac.broker, ' — ', ac.account_name), 'Unassigned') AS account
            FROM transactions t
            JOIN assets a ON a.id = t.asset_id
            LEFT JOIN accounts ac ON ac.id = t.account_id
            ORDER BY t.transaction_date DESC, t.id DESC;
            """
        )

        if managed_transactions.empty:
            st.info("No transactions to manage.")
        else:
            tx_labels = {}
            for _, tx_row in managed_transactions.iterrows():
                label = (
                    f"#{int(tx_row['id'])} | {tx_row['transaction_date']} | "
                    f"{tx_row['account']} | {tx_row['ticker']} | "
                    f"{tx_row['transaction_type']} {float(tx_row['quantity']):g}"
                )
                tx_labels[label] = int(tx_row["id"])

            selected_tx_label = st.selectbox(
                "Transaction",
                list(tx_labels.keys()),
                key="manage_transaction_select",
            )
            selected_tx_id = tx_labels[selected_tx_label]
            tx_row = managed_transactions[
                managed_transactions["id"] == selected_tx_id
            ].iloc[0]

            if str(tx_row["source"]).upper() != "MANUAL":
                st.warning(
                    f"This transaction came from {tx_row['source']}. Editing or deleting only "
                    "the security transaction does not automatically change its matching cash "
                    "movement. Prefer Undo Import if the whole broker import is wrong."
                )

            manage_asset_options = {
                f"{row['name']} ({row['ticker']})": int(row["id"])
                for _, row in assets.iterrows()
            }
            manage_asset_labels = list(manage_asset_options.keys())
            current_asset_label = next(
                (
                    label
                    for label, asset_id in manage_asset_options.items()
                    if asset_id == int(tx_row["asset_id"])
                ),
                manage_asset_labels[0],
            )

            manage_account_options = {
                f"{row['broker']} — {row['account_name']} ({row['account_type']})": int(row["id"])
                for _, row in accounts.iterrows()
            }
            manage_account_labels = list(manage_account_options.keys())
            current_account_label = next(
                (
                    label
                    for label, account_id in manage_account_options.items()
                    if pd.notna(tx_row["account_id"])
                    and account_id == int(tx_row["account_id"])
                ),
                manage_account_labels[0] if manage_account_labels else None,
            )

            if not manage_account_labels:
                st.error("Create an account before editing transactions.")
            else:
                with st.form("edit_transaction_form"):
                    edit_asset_label = st.selectbox(
                        "Investment",
                        manage_asset_labels,
                        index=manage_asset_labels.index(current_asset_label),
                    )
                    edit_account_label = st.selectbox(
                        "Account",
                        manage_account_labels,
                        index=manage_account_labels.index(current_account_label),
                    )
                    edit_type = st.selectbox(
                        "Type",
                        ["BUY", "SELL"],
                        index=0 if str(tx_row["transaction_type"]).upper() == "BUY" else 1,
                    )
                    edit_quantity = st.number_input(
                        "Quantity",
                        min_value=0.0,
                        value=float(tx_row["quantity"]),
                        step=1.0,
                        format="%.6f",
                    )
                    edit_price = st.number_input(
                        "Price per share",
                        min_value=0.0,
                        value=float(tx_row["price"]),
                        step=1.0,
                        format="%.4f",
                    )
                    edit_fees = st.number_input(
                        "Fees",
                        min_value=0.0,
                        value=float(tx_row["fees"] or 0),
                        step=1.0,
                        format="%.2f",
                    )
                    edit_date = st.date_input(
                        "Transaction date",
                        value=as_date(tx_row["transaction_date"]),
                        max_value=date.today(),
                    )
                    save_tx_edit = st.form_submit_button(
                        "💾 Save Transaction Changes",
                        type="primary",
                        use_container_width=True,
                    )

                if save_tx_edit:
                    try:
                        if edit_quantity <= 0:
                            raise ValueError("Quantity must be greater than zero.")
                        if edit_price <= 0:
                            raise ValueError("Price must be greater than zero.")

                        old_asset_id = int(tx_row["asset_id"])
                        old_account_id = (
                            None if pd.isna(tx_row["account_id"]) else int(tx_row["account_id"])
                        )
                        new_asset_id = manage_asset_options[edit_asset_label]
                        new_account_id = manage_account_options[edit_account_label]

                        selected_asset_row = assets[assets["id"] == new_asset_id].iloc[0]
                        new_currency = selected_asset_row["currency"]
                        new_fx = get_fx_rate_to_sek(new_currency, edit_date)

                        cursor.execute("START TRANSACTION;")
                        cursor.execute(
                            """
                            UPDATE transactions
                            SET asset_id = %s,
                                account_id = %s,
                                transaction_type = %s,
                                quantity = %s,
                                price = %s,
                                fees = %s,
                                transaction_date = %s,
                                fx_rate_to_sek = %s
                            WHERE id = %s;
                            """,
                            (
                                new_asset_id,
                                new_account_id,
                                edit_type,
                                edit_quantity,
                                edit_price,
                                edit_fees,
                                edit_date,
                                new_fx,
                                selected_tx_id,
                            ),
                        )

                        validate_position_history(old_asset_id, old_account_id)
                        if (new_asset_id, new_account_id) != (old_asset_id, old_account_id):
                            validate_position_history(new_asset_id, new_account_id)

                        connection.commit()
                        st.session_state["manage_data_message"] = (
                            f"✅ Transaction #{selected_tx_id} updated."
                        )
                        st.rerun()

                    except Exception as error:
                        connection.rollback()
                        st.error(f"Could not update transaction: {error}")

                st.divider()
                confirm_tx_delete = st.checkbox(
                    "I understand this permanently deletes this transaction.",
                    key=f"confirm_delete_tx_{selected_tx_id}",
                )
                if st.button(
                    "🗑 Delete Transaction",
                    disabled=not confirm_tx_delete,
                    key=f"delete_tx_{selected_tx_id}",
                ):
                    try:
                        old_asset_id = int(tx_row["asset_id"])
                        old_account_id = (
                            None if pd.isna(tx_row["account_id"]) else int(tx_row["account_id"])
                        )
                        batch_id = (
                            None if pd.isna(tx_row["import_batch_id"]) else int(tx_row["import_batch_id"])
                        )

                        cursor.execute("START TRANSACTION;")
                        cursor.execute(
                            "DELETE FROM transactions WHERE id = %s;",
                            (selected_tx_id,),
                        )
                        validate_position_history(old_asset_id, old_account_id)
                        recalculate_import_batch_count(batch_id)
                        connection.commit()

                        st.session_state["manage_data_message"] = (
                            f"✅ Transaction #{selected_tx_id} deleted."
                        )
                        st.rerun()

                    except Exception as error:
                        connection.rollback()
                        st.error(f"Could not delete transaction: {error}")

    # --------------------------------------------------------
    # 23E-2. DELETE DIVIDEND
    # --------------------------------------------------------
    with manage_div_tab:
        managed_dividends = query_dataframe(
            """
            SELECT
                d.id,
                d.asset_id,
                d.account_id,
                d.payment_date,
                d.dividend_per_share,
                d.shares_held,
                d.currency,
                d.fx_rate_to_sek,
                d.source,
                d.import_batch_id,
                a.name,
                a.ticker,
                CONCAT(ac.broker, ' — ', ac.account_name) AS account
            FROM dividends d
            JOIN assets a ON a.id = d.asset_id
            LEFT JOIN accounts ac ON ac.id = d.account_id
            ORDER BY d.payment_date DESC, d.id DESC;
            """
        )

        if managed_dividends.empty:
            st.info("No dividends to manage.")
        else:
            dividend_labels = {}
            for _, div_row in managed_dividends.iterrows():
                div_label = (
                    f"#{int(div_row['id'])} | {div_row['payment_date']} | "
                    f"{div_row['ticker']} | {float(div_row['dividend_per_share']):g} "
                    f"{div_row['currency']} / share"
                )
                dividend_labels[div_label] = int(div_row["id"])

            selected_div_label = st.selectbox(
                "Dividend",
                list(dividend_labels.keys()),
                key="manage_dividend_select",
            )
            selected_div_id = dividend_labels[selected_div_label]
            div_row = managed_dividends[
                managed_dividends["id"] == selected_div_id
            ].iloc[0]

            st.write(
                f"**{div_row['name']}** · {div_row['account'] or 'Unassigned'} · "
                f"{float(div_row['shares_held']):g} shares · source: {div_row['source']}"
            )

            confirm_div_delete = st.checkbox(
                "I understand this permanently deletes this dividend record.",
                key=f"confirm_delete_div_{selected_div_id}",
            )
            if st.button(
                "🗑 Delete Dividend",
                disabled=not confirm_div_delete,
                key=f"delete_div_{selected_div_id}",
            ):
                try:
                    batch_id = (
                        None if pd.isna(div_row["import_batch_id"]) else int(div_row["import_batch_id"])
                    )
                    cursor.execute("START TRANSACTION;")
                    cursor.execute(
                        "DELETE FROM dividends WHERE id = %s;",
                        (selected_div_id,),
                    )
                    recalculate_import_batch_count(batch_id)
                    connection.commit()
                    st.session_state["manage_data_message"] = (
                        f"✅ Dividend #{selected_div_id} deleted."
                    )
                    st.rerun()
                except Exception as error:
                    connection.rollback()
                    st.error(f"Could not delete dividend: {error}")

    # --------------------------------------------------------
    # 23E-3. DELETE CASH MOVEMENT
    # --------------------------------------------------------
    with manage_cash_tab:
        managed_cash = query_dataframe(
            """
            SELECT
                cm.id,
                cm.account_id,
                cm.movement_date,
                cm.movement_type,
                cm.description,
                cm.amount,
                cm.currency,
                cm.source,
                cm.import_batch_id,
                CONCAT(ac.broker, ' — ', ac.account_name) AS account
            FROM cash_movements cm
            LEFT JOIN accounts ac ON ac.id = cm.account_id
            ORDER BY cm.movement_date DESC, cm.id DESC;
            """
        )

        if managed_cash.empty:
            st.info("No cash movements to manage.")
        else:
            cash_labels = {}
            for _, cash_row in managed_cash.iterrows():
                cash_label = (
                    f"#{int(cash_row['id'])} | {cash_row['movement_date']} | "
                    f"{cash_row['account'] or 'Unassigned'} | {cash_row['movement_type']} | "
                    f"{float(cash_row['amount']):+,.2f} {cash_row['currency']}"
                )
                cash_labels[cash_label] = int(cash_row["id"])

            selected_cash_label = st.selectbox(
                "Cash movement",
                list(cash_labels.keys()),
                key="manage_cash_select",
            )
            selected_cash_id = cash_labels[selected_cash_label]
            cash_row = managed_cash[managed_cash["id"] == selected_cash_id].iloc[0]

            if cash_row["description"]:
                st.caption(str(cash_row["description"]))

            confirm_cash_delete = st.checkbox(
                "I understand this permanently deletes this cash movement.",
                key=f"confirm_delete_cash_{selected_cash_id}",
            )
            if st.button(
                "🗑 Delete Cash Movement",
                disabled=not confirm_cash_delete,
                key=f"delete_cash_{selected_cash_id}",
            ):
                try:
                    batch_id = (
                        None if pd.isna(cash_row["import_batch_id"]) else int(cash_row["import_batch_id"])
                    )
                    cursor.execute("START TRANSACTION;")
                    cursor.execute(
                        "DELETE FROM cash_movements WHERE id = %s;",
                        (selected_cash_id,),
                    )
                    recalculate_import_batch_count(batch_id)
                    connection.commit()
                    st.session_state["manage_data_message"] = (
                        f"✅ Cash movement #{selected_cash_id} deleted."
                    )
                    st.rerun()
                except Exception as error:
                    connection.rollback()
                    st.error(f"Could not delete cash movement: {error}")

    # --------------------------------------------------------
    # 23E-4. UNDO ENTIRE IMPORT BATCH
    # --------------------------------------------------------
    with undo_import_tab:
        import_history = query_dataframe(
            """
            SELECT
                ib.id,
                ib.file_name,
                ib.file_hash,
                ib.imported_at,
                ib.row_count,
                CONCAT(ac.broker, ' — ', ac.account_name) AS account,
                (SELECT COUNT(*) FROM transactions t WHERE t.import_batch_id = ib.id) AS transactions_count,
                (SELECT COUNT(*) FROM dividends d WHERE d.import_batch_id = ib.id) AS dividends_count,
                (SELECT COUNT(*) FROM cash_movements cm WHERE cm.import_batch_id = ib.id) AS cash_count,
                (SELECT COUNT(*) FROM corporate_actions ca WHERE ca.import_batch_id = ib.id) AS actions_count
            FROM import_batches ib
            LEFT JOIN accounts ac ON ac.id = ib.account_id
            ORDER BY ib.imported_at DESC, ib.id DESC;
            """
        )

        if import_history.empty:
            st.info("No import batches exist yet.")
        else:
            batch_labels = {}
            for _, batch_row in import_history.iterrows():
                batch_label = (
                    f"Batch #{int(batch_row['id'])} | {batch_row['account'] or 'Unassigned'} | "
                    f"{batch_row['file_name']} | {batch_row['imported_at']}"
                )
                batch_labels[batch_label] = int(batch_row["id"])

            selected_batch_label = st.selectbox(
                "Import batch",
                list(batch_labels.keys()),
                key="manage_import_batch_select",
            )
            selected_batch_id = batch_labels[selected_batch_label]
            batch_row = import_history[import_history["id"] == selected_batch_id].iloc[0]

            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Trades", int(batch_row["transactions_count"] or 0))
            b2.metric("Dividends", int(batch_row["dividends_count"] or 0))
            b3.metric("Cash rows", int(batch_row["cash_count"] or 0))
            b4.metric("Corporate actions", int(batch_row["actions_count"] or 0))

            st.warning(
                "Undo Import permanently removes every transaction, dividend, cash movement "
                "and tracked corporate action linked to this batch. Investment records in the "
                "assets table are intentionally kept, because the same security may also be "
                "used by another account or import. After undoing, the same CSV can be imported again."
            )

            undo_text = st.text_input(
                "Type UNDO to confirm",
                key=f"undo_text_{selected_batch_id}",
            )

            if st.button(
                "↩️ Undo Entire Import",
                type="primary",
                disabled=undo_text.strip().upper() != "UNDO",
                key=f"undo_import_{selected_batch_id}",
            ):
                try:
                    cursor.execute("START TRANSACTION;")

                    cursor.execute(
                        "DELETE FROM corporate_actions WHERE import_batch_id = %s;",
                        (selected_batch_id,),
                    )
                    removed_actions = cursor.rowcount

                    cursor.execute(
                        "DELETE FROM dividends WHERE import_batch_id = %s;",
                        (selected_batch_id,),
                    )
                    removed_dividends = cursor.rowcount

                    cursor.execute(
                        "DELETE FROM cash_movements WHERE import_batch_id = %s;",
                        (selected_batch_id,),
                    )
                    removed_cash = cursor.rowcount

                    cursor.execute(
                        "DELETE FROM transactions WHERE import_batch_id = %s;",
                        (selected_batch_id,),
                    )
                    removed_transactions = cursor.rowcount

                    cursor.execute(
                        "DELETE FROM import_batches WHERE id = %s;",
                        (selected_batch_id,),
                    )

                    connection.commit()
                    st.session_state["manage_data_message"] = (
                        "✅ Import undone: "
                        f"{removed_transactions} transaction(s), "
                        f"{removed_dividends} dividend(s), "
                        f"{removed_cash} cash movement(s), "
                        f"{removed_actions} corporate action(s) removed."
                    )
                    st.rerun()

                except Exception as error:
                    connection.rollback()
                    st.error(f"Could not undo import: {error}")


if "manage_data_message" in st.session_state:
    st.success(st.session_state.pop("manage_data_message"))


# ============================================================
# 24. CLOSE DATABASE CONNECTION
# ============================================================

cursor.close()
connection.close()
