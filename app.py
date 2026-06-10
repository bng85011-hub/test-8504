import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="매출 대시보드",
    page_icon="📊",
    layout="wide",
)

st.title("📊 매출 분석 대시보드")
st.markdown("---")


@st.cache_data
def load_data():
    df = pd.read_csv("sample_sales.csv", encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연월"] = df["날짜"].dt.to_period("M").astype(str)
    return df


df = load_data()

# ── 사이드바 필터 ──────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 필터")

    min_date = df["날짜"].min().date()
    max_date = df["날짜"].max().date()
    date_range = st.date_input(
        "기간 선택",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    all_categories = sorted(df["카테고리"].unique())
    selected_categories = st.multiselect(
        "카테고리", all_categories, default=all_categories
    )

    all_regions = sorted(df["지역"].unique())
    selected_regions = st.multiselect("지역", all_regions, default=all_regions)

# ── 데이터 필터링 ─────────────────────────────────────────────
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start, end = df["날짜"].min(), df["날짜"].max()

filtered = df[
    (df["날짜"] >= start)
    & (df["날짜"] <= end)
    & (df["카테고리"].isin(selected_categories))
    & (df["지역"].isin(selected_regions))
]

# ── KPI 카드 ──────────────────────────────────────────────────
total_sales = filtered["매출액"].sum()
total_orders = len(filtered)
avg_order = filtered["매출액"].mean() if total_orders > 0 else 0
total_qty = filtered["수량"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 총 매출", f"₩{total_sales:,.0f}")
col2.metric("🛒 총 주문 수", f"{total_orders:,}건")
col3.metric("📦 총 판매 수량", f"{total_qty:,}개")
col4.metric("💳 평균 주문금액", f"₩{avg_order:,.0f}")

st.markdown("---")

# ── 월별 매출 추이 ────────────────────────────────────────────
st.subheader("📈 월별 매출 추이")
monthly = (
    filtered.groupby("연월")["매출액"].sum().reset_index()
)
monthly.columns = ["연월", "매출액"]

fig_line = px.line(
    monthly,
    x="연월",
    y="매출액",
    markers=True,
    labels={"연월": "월", "매출액": "매출액 (원)"},
)
fig_line.update_traces(line_color="#4C78A8", marker_size=8)
fig_line.update_layout(
    xaxis_tickangle=-45,
    yaxis_tickformat=",",
    height=350,
    margin=dict(t=20),
)
st.plotly_chart(fig_line, use_container_width=True)

# ── 카테고리 & 지역별 매출 ────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🗂 카테고리별 매출")
    cat_sales = (
        filtered.groupby("카테고리")["매출액"].sum().reset_index().sort_values("매출액", ascending=True)
    )
    fig_cat = px.bar(
        cat_sales,
        x="매출액",
        y="카테고리",
        orientation="h",
        color="카테고리",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"매출액": "매출액 (원)", "카테고리": ""},
    )
    fig_cat.update_layout(
        showlegend=False,
        xaxis_tickformat=",",
        height=320,
        margin=dict(t=20),
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with col_right:
    st.subheader("🗺 지역별 매출")
    region_sales = (
        filtered.groupby("지역")["매출액"].sum().reset_index().sort_values("매출액", ascending=False)
    )
    fig_region = px.bar(
        region_sales,
        x="지역",
        y="매출액",
        color="지역",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        labels={"매출액": "매출액 (원)", "지역": ""},
    )
    fig_region.update_layout(
        showlegend=False,
        yaxis_tickformat=",",
        height=320,
        margin=dict(t=20),
    )
    st.plotly_chart(fig_region, use_container_width=True)

# ── 카테고리 비중 & 제품 TOP 10 ──────────────────────────────
col3_left, col3_right = st.columns(2)

with col3_left:
    st.subheader("🥧 카테고리 매출 비중")
    cat_pie = filtered.groupby("카테고리")["매출액"].sum().reset_index()
    fig_pie = px.pie(
        cat_pie,
        names="카테고리",
        values="매출액",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(height=320, margin=dict(t=20), showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with col3_right:
    st.subheader("🏆 제품별 매출 TOP 10")
    top_products = (
        filtered.groupby("제품명")["매출액"].sum().reset_index()
        .sort_values("매출액", ascending=False)
        .head(10)
    )
    top_products["순위"] = range(1, len(top_products) + 1)
    top_products["매출액"] = top_products["매출액"].map("{:,.0f}원".format)
    top_products = top_products[["순위", "제품명", "매출액"]].reset_index(drop=True)
    st.dataframe(top_products, use_container_width=True, hide_index=True, height=320)

# ── 담당자별 성과 ────────────────────────────────────────────
st.markdown("---")
st.subheader("👤 담당자별 성과")
rep_sales = (
    filtered.groupby("담당자")
    .agg(매출액=("매출액", "sum"), 주문수=("매출액", "count"), 판매수량=("수량", "sum"))
    .reset_index()
    .sort_values("매출액", ascending=False)
)
rep_sales["매출액"] = rep_sales["매출액"].map("{:,.0f}원".format)
rep_sales["판매수량"] = rep_sales["판매수량"].map("{:,}개".format)
rep_sales["주문수"] = rep_sales["주문수"].map("{:,}건".format)
st.dataframe(rep_sales, use_container_width=True, hide_index=True)

# ── 원본 데이터 ───────────────────────────────────────────────
st.markdown("---")
with st.expander("📄 원본 데이터 보기"):
    display_df = filtered.copy()
    display_df["날짜"] = display_df["날짜"].dt.strftime("%Y-%m-%d")
    display_df = display_df.drop(columns=["연월"])
    display_df["단가"] = display_df["단가"].map("{:,}원".format)
    display_df["매출액"] = display_df["매출액"].map("{:,}원".format)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.caption(f"총 {len(filtered):,}건의 데이터")
