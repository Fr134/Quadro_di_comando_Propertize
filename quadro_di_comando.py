import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go



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
    return uploaded_file





############### Funzione per calcolare le notti disponibili   ############# 

def calcola_notti_disponibili(file_path, start_date, end_date):
    """
    Calcola il numero totale di notti disponibili per ogni appartamento
    nel periodo specificato dai filtri.
    """
    # Legge il Foglio 2 del file Excel
    disponibilita = pd.read_excel(file_path, sheet_name=1)
    
    # Dizionario per salvare le notti disponibili per ogni appartamento
    notti_disponibili = []

    for index, row in disponibilita.iterrows():
        appartamento = row[0]  # Nome dell'appartamento nella prima colonna
        totale_notti = 0

        # Itera sulle colonne in coppie (Data inizio, Data fine)
        for i in range(1, len(row), 2):  # Parte dalla seconda colonna e salta di 2
            data_inizio = row[i]
            data_fine = row[i + 1] if i + 1 < len(row) else None

            # Controlla se entrambe le date sono valide
            if pd.notnull(data_inizio) and pd.notnull(data_fine):
                data_inizio = pd.to_datetime(data_inizio, errors='coerce')
                data_fine = pd.to_datetime(data_fine, errors='coerce')

                # Filtra le date che rientrano nell'intervallo selezionato
                if data_inizio and data_fine:
                    intervallo_inizio = max(data_inizio, pd.Timestamp(start_date))
                    intervallo_fine = min(data_fine, pd.Timestamp(end_date))
                    notti = (intervallo_fine - intervallo_inizio).days + 1
                    totale_notti += max(notti, 0)  # Solo notti positive

        # Salva il risultato per l'appartamento
        notti_disponibili.append({"Appartamento": appartamento, "Notti Disponibili": totale_notti})

    # Converti il risultato in un DataFrame
    return pd.DataFrame(notti_disponibili)



############### Funzione per caricare e preprocessare i dati    #############   

def load_and_preprocess_data(uploaded_file):
    data = pd.read_excel(
        uploaded_file,
        sheet_name=0,
        usecols="B,C,D,G,H,I,J,O,P,Q,R,U,V,W,X,AA,AB,AC,AJ,AK,AL",
        dtype=str,
        engine="openpyxl"
    )

    data.columns = [
        'ID Appartamento', 
        'Nome Appartamento',
        'Nome Proprietario',
        'Data Check-In',
        'Data Check-Out',
        'Ricavi Locazione',
        'Ricavi Pulizie',
        'Tassa di Soggiorno',
        'OTA',
        'OTA Lordo/Netta',
        'Commissioni OTA',
        'Commissioni ITW Nette',
        'IVA Commissioni ITW',
        'Commissioni ITW Lorde',
        'Costi di incasso',
        'Provvigioni PM Nette',
        'IVA Provvigioni PM',
        'Provvigioni PM Lorde',
        'Commissioni Proprietari Lorde',
        'Cedolare secca',
        'Commissioni Proprietari Nette'
    ]

    data = data.dropna(subset=['ID Appartamento'])
    
    
    # Conversione delle date con il formato DD/MM/YYYY
    data['Data Check-In'] = pd.to_datetime(data['Data Check-In'], errors='coerce', dayfirst=True)
    data['Data Check-Out'] = pd.to_datetime(data['Data Check-Out'], errors='coerce', dayfirst=True)


    data = data.dropna(subset=['Data Check-In'])
    data['Durata Soggiorno'] = (data['Data Check-Out'] - data['Data Check-In']).dt.days

    numeric_columns = [
        'Ricavi Locazione', 'Ricavi Pulizie', 'Tassa di Soggiorno',
        'Commissioni OTA', 'Commissioni ITW Nette', 'IVA Commissioni ITW',
        'Commissioni ITW Lorde', 'Costi di incasso', 'Provvigioni PM Nette',
        'IVA Provvigioni PM', 'Provvigioni PM Lorde', 'Commissioni Proprietari Lorde',
        'Cedolare secca', 'Commissioni Proprietari Nette'
    ]
    
    
    
    
    
    for col in numeric_columns:
        data[col] = data[col].str.replace(',', '.', regex=False)
        data[col] = pd.to_numeric(data[col], errors='coerce')
        
        
    data['ricavi_totali'] = data['Ricavi Locazione'] - data['IVA Provvigioni PM'] + data['Ricavi Pulizie'] / 1.22
    data['commissioni_totali'] = data['Commissioni OTA'] / 1.22 + data['Commissioni ITW Nette'] + data['Commissioni Proprietari Lorde']    
    data['marginalità_totale'] = data['ricavi_totali'] - data['commissioni_totali']
    data['commissioni_OTA_locazioni'] = data['Commissioni OTA']/1.22 - (data['Ricavi Locazione'] / (data['Ricavi Locazione'] + data['Ricavi Pulizie']))
    data['marginalità_locazioni'] = data['Ricavi Locazione']-data['Commissioni Proprietari Lorde'] - data['IVA Provvigioni PM'] - data['commissioni_OTA_locazioni']
    data['marginalità_pulizie'] = data['Ricavi Pulizie']/1.22 - (data['Commissioni OTA'] - data['marginalità_locazioni'])
     

    data = data.fillna(0)
    data['Mese'] = data['Data Check-In'].dt.to_period('M').astype(str)
    return data

