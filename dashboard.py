import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wikipedia Clickstream",
    page_icon="📖",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Syne', sans-serif; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 100%; }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 0.75rem;
        text-align: center;
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        overflow: hidden;
    }
    .metric-value {
        font-family: 'Syne', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        color: #f97316;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    .metric-value-sm {
        font-family: 'Syne', sans-serif;
        font-size: 1.05rem;
        font-weight: 800;
        color: #f97316;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
        line-height: 1.3;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-top: 0.25rem;
    }
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: #f1f5f9;
        border-left: 3px solid #f97316;
        padding-left: 0.75rem;
        margin-bottom: 0.4rem;
        margin-top: 0.2rem;
    }
    .outlier-box {
        background: #1e1a0e;
        border: 1px solid #854d0e;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    .nav-link {
        display: block;
        color: #94a3b8;
        font-size: 0.82rem;
        padding: 0.3rem 0;
        text-decoration: none;
        border-bottom: 1px solid #1e293b;
    }
    .nav-link:hover { color: #f97316; }
</style>
""", unsafe_allow_html=True)

# ── Colour-blind safe palette (Wong 2011) ─────────────────────────────────────
CB_ORANGE  = "#E69F00"
CB_BLUE    = "#56B4E9"
CB_GREEN   = "#009E73"
CB_YELLOW  = "#F0E442"
CB_DBLUE   = "#0072B2"
CB_RED     = "#D55E00"
CB_PINK    = "#CC79A7"
CB_BLACK   = "#000000"

CHART_COLORS = [CB_ORANGE, CB_BLUE, CB_GREEN, CB_YELLOW, CB_DBLUE, CB_RED, CB_PINK]

PLOT_BG  = "#0f172a"
PAPER_BG = "#0f172a"
GRID     = "#1e293b"
TEXT     = "#f1f5f9"

MONTH_LABELS = {
    "2025-09": "Sep 2025",
    "2025-10": "Oct 2025",
    "2025-11": "Nov 2025",
    "2025-12": "Dec 2025",
    "2026-01": "Jan 2026",
    "2026-02": "Feb 2026",
}

def fmt_m(n):
    """Format a number as XM or X.XM."""
    return f"{n/1e6:.1f}M"

def base_layout(height=380):
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(family="IBM Plex Sans", color=TEXT, size=11),
        xaxis=dict(gridcolor=GRID, showline=False, tickfont=dict(size=10), automargin=True),
        yaxis=dict(gridcolor=GRID, showline=False, tickfont=dict(size=10), automargin=True),
        height=height,
    )

# ── Load CSVs ─────────────────────────────────────────────────────────────────
REQUIRED = ["top_articles.csv", "traffic_sources.csv",
            "top_searched.csv", "top_pairs.csv",
            "monthly_totals.csv", "hyphen_minus.csv"]
missing = [f for f in REQUIRED if not os.path.exists(f)]

if missing:
    st.error(f"Missing CSV files: {', '.join(missing)}")
    st.info("Run `python prepare_data.py` first to generate them.")
    st.stop()

all_articles   = pd.read_csv("top_articles.csv")
all_traffic    = pd.read_csv("traffic_sources.csv")
all_searched   = pd.read_csv("top_searched.csv")
all_pairs      = pd.read_csv("top_pairs.csv")
monthly_totals = pd.read_csv("monthly_totals.csv")
hyphen_minus   = pd.read_csv("hyphen_minus.csv")

monthly_totals["month_label"] = monthly_totals["month"].map(MONTH_LABELS)
hyphen_minus["month_label"]   = hyphen_minus["month"].map(MONTH_LABELS)

# All articles that ever appeared in the top 50 across any month
all_article_options = sorted(all_articles["curr"].unique().tolist())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-family:Syne; font-size:1.15rem; font-weight:800;
                color:#f97316; margin-bottom:0.25rem;'>
        📖 Wikipedia Clickstream
    </div>
    <div style='color:#64748b; font-size:0.78rem; margin-bottom:1rem;'>
        English Wikipedia · Sep 2025 – Feb 2026
    </div>
    """, unsafe_allow_html=True)

    # ── Navigation index ──────────────────────────────────────────────────────
    with st.expander("📑 Jump to section", expanded=False):
        st.markdown("""
        - [Overview KPIs](#overview)
        - [Monthly Trend](#monthly-trend)
        - [Top Articles](#top-articles-by-clicks)
        - [Traffic Sources](#traffic-source-breakdown)
        - [Search-Driven Articles](#top-search-driven-articles)
        - [Internal Link Sources](#top-internal-link-sources)
        - [Article Trends](#article-trends-month-over-month)
        - [Outlier: Hyphen-Minus](#outlier-hyphen-minus)
        """)

    st.markdown("---")

    # ── Month selector ────────────────────────────────────────────────────────
    st.markdown("**🗓 Time period**")
    month_options = ["All months"] + list(MONTH_LABELS.keys())
    month_display = ["All months combined"] + list(MONTH_LABELS.values())
    selected_idx = st.selectbox(
        "Select month",
        options=range(len(month_options)),
        format_func=lambda i: month_display[i],
        label_visibility="collapsed",
    )
    selected_month = month_options[selected_idx]
    is_all = selected_month == "All months"

    st.markdown("---")

    # ── Chart controls ────────────────────────────────────────────────────────
    st.markdown("**📊 Chart controls**")
    top_n = st.slider("Articles to show", min_value=5, max_value=50, value=20, step=5)

    st.markdown("---")

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown("**🔍 Filters**")

    traffic_type_options = ["All", "Internal links only", "Search traffic only", "External only"]
    traffic_filter = st.selectbox("Traffic type", traffic_type_options)

    min_clicks_m = st.slider(
        "Min. clicks (M) for article charts",
        min_value=0.0, max_value=50.0, value=0.0, step=0.5,
        help="Hide articles below this monthly click threshold"
    )
    min_clicks = min_clicks_m * 1_000_000

    st.markdown("---")

    # ── Article search ────────────────────────────────────────────────────────
    st.markdown("**🔎 Article search**")
    article_search = st.text_input(
        "Filter articles by name",
        placeholder="e.g. United States",
        label_visibility="collapsed",
    )

