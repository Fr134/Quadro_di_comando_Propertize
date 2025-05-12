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

        /* Stile per l'icona info */
        .info-icon {
            font-size: 12px;
            color: rgb(51, 255, 0);
            cursor: pointer;
            margin-left: 4px;
        }
    </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)

    # Applica stili personalizzati alla dashboard (già esistente)
    st.markdown(
        """
        <style>
        /* Stili esistenti della dashboard (se presenti) */
        /* (Lasciato vuoto per evitare conflitti) */
        </style>
        """,
        unsafe_allow_html=True
    )
