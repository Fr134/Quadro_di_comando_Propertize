import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import math
import streamlit as st

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
    # Assicuriamoci che 'totale' e 'kpi' siano numeri scalari
    totale_scalar = float(totale) if not isinstance(totale, (int, float)) else totale
    kpi_scalar = float(kpi) if not isinstance(kpi, (int, float)) else kpi

    # Calcola la percentuale rispetto al totale
    percentuale = (kpi_scalar / totale_scalar) * 100

    # Dati per il grafico
    labels = ['Kpi', 'Altro']
    values = [kpi_scalar, totale_scalar - kpi_scalar]

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


def create_horizontal_bar_chart(df, category_col, value_col):
    """
    Crea un grafico a barre orizzontali in cui per ogni riga del DataFrame viene disegnata una barra.
    Sul lato sinistro della barra viene visualizzato il valore corrispondente.
    """

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
        xaxis_title="",
        yaxis_title="",
        margin=dict(l=left_margin + 50, r=20, t=20, b=20),
        xaxis=dict(range=[0, max_val * 1.1]),
        autosize=True
    )

    return fig


def create_tachometer(kpi, reference, title="Performance KPI"):
    """
    Crea un tachimetro a 180° diviso in tre zone (verde, arancione, rossa) e con un indicatore a freccia.

    Il grafico mostra un gauge (semicerchio) con scala percentuale da 0 a 100.
    L'indicatore (freccia) parte dal centro del semicerchio (0.5,0.5 in coordinate paper)
    e punta verso il valore percentuale (kpi/reference*100).

    Le tre zone sono equidistanti e colorate (verde, arancione, rossa) con trasparenza.
    Il valore percentuale al centro viene mostrato con un font ridotto.
    """
    # Calcola la percentuale
    percentage = (kpi / reference) * 100

    # Crea il gauge indicator
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentage,
        number={'suffix': "%", 'font': {'size': 12}},
        title={'text': title, 'font': {'size': 18}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': "rgba(0,0,0,0)"},  # rende trasparente la barra
            'bgcolor': "white",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 33.33], 'color': "rgba(0,128,0,0.3)"},
                {'range': [33.33, 66.66], 'color': "rgba(255,165,0,0.3)"},
                {'range': [66.66, 100], 'color': "rgba(255,0,0,0.3)"}
            ]
        }
    ))

    # Imposta dimensioni e margini del grafico
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), width=500, height=300)

    # In coordinate paper, il centro del gauge è sempre (0.5, 0.5)
    center_x, center_y = 0.5, 0.5

    # Calcola l'angolo (in radianti) corrispondente al valore percentuale:
    # 0% -> angolo = π (180°) e 100% -> angolo = 0
    angle = math.radians(180 * (1 - percentage/100))

    # Lunghezza della freccia (needle) in unità relative (paper coordinates)
    needle_length = 0.4
    # Calcola le coordinate del "tip" della freccia
    needle_x = center_x + needle_length * math.cos(angle)
    needle_y = center_y + needle_length * math.sin(angle)

    # Otteniamo le dimensioni in pixel (questo serve solo per il calcolo dell'offset)
    width = fig.layout.width
    height = fig.layout.height

    # Calcola l'offset (in pixel) affinché la base della freccia sia esattamente il centro (0.5, 0.5)
    # La formula è: offset_x = (center_x - needle_x) * width
    ax_val = (center_x - needle_x) * width
    ay_val = (center_y - needle_y) * height

    # Aggiungi l'annotazione con freccia che parte dal centro (0.5, 0.5) e punta al tip (needle_x, needle_y)
    fig.add_annotation(
        x=needle_x,
        y=needle_y,
        ax=ax_val,
        ay=ay_val,
        xref="paper",
        yref="paper",
        showarrow=True,
        arrowhead=2,
        arrowsize=2,
        arrowwidth=3,
        arrowcolor="black"
    )

    return fig