# ── Filter logic ──────────────────────────────────────────────────────────────
def apply_traffic_filter(df, col="type"):
    if traffic_filter == "Internal links only":
        return df[df[col] == "link"]
    elif traffic_filter == "Search traffic only":
        return df[df["prev"] == "other-search"] if "prev" in df.columns else df
    elif traffic_filter == "External only":
        return df[df[col] == "external"]
    return df

if is_all:
    articles = (
        all_articles.groupby("curr")["total_clicks"]
        .sum().reset_index()
        .sort_values("total_clicks", ascending=False)
    )
    traffic = (
        all_traffic.groupby("type")["total_clicks"]
        .sum().reset_index()
    )
    searched = (
        all_searched.groupby("curr")["total_clicks"]
        .sum().reset_index()
        .sort_values("total_clicks", ascending=False)
    )
    # Fix: ensure pairs are fully aggregated — sum across months
    pairs = (
        all_pairs.groupby(["prev", "curr"])["total_clicks"]
        .sum().reset_index()
        .sort_values("total_clicks", ascending=False)
    )
else:
    articles = all_articles[all_articles["month"] == selected_month].sort_values("total_clicks", ascending=False)
    traffic  = all_traffic[all_traffic["month"] == selected_month]
    searched = all_searched[all_searched["month"] == selected_month].sort_values("total_clicks", ascending=False)
    # Fix: sum within month to collapse any residual duplicates
    pairs = (
        all_pairs[all_pairs["month"] == selected_month]
        .groupby(["prev", "curr"])["total_clicks"]
        .sum().reset_index()
        .sort_values("total_clicks", ascending=False)
    )

# Apply min clicks filter
articles = articles[articles["total_clicks"] >= min_clicks]
searched = searched[searched["total_clicks"] >= min_clicks]

# Apply article name search
if article_search.strip():
    q = article_search.strip().lower().replace(" ", "_")
    articles = articles[articles["curr"].str.lower().str.contains(q, na=False)]
    searched = searched[searched["curr"].str.lower().str.contains(q, na=False)]

