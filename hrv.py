from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time

# Configure WebDriver
service = Service('/Users/rx/Documents/chromedriver/chromedriver')  # Update with your ChromeDriver path
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
driver = webdriver.Chrome(service=service, options=options)

# Define date range
start_date = datetime(2024, 11, 11)
end_date = datetime.now()

# Initialize list to store data
weather_data = []

# Iterate over each date
current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    url = f"https://www.wunderground.com/history/daily/us/il/evanston/KILEVANS56/date/{date_str}"
    driver.get(url)

    # Wait for the page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'lib-city-history-observation'))
        )
    except Exception as e:
        print(f"Error loading page for {date_str}: {e}")
        current_date += timedelta(days=1)
        continue

    # Parse page content
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract summary data
    summary = soup.find('lib-city-history-summary')
    if summary:
        try:
            temp_high = summary.find('span', text='High Temp').find_next('span').text.strip()
            temp_low = summary.find('span', text='Low Temp').find_next('span').text.strip()
            precip = summary.find('span', text='Precipitation').find_next('span').text.strip()
            wind = summary.find('span', text='Wind').find_next('span').text.strip()
            visibility = summary.find('span', text='Visibility').find_next('span').text.strip()
            pressure = summary.find('span', text='Sea Level Pressure').find_next('span').text.strip()
            condition = summary.find('span', text='Conditions').find_next('span').text.strip()
        except AttributeError:
            print(f"Data missing for {date_str}")
            current_date += timedelta(days=1)
            continue

        # Append data to list
        weather_data.append({
            'Date': date_str,
            'High Temp (°C)': temp_high,
            'Low Temp (°C)': temp_low,
            'Precipitation (mm)': precip,
            'Wind (km/h)': wind,
            'Visibility (km)': visibility,
            'Pressure (hPa)': pressure,
            'Condition': condition
        })
        print(f"Data extracted for {date_str}")
    else:
        print(f"No summary data found for {date_str}")

    # Increment date
    current_date += timedelta(days=1)
    time.sleep(1)  # Pause to avoid overwhelming the server

# Close WebDriver
driver.quit()

# Save data to CSV
df = pd.DataFrame(weather_data)
df.to_csv('evanston_weather_data.csv', index=False)
print("Data saved to evanston_weather_data.csv")
