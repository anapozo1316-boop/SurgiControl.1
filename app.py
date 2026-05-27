
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="SurgiControl",
    page_icon="🏥",
    layout="wide"
)

# =====================================================
# CONEXIÓN SEGURA
# =====================================================

def get_connection():
    conn = sqlite3.connect(
        "surgicontrol.db",
        check_same_thread=False
    )

    conn.execute("PRAGMA foreign_keys = ON")

    return conn

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# CREACIÓN DE TABLAS
# =====================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS instrumental (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL UNIQUE,

    tipo TEXT NOT NULL,

    cantidad_total INTEGER NOT NULL,

    cantidad_disponible INTEGER NOT NULL,

    cantidad_reparacion INTEGER DEFAULT 0,

    cantidad_prestada INTEGER DEFAULT 0,

    estado TEXT NOT NULL,

    ubicacion TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS equipos (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL UNIQUE,

    especialidad TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS equipo_instrumental (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    equipo_id INTEGER NOT NULL,

    instrumental_id INTEGER NOT NULL,

    cantidad_requerida INTEGER NOT NULL,

    FOREIGN KEY (equipo_id)
    REFERENCES equipos(id)
    ON DELETE CASCADE,

    FOREIGN KEY (instrumental_id)
    REFERENCES instrumental(id)
    ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS auditoria (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    usuario TEXT,

    accion TEXT,

    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# =====================================================
# FUNCIONES
# =====================================================

def registrar_auditoria(usuario, accion):

    cursor.execute("""
    INSERT INTO auditoria
    (usuario, accion)
    VALUES (?, ?)
    """, (usuario, accion))

    conn.commit()


def obtener_instrumental():

    query = """
    SELECT * FROM instrumental
    """

    return pd.read_sql_query(query, conn)


def obtener_equipos():

    query = """
    SELECT * FROM equipos
    """

    return pd.read_sql_query(query, conn)


def calcular_estado_equipo(equipo_id):

    query = """
    SELECT
        ei.cantidad_requerida,
        i.cantidad_disponible

    FROM equipo_instrumental ei

    JOIN instrumental i
    ON ei.instrumental_id = i.id

    WHERE ei.equipo_id = ?
    """

    datos = pd.read_sql_query(
        query,
        conn,
        params=(equipo_id,)
    )

    if len(datos) == 0:
        return "Sin Instrumental"

    faltantes = False

    for _, row in datos.iterrows():

        if row["cantidad_disponible"] < row["cantidad_requerida"]:
            faltantes = True

    if faltantes:
        return "Incompleto"

    return "Completo"


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("🏥 SurgiControl")

menu = st.sidebar.radio(
    "Menú",
    [
        "Dashboard",
        "Registrar Instrumental",
        "Registrar Equipo",
        "Agregar Instrumental a Equipo",
        "Buscar Instrumental",
        "Ver Equipos",
        "Auditoría",
        "Eliminar Instrumental"
    ]
)

# =====================================================
# DASHBOARD
# =====================================================

if menu == "Dashboard":

    st.title("🏥 Dashboard")

    instrumental_df = obtener_instrumental()
    equipos_df = obtener_equipos()

    total_instrumental = len(instrumental_df)
    total_equipos = len(equipos_df)

    stock_critico = len(
        instrumental_df[
            instrumental_df["cantidad_disponible"] <= 2
        ]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Instrumental",
        total_instrumental
    )

    col2.metric(
        "Equipos",
        total_equipos
    )

    col3.metric(
        "Stock Crítico",
        stock_critico
    )

    st.subheader("📋 Inventario")

    st.dataframe(
        instrumental_df,
        use_container_width=True
    )

# =====================================================
# REGISTRAR INSTRUMENTAL
# =====================================================

elif menu == "Registrar Instrumental":

    st.title("➕ Registrar Instrumental")

    with st.form("form_instrumental"):

        nombre = st.text_input("Nombre")

        tipo = st.selectbox(
            "Tipo",
            [
                "Pinza",
                "Separador",
                "Tijera",
                "Óptica",
                "Accesorio"
            ]
        )

        cantidad = st.number_input(
            "Cantidad Total",
            min_value=1,
            step=1
        )

        ubicacion = st.text_input("Ubicación")

        guardar = st.form_submit_button("Guardar")

        if guardar:

            if not nombre.strip():

                st.error("Nombre obligatorio")

            elif not ubicacion.strip():

                st.error("Ubicación obligatoria")

            else:

                try:

                    cursor.execute("""
                    INSERT INTO instrumental (

                        nombre,
                        tipo,
                        cantidad_total,
                        cantidad_disponible,
                        estado,
                        ubicacion

                    )

                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (

                        nombre,
                        tipo,
                        cantidad,
                        cantidad,
                        "Disponible",
                        ubicacion
                    ))

                    conn.commit()

                    registrar_auditoria(
                        "admin",
                        f"Registró instrumental {nombre}"
                    )

                    st.success(
                        "✅ Instrumental registrado"
                    )

                except:

                    st.error(
                        "⚠️ El instrumento ya existe"
                    )

# =====================================================
# REGISTRAR EQUIPO
# =====================================================

elif menu == "Registrar Equipo":

    st.title("🩺 Registrar Equipo")

    with st.form("form_equipo"):

        nombre = st.text_input(
            "Nombre del equipo"
        )

        especialidad = st.selectbox(
            "Especialidad",
            [
                "Ortopedia",
                "Neurocirugía",
                "Cirugía General",
                "Ginecología"
            ]
        )

        guardar = st.form_submit_button(
            "Guardar"
        )

        if guardar:

            try:

                cursor.execute("""
                INSERT INTO equipos
                (nombre, especialidad)

                VALUES (?, ?)
                """, (
                    nombre,
                    especialidad
                ))

                conn.commit()

                registrar_auditoria(
                    "admin",
                    f"Creó equipo {nombre}"
                )

                st.success(
                    "✅ Equipo registrado"
                )

            except:

                st.error(
                    "⚠️ El equipo ya existe"
                )

# =====================================================
# AGREGAR INSTRUMENTAL A EQUIPO
# =====================================================

elif menu == "Agregar Instrumental a Equipo":

    st.title("🔗 Relacionar Instrumental")

    equipos_df = obtener_equipos()
    instrumental_df = obtener_instrumental()

    if len(equipos_df) == 0 or len(instrumental_df) == 0:

        st.warning(
            "Debe registrar equipos e instrumental"
        )

    else:

        equipo_nombre = st.selectbox(
            "Equipo",
            equipos_df["nombre"]
        )

        instrumental_nombre = st.selectbox(
            "Instrumental",
            instrumental_df["nombre"]
        )

        cantidad = st.number_input(
            "Cantidad requerida",
            min_value=1,
            step=1
        )

        if st.button("Agregar"):

            equipo_id = int(
                equipos_df[
                    equipos_df["nombre"] == equipo_nombre
                ]["id"].values[0]
            )

            instrumental_id = int(
                instrumental_df[
                    instrumental_df["nombre"] == instrumental_nombre
                ]["id"].values[0]
            )

            cursor.execute("""
            INSERT INTO equipo_instrumental (

                equipo_id,
                instrumental_id,
                cantidad_requerida

            )

            VALUES (?, ?, ?)
            """, (
                equipo_id,
                instrumental_id,
                cantidad
            ))

            conn.commit()

            registrar_auditoria(
                "admin",
                f"Agregó {instrumental_nombre} al equipo {equipo_nombre}"
            )

            st.success(
                "✅ Relación creada"
            )

# =====================================================
# BUSCAR INSTRUMENTAL
# =====================================================

elif menu == "Buscar Instrumental":

    st.title("🔍 Buscar Instrumental")

    busqueda = st.text_input(
        "Buscar instrumento"
    )

    if busqueda:

        query = """
        SELECT * FROM instrumental
        WHERE nombre LIKE ?
        """

        resultados = pd.read_sql_query(
            query,
            conn,
            params=(f"%{busqueda}%",)
        )

        if len(resultados) > 0:

            st.dataframe(
                resultados,
                use_container_width=True
            )

        else:

            st.warning(
                "No se encontraron resultados"
            )

# =====================================================
# VER EQUIPOS
# =====================================================

elif menu == "Ver Equipos":

    st.title("📦 Equipos")

    equipos_df = obtener_equipos()

    if len(equipos_df) == 0:

        st.warning(
            "No hay equipos registrados"
        )

    else:

        for _, equipo in equipos_df.iterrows():

            estado = calcular_estado_equipo(
                equipo["id"]
            )

            if estado == "Completo":
                icono = "🟢"

            elif estado == "Incompleto":
                icono = "🟡"

            else:
                icono = "⚪"

            st.subheader(
                f"{icono} {equipo['nombre']}"
            )

            st.write(
                f"Especialidad: {equipo['especialidad']}"
            )

            st.write(
                f"Estado: {estado}"
            )

            query = """
            SELECT

                i.nombre,
                ei.cantidad_requerida,
                i.cantidad_disponible

            FROM equipo_instrumental ei

            JOIN instrumental i
            ON ei.instrumental_id = i.id

            WHERE ei.equipo_id = ?
            """

            detalle = pd.read_sql_query(
                query,
                conn,
                params=(equipo["id"],)
            )

            st.dataframe(
                detalle,
                use_container_width=True
            )

            st.divider()

# =====================================================
# AUDITORÍA
# =====================================================

elif menu == "Auditoría":

    st.title("📜 Historial")

    auditoria_df = pd.read_sql_query(
        "SELECT * FROM auditoria ORDER BY fecha DESC",
        conn
    )

    st.dataframe(
        auditoria_df,
        use_container_width=True
    )

# =====================================================
# ELIMINAR INSTRUMENTAL
# =====================================================

elif menu == "Eliminar Instrumental":

    st.title("🗑️ Eliminar Instrumental")

    instrumental_df = obtener_instrumental()

    if len(instrumental_df) == 0:

        st.warning(
            "No hay instrumental registrado"
        )

    else:

        seleccion = st.selectbox(
            "Seleccionar",
            instrumental_df["nombre"]
        )

        instrumento_id = int(

            instrumental_df[
                instrumental_df["nombre"] == seleccion
            ]["id"].values[0]

        )

        if st.button("Eliminar"):

            cursor.execute("""
            DELETE FROM instrumental
            WHERE id = ?
            """, (instrumento_id,))

            conn.commit()

            registrar_auditoria(
                "admin",
                f"Eliminó instrumental {seleccion}"
            )

            st.success(
                "✅ Instrumental eliminado"
            )
