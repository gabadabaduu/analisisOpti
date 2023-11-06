from pulp import LpVariable, LpProblem, LpMinimize, lpSum, value
import pandas as pd

# Load demand and capacity data
Demanda = pd.read_csv("demanda.csv")
Capacidad = pd.read_csv("capacidad.csv")

# Define the time slots from 7:30 AM to 6:30 PM
time_slots = list(range(7, 19))  # Assuming 15-minute slots for simplicity

# Create a binary variable for each employee, time slot, and state
employees = range(1, 9)
states = ['Trabaja', 'Pausa Activa', 'Almuerza', 'Nada']

# Create a binary variable for each employee, time slot, and state
x = LpVariable.dicts('x', (employees, time_slots, states), cat='Binary')

# Create the LP problem
prob = LpProblem("Employee_Schedule_Optimization", LpMinimize)

# Define demand column name based on your dataset
demand_column_name = 'demanda'

# Replace column names with the correct names in the Demanda DataFrame
for e in employees:
    for t in time_slots:
        prob += lpSum(x[e][t][s] for s in states) == 1  # Employee is in one state at a time
        prob += x[e][t]['Trabaja'] - Demanda.at[t - 7, demand_column_name] <= 0

# Restricciones de trabajo continuo antes de pausa o almuerzo
for e in employees:
    for t in time_slots:
        if t + 3 in time_slots:
            prob += lpSum(x[e][t + i]['Trabaja'] for i in range(4) if t + i in time_slots) >= x[e][t]['Trabaja']

        if t + 8 in time_slots:
            prob += lpSum(x[e][t + i]['Trabaja'] for i in range(9) if t + i in time_slots) <= 2 * x[e][t]['Trabaja']

        if t + 4 in time_slots and t + 12 in time_slots:
            prob += lpSum(x[e][t + i]['Almuerza'] for i in range(9) if t + i in time_slots) == 1

        if t + 4 in time_slots:
            prob += lpSum(x[e][t + i]['Almuerza'] for i in range(5) if t + i in time_slots) == 1

        if t + 12 in time_slots:
            prob += lpSum(x[e][t + i]['Almuerza'] for i in range(13, 15) if t + i in time_slots) == 1

# Restricciones para pausas activas
for e in employees:
    for t in time_slots:
        if t + 3 in time_slots:
            prob += lpSum(x[e][t + i]['Pausa Activa'] for i in range(4) if t + i in time_slots) <= x[e][t]['Trabaja']

# Restricción: Al menos 1 empleado debe estar en algún estado en cada franja horaria
for t in time_slots:
    prob += lpSum(x[e][t]['Trabaja'] for e in employees) >= 1

# Restricción: Al menos 1 empleado debe estar en algún estado en cada franja horaria
for t in time_slots:
    prob += lpSum(x[e][t][s] for e in employees for s in states) >= 1


# Constraint: Duración de la jornada laboral de 8 horas
for e in employees:
    prob += lpSum(x[e][t]['Trabaja'] for t in time_slots) == 8

# Constraint: El horario de los empleados debe ser continuo
for e in employees:
    for t in time_slots:
        prob += lpSum(x[e][t][s] for s in states if s != 'Nada') <= 1

# Constraint: Último estado de la jornada laboral debe ser Trabaja
for e in employees:
    prob += lpSum(x[e][t][s] for t in time_slots for s in states if s == 'Trabaja') == 1

# Constraint: Duración de la franja de trabajo entre 1 y 2 horas
for t in time_slots:
    prob += lpSum(x[e][t][s] for e in employees for s in states if s != 'Nada') >= 1
    prob += lpSum(x[e][t][s] for e in employees for s in states if s != 'Nada') <= 2

# Solve the problem
prob.solve()

# Create a DataFrame to store the schedule
schedule_df = pd.DataFrame(index=time_slots, columns=employees, data="")

# Populate the DataFrame with the optimized schedule
for t in time_slots:
    for e in employees:
        for s in states:
            if value(x[e][t][s]) == 1:
                schedule_df.at[t, e] = s

# Export the DataFrame to a CSV file
schedule_df.to_csv("optimized_horario.csv", index_label="fecha_hora")
