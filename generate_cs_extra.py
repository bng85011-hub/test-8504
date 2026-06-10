"""
기존 2개 파일 포함 총 5개 CSV 구성
  1. cs_inquiries.csv         (기존 - 1,000행)
  2. cs_inquiries_large.csv   (기존 - 5,000행)
  3. cs_agents.csv            (상담원 마스터)
  4. cs_customers.csv         (고객 마스터)
  5. cs_kpi_monthly.csv       (월별 팀/개인 KPI)
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(99)
np.random.seed(99)

# ── 공통 기준값 ────────────────────────────────────────────────
HANDLERS = ["김민지", "이재원", "박소연", "최현우", "정다은", "한승호", "윤지아", "장현석"]
TEAMS    = {"1팀": ["김민지", "이재원", "박소연"],
            "2팀": ["최현우", "정다은"],
            "3팀": ["한승호", "윤지아", "장현석"]}
HANDLER_TEAM = {h: t for t, members in TEAMS.items() for h in members}

# ════════════════════════════════════════════════════════════════
# 3. cs_agents.csv  — 상담원 마스터
# ════════════════════════════════════════════════════════════════
ranks    = ["팀장", "선임", "주임", "사원"]
ranks_by = {
    "김민지": "팀장", "이재원": "선임", "박소연": "선임",
    "최현우": "팀장", "정다은": "주임",
    "한승호": "팀장", "윤지아": "주임", "장현석": "사원",
}
work_types = ["주간", "주간", "주간", "순환"]  # 가중치

agent_rows = []
for handler in HANDLERS:
    join_year  = random.randint(2018, 2023)
    join_month = random.randint(1, 12)
    join_day   = random.randint(1, 28)
    join_date  = f"{join_year}-{join_month:02d}-{join_day:02d}"

    agent_rows.append({
        "담당자명":    handler,
        "팀":          HANDLER_TEAM[handler],
        "직급":        ranks_by[handler],
        "입사일":      join_date,
        "근무형태":    random.choice(work_types),
        "월목표건수":  random.choice([80, 90, 100, 110]),
        "전담채널":    random.choice(["전화", "채팅", "이메일", "전체"]),
        "자격증보유":  random.choice(["Y", "N"]),
    })

df_agents = pd.DataFrame(agent_rows)
df_agents.to_csv("cs_agents.csv", index=False, encoding="utf-8-sig")
print(f"cs_agents.csv 생성 완료: {len(df_agents)}행")
print(df_agents.to_string(index=False))


# ════════════════════════════════════════════════════════════════
# 4. cs_customers.csv  — 고객 마스터
# ════════════════════════════════════════════════════════════════
grades         = ["VIP", "GOLD", "SILVER", "일반"]
grade_weights  = [0.05, 0.15, 0.30, 0.50]
genders        = ["남", "여"]
age_groups     = ["10대", "20대", "30대", "40대", "50대", "60대 이상"]
age_weights    = [0.05, 0.20, 0.25, 0.25, 0.15, 0.10]
regions        = ["서울", "경기", "부산", "인천", "대구", "광주", "대전", "울산",
                  "경남", "경북", "전남", "전북", "충남", "충북", "강원", "제주"]
region_weights = [0.20, 0.25, 0.08, 0.06, 0.05, 0.03, 0.03, 0.02,
                  0.05, 0.04, 0.03, 0.03, 0.04, 0.03, 0.03, 0.03]

cust_rows = []
for i in range(2000):
    grade = random.choices(grades, grade_weights)[0]
    join_dt = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1460))
    last_contact = join_dt + timedelta(days=random.randint(1, 365))

    # 등급별 누적문의 수 분포
    inq_base = {"VIP": (20, 10), "GOLD": (12, 6), "SILVER": (6, 4), "일반": (3, 2)}[grade]
    total_inq = max(1, int(np.random.normal(*inq_base)))

    cust_rows.append({
        "고객ID":       f"CUST-{10000 + i + 1}",
        "고객등급":     grade,
        "성별":         random.choice(genders),
        "연령대":       random.choices(age_groups, age_weights)[0],
        "지역":         random.choices(regions, region_weights)[0],
        "가입일":       join_dt.strftime("%Y-%m-%d"),
        "최근문의일":   last_contact.strftime("%Y-%m-%d"),
        "누적문의수":   total_inq,
        "마케팅수신동의": random.choice(["Y", "N"]),
        "이탈위험도":   random.choices(["높음", "보통", "낮음"], [0.15, 0.35, 0.50])[0],
    })

df_customers = pd.DataFrame(cust_rows)
df_customers.to_csv("cs_customers.csv", index=False, encoding="utf-8-sig")
print(f"\ncs_customers.csv 생성 완료: {len(df_customers)}행")
print(df_customers.head(3).to_string(index=False))


# ════════════════════════════════════════════════════════════════
# 5. cs_kpi_monthly.csv  — 월별 개인 KPI
# ════════════════════════════════════════════════════════════════
months = [f"2024-{m:02d}" for m in range(1, 13)]

kpi_rows = []
for month in months:
    for handler in HANDLERS:
        target      = random.choice([80, 90, 100, 110])
        actual      = max(30, int(np.random.normal(target * 0.97, 10)))
        completed   = int(actual * random.uniform(0.60, 0.80))
        avg_time    = round(random.uniform(18, 38), 1)
        sla_rate    = round(random.uniform(0.60, 0.95) * 100, 1)
        avg_sat     = round(random.uniform(3.2, 4.8), 2)
        absence_day = random.choices([0, 1, 2], [0.75, 0.18, 0.07])[0]

        kpi_rows.append({
            "연월":         month,
            "팀":           HANDLER_TEAM[handler],
            "담당자명":     handler,
            "목표건수":     target,
            "실적건수":     actual,
            "처리완료건수": completed,
            "처리완료율(%)": round(completed / actual * 100, 1),
            "목표달성율(%)": round(actual / target * 100, 1),
            "평균처리시간(분)": avg_time,
            "SLA달성율(%)": sla_rate,
            "평균만족도":   avg_sat,
            "결근일수":     absence_day,
        })

df_kpi = pd.DataFrame(kpi_rows)
df_kpi.to_csv("cs_kpi_monthly.csv", index=False, encoding="utf-8-sig")
print(f"\ncs_kpi_monthly.csv 생성 완료: {len(df_kpi)}행 ({len(months)}개월 × {len(HANDLERS)}명)")
print(df_kpi.head(3).to_string(index=False))

print("\n=== 전체 CSV 현황 ===")
import os
for fname in sorted(f for f in os.listdir('.') if f.endswith('.csv')):
    size = os.path.getsize(fname)
    rows = sum(1 for _ in open(fname, encoding='utf-8-sig')) - 1
    print(f"  {fname:<30} {rows:>5,}행  {size/1024:.0f}KB")
