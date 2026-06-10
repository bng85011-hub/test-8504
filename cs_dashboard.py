import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="CS 고객문의 대시보드",
    page_icon="🎧",
    layout="wide",
)

st.title("🎧 CS 고객문의 대시보드")
st.markdown("---")


@st.cache_data
def load_data():
    df = pd.read_csv("cs_inquiries.csv", encoding="utf-8-sig")
    df["접수일시"] = pd.to_datetime(df["접수일시"])
    df["접수일"] = df["접수일시"].dt.date
    return df


df = load_data()

# ── 사이드바 필터 ─────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 필터")

    min_date = df["접수일시"].min().date()
    max_date = df["접수일시"].max().date()
    date_range = st.date_input("접수 기간", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)

    all_channels = sorted(df["문의채널"].unique())
    sel_channels = st.multiselect("문의채널", all_channels, default=all_channels)

    all_types = sorted(df["문의유형"].unique())
    sel_types = st.multiselect("문의유형", all_types, default=all_types)

    all_statuses = sorted(df["처리상태"].unique())
    sel_statuses = st.multiselect("처리상태", all_statuses, default=all_statuses)

    all_handlers = sorted(df["처리담당자"].unique())
    sel_handlers = st.multiselect("담당자", all_handlers, default=all_handlers)

# ── 필터 적용 ─────────────────────────────────────────────────
if len(date_range) == 2:
    s, e = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    s, e = df["접수일시"].min(), df["접수일시"].max()

fdf = df[
    (df["접수일시"] >= s) & (df["접수일시"] <= e)
    & df["문의채널"].isin(sel_channels)
    & df["문의유형"].isin(sel_types)
    & df["처리상태"].isin(sel_statuses)
    & df["처리담당자"].isin(sel_handlers)
]

# ── KPI 카드 ──────────────────────────────────────────────────
total        = len(fdf)
completed    = len(fdf[fdf["처리상태"] == "처리완료"])
completion_r = completed / total * 100 if total else 0
avg_time     = fdf["처리시간(분)"].mean()
avg_sat      = fdf["고객만족도"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📋 총 문의 수",    f"{total:,}건")
c2.metric("✅ 처리완료",      f"{completed:,}건")
c3.metric("📈 처리완료율",    f"{completion_r:.1f}%")
c4.metric("⏱ 평균 처리시간", f"{avg_time:.0f}분" if pd.notna(avg_time) else "-")
c5.metric("⭐ 평균 만족도",   f"{avg_sat:.2f} / 5" if pd.notna(avg_sat) else "-")

st.markdown("---")

# ── 월별 문의 추이 & 처리상태 비중 ────────────────────────────
row1_l, row1_r = st.columns([2, 1])

with row1_l:
    st.subheader("📅 월별 문의 추이")
    monthly = fdf.groupby(["접수월", "처리상태"]).size().reset_index(name="건수")
    fig_trend = px.bar(
        monthly, x="접수월", y="건수", color="처리상태",
        color_discrete_map={"처리완료": "#2ecc71", "처리중": "#3498db",
                            "대기": "#e67e22", "재문의": "#e74c3c"},
        labels={"접수월": "월", "건수": "문의 건수"},
        barmode="stack",
    )
    fig_trend.update_layout(height=340, margin=dict(t=10), xaxis_tickangle=-45,
                            legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig_trend, width="stretch")

with row1_r:
    st.subheader("🔄 처리상태 현황")
    status_cnt = fdf["처리상태"].value_counts().reset_index()
    status_cnt.columns = ["처리상태", "건수"]
    color_map = {"처리완료": "#2ecc71", "처리중": "#3498db",
                 "대기": "#e67e22", "재문의": "#e74c3c"}
    fig_status = px.pie(status_cnt, names="처리상태", values="건수",
                        color="처리상태", color_discrete_map=color_map, hole=0.45)
    fig_status.update_traces(textposition="inside", textinfo="percent+label")
    fig_status.update_layout(height=340, margin=dict(t=10), showlegend=False)
    st.plotly_chart(fig_status, width="stretch")

# ── 문의유형 & 채널 ───────────────────────────────────────────
row2_l, row2_r = st.columns(2)

with row2_l:
    st.subheader("📂 문의유형별 현황")
    type_cnt = fdf["문의유형"].value_counts().reset_index()
    type_cnt.columns = ["문의유형", "건수"]
    fig_type = px.bar(
        type_cnt.sort_values("건수"), x="건수", y="문의유형",
        orientation="h", color="문의유형",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"건수": "문의 건수", "문의유형": ""},
    )
    fig_type.update_layout(height=300, margin=dict(t=10), showlegend=False)
    st.plotly_chart(fig_type, width="stretch")

