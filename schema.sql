-- Tabla para el personal (Reemplaza empleados_grupos.xlsx)
CREATE TABLE empleados (
    cedula VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    cargo VARCHAR(50),
    grupo_asignado VARCHAR(20) DEFAULT 'None'
);

-- Tabla para los ajustes manuales y programación (Reemplaza los diccionarios en memoria)
CREATE TABLE programacion_turnos (
    id SERIAL PRIMARY KEY,
    sujeto VARCHAR(100) NOT NULL, -- Puede ser nombre de empleado o "Grupo 1"
    fecha DATE NOT NULL,
    turno_asignado VARCHAR(20) NOT NULL,
    UNIQUE (sujeto, fecha) -- Evita duplicados para un mismo sujeto en la misma fecha
);