# ── Header ────────────────────────────────────────────────────────────────────
period_label = "Sep 2025 – Feb 2026" if is_all else MONTH_LABELS[selected_month]
st.markdown(f"""
<h1 id="overview" style='font-family:Syne; font-size:1.9rem; margin-bottom:0; color:#f1f5f9;'>
    Wikipedia Clickstream &nbsp;
    <span style='color:#f97316;'>{period_label}</span>
</h1>
<p style='color:#64748b; margin-top:0.2rem; font-size:0.82rem;'>
    English Wikipedia reader navigation · Main_Page and Hyphen-Minus excluded from main analysis
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── KPI cards ─────────────────────────────────────────────────────────────────
total_clicks    = articles["total_clicks"].sum()
top_page        = articles.iloc[0]["curr"] if len(articles) > 0 else "N/A"
top_page_clicks = articles.iloc[0]["total_clicks"] if len(articles) > 0 else 0
top_page_label  = top_page.replace("_", " ")

# Shorten for display — if over 18 chars use abbreviation
if len(top_page_label) > 18:
    display_name = top_page_label[:16] + "…"
    name_class   = "metric-value-sm"
else:
    display_name = top_page_label
    name_class   = "metric-value"

try:
    link_pct = traffic[traffic["type"] == "link"]["total_clicks"].values[0]
    link_pct = link_pct / traffic["total_clicks"].sum() * 100
except:
    link_pct = 0.0

c1, c2, c3, c4 = st.columns(4)
cards = [
    ("metric-value", f"{total_clicks/1e6:.1f}M", "Total clicks (excl. outliers)"),
    (name_class,     display_name,                "Most visited article"),
    ("metric-value", fmt_m(top_page_clicks),      "Clicks on top article"),
    ("metric-value", f"{link_pct:.1f}%",          "Traffic via internal links"),
]
for col, (cls, val, label) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="{cls}" title="{val}">{val}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Trend chart (all months only) ─────────────────────────────────────────────
if is_all:
    st.markdown('<div class="section-title" id="monthly-trend">Total Clicks by Month</div>', unsafe_allow_html=True)
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly_totals["month_label"],
        y=monthly_totals["total_clicks"],
        mode="lines+markers",
        line=dict(color=CB_ORANGE, width=3),
        marker=dict(size=8, color=CB_ORANGE),
        fill="tozeroy",
        fillcolor="rgba(230,159,0,0.12)",
        hovertemplate="<b>%{x}</b><br>%{y:,} clicks<extra></extra>",
    ))
    fig_trend.update_layout(**base_layout(height=240), margin=dict(t=10, b=40, l=10, r=10))
    st.plotly_chart(fig_trend, use_container_width=True)

# ── Row 1: Top articles + Traffic donut ───────────────────────────────────────
col_a, col_b = st.columns([3, 2], gap="medium")

with col_a:
    st.markdown('<div class="section-title" id="top-articles-by-clicks">Top Articles by Clicks</div>', unsafe_allow_html=True)
    df_art = articles.head(top_n).copy()
    df_art["label"] = df_art["curr"].str.replace("_", " ")
    fig1 = go.Figure(go.Bar(
        x=df_art["label"],
        y=df_art["total_clicks"],
        marker=dict(
            color=df_art["total_clicks"],
            colorscale=[[0, "#1a3a5c"], [1, CB_ORANGE]],
            showscale=False,
        ),
        hovertemplate="<b>%{x}</b><br>%{y:,} clicks<extra></extra>",
    ))
    layout1 = base_layout(380)
    layout1["xaxis"]["tickangle"] = -40
    fig1.update_layout(**layout1, margin=dict(t=20, b=60, l=10, r=10))
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.markdown('<div class="section-title" id="traffic-source-breakdown">Traffic Source Breakdown</div>', unsafe_allow_html=True)
    traffic_display = traffic.copy()
    traffic_display["type_label"] = traffic_display["type"].map({
        "link":     "Internal link",
        "external": "External / direct",
        "other":    "Other",
    }).fillna(traffic_display["type"])
    fig2 = go.Figure(go.Pie(
        labels=traffic_display["type_label"],
        values=traffic_display["total_clicks"],
        hole=0.5,
        marker=dict(colors=CHART_COLORS),
        textinfo="percent+label",
        textfont=dict(size=11, family="IBM Plex Sans"),
        hovertemplate="<b>%{label}</b><br>%{value:,} clicks · %{percent}<extra></extra>",
    ))
    fig2.update_layout(
        plot_bgcolor=PLOT_BG, paper_bgcolor=PAPER_BG,
        font=dict(color=TEXT),
        margin=dict(t=20, b=20, l=10, r=10),
        height=380,
        showlegend=True,
        legend=dict(font=dict(color=TEXT, size=11), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Search-driven + Internal link pairs ────────────────────────────────
col_c, col_d = st.columns(2, gap="medium")

with col_c:
    st.markdown('<div class="section-title" id="top-search-driven-articles">Top Search-Driven Articles</div>', unsafe_allow_html=True)
    df_s = searched.head(top_n).copy()
    df_s["label"] = df_s["curr"].str.replace("_", " ")
    fig3 = go.Figure(go.Bar(
        x=df_s["label"],
        y=df_s["total_clicks"],
        marker_color=CB_BLUE,
        hovertemplate="<b>%{x}</b><br>%{y:,} clicks<extra></extra>",
    ))
    layout3 = base_layout(380)
    layout3["xaxis"]["tickangle"] = -40
    fig3.update_layout(**layout3, margin=dict(t=20, b=60, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.markdown('<div class="section-title" id="top-internal-link-sources">Top Internal Link Sources</div>', unsafe_allow_html=True)
    df_p = pairs.head(top_n).copy()
    df_p["prev_label"] = df_p["prev"].str.replace("_", " ")
    df_p["curr_label"] = df_p["curr"].str.replace("_", " ")

    fig4 = go.Figure(go.Bar(
        y=df_p["prev_label"],
        x=df_p["total_clicks"],
        orientation="h",
        marker_color=CB_GREEN,
        customdata=df_p[["curr_label", "total_clicks"]],
        hovertemplate=(
            "<b>From:</b> %{y}<br>"
            "<b>To:</b> %{customdata[0]}<br>"
            "<b>Clicks:</b> %{x:,}<extra></extra>"
        ),
    ))
    layout4 = base_layout(380)
    layout4["yaxis"]["autorange"] = "reversed"
    layout4["margin"] = dict(t=20, b=20, l=10, r=10)
    fig4.update_layout(**layout4)
    st.plotly_chart(fig4, use_container_width=True)
    st.caption("Each bar = total clicks from one article (prev) to its most-linked destination (curr). Hover to see the destination.")

# ── Article trends (all months only) ─────────────────────────────────────────
if is_all:
    st.markdown("---")
    st.markdown('<div class="section-title" id="article-trends-month-over-month">Article Trends — Month over Month</div>', unsafe_allow_html=True)

    selected_articles = st.multiselect(
        "Pick articles to compare (any article that appeared in top 50 in any month)",
        options=all_article_options,
        default=all_article_options[:3],
        format_func=lambda x: x.replace("_", " "),
    )

    if selected_articles:
        trend_df = all_articles[all_articles["curr"].isin(selected_articles)].copy()
        trend_df["month_label"] = trend_df["month"].map(MONTH_LABELS)
        trend_df["label"] = trend_df["curr"].str.replace("_", " ")

        fig5 = px.line(
            trend_df,
            x="month_label", y="total_clicks",
            color="label",
            markers=True,
            color_discrete_sequence=CHART_COLORS,
        )
        fig5.update_traces(line=dict(width=2.5), marker=dict(size=7))
        fig5.update_layout(
            **base_layout(height=360),
            legend=dict(font=dict(color=TEXT, size=11), bgcolor="rgba(0,0,0,0)"),
            xaxis_title="", yaxis_title="Clicks",
            margin=dict(t=20, b=40, l=10, r=10),
        )
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("Select at least one article above to see its trend.")

# ── Outlier: Hyphen-Minus ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title" id="outlier-hyphen-minus">⚠️ Outlier: Hyphen-Minus</div>', unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div class="outlier-box">
        <b style="color:#fbbf24;">Why is this excluded from the main charts?</b><br>
        <span style="color:#cbd5e1; font-size:0.87rem;">
        The article <i>Hyphen-Minus</i> received an anomalously high number of clicks across all months,
        widely attributed to a Wikipedia internal linking error that caused unintended redirects to this page.
        Including it would compress all other articles into insignificance on every chart.
        It is tracked here separately for transparency.
        </span>
    </div>
    """, unsafe_allow_html=True)

    hm_display = hyphen_minus.copy()
    if not is_all:
        hm_display = hm_display[hm_display["month"] == selected_month]

    col_hm1, col_hm2 = st.columns([1, 2], gap="medium")

    with col_hm1:
        total_hm = hm_display["total_clicks"].sum()
        st.markdown(f"""
        <div class="metric-card" style="height:auto; padding:1.25rem;">
            <div class="metric-value">{fmt_m(total_hm)}</div>
            <div class="metric-label">{"Total clicks (all months)" if is_all else "Clicks this month"}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_hm2:
        fig_hm = go.Figure(go.Bar(
            x=hm_display["month_label"] if is_all else [MONTH_LABELS.get(selected_month, selected_month)],
            y=hm_display["total_clicks"],
            marker_color=CB_RED,
            hovertemplate="<b>%{x}</b><br>%{y:,} clicks<extra></extra>",
        ))
        fig_hm.update_layout(**base_layout(height=200), margin=dict(t=10, b=40, l=10, r=10))
        st.plotly_chart(fig_hm, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style='color:#475569; font-size:0.75rem; text-align:center;'>
    Data: Wikimedia Foundation · English Wikipedia Clickstream Sep 2025 – Feb 2026 &nbsp;|&nbsp;
    Processed with DuckDB &nbsp;|&nbsp; Visualised with Streamlit + Plotly
</p>
""", unsafe_allow_html=True)