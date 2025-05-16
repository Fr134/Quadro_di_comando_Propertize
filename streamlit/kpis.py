import pandas as pd


def somme_IVA(df, kpsi):
    import pandas as pd
    # df è il DataFrame con i totali (che contiene la colonna 'Totale_IVA')
    # kpsi è un dizionario (non un DataFrame) che contiene i valori di IVA_Totale_credito e IVA_Totale_debito
    totale_IVA_value = pd.to_numeric(df['Totale_IVA'].iloc[0], errors='coerce')
    IVA_Totale_credito = float(kpsi.get('IVA_Totale_credito', 0))
    IVA_Totale_debito = float(kpsi.get('IVA_Totale_Debito', 0))

    IVA_a_credito = totale_IVA_value + IVA_Totale_credito
    IVA_a_debito = IVA_Totale_debito
    saldo_IVA = IVA_a_debito - IVA_a_credito

    return {
        "IVA_a_credito": IVA_a_credito,
        "IVA_a_debito": IVA_a_debito,
        "saldo_IVA": saldo_IVA
    }


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

    #CALCOLO COSTI DI PULIZIE SCORTE E MANUTENZIONE PER SOGGIORNO E TOTALI

    costo_pulizie_ps = data['costo_pulizie_ps'].mean()
    costo_scorte_ps = data['costo_scorte_ps'].mean()
    costo_manutenzioni_ps = data['costo_manutenzioni_ps'].mean()

    costo_pulizie_ps_totali = data['costo_pulizie_ps'].sum()
    costo_scorte_ps_totali = data['costo_scorte_ps'].sum()
    costo_manutenzioni_ps_totali = data['costo_manutenzioni_ps'].sum()
    altri_costi = costo_scorte_ps_totali + costo_manutenzioni_ps_totali

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

    #    Utile   #

    marginalità_immobile = marginalità_totale - costo_pulizie_ps_totali - altri_costi

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
        'numero_prenotazioni': numero_prenotazioni,
        'costo_pulizie_ps':  costo_pulizie_ps,
        'costo_scorte_ps':costo_scorte_ps,
        'costo_manutenzioni_ps':costo_manutenzioni_ps,
        'costo_pulizie_ps_totali':costo_pulizie_ps_totali,
        'costo_scorte_ps_totali':costo_scorte_ps_totali,
        'costo_manutenzioni_ps_totali':costo_manutenzioni_ps_totali,
        'altri_costi':altri_costi,
        'marginalità_immobile':marginalità_immobile
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


def elabora_spese_ricavi(spese, spese_totali, spese_totali_settore, ricavi):
    costi_totali = float(spese_totali["Totale_Spese_netto"].iloc[0]) + float(ricavi["totale_commissioni"])
    costi_variabili = float(ricavi["totale_commissioni"])
    costi_fissi = float(spese_totali["Totale_Spese_netto"].iloc[0])
    if "PULIZIE" in spese_totali_settore["Settore di spesa"].unique():
        df_pulizie = spese_totali_settore[spese_totali_settore["Settore di spesa"] == "PULIZIE"]
        # Supponendo che il valore numerico da usare sia nella colonna "totale_netto"
        costi_pulizie = float(df_pulizie["totale_netto"].iloc[0])
    else:
        costi_pulizie = 0.0
    costi_gestione = costi_fissi - costi_pulizie
    ricavi_totali = float(ricavi["ricavi_totali"])
    ammortamenti = 15000
    EBITDA = ricavi_totali - costi_totali
    MOL = EBITDA - ammortamenti

    df_costi = pd.DataFrame({
        'costi_totali': [costi_totali],
        'costi_variabili': [costi_variabili],
        'costi_fissi': [costi_fissi],
        'costi_pulizie': [costi_pulizie],
        'costi_gestione': [costi_gestione],
        'ricavi_totali': [ricavi_totali],
        'ammortamenti': [ammortamenti],
        'EBITDA': [EBITDA],
        'MOL': [MOL]
    })

    return df_costi
