import folium, math, os, webbrowser, pytz
import numpy as np
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from astral import LocationInfo
from astral.sun import sun
from geopy.distance import geodesic
from geopy.point import Point

# Constants
RAINBOW_ANGLE_DEG = 42  # Precise rainbow cone angle (in degrees)
EARTH_RADIUS = 6371008.8  # Earth radius in meters, more precise value

# Coordinates for six fountains
fountains = [
    (42.054788, -87.672590),
    (42.054573, -87.672849),
    (42.054710, -87.673108),
    (42.054945, -87.673079),
    (42.054963, -87.672736)
] # (42.054756, -87.672833) is the center

# Function to add two lines representing the 2D boundary of the rainbow visibility cone
def add_rainbow_boundary_to_map_all(fountain_lat, fountain_lon, sun_azimuth, angle_deg, map_object):
    # Define the distance for the projection of the rainbow cone boundary (e.g., 100 meters)
    boundary_length_m = 120
    
    # Calculate two lines at the 42-degree boundary (left and right of the Sun's azimuth)
    for angle_offset in [-angle_deg, angle_deg]:
        angle_rad = math.radians(sun_azimuth + angle_offset)
        
        # Calculate the lat/lon change for this boundary
        d_lat = (boundary_length_m / EARTH_RADIUS) * (180 / math.pi)
        d_lon = (boundary_length_m / (EARTH_RADIUS * math.cos(math.radians(fountain_lat)))) * (180 / math.pi)
        
        # Corrected: Latitude uses cos, Longitude uses sin
        boundary_lat = fountain_lat + d_lat * math.cos(angle_rad)
        boundary_lon = fountain_lon + d_lon * math.sin(angle_rad)
        
        # Add a line from the fountain to the boundary with higher weight and opacity to ensure visibility
        folium.PolyLine([(fountain_lat, fountain_lon), (boundary_lat, boundary_lon)],
                        color='blue', weight=2.5, opacity=0.25).add_to(map_object)
    
centrale_lat, centrale_lon = 42.054756, -87.672833


def add_rainbow_boundary_to_map_centrale(centrale_lat, centrale_lon, sun_azimuth, angle_deg, map_object):
    # Define the distance for the projection of the rainbow cone boundary (e.g., 100 meters)
    boundary_length_m = 500
    
    # Calculate two lines at the 42-degree boundary (left and right of the Sun's azimuth)
    for angle_offset in [-angle_deg, angle_deg]:
        angle_rad = math.radians(sun_azimuth + angle_offset)
        
        # Calculate the lat/lon change for this boundary
        d_lat = (boundary_length_m / EARTH_RADIUS) * (180 / math.pi)
        d_lon = (boundary_length_m / (EARTH_RADIUS * math.cos(math.radians(centrale_lat)))) * (180 / math.pi)
        
        # Corrected: Latitude uses cos, Longitude uses sin
        boundary_lat = centrale_lat + d_lat * math.cos(angle_rad)
        boundary_lon = centrale_lon + d_lon * math.sin(angle_rad)
        
        # Add a line from the fountain to the boundary with higher weight and opacity to ensure visibility
        folium.PolyLine([(centrale_lat, centrale_lon), (boundary_lat, boundary_lon)],
                        color='lightpink', weight=77, opacity=0.55).add_to(map_object)



# Function to add a line representing the sunlight direction
def add_sunlight_direction(fountain_lat, fountain_lon, sun_azimuth, map_object):
    # Define the length of the line (e.g., 100 meters for visualization)
    line_length_m = 500
    
    # Corrected calculation for azimuth direction (azimuth is measured clockwise from north)
    azimuth_rad = math.radians(sun_azimuth)
    
    # Calculate the end point of the line (in the direction of the Sun's azimuth)
    d_lat = (line_length_m / EARTH_RADIUS) * (180 / math.pi)
    d_lon = (line_length_m / (EARTH_RADIUS * math.cos(math.radians(fountain_lat)))) * (180 / math.pi)
    
    end_lat = fountain_lat + d_lat * math.cos(azimuth_rad)
    end_lon = fountain_lon + d_lon * math.sin(azimuth_rad)
    
    # Add the line to the map
    folium.PolyLine([(fountain_lat, fountain_lon), (end_lat, end_lon)], color='yellow', weight=5, opacity=1).add_to(map_object)