############## Calcolo dei KPI    #############   


def calculate_kpis(data, notti_disponibili_filtrate):
    
    
    #   RICAVI   SENZA IVA   #
    
    
    
    totale_ricavi_locazione = data['Ricavi Locazione'].sum() - data['IVA Provvigioni PM'].sum() 
    totale_ricavi_pulizie = data['Ricavi Pulizie'].sum() / 1.22
    ricavi_totali = totale_ricavi_locazione + totale_ricavi_pulizie
    
    
    #   COMMISSIONI SENZA IVA   #
    
    commissioni_ota = data['Commissioni OTA'].sum() / 1.22
    commissioni_proprietari = data['Commissioni Proprietari Lorde'].sum()
    commissioni_ota_locazioni = data['Commissioni OTA'].sum() / 1.22 * (data['Ricavi Locazione'].sum() / (data['Ricavi Locazione'].sum() + data['Ricavi Pulizie'].sum()))
    commissioni_itw = data['Commissioni ITW Nette'].sum()
    totale_commissioni = data['Commissioni OTA'].sum() / 1.22 + data['Commissioni ITW Nette'].sum() + commissioni_proprietari
    
    #   MARGINALITà SENZA IVA   #
    
    marginalità_locazioni = totale_ricavi_locazione - commissioni_ota_locazioni - data['Commissioni Proprietari Lorde'].sum()
    marginalità_pulizie = totale_ricavi_pulizie - (data['Commissioni OTA'].sum() / 1.22 - commissioni_ota_locazioni)
    marginalità_totale = marginalità_locazioni + marginalità_pulizie
    
    
    #  SALDO IVA   #

    IVA_OTA = data['Commissioni OTA'].sum() * 0.22
    IVA_Totale_credito = data['IVA Commissioni ITW'].sum() + IVA_OTA
    IVA_Totale_Debito = data['IVA Provvigioni PM'].sum()
    Saldo_IVA = IVA_Totale_Debito - IVA_Totale_credito
    
    
    
    #  CALCOLO NOTTI, PRENOTAZIONI ECC...   #
        
    # Calcolo delle notti occupate (Durata soggiorno) per ogni riga
    data['Notti Occupate'] = (data['Data Check-Out'] - data['Data Check-In']).dt.days
   
    # Controlla se ci sono valori negativi (check-out prima del check-in) e li gestisce
    data['Notti Occupate'] = data['Notti Occupate'].apply(lambda x: max(x, 0))  # Imposta a 0 eventuali valori negativi
    
    #Calcola il numero totale di prenotazioni basandosi sul numero di righe del DataFrame.    
    numero_prenotazioni = len(data)
    
    #Calcolo notti occupate, libere e tasso di occupazione
    valore_medio_prenotazione = totale_ricavi_locazione/numero_prenotazioni
    prezzo_medio_notte = totale_ricavi_locazione/data['Notti Occupate'].sum()
    soggiorno_medio = data['Notti Occupate'].sum()/numero_prenotazioni
    notti_occupate = data['Notti Occupate'].sum()   
    notti_disponibili = notti_disponibili_filtrate['Notti Disponibili'].sum()
    notti_libere = notti_disponibili - notti_occupate
    tasso_di_occupazione = notti_occupate/notti_disponibili*100
    
    
    #   MARGINALITà MEDIA SENZA IVA   #
    
    
    margine_medio_prenotazione = marginalità_totale/numero_prenotazioni
    margine_medio_notte = marginalità_locazioni/data['Notti Occupate'].sum()
    prezzo_pulizie = totale_ricavi_pulizie/numero_prenotazioni
    margine_medio_pulizie = marginalità_pulizie/numero_prenotazioni
    
    
    
    return {
        "totale_ricavi_locazione": totale_ricavi_locazione,
        "totale_ricavi_pulizie": totale_ricavi_pulizie,
        "ricavi_totali": ricavi_totali,
        "commissioni_ota": commissioni_ota,
        "commissioni_itw": commissioni_itw,
        "commissioni_proprietari": commissioni_proprietari,
        "totale_commissioni": totale_commissioni,
        "marginalità_locazioni": marginalità_locazioni,
        "marginalità_pulizie": marginalità_pulizie,
        "marginalità_totale": marginalità_totale,
        "IVA_Totale_credito": IVA_Totale_credito,
        "IVA_Totale_Debito": IVA_Totale_Debito,
        "Saldo_IVA": Saldo_IVA,
        "valore_medio_prenotazione": valore_medio_prenotazione,
        'prezzo_medio_notte':prezzo_medio_notte,
        'soggiorno_medio':soggiorno_medio,
        'margine_medio_prenotazione':margine_medio_prenotazione,
        'margine_medio_notte': margine_medio_notte,
        'margine_medio_pulizie': margine_medio_pulizie,
        'prezzo_pulizie':prezzo_pulizie,
        'notti_occupate':notti_occupate,
        'tasso_di_occupazione':tasso_di_occupazione,
        'notti_disponibili': notti_disponibili,
        'notti_libere': notti_libere
    }

