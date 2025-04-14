def calculate_available_nigths(file_path, start_date, end_date):
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