# Function to get the Sun's position using pysolar
def get_sun_position(lat, lon, date_time):
    import pysolar.solar
    altitude = pysolar.solar.get_altitude(lat, lon, date_time)
    azimuth = pysolar.solar.get_azimuth(lat, lon, date_time)
    return altitude, azimuth

# Function to get the sunrise and sunset times using astral
def get_sunrise_sunset(lat, lon, date_time):
    location = LocationInfo(latitude=lat, longitude=lon)
    sun_info = sun(location.observer, date=date_time)
    sunrise = sun_info['sunrise'].astimezone(pytz.timezone('America/Chicago'))
    sunset = sun_info['sunset'].astimezone(pytz.timezone('America/Chicago'))
    return sunrise, sunset

# Function to create a map for a specific time and save it as an image using Selenium
def create_map_for_time(date_time, filename, driver):
    # Create the map centered at the first fountain
    map_fountain = folium.Map(location=[42.054756, -87.672833], zoom_start=17)
    
    # Get the Sun's position (altitude and azimuth)
    sun_altitude, sun_azimuth = get_sun_position(42.054756, -87.672833, date_time)
    
    # Get sunrise and sunset times
    sunrise, sunset = get_sunrise_sunset(42.054756, -87.672833, date_time)

    # Format the current time, sunrise, and sunset in 'yyyy.mm.dd.hhmm' format
    current_time_str = date_time.strftime("%Y.%m.%d.%H%M")
    sunrise_str = sunrise.strftime("%Y.%m.%d.%H%M")
    sunset_str = sunset.strftime("%Y.%m.%d.%H%M")

    # Output the current time, sun altitude, azimuth, and sunrise/sunset times to the terminal
    print(f"{current_time_str}")
    print(f"Sunrise: {sunrise_str}, Sunset: {sunset_str}")
    print(f"Sun Altitude: {sun_altitude:.2f}°, Sun Azimuth: {sun_azimuth:.2f}°")

    # Only proceed if the Sun's altitude is less than 42 degrees
    if sun_altitude < 42 and sun_altitude > 0:
        print(f"Calculating rainbow visibility... 🌈")

        add_sunlight_direction(42.054756, -87.672833, sun_azimuth, map_fountain)
        add_rainbow_boundary_to_map_centrale(centrale_lat, centrale_lon, sun_azimuth, RAINBOW_ANGLE_DEG, map_fountain)

        """
        # Iterate over all fountains and add their rainbow boundary and sunlight direction
        for fountain_lat, fountain_lon in fountains:
            # Add the rainbow boundary lines (representing the 2D boundary of the rainbow cone)
            # add_rainbow_boundary_to_map(fountain_lat, fountain_lon, sun_azimuth, RAINBOW_ANGLE_DEG, map_fountain)
            add_rainbow_boundary_to_map_all(fountain_lat, fountain_lon, sun_azimuth, RAINBOW_ANGLE_DEG, map_fountain)

            
            # Add the sunlight direction line to the map
        """

    elif sun_altitude > 42:
        print("Rainbow not visible, the Sun is too high!")
        return   # Exit the function immediately
    
    else:
        print("Rainbow not visible, the is sleeping! (below horizon).")
        return

    # Get the folder where the current script is located
    current_folder = os.path.dirname(os.path.abspath(__file__))
    
    # Define the output file paths in the same folder as the script
    map_html = os.path.join(current_folder, f"{filename}.html")
    
    # Save the map as an HTML file
    map_fountain.save(map_html)

    # Automatically open the HTML file in the browser
    webbrowser.open(f"file://{os.path.abspath(map_html)}", new=2)  # Opens in a new browser tab

    # Convert HTML to PNG using Selenium
    driver.get(f"file://{os.path.abspath(map_html)}")
    screenshot_filename = os.path.join(current_folder, f"{filename}.png")
    driver.save_screenshot(screenshot_filename)
    
    return screenshot_filename  # Return the PNG filename

