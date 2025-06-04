import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
file_path = "~/Downloads/chaos01.csv"  # Replace with your file path
data = pd.read_csv(file_path)
# Ensure columns are named correctly
data.columns = ['Time', 'Counts', 'isGate']

# Calculate velocity (rate of change of Counts with respect to Time)
data['Velocity'] = np.gradient(data['Counts'], data['Time'])

# Identify rows where a revolution starts
# Assuming `isGate` = 1 indicates the start of a new revolution
revolutions = data[data['isGate'] == 1].index

if len(revolutions) < 2:
    raise ValueError("Not enough revolutions detected to generate a Poincaré plot.")

# Extract velocity and position at each revolution
poincare_data = pd.DataFrame({
    "Position": data.loc[revolutions, 'Counts'].values,
    "Velocity": data.loc[revolutions, 'Velocity'].values
})

# Create Poincaré plot
plt.figure(figsize=(10, 6))
plt.scatter(poincare_data['Position'], poincare_data['Velocity'], s=10, c='blue', label="Poincaré Points")
plt.title("Poincaré Plot: Velocity vs. Position")
plt.xlabel("Position (Counts)")
plt.ylabel("Velocity")
plt.grid()
plt.legend()
plt.show()
