from datetime import datetime
from typing import cast

import altair as alt
import pandas as pd
import streamlit as st


def load_busyness() -> tuple[pd.DataFrame, datetime]:
    """return df indexed by time, column for num_people"""
    df = pd.read_csv("busyness.csv", names=["time", "num_people"], parse_dates=["time"])
    last_update = df["time"].iloc[-1]
    df = df.set_index("time").resample("10min").mean()
    return cast(pd.DataFrame, df), last_update


def convert_datetime_column_to_weekday_and_time(series: pd.Series) -> pd.Series:
    """convert from timestamp series to weekday+time, like "0 Mon 12:30" """
    return pd.Series(
        # need this hack because it sorts by x-axis :/
        series.apply(lambda s: str(s.dayofweek))
        + " "
        + series.apply(lambda s: s.day_name()[:3])
        + " "
        + series.apply(lambda s: str(s.time()).removesuffix(":00"))
    )


def split_df_by_day_of_week_and_time(df: pd.DataFrame) -> pd.DataFrame:
    """input: time->num_people
    output: weekday+time -> one column per week"""
    df = df.copy()
    df["week_num"] = df.index.isocalendar().week  # type: ignore
    df["weekday_time"] = convert_datetime_column_to_weekday_and_time(df.index.to_series())
    weeks = df.week_num.unique()  # all week numbers

    results = []
    for week in weeks:
        df_one_week = df[df.week_num == week]
        df_week_grouped = df_one_week.groupby("weekday_time")[["num_people"]].mean()
        df_week_grouped = df_week_grouped.rename(columns={"num_people": f"week_{week}"})
        results.append(df_week_grouped)
    result = pd.concat(results, axis=1)
    result.sort_index(inplace=True)
    return result


def make_spread_df(one_col_per_week_df) -> pd.DataFrame:
    """input: df indexed by weekday+time, one column per week
    output: df indexed by weekday+time, columns for mean, std, hi, lo
    """
    mean = one_col_per_week_df.mean(axis=1)
    std = one_col_per_week_df.std(axis=1)
    hi = mean + std
    lo = mean - std
    spread_df = pd.concat([mean, std, hi, lo], keys=["mean", "std", "hi", "lo"], axis=1)
    return spread_df


### state

full_df, last_update = load_busyness()
one_col_per_week_df = split_df_by_day_of_week_and_time(full_df)
weekday_spread_df = make_spread_df(one_col_per_week_df)

now = datetime.now()
today = now.today().date()
today_dayname = today.strftime("%a")  # 3 char str
# data for today so far
today_df = full_df[full_df.index.date == today]
today_df.index = convert_datetime_column_to_weekday_and_time(today_df.index.to_series())

# chart with vertical rule for current time
now_df = pd.DataFrame([dict(time=today_df.index[-1])])
now_chart = alt.Chart(now_df).mark_rule(opacity=0.2).encode(x="time")


### display


"# how busy is vital?"

st.write(f"now: {now:%a %m-%d %H:%M}")
st.write(f"last update: {last_update:%m-%d %H:%M:%S}")


"## right now"

historical_today = weekday_spread_df[lambda df: df.index.str.contains(today_dayname)]
historical_and_current_today = historical_today.join(
    today_df.rename(columns=dict(num_people="today"))
)

# st.line_chart(historical_today)
x = historical_and_current_today.reset_index(names="time")
base = alt.Chart(x).encode(x="time")
chart = (
    base.mark_bar().encode(y="lo", y2="hi")
    + base.mark_line().encode(y="mean")
    + base.mark_line(opacity=1).encode(y="today")
).configure_mark(opacity=0.3)
st.altair_chart(chart + now_chart, use_container_width=True)


"## weekday averages"

# st.line_chart(spread_df)
x = weekday_spread_df.reset_index(names="time")
base = alt.Chart(x).encode(x="time")
chart = (
    base.mark_bar().encode(y="lo", y2="hi") + base.mark_line().encode(y="mean")
).configure_mark(opacity=0.3)

st.altair_chart(chart + now_chart, use_container_width=True)
