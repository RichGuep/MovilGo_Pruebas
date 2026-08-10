# database.py
import os
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno (para no poner claves en el código)
load_dotenv()

# La URL será algo como: postgresql://usuario:contraseña@ip_servidor:5432/nombre_bd
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def cargar_empleados():
    """Reemplaza a cargar_excel('empleados_grupos.xlsx')"""
    query = "SELECT * FROM empleados"
    return pd.read_sql(query, engine)

def guardar_empleados(df):
    """Reemplaza a guardar_github(df, 'empleados_grupos.xlsx')"""
    # Escribe el DataFrame directo a la tabla PostgreSQL
    df.to_sql('empleados', engine, if_exists='replace', index=False)
