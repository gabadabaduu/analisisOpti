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

# Additional Constraints
for e in employees:
    for t in time_slots:
        # Constraint: Minimum 1 hour continuous work before break
        if t + 3 in time_slots:
            prob += lpSum(x[e][t + i]['Trabaja'] for i in range(4)) >= x[e][t]['Trabaja']

        # Constraint: Maximum 2 hours continuous work before break
        if t + 8 in time_slots:
            prob += lpSum(x[e][t + i]['Trabaja'] for i in range(9)) <= 2 * x[e][t]['Trabaja']

        # Constraint: Almuerzo de 1 hora y media
        if t + 4 in time_slots and t + 12 in time_slots:
            prob += lpSum(x[e][t + i]['Almuerza'] for i in range(9)) == 1

        # Constraint: Hora mínima de salida para tomar almuerzo
        if t + 4 in time_slots:
            prob += lpSum(x[e][t + i]['Almuerza'] for i in range(5)) == 1

        # Constraint: Hora máxima de salida para tomar almuerzo
        if t + 12 in time_slots:
            prob += lpSum(x[e][t + i]['Almuerza'] for i in range(13, 15)) == 1

# Restricción: Al menos 1 empleado debe trabajar en cada franja horaria
for t in time_slots:
    prob += lpSum(x[e][t]['Trabaja'] for e in employees) >= 1

# Restricción: Al menos 1 empleado debe estar en estado Trabaja en cada franja horaria
for t in time_slots:
    prob += lpSum(x[e][t]['Trabaja'] for e in employees) >= 1

# Restricción: Todos los empleados deben trabajar al menos 1 hora continua antes de tomar Pausa Activa o Almuerzo
for e in employees:
    for t in time_slots[:-4]:  # Excluyendo las últimas cuatro franjas horarias
        prob += lpSum(x[e][t + i]['Trabaja'] for i in range(4)) >= x[e][t]['Trabaja']

# Restricción: Todos los empleados deben trabajar máximo 2 horas continuas antes de tomar Pausa Activa o Almuerzo
for e in employees:
    for t in time_slots[:-9]:  # Excluyendo las últimas nueve franjas horarias
        prob += lpSum(x[e][t + i]['Trabaja'] for i in range(9)) <= 2 * x[e][t]['Trabaja']

# Restricción: La jornada laboral de todos los empleados es de 8 horas diarias
for e in employees:
    prob += lpSum(x[e][t]['Trabaja'] for t in time_slots) == 8

# Restricción: El horario de los empleados debe ser continuo
for e in employees:
    for t in time_slots:
        prob += lpSum(x[e][t][s] for s in states if s != 'Nada') <= 1

# Restricción: Último estado de la jornada laboral debe ser Trabaja
for e in employees:
    prob += lpSum(x[e][t][s] for t in time_slots for s in states if s == 'Trabaja') == 1

# Restricción: Duración de la franja de trabajo entre 1 y 2 horas
for t in time_slots:
    prob += lpSum(x[e][t][s] for e in employees for s in states if s != 'Nada') >= 1
    prob += lpSum(x[e][t][s] for e in employees for s in states if s != 'Nada') <= 2

# Restricción: El estado Nada solo puede estar activo al comienzo o al final del día
for e in employees:
    prob += x[e][time_slots[0]]['Nada'] == 1  # Al comienzo del día
    prob += x[e][time_slots[-1]]['Nada'] == 1  # Al final del día

# Restricción: No se puede salir a tomar almuerzo a las 11:15 am
for e in employees:
    prob += x[e][10]['Almuerza'] == 0

# Restricción: No se puede salir a tomar almuerzo a las 1:45 pm
for e in employees:
    prob += x[e][16]['Almuerza'] == 0

# Restricción: Es VÁLIDO que una persona tome almuerzo de 1:30 pm a 3:00 pm
for e in employees:
    prob += lpSum(x[e][t]['Almuerza'] for t in range(12, 18)) >= 1

# Restricción: Al menos 1 empleado debe trabajar en cada franja horaria
for t in time_slots:
    prob += lpSum(x[e][t]['Trabaja'] for e in employees) >= 1

# Restricción: Al menos 1 empleado debe estar en algún estado en cada franja horaria
for t in time_slots:
    prob += lpSum(x[e][t][s] for e in employees for s in states) >= 1

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
schedule_df.to_csv("optimized_horario2.csv", index_label="fecha_hora")