############## Funzione per Modificare la grafica della pagina     ############# 

def inject_custom_css():
    """
    Inietta CSS personalizzato nella pagina Streamlit.
    """
    custom_css = """
    <style>
        /* Cambia il colore del titolo */
        h1 {
            color: #2E8B57; /* Verde scuro */
        }

        /* Personalizza i metriche */
        .metric-container {
            background-color: #f7f7f7; /* Grigio chiaro */
            border: 1px solid #ddd; /* Bordo sottile */
            border-radius: 8px; /* Angoli arrotondati */
            padding: 10px; /* Spaziatura interna */
            margin: 5px; /* Spaziatura esterna */
        }

        /* Modifica i pulsanti */
        button {
            background-color: #007BFF; /* Blu scuro */
            color: white; /* Testo bianco */
            border: none;
            border-radius: 5px;
            padding: 10px 15px;
        }
        button:hover {
            background-color: #0056b3; /* Blu ancora più scuro */
        }

        /* Personalizza il layout delle colonne */
        .stColumn {
            margin-bottom: 20px; /* Spazio tra colonne */
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


############## Funzione per visualizzare i KPI e i grafici      #############   


def render_dashboard():
    """
    Visualizza la dashboard con KPI, grafici e calcolo dinamico delle notti disponibili.
    """
    inject_custom_css()
    st.title("📊 Dashboard Dati immobiliari")

    

    # Verifica se i dati principali sono disponibili
    if 'data' not in st.session_state or st.session_state['data'] is None:
        st.error("Nessun dato disponibile. Torna alla pagina di caricamento.")
        return

    # Verifica se il file è disponibile per il calcolo delle notti disponibili
    if 'uploaded_file' not in st.session_state:
        st.error("Nessun file caricato per il calcolo delle notti disponibili.")
        return

    file_path = st.session_state['uploaded_file']
    data = st.session_state['data']
    print(data)
    
    
    
    # Sezione Filtri
    with st.sidebar.expander("🔍 Filtro Dati"):
        st.markdown("### Filtra i dati")
        
        # Filtro per intervallo di date
        start_date = st.date_input(
            "Data Inizio",
            data['Data Check-In'].min().date(),
            key="start_date_filter"
        )
        end_date = st.date_input(
            "Data Fine",
            data['Data Check-In'].max().date(),
            key="end_date_filter"
        )

        # Filtro per appartamento
        view_option = st.radio(
            "Visualizza",
            ("Tutti gli Appartamenti", "Singolo Appartamento"),
            key="view_option_filter"
        )
        appartamento = None
        if view_option == "Singolo Appartamento":
            appartamento = st.selectbox(
                "Seleziona Appartamento",
                data['Nome Appartamento'].unique(),
                key="appartamento_filter"
            )

        # Filtraggio dei dati principali
        dati_filtrati = data[
            (data['Data Check-In'] >= pd.Timestamp(start_date)) &
            (data['Data Check-In'] <= pd.Timestamp(end_date))
        ]
        if appartamento:
            dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'] == appartamento]

        # Assicurati che le colonne calcolate siano presenti nel DataFrame filtrato
        if 'ricavi_totali' not in dati_filtrati.columns:
            dati_filtrati['ricavi_totali'] = dati_filtrati['Ricavi Locazione'] - dati_filtrati['IVA Provvigioni PM'] - dati_filtrati['Commissioni OTA'] * 0.22 + dati_filtrati['Ricavi Pulizie'] / 1.22
        if 'commissioni_totali' not in dati_filtrati.columns:
            dati_filtrati['commissioni_totali'] = dati_filtrati['Commissioni OTA'] / 1.22 + dati_filtrati['Commissioni ITW Nette']

        # Calcola le notti disponibili
        notti_disponibili_df = calcola_notti_disponibili(file_path, start_date, end_date)
        
        # Filtra le notti disponibili in base al filtro appartamento
        if appartamento:
            notti_disponibili_filtrate = notti_disponibili_df[
                notti_disponibili_df['Appartamento'] == appartamento
            ]
        else:
            notti_disponibili_filtrate = notti_disponibili_df

        # Salva i dati filtrati nel session state
        st.session_state['filtered_data'] = dati_filtrati
        st.session_state['filtered_notti_disponibili'] = notti_disponibili_filtrate

    # Usa i dati filtrati se disponibili
    if 'filtered_data' in st.session_state:
        dati_filtrati = st.session_state['filtered_data']
    if 'filtered_notti_disponibili' in st.session_state:
        notti_disponibili_filtrate = st.session_state['filtered_notti_disponibili']


    
    # Calcolo dei KPI
    kpis = calculate_kpis(dati_filtrati, notti_disponibili_filtrate)
    st.dataframe(kpis)


    
    
    st.divider()
    
   ############ Layout a 3 colonne per dividere lo schermo in tre sezioni uguali    ###########
   
        
            
    col1, col2 = st.columns([2,4])  # Tre colonne di uguale larghezza

    # Colonna 1: Grafico ad anello + KPI
    
    
    with col1:
        
        
        st.metric("💰 Ricavi Totali (€)", f"{kpis['ricavi_totali']:,.2f}")

        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_commissioni"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("📈 Costi (€)", f"{kpis['totale_commissioni']:,.2f}")

        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["marginalità_totale"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("📈 Margine sul venduto (€)", f"{kpis['marginalità_totale']:,.2f}")
         
        
                      
        
      
    with col2:
        colonne = ['ricavi_totali', 'commissioni_totali', 'marginalità_totale']
        fig = visualizza_andamento_ricavi(dati_filtrati, colonne)
        st.plotly_chart(fig)

           
    with col3:
        
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        with col3:
            totale = kpis["ricavi_totali"]
            kpi = kpis["marginalità_pulizie"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with col3:
            st.metric("📊 Marginalità Pulizie (€)", f"{kpis['marginalità_pulizie']:,.2f}")
                       
    with col4:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        with col4:
            totale = kpis["ricavi_totali"]
            kpi = kpis["marginalità_totale"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with col4:
            st.metric("💰 Marginalità Totale (€)", f"{kpis['marginalità_totale']:,.2f}")
        
    with col4_1:
        # Visualizza il grafico nella dashboard
        
        crea_grafico_barre(
            dati_filtrati,
            ricavi_colonna="marginalità_pulizie",
            commissioni_colonna="marginalità_locazioni",
            marginalita_colonna="marginalità_totale",  # Assicurati che questa colonna esista nel DataFrame
            start_date=start_date,
            end_date=end_date
        )
        


           
    col5, col6, col7 = st.columns([6, 8, 4])  # Tre colonne di uguale larghezza
    
    with col5:
        
        with col5:
            st.metric("💰 Ricavi Totali (€)", f"{kpis['ricavi_totali']:,.2f}")
                      
        
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_locazione"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("📈 Ricavi Locazione (€)", f"{kpis['totale_ricavi_locazione']:,.2f}")
            
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_pulizie"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Ricavi Pulizie (€)", f"{kpis['totale_ricavi_pulizie']:,.2f}") 
            
        
    with col6:
        # Visualizza il grafico nella dashboard
        st.markdown("### Andamento Ricavi, Commissioni e Marginalità")
        crea_grafico_barre(
            dati_filtrati,
            ricavi_colonna="ricavi_totali",
            commissioni_colonna="commissioni_totali",
            marginalita_colonna="marginalità_totale",  # Assicurati che questa colonna esista nel DataFrame
            start_date=start_date,
            end_date=end_date
        )
        
        


        
    with col7:
        col7_1, col7_2 = st.columns([2,2])
        with col7_1:
            st.metric("🔄 IVA a Credito (€)", f"{kpis['IVA_Totale_credito']:,.2f}")
            
        with col7_2:
            st.metric("📊 IVA a Debito (€)", f"{kpis['IVA_Totale_Debito']:,.2f}")
            
        st.metric("💼 Saldo IVA (€)", f"{kpis['Saldo_IVA']:,.2f}")
            
    
    
    st.divider()
            
    col8, col9, col10, col11 = st.columns([4.5, 4.5, 4.5, 4.5])  # Tre colonne di uguale larghezza
    
    with col8:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        with col8:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_proprietari"]
            grafico_anello = create_donut_chart2(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with col8:
            st.metric("💼 Commissioni Proprietari (€)", f"{kpis['commissioni_proprietari']:,.2f}")
    
    with col9:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        
        with col9:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_ota"]
            grafico_anello = create_donut_chart2(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with col9:
            st.metric("🔄 Commissioni OTA (€)", f"{kpis['commissioni_ota']:,.2f}")
    
    with col10:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        col10_1, col10_2 = st.columns([2, 2])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with col10_1:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_itw"]
            grafico_anello = create_donut_chart2(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        
        with col10_2:
            totale = kpis["ricavi_totali"]
            kpi = kpis["marginalità_totale"]
            grafico_anello = create_donut_chart2(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        
        
        with col10:
            st.metric("📊 Commissioni ITW (€)", f"{kpis['commissioni_itw']:,.2f}")
    
    with col11:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        with col11:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_commissioni"]
            grafico_anello = create_donut_chart2(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with col11:
            st.metric("📊 Commissioni Totali (€)", f"{kpis['totale_commissioni']:,.2f}")
    
        
    
    st.divider()
         
    

    

def dashboard_proprietari():
    inject_custom_css()
    st.title("📊 Performance immobili")

    

    # Verifica se i dati principali sono disponibili
    if 'data' not in st.session_state or st.session_state['data'] is None:
        st.error("Nessun dato disponibile. Torna alla pagina di caricamento.")
        return

    # Verifica se il file è disponibile per il calcolo delle notti disponibili
    if 'uploaded_file' not in st.session_state:
        st.error("Nessun file caricato per il calcolo delle notti disponibili.")
        return

    file_path = st.session_state['uploaded_file']
    data = st.session_state['data']

    # Sezione Filtri
    with st.sidebar.expander("🔍 Filtro Dati"):
        st.markdown("### Filtra i dati")
        
        # Filtro per intervallo di date
        start_date = st.date_input(
            "Data Inizio",
            data['Data Check-In'].min().date(),
            key="start_date_filter"
        )
        end_date = st.date_input(
            "Data Fine",
            data['Data Check-In'].max().date(),
            key="end_date_filter"
        )

        # Filtro per appartamento
        view_option = st.radio(
            "Visualizza",
            ("Tutti gli Appartamenti", "Singolo Appartamento"),
            key="view_option_filter"
        )
        appartamento = None
        if view_option == "Singolo Appartamento":
            appartamento = st.selectbox(
                "Seleziona Appartamento",
                data['Nome Appartamento'].unique(),
                key="appartamento_filter"
            )

        # Filtraggio dei dati principali
        dati_filtrati = data[
            (data['Data Check-In'] >= pd.Timestamp(start_date)) &
            (data['Data Check-In'] <= pd.Timestamp(end_date))
        ]
        if appartamento:
            dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'] == appartamento]

        # Assicurati che le colonne calcolate siano presenti nel DataFrame filtrato
        if 'ricavi_totali' not in dati_filtrati.columns:
            dati_filtrati['ricavi_totali'] = dati_filtrati['Ricavi Locazione'] - dati_filtrati['IVA Provvigioni PM'] - dati_filtrati['Commissioni OTA'] * 0.22 + dati_filtrati['Ricavi Pulizie'] / 1.22
        if 'commissioni_totali' not in dati_filtrati.columns:
            dati_filtrati['commissioni_totali'] = dati_filtrati['Commissioni OTA'] / 1.22 + dati_filtrati['Commissioni ITW Nette']

        # Calcola le notti disponibili
        notti_disponibili_df = calcola_notti_disponibili(file_path, start_date, end_date)
        
        # Filtra le notti disponibili in base al filtro appartamento
        if appartamento:
            notti_disponibili_filtrate = notti_disponibili_df[
                notti_disponibili_df['Appartamento'] == appartamento
            ]
        else:
            notti_disponibili_filtrate = notti_disponibili_df

        # Salva i dati filtrati nel session state
        st.session_state['filtered_data'] = dati_filtrati
        st.session_state['filtered_notti_disponibili'] = notti_disponibili_filtrate

    # Usa i dati filtrati se disponibili
    if 'filtered_data' in st.session_state:
        dati_filtrati = st.session_state['filtered_data']
    if 'filtered_notti_disponibili' in st.session_state:
        notti_disponibili_filtrate = st.session_state['filtered_notti_disponibili']


    # Calcolo dei KPI
    kpis = calculate_kpis(dati_filtrati, notti_disponibili_filtrate)



    col1, col2, col3, col4 = st.columns([6, 4, 4, 4])  # Tre colonne di uguale larghezza
    
    with col1:
        
        with col1:
            st.metric("💰 Ricavi Totali (€)", f"{kpis['ricavi_totali']:,.2f}")
                      
        
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_locazione"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("📈 Ricavi Locazione (€)", f"{kpis['totale_ricavi_locazione']:,.2f}")
            
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_pulizie"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Ricavi Pulizie (€)", f"{kpis['totale_ricavi_pulizie']:,.2f}") 
          
    with col2:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        with col2:
            totale = kpis["ricavi_totali"]
            kpi = kpis["marginalità_locazioni"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with col2:
            st.metric("💰 Marginalità Locazioni (€)", f"{kpis['marginalità_locazioni']:,.2f}")
           
    with col3:
        
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        with col3:
            totale = kpis["ricavi_totali"]
            kpi = kpis["marginalità_pulizie"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with col3:
            st.metric("📊 Marginalità Pulizie (€)", f"{kpis['marginalità_pulizie']:,.2f}")
                       
    with col4:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        
        with col4:
            totale = kpis["ricavi_totali"]
            kpi = kpis["marginalità_totale"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with col4:
            st.metric("💰 Marginalità Totale (€)", f"{kpis['marginalità_totale']:,.2f}")
        
    # Layout a colonne: il grafico occuperà una colonna di larghezza 1/3
    col12, col13, col14 = st.columns([4.5,9,4.5])  
    
    with col12:
    
        st.metric("📈 Prezzo medio a notte (€)", f"{kpis['prezzo_medio_notte']:,.0f}")
        st.metric("📈 Prezzo pulizie (€)", f"{kpis['prezzo_pulizie']:,.0f}")
        st.metric("📈 Valore medio prenotazione (€)", f"{kpis['valore_medio_prenotazione']:,.0f}")
        st.metric("📈 Soggiorno medio ", f"{kpis['soggiorno_medio']:,.0f}")
        
    with col13:
        # Integrazione nella dashboard
        fig = visualizza_andamento_metriche(dati_filtrati, notti_disponibili_filtrate, start_date, end_date)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    


        col13_1, col13_2 = st.columns([2,2])
        
        with col13_1:
            st.metric("📈 Notti diponibili (€)", f"{kpis['notti_disponibili']:,.0f}")
            st.metric("📈 Notti libere (€)", f"{kpis['notti_libere']:,.0f}")
        with col13_2:
            st.metric("📈 Notti occupate (€)", f"{kpis['notti_occupate']:,.0f}")
            st.metric("📈 Tasso di occupazione (€)", f"{kpis['tasso_di_occupazione']:,.0f}")
            
        
    with col14:
        
        st.metric("📈 Margine medio a notte (€)", f"{kpis['margine_medio_notte']:,.0f}")
        st.metric("📈 Margine pulizie per soggiorno (€)", f"{kpis['margine_medio_pulizie']:,.0f}")
        st.metric("📈 Margine medio per prenotazione (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")
         


    



   
    
    
    


############## Funzione per creare un grafico ad anello compatto    #############   

def create_donut_chart(totale, kpi):
    
    

    """
    Crea un grafico ad anello compatto che mostra la percentuale del kpi passato sul totale
    
    
    """
    
    
    # Calcola la percentuale rispetto al totale
    percentuale = (kpi / totale) * 100

    # Dati per il grafico
    labels = ['Kpi', 'Altro']
    values = [kpi, totale - kpi]

    # Creazione del grafico
    fig = go.Figure(
        data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            textinfo='none',  # Rimuove le etichette standard
            marker=dict(colors=['#1f77b4', '#d3d3d3'])  # Colori del grafico
        )]
    )

    # Personalizzazione del layout
    fig.update_layout(
        annotations=[
            {
                "font": {"size": 20},
                "showarrow": False,
                "text": f"{percentuale:.0f}%",  # Mostra la percentuale al centro
                "x": 0.1,
                "y": 0.5
            }
        ],
        showlegend=False,  # Nasconde la legenda
        margin=dict(t=0, b=0, l=0, r=0),  # Rimuove i margini
        height=40,  # Altezza compatta
        width=40,   # Larghezza compatta
    )

    return fig


def create_donut_chart1(totale, kpi):
    
    

    """
    Crea un grafico ad anello compatto che mostra la percentuale del kpi passato sul totale
    
    
    """
    
    
    # Calcola la percentuale rispetto al totale
    percentuale = (kpi / totale) * 100

    # Dati per il grafico
    labels = ['Kpi', 'Altro']
    values = [kpi, totale - kpi]

    # Creazione del grafico
    fig = go.Figure(
        data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            textinfo='none',  # Rimuove le etichette standard
            marker=dict(colors=['#1f77b4', '#d3d3d3'])  # Colori del grafico
        )]
    )

    # Personalizzazione del layout
    fig.update_layout(
        annotations=[
            {
                "font": {"size": 20},
                "showarrow": False,
                "text": f"{percentuale:.0f}%",  # Mostra la percentuale al centro
                "x": 0.5,
                "y": 0.5
            }
        ],
        showlegend=False,  # Nasconde la legenda
        margin=dict(t=0, b=0, l=0, r=0),  # Rimuove i margini
        height=120,  # Altezza compatta
        width=120,   # Larghezza compatta
    )

    return fig




def create_donut_chart2(totale, kpi):
    
    

    """
    Crea un grafico ad anello compatto che mostra la percentuale del kpi passato sul totale
    
    
    """
    
    
    # Calcola la percentuale rispetto al totale
    percentuale = (kpi / totale) * 100

    # Dati per il grafico
    labels = ['Kpi', 'Altro']
    values = [kpi, totale - kpi]

    # Creazione del grafico
    fig = go.Figure(
        data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            textinfo='none',  # Rimuove le etichette standard
            marker=dict(colors=['#1f77b4', '#d3d3d3'])  # Colori del grafico
        )]
    )

    # Personalizzazione del layout
    fig.update_layout(
        annotations=[
            {
                "font": {"size": 15},
                "showarrow": False,
                "text": f"{percentuale:.0f}%",  # Mostra la percentuale al centro
                "x": 0.5,
                "y": 0.5
            }
        ],
        showlegend=False,  # Nasconde la legenda
        margin=dict(t=0, b=0, l=0, r=0),  # Rimuove i margini
        height=50,  # Altezza compatta
        width=50,   # Larghezza compatta
    )

    return fig




def visualizza_andamento_metriche(dati_filtrati, notti_disponibili_filtrate, start_date, end_date):
    """
    Crea un grafico a linee curve che confronta il tasso di occupazione,
    il valore medio prenotazione, il prezzo medio a notte, il margine medio a notte,
    e il margine medio per prenotazione.

    Parametri:
        dati_filtrati (DataFrame): Un DataFrame contenente i dati filtrati,
                                   con colonne necessarie per il calcolo delle metriche.
        start_date (datetime.date): Data di inizio filtro.
        end_date (datetime.date): Data di fine filtro.

    Output:
        Ritorna una figura Plotly che rappresenta l'andamento delle metriche nel tempo.
    """
   

    # Calcola metriche richieste
    dati_filtrati['Tasso di Occupazione'] = dati_filtrati['Notti Occupate'] / notti_disponibili_filtrate['Notti Disponibili'] * 100
    dati_filtrati['Valore Prenotazione'] = dati_filtrati['ricavi_totali']
    dati_filtrati['Prezzo Medio Notte'] = dati_filtrati['ricavi_totali'] / dati_filtrati['Notti Occupate']
    dati_filtrati['Margine Medio Notte'] = dati_filtrati['marginalità_totale'] / dati_filtrati['Notti Occupate']
    dati_filtrati['Margine Prenotazione'] = dati_filtrati['marginalità_totale']

    # Determina la scala temporale
    delta = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days
    if delta > 60:
        freq = 'M'  # Mensile
        label = 'Mese'
    elif delta > 15:
        freq = '2W'  # Ogni 15 giorni
        label = 'Quindicina'
    else:
        freq = '3D'  # Ogni 3 giorni
        label = 'Ogni 3 giorni'

    # Raggruppa i dati
    dati_filtrati['Periodo'] = dati_filtrati['Data Check-In'].dt.to_period(freq).dt.start_time
    grouped_data = dati_filtrati.groupby('Periodo').agg({
        'Tasso di Occupazione': 'mean',
        'Valore Prenotazione': 'mean',
        'Prezzo Medio Notte': 'mean',
        'Margine Medio Notte': 'mean',
        'Margine Prenotazione': 'mean'
    }).reset_index()

    # Trasforma i dati in formato lungo
    dati_melted = grouped_data.melt(
        id_vars=['Periodo'],
        value_vars=[
            'Tasso di Occupazione',
            'Valore Prenotazione',
            'Prezzo Medio Notte',
            'Margine Medio Notte',
            'Margine Prenotazione'
        ],
        var_name='Metrica',
        value_name='Valore'
    )

    # Crea il grafico
    fig = px.line(
        dati_melted,
        x='Periodo',
        y='Valore',
        color='Metrica',
        markers=True,
        line_shape='spline',
        title="",
        labels={'Periodo': label, 'Valore': 'Valore', 'Metrica': 'Metrica'}
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        hovermode="x unified",
        showlegend=False,  # Nasconde la legenda
        height=400,
        width=800,
        margin=dict(l=10, r=10, t=40, b=20)
    )

    return fig



####################  grafico andamento dei ricavi ####################



def visualizza_andamento_ricavi(dati_filtrati, colonne_da_visualizzare):
    """
    Crea un grafico a linee per visualizzare l'andamento di diverse metriche nel tempo.

    Parametri:
        dati_filtrati (DataFrame): Un DataFrame contenente i dati filtrati,
                                   con una colonna 'Data Check-In' e altre colonne numeriche da visualizzare.
        colonne_da_visualizzare (list): Lista delle colonne da mostrare nel grafico.

    Output:
        Ritorna una figura Plotly che rappresenta l'andamento delle metriche nel tempo.
    """
    if dati_filtrati.empty:
        st.warning("Nessun dato disponibile per creare il grafico.")
        return None

    # Assicura che 'Data Check-In' sia in formato datetime
    dati_filtrati['Data Check-In'] = pd.to_datetime(dati_filtrati['Data Check-In'], errors='coerce')
    dati_filtrati = dati_filtrati.dropna(subset=['Data Check-In'])

    # Raggruppa per mese, sommando le colonne selezionate
    dati_gruppati = dati_filtrati.groupby(dati_filtrati['Data Check-In'].dt.to_period('M')).agg({
        col: 'sum' for col in colonne_da_visualizzare
    }).reset_index()

    # Converti il periodo in datetime per il grafico
    dati_gruppati['Data'] = dati_gruppati['Data Check-In'].dt.to_timestamp()

    # Crea il grafico con le colonne specificate
    fig = px.line(
        dati_gruppati,
        x='Data',
        y=colonne_da_visualizzare,
        title="",
        labels={'value': 'Ricavi (€)', 'Data': 'Mese'},
        markers=True,
        line_shape="spline"  # Smussatura linee
    )

    # Personalizzazione del layout
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
        height=300,  # Altezza compatta
        width=300,   # Larghezza compatta
        hovermode="x unified"
    )

    return fig


####################  grafico a barre ricavi/commissioni   ####################

def crea_grafico_barre(df, ricavi_colonna, commissioni_colonna, marginalita_colonna, start_date, end_date):
    """
    Crea un grafico a barre che confronta ricavi totali, commissioni totali e marginalità totale,
    adattando l'asse X alla scala temporale selezionata (mese, 15 giorni, 3 giorni).

    Parametri:
        df (pd.DataFrame): Il DataFrame contenente i dati.
        ricavi_colonna (str): Nome della colonna dei ricavi totali.
        commissioni_colonna (str): Nome della colonna delle commissioni totali.
        marginalita_colonna (str): Nome della colonna della marginalità totale.
        start_date (datetime.date): Data di inizio filtro.
        end_date (datetime.date): Data di fine filtro.

    Ritorna:
        None: Il grafico viene visualizzato direttamente nella dashboard.
    """
    # Controlla se le colonne esistono
    if ricavi_colonna not in df.columns or commissioni_colonna not in df.columns or marginalita_colonna not in df.columns:
        raise ValueError(f"Le colonne {ricavi_colonna}, {commissioni_colonna} e/o {marginalita_colonna} non esistono nel DataFrame.")

    # Determina la scala temporale basata sulla durata del periodo selezionato
    delta = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days
    if delta > 60:
        freq = 'M'  # Mensile
        label = 'Mese'
    elif delta > 15:
        freq = '2W'  # Ogni 15 giorni
        label = 'Quindicina'
    else:
        freq = '3D'  # Ogni 3 giorni
        label = 'Ogni 3 giorni'

    # Raggruppa i dati per il periodo scelto
    df['Data Check-In'] = pd.to_datetime(df['Data Check-In'])
    df['Periodo'] = df['Data Check-In'].dt.to_period(freq).dt.start_time
    grouped_df = df.groupby('Periodo').agg({
        ricavi_colonna: 'sum',
        commissioni_colonna: 'sum',
        marginalita_colonna: 'sum'
    }).reset_index()

    # Trasforma i dati in formato lungo per il grafico
    df_melted = grouped_df.melt(
        id_vars=['Periodo'],
        value_vars=[ricavi_colonna, commissioni_colonna, marginalita_colonna],
        var_name='Categoria',
        value_name='Valore'
    )

    # Creazione del grafico a barre
    fig = px.bar(
        df_melted,
        x="Periodo",
        y="Valore",
        color="Categoria",
        barmode="group",
        text="Valore",
        title="",
        labels={"Periodo": label, "Valore": "Valore (€)", "Categoria": "Tipologia"}
    )

    # Personalizzazione del layout
    fig.update_traces(
        texttemplate='%{text:.2f} €',
        textposition='outside'
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        showlegend=True,
        height=300,  # Altezza personalizzata
        width=800,   # Larghezza personalizzata
        margin=dict(l=10, r=10, t=40, b=20)  # Margini del grafico
    )

    # Visualizza il grafico nella dashboard
    st.plotly_chart(fig, use_container_width=True)




# Main
menu = st.sidebar.selectbox("Menù", ["Carica File", "Dashboard", "Dashboard Propietari"])

if menu == "Carica File":
    upload_file()
elif menu == "Dashboard":
    render_dashboard()
elif menu == "Dashboard Propietari":
    dashboard_proprietari()

    


