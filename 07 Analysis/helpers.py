"""Helper columns for 07 Analysis. Does not change the row count or any cleaned column."""
import numpy as np
import pandas as pd

def add_helpers(df):
    n = len(df)
    st = df["Booking_Status"]
    df["Bookings"] = 1
    df["Cust_Cancelled"] = (st == "Canceled by Customer").astype(int)
    df["Driver_Cancelled"] = (st == "Canceled by Driver").astype(int)
    df["Not_Found"] = (st == "Driver Not Found").astype(int)
    df["Failed"] = (df["Is_Completed"] == 0).astype(int)
    df["Quoted_Lost"] = np.where(df["Is_Completed"] == 0, df["Booking_Value"], 0)
    dt = pd.to_datetime(df["Booking_Datetime"])
    df["Date_Label"] = dt.dt.strftime("%Y-%m-%d")
    df["Hour_Label"] = dt.dt.hour.map(lambda h: f"{h:02d}")
    wk = pd.to_datetime(df["Week_Start"]).dt.strftime("%Y-%m-%d")
    df["Week_Label"] = np.where(wk == "2024-07-29", "Week of 2024-07-29 (3 days)", "Week of " + wk)
    df["Payment_Label"] = df["Payment_Method"].fillna("Not completed (no payment)").astype(str)
    df["Cust_Reason"] = np.where(st == "Canceled by Customer", df["Canceled_Rides_by_Customer"].astype(str), "Not a customer cancellation")
    df["Driver_Reason"] = np.where(st == "Canceled by Driver", df["Canceled_Rides_by_Driver"].astype(str), "Not a driver cancellation")
    assert len(df) == n
    return df
