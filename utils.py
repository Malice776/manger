# utils.py
import pandas as pd
from datetime import datetime




def build_month_calendar(year, month):
    # renvoie DataFrame avec une grille du mois
    first = pd.Timestamp(year=year, month=month, day=1)
    start = first - pd.Timedelta(days=first.weekday())
    days = [start + pd.Timedelta(days=i) for i in range(6*7)]
    weeks = []
    for w in range(6):
        week = days[w*7:(w+1)*7]
        weeks.append(week)
    return weeks




def iso_date(d):
    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d).date().isoformat()
        except Exception:
            return d
    if hasattr(d, 'isoformat'):
        return d.isoformat()
    return str(d)