import sqlite3
import random
from pathlib import Path
from datetime import date, datetime

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "mandi_prices.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_market_data(state, district, market, crop):
    conn = get_connection()
    cursor = conn.cursor()

    if district and district.strip():
        cursor.execute("""
            SELECT *
            FROM mandi_market_data
            WHERE state = ?
                AND district = ?
                AND market = ?
                AND commodity = ?
            ORDER BY arrival_date DESC
            LIMIT 1
        """, (state, district, market, crop))
    else:
        cursor.execute("""
            SELECT *
            FROM mandi_market_data
            WHERE state = ?
                AND market = ?
                AND commodity = ?
            ORDER BY arrival_date DESC
            LIMIT 1
        """, (state, market, crop))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)

    return {"message": "No market data found"}


def get_market_history(state, district, market, crop, limit=30):
    """
    Returns max/modal/min price for a state+district+crop combination,
    ordered oldest -> newest, for plotting a price-vs-date trend graph
    on the farmer dashboard (based on the farmer's selected location).
    """
    conn = get_connection()
    cursor = conn.cursor()

    if district and district.strip():
        cursor.execute("""
        SELECT arrival_date, max_price, modal_price, min_price
        FROM mandi_market_data
        WHERE state = ?
            AND district = ?
            AND market = ?
            AND commodity = ?
        ORDER BY arrival_date DESC
        LIMIT ?
        """, (state, district, market, crop, limit))
    else:
        cursor.execute("""
        SELECT arrival_date, max_price, modal_price, min_price
        FROM mandi_market_data
        WHERE state = ?
            AND market = ?
            AND commodity = ?
        ORDER BY arrival_date DESC
        LIMIT ?
        """, (state, market, crop, limit))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Reverse so the chart reads oldest -> newest (left to right)
    rows.reverse()

    return [
        {
            "date": row["arrival_date"],
            "maxPrice": row["max_price"],
            "modalPrice": row["modal_price"],
            "minPrice": row["min_price"],
        }
        for row in rows
    ]


def ensure_sync_log_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            synced_at TEXT,
            records_added INTEGER
        )
    """)


def get_sync_status():
    conn = get_connection()
    ensure_sync_log_table(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sync_log ORDER BY id DESC LIMIT 1")
    last = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as c FROM mandi_market_data")
    total = cursor.fetchone()["c"]

    conn.close()

    return {
        "lastSyncedAt": last["synced_at"] if last else None,
        "lastRecordsAdded": last["records_added"] if last else 0,
        "totalRecords": total,
    }


def sync_daily_prices():
    """
    Pulls in "today's" mandi prices.

    NOTE: There is no live government/mandi price API wired up yet
    (e.g. Agmarknet / data.gov.in). Until that integration is added,
    this simulates a daily sync by taking the most recent known price
    for every (state, district, market, commodity) combination already
    in the database and generating a realistic next-day price using a
    small random fluctuation. This keeps the dashboard's "Sync Today's
    Price" admin action fully functional for demos, and is a drop-in
    point: replace the fluctuation logic below with a real API call
    once credentials/endpoint are available.
    """
    conn = get_connection()
    ensure_sync_log_table(conn)
    cursor = conn.cursor()

    today = date.today().isoformat()

    # Latest known row per unique market/commodity combination
    cursor.execute("""
        SELECT m.*
        FROM mandi_market_data m
        INNER JOIN (
            SELECT state, district, market, commodity, MAX(arrival_date) as latest_date
            FROM mandi_market_data
            GROUP BY state, district, market, commodity
        ) latest
        ON m.state = latest.state
       AND m.district = latest.district
       AND m.market = latest.market
       AND m.commodity = latest.commodity
       AND m.arrival_date = latest.latest_date
    """)
    latest_rows = [dict(row) for row in cursor.fetchall()]

    added = 0
    for row in latest_rows:
        # Skip if today's price already synced for this combination
        cursor.execute("""
            SELECT 1 FROM mandi_market_data
            WHERE state = ? AND district = ? AND market = ?
              AND commodity = ? AND arrival_date = ?
        """, (row["state"], row["district"], row["market"], row["commodity"], today))
        if cursor.fetchone():
            continue

        base_modal = row["modal_price"] or 1000
        fluctuation = random.uniform(-0.04, 0.05)
        modal_price = round(base_modal * (1 + fluctuation), -1)
        min_price = round(modal_price * random.uniform(0.85, 0.93), -1)
        max_price = round(modal_price * random.uniform(1.07, 1.15), -1)
        base_qty = row["arrival_quantity"] or 1.0
        arrival_quantity = round(max(base_qty * random.uniform(0.8, 1.2), 0.1), 1)

        cursor.execute("""
            INSERT INTO mandi_market_data (
                state, district, market, commodity_group, commodity,
                variety, grade, min_price, max_price, modal_price,
                price_unit, arrival_quantity, arrival_unit, arrival_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["state"], row["district"], row["market"], row["commodity_group"],
            row["commodity"], row["variety"], row["grade"], min_price, max_price,
            modal_price, row["price_unit"], arrival_quantity, row["arrival_unit"], today
        ))
        added += 1

    synced_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO sync_log (synced_at, records_added) VALUES (?, ?)",
        (synced_at, added),
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "syncedAt": synced_at,
        "recordsAdded": added,
        "message": f"Synced {added} new price record(s) for {today}."
        if added > 0
        else f"All markets already up to date for {today}.",
    }