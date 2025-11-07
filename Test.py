import numpy as np
import matplotlib.pyplot as plt

# Constants
c = 299_792_458  # Speed of light in m/s
efficiency = 0.40  # Engine efficiency
backup_multiplier = 1.5  # Backup energy multiplier for safety
joules_per_kg_antimatter = 9 * 10**16  # Energy per kg of antimatter (E=mc^2)
m_ship = 70_000  # Ship mass without fuel in kg
total_time = 99.9  # Total time in seconds
v_final = 0.999 * c  # Final velocity in m/s

# Step 1: Calculate constant coordinate acceleration (a)
a = v_final / total_time  # Constant acceleration in m/s^2

# Time steps
dt = 0.1  # Time step in seconds
time_array = np.arange(0, total_time + dt, dt)
n_steps = len(time_array)

# Initialize arrays
velocity = np.zeros(n_steps)
gamma = np.zeros(n_steps)
mass = np.zeros(n_steps)
force = np.zeros(n_steps)
power = np.zeros(n_steps)
fuel_consumption_rate = np.zeros(n_steps)

# Initial conditions
velocity[0] = 0
gamma[0] = 1  # Lorentz factor at rest
mass[0] = m_ship  # Start with ship mass; fuel mass will be added later

# Placeholder for total fuel mass
total_fuel_mass = 0

# Function to compute the trajectory
def compute_trajectory(m_initial_fuel):
    mass = np.zeros(n_steps)
    mass[0] = m_ship + m_initial_fuel  # Total initial mass including fuel
    total_fuel_consumed = 0

    for i in range(1, n_steps):
        # Update velocity with constant acceleration
        velocity[i] = velocity[i-1] + a * dt
        if velocity[i] >= v_final:
            velocity[i] = v_final
            velocity[i+1:] = v_final
            gamma[i+1:] = 1 / np.sqrt(1 - (v_final / c) ** 2)
            mass[i+1:] = mass[i-1]
            force[i+1:] = force[i-1]
            power[i+1:] = power[i-1]
            fuel_consumption_rate[i+1:] = 0
            break

        # Update gamma
        gamma[i] = 1 / np.sqrt(1 - (velocity[i] / c) ** 2)

        # Calculate force required: F = gamma^3 * m * a
        force[i] = gamma[i] ** 3 * mass[i-1] * a

        # Power required: P = F * v
        power[i] = force[i] * velocity[i]

        # Considering efficiency, calculate power input
        power_input = power[i] / efficiency

        # Fuel mass consumed in this time step
        fuel_mass_consumed = power_input * dt / joules_per_kg_antimatter

        # Update total fuel consumed
        total_fuel_consumed += fuel_mass_consumed

        # Update mass
        mass[i] = mass[i-1] - fuel_mass_consumed

        # If mass drops below ship mass, not enough fuel
        if mass[i] < m_ship:
            return False, total_fuel_consumed

    return True, total_fuel_consumed

# Iteratively find the required initial fuel mass
fuel_mass_guess = 1e6  # Initial guess in kg
tolerance = 1e-3  # Tolerance for convergence
max_iterations = 100

for iteration in range(max_iterations):
    success, total_fuel_consumed = compute_trajectory(fuel_mass_guess)
    if success:
        # Check if total_fuel_consumed is close to fuel_mass_guess
        if abs(total_fuel_consumed - fuel_mass_guess) < tolerance:
            break
        else:
            # Adjust fuel_mass_guess
            fuel_mass_guess = total_fuel_consumed
    else:
        # Not enough fuel, increase guess
        fuel_mass_guess *= 1.5  # Increase by a factor for faster convergence

# Apply backup multiplier
required_fuel_mass = total_fuel_consumed * backup_multiplier

# Run the simulation one more time with the final fuel mass to get data for plotting
compute_trajectory(required_fuel_mass)

# Convert units for plotting
velocity_fraction = velocity / c
mass_tons = mass / 1e3
power_TW = power / 1e12
force_MN = force / 1e6
fuel_consumption_rate_kg_s = fuel_consumption_rate

# Plotting the results
plt.figure(figsize=(12, 10))

plt.subplot(2, 2, 1)
plt.plot(time_array, velocity_fraction)
plt.xlabel('Time (s)')
plt.ylabel('Velocity (fraction of c)')
plt.title('Velocity vs Time (Constant Coordinate Acceleration)')
plt.grid(True)

plt.subplot(2, 2, 2)
plt.plot(time_array, mass_tons)
plt.xlabel('Time (s)')
plt.ylabel('Mass (tons)')
plt.title('Mass vs Time')
plt.grid(True)

plt.subplot(2, 2, 3)
plt.plot(time_array, power_TW)
plt.xlabel('Time (s)')
plt.ylabel('Power (TW)')
plt.title('Power vs Time')
plt.grid(True)

plt.subplot(2, 2, 4)
plt.plot(time_array, force_MN)
plt.xlabel('Time (s)')
plt.ylabel('Force (MN)')
plt.title('Force vs Time')
plt.grid(True)

plt.tight_layout()
plt.show()

# Output the required fuel mass
required_fuel_tons = required_fuel_mass / 1e3
print(f"Required fuel mass: {required_fuel_tons:.2f} tons")
