from pulp import LpVariable, LpProblem, LpMinimize, lpSum, value
import pandas as pd

# Load demand and capacity data
Demanda = pd.read_csv("demanda.csv")
Capacidad = pd.read_csv("capacidad.csv")

# Print column names in the Demanda DataFrame
print("Demanda DataFrame Columns:", Demanda.columns)

# Define the time slots from 6:00 AM to 7:00 PM
time_slots = list(range(7, 20))  # Assuming 15-minute slots for simplicity

# Create a binary variable for each employee, time slot, and state
employees = range(1, 9)
states = ['trabajando', 'pausa_activa', 'Almuerzo', 'nada']

# Create a binary variable for each employee, time slot, and state
x = LpVariable.dicts('x', (employees, time_slots, states), cat='Binary')

# Create the LP problem
prob = LpProblem("Employee_Schedule_Optimization", LpMinimize)

# Replace column names with the correct names in the Demanda DataFrame
demand_column_name = 'demanda'
prob += lpSum(x[e][t]['trabajando'] for e in employees for t in time_slots) - Demanda[demand_column_name].tolist()

# Define the constraints based on the 'fecha_hora' column in the Demanda DataFrame
for t in time_slots:
    prob += lpSum(x[e][t]['trabajando'] for e in employees) >= Demanda.at[t - 6, demand_column_name]

# Additional Constraints
for e in employees:
    for t in time_slots:
        # Constraint: Minimum 1 hour continuous work before break
        if t + 3 in time_slots:
            prob += lpSum(x[e][t + i]['trabajando'] for i in range(4)) >= x[e][t]['trabajando']

        # Constraint: Maximum 2 hours continuous work before break
        if t + 8 in time_slots:
            prob += lpSum(x[e][t + i]['trabajando'] for i in range(9)) <= 2 * x[e][t]['trabajando']


# Solve the problem
prob.solve()

# Create a DataFrame to store the schedule
schedule_df = pd.DataFrame(index=time_slots, columns=employees, data="")

# Populate the DataFrame with the optimized schedule
for t in time_slots:
    for e in employees:
        for s in states:
            if x[e][t][s].value() == 1:
                schedule_df.at[t, e] = s

# Export the DataFrame to a CSV file
schedule_df.to_csv("optimized_horario.csv", index_label="fecha_hora")