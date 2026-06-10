import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="삼천리 CS 고객문의 대시보드", page_icon="🎧", layout="wide")

# ── 브랜드 컬러 (삼천리 CI #0077C8, PANTONE 3005C) ───────────
SC_BLUE       = "#0077C8"
SC_DARK       = "#005A99"
SC_LIGHT      = "#4AA8E0"
SC_PALE       = "#D6EAFA"
SC_SUCCESS    = "#00A878"
SC_WARNING    = "#F5A623"
SC_DANGER     = "#E85D5D"
SC_PROCESS    = "#4AA8E0"
STATUS_COLORS = {"처리완료": SC_SUCCESS, "처리중": SC_PROCESS, "대기": SC_WARNING, "재문의": SC_DANGER}
QUAL_PALETTE  = [SC_BLUE, SC_SUCCESS, SC_WARNING, SC_DANGER, "#8B5CF6", "#EC4899", "#14B8A6"]

# ── 전역 CSS ─────────────────────────────────────────────────
st.markdown(f"""<style>
html, body, [class*="css"] {{ font-family: "Malgun Gothic", "맑은 고딕", sans-serif !important; }}
.stApp {{ background: #F0F6FC; }}
section[data-testid="stSidebar"] {{ background: #1A2B3C !important; }}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {{ color: #D6EAFA !important; }}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{ color: #ffffff !important; }}
[data-testid="metric-container"] {{
    background: #ffffff;
    border-radius: 12px;
    border-left: 4px solid {SC_BLUE};
    padding: 14px 18px !important;
    box-shadow: 0 2px 10px rgba(0,119,200,0.12);
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    font-size: 0.82rem !important;
    color: #6B7E94 !important;
    font-weight: 600;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 1.45rem !important;
    color: #1A2B3C !important;
    font-weight: 700;
}}
.stTabs [data-baseweb="tab-list"] {{ background: transparent; gap: 4px; }}
.stTabs [data-baseweb="tab"] {{
    font-weight: 600; font-size: 0.88rem;
    border-radius: 8px 8px 0 0;
    padding: 8px 18px;
    color: #6B7E94;
}}
.stTabs [aria-selected="true"] {{
    color: {SC_BLUE} !important;
    background: #ffffff;
    border-bottom: 3px solid {SC_BLUE} !important;
}}
h2, h3 {{ color: #1A2B3C !important; }}
.stButton>button {{
    background: {SC_BLUE}; color: #fff;
    border-radius: 8px; border: none; font-weight: 600;
}}
.stButton>button:hover {{ background: {SC_DARK}; }}
hr {{ border-color: {SC_PALE}; }}
</style>""", unsafe_allow_html=True)

