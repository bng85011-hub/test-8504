import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# ── 기준 데이터 ────────────────────────────────────────────────
channels         = ["전화", "이메일", "채팅", "카카오톡", "앱"]
channel_weights  = [0.35, 0.20, 0.25, 0.15, 0.05]

inquiry_types   = ["배송문의", "반품/교환", "결제문의", "상품문의", "계정문의", "서비스불만", "기타"]
type_weights    = [0.28, 0.22, 0.15, 0.14, 0.10, 0.07, 0.04]

statuses        = ["처리완료", "처리중", "대기", "재문의"]
status_weights  = [0.65, 0.18, 0.10, 0.07]

priorities      = ["높음", "보통", "낮음"]
priority_weights = [0.20, 0.55, 0.25]

handlers = ["김민지", "이재원", "박소연", "최현우", "정다은", "한승호", "윤지아", "장현석"]

regions = ["서울", "경기", "부산", "인천", "대구", "광주", "대전", "울산",
           "경남", "경북", "전남", "전북", "충남", "충북", "강원", "제주"]
region_weights = [0.20, 0.25, 0.08, 0.06, 0.05, 0.03, 0.03, 0.02,
                  0.05, 0.04, 0.03, 0.03, 0.04, 0.03, 0.03, 0.03]

# ── SLA 목표 처리시간 (분) ────────────────────────────────────
sla_targets = {
    "배송문의":   20,
    "반품/교환":  60,
    "결제문의":   30,
    "상품문의":   15,
    "계정문의":   40,
    "서비스불만": 60,
    "기타":       20,
}

# ── 문의유형별 처리시간 분포 ──────────────────────────────────
handling_time_params = {
    "배송문의":   (15, 8),
    "반품/교환":  (35, 15),
    "결제문의":   (20, 10),
    "상품문의":   (10, 5),
    "계정문의":   (25, 12),
    "서비스불만": (45, 20),
    "기타":       (12, 6),
}

def get_satisfaction(status, inquiry_type):
    base = {"처리완료": 4.0, "처리중": 3.2, "대기": 2.8, "재문의": 2.5}[status]
    if inquiry_type == "서비스불만":
        base -= 0.5
    return int(np.clip(np.round(np.random.normal(base, 0.8)), 1, 5))

# ── 데이터 생성 ───────────────────────────────────────────────
start_date    = datetime(2024, 1, 1, 9, 0)
end_date      = datetime(2024, 12, 31, 18, 0)
total_minutes = int((end_date - start_date).total_seconds() / 60)

rows = []
for i in range(5000):
    receipt_dt = start_date + timedelta(minutes=random.randint(0, total_minutes))
    channel    = random.choices(channels, channel_weights)[0]
    inq_type   = random.choices(inquiry_types, type_weights)[0]
    status     = random.choices(statuses, status_weights)[0]
    priority   = random.choices(priorities, priority_weights)[0]
    handler    = random.choice(handlers)
    region     = random.choices(regions, region_weights)[0]

    # 처리시간 (처리완료만)
    if status == "처리완료":
        mu, sigma   = handling_time_params[inq_type]
        handling_min = max(1, int(np.random.normal(mu, sigma)))
        satisfaction = get_satisfaction(status, inq_type)
        sla = "Y" if handling_min <= sla_targets[inq_type] else "N"
    else:
        handling_min = None
        satisfaction = None
        sla = "미결"

    rows.append({
        "문의번호":     f"INQ-{2024_0000 + i + 1}",
        "접수일시":     receipt_dt.strftime("%Y-%m-%d %H:%M"),
        "접수월":       receipt_dt.strftime("%Y-%m"),
        "접수요일":     ["월", "화", "수", "목", "금", "토", "일"][receipt_dt.weekday()],
        "접수시간대":   f"{receipt_dt.hour:02d}시",
        "지역":         region,
        "문의채널":     channel,
        "문의유형":     inq_type,
        "우선순위":     priority,
        "처리상태":     status,
        "처리담당자":   handler,
        "처리시간(분)": handling_min,
        "고객만족도":   satisfaction,
        "SLA준수":      sla,
    })

df = pd.DataFrame(rows).sort_values("접수일시").reset_index(drop=True)
df.to_csv("cs_inquiries_large.csv", index=False, encoding="utf-8-sig")
print(f"cs_inquiries_large.csv 생성 완료: {len(df)}행, {len(df.columns)}컬럼")
print("\n[컬럼 목록]")
print(list(df.columns))
print("\n[SLA준수 분포]")
print(df["SLA준수"].value_counts())
print("\n[지역 분포 상위 5]")
print(df["지역"].value_counts().head(5))
print("\n[샘플 3행]")
print(df.head(3).to_string())
