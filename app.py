import streamlit as st

from modules.dashboard import dashboard
from modules.instrumental import registrar_instrumental
from modules.equipos import registrar_equipo
from modules.busqueda import buscar_instrumental
from modules.auditoria import ver_auditoria
from modules.eliminar import eliminar_instrumental

st.set_page_config(
    page_title="SurgiControl",
    page_icon="🏥",
    layout="wide"
)

st.sidebar.title("🏥 SurgiControl")

menu = st.sidebar.radio(
    "Menú",
    [
        "Dashboard",
        "Registrar Instrumental",
        "Registrar Equipo",
        "Buscar Instrumental",
        "Auditoría",
        "Eliminar Instrumental"
    ]
)

if menu == "Dashboard":
    dashboard()

elif menu == "Registrar Instrumental":
    registrar_instrumental()

elif menu == "Registrar Equipo":
    registrar_equipo()

elif menu == "Buscar Instrumental":
    buscar_instrumental()

elif menu == "Auditoría":
    ver_auditoria()

elif menu == "Eliminar Instrumental":
    eliminar_instrumental()
