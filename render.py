from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

# TODO:
# draw average for the current day of week (plus the next day maybe)
# read streamlit docs on how to explore plots (pan, zoom)


def split_df_by_day_of_week_and_time(df):
    # df = df.resample("5T").mean()
    df = df.copy()
    df["day_of_week"] = df.index.dayofweek
    df["day_name"] = df.index.day_name()
    df["time_of_day"] = df.index.time

    # df_grouped = df.groupby(['day_of_week', 'time_of_day']).mean()
    weeks = df.index.isocalendar().week.unique()
    result = pd.DataFrame()
    for week in weeks:
        df_week = df[df.index.isocalendar().week == week]
        df_week_grouped = df_week.groupby(["day_of_week", "day_name", "time_of_day"]).mean()
        df_week_grouped = df_week_grouped.rename(columns={"num_people": f"week_{week}"})
        result = pd.concat([result, df_week_grouped], axis=1)
    result.sort_index(inplace=True)

    # index by strings like "Monday 00:05:00"
    idx = result.index.to_frame()
    result.set_index(
        idx.day_of_week.apply(str) + " " + idx.day_name + " " + idx.time_of_day.apply(str),
        inplace=True,
    )
    return result


def load_busyness():
    df = pd.read_csv("busyness.csv", names=["time", "num_people"], parse_dates=["time"])
    df = df.set_index("time").resample("5min").mean()
    return df


"# how busy is vital?"

df = load_busyness()

now = datetime.now()
dt_24h_ago = now - timedelta(days=1)

"## last 24h"
last_24h_df = df[df.index > dt_24h_ago]  # type: ignore
st.line_chart(last_24h_df)

"## weekday averages"
one_col_per_week = split_df_by_day_of_week_and_time(df)
st.line_chart(one_col_per_week)

"## weekday averages: mean, stdev"
mean = one_col_per_week.mean(axis=1).rename("mean")
std = one_col_per_week.std(axis=1).rename("std")
x = pd.concat([mean, std], axis=1)
x["hi"] = x["mean"] + x["std"]
x["lo"] = x["mean"] - x["std"]

# TODO: not working yet...
base = alt.Chart(x.reset_index()).encode(x="index")
chart = base.mark_line().encode(y="mean") + base.mark_line().encode(y="hi")
st.altair_chart(chart, use_container_width=True)

# "## full data"
# st.write(df)

# "## all time"
# st.line_chart(df.resample("1H").mean())