# ── 공통 차트 레이아웃 함수 ───────────────────────────────────
def cl(fig, height=320, **kwargs):
    fig.update_layout(
        height=height,
        margin=dict(t=16, b=8, l=8, r=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Malgun Gothic, 맑은 고딕, sans-serif", color="#1A2B3C", size=12),
        **kwargs,
    )
    fig.update_xaxes(gridcolor="#E8F2FB", zeroline=False, linecolor="#D0E4F5")
    fig.update_yaxes(gridcolor="#E8F2FB", zeroline=False, linecolor="#D0E4F5")
    return fig

# ── 데이터 로딩 ───────────────────────────────────────────────
@st.cache_data
def load_data():
    inq = pd.read_csv("data/cs_inquiries_large.csv", encoding="utf-8-sig")
    inq["접수일시"] = pd.to_datetime(inq["접수일시"])
    inq["접수일"] = inq["접수일시"].dt.date

    agents = pd.read_csv("data/cs_agents.csv", encoding="utf-8-sig")
    inq = inq.merge(agents[["담당자명", "팀", "직급"]],
                    left_on="처리담당자", right_on="담당자명", how="left")

    kpi = pd.read_csv("data/cs_kpi_monthly.csv", encoding="utf-8-sig")
    kpi = kpi.merge(agents[["담당자명", "직급"]], on="담당자명", how="left")

    cust = pd.read_csv("data/cs_customers.csv", encoding="utf-8-sig")
    return inq, agents, kpi, cust

inq_all, agents, kpi, cust = load_data()

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:16px 0 12px;border-bottom:1px solid #2E4060;margin-bottom:16px">
      <div style="font-size:1.5rem;font-weight:700;color:{SC_LIGHT};letter-spacing:2px">삼천리</div>
      <div style="font-size:0.72rem;color:#6B7E94;margin-top:2px">CS Analytics Dashboard</div>
    </div>""", unsafe_allow_html=True)
    st.header("🔍 필터")
    st.caption("탭 1~4에 적용됩니다")

    min_d, max_d = inq_all["접수일시"].min().date(), inq_all["접수일시"].max().date()
    dr = st.date_input("접수 기간", value=(min_d, max_d), min_value=min_d, max_value=max_d)

    all_types   = sorted(inq_all["문의유형"].unique())
    sel_types   = st.multiselect("문의유형", all_types, default=all_types)

    all_regions = sorted(inq_all["지역"].unique())
    sel_regions = st.multiselect("지역", all_regions, default=all_regions)

    st.markdown("---")
    st.caption("탭 5(인사이트)는 전체 기간 고정")

# ── 필터 적용 ─────────────────────────────────────────────────
s = pd.Timestamp(dr[0]) if len(dr) >= 1 else inq_all["접수일시"].min()
e = pd.Timestamp(dr[1]) if len(dr) == 2 else inq_all["접수일시"].max()

df = inq_all[
    (inq_all["접수일시"] >= s) & (inq_all["접수일시"] <= e)
    & inq_all["문의유형"].isin(sel_types)
    & inq_all["지역"].isin(sel_regions)
]

# ── 헤더 ─────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,{SC_BLUE},{SC_DARK});
            padding:22px 30px;border-radius:16px;margin-bottom:20px;
            box-shadow:0 4px 16px rgba(0,119,200,0.25)">
  <div style="font-size:1.65rem;font-weight:700;color:#ffffff;
              font-family:'Malgun Gothic','맑은 고딕',sans-serif">
    🎧 삼천리 CS 고객문의 분석 대시보드
  </div>
  <div style="color:{SC_PALE};font-size:0.85rem;margin-top:6px;
              font-family:'Malgun Gothic','맑은 고딕',sans-serif">
    전체 데이터: {len(inq_all):,}건 &nbsp;|&nbsp; 필터 적용: {len(df):,}건
  </div>
</div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 전체 현황", "📋 문의 패턴", "⚡ SLA & 품질", "👤 상담원 성과", "🎯 개선 인사이트", "🤖 AI 대화"
])

# ════════════════════════════════════════════════════════════════
# 탭 1 — 전체 현황
# ════════════════════════════════════════════════════════════════
with tab1:
    total     = len(df)
    completed = (df["처리상태"] == "처리완료").sum()
    pending   = df["처리상태"].isin(["처리중", "대기"]).sum()
    reinquiry = (df["처리상태"] == "재문의").sum()

    sla_base  = df[df["SLA준수"] != "미결"]
    sla_rate  = (sla_base["SLA준수"] == "Y").mean() * 100 if len(sla_base) else 0
    avg_sat   = df["고객만족도"].mean()
    reinq_rate = reinquiry / total * 100 if total else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📋 총 문의",     f"{total:,}건")
    c2.metric("✅ 처리완료율",   f"{completed/total*100:.1f}%" if total else "-")
    c3.metric("⚡ SLA 달성율",   f"{sla_rate:.1f}%")
    c4.metric("⭐ 평균 만족도",  f"{avg_sat:.2f}점" if pd.notna(avg_sat) else "-")
    c5.metric("⏳ 미처리 건수",  f"{pending:,}건")
    c6.metric("🔄 재문의율",     f"{reinq_rate:.1f}%")

    st.markdown("---")
    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.subheader("📅 월별 문의 추이 (처리상태별)")
        monthly_status = df.groupby(["접수월", "처리상태"]).size().reset_index(name="건수")
        fig = px.bar(monthly_status, x="접수월", y="건수", color="처리상태", barmode="stack",
                     color_discrete_map=STATUS_COLORS,
                     labels={"접수월":"월","건수":"문의 건수"})
        cl(fig, height=320, xaxis_tickangle=-45,
           legend=dict(orientation="h", y=-0.35))
        st.plotly_chart(fig, width="stretch")

    with col_r:
        st.subheader("📡 채널별 문의 비중")
        ch = df["문의채널"].value_counts().reset_index()
        ch.columns = ["채널", "건수"]
        fig2 = px.pie(ch, names="채널", values="건수", hole=0.48,
                      color_discrete_sequence=QUAL_PALETTE)
        fig2.update_traces(textposition="inside", textinfo="percent+label",
                           marker=dict(line=dict(color="#fff", width=2)))
        cl(fig2, height=320, showlegend=False)
        st.plotly_chart(fig2, width="stretch")

    st.subheader("🗂 문의유형 × 처리상태 히트맵")
    hm = df.groupby(["문의유형", "처리상태"]).size().reset_index(name="건수")
    hm_pivot = hm.pivot(index="문의유형", columns="처리상태", values="건수").fillna(0)
    fig3 = px.imshow(hm_pivot,
                     color_continuous_scale=[[0, SC_PALE], [0.5, SC_LIGHT], [1, SC_DARK]],
                     labels=dict(x="처리상태", y="문의유형", color="건수"), text_auto=True)
    cl(fig3, height=300)
    st.plotly_chart(fig3, width="stretch")

# ════════════════════════════════════════════════════════════════
# 탭 2 — 문의 패턴 분석
# ════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🕐 시간대 × 요일 문의 집중도")
    dow_order  = ["월", "화", "수", "목", "금", "토", "일"]
    hour_order = [f"{h:02d}시" for h in range(0, 24)]
    hm2 = (df.groupby(["접수요일", "접수시간대"]).size()
             .reindex(pd.MultiIndex.from_product([dow_order, hour_order],
                                                  names=["접수요일","접수시간대"]), fill_value=0)
             .reset_index(name="건수"))
    hm2_pivot = hm2.pivot(index="접수요일", columns="접수시간대", values="건수")
    hm2_pivot = hm2_pivot.reindex(dow_order)
    fig_heat = px.imshow(
        hm2_pivot,
        color_continuous_scale=[[0, SC_PALE], [0.5, SC_LIGHT], [1, SC_DARK]],
        labels=dict(x="시간대", y="요일", color="건수"),
        aspect="auto",
        text_auto=True,
    )
    fig_heat.update_traces(textfont=dict(size=9))
    cl(fig_heat, height=340,
       coloraxis_colorbar=dict(title="건수", thickness=14),
       xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
       yaxis=dict(tickfont=dict(size=11)))
    st.plotly_chart(fig_heat, width="stretch")

    col2_l, col2_r = st.columns(2)

    with col2_l:
        st.subheader("🗺 지역별 문의 현황")
        region_cnt = df["지역"].value_counts().reset_index()
        region_cnt.columns = ["지역", "건수"]
        fig_r = px.bar(region_cnt, x="건수", y="지역", orientation="h",
                       color="건수",
                       color_continuous_scale=[[0, SC_PALE], [1, SC_DARK]],
                       labels={"건수":"문의 건수","지역":""})
        cl(fig_r, height=380, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_r, width="stretch")

    with col2_r:
        st.subheader("📂 문의유형별 월별 추이")
        type_monthly = df.groupby(["접수월", "문의유형"]).size().reset_index(name="건수")
        fig_tm = px.line(type_monthly, x="접수월", y="건수", color="문의유형",
                         markers=True,
                         color_discrete_sequence=QUAL_PALETTE,
                         labels={"접수월":"월","건수":"건수"})
        cl(fig_tm, height=380, xaxis_tickangle=-45,
           legend=dict(orientation="h", y=-0.45))
        st.plotly_chart(fig_tm, width="stretch")

    st.subheader("🚨 우선순위별 처리 현황")
    pri_status = df.groupby(["우선순위", "처리상태"]).size().reset_index(name="건수")
    fig_pri = px.bar(pri_status, x="우선순위", y="건수", color="처리상태",
                     barmode="group",
                     color_discrete_map=STATUS_COLORS,
                     category_orders={"우선순위": ["높음", "보통", "낮음"]},
                     labels={"우선순위":"우선순위","건수":"건수"})
    cl(fig_pri, height=280, legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig_pri, width="stretch")

# ════════════════════════════════════════════════════════════════
# 탭 3 — SLA & 품질 분석
# ════════════════════════════════════════════════════════════════
with tab3:
    col3_l, col3_r = st.columns(2)

    with col3_l:
        st.subheader("📈 SLA 월별 달성률 추이")
        sla_monthly = (df[df["SLA준수"] != "미결"]
                       .groupby("접수월")
                       .apply(lambda x: (x["SLA준수"] == "Y").mean() * 100)
                       .reset_index(name="SLA달성율(%)"))
        fig_sla = px.line(sla_monthly, x="접수월", y="SLA달성율(%)", markers=True,
                          labels={"접수월":"월"})
        fig_sla.add_hline(y=80, line_dash="dash", line_color=SC_DANGER,
                          annotation_text="목표 80%", annotation_position="right")
        fig_sla.update_traces(line_color=SC_BLUE, marker=dict(color=SC_BLUE, size=8))
        cl(fig_sla, height=300, xaxis_tickangle=-45)
        st.plotly_chart(fig_sla, width="stretch")

    with col3_r:
        st.subheader("🗂 문의유형별 SLA 달성률")
        sla_type = (df[df["SLA준수"] != "미결"]
                    .groupby("문의유형")
                    .apply(lambda x: (x["SLA준수"] == "Y").mean() * 100)
                    .reset_index(name="SLA달성율(%)"))
        sla_type = sla_type.sort_values("SLA달성율(%)")
        sla_type["색상"] = sla_type["SLA달성율(%)"].apply(
            lambda v: SC_DANGER if v < 70 else (SC_WARNING if v < 80 else SC_SUCCESS))
        fig_st = px.bar(sla_type, x="SLA달성율(%)", y="문의유형", orientation="h",
                        labels={"SLA달성율(%)":"SLA 달성율 (%)","문의유형":""},
                        color="색상", color_discrete_map="identity")
        fig_st.add_vline(x=80, line_dash="dash", line_color="#aaa",
                         annotation_text="목표 80%")
        cl(fig_st, height=300, showlegend=False)
        st.plotly_chart(fig_st, width="stretch")

    col3_b, col3_c = st.columns(2)

    with col3_b:
        st.subheader("🔍 처리시간 vs 고객만족도")
        scatter_df = df[df["처리시간(분)"].notna() & df["고객만족도"].notna()].copy()
        scatter_df["처리시간(분)"] = scatter_df["처리시간(분)"].clip(upper=120)
        fig_sc = px.scatter(scatter_df, x="처리시간(분)", y="고객만족도",
                            color="문의유형", opacity=0.55,
                            color_discrete_sequence=QUAL_PALETTE,
                            labels={"처리시간(분)":"처리시간 (분)","고객만족도":"만족도"})
        cl(fig_sc, height=320, legend=dict(orientation="h", y=-0.4))
        st.plotly_chart(fig_sc, width="stretch")

    with col3_c:
        st.subheader("📡 채널별 평균 만족도")
        ch_sat = (df.groupby("문의채널")["고객만족도"].mean()
                  .reset_index().sort_values("고객만족도"))
        ch_sat.columns = ["채널", "평균만족도"]
        ch_sat["색상"] = ch_sat["평균만족도"].apply(
            lambda v: SC_DANGER if v < 3.5 else (SC_WARNING if v < 4.0 else SC_SUCCESS))
        fig_cs = px.bar(ch_sat, x="평균만족도", y="채널", orientation="h",
                        color="색상", color_discrete_map="identity",
                        labels={"평균만족도":"평균 만족도","채널":""})
        fig_cs.add_vline(x=3.5, line_dash="dash", line_color="#aaa",
                         annotation_text="주의선 3.5")
        cl(fig_cs, height=320, showlegend=False)
        st.plotly_chart(fig_cs, width="stretch")

    st.subheader("🔄 재문의 발생 분석 — 유형·담당자 TOP 5")
    col3_d, col3_e = st.columns(2)
    reinq_df = df[df["처리상태"] == "재문의"]

    with col3_d:
        r_type = reinq_df["문의유형"].value_counts().head(5).reset_index()
        r_type.columns = ["문의유형", "재문의 건수"]
        fig_rt = px.bar(r_type, x="재문의 건수", y="문의유형", orientation="h",
                        color_discrete_sequence=[SC_DANGER],
                        labels={"재문의 건수":"재문의 건수","문의유형":""})
        cl(fig_rt, height=240)
        st.plotly_chart(fig_rt, width="stretch")

    with col3_e:
        r_agent = reinq_df["처리담당자"].value_counts().head(5).reset_index()
        r_agent.columns = ["담당자", "재문의 건수"]
        fig_ra = px.bar(r_agent, x="재문의 건수", y="담당자", orientation="h",
                        color_discrete_sequence=[SC_WARNING],
                        labels={"재문의 건수":"재문의 건수","담당자":""})
        cl(fig_ra, height=240)
        st.plotly_chart(fig_ra, width="stretch")

# ════════════════════════════════════════════════════════════════
# 탭 4 — 상담원 성과
# ════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📈 팀별 월별 목표달성율 추이")
    team_kpi = kpi.groupby(["연월", "팀"])["목표달성율(%)"].mean().reset_index()
    fig_team = px.line(team_kpi, x="연월", y="목표달성율(%)", color="팀",
                       markers=True,
                       color_discrete_sequence=[SC_BLUE, SC_LIGHT, SC_SUCCESS],
                       labels={"연월":"월","목표달성율(%)":"목표달성율 (%)"})
    fig_team.add_hline(y=100, line_dash="dash", line_color="#aaa",
                       annotation_text="목표 100%")
    cl(fig_team, height=300, xaxis_tickangle=-45)
    st.plotly_chart(fig_team, width="stretch")

    col4_l, col4_r = st.columns(2)

    with col4_l:
        st.subheader("🕸 담당자별 KPI 레이더 차트")
        handler_avg = kpi.groupby("담당자명").agg(
            실적건수=("실적건수", "mean"),
            처리완료율=("처리완료율(%)", "mean"),
            SLA달성율=("SLA달성율(%)", "mean"),
            평균만족도=("평균만족도", "mean"),
        ).reset_index()

        for col in ["실적건수", "처리완료율", "SLA달성율", "평균만족도"]:
            mn, mx = handler_avg[col].min(), handler_avg[col].max()
            handler_avg[col] = (handler_avg[col] - mn) / (mx - mn + 1e-9)

        categories = ["실적건수", "처리완료율", "SLA달성율", "평균만족도"]
        fig_radar = go.Figure()
        for i, row in handler_avg.iterrows():
            vals = [row[c] for c in categories] + [row[categories[0]]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=categories + [categories[0]],
                fill="toself", name=row["담당자명"],
                line_color=QUAL_PALETTE[i % len(QUAL_PALETTE)], opacity=0.65,
            ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1], gridcolor="#E8F2FB"),
                angularaxis=dict(gridcolor="#E8F2FB"),
                bgcolor="rgba(0,0,0,0)",
            ),
            height=380, margin=dict(t=30, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Malgun Gothic, 맑은 고딕, sans-serif", color="#1A2B3C"),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_radar, width="stretch")

    with col4_r:
        st.subheader("📉 결근일수 vs 목표달성율")
        abs_data = kpi.groupby("담당자명").agg(
            결근일수=("결근일수", "sum"),
            목표달성율=("목표달성율(%)", "mean"),
            팀=("팀", "first"),
        ).reset_index()
        fig_abs = px.scatter(abs_data, x="결근일수", y="목표달성율",
                             text="담당자명", color="팀", size_max=14,
                             color_discrete_sequence=[SC_BLUE, SC_LIGHT, SC_SUCCESS],
                             labels={"결근일수":"연간 결근일수","목표달성율":"평균 목표달성율 (%)"})
        fig_abs.update_traces(textposition="top center")
        cl(fig_abs, height=380)
        st.plotly_chart(fig_abs, width="stretch")

    st.subheader("📋 담당자별 성과 종합")
    summary = kpi.groupby("담당자명").agg(
        팀=("팀", "first"),
        직급=("직급", "first"),
        월평균실적=("실적건수", "mean"),
        목표달성율=("목표달성율(%)", "mean"),
        처리완료율=("처리완료율(%)", "mean"),
        SLA달성율=("SLA달성율(%)", "mean"),
        평균만족도=("평균만족도", "mean"),
        결근일수합계=("결근일수", "sum"),
    ).reset_index().sort_values("목표달성율", ascending=False)
    for col in ["월평균실적", "목표달성율", "처리완료율", "SLA달성율", "평균만족도"]:
        summary[col] = summary[col].round(1)
    st.dataframe(summary, hide_index=True, width=900)

# ════════════════════════════════════════════════════════════════
# 탭 5 — 개선 인사이트 (전체 데이터 고정)
# ════════════════════════════════════════════════════════════════
with tab5:
    full = inq_all
    st.caption("⚠️ 이 탭은 전체 기간·전체 데이터 기준으로 계산됩니다")
    st.markdown("---")

    sla_t = (full[full["SLA준수"] != "미결"]
             .groupby("문의유형")
             .apply(lambda x: (x["SLA준수"] == "Y").mean() * 100))

    reinq_t = (full.groupby("문의유형")
               .apply(lambda x: (x["처리상태"] == "재문의").mean() * 100))

    sat_ch = full.groupby("문의채널")["고객만족도"].mean()

    peak = (full.groupby("접수시간대")
            .apply(lambda x: pd.Series({
                "건수": len(x),
                "처리완료율": (x["처리상태"] == "처리완료").mean() * 100,
            }))
            .sort_values("건수", ascending=False))

    best = kpi.groupby("담당자명").agg(
        SLA달성율=("SLA달성율(%)", "mean"),
        평균만족도=("평균만족도", "mean"),
    )
    best["종합점수"] = best["SLA달성율"] * 0.5 + best["평균만족도"] * 10 * 0.5
    top_agent   = best["종합점수"].idxmax()
    top_sla     = best.loc[top_agent, "SLA달성율"]
    top_sat     = best.loc[top_agent, "평균만족도"]

    eff_ch = full.groupby("문의채널").agg(
        처리시간=("처리시간(분)", "mean"),
        만족도=("고객만족도", "mean"),
    ).dropna()
    eff_ch["효율점수"] = (1 / (eff_ch["처리시간"] + 1)) * eff_ch["만족도"]
    best_ch = eff_ch["효율점수"].idxmax()

    st.subheader("🔴 즉시 개선 필요")
    danger_sla   = sla_t[sla_t < 70].sort_values()
    danger_reinq = reinq_t[reinq_t > 15].sort_values(ascending=False)

    if not danger_sla.empty:
        for inq_type, rate in danger_sla.items():
            st.error(f"**SLA 위험 — {inq_type}** : SLA 달성율 {rate:.1f}% (목표 80% 미달)\n\n"
                     f"→ 처리 프로세스 점검 및 담당자 역량 강화 필요")
    else:
        st.success("SLA 위험 유형 없음 (전 유형 70% 이상)")

    if not danger_reinq.empty:
        for inq_type, rate in danger_reinq.items():
            st.error(f"**재문의 과다 — {inq_type}** : 재문의율 {rate:.1f}% (기준 15% 초과)\n\n"
                     f"→ 1차 응대 완결율 개선, FAQ/스크립트 보강 검토")
    else:
        st.success("재문의 과다 유형 없음 (전 유형 15% 이하)")

    st.markdown("---")
    st.subheader("🟡 모니터링 필요")

    low_sat_ch = sat_ch[sat_ch < 3.5].sort_values()
    if not low_sat_ch.empty:
        for ch, score in low_sat_ch.items():
            st.warning(f"**만족도 저하 채널 — {ch}** : 평균 {score:.2f}점 (기준 3.5점 미만)\n\n"
                       f"→ {ch} 채널 응대 속도·품질 점검, 고객 피드백 수집 강화")
    else:
        st.success("전 채널 만족도 3.5점 이상 (정상)")

    peak_row  = peak.iloc[0]
    peak_time = peak.index[0]
    if peak_row["처리완료율"] < 65:
        st.warning(f"**피크 시간대 처리율 저하 — {peak_time}** : "
                   f"문의 집중 시간대(일일 {peak_row['건수']:.0f}건), "
                   f"처리완료율 {peak_row['처리완료율']:.1f}%\n\n"
                   f"→ 해당 시간대 인력 추가 배치 또는 자동 응대(챗봇) 도입 검토")

    st.markdown("---")
    st.subheader("🟢 잘하고 있는 점 & 확대 검토")

    st.success(f"**우수 상담원 — {top_agent}** : SLA 달성율 {top_sla:.1f}%, 평균만족도 {top_sat:.2f}점\n\n"
               f"→ 응대 사례 팀 내 공유, 멘토링 제도 활용 권장")

    best_ch_time = eff_ch.loc[best_ch, "처리시간"]
    best_ch_sat  = eff_ch.loc[best_ch, "만족도"]
    st.success(f"**효율 채널 — {best_ch}** : 평균 처리시간 {best_ch_time:.0f}분, "
               f"만족도 {best_ch_sat:.2f}점\n\n"
               f"→ {best_ch} 채널 비중 확대 및 타 채널 운영 방식 벤치마킹")

    st.markdown("---")
    st.subheader("📌 고객 세그먼트 이탈 위험")
    risk_hi    = cust[cust["이탈위험도"] == "높음"]
    risk_grade = risk_hi["고객등급"].value_counts()
    col5_l, col5_r = st.columns(2)
    with col5_l:
        st.metric("이탈 위험 고객 수",   f"{len(risk_hi):,}명",
                  delta=f"전체 {len(risk_hi)/len(cust)*100:.1f}%", delta_color="inverse")
    with col5_r:
        if "VIP" in risk_grade or "GOLD" in risk_grade:
            vip_gold = risk_grade.get("VIP", 0) + risk_grade.get("GOLD", 0)
            st.metric("VIP+GOLD 이탈 위험", f"{vip_gold}명",
                      delta="우선 관리 대상", delta_color="inverse")

    fig_risk = px.bar(risk_grade.reset_index().rename(columns={"고객등급":"등급","count":"명수"}),
                      x="등급", y="명수", color="등급",
                      color_discrete_sequence=[SC_DANGER, SC_WARNING, SC_BLUE, SC_LIGHT],
                      labels={"등급":"고객등급","명수":"이탈위험 고객 수"})
    cl(fig_risk, height=260, showlegend=False)
    st.plotly_chart(fig_risk, width="stretch")
    st.caption("→ VIP/GOLD 이탈 위험 고객 대상 선제적 CS 아웃바운드 권장")

# ════════════════════════════════════════════════════════════════
# 탭 6 — AI 대화
# ════════════════════════════════════════════════════════════════
with tab6:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{SC_BLUE},{SC_DARK});
                padding:16px 24px;border-radius:12px;margin-bottom:16px">
      <div style="color:#fff;font-size:1.1rem;font-weight:700">🤖 AI 데이터 분석 대화</div>
      <div style="color:{SC_PALE};font-size:0.82rem;margin-top:4px">
        현재 필터가 적용된 데이터를 기반으로 질문하세요 (gemini-flash-lite-latest)
      </div>
    </div>""", unsafe_allow_html=True)

    total_cnt = len(df)
    completed_rate = (df["처리상태"] == "처리완료").mean() * 100 if total_cnt else 0
    sla_base2 = df[df["SLA준수"] != "미결"]
    sla_rate_ctx = (sla_base2["SLA준수"] == "Y").mean() * 100 if len(sla_base2) else 0
    avg_sat_ctx = df["고객만족도"].mean()
    reinq_rate_ctx = (df["처리상태"] == "재문의").mean() * 100 if total_cnt else 0

    type_top5   = df["문의유형"].value_counts().head(5).to_string()
    region_ctx  = df["지역"].value_counts().to_string()
    ch_sat_ctx  = df.groupby("문의채널")["고객만족도"].mean().round(2).to_string()
    kpi_summary = kpi.groupby("담당자명").agg(
        SLA달성율=("SLA달성율(%)", "mean"),
        평균만족도=("평균만족도", "mean"),
        목표달성율=("목표달성율(%)", "mean"),
    ).round(1).to_string()
    risk_cnt = len(cust[cust["이탈위험도"] == "높음"])

    data_context = f"""=== 현재 필터 적용 데이터 요약 ===
총 문의 건수: {total_cnt:,}건
처리완료율: {completed_rate:.1f}%
SLA 달성율: {sla_rate_ctx:.1f}%
평균 고객만족도: {avg_sat_ctx:.2f}점
재문의율: {reinq_rate_ctx:.1f}%
이탈위험 고객 수: {risk_cnt:,}명

[문의유형별 건수 TOP5]
{type_top5}

[지역별 문의 건수]
{region_ctx}

[채널별 평균 만족도]
{ch_sat_ctx}

[담당자별 KPI (평균)]
{kpi_summary}
"""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg["parts"][0])

    user_input = st.chat_input("데이터에 대해 질문하세요...")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                try:
                    model = genai.GenerativeModel(
                        "gemini-flash-lite-latest",
                        system_instruction=(
                            "당신은 삼천리 CS 고객문의 데이터 분석 전문가입니다. "
                            "아래 데이터를 기반으로 한국어로 간결하고 정확하게 답변하세요.\n\n"
                            + data_context
                        ),
                    )
                    chat = model.start_chat(history=st.session_state.chat_history)
                    response = chat.send_message(user_input)
                    answer = response.text
                    st.markdown(answer)

                    st.session_state.chat_history.append({"role": "user",  "parts": [user_input]})
                    st.session_state.chat_history.append({"role": "model", "parts": [answer]})

                except Exception as e:
                    st.error(f"오류 발생: {e}")

    if st.session_state.chat_history:
        if st.button("대화 초기화"):
            st.session_state.chat_history = []
            st.rerun()
