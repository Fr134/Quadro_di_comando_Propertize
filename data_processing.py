import pandas as pd

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


def localizzatore(file_path, data):
    """
    Associa a ogni immobile la posizione e i costi per ogni soggiorno.
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
            'coordinate_indirizzo': row[5],     # Coordinate dell'indirizzo nella sesta colonna
            'costo_pulizie_ps': row[6],         # Coordinate dell'indirizzo nella sesta colonna
            'costo_scorte_ps': row[7],          # Coordinate dell'indirizzo nella sesta colonna
            'costo_manutenzioni_ps': row[8]     # Coordinate dell'indirizzo nella sesta colonna
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