with row2_r:
    st.subheader("📡 채널별 문의 현황")
    ch_cnt = fdf["문의채널"].value_counts().reset_index()
    ch_cnt.columns = ["문의채널", "건수"]
    fig_ch = px.bar(
        ch_cnt.sort_values("건수"), x="건수", y="문의채널",
        orientation="h", color="문의채널",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        labels={"건수": "문의 건수", "문의채널": ""},
    )
    fig_ch.update_layout(height=300, margin=dict(t=10), showlegend=False)
    st.plotly_chart(fig_ch, width="stretch")

# ── 시간대별 & 요일별 문의 히트맵 ────────────────────────────
st.subheader("🕐 시간대 × 요일별 문의 집중도")
dow_order  = ["월", "화", "수", "목", "금", "토", "일"]
hour_order = [f"{h:02d}시" for h in range(0, 24)]
heatmap_data = (
    fdf.groupby(["접수요일", "접수시간대"]).size()
    .reindex(pd.MultiIndex.from_product([dow_order, hour_order],
                                         names=["접수요일", "접수시간대"]), fill_value=0)
    .reset_index(name="건수")
)
heatmap_pivot = heatmap_data.pivot(index="접수요일", columns="접수시간대", values="건수")
fig_heat = px.imshow(
    heatmap_pivot, color_continuous_scale="Blues",
    labels=dict(x="시간대", y="요일", color="건수"),
    aspect="auto",
)
fig_heat.update_layout(height=280, margin=dict(t=10))
st.plotly_chart(fig_heat, width="stretch")

# ── 담당자별 성과 테이블 ──────────────────────────────────────
st.subheader("👤 담당자별 성과")
handler_df = (
    fdf.groupby("처리담당자")
    .agg(
        총문의=("문의번호", "count"),
        처리완료=("처리상태", lambda x: (x == "처리완료").sum()),
        평균처리시간=("처리시간(분)", "mean"),
        평균만족도=("고객만족도", "mean"),
    )
    .reset_index()
)
handler_df["처리완료율(%)"] = (handler_df["처리완료"] / handler_df["총문의"] * 100).round(1)
handler_df["평균처리시간"] = handler_df["평균처리시간"].round(1)
handler_df["평균만족도"]   = handler_df["평균만족도"].round(2)
handler_df = handler_df.sort_values("총문의", ascending=False).reset_index(drop=True)
handler_df = handler_df[["처리담당자", "총문의", "처리완료", "처리완료율(%)", "평균처리시간", "평균만족도"]]
st.dataframe(handler_df, width="stretch", hide_index=True)

# ── 만족도 분포 & 유형별 평균 처리시간 ───────────────────────
row4_l, row4_r = st.columns(2)

with row4_l:
    st.subheader("⭐ 고객만족도 분포")
    sat_data = fdf["고객만족도"].dropna().astype(int).value_counts().sort_index().reset_index()
    sat_data.columns = ["만족도", "건수"]
    sat_data["만족도"] = sat_data["만족도"].map({1: "1점", 2: "2점", 3: "3점", 4: "4점", 5: "5점"})
    fig_sat = px.bar(
        sat_data, x="만족도", y="건수",
        color="만족도",
        color_discrete_sequence=["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#27ae60"],
        labels={"건수": "응답 수", "만족도": ""},
    )
    fig_sat.update_layout(height=280, margin=dict(t=10), showlegend=False)
    st.plotly_chart(fig_sat, width="stretch")

with row4_r:
    st.subheader("⏱ 문의유형별 평균 처리시간")
    type_time = (
        fdf.groupby("문의유형")["처리시간(분)"].mean().dropna()
        .reset_index().sort_values("처리시간(분)", ascending=True)
    )
    type_time.columns = ["문의유형", "평균처리시간(분)"]
    fig_time = px.bar(
        type_time, x="평균처리시간(분)", y="문의유형",
        orientation="h", color="문의유형",
        color_discrete_sequence=px.colors.qualitative.Set3,
        labels={"평균처리시간(분)": "평균 처리시간 (분)", "문의유형": ""},
    )
    fig_time.update_layout(height=280, margin=dict(t=10), showlegend=False)
    st.plotly_chart(fig_time, width="stretch")

# ── 원본 데이터 ───────────────────────────────────────────────
st.markdown("---")
with st.expander("📄 원본 데이터 보기"):
    show = fdf.drop(columns=["접수일"]).copy()
    show["접수일시"] = show["접수일시"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(show, width="stretch", hide_index=True)
    st.caption(f"총 {len(fdf):,}건")
