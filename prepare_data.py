import duckdb
import os

DATA_DIR = "data"

MONTHS = [
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
]

EXCLUDE = ("'Main_Page'", "'Hyphen-minus'", "'Hyphen-Minus'")
EXCLUDE_CLAUSE = f"AND curr NOT IN ({', '.join(EXCLUDE)})"

# ── Verify all files exist ────────────────────────────────────────────────────
print("Checking files...")
missing = []
for month in MONTHS:
    path = os.path.join(DATA_DIR, f"clickstream-enwiki-{month}.tsv")
    if not os.path.exists(path):
        missing.append(path)

if missing:
    print("\nERROR: Could not find the following files:")
    for f in missing:
        print(f"  {f}")
    print("\nMake sure all 6 TSV files are in the 'data/' folder.")
    exit()

print("All 6 files found.\n")

con = duckdb.connect()

# ── Helper: UNION ALL across all 6 months ────────────────────────────────────
def union_all(select_sql, extra_where=""):
    parts = []
    for month in MONTHS:
        path = os.path.join(DATA_DIR, f"clickstream-enwiki-{month}.tsv").replace("\\", "/")
        parts.append(f"""
        SELECT '{month}' AS month, {select_sql}
        FROM read_csv('{path}',
                      sep='\t',
                      header=false,
                      columns={{
                          'prev': 'VARCHAR',
                          'curr': 'VARCHAR',
                          'type': 'VARCHAR',
                          'n':    'BIGINT'
                      }})
        WHERE curr != 'Main_Page'
        {EXCLUDE_CLAUSE}
        {extra_where}
        """)
    return " UNION ALL ".join(parts)


# ── 1. Top 50 articles per month ──────────────────────────────────────────────
print("Building top_articles.csv...")
con.execute(f"""
    COPY (
        SELECT month, curr, SUM(n) AS total_clicks
        FROM ({union_all('curr, n')})
        GROUP BY month, curr
        QUALIFY ROW_NUMBER() OVER (PARTITION BY month ORDER BY SUM(n) DESC) <= 50
        ORDER BY month, total_clicks DESC
    ) TO 'top_articles.csv' (HEADER, DELIMITER ',')
""")

# ── 2. Traffic source breakdown per month ─────────────────────────────────────
print("Building traffic_sources.csv...")
con.execute(f"""
    COPY (
        SELECT month, type, SUM(n) AS total_clicks
        FROM ({union_all('type, n')})
        GROUP BY month, type
        ORDER BY month, total_clicks DESC
    ) TO 'traffic_sources.csv' (HEADER, DELIMITER ',')
""")

# ── 3. Top 30 search-driven articles per month ────────────────────────────────
print("Building top_searched.csv...")
con.execute(f"""
    COPY (
        SELECT month, curr, SUM(n) AS total_clicks
        FROM ({union_all('curr, n', "AND prev = 'other-search'")})
        GROUP BY month, curr
        QUALIFY ROW_NUMBER() OVER (PARTITION BY month ORDER BY SUM(n) DESC) <= 30
        ORDER BY month, total_clicks DESC
    ) TO 'top_searched.csv' (HEADER, DELIMITER ',')
""")

# ── 4. Top 50 internal link pairs per month — fixed aggregation ───────────────
# Previous bug: QUALIFY was applied before GROUP BY fully collapsed duplicates.
# Fix: aggregate fully first in a subquery, then rank in an outer query.
print("Building top_pairs.csv...")
con.execute(f"""
    COPY (
        SELECT month, prev, curr, total_clicks
        FROM (
            SELECT month, prev, curr, SUM(n) AS total_clicks,
                   ROW_NUMBER() OVER (PARTITION BY month ORDER BY SUM(n) DESC) AS rn
            FROM ({union_all('prev, curr, n', "AND type = 'link'")})
            GROUP BY month, prev, curr
        )
        WHERE rn <= 50
        ORDER BY month, total_clicks DESC
    ) TO 'top_pairs.csv' (HEADER, DELIMITER ',')
""")

# ── 5. Monthly totals trend ────────────────────────────────────────────────────
print("Building monthly_totals.csv...")
con.execute(f"""
    COPY (
        SELECT month, SUM(n) AS total_clicks
        FROM ({union_all('n')})
        GROUP BY month
        ORDER BY month
    ) TO 'monthly_totals.csv' (HEADER, DELIMITER ',')
""")

# ── 6. Hyphen-Minus stats (outlier — kept separate) ───────────────────────────
print("Building hyphen_minus.csv...")
parts = []
for month in MONTHS:
    path = os.path.join(DATA_DIR, f"clickstream-enwiki-{month}.tsv").replace("\\", "/")
    parts.append(f"""
    SELECT '{month}' AS month, SUM(n) AS total_clicks
    FROM read_csv('{path}',
                  sep='\t',
                  header=false,
                  columns={{
                      'prev': 'VARCHAR',
                      'curr': 'VARCHAR',
                      'type': 'VARCHAR',
                      'n':    'BIGINT'
                  }})
    WHERE curr IN ('Hyphen-minus', 'Hyphen-Minus')
    """)
hm_query = " UNION ALL ".join(parts)
con.execute(f"""
    COPY (
        SELECT month, SUM(total_clicks) AS total_clicks
        FROM ({hm_query})
        GROUP BY month
        ORDER BY month
    ) TO 'hyphen_minus.csv' (HEADER, DELIMITER ',')
""")

print("""
Done — 6 CSVs exported:
  top_articles.csv
  traffic_sources.csv
  top_searched.csv
  top_pairs.csv
  monthly_totals.csv
  hyphen_minus.csv

You can now run:  streamlit run dashboard.py
""")