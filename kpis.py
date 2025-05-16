import pandas as pd

from file_utility import save_df_to_csv
class KPIs:
    
    def __init__(self, stays_df: pd.DataFrame, expenses_df: pd.DataFrame):
        self.stays_df = stays_df
        self.expenses_df = self.__get_df_with_iva(expenses_df)

    @staticmethod
    def __get_df_with_iva(df: pd.DataFrame) -> pd.DataFrame:
        result = []
        previous_row = None
        for _, row in df.iterrows():
            dict_row = row.to_dict()
            if row['codice'] != '59.01.01':
                if previous_row is not None:
                    previous_row['netto'] = previous_row['importo_totale'] - previous_row.get('iva', 0)
                    result.append(previous_row)
                previous_row = dict_row
            else:
                previous_row['iva'] = row['importo']
        return pd.DataFrame(result)
    
    @staticmethod
    def __remove_iva(value: float) -> float:
        return value / 1.22
    
    ###### EXPENSES ######
    
    @property
    def totale_spese_netto(self) -> float:
        return self.expenses_df['netto'].sum()
    
    @property
    def totale_iva(self) -> float:
        return self.expenses_df['iva'].sum()
    
    @property
    def totale_spese_lordo(self) -> float:
        return self.expenses_df['importo_totale'].sum()

    
    ###### STAYS ######

    # RICAVI SENZA IVA
    @property
    def tot_ricavi_locazione(self) -> float:
        return self.stays_df['ricavi_locazione'].sum() - self.stays_df['iva_provvigioni_pm'].sum()

    @property
    def tot_ricavi_pulizie(self) -> float:
        return self.__remove_iva(self.stays_df['ricavi_pulizie'].sum())

    @property
    def ricavi_totali(self) -> float:
        return self.tot_ricavi_locazione + self.tot_ricavi_pulizie
    
    # COMMISSIONI SENZA IVA
    
    @property
    def commissioni_ota(self) -> float:
        return self.__remove_iva(self.stays_df['commissioni_ota'].sum())
    
    @property
    def commissioni_proprietari(self) -> float:
        return self.stays_df['commissioni_proprietari_lorde'].sum()
    
    @property
    def commissioni_ota_locazioni(self) -> float:
        return self.commissioni_ota * (self.tot_ricavi_locazione / self.ricavi_totali)
    
    @property
    def commissioni_itw(self) -> float:
        return self.stays_df['commissioni_itw_nette'].sum()
    
    @property
    def totale_commissioni(self) -> float:
        return self.commissioni_ota + self.commissioni_itw + self.commissioni_proprietari
    
    # MARGINALITà SENZA IVA

    @property
    def marginalita_locazioni(self) -> float:
        return self.tot_ricavi_locazione - self.commissioni_ota_locazioni - self.commissioni_proprietari
    
    @property
    def marginalita_pulizie(self) -> float:
        return self.tot_ricavi_pulizie - (self.commissioni_ota - self.commissioni_ota_locazioni)
    
    @property
    def marginalita_totale(self) -> float:
        return self.marginalita_locazioni + self.marginalita_pulizie
    
    # SALDO IVA

    @property
    def iva_ota(self) -> float:
        return self.commissioni_ota * 0.22
    
    @property
    def iva_totale_credito(self) -> float:
        return self.stays_df['iva_commissioni_itw'].sum() + self.iva_ota
    
    @property
    def iva_totale_debito(self) -> float:
        return self.stays_df['iva_provvigioni_pm'].sum()
    
    @property
    def saldo_iva(self) -> float:
        return self.iva_totale_debito - self.iva_totale_credito
    
    # COSTI DI PULIZIE SCORTE E MANUTENZIONE PER SOGGIORNO E TOTALI

    @property
    def costo_pulizie_ps(self) -> float:
        # TODO return self.stays_df['costo_pulizie_ps'].mean()   
        return 1
        
    
    @property
    def costo_scorte_ps(self) -> float:
        # TODO return self.stays_df['costo_scorte_ps'].mean()
        return 1
    
    @property
    def costo_manutenzioni_ps(self) -> float:
        # TODO return self.stays_df['costo_manutenzioni_ps'].mean()  
        return 1
    
    @property
    def costo_pulizie_ps_totali(self) -> float:
        # TODO return self.stays_df['costo_pulizie_ps'].sum()    
        return 1
    
    @property
    def costo_scorte_ps_totali(self) -> float:
        # TODO return self.stays_df['costo_scorte_ps'].sum()
        return 1
    
    @property
    def costo_manutenzioni_ps_totali(self) -> float:
        # TODO return self.stays_df['costo_manutenzioni_ps'].sum()
        return 1
    
    @property
    def altri_costi(self) -> float:
        return self.costo_scorte_ps_totali + self.costo_manutenzioni_ps_totali
    
    # NOTTI, PRENOTAZIONI ECC...

    @property
    def notti_occupate(self) -> float:
        # Calcola le notti occupate per ogni soggiorno (durata del soggiorno)
        notti_occupate_series = (self.stays_df['data_check_out'] - self.stays_df['data_check_in']).dt.days

        # Gestisci possibili anomalie (check-out prima del check-in) sostituendo con 0 i valori negativi
        notti_occupate_series = notti_occupate_series.apply(lambda x: max(x, 0))

        # Ritorna il totale delle notti occupate come valore scalare.
        # Un valore scalare evita la creazione di righe duplicate quando il dizionario
        # dei KPI viene trasformato in un DataFrame (broadcasting dei valori scalari).
        return notti_occupate_series.sum()
    
    @property
    def n_prenotazioni(self) -> float:
        return len(self.stays_df)
    
    @property
    def valore_medio_prenotazione(self) -> float:
        return self.ricavi_totali / self.n_prenotazioni
    
    @property
    def prezzo_medio_notte(self) -> float:
        return self.ricavi_totali / self.notti_occupate
    
    @property
    def soggiorno_medio(self) -> float:
        return self.notti_occupate / self.n_prenotazioni
    
    @property
    def prezzo_medio_notte(self) -> float:
        return self.ricavi_totali / self.notti_occupate
    
    # MARGINALITà MEDIA SENZA IVA

    @property
    def marginalita_media_prenotazione(self) -> float:
        return self.marginalita_totale / self.n_prenotazioni
    
    @property
    def marginalita_media_notte(self) -> float:
        return self.marginalita_locazioni / self.notti_occupate
    
    @property
    def prezzo_pulizie(self) -> float:
        return self.tot_ricavi_pulizie / self.n_prenotazioni
    
    @property
    def marginalita_media_pulizie(self) -> float:
        return self.marginalita_pulizie / self.n_prenotazioni
    
    # Utile

    @property
    def utile(self) -> float:
        return self.marginalita_totale - self.costo_pulizie_ps_totali - self.altri_costi
    

    ###### EXPENSES + STAYS ######
    @property
    def costi_totali(self) -> float:
        return self.totale_commissioni + self.totale_spese_netto
    
    @property
    def costi_variabili(self) -> float:
        return self.totale_commissioni
    
    @property
    def costi_fissi(self) -> float:
        return self.totale_spese_netto
    
    @property
    def costi_pulizie(self) -> float:
        return self.expenses_df[self.expenses_df['settore_spesa'] == 'PULIZIE']['netto'].sum() or 0
    
    @property
    def costi_gestione(self) -> float:
        return self.costi_fissi - self.costi_pulizie
    
    @property
    def ammortamenti(self) -> float:
        # TODO: get from user
        return 15000
    
    @property
    def EBITDA(self) -> float:
        return self.ricavi_totali - self.costi_totali
    
    @property
    def MOL(self) -> float:
        return self.EBITDA - self.ammortamenti
    
    def get_kpis(self, round_to: int = 2) -> dict:
        result = {
            'tot_ricavi_locazione': self.tot_ricavi_locazione,
            'tot_ricavi_pulizie': self.tot_ricavi_pulizie,
            'ricavi_totali': self.ricavi_totali,
            'commissioni_ota': self.commissioni_ota,
            'commissioni_proprietari': self.commissioni_proprietari,
            'commissioni_ota_locazioni': self.commissioni_ota_locazioni,
            'commissioni_itw': self.commissioni_itw,
            'totale_commissioni': self.totale_commissioni,
            'marginalita_locazioni': self.marginalita_locazioni,
            'marginalita_pulizie': self.marginalita_pulizie,
            'marginalita_totale': self.marginalita_totale,
            'iva_ota': self.iva_ota,
            'iva_totale_credito': self.iva_totale_credito,
            'iva_totale_debito': self.iva_totale_debito,
            'saldo_iva': self.saldo_iva,
            'costo_pulizie_ps': self.costo_pulizie_ps,
            'costo_scorte_ps': self.costo_scorte_ps,
            'costo_manutenzioni_ps': self.costo_manutenzioni_ps,
            'costo_pulizie_ps_totali': self.costo_pulizie_ps_totali,
            'costo_scorte_ps_totali': self.costo_scorte_ps_totali,
            'costo_manutenzioni_ps_totali': self.costo_manutenzioni_ps_totali,
            'altri_costi': self.altri_costi,
            'notti_occupate': self.notti_occupate,
            'n_prenotazioni': self.n_prenotazioni,
            'valore_medio_prenotazione': self.valore_medio_prenotazione,
            'prezzo_medio_notte': self.prezzo_medio_notte,
            'soggiorno_medio': self.soggiorno_medio,
            'prezzo_medio_notte': self.prezzo_medio_notte,
            'marginalita_media_prenotazione': self.marginalita_media_prenotazione,
            'marginalita_media_notte': self.marginalita_media_notte,
            'prezzo_pulizie': self.prezzo_pulizie,
            'marginalita_media_pulizie': self.marginalita_media_pulizie,
            'utile': self.utile,
            'costi_totali': self.costi_totali,
            'costi_variabili': self.costi_variabili,
            'costi_fissi': self.costi_fissi,
            'costi_pulizie': self.costi_pulizie,
            'costi_gestione': self.costi_gestione,
            'ammortamenti': self.ammortamenti,
            'EBITDA': self.EBITDA,
            'MOL': self.MOL,
        }
        return {k: round(v, round_to) for k, v in result.items()}
    
    def df_with_kpis(self) -> pd.DataFrame:
        return pd.DataFrame([self.get_kpis()])
    
    def save_kpis(self, path: str):
        save_df_to_csv(self.df_with_kpis(), path)
    
    
    
    

