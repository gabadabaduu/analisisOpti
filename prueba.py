import pandas as pd
import pulp
from datetime import datetime

# Cargar los datos de demanda
demanda_df = pd.read_csv("demanda.csv", sep='\s+')

fecha_hora = datetime.strptime(date_str, '%H:%M')
# Asegúrate de que los valores en tus datos coincidan con el nuevo formato de 'fecha_hora'
fechas_hora = []
for date_str in demanda_df['fecha_hora']:  # Reemplaza 'nombre_de_la_columna_correcta' con el nombre correcto
    try:
        fecha_hora = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
    except ValueError:
        # Si el formato es diferente, intenta manejarlo de otra manera
        # Ajusta esta parte según el formato real en tus datos
        fecha_hora = datetime.strptime(date_str, '%H:%M')
    fechas_hora.append(fecha_hora)
franjas_horarias = [fecha.strftime('%Y-%m-%d %H:%M:%S') for fecha in fechas_hora]

# Cargar los datos de capacidad
capacidad_df = pd.read_csv("capacidad.csv", sep='\s+')

# Asegúrate de que las fechas se ajusten al nuevo formato en los datos de capacidad
# Cambia esta línea para seleccionar 'suc_cod' en lugar de 'documento'
empleados = capacidad_df['suc_cod'].tolist()

# Lista de empleados
empleados = capacidad_df['suc_cod'].tolist()

# Lista de franjas horarias
franjas_horarias = demanda_df['fecha_hora'].tolist()

dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

# Listas de empleados
empleados_TC = capacidad_df[capacidad_df['contrato'] == 'TC']['suc_cod'].tolist()
empleados_MT = capacidad_df[capacidad_df['contrato'] == 'MT']['suc_cod'].tolist()

# Crear un problema de programación lineal entera
model = pulp.LpProblem("ProgramacionHoraria", pulp.LpMinimize)

# Variables binarias para el estado de Trabaja de cada empleado en cada franja horaria
Trabaja = pulp.LpVariable.dicts("Trabaja", [(i, j) for i in empleados for j in franjas_horarias], cat=pulp.LpBinary)

# Variables binarias para el estado de Pausa_Activa de cada empleado en cada franja horaria
Pausa_Activa = pulp.LpVariable.dicts("Pausa_Activa", [(i, j) for i in empleados for j in franjas_horarias], cat=pulp.LpBinary)

# Variables binarias para el estado de Almuerzo de cada empleado en cada franja horaria
Almuerzo = pulp.LpVariable.dicts("Almuerzo", [(i, j) for i in empleados_TC for j in franjas_horarias], cat=pulp.LpBinary)

# Variables continuas para la demanda en cada franja horaria
demanda = pulp.LpVariable.dicts("Demanda", franjas_horarias, lowBound=0)
for f in franjas_horarias:
    if f in demanda_df['fecha_hora'].values:
        demanda[f] = pulp.LpVariable(name=f"Demanda_{f}", lowBound=0, upBound=demanda_df[demanda_df['fecha_hora'] == f]['demanda'].values[0], cat=pulp.LpInteger)
    else:
        demanda[f] = pulp.LpVariable(name=f"Demanda_{f}", lowBound=0, cat=pulp.LpInteger)

# Variables binarias para el estado de Nada de cada empleado en cada franja horaria
Nada = pulp.LpVariable.dicts("Nada", [(i, j) for i in empleados for j in franjas_horarias], cat=pulp.LpBinary)

# Variables binarias para el estado de cada empleado en cada franja horaria
X = pulp.LpVariable.dicts("Estado", [(i, j) for i in empleados for j in franjas_horarias], cat=pulp.LpBinary)

# Variables continuas para el tiempo de inicio de la jornada laboral de cada empleado
T = pulp.LpVariable.dicts("TiempoInicioJornada", empleados, lowBound=0, upBound=len(franjas_horarias))

# Variables continuas para el tiempo de inicio del almuerzo
TiempoAlmuerzo = pulp.LpVariable.dicts("TiempoAlmuerzo", empleados_TC, lowBound=0, upBound=len(franjas_horarias))

# Variables continuas para el tiempo de fin del almuerzo
TiempoFinAlmuerzo = pulp.LpVariable.dicts("TiempoFinAlmuerzo", empleados_TC, lowBound=0, upBound=len(franjas_horarias))

# Variables continuas para el tiempo de fin de la jornada laboral de cada empleado
TiempoFinJornada = pulp.LpVariable.dicts("TiempoFinJornada", empleados, lowBound=0, upBound=len(franjas_horarias))

# Variables binarias para indicar si al menos un empleado trabaja en cada franja requerida
TrabajaEnFranja = pulp.LpVariable.dicts("TrabajaEnFranja", franjas_horarias, cat=pulp.LpBinary)

# Asegura que un empleado no trabaje más de 8 franjas horarias seguidas
for i in empleados:
    for j in franjas_horarias:
        model.addConstraint(Trabaja[i, j] + Pausa_Activa[i, j] + Nada[i, j] + Almuerzo[i, j] == 1)
        model.addConstraint(T[i] + 1 <= T[i] + 8 * (1 - X[i, j]))
        
# Asegura que al menos un empleado trabaje en cada franja con demanda
for f in franjas_horarias:
    if f in demanda_df['fecha_hora'].values:
        model.addConstraint(TrabajaEnFranja[f] == pulp.lpSum(Trabaja[i, j] for i in empleados for j in franjas_horarias))

# Asegura que ningún empleado trabaje en franjas sin demanda
for f in franjas_horarias:
    if f not in demanda_df['fecha_hora'].values:
        model.addConstraint(TrabajaEnFranja[f] == 0)

# Define la función objetivo para minimizar la diferencia entre la cantidad de empleados trabajando y la demanda
model += pulp.lpSum(Trabaja[i, j] for i in empleados for j in franjas_horarias) - pulp.lpSum(demanda[j] for j in franjas_horarias), "Objetivo"

# Resuelve el problema
model.solve()

# Verifica el estado de la solución
if pulp.LpStatus[model.status] == 'Optimal':
    # Crear una lista de variables con valor 1 en la solución
    variables_con_valor_1 = [(i, j) for i in empleados for j in franjas_horarias if pulp.value(X[i, j]) == 1]

    # Crear un DataFrame detallado con los resultados
    resultados = []
    for empleado, franja in variables_con_valor_1:
        tipo_contrato = "TC" if empleado in empleados_TC else "MT"
        resultados.append([empleado, franja, tipo_contrato])

    # Guardar los resultados en un archivo CSV
    df = pd.DataFrame(resultados, columns=["Empleado", "Franja Horaria", "Tipo de Contrato"])
    df.to_csv("resultados.csv", index=False)

    print("Resultados guardados en resultados.csv")
else:
    print("No se encontró una solución óptima.")


