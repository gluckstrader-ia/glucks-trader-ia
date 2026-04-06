from typing import List

import pandas as pd


MONTH_NAMES_PT = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}


def calculate_seasonality(df: pd.DataFrame) -> List[dict]:
    working = df.copy()

    if working.empty:
        return []

    if not isinstance(working.index, pd.DatetimeIndex):
        return []

    monthly = working["close"].resample("M").agg(["first", "last"]).dropna()

    if monthly.empty:
        return []

    monthly["ret"] = ((monthly["last"] / monthly["first"]) - 1.0) * 100
    monthly["month"] = monthly.index.month

    result = (
        monthly.groupby("month")["ret"]
        .median()
        .reset_index()
        .sort_values("month")
    )

    items = []
    for _, row in result.iterrows():
        month_num = int(row["month"])
        items.append(
            {
                "month": MONTH_NAMES_PT.get(month_num, str(month_num)),
                "value": round(float(row["ret"]), 2),
            }
        )

    return items