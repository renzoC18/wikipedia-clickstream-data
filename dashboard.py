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
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 400; }
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 100%; }

    /* Force all Streamlit accent elements to blue */
    :root {
        --primary-color: #3b82f6 !important;
    }
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #3b82f6 !important;
        border-color: #3b82f6 !important;
    }
    .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {
        color: #3b82f6 !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background: #3b82f6 !important;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #1d4ed8 !important;
    }
    .stSelectbox [aria-selected="true"] {
        color: #3b82f6 !important;
    }
    a { color: #60a5fa !important; }

    /* KPI cards */
    .kpi-row {
        display: flex;
        gap: 1rem;
        align-items: stretch;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #1a2744;
        border: 1px solid #2a3f6f;
        border-radius: 12px;
        padding: 1rem 0.75rem;
        text-align: center;
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 80px;
    }
    .metric-value {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #60a5fa;
        word-break: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.25;
    }
    .metric-label {
        font-size: 0.72rem;
        font-weight: 500;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-top: 0.35rem;
    }
    .section-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: #f1f5f9;
        border-left: 3px solid #3b82f6;
        padding-left: 0.75rem;
        margin-bottom: 0.4rem;
        margin-top: 0.2rem;
    }
    .outlier-box {
        background: #1e1a0e;
        border: 1px solid #854d0e;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        color: #e2e8f0;
        font-size: 0.92rem;
        font-weight: 400;
        line-height: 1.65;
    }
    .outlier-box b {
        font-size: 1rem;
        font-weight: 600;
    }
    .info-box {
        background: #0f1e35;
        border: 1px solid #2a3f6f;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-top: 1rem;
        color: #e2e8f0;
        font-size: 0.92rem;
        font-weight: 400;
        line-height: 1.65;
    }
    .info-box b {
        font-size: 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Colour palette — Wikipedia blue, colour-blind safe (Wong 2011) ────────────
CB_BLUE   = "#3b82f6"
CB_LBLUE  = "#60a5fa"
CB_DBLUE  = "#0072B2"
CB_TEAL   = "#009E73"
CB_YELLOW = "#F0E442"
CB_RED    = "#D55E00"
CB_PINK   = "#CC79A7"
CB_ORANGE = "#E69F00"

CHART_COLORS = [CB_BLUE, CB_DBLUE, CB_TEAL, CB_YELLOW, CB_LBLUE, CB_RED, CB_PINK]

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
    return f"{n/1e6:.1f}M"

def base_layout(height=380):
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(family="Helvetica Neue, Helvetica, Arial, sans-serif", color=TEXT, size=11),
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

all_article_options = sorted(all_articles["curr"].unique().tolist())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-family:"Helvetica Neue", Helvetica, Arial, sans-serif; font-size:1.15rem; font-weight:700;
                color:#3b82f6; margin-bottom:0.25rem;'>
        📖 Wikipedia Clickstream
    </div>
    <div style='color:#64748b; font-size:0.78rem; margin-bottom:1rem;'>
        English Wikipedia · Sep 2025 – Feb 2026
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📑 Jump to section", expanded=False):
        st.markdown("""
        - [Overview KPIs](#kpi-overview)
        - [Monthly Trend](#monthly-trend)
        - [Top Articles](#top-articles-by-clicks)
        - [Traffic Sources](#traffic-source-breakdown)
        - [Search-Driven Articles](#top-search-driven-articles)
        - [Internal Link Sources](#top-internal-link-sources)
        - [Article Trends](#article-trends-month-over-month)
        - [Outlier: Hyphen-Minus](#outlier-hyphen-minus)
        """)

    st.markdown("---")

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

    st.markdown("**📊 Chart controls**")
    top_n = st.slider("Articles to show", min_value=5, max_value=50, value=20, step=5)

    st.markdown("---")

    st.markdown("**🔍 Filters**")
    traffic_type_options = ["All", "Internal links only", "Search traffic only"]
    traffic_filter = st.selectbox(
        "Traffic type",
        traffic_type_options,
        help=(
            "All: show everything.\n"
            "Internal links only: articles reached via Wikipedia internal links.\n"
            "Search traffic only: articles reached via search engines."
        ),
    )

    min_clicks_m = st.slider(
        "Min. clicks (M) for article charts",
        min_value=0.0, max_value=50.0, value=0.0, step=0.5,
        help="Hide articles below this click threshold",
    )
    min_clicks = min_clicks_m * 1_000_000

    st.markdown("---")

    st.markdown("**🔎 Article search**")
    article_search = st.text_input(
        "Filter articles by name",
        placeholder="e.g. United States",
        label_visibility="collapsed",
    )

# ── Base data selection (by month) ────────────────────────────────────────────
if is_all:
    articles_base = (
        all_articles.groupby("curr")["total_clicks"]
        .sum().reset_index()
        .sort_values("total_clicks", ascending=False)
    )
    traffic = (
        all_traffic.groupby("type")["total_clicks"]
        .sum().reset_index()
    )
    searched_base = (
        all_searched.groupby("curr")["total_clicks"]
        .sum().reset_index()
        .sort_values("total_clicks", ascending=False)
    )
    pairs_base = (
        all_pairs.groupby(["prev", "curr"])["total_clicks"]
        .sum().reset_index()
        .sort_values("total_clicks", ascending=False)
    )
else:
    articles_base = (
        all_articles[all_articles["month"] == selected_month]
        .sort_values("total_clicks", ascending=False)
        .reset_index(drop=True)
    )
    traffic = all_traffic[all_traffic["month"] == selected_month]
    searched_base = (
        all_searched[all_searched["month"] == selected_month]
        .sort_values("total_clicks", ascending=False)
        .reset_index(drop=True)
    )
    pairs_base = (
        all_pairs[all_pairs["month"] == selected_month]
        .groupby(["prev", "curr"])["total_clicks"]
        .sum().reset_index()
        .sort_values("total_clicks", ascending=False)
    )

# ── Apply traffic type filter ─────────────────────────────────────────────────
if traffic_filter == "Internal links only":
    valid_curr = pairs_base["curr"].unique()
    articles   = articles_base[articles_base["curr"].isin(valid_curr)].copy()
    searched   = pd.DataFrame(columns=searched_base.columns)
    pairs      = pairs_base.copy()
elif traffic_filter == "Search traffic only":
    valid_curr = searched_base["curr"].unique()
    articles   = articles_base[articles_base["curr"].isin(valid_curr)].copy()
    searched   = searched_base.copy()
    pairs      = pd.DataFrame(columns=pairs_base.columns)
else:
    articles = articles_base.copy()
    searched = searched_base.copy()
    pairs    = pairs_base.copy()

# ── Apply min clicks filter ───────────────────────────────────────────────────
articles = articles[articles["total_clicks"] >= min_clicks]
searched = searched[searched["total_clicks"] >= min_clicks] if not searched.empty else searched

# ── Apply article name search ─────────────────────────────────────────────────
if article_search.strip():
    q = article_search.strip().lower().replace(" ", "_")
    articles = articles[articles["curr"].str.lower().str.contains(q, na=False)]
    if not searched.empty:
        searched = searched[searched["curr"].str.lower().str.contains(q, na=False)]
    if not pairs.empty:
        pairs = pairs[
            pairs["prev"].str.lower().str.contains(q, na=False) |
            pairs["curr"].str.lower().str.contains(q, na=False)
        ]

# ── Header ────────────────────────────────────────────────────────────────────
period_label = "Sep 2025 – Feb 2026" if is_all else MONTH_LABELS[selected_month]
st.markdown(f"""
<h1 style='font-family:"Helvetica Neue", Helvetica, Arial, sans-serif; font-size:1.9rem; margin-bottom:0; color:#f1f5f9;'>
    Wikipedia Clickstream &nbsp;
    <span style='color:#3b82f6;'>{period_label}</span>
</h1>
<p style='color:#64748b; margin-top:0.2rem; font-size:0.82rem; font-weight:500;'>
    English Wikipedia reader navigation · Main_Page and Hyphen-Minus excluded from main analysis
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── KPI cards ─────────────────────────────────────────────────────────────────
st.markdown('<div id="kpi-overview"></div>', unsafe_allow_html=True)

total_clicks    = articles["total_clicks"].sum() if not articles.empty else 0
top_page        = articles.iloc[0]["curr"] if not articles.empty else "N/A"
top_page_clicks = articles.iloc[0]["total_clicks"] if not articles.empty else 0
top_page_label  = top_page.replace("_", " ")

try:
    link_pct = traffic[traffic["type"] == "link"]["total_clicks"].values[0]
    link_pct = link_pct / traffic["total_clicks"].sum() * 100
except Exception:
    link_pct = 0.0

st.markdown(f"""
<div class="kpi-row">
    <div class="metric-card">
        <div class="metric-value">{total_clicks/1e6:.1f}M</div>
        <div class="metric-label">Total clicks (excl. outliers)</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{top_page_label}</div>
        <div class="metric-label">Most visited article</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{fmt_m(top_page_clicks)}</div>
        <div class="metric-label">Clicks on top article</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{link_pct:.1f}%</div>
        <div class="metric-label">Traffic via internal links</div>
    </div>
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
        line=dict(color=CB_BLUE, width=3),
        marker=dict(size=8, color=CB_BLUE),
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.12)",
        hovertemplate="<b>%{x}</b><br>%{y:,} clicks<extra></extra>",
    ))
    fig_trend.update_layout(**base_layout(height=240), margin=dict(t=10, b=40, l=10, r=10))
    st.plotly_chart(fig_trend, use_container_width=True)

