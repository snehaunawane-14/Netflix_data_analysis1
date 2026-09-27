from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


st.set_page_config(
    page_title="Netflix Data Analysis",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_FILE = Path(__file__).with_name("Netflix_100_Customers_Dataset.csv")
IMAGE_DIR = Path(__file__).with_name("images")
IMAGE_FILES = sorted(
    image_path
    for image_path in IMAGE_DIR.glob("*")
    if image_path.is_file() and image_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".avif"}
)
NETFLIX_RED = "#E50914"
NETFLIX_DARK_RED = "#B20710"
CHART_BLACK = "#050505"
CHART_PANEL = "#0B0B0B"
CHART_GRID = "#303030"


def load_data(source):
    file_name = getattr(source, "name", str(source)).lower()
    if file_name.endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(source)
        except Exception:
            if hasattr(source, "seek"):
                source.seek(0)
            return pd.read_csv(source)
    return pd.read_csv(source)


def prepare_data(data):
    data = data.drop_duplicates().copy()
    if "Watch_Date" in data:
        data["Watch_Date"] = pd.to_datetime(data["Watch_Date"], errors="coerce")
    for column in ("Rating", "Watch_Count", "Watch_Time_Minutes", "Monthly_Revenue"):
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def render_percentage_bar(series, color=NETFLIX_RED, horizontal=False):
    values = pd.to_numeric(series, errors="coerce").dropna()
    values = values[values >= 0]
    total = values.sum()
    if values.empty or total <= 0:
        st.info("No positive values are available for this chart.")
        return

    figure, axis = plt.subplots(figsize=(8, 4.5), facecolor=CHART_BLACK)
    axis.set_facecolor(CHART_PANEL)
    axis.tick_params(colors="#ffffff")
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(CHART_GRID)
    axis.spines["bottom"].set_color(CHART_GRID)

    if horizontal:
        bars = axis.barh(values.index.astype(str), values, color=color)
        axis.set_xlim(0, values.max() * 1.4)
        for bar, value in zip(bars, values):
            percent = value / total * 100
            axis.text(value + values.max() * 0.025, bar.get_y() + bar.get_height() / 2,
                      f"{percent:.1f}%  |  {value:,.0f}", va="center", color="#f5f3ee", fontsize=9)
        axis.grid(axis="x", color=CHART_GRID, alpha=0.7)
    else:
        bars = axis.bar(values.index.astype(str), values, color=color, width=0.65)
        axis.set_ylim(0, values.max() * 1.32)
        for bar, value in zip(bars, values):
            percent = value / total * 100
            axis.text(bar.get_x() + bar.get_width() / 2, value + values.max() * 0.025,
                      f"{percent:.1f}%\n{value:,.0f}", ha="center", va="bottom", color="#f5f3ee", fontsize=9)
        axis.grid(axis="y", color=CHART_GRID, alpha=0.7)

    axis.set_axisbelow(True)
    figure.tight_layout()
    st.pyplot(figure, width="stretch")
    plt.close(figure)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink: #ffffff; --muted: #b4b4b4; --red: #e50914; --red-dark: #b20710; --panel: #0b0b0b; --border: #292929; }
    .stApp { background: #050505; color: var(--ink); font-family: 'DM Sans', sans-serif; }
    [data-testid="stSidebar"] { background: #080808; border-right: 1px solid var(--border); }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: 0 !important; }
    h1 { font-size: 2.5rem !important; margin-bottom: .15rem !important; }
    .eyebrow { color: #e50914; font-size: .72rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    .subhead { color: #b4b4b4; margin: 0 0 1.25rem; }
    .dashboard-hero { border-bottom: 2px solid #e50914; padding-bottom: 1rem; margin-bottom: 1rem; }
    [data-testid="stImage"] img { border: 1px solid var(--red-dark); border-radius: 3px; }
    div[data-testid="stMetric"] { background: #0b0b0b; border: 1px solid #2d2d2d; border-top: 3px solid #e50914; padding: 1rem 1.1rem; border-radius: 4px; }
    div[data-testid="stMetricLabel"] { color: #b4b4b4; }
    div[data-testid="stMetricValue"] { font-family: 'Space Grotesk', sans-serif; }
    .section-label { color: #b4b4b4; font-size: .74rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; margin: .3rem 0 .55rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("<div class='eyebrow'>NETFLIX / INSIGHTS</div>", unsafe_allow_html=True)
    st.title("Explore data")
    uploaded_file = st.file_uploader("Choose a dataset", type=["csv", "xls", "xlsx"])

    data_source = uploaded_file if uploaded_file else DATA_FILE
    if uploaded_file is None:
        st.caption(f"Using {DATA_FILE.name}" if DATA_FILE.exists() else "Upload a CSV or Excel file to begin.")

    if not uploaded_file and not DATA_FILE.exists():
        st.info("Add the customer dataset beside this app or upload a file.")
        st.stop()

    try:
        raw_data = load_data(data_source)
    except Exception as error:
        st.error(f"Could not read this dataset: {error}")
        st.stop()

    data = prepare_data(raw_data)
    filtered = data.copy()

    st.divider()
    st.markdown("<div class='section-label'>Filters</div>", unsafe_allow_html=True)
    for column, label in (("Region", "Region"), ("Subscription_Plan", "Plan"), ("Type", "Content type"), ("Device", "Device")):
        if column in filtered:
            options = sorted(filtered[column].dropna().astype(str).unique())
            selection = st.multiselect(label, options, default=options)
            filtered = filtered[filtered[column].astype(str).isin(selection)]

    if "Watch_Date" in filtered and filtered["Watch_Date"].notna().any():
        min_date = filtered["Watch_Date"].min().date()
        max_date = filtered["Watch_Date"].max().date()
        selected_dates = st.date_input("Watch date", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
            filtered = filtered[filtered["Watch_Date"].dt.date.between(start_date, end_date)]

hero_text, hero_images = st.columns([1.1, 1.5], vertical_alignment="center")
with hero_text:
    st.markdown("<div class='dashboard-hero'><div class='eyebrow'>AUDIENCE & VIEWING</div>", unsafe_allow_html=True)
    st.title("Netflix Data Analysis")
    st.markdown("<p class='subhead'>Explore revenue, ratings, and viewing activity.</p></div>", unsafe_allow_html=True)
with hero_images:
    available_images = [image for image in IMAGE_FILES if image.exists()]
    if available_images:
        image_columns = st.columns(len(available_images), gap="small")
        for column, image_path in zip(image_columns, available_images):
            with column:
                st.image(str(image_path), width="stretch")

if filtered.empty:
    st.warning("No records match the selected filters. Adjust them in the sidebar.")
    st.stop()

bar_tab, pie_tab, line_tab = st.tabs(["Bar Charts", "Pie Charts", "Line Charts"])

with bar_tab:
    first, second = st.columns(2)
    with first:
        st.markdown("<div class='section-label'>Revenue by region</div>", unsafe_allow_html=True)
        if {"Region", "Monthly_Revenue"}.issubset(filtered.columns):
            by_region = filtered.groupby("Region")["Monthly_Revenue"].sum().sort_values(ascending=False)
            render_percentage_bar(by_region, horizontal=True)
    with second:
        st.markdown("<div class='section-label'>Viewing by subscription plan</div>", unsafe_allow_html=True)
        if {"Subscription_Plan", "Watch_Count"}.issubset(filtered.columns):
            by_plan = filtered.groupby("Subscription_Plan")["Watch_Count"].sum().sort_values(ascending=False)
            render_percentage_bar(by_plan, color=NETFLIX_DARK_RED)
    if "Rating" in filtered:
        st.markdown("<div class='section-label'>Rating distribution</div>", unsafe_allow_html=True)
        render_percentage_bar(filtered["Rating"].dropna().value_counts().sort_index())
    if {"Watch_Date", "Monthly_Revenue"}.issubset(filtered.columns):
        st.markdown("<div class='section-label'>Monthly revenue</div>", unsafe_allow_html=True)
        monthly_revenue = filtered.dropna(subset=["Watch_Date"]).groupby(
            filtered.dropna(subset=["Watch_Date"])["Watch_Date"].dt.to_period("M").astype(str)
        )["Monthly_Revenue"].sum()
        render_percentage_bar(monthly_revenue, color=NETFLIX_DARK_RED)
    if {"Category", "Watch_Count"}.issubset(filtered.columns):
        st.markdown("<div class='section-label'>Viewing by category</div>", unsafe_allow_html=True)
        category_watches = filtered.groupby("Category")["Watch_Count"].sum().sort_values(ascending=False)
        render_percentage_bar(category_watches, horizontal=True)
    if {"Device", "Customer_ID"}.issubset(filtered.columns):
        st.markdown("<div class='section-label'>Customers by device</div>", unsafe_allow_html=True)
        device_customers = filtered.groupby("Device")["Customer_ID"].nunique().sort_values(ascending=False)
        render_percentage_bar(device_customers, color=NETFLIX_DARK_RED)

    customer_plan_column, content_type_column = st.columns(2)
    with customer_plan_column:
        if {"Subscription_Plan", "Customer_ID"}.issubset(filtered.columns):
            st.markdown("<div class='section-label'>Customer share by subscription plan</div>", unsafe_allow_html=True)
            customers_by_plan = filtered.groupby("Subscription_Plan")["Customer_ID"].nunique().sort_values(ascending=False)
            render_percentage_bar(customers_by_plan, color=NETFLIX_DARK_RED)
    with content_type_column:
        if {"Type", "Watch_Count"}.issubset(filtered.columns):
            st.markdown("<div class='section-label'>Watch share by content type</div>", unsafe_allow_html=True)
            watches_by_type = filtered.groupby("Type")["Watch_Count"].sum().sort_values(ascending=False)
            render_percentage_bar(watches_by_type)

    if {"Language", "Watch_Time_Minutes"}.issubset(filtered.columns):
        st.markdown("<div class='section-label'>Watch time share by language</div>", unsafe_allow_html=True)
        watch_time_by_language = filtered.groupby("Language")["Watch_Time_Minutes"].sum().sort_values(ascending=False)
        render_percentage_bar(watch_time_by_language, color=NETFLIX_DARK_RED, horizontal=True)

with pie_tab:
    first, second = st.columns(2)
    if {"Region", "Rating"}.issubset(filtered.columns):
        with first:
            st.markdown("<div class='section-label'>Rating share by region</div>", unsafe_allow_html=True)
            region_ratings = filtered.groupby("Region")["Rating"].sum()
            figure, axis = plt.subplots(figsize=(5, 4), facecolor=CHART_BLACK)
            axis.set_facecolor(CHART_PANEL)
            axis.pie(
                region_ratings,
                labels=region_ratings.index,
                autopct="%1.1f%%",
                startangle=90,
                colors=[NETFLIX_RED, NETFLIX_DARK_RED, "#7A050B", "#4A0307"],
                textprops={"color": "#ffffff"},
                wedgeprops={"edgecolor": "#000000", "linewidth": 2},
            )
            axis.axis("equal")
            st.pyplot(figure, width="stretch")
            plt.close(figure)
    if {"Subscription_Plan", "Watch_Count"}.issubset(filtered.columns):
        with second:
            st.markdown("<div class='section-label'>Watch share by subscription plan</div>", unsafe_allow_html=True)
            plan_watches = filtered.groupby("Subscription_Plan")["Watch_Count"].sum()
            figure, axis = plt.subplots(figsize=(5, 4), facecolor=CHART_BLACK)
            axis.set_facecolor(CHART_PANEL)
            axis.pie(
                plan_watches,
                labels=plan_watches.index,
                autopct="%1.1f%%",
                startangle=90,
                colors=[NETFLIX_RED, NETFLIX_DARK_RED, "#7A050B"],
                textprops={"color": "#ffffff"},
                wedgeprops={"edgecolor": "#000000", "linewidth": 2},
            )
            axis.axis("equal")
            st.pyplot(figure, width="stretch")
            plt.close(figure)

with line_tab:
    st.markdown("<div class='section-label'>Revenue over time</div>", unsafe_allow_html=True)
    if {"Watch_Date", "Monthly_Revenue"}.issubset(filtered.columns):
        revenue_by_month = filtered.dropna(subset=["Watch_Date"]).set_index("Watch_Date").resample("MS")["Monthly_Revenue"].sum()
        st.line_chart(revenue_by_month, color=NETFLIX_RED, height=360)
    if {"Device", "Monthly_Revenue"}.issubset(filtered.columns):
        st.markdown("<div class='section-label'>Revenue by device</div>", unsafe_allow_html=True)
        revenue_by_device = filtered.groupby("Device")["Monthly_Revenue"].sum()
        st.line_chart(revenue_by_device, color=NETFLIX_DARK_RED, height=300)
