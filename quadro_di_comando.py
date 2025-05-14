import streamlit as st

from data_processing import carica_elaboara_spese, load_and_preprocess_data
from draw_dashboard import dashboard_analisi_performance, dashboard_proprietari, dashboard_spese, render_calcolatore, \
    render_dashboard

# Configurazione della pagina
st.set_page_config(
    page_title="Dashboard Dati Immobiliari",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

#############   caricamento manuale file     ##################

def upload_file():
    # Sezione espandibile per il caricamento del file
    with st.expander("📂 Carica File Excel"):
        uploaded_file = st.file_uploader("Seleziona un file Excel", type="xlsx")
        if uploaded_file:
            st.success("File caricato con successo!")
           # Salva i dati nel session state
            st.session_state['uploaded_file'] = uploaded_file
            st.session_state['data'] = load_and_preprocess_data(uploaded_file)
            st.session_state['spese'] = carica_elaboara_spese(uploaded_file)
    return uploaded_file


################### Main  ####################
menu = st.sidebar.selectbox("Menù", ["Carica File", "Dashboard", "Analisi Performance", "Dashboard Propietari", "Analisi spese", "Calcolatore"])

if menu == "Carica File":
    upload_file()
elif menu == "Dashboard":
    render_dashboard()
elif menu == "Analisi Performance":
    dashboard_analisi_performance()
elif menu == "Dashboard Propietari":
    dashboard_proprietari()
elif menu == "Analisi spese":
    dashboard_spese()
elif menu == "Calcolatore":
    render_calcolatore()
