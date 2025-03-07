import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
import ast
from streamlit_folium import st_folium


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



def localizzatore(file_path, data):
    """
    Associa a ogni immobile la posizione.
    """
    # Legge il Foglio 2 del file Excel
    file_posizioni = pd.read_excel(file_path, sheet_name=2)
    
    # Lista per salvare le informazioni di ogni immobile
    lista_posizione = []

    # Itera sulle righe del file e crea un dizionario per ogni riga
    for index, row in file_posizioni.iterrows():
        d = {
            'nome_immobile': row[0],            # Nome dell'appartamento nella prima colonna
            'id_immobile': row[1],              # ID dell'appartamento nella seconda colonna
            'zona': row[2],                     # Zona nella terza colonna
            'coordinate_zona': row[3],          # Coordinate della zona nella quarta colonna
            'indirizzo': row[4],                # Indirizzo nella quinta colonna
            'coordinate_indirizzo': row[5]      # Coordinate dell'indirizzo nella sesta colonna
        }
        lista_posizione.append(d)
    
    # Converti l'elenco di dizionari in un DataFrame
    df_posizione = pd.DataFrame(lista_posizione)

    # Unisci i DataFrame specificando le colonne chiave diverse
    data = data.merge(df_posizione, left_on='ID Appartamento', right_on='id_immobile', how='left')

    return data

def carica_elaboara_spese(file_path):
    

    # Legge il Foglio 4 del file Excel
    file_spese = pd.read_excel(
        file_path, 
        sheet_name=3,
        usecols="B,D,E,F,I,J,K",
        dtype=str,
        engine="openpyxl"
    )
    file_spese.columns = [
        'Codice',
        'Descrizione',
        'Importo',
        'Importo Totale',
        'data',
        'Settore di spesa',
        'Immobile associato alla spesa'
    ]
    
    # Trasforma la colonna "data" in formato datetime
    file_spese['data'] = pd.to_datetime(file_spese['data'], errors='coerce')
    
    # Elimina le righe in cui:
    # - la colonna "Importo Totale" è nulla
    # - e la colonna "Codice" ha un valore diverso da "59.01.01"
    file_spese = file_spese[~(file_spese['Importo Totale'].isnull() & (file_spese['Codice'] != '59.01.01'))]
    
    # Resetta l'indice per garantire che le righe siano consecutive
    file_spese.reset_index(drop=True, inplace=True)
    
    # Per le righe IVA (Codice "59.01.01") che non hanno una data, assegna la data della riga precedente
    iva_mask = (file_spese['Codice'] == '59.01.01') & (file_spese['data'].isnull())
    file_spese.loc[iva_mask, 'data'] = file_spese['data'].shift(1)
    
    # Per le righe IVA (Codice "59.01.01"), assegna il Settore di spesa della riga precedente
    file_spese.loc[file_spese['Codice'] == '59.01.01', 'Settore di spesa'] = file_spese['Settore di spesa'].shift(1)
    
    return pd.DataFrame(file_spese)







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


def load_and_preprocess_input_data(uploaded_file):
    data = pd.read_excel(
        uploaded_file,
        sheet_name=0,
        usecols="A,B,C,D,E",
        dtype=str,
        engine="openpyxl"
    )

    data.columns = [
        'Nome Appartamento',
        'ID Appartamento',
        'Comune',
        'Zona',
        'coordinate'
        
    ]

    data = data.dropna(subset=['ID Appartamento'])
    return pd.DataFrame(data)




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
        'notti_libere': notti_libere,
        'numero_prenotazioni': numero_prenotazioni
    }