# ── Row 1: Top articles (HORIZONTAL) + Traffic donut ─────────────────────────
col_a, col_b = st.columns([3, 2], gap="medium")

with col_a:
    st.markdown('<div class="section-title" id="top-articles-by-clicks">Top Articles by Clicks</div>', unsafe_allow_html=True)
    if articles.empty:
        st.info("No articles match the current filter selection.")
    else:
        df_art = articles.head(top_n).copy()
        # Truncate label for display; full name available on hover
        df_art["label"] = df_art["curr"].str.replace("_", " ")
        df_art["label_short"] = df_art["label"].str.slice(0, 30) + df_art["label"].apply(
            lambda x: "…" if len(x) > 30 else ""
        )
        # Horizontal bar — sorted ascending so top article is at the top
        df_art_sorted = df_art.sort_values("total_clicks", ascending=True)
        fig1 = go.Figure(go.Bar(
            y=df_art_sorted["label_short"],
            x=df_art_sorted["total_clicks"],
            orientation="h",
            marker=dict(
                color=df_art_sorted["total_clicks"],
                colorscale=[[0, "#1a3a5c"], [1, CB_BLUE]],
                showscale=False,
            ),
            customdata=df_art_sorted[["label"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{x:,} clicks<extra></extra>",
        ))
        # Dynamic height: grow with number of bars, min 380
        bar_height = max(380, top_n * 22)
        layout1 = base_layout(bar_height)
        layout1["yaxis"]["tickfont"] = dict(size=11)
        layout1["xaxis"]["title"] = "Total clicks"
        layout1["margin"] = dict(t=20, b=40, l=10, r=20)
        fig1.update_layout(**layout1)
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
        textfont=dict(size=11, family="Helvetica Neue, Helvetica, Arial, sans-serif"),
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
    if searched.empty:
        st.info("Not applicable for 'Internal links only' filter.")
    else:
        df_s = searched.head(top_n).copy()
        df_s["label"] = df_s["curr"].str.replace("_", " ")
        df_s["label_short"] = df_s["label"].str.slice(0, 30) + df_s["label"].apply(
            lambda x: "…" if len(x) > 30 else ""
        )
        fig3 = go.Figure(go.Bar(
            x=df_s["label_short"],
            y=df_s["total_clicks"],
            marker=dict(
                color=df_s["total_clicks"],
                colorscale=[[0, "#1a3a5c"], [1, CB_DBLUE]],
                showscale=False,
            ),
            customdata=df_s[["label"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{y:,} clicks<extra></extra>",
        ))
        layout3 = base_layout(380)
        layout3["xaxis"]["tickangle"] = -35
        layout3["xaxis"]["tickfont"] = dict(size=10)
        fig3.update_layout(**layout3, margin=dict(t=20, b=100, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.markdown('<div class="section-title" id="top-internal-link-sources">Top Internal Link Sources</div>', unsafe_allow_html=True)
    if pairs.empty:
        st.info("Not applicable for 'Search traffic only' filter.")
    else:
        df_p = pairs.head(top_n).copy()
        df_p["prev_label"] = df_p["prev"].str.replace("_", " ")
        df_p["curr_label"] = df_p["curr"].str.replace("_", " ")
        df_p["prev_short"] = df_p["prev_label"].str.slice(0, 28) + df_p["prev_label"].apply(
            lambda x: "…" if len(x) > 28 else ""
        )
        fig4 = go.Figure(go.Bar(
            y=df_p["prev_short"],
            x=df_p["total_clicks"],
            orientation="h",
            marker=dict(
                color=df_p["total_clicks"],
                colorscale=[[0, "#0a2a4a"], [1, CB_TEAL]],
                showscale=False,
            ),
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
        st.caption("Each bar = clicks from one source article (prev) to its top linked destination (curr). Hover to see destination.")

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
st.markdown('<div class="section-title" id="outlier-hyphen-minus">⚠️ Outliers: Excluded Articles</div>', unsafe_allow_html=True)

st.markdown("""
<div class="outlier-box">
    <b style="color:#fbbf24;">Hyphen-Minus</b><br>
    The article <i>Hyphen-Minus</i> received an anomalously high number of clicks across all months,
    widely attributed to a Wikipedia internal linking error that caused unintended redirects to this page.
    Including it would compress every other article into insignificance on every chart.
    It is tracked below separately for transparency.
</div>
""", unsafe_allow_html=True)

hm_display = hyphen_minus.copy()
if not is_all:
    hm_display = hm_display[hm_display["month"] == selected_month]

col_hm1, col_hm2 = st.columns([1, 2], gap="medium")

with col_hm1:
    total_hm = hm_display["total_clicks"].sum()
    st.markdown(f"""
    <div class="metric-card" style="height:auto; padding:1.25rem; background:#1e1a0e; border-color:#854d0e;">
        <div class="metric-value" style="color:#fbbf24;">{fmt_m(total_hm)}</div>
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

# ── Main_Page exclusion explanation ───────────────────────────────────────────
st.markdown("""
<div class="info-box">
    <b style="color:#60a5fa;">Why is Main Page excluded?</b><br>
    Wikipedia's <i>Main Page</i> is the default landing page of the entire site and receives a
    disproportionate volume of traffic by design — it is the first page every new visitor sees,
    and is linked from virtually every external source. Its click volume is so large that including
    it as a <code>curr</code> destination would make every other article appear negligible.
    Unlike Hyphen-Minus, this is not an error; it is simply not meaningful to compare editorial
    articles against a navigation hub. It has therefore been excluded from all <code>curr</code>
    counts across the entire dataset.
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style='color:#475569; font-size:0.75rem; text-align:center; font-weight:500;'>
    Data: Wikimedia Foundation · English Wikipedia Clickstream Sep 2025 – Feb 2026 &nbsp;|&nbsp;
    Processed with DuckDB &nbsp;|&nbsp; Visualised with Streamlit + Plotly
</p>
""", unsafe_allow_html=True)