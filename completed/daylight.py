import numpy as np
import matplotlib.pyplot as plt

# Define function: Daylight duration
def daylight_duration(latitude, day_of_year):
    delta = 23.44 * np.sin(2 * np.pi * (day_of_year - 81) / 365)  # Solar declination angle
    phi_rad = np.radians(latitude)  # Convert latitude to radians
    delta_rad = np.radians(delta)  # Convert declination to radians
    cos_h = -np.tan(phi_rad) * np.tan(delta_rad)  # Cosine of hour angle at sunrise/sunset
    cos_h = np.clip(cos_h, -1, 1)  # Clip to avoid numerical errors
    daylight_hours = 24 * (1 - (1 / np.pi) * np.arccos(cos_h))  # Compute daylight hours
    return daylight_hours

# Latitude and day-of-year grid
latitudes = np.linspace(-90, 90, 181)  # Latitude range from -90 to 90 degrees
days = np.arange(1, 366)               # Days of the year (1 to 365)
lat_grid, day_grid = np.meshgrid(latitudes, days)  # Create a grid for latitude and day

# Calculate daylight hours
daylight = daylight_duration(lat_grid, day_grid)

# Plot the graph with contours every 2 hours
plt.figure(figsize=(12, 6))
contour = plt.contour(latitudes, days, daylight, levels=np.arange(0, 25, 2), colors='black', linestyles='dashed')
plt.clabel(contour, inline=True, fontsize=8, fmt='%d hrs')  # Add labels to contours
contourf = plt.contourf(latitudes, days, daylight, levels=np.arange(0, 25, 2), cmap='rainbow', alpha=0.8)
plt.colorbar(contourf, label='Daylight Hours')
plt.xlabel('Latitude (°)')
plt.ylabel('Day of Year')
plt.title('Daylight Hours as a Function of Latitude and Day of Year (Contours Every 2 Hours)')
plt.show()