def validate_time_input(time_input):
    """
    Validate and parse time in yyyy.mm.dd.hhmm format.
    Automatically adjusts for input format and forbids dates before October 15, 1582.
    Returns a datetime object if valid. Prints an error message if invalid.
    """
    try:
        # Split the input by '.'
        parts = time_input.split('.')
        
        # Check that we have exactly 4 parts: year, month, day, and hhmm (no extra parts)
        if len(parts) != 4:
            print("Invalid time format. Please use 'yyyy.mm.dd.hhmm'.")
            return None

        year, month, day, time_part = parts
        
        # Validate year, ensure it's between 1582 and 9999
        if not (1582 <= int(year) <= 9999):
            print("Invalid year. The year must be between 1582 and 9999.")
            return None
        
        # Validate and auto-correct month (convert 1 to 01)
        if not (1 <= int(month) <= 12):
            print("Invalid month. The month must be between 1 and 12.")
            return None
        month = month.zfill(2)

        # Validate and auto-correct day (convert 1 to 01)
        if not (1 <= int(day) <= 31):
            print("Invalid day. The day must be between 1 and 31.")
            return None
        day = day.zfill(2)

        # Validate the time part (hhmm should be exactly 4 digits)
        if len(time_part) != 4 or not time_part.isdigit():
            print("Invalid time format. The time must be exactly 4 digits in hhmm format.")
            return None
        hour = int(time_part[:2])
        minute = int(time_part[2:])

        # Ensure hours and minutes are valid
        if not (0 <= hour < 24):
            print("Invalid hour. Hours should be between 0 and 23.")
            return None
        if not (0 <= minute < 60):
            print("Invalid minutes. Minutes should be between 0 and 59.")
            return None

        # Create the formatted date-time string
        formatted_input = f"{year.zfill(4)}-{month}-{day} {time_part[:2]}:{time_part[2:]}"
        
        # Parse the date and time
        time_obj = datetime.strptime(formatted_input, "%Y-%m-%d %H:%M")

        # Ensure the date is after October 15, 1582
        cutoff_date = datetime(1582, 10, 15)
        if time_obj < cutoff_date:
            print("Invalid date. The date must be after October 15, 1582.")
            return None

        return time_obj
    except ValueError:
        print("Invalid date or time. Please check your input.")
        return None


# Main function
def main():
    # Set up Selenium for Chrome (use ChromeDriver)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Provide the path to your ChromeDriver
    driver_path = '/Users/rx/Downloads/chromedriver-mac-arm64/chromedriver'  # Replace with the actual path
    driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)

    while True:
        # Ask the user for input: use current time or input custom time
        choice = input("Enter 'current' for current time, 'custom' to input date and time (format: yyyy.mm.dd.hhmm), or 'q'/'esc' to quit: ").strip().lower()

        if choice in ['q', 'esc']:
            print("Exiting program.")
            break  # Exit the loop and program

        elif choice == 'current':
            # Use the current time to generate the rainbow visibility map
            timezone = pytz.timezone('America/Chicago')
            current_time = datetime.now(timezone)
            create_map_for_time(current_time, f"rainbow_viewline_{current_time}", driver)
            print(f"Map for current time created and opened in browser: rainbow_viewline_{current_time}.html")
        
        elif choice == 'custom':
            # Ask the user for a custom date and time
            custom_date_time_str = input("Enter the date and time (yyyy.mm.dd.hhmm): ").strip()
            
            # Validate and parse the custom date and time
            custom_date_time = validate_time_input(custom_date_time_str)
            
            if custom_date_time:
                # If the validation is successful, generate the map for the custom date and time
                timezone = pytz.timezone('America/Chicago')
                custom_date_time = timezone.localize(custom_date_time)
                create_map_for_time(custom_date_time, f"rainbow_visibility_{custom_date_time_str}", driver)
                print(f"Map for custom time {custom_date_time_str} created and opened in browser.")
            else:
                print("Invalid date/time input. Please try again.")
        
        else:
            print("Invalid input. Please enter 'current', 'custom', or 'q'/'esc' to quit.")
    
    driver.quit()

if __name__ == "__main__":
    main()