def eleboratore_spese(df):
    """
    Per ogni spesa (riga in cui il codice non è "59.01.01"), calcola l'importo netto
    sottraendo l'importo IVA (presumibilmente nella riga immediatamente successiva, 
    colonna 'y') dall'importo (colonna 'x'). Inoltre, per ogni riga IVA (codice "59.01.01"),
    assegna il settore di spesa della riga precedente nella nuova colonna 'settore_spesa'.
    
    Parametri:
      - df: DataFrame contenente le colonne 'x', 'y', 'settore' e 'codice'.
    
    Ritorna:
      - df: DataFrame aggiornato con la colonna 'importo_netto' per le spese e la colonna
            'settore_spesa' assegnata per le righe IVA.
    """
    

    # Maschera per identificare le righe delle spese (non IVA)
    expense_mask = df['Codice'] != "59.01.01"
    
    # Assicurati che le colonne siano di tipo numerico
    df['Importo Totale'] = pd.to_numeric(df['Importo Totale'], errors='coerce')
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce')

    # Calcola l'importo netto per le spese (sottraendo l'importo IVA dalla spesa)
    # Si assume che la riga successiva contenga l'importo dell'IVA (colonna y)
    df.loc[expense_mask, 'importo_netto'] = df.loc[expense_mask, 'Importo Totale'].astype(float) - df['Importo'].shift(-1).astype(float)
    
    # Maschera per le righe IVA (codice "59.01.01")
    vat_mask = df['Codice'] == "59.01.01"
    
    # Assegna alla riga IVA il settore della spesa dalla riga precedente
    df.loc[vat_mask, 'Settore di spesa'] = df['Settore di spesa'].shift(1)

    # Converti in numerico le colonne, in caso contengano stringhe o formati non numerici
    df['Importo Totale'] = pd.to_numeric(df['Importo Totale'], errors='coerce')
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce')

    # Filtra le righe spesa (non IVA)
    df_spesa = df[df['Codice'] != "59.01.01"]
    totali_spesa = df_spesa.groupby("Settore di spesa")['Importo Totale'].sum().reset_index()
    totali_spesa.rename(columns={'Importo Totale': 'Totale Spese'}, inplace=True)

    # Filtra le righe IVA
    df_iva = df[df['Codice'] == "59.01.01"]
    totali_iva = df_iva.groupby("Settore di spesa")['Importo'].sum().reset_index()
    totali_iva.rename(columns={'Importo': 'Totale IVA'}, inplace=True)

    # Unisci i risultati per settore
    totali = pd.merge(totali_spesa, totali_iva, on="Settore di spesa", how="outer").fillna(0)

    totali['totale_netto'] = totali['Totale Spese'] - totali['Totale IVA']

    # Calcola il totale IVA complessivo
    totale_iva_complessivo = totali_iva['Totale IVA'].sum()

    totale_spese_netto = totali['totale_netto'].sum()
    totale_spese_lordo = totali['Totale Spese'].sum()

    # Crea un nuovo DataFrame con i totali ottenuti
    totali_df = pd.DataFrame({
        'Totale_Spese_netto': [totale_spese_netto],
        'Totale_Spese_lordo': [totale_spese_lordo],
        'Totale_IVA': [totale_iva_complessivo]
    })

    return df, totali, totali_df


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

    #Applica stili personalizzati alla dashboard.
    st.markdown(
        """
        <style>
        /* Stili esistenti della dashboard (se presenti) */

        /* Stile per l'icona info */
        .info-icon {
            font-size: 12px;
            color:rgb(51, 255, 0);
            cursor: pointer;
            margin-left: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )



############## Funzioni per visualizzare le dashboard    #############   


def render_dashboard():
    """
    Visualizza la dashboard con KPI, grafici e calcolo dinamico delle notti disponibili.
    """
    inject_custom_css()
    st.title("📊 Propertize")

    

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
    data = localizzatore(file_path, data)
    
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
            "Visualizza Appartamenti",
            ("Tutti gli Appartamenti", "Singolo Appartamento", "Multipli Appartamenti"),
            key="view_option_filter"
        )
        immobili_selezionati = None
        if view_option == "Singolo Appartamento":
            immobili_selezionati = st.selectbox(
                "Seleziona Appartamento",
                data['Nome Appartamento'].unique(),
                key="appartamento_filter"
            )
        elif view_option == "Multipli Appartamenti":
            immobili_selezionati = st.multiselect(
                "Seleziona uno o più Appartamenti",
                data['Nome Appartamento'].unique(),
                key="appartamento_filter_multi"
            )
        
        # Filtro per zona
        zona_option = st.radio(
            "Visualizza Zone",
            ("Tutte le Zone", "Singola Zona", "Multipla Zona"),
            key="zona_option_filter"
        )
        zona_selezionata = None
        if zona_option == "Singola Zona":
            zona_selezionata = st.selectbox(
                "Seleziona Zona",
                list(data['zona'].unique()),
                key="zona_filter"
            )
        elif zona_option == "Multipla Zona":
            zona_selezionata = st.multiselect(
                "Seleziona una o più Zone",
                list(data['zona'].unique()),
                key="zona_filter_multi"
            )
        
        # Filtraggio dei dati principali in base alle date
        dati_filtrati = data[
            (data['Data Check-In'] >= pd.Timestamp(start_date)) &
            (data['Data Check-In'] <= pd.Timestamp(end_date))
        ]
        
        # Filtra in base agli immobili
        if view_option != "Tutti gli Appartamenti" and immobili_selezionati:
            if view_option == "Singolo Appartamento":
                dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'] == immobili_selezionati]
            else:  # Multipli Appartamenti
                dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'].isin(immobili_selezionati)]
        
        # Filtra in base alla zona
        if zona_option != "Tutte le Zone" and zona_selezionata:
            if zona_option == "Singola Zona":
                dati_filtrati = dati_filtrati[dati_filtrati['zona'] == zona_selezionata]
            else:  # Multipla Zona
                dati_filtrati = dati_filtrati[dati_filtrati['zona'].isin(zona_selezionata)]
        
        # Assicurati che le colonne calcolate siano presenti nel DataFrame filtrato
        if 'ricavi_totali' not in dati_filtrati.columns:
            dati_filtrati['ricavi_totali'] = (
                dati_filtrati['Ricavi Locazione'] -
                dati_filtrati['IVA Provvigioni PM'] -
                dati_filtrati['Commissioni OTA'] * 0.22 +
                dati_filtrati['Ricavi Pulizie'] / 1.22
            )
        if 'commissioni_totali' not in dati_filtrati.columns:
            dati_filtrati['commissioni_totali'] = (
                dati_filtrati['Commissioni OTA'] / 1.22 +
                dati_filtrati['Commissioni ITW Nette']
            )
        
        # Calcola le notti disponibili
        notti_disponibili_df = calcola_notti_disponibili(file_path, start_date, end_date)
        
        # Filtra le notti disponibili in base al filtro appartamento
        if view_option != "Tutti gli Appartamenti" and immobili_selezionati:
            if view_option == "Singolo Appartamento":
                notti_disponibili_filtrate = notti_disponibili_df[
                    notti_disponibili_df['Appartamento'] == immobili_selezionati
                ]
            else:
                notti_disponibili_filtrate = notti_disponibili_df[
                    notti_disponibili_df['Appartamento'].isin(immobili_selezionati)
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
        st.divider()
        
        col3, col4, col5 = st.columns([1,1,1])

        with col3:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col3:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_totale"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col3:
                st.metric("📊 Marginalità Totale (€)", f"{kpis['marginalità_totale']:,.2f}")

        with col4:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col4:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_locazioni"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col4:
                st.metric("📊 Marginalità Locazioni (€)", f"{kpis['marginalità_locazioni']:,.2f}")

        with col5:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col5:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_pulizie"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col5:
                st.metric("📊 Marginalità Pulizie (€)", f"{kpis['marginalità_pulizie']:,.2f}")

        col03, col04, col05 = st.columns([1,1,1])

        with col03:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col03:
                totale = kpis["ricavi_totali"]
                kpi = kpis["commissioni_proprietari"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col03:
                st.metric("📊 Commissioni Proprietari (€)", f"{kpis['commissioni_proprietari']:,.2f}")

        with col04:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col04:
                totale = kpis["ricavi_totali"]
                kpi = kpis["commissioni_ota"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col04:
                st.metric("📊 Commissioni OTA (€)", f"{kpis['commissioni_ota']:,.2f}")

        with col05:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col05:
                totale = kpis["ricavi_totali"]
                kpi = kpis["commissioni_itw"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col05:
                st.metric("📊 Commissioni ITW (€)", f"{kpis['commissioni_itw']:,.2f}")


        
        
    
           


    
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
         
    
def dashboard_spese():
    
    inject_custom_css()
    st.title("📊 Analisi delle spese")

    

    # Verifica se i dati principali sono disponibili
    if 'data' not in st.session_state or st.session_state['data'] is None:
        st.error("Nessun dato disponibile. Torna alla pagina di caricamento.")
        return

    # Verifica se il file è disponibile per il calcolo delle notti disponibili
    if 'uploaded_file' not in st.session_state:
        st.error("Nessun file caricato per il calcolo delle notti disponibili.")
        return

    # Verifica se il file è disponibile per il calcolo delle notti disponibili
    if 'spese' not in st.session_state:
        st.error("Nessun dato relativo alle spese caricato.")
        return


    file_path = st.session_state['uploaded_file']
    data = st.session_state['data']
    data = localizzatore(file_path, data)
    spese = st.session_state['spese']
    st.write(spese)

    # Sezione Filtri
    # Sezione Filtri
    with st.sidebar.expander("🔍 Filtro Dati"):
        st.markdown("### Filtra i dati")
        
        # Filtro per intervallo di date (colonna "data" del dataframe spese)
        start_date = st.date_input(
            "Data Inizio",
            spese['data'].min().date(),
            key="start_date_filter"
        )
        end_date = st.date_input(
            "Data Fine",
            spese['data'].max().date(),
            key="end_date_filter"
        )
        
        # Filtraggio dei dati principali in base alle date
        dati_filtrati = spese[
            (spese['data'] >= pd.Timestamp(start_date)) &
            (spese['data'] <= pd.Timestamp(end_date))
        ]
        
        # Salva i dati filtrati nel session state
        st.session_state['filtered_data'] = dati_filtrati



    # Usa i dati filtrati se disponibili
    if 'filtered_data' in st.session_state:
        dati_filtrati = st.session_state['filtered_data']  
        

    # Calcola le notti disponibili
    notti_disponibili_filtrate = calcola_notti_disponibili(file_path, start_date, end_date)
    st.session_state['filtered_notti_disponibili'] = notti_disponibili_filtrate

    if 'filtered_notti_disponibili' in st.session_state:
        notti_disponibili_filtrate = st.session_state['filtered_notti_disponibili']
    

    st.write(dati_filtrati)
    kpis_spese, totali_spese_settore, totale_spese = eleboratore_spese(dati_filtrati)
    
    kpis = calculate_kpis(data, notti_disponibili_filtrate)
    
    st.write(kpis_spese)
    st.write(totali_spese_settore)


    col1, col2 = st.columns([2,4])
    with col1:
        #grafico ad anello + scritta + bottone info 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = totale_spese['Totale_Spese_netto']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Spese Totali (€)", f"{totale_spese['Totale_Spese_netto'].iloc[0]:,.2f}") 
        # bottone info
        with info_col:
            st.markdown(
            '<span class="info-icon" title="I Ricavi Totali rappresentano la somma complessiva dei ricavi generati dall\'immobile, ottenuti sommando i ricavi da locazione e quelli da servizi aggiuntivi. Questa metrica consente di valutare la performance economica globale dell\'immobile.">ℹ️</span>',
             unsafe_allow_html=True
        )

        #grafico ad anello + scritta + bottone info 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = totale_spese['Totale_Spese_netto']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="grafico2")  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Spese Totali (€)", f"{totale_spese['Totale_Spese_netto'].iloc[0]:,.2f}") 
        # bottone info
        with info_col:
            st.markdown(
            '<span class="info-icon" title="I Ricavi Totali rappresentano la somma complessiva dei ricavi generati dall\'immobile, ottenuti sommando i ricavi da locazione e quelli da servizi aggiuntivi. Questa metrica consente di valutare la performance economica globale dell\'immobile.">ℹ️</span>',
             unsafe_allow_html=True
        )

        #grafico ad anello + scritta + bottone info 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = totale_spese['Totale_Spese_netto']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="grafico3")  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Spese Totali (€)", f"{totale_spese['Totale_Spese_netto'].iloc[0]:,.2f}") 
        # bottone info
        with info_col:
            st.markdown(
            '<span class="info-icon" title="I Ricavi Totali rappresentano la somma complessiva dei ricavi generati dall\'immobile, ottenuti sommando i ricavi da locazione e quelli da servizi aggiuntivi. Questa metrica consente di valutare la performance economica globale dell\'immobile.">ℹ️</span>',
             unsafe_allow_html=True
        )

    with col2:
        colonne = ['ricavi_totali', 'commissioni_totali', 'marginalità_totale']
        fig = visualizza_andamento_ricavi(data, colonne)
        st.plotly_chart(fig)
        st.divider()

    col01, col02, col03, col04, col05 = st.columns([1,1,1,1,1])
    with col01:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        with col01:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_proprietari"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col01")  # Mantieni larghezza compatta
        with col01:
            st.metric("📊 Commissioni Proprietari (€)", f"{kpis['commissioni_proprietari']:,.2f}")
    with col02:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        with col02:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_proprietari"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col02")  # Mantieni larghezza compatta
        with col02:
            st.metric("📊 Commissioni Proprietari (€)", f"{kpis['commissioni_proprietari']:,.2f}")


    with col03:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        with col03:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_proprietari"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col03")  # Mantieni larghezza compatta
        with col03:
            st.metric("📊 Commissioni Proprietari (€)", f"{kpis['commissioni_proprietari']:,.2f}")

    with col04:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        with col04:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_ota"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col04")  # Mantieni larghezza compatta
        with col04:
            st.metric("📊 Commissioni OTA (€)", f"{kpis['commissioni_ota']:,.2f}")

    with col05:
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        with col05:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_itw"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col05")  # Mantieni larghezza compatta
        with col05:
            st.metric("📊 Commissioni ITW (€)", f"{kpis['commissioni_itw']:,.2f}")

    col001, col002 = st.columns([4,2])
    with col001:
        fig = create_horizontal_bar_chart(totali_spese_settore, "Settore di spesa", "totale_netto")
        st.plotly_chart(fig)







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
    data = localizzatore(file_path, data)
    

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
            "Visualizza Appartamenti",
            ("Tutti gli Appartamenti", "Singolo Appartamento", "Multipli Appartamenti"),
            key="view_option_filter"
        )
        immobili_selezionati = None
        if view_option == "Singolo Appartamento":
            immobili_selezionati = st.selectbox(
                "Seleziona Appartamento",
                data['Nome Appartamento'].unique(),
                key="appartamento_filter"
            )
        elif view_option == "Multipli Appartamenti":
            immobili_selezionati = st.multiselect(
                "Seleziona uno o più Appartamenti",
                data['Nome Appartamento'].unique(),
                key="appartamento_filter_multi"
            )
        
        # Filtro per zona
        zona_option = st.radio(
            "Visualizza Zone",
            ("Tutte le Zone", "Singola Zona", "Multipla Zona"),
            key="zona_option_filter"
        )
        zona_selezionata = None
        if zona_option == "Singola Zona":
            zona_selezionata = st.selectbox(
                "Seleziona Zona",
                list(data['zona'].unique()),
                key="zona_filter"
            )
        elif zona_option == "Multipla Zona":
            zona_selezionata = st.multiselect(
                "Seleziona una o più Zone",
                list(data['zona'].unique()),
                key="zona_filter_multi"
            )
        
        # Filtraggio dei dati principali in base alle date
        dati_filtrati = data[
            (data['Data Check-In'] >= pd.Timestamp(start_date)) &
            (data['Data Check-In'] <= pd.Timestamp(end_date))
        ]
        
        # Filtra in base agli immobili
        if view_option != "Tutti gli Appartamenti" and immobili_selezionati:
            if view_option == "Singolo Appartamento":
                dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'] == immobili_selezionati]
            else:  # Multipli Appartamenti
                dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'].isin(immobili_selezionati)]
        
        # Filtra in base alla zona
        if zona_option != "Tutte le Zone" and zona_selezionata:
            if zona_option == "Singola Zona":
                dati_filtrati = dati_filtrati[dati_filtrati['zona'] == zona_selezionata]
            else:  # Multipla Zona
                dati_filtrati = dati_filtrati[dati_filtrati['zona'].isin(zona_selezionata)]
        
        # Assicurati che le colonne calcolate siano presenti nel DataFrame filtrato
        if 'ricavi_totali' not in dati_filtrati.columns:
            dati_filtrati['ricavi_totali'] = (
                dati_filtrati['Ricavi Locazione'] -
                dati_filtrati['IVA Provvigioni PM'] -
                dati_filtrati['Commissioni OTA'] * 0.22 +
                dati_filtrati['Ricavi Pulizie'] / 1.22
            )
        if 'commissioni_totali' not in dati_filtrati.columns:
            dati_filtrati['commissioni_totali'] = (
                dati_filtrati['Commissioni OTA'] / 1.22 +
                dati_filtrati['Commissioni ITW Nette']
            )
        
        # Calcola le notti disponibili
        notti_disponibili_df = calcola_notti_disponibili(file_path, start_date, end_date)
        
        # Filtra le notti disponibili in base al filtro appartamento
        if view_option != "Tutti gli Appartamenti" and immobili_selezionati:
            if view_option == "Singolo Appartamento":
                notti_disponibili_filtrate = notti_disponibili_df[
                    notti_disponibili_df['Appartamento'] == immobili_selezionati
                ]
            else:
                notti_disponibili_filtrate = notti_disponibili_df[
                    notti_disponibili_df['Appartamento'].isin(immobili_selezionati)
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


    
    col1, col2 = st.columns([2,4])  # Tre colonne di uguale larghezza
    
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
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_pulizie"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Ricavi Pulizie (€)", f"{kpis['totale_ricavi_pulizie']:,.2f}") 
        # bottone info
        with info_col:
            st.markdown(
            '<span class="info-icon" title="I Ricavi Totali rappresentano la somma complessiva dei ricavi generati dall\'immobile, ottenuti sommando i ricavi da locazione e quelli da servizi aggiuntivi. Questa metrica consente di valutare la performance economica globale dell\'immobile.">ℹ️</span>',
             unsafe_allow_html=True
        )
            
            
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_commissioni"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("📈 Totale Commissioni (€)", f"{kpis['totale_commissioni']:,.2f}")
            
        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_ota"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Commissioni OTA (€)", f"{kpis['commissioni_ota']:,.2f}")

        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_proprietari"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Commissioni Proprietari (€)", f"{kpis['commissioni_proprietari']:,.2f}") 

        #grafico ad anello 
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_itw"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("🧹 Commissioni ITW (€)", f"{kpis['commissioni_itw']:,.2f}") 
        



    with col2:
        colonne = ['ricavi_totali', 'commissioni_totali', 'marginalità_totale']
        fig = visualizza_andamento_ricavi(dati_filtrati, colonne)
        st.plotly_chart(fig)
        st.divider()
        
        col3, col4, col5 = st.columns([1,1,1])

        with col3:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col3:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_totale"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col3:
                st.metric("📊 Marginalità Totale (€)", f"{kpis['marginalità_totale']:,.2f}")

        with col4:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col4:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_locazioni"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col4:
                st.metric("📊 Marginalità Locazioni (€)", f"{kpis['marginalità_locazioni']:,.2f}")

        with col5:
            #grafico ad anello 
            # Sub-layout per centrare il grafico e il dato
            with col5:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_pulizie"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col5:
                st.metric("📊 Marginalità Pulizie (€)", f"{kpis['marginalità_pulizie']:,.2f}")

    st.divider()

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
         


    



   
    
    
    
def dashboard_analisi_performance():
    inject_custom_css()
    st.title("📊 Analisi Performance ")

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
    data = localizzatore(file_path, data)

    # SEZIONE FILTRI (in sidebar)
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
        
        # Nuovo filtro per Modalità Confronto
        confronto_mode = st.radio(
            "Modalità Confronto",
            ("Nessun Confronto", "Confronto Immobili", "Confronto Zone"),
            key="confronto_mode"
        )
        
        # Filtro per appartamento
        view_option = st.radio(
            "Visualizza Appartamenti",
            ("Tutti gli Appartamenti", "Singolo Appartamento", "Multipli Appartamenti"),
            key="view_option_filter"
        )
        immobili_selezionati = None
        if confronto_mode == "Confronto Immobili":
            # Se confronto attivo, fornisce la possibilità di selezionare due immobili
            immobili_selezionati = st.multiselect(
                "Seleziona due Appartamenti da confrontare",
                data['Nome Appartamento'].unique(),
                key="confronto_immobili"
            )
        else:
            if view_option == "Singolo Appartamento":
                immobili_selezionati = st.selectbox(
                    "Seleziona Appartamento",
                    data['Nome Appartamento'].unique(),
                    key="appartamento_filter"
                )
            elif view_option == "Multipli Appartamenti":
                immobili_selezionati = st.multiselect(
                    "Seleziona uno o più Appartamenti",
                    data['Nome Appartamento'].unique(),
                    key="appartamento_filter_multi"
                )
        
        # Filtro per zona
        zona_option = st.radio(
            "Visualizza Zone",
            ("Tutte le Zone", "Singola Zona", "Multipla Zona"),
            key="zona_option_filter"
        )
        zona_selezionata = None
        if confronto_mode == "Confronto Zone":
            zona_selezionata = st.multiselect(
                "Seleziona due Zone da confrontare",
                list(data['zona'].unique()),
                key="confronto_zone"
            )
        else:
            if zona_option == "Singola Zona":
                zona_selezionata = st.selectbox(
                    "Seleziona Zona",
                    list(data['zona'].unique()),
                    key="zona_filter"
                )
            elif zona_option == "Multipla Zona":
                zona_selezionata = st.multiselect(
                    "Seleziona una o più Zone",
                    list(data['zona'].unique()),
                    key="zona_filter_multi"
                )
        
        # Filtraggio dei dati principali in base alle date
        dati_filtrati = data[
            (data['Data Check-In'] >= pd.Timestamp(start_date)) &
            (data['Data Check-In'] <= pd.Timestamp(end_date))
        ]
        # Se non si sta effettuando un confronto, applica i filtri sugli immobili e sulle zone
        if confronto_mode == "Nessun Confronto":
            if view_option != "Tutti gli Appartamenti" and immobili_selezionati:
                if view_option == "Singolo Appartamento":
                    dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'] == immobili_selezionati]
                else:
                    dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'].isin(immobili_selezionati)]
            if zona_option != "Tutte le Zone" and zona_selezionata:
                if zona_option == "Singola Zona":
                    dati_filtrati = dati_filtrati[dati_filtrati['zona'] == zona_selezionata]
                else:
                    dati_filtrati = dati_filtrati[dati_filtrati['zona'].isin(zona_selezionata)]
        # Non applichiamo ulteriori filtri se siamo in modalità confronto (si considerano l'intero dataset filtrato per date)

        # Assicurati che le colonne calcolate siano presenti nel DataFrame filtrato
        if 'ricavi_totali' not in dati_filtrati.columns:
            dati_filtrati['ricavi_totali'] = (
                dati_filtrati['Ricavi Locazione'] -
                dati_filtrati['IVA Provvigioni PM'] -
                dati_filtrati['Commissioni OTA'] * 0.22 +
                dati_filtrati['Ricavi Pulizie'] / 1.22
            )
        if 'commissioni_totali' not in dati_filtrati.columns:
            dati_filtrati['commissioni_totali'] = (
                dati_filtrati['Commissioni OTA'] / 1.22 +
                dati_filtrati['Commissioni ITW Nette']
            )
        
        # Calcola le notti disponibili
        notti_disponibili_df = calcola_notti_disponibili(file_path, start_date, end_date)
        if view_option != "Tutti gli Appartamenti" and immobili_selezionati and confronto_mode == "Nessun Confronto":
            if view_option == "Singolo Appartamento":
                notti_disponibili_filtrate = notti_disponibili_df[
                    notti_disponibili_df['Appartamento'] == immobili_selezionati
                ]
            else:
                notti_disponibili_filtrate = notti_disponibili_df[
                    notti_disponibili_df['Appartamento'].isin(immobili_selezionati)
                ]
        else:
            notti_disponibili_filtrate = notti_disponibili_df

        # Salva i dati filtrati nel session state
        st.session_state['filtered_data'] = dati_filtrati
        st.session_state['filtered_notti_disponibili'] = notti_disponibili_filtrate

    if 'filtered_data' in st.session_state:
        dati_filtrati = st.session_state['filtered_data']
    if 'filtered_notti_disponibili' in st.session_state:
        notti_disponibili_filtrate = st.session_state['filtered_notti_disponibili']

    # Se è attivo il confronto, elaboriamo e mostriamo i KPI dei due gruppi separatamente
    if confronto_mode == "Confronto Immobili":
        if immobili_selezionati and isinstance(immobili_selezionati, list) and len(immobili_selezionati) == 2:
            imm1, imm2 = immobili_selezionati[0], immobili_selezionati[1]
            dati1 = dati_filtrati[dati_filtrati['Nome Appartamento'] == imm1]
            dati2 = dati_filtrati[dati_filtrati['Nome Appartamento'] == imm2]
            notti1 = notti_disponibili_filtrate[notti_disponibili_filtrate['Appartamento'] == imm1]
            notti2 = notti_disponibili_filtrate[notti_disponibili_filtrate['Appartamento'] == imm2]
            kpis1 = calculate_kpis(dati1, notti1)
            kpis2 = calculate_kpis(dati2, notti2)
            st.subheader("Confronto Immobili")
            colA, colB = st.columns(2)
            with colA:
                st.subheader(imm1)
                st.metric("💰 Ricavi Totali (€)", f"{kpis1['ricavi_totali']:,.2f}")
                st.metric("📈 Ricavi Locazione (€)", f"{kpis1['totale_ricavi_locazione']:,.2f}")
                st.metric("🧹 Ricavi Pulizie (€)", f"{kpis1['totale_ricavi_pulizie']:,.2f}")
                st.metric("📈 Totale Commissioni (€)", f"{kpis1['totale_commissioni']:,.2f}")
                st.metric("🧹 Commissioni OTA (€)", f"{kpis1['commissioni_ota']:,.2f}")
                st.metric("🧹 Commissioni Proprietari (€)", f"{kpis1['commissioni_proprietari']:,.2f}")
                st.metric("🧹 Commissioni ITW (€)", f"{kpis1['commissioni_itw']:,.2f}")
            with colB:
                st.subheader(imm2)
                st.metric("💰 Ricavi Totali (€)", f"{kpis2['ricavi_totali']:,.2f}")
                
                st.metric("📈 Ricavi Locazione (€)", f"{kpis2['totale_ricavi_locazione']:,.2f}")
                st.metric("🧹 Ricavi Pulizie (€)", f"{kpis2['totale_ricavi_pulizie']:,.2f}")
                st.metric("📈 Totale Commissioni (€)", f"{kpis2['totale_commissioni']:,.2f}")
                st.metric("🧹 Commissioni OTA (€)", f"{kpis2['commissioni_ota']:,.2f}")
                st.metric("🧹 Commissioni Proprietari (€)", f"{kpis2['commissioni_proprietari']:,.2f}")
                st.metric("🧹 Commissioni ITW (€)", f"{kpis2['commissioni_itw']:,.2f}")
            return
        else:
            st.info("Seleziona esattamente due appartamenti per il confronto.")
            return

    elif confronto_mode == "Confronto Zone":
        if zona_selezionata and isinstance(zona_selezionata, list) and len(zona_selezionata) == 2:
            z1, z2 = zona_selezionata[0], zona_selezionata[1]
            dati1 = dati_filtrati[dati_filtrati['zona'] == z1]
            dati2 = dati_filtrati[dati_filtrati['zona'] == z2]
            notti1 = notti_disponibili_filtrate[dati_filtrati['zona'] == z1]
            notti2 = notti_disponibili_filtrate[dati_filtrati['zona'] == z2]
            kpis1 = calculate_kpis(dati1, notti1)
            kpis2 = calculate_kpis(dati2, notti2)
            st.subheader("Confronto Zone")
            colA, colB = st.columns(2)
            with colA:
                st.subheader(z1)
                st.metric("💰 Ricavi Totali (€)", f"{kpis1['ricavi_totali']:,.2f}")
                st.metric("📈 Ricavi Locazione (€)", f"{kpis1['totale_ricavi_locazione']:,.2f}")
                st.metric("🧹 Ricavi Pulizie (€)", f"{kpis1['totale_ricavi_pulizie']:,.2f}")
                st.metric("📈 Totale Commissioni (€)", f"{kpis1['totale_commissioni']:,.2f}")
                st.metric("🧹 Commissioni OTA (€)", f"{kpis1['commissioni_ota']:,.2f}")
                st.metric("🧹 Commissioni Proprietari (€)", f"{kpis1['commissioni_proprietari']:,.2f}")
                st.metric("🧹 Commissioni ITW (€)", f"{kpis1['commissioni_itw']:,.2f}")
            with colB:
                st.subheader(z2)
                st.metric("💰 Ricavi Totali (€)", f"{kpis2['ricavi_totali']:,.2f}")
                st.metric("📈 Ricavi Locazione (€)", f"{kpis2['totale_ricavi_locazione']:,.2f}")
                st.metric("🧹 Ricavi Pulizie (€)", f"{kpis2['totale_ricavi_pulizie']:,.2f}")
                st.metric("📈 Totale Commissioni (€)", f"{kpis2['totale_commissioni']:,.2f}")
                st.metric("🧹 Commissioni OTA (€)", f"{kpis2['commissioni_ota']:,.2f}")
                st.metric("🧹 Commissioni Proprietari (€)", f"{kpis2['commissioni_proprietari']:,.2f}")
                st.metric("🧹 Commissioni ITW (€)", f"{kpis2['commissioni_itw']:,.2f}")
            return
        else:
            st.info("Seleziona esattamente due zone per il confronto.")
            return

    # Se non è attivo il confronto (confronto_mode == "Nessun Confronto"), prosegui con la dashboard originale
    kpis = calculate_kpis(dati_filtrati, notti_disponibili_filtrate)



    # Creazione della colonna per la mappa

    #Visualizza una mappa interattiva con un marker per ogni appartamento.
    
    #Parametri:
      #- dati_filtrati: DataFrame contenente le colonne 'zona' e 'coordinate_indirizzo'
      #- zona_option: stringa che indica l'opzione scelta ("Tutte le Zone", "Singola Zona" o "Multipla Zona")
      #- zona_selezionata: se zona_option è "Singola Zona", una stringa; se "Multipla Zona", una lista di zone.

    
    col0, _ = st.columns([8, 1])
    with col0:
        if zona_option == "Tutte le Zone":
            # Visualizza marker per ogni appartamento in tutti i dati filtrati
            lat_list = []
            lon_list = []
            for idx, row in dati_filtrati.iterrows():
                coord = row['coordinate_indirizzo']
                if pd.isnull(coord) or (isinstance(coord, str) and coord.strip() == ""):
                    continue
                if isinstance(coord, str):
                    try:
                        coord = ast.literal_eval(coord)
                    except Exception:
                        continue
                if not (isinstance(coord, (tuple, list)) and len(coord) == 2):
                    continue
                lat, lon = coord
                lat_list.append(lat)
                lon_list.append(lon)
            if lat_list and lon_list:
                center_lat = sum(lat_list) / len(lat_list)
                center_lon = sum(lon_list) / len(lon_list)
            else:
                center_lat, center_lon = 0, 0
            mappa = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            for idx, row in dati_filtrati.iterrows():
                coord = row['coordinate_indirizzo']
                if pd.isnull(coord) or (isinstance(coord, str) and coord.strip() == ""):
                    continue
                if isinstance(coord, str):
                    try:
                        coord = ast.literal_eval(coord)
                    except Exception:
                        continue
                if not (isinstance(coord, (tuple, list)) and len(coord) == 2):
                    continue
                lat, lon = coord
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    tooltip="Appartamento"
                ).add_to(mappa)
        else:
            # Se è selezionata una o più zone
            if zona_option == "Multipla Zona":
                df_zone = dati_filtrati[dati_filtrati['zona'].isin(zona_selezionata)]
            else:  # "Singola Zona"
                df_zone = dati_filtrati[dati_filtrati['zona'] == zona_selezionata]
            lat_list = []
            lon_list = []
            for idx, row in df_zone.iterrows():
                coord = row['coordinate_indirizzo']
                if pd.isnull(coord) or (isinstance(coord, str) and coord.strip() == ""):
                    continue
                if isinstance(coord, str):
                    try:
                        coord = ast.literal_eval(coord)
                    except Exception:
                        continue
                if not (isinstance(coord, (tuple, list)) and len(coord) == 2):
                    continue
                lat, lon = coord
                lat_list.append(lat)
                lon_list.append(lon)
            if lat_list and lon_list:
                center_lat = sum(lat_list) / len(lat_list)
                center_lon = sum(lon_list) / len(lon_list)
            else:
                center_lat, center_lon = 0, 0
            mappa = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            for idx, row in df_zone.iterrows():
                coord = row['coordinate_indirizzo']
                if pd.isnull(coord) or (isinstance(coord, str) and coord.strip() == ""):
                    continue
                if isinstance(coord, str):
                    try:
                        coord = ast.literal_eval(coord)
                    except Exception:
                        continue
                if not (isinstance(coord, (tuple, list)) and len(coord) == 2):
                    continue
                lat, lon = coord
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    tooltip="Appartamento"
                ).add_to(mappa)
        # Visualizza la mappa in Streamlit
        st_folium(mappa, width=1500, height=250)



    col1, col2 = st.columns([2,4])
    with col1:
        with col1:
            st.metric("💰 Ricavi Totali (€)", f"{kpis['ricavi_totali']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_locazione"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        with metrica_col:
            st.metric("📈 Ricavi Locazione (€)", f"{kpis['totale_ricavi_locazione']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_pulizie"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        with metrica_col:
            st.metric("🧹 Ricavi Pulizie (€)", f"{kpis['totale_ricavi_pulizie']:,.2f}") 
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_commissioni"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        with metrica_col:
            st.metric("📈 Totale Commissioni (€)", f"{kpis['totale_commissioni']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_ota"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        with metrica_col:
            st.metric("🧹 Commissioni OTA (€)", f"{kpis['commissioni_ota']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_proprietari"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        with metrica_col:
            st.metric("🧹 Commissioni Proprietari (€)", f"{kpis['commissioni_proprietari']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_itw"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        with metrica_col:
            st.metric("🧹 Commissioni ITW (€)", f"{kpis['commissioni_itw']:,.2f}")
    with col2:
        colonne = ['ricavi_totali', 'commissioni_totali', 'marginalità_totale']
        fig = visualizza_andamento_ricavi(dati_filtrati, colonne)
        st.plotly_chart(fig)
        st.divider()
        col3, col4, col5 = st.columns([1,1,1])
        with col3:
            with col3:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_totale"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)
            with col3:
                st.metric("📊 Marginalità Totale (€)", f"{kpis['marginalità_totale']:,.2f}")
        with col4:
            with col4:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_locazioni"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)
            with col4:
                st.metric("📊 Marginalità Locazioni (€)", f"{kpis['marginalità_locazioni']:,.2f}")
        with col5:
            with col5:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_pulizie"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)
            with col5:
                st.metric("📊 Marginalità Pulizie (€)", f"{kpis['marginalità_pulizie']:,.2f}")
    st.divider()
    st.title("📊 Analisi Prenotazioni ")
    col12, col13, col14 = st.columns([4.5,9,4.5])
    with col12:
        st.metric("📈 Prezzo medio a notte (€)", f"{kpis['prezzo_medio_notte']:,.0f}")
        st.metric("📈 Prezzo pulizie (€)", f"{kpis['prezzo_pulizie']:,.0f}")
        st.metric("📈 M.S.V medio a notte (€)", f"{kpis['margine_medio_notte']:,.0f}")
        st.metric("📈 M.S.V pulizie per soggiorno (€)", f"{kpis['margine_medio_pulizie']:,.0f}")
        with col12:
            totale = 100
            kpi = kpis["tasso_di_occupazione"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        with col12:
            st.write("📊 Tasso di occupazione (%)")
    with col13:
        fig = visualizza_andamento_metriche(dati_filtrati, notti_disponibili_filtrate, start_date, end_date)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        col13_1, col13_2 = st.columns([2,2])
        with col13_1:
            st.metric("📈 Notti diponibili (€)", f"{kpis['notti_disponibili']:,.0f}")
            st.metric("📈 Notti libere (€)", f"{kpis['notti_libere']:,.0f}")
        with col13_2:
            st.metric("📈 Notti occupate ", f"{kpis['notti_occupate']:,.0f}")
            st.metric("📈 Soggiorno medio ", f"{kpis['soggiorno_medio']:,.0f}")
            st.metric("📈 Numero prenotazioni ", f"{kpis['numero_prenotazioni']:,.0f}")
    with col14:
        st.metric("📈 Valore medio prenotazione (€)", f"{kpis['valore_medio_prenotazione']:,.0f}")
        st.metric("📈 M.S.V medio per prenotazione (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")
        st.metric("📈 Margine medio per prenotazione (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")
        st.metric("📈 Costo Pulizia (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")
        st.metric("📈 Costo biancheria (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")
        st.metric("📈 Costo scorte (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")



    
def render_calcolatore():
    inject_custom_css()
    st.title("📊 Calcolatore profitti ")

    

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
    data = localizzatore(file_path, data)
    st.write(data)

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
            "Visualizza Appartamenti",
            ("Tutti gli Appartamenti", "Singolo Appartamento", "Multipli Appartamenti"),
            key="view_option_filter"
        )
        immobili_selezionati = None
        if view_option == "Singolo Appartamento":
            immobili_selezionati = st.selectbox(
                "Seleziona Appartamento",
                data['Nome Appartamento'].unique(),
                key="appartamento_filter"
            )
        elif view_option == "Multipli Appartamenti":
            immobili_selezionati = st.multiselect(
                "Seleziona uno o più Appartamenti",
                data['Nome Appartamento'].unique(),
                key="appartamento_filter_multi"
            )
        
        # Filtro per zona
        zona_option = st.radio(
            "Visualizza Zone",
            ("Tutte le Zone", "Singola Zona", "Multipla Zona"),
            key="zona_option_filter"
        )
        zona_selezionata = None
        if zona_option == "Singola Zona":
            zona_selezionata = st.selectbox(
                "Seleziona Zona",
                list(data['zona'].unique()),
                key="zona_filter"
            )
        elif zona_option == "Multipla Zona":
            zona_selezionata = st.multiselect(
                "Seleziona una o più Zone",
                list(data['zona'].unique()),
                key="zona_filter_multi"
            )
        
        # Filtraggio dei dati principali in base alle date
        dati_filtrati = data[
            (data['Data Check-In'] >= pd.Timestamp(start_date)) &
            (data['Data Check-In'] <= pd.Timestamp(end_date))
        ]
        
        # Filtra in base agli immobili
        if view_option != "Tutti gli Appartamenti" and immobili_selezionati:
            if view_option == "Singolo Appartamento":
                dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'] == immobili_selezionati]
            else:  # Multipli Appartamenti
                dati_filtrati = dati_filtrati[dati_filtrati['Nome Appartamento'].isin(immobili_selezionati)]
        
        # Filtra in base alla zona
        if zona_option != "Tutte le Zone" and zona_selezionata:
            if zona_option == "Singola Zona":
                dati_filtrati = dati_filtrati[dati_filtrati['zona'] == zona_selezionata]
            else:  # Multipla Zona
                dati_filtrati = dati_filtrati[dati_filtrati['zona'].isin(zona_selezionata)]
        
        # Assicurati che le colonne calcolate siano presenti nel DataFrame filtrato
        if 'ricavi_totali' not in dati_filtrati.columns:
            dati_filtrati['ricavi_totali'] = (
                dati_filtrati['Ricavi Locazione'] -
                dati_filtrati['IVA Provvigioni PM'] -
                dati_filtrati['Commissioni OTA'] * 0.22 +
                dati_filtrati['Ricavi Pulizie'] / 1.22
            )
        if 'commissioni_totali' not in dati_filtrati.columns:
            dati_filtrati['commissioni_totali'] = (
                dati_filtrati['Commissioni OTA'] / 1.22 +
                dati_filtrati['Commissioni ITW Nette']
            )
        
        # Calcola le notti disponibili
        notti_disponibili_df = calcola_notti_disponibili(file_path, start_date, end_date)
        
        # Filtra le notti disponibili in base al filtro appartamento
        if view_option != "Tutti gli Appartamenti" and immobili_selezionati:
            if view_option == "Singolo Appartamento":
                notti_disponibili_filtrate = notti_disponibili_df[
                    notti_disponibili_df['Appartamento'] == immobili_selezionati
                ]
            else:
                notti_disponibili_filtrate = notti_disponibili_df[
                    notti_disponibili_df['Appartamento'].isin(immobili_selezionati)
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
    

    st.write(dati_filtrati)



    # Calcolo dei KPI
    kpis = calculate_kpis(dati_filtrati, notti_disponibili_filtrate)


    st.write("Inserisci i dettagli dell'immobile:")
    

    
    


   
    
    
   

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
                "text": f"{float(percentuale):.0f}%",  # Converte percentuale in float prima della formattazione
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
    
    dati_filtrati['Prezzo Medio Notte'] = dati_filtrati['ricavi_totali'] / dati_filtrati['Notti Occupate']
    dati_filtrati['Margine Medio Notte'] = dati_filtrati['marginalità_totale'] / dati_filtrati['Notti Occupate']
    

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
        'Prezzo Medio Notte': 'mean',
        'Margine Medio Notte': 'mean',
        
    }).reset_index()

    # Trasforma i dati in formato lungo
    dati_melted = grouped_data.melt(
        id_vars=['Periodo'],
        value_vars=[
            'Tasso di Occupazione',
            'Prezzo Medio Notte',
            'Margine Medio Notte',
            
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
        height=400,  # Altezza compatta
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

##################    grafico a barre orizzontali    ##################
def create_horizontal_bar_chart(df, category_col, value_col):
    """
    Crea un grafico a barre orizzontali in cui per ogni riga del DataFrame viene disegnata una barra.
    Sul lato sinistro della barra viene visualizzato il valore corrispondente.
    """
    import plotly.graph_objects as go
    import plotly.express as px

    # Calcola il massimo valore per impostare il range dell'asse x
    max_val = df[value_col].max()
    
    # Imposta un offset negativo fisso per le annotazioni
    x_offset = -0.2  # Più a sinistra rispetto a prima
    
    # Calcola il margine sinistro in base alla lunghezza massima delle etichette
    max_label_length = df[category_col].astype(str).str.len().max()
    left_margin = max(150, max_label_length * 10)
    
    # Genera un colore diverso per ogni barra utilizzando la palette Plotly
    colors = px.colors.qualitative.Plotly
    bar_colors = [colors[i % len(colors)] for i in range(len(df))]

    fig = go.Figure()
    
    # Aggiunge la traccia a barre orizzontali
    fig.add_trace(go.Bar(
        x=df[value_col],
        y=df[category_col],
        orientation='h',
        marker=dict(color=bar_colors),
        text="",
    ))
    
    # Aggiungi annotazioni per mostrare il valore a sinistra di ogni barra
    # Utilizziamo xref="paper" per fissare il testo rispetto all'area del grafico.
    for i, row in df.iterrows():
        fig.add_annotation(
            x=x_offset,
            xref="paper",
            y=row[category_col],
            text=f"{row[value_col]:,.2f}",
            showarrow=False,
            xanchor="right",
            yanchor="middle",
            font=dict(size=10, color="black"),
            align="right",
            bordercolor="white",
            borderpad=4,
            bgcolor="white",
            opacity=0.8
        )
    
    # Imposta il layout, eliminando il titolo dell'asse verticale
    fig.update_layout(
        xaxis_title=value_col,
        yaxis_title="",
        margin=dict(l=left_margin + 50, r=20, t=20, b=20),
        xaxis=dict(range=[0, max_val * 1.1]),
        autosize=True
    )
    
    return fig




# Main
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

    


