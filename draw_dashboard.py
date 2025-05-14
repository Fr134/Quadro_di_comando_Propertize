import ast

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from calculate_available_nights import calculate_available_nigths
from custom_css import inject_custom_css
from data_processing import localizzatore
from draw_charts import create_donut_chart, create_donut_chart1, create_horizontal_bar_chart, create_tachometer, \
    visualizza_andamento_metriche, visualizza_andamento_ricavi
from kpis import calculate_kpis, elabora_spese_ricavi, eleboratore_spese, somme_IVA


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
        notti_disponibili_df = calculate_available_nigths(file_path, start_date, end_date)

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
    spese = st.session_state['spese']
    kpis_spese, totali_spese_settore, totale_spese = eleboratore_spese(spese)
    dati_IVA = somme_IVA(totale_spese, kpis)
    riassunto_spese = elabora_spese_ricavi(kpis_spese, totale_spese, totali_spese_settore, kpis)

    st.divider()

   ############ Layout a 3 colonne per dividere lo schermo in tre sezioni uguali    ###########
    col1, col2 = st.columns([2,4])  # Tre colonne di uguale larghezza
    # Colonna 1: Grafico ad anello + KPI

    with col1:
        # Apre il contenitore della card
        st.metric("💰 Fatturato (€)", f"{kpis['ricavi_totali']:,.2f}")

        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = riassunto_spese["ricavi_totali"]
            kpi = riassunto_spese['costi_totali']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="gr21")
        with metrica_col:
            st.metric(" Costi (€)", f"{riassunto_spese['costi_totali'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Variabili rappresentano le commissioni variabili.">ℹ️</span>',
                unsafe_allow_html=True
            )


        # Terzo blocco
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = riassunto_spese["ricavi_totali"]
            kpi = riassunto_spese['EBITDA']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="gr31")
        with metrica_col:
            st.metric(" EBITDA (€)", f"{riassunto_spese['EBITDA'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Fissi rappresentano la parte fissa dei costi di gestione.">ℹ️</span>',
                unsafe_allow_html=True
            )

        # Terzo blocco
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = riassunto_spese["ricavi_totali"]
            kpi = riassunto_spese['MOL']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="gr41")
        with metrica_col:
            st.metric("  MOL (€)", f"{riassunto_spese['MOL'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Fissi rappresentano la parte fissa dei costi di gestione.">ℹ️</span>',
                unsafe_allow_html=True
            )

        st.divider()
        st.write("")  # Spazio verticale

        # Secondo blocco
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = riassunto_spese["ricavi_totali"]
            kpi = riassunto_spese['costi_variabili']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="gr2")
        with metrica_col:
            st.metric(" Costi Variabili (€)", f"{riassunto_spese['costi_variabili'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Variabili rappresentano le commissioni variabili.">ℹ️</span>',
                unsafe_allow_html=True
            )

        # Terzo blocco
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = riassunto_spese["costi_totali"]
            kpi = riassunto_spese['costi_fissi']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="gr3")
        with metrica_col:
            st.metric(" Costi Fissi (€)", f"{riassunto_spese['costi_fissi'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Fissi rappresentano la parte fissa dei costi di gestione.">ℹ️</span>',
                unsafe_allow_html=True
            )
        # Terzo blocco
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = riassunto_spese["costi_totali"]
            kpi = riassunto_spese['ammortamenti']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="gr4")
        with metrica_col:
            st.metric("  Ammortamenti (€)", f"{riassunto_spese['ammortamenti'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Fissi rappresentano la parte fissa dei costi di gestione.">ℹ️</span>',
                unsafe_allow_html=True
            )


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
                st.metric("📊 M.S.V. (€)", f"{kpis['marginalità_totale']:,.2f}")

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
            # Supponiamo di avere:
            kpi_value = 75      # il valore del KPI
            reference_value = 100  # il valore di riferimento

            # Crea il tachimetro:
            tachometer_fig = create_tachometer(kpi_value, reference_value, title="Performance KPI")

            # Visualizza il tachimetro in Streamlit:
            st.plotly_chart(tachometer_fig, use_container_width=True)


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
                st.metric("📊 Commissioni Local Manager (€)", f"{kpis['commissioni_itw']:,.2f}")




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

    # Sezione Filtri
    # Sezione Filtri
    with st.sidebar.expander("🔍 Filtro Dati"):
        st.markdown("### Filtra i dati")

        # Filtro per intervallo di date (usando il dataframe spese per determinare i limiti)
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

        # Filtra il dataframe spese in base alle date
        dati_filtrati_spese = spese[
            (spese['data'] >= pd.Timestamp(start_date)) &
            (spese['data'] <= pd.Timestamp(end_date))
        ]

        # Filtra il dataframe data in base allo stesso intervallo (colonna "Data Check-In")
        dati_filtrati_data = data[
            (data['Data Check-In'] >= pd.Timestamp(start_date)) &
            (data['Data Check-In'] <= pd.Timestamp(end_date))
        ]

        # Salva i dati filtrati nel session state
        st.session_state['filtered_data_spese'] = dati_filtrati_spese
        st.session_state['filtered_data_data'] = dati_filtrati_data

    # Usa i dati filtrati se disponibili
    if 'filtered_data_spese' in st.session_state:
        dati_filtrati_spese = st.session_state['filtered_data_spese']
    # Usa i dati filtrati se disponibili
    if 'filtered_data_data' in st.session_state:
        dati_filtrati_data = st.session_state['filtered_data_data']

    # Calcola le notti disponibili
    notti_disponibili_filtrate = calculate_available_nigths(file_path, start_date, end_date)
    st.session_state['filtered_notti_disponibili'] = notti_disponibili_filtrate

    if 'filtered_notti_disponibili' in st.session_state:
        notti_disponibili_filtrate = st.session_state['filtered_notti_disponibili']

    kpis_spese, totali_spese_settore, totale_spese = eleboratore_spese(dati_filtrati_spese)

    kpis = calculate_kpis(dati_filtrati_data, notti_disponibili_filtrate)
    dati_IVA = somme_IVA(totale_spese, kpis)
    riassunto_spese = elabora_spese_ricavi(kpis_spese, totale_spese, totali_spese_settore, kpis)

    col1, col2 = st.columns([2,4])
    with col1:
        # Primo blocco
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = riassunto_spese['costi_totali']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="grafico1")
        with metrica_col:
            st.metric("🧹 Costi Totali (€)", f"{riassunto_spese['costi_totali'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Totali rappresentano il totale dei costi fissi, compresi quelli relativi alle spese di gestione.">ℹ️</span>',
                unsafe_allow_html=True
            )

        st.write("")  # Spazio verticale per separare i blocchi

        # Secondo blocco
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = riassunto_spese["costi_totali"]
            kpi = riassunto_spese['costi_variabili']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="grafico2")
        with metrica_col:
            st.metric("🧹 Costi Variabili (€)", f"{riassunto_spese['costi_variabili'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Variabili rappresentano le commissioni variabili.">ℹ️</span>',
                unsafe_allow_html=True
            )

        st.write("")  # Spazio verticale

        # Terzo blocco
        grafico_col, info_col, metrica_col = st.columns([3, 0.3, 5])
        with grafico_col:
            totale = riassunto_spese["costi_totali"]
            kpi = riassunto_spese['costi_fissi']
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="grafico3")
        with metrica_col:
            st.metric("🧹 Costi Fissi (€)", f"{riassunto_spese['costi_fissi'].iloc[0]:,.2f}")
        with info_col:
            st.markdown(
                '<span class="info-icon" title="I Costi Fissi rappresentano la parte fissa dei costi di gestione.">ℹ️</span>',
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
            kpi = riassunto_spese["costi_gestione"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col01")  # Mantieni larghezza compatta
        with col01:
            render_metric_with_info(
                metric_label="📊 Costi di gestione (€)",
                metric_value=riassunto_spese['costi_gestione'],
                info_text="I Costi di gestione rappresentano il totale delle commissioni per i proprietari, indicatore dei costi di gestione dell'immobile."
            )
    with col02:
        #grafico ad anello
        # Sub-layout per centrare il grafico e il dato
        with col02:
            totale = kpis["ricavi_totali"]
            kpi = riassunto_spese["costi_pulizie"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col02")  # Mantieni larghezza compatta
        with col02:
            render_metric_with_info(
                metric_label="📊 Costi Pulizie (€)",
                metric_value=riassunto_spese["costi_pulizie"],
                info_text="I Costi di gestione rappresentano il totale delle commissioni per i proprietari, indicatore dei costi di gestione dell'immobile."
            )
    with col03:
        #grafico ad anello
        # Sub-layout per centrare il grafico e il dato
        with col03:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_ota"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col03")  # Mantieni larghezza compatta
        with col03:
            render_metric_with_info(
                metric_label="📊 Commissioni OTA (€)",
                metric_value=kpis['commissioni_ota'],
                info_text="I Costi di gestione rappresentano il totale delle commissioni per i proprietari, indicatore dei costi di gestione dell'immobile."
            )
    with col04:
        #grafico ad anello
        # Sub-layout per centrare il grafico e il dato
        with col04:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_proprietari"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col04")  # Mantieni larghezza compatta
        with col04:
            render_metric_with_info(
                metric_label="📊 Commissioni Proprietari (€)",
                metric_value=kpis['commissioni_proprietari'],
                info_text="I Costi di gestione rappresentano il totale delle commissioni per i proprietari, indicatore dei costi di gestione dell'immobile."
            )
    with col05:
        #grafico ad anello
        # Sub-layout per centrare il grafico e il dato
        with col05:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_itw"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="plotly_chart_col05")  # Mantieni larghezza compatta
        with col05:
            render_metric_with_info(
                metric_label="📊 Local Manager (€)",
                metric_value=kpis['commissioni_itw'],
                info_text="I Costi di gestione rappresentano il totale delle commissioni per i proprietari, indicatore dei costi di gestione dell'immobile."
            )
    col001, col002 = st.columns([4,2])
    with col001:
        fig = create_horizontal_bar_chart(totali_spese_settore, "Settore di spesa", "totale_netto")
        st.plotly_chart(fig)
    with col002:
        render_metric_with_info(
            metric_label="📊 Saldo IVA (€)",
            metric_value=dati_IVA['saldo_IVA'],
            info_text="I Costi di gestione rappresentano il totale delle commissioni per i proprietari, indicatore dei costi di gestione dell'immobile."
        )
        render_metric_with_info(
            metric_label="📊 Saldo a Debito (€)",
            metric_value=dati_IVA['IVA_a_credito'],
            info_text="I Costi di gestione rappresentano il totale delle commissioni per i proprietari, indicatore dei costi di gestione dell'immobile."
        )
        render_metric_with_info(
            metric_label="📊 IVA a Credito (€)",
            metric_value=dati_IVA['IVA_a_debito'],
            info_text="I Costi di gestione rappresentano il totale delle commissioni per i proprietari, indicatore dei costi di gestione dell'immobile."
        )


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
        notti_disponibili_df = calculate_available_nigths(file_path, start_date, end_date)

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
            st.metric("💰 Fatturato (€)", f"{kpis['ricavi_totali']:,.2f}")


        #grafico ad anello
        # Sub-layout per centrare il grafico e il dato
        grafico_col, metrica_col = st.columns([3, 5])  # Due sotto-colonne: 2/3 per il grafico, 1/3 per il dato
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_locazione"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
        with metrica_col:
            st.metric("📈 Ricavi (€)", f"{kpis['totale_ricavi_locazione']:,.2f}")

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
                st.metric("📊 Profitto (€)", f"{kpis['marginalità_totale']:,.2f}")

        with col4:
            #grafico ad anello
            # Sub-layout per centrare il grafico e il dato
            with col4:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_locazioni"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col4:
                st.metric("📊 Cedolare Secca (€)", f"{kpis['marginalità_locazioni']:,.2f}")

        with col5:
            #grafico ad anello
            # Sub-layout per centrare il grafico e il dato
            with col5:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_pulizie"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)  # Mantieni larghezza compatta
            with col5:
                st.metric("📊 Profitto Netto (€)", f"{kpis['marginalità_pulizie']:,.2f}")

    st.divider()

    # Layout a colonne: il grafico occuperà una colonna di larghezza 1/3
    col12, col13, col14 = st.columns([4.5,9,4.5])

    with col12:
        with col12:
            st.write("📊 Tasso di occupazione (%)")
        with col12:
            totale = 100
            kpi = kpis["tasso_di_occupazione"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        st.divider()
        st.metric("📈 Prezzo medio a notte (€)", f"{kpis['prezzo_medio_notte']:,.0f}")
        st.metric("📈 Valore medio prenotazione (€)", f"{kpis['valore_medio_prenotazione']:,.0f}")


    with col13:
        # Integrazione nella dashboard
        fig = visualizza_andamento_metriche(dati_filtrati, notti_disponibili_filtrate, start_date, end_date)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with col14:
        st.metric("📈 Margine medio a notte (€)", f"{kpis['margine_medio_notte']:,.0f}")
        st.metric("📈 Margine medio per prenotazione (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")
        st.divider()
        st.metric("📈 Notti occupate (€)", f"{kpis['notti_occupate']:,.0f}")
        st.metric("📈 Soggiorno medio ", f"{kpis['soggiorno_medio']:,.0f}")


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
        notti_disponibili_df = calculate_available_nigths(file_path, start_date, end_date)
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
            st.plotly_chart(grafico_anello, use_container_width=False, key="g1")
        with metrica_col:
            st.metric("📈 Ricavi Locazione (€)", f"{kpis['totale_ricavi_locazione']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["totale_ricavi_pulizie"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="g2")
        with metrica_col:
            st.metric("📈 Ricavi Pulizie (€)", f"{kpis['totale_ricavi_pulizie']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_proprietari"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="g3")
        with metrica_col:
            st.metric("📈 Commissioni Proprietari (€)", f"{kpis['commissioni_proprietari']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["commissioni_ota"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="g4")
        with metrica_col:
            st.metric("📈 Commissioni OTA (€)", f"{kpis['commissioni_ota']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["costo_pulizie_ps_totali"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="g5")
        with metrica_col:
            st.metric("🧹 Costi Pulizie (€)", f"{kpis['costo_pulizie_ps_totali']:,.2f}")
        grafico_col, metrica_col = st.columns([3, 5])
        with grafico_col:
            totale = kpis["ricavi_totali"]
            kpi = kpis["altri_costi"]
            grafico_anello = create_donut_chart(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False, key="g6")
        with metrica_col:
            st.metric("📈 Altri Costi (€)", f"{kpis['altri_costi']:,.2f}")
    with col2:
        colonne = ['ricavi_totali', 'commissioni_totali', 'marginalità_totale']
        fig = visualizza_andamento_ricavi(dati_filtrati, colonne)
        st.plotly_chart(fig)
        st.divider()
        col3, col4, col5 = st.columns([1,1,1])
        with col3:
            with col3:
                totale = kpis["ricavi_totali"]
                kpi = kpis["marginalità_immobile"]
                grafico_anello = create_donut_chart1(totale, kpi)
                st.plotly_chart(grafico_anello, use_container_width=False)
            with col3:
                st.metric("📊 Marginalità Operativa (€)", f"{kpis['marginalità_immobile']:,.2f}")
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
        with col12:
            st.write("📊 Tasso di occupazione (%)")
        with col12:
            totale = 100
            kpi = kpis["tasso_di_occupazione"]
            grafico_anello = create_donut_chart1(totale, kpi)
            st.plotly_chart(grafico_anello, use_container_width=False)
        st.divider()
        st.metric("📈 Prezzo medio a notte (€)", f"{kpis['prezzo_medio_notte']:,.0f}")
        st.metric("📈 Prezzo pulizie (€)", f"{kpis['prezzo_pulizie']:,.0f}")
        st.metric("📈 M.S.V medio a notte (€)", f"{kpis['margine_medio_notte']:,.0f}")
        st.metric("📈 M.S.V pulizie per soggiorno (€)", f"{kpis['margine_medio_pulizie']:,.0f}")
    with col13:
        fig = visualizza_andamento_metriche(dati_filtrati, notti_disponibili_filtrate, start_date, end_date)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        col13_1, col13_2 = st.columns([2,2])
        with col13_1:
            st.metric("📈 Notti diponibili ", f"{kpis['notti_disponibili']:,.0f}")
            st.metric("📈 Numero prenotazion (€)", f"{kpis['numero_prenotazioni']:,.0f}")
        with col13_2:
            st.metric("📈 Notti occupate ", f"{kpis['notti_occupate']:,.0f}")
            st.metric("📈 Soggiorno medio ", f"{kpis['soggiorno_medio']:,.0f}")
    with col14:
        st.metric("📈 Valore medio prenotazione (€)", f"{kpis['valore_medio_prenotazione']:,.0f}")
        st.metric("📈 M.S.V medio per prenotazione (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")
        st.metric("📈 Margine medio per prenotazione (€)", f"{kpis['margine_medio_prenotazione']:,.0f}")
        st.divider()
        st.metric("📈 Costo Pulizia (€)", f"{kpis['costo_pulizie_ps']:,.0f}")
        st.metric("📈 Costo Scorte (€)", f"{kpis['costo_scorte_ps']:,.0f}")
        st.metric("📈 Costo Manutenzioni (€)", f"{kpis['costo_manutenzioni_ps']:,.0f}")


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
        notti_disponibili_df = calculate_available_nigths(file_path, start_date, end_date)

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


def render_metric_with_info(metric_label, metric_value, info_text, value_format=",.2f", col_ratio=(0.3, 5)):
    """
    Visualizza una metrica con un bottone info associato.

    Parametri:
      - metric_label (str): l'etichetta della metrica (es. "Costi di gestione (€)")
      - metric_value (float): il valore della metrica (es. kpis['commissioni_proprietari'])
      - info_text (str): il testo da mostrare al passaggio del mouse sull'icona info.
      - value_format (str): formato da utilizzare per il valore (default ",.2f").
      - col_ratio (tuple): rapporto delle colonne per il valore e il bottone info (default (5, 0.3)).
    """
    col_info, col_value = st.columns(col_ratio)
    with col_value:
        st.metric(metric_label, f"{float(metric_value):{value_format}}")
    with col_info:
        st.markdown(
            f'<span class="info-icon" title="{info_text}">ℹ️</span>',
            unsafe_allow_html=True
        )
