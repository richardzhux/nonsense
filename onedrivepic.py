import os
import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

def parse_filenames(base_path, start_date_str):
    date_pattern = re.compile(r'^(\d{8})')
    start_date = datetime.strptime(start_date_str, '%Y%m%d')
    start_year, start_month = start_date.year, start_date.month
    date_counts = []

    for year_folder in sorted(os.listdir(base_path)):
        if not year_folder.isdigit() or int(year_folder) < start_year:
            continue
        year_path = os.path.join(base_path, year_folder)
        if not os.path.isdir(year_path):
            continue

        for month_folder in sorted(os.listdir(year_path)):
            if not month_folder.isdigit():
                continue
            year = int(year_folder)
            month = int(month_folder)
            if year == start_year and month < start_month:
                continue

            month_path = os.path.join(year_path, month_folder)
            if not os.path.isdir(month_path):
                continue

            for file in os.listdir(month_path):
                match = date_pattern.match(file)
                if match:
                    date_str = match.group(1)
                    try:
                        date_obj = datetime.strptime(date_str, '%Y%m%d')
                        if date_obj >= start_date:
                            date_counts.append(date_obj.date())
                    except ValueError:
                        continue

    return date_counts

def smooth_series(series, window=5):
    return series.rolling(window=window, center=True, min_periods=1).mean()

def plot_activity(dates):
    df = pd.DataFrame({'date': dates})
    df['date'] = pd.to_datetime(df['date'])

    df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
    df['month'] = df['date'].dt.to_period('M').apply(lambda r: r.start_time)

    time_groups = {
        'Daily': df.groupby('date').size().rename('count').reset_index(),
        'Weekly': df.groupby('week').size().rename('count').reset_index(),
        'Monthly': df.groupby('month').size().rename('count').reset_index()
    }

    for label, data in time_groups.items():
        smooth = smooth_series(data['count'])

        plt.figure(figsize=(12, 4))
        plt.plot(data.iloc[:, 0], data['count'], marker='o', label='Original', alpha=0.6)
        plt.plot(data.iloc[:, 0], smooth, linestyle='-', linewidth=2, color='lightpink', label='Smoothed')
        plt.title(f'{label} Picture Count')
        plt.xlabel(label)
        plt.ylabel('Number of Pictures')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

# ==== INPUT ====
start_date_input = '20220101'  # Change as needed
base_folder = 'media_archive'  # Change to your year/month media root

# ==== RUN ====
dates = parse_filenames(base_folder, start_date_input)
plot_activity(dates)
