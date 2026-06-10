import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

categories = {
    "전자제품": ["노트북", "스마트폰", "태블릿", "이어폰", "스마트워치"],
    "의류": ["티셔츠", "청바지", "원피스", "재킷", "운동복"],
    "식품": ["과자", "음료", "건강식품", "커피", "라면"],
    "가구": ["책상", "의자", "소파", "침대", "책장"],
    "스포츠": ["운동화", "헬멧", "요가매트", "덤벨", "텐트"],
}

unit_prices = {
    "노트북": 1200000, "스마트폰": 900000, "태블릿": 650000, "이어폰": 180000, "스마트워치": 350000,
    "티셔츠": 25000, "청바지": 55000, "원피스": 65000, "재킷": 120000, "운동복": 45000,
    "과자": 3500, "음료": 2000, "건강식품": 45000, "커피": 15000, "라면": 4500,
    "책상": 280000, "의자": 150000, "소파": 650000, "침대": 800000, "책장": 200000,
    "운동화": 95000, "헬멧": 75000, "요가매트": 35000, "덤벨": 50000, "텐트": 250000,
}

regions = ["서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산"]
sales_reps = ["김민준", "이서연", "박지호", "최수아", "정태양", "한예진", "윤도현", "장나리"]

start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

rows = []
for _ in range(800):
    date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    category = random.choice(list(categories.keys()))
    product = random.choice(categories[category])
    region = random.choice(regions)
    rep = random.choice(sales_reps)
    quantity = random.randint(1, 20)
    base_price = unit_prices[product]
    # 약간의 가격 변동 적용
    price = int(base_price * random.uniform(0.9, 1.1))
    sales = price * quantity

    rows.append({
        "날짜": date.strftime("%Y-%m-%d"),
        "제품명": product,
        "카테고리": category,
        "지역": region,
        "수량": quantity,
        "단가": price,
        "매출액": sales,
        "담당자": rep,
    })

df = pd.DataFrame(rows)
df = df.sort_values("날짜").reset_index(drop=True)
df.to_csv("sample_sales.csv", index=False, encoding="utf-8-sig")
print(f"sample_sales.csv 생성 완료: {len(df)}행")
print(df.head())
