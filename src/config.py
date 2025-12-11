# config.py
# ========= parametri di business 2021-2022 =========

# ----- DATI da CONSUNTIVO 2022 (dal foglio CE 21-22) -----
QTA_SPESE_TRASPORTO_CONS_2022 = 14                      # numero note spese trasporto
COSTO_PER_UNITA_TRASPORTO_CONS_2022 = 697               # €/unità (697 €/nota)
QTA_PREMIO_YEAR21_CONS_2022 = 15                        # numero premi
COSTO_PER_UNITA_PREMIO_CONS_2022 = 19835                # €/premio (19.835 × 1000)
QTA_ADEBITI_VARI_CONS_2022 = 49573                      # numero addebiti
COSTO_PER_UNITA_ADEBITI_VARI_CONS_2022 = 7.16           # €/addebito

# ----- DATI da BUDGET 2022 -----
COSTO_TOT_SPESE_TRASPORTO_BUDGET = 25000                # € complessivi
QTA_PREMIO_YEAR22_BUDGET = 12                           # numero premi budget
COSTO_PER_UNITA_PREMIO_BUDGET = 18981                   # €/premio (18.981 × 1000)

# ----- CONSUMI SPECIFICI (t vapor / t prodotto finito) -----
CONS_TON_VAP_PER_TON_PF_A = 0.93                        # ton vap / ton PF  polveri A
CONS_TON_VAP_PER_TON_PF_V = 0.64                        # ton vap / ton PF  polveri V

# ----- CONSUMI ENERGIA ELETTRICA (kWh per tonnellata di prodotto) -----
KWH_PER_TON_PF_A = 65
KWH_PER_TON_PF_V = 60
KWH_PER_TON_PF_P = 140
KWH_SERVIZI_GENERALI_MENSILI = 275_000                  # kWh/mese

# ----- FATTORI DI CONVERSIONE / RAPPORTI TECNICI -----
FATTORE_EMULSIONI_VINILICHE_PER_P = 1.67                # t emulsioni viniliche / t polvere P

# ----- AUMENTI PERCENTUALI SU COSTI ENERGIA -----
AUMENTO_COSTO_METANO_2022 = 0.14                        # +14 %
AUMENTO_COSTO_ENERGIA_ELETTRICA_2022 = 0.11             # +11 %

# ----- QUOTE CO2 -----
QUOTA_CO2_GRATUITA = 0.75                               # 75 % gratuite
QUOTA_CO2_DA_ACQUISTARE = 1 - QUOTA_CO2_GRATUITA        # 25 % a pagamento

# ----- VAPORE / METANO -----
SMC_METANO_PER_TON_VAPORE = 86                          # smc / t vapore
COSTO_QUOTA_CO2_PER_TON_VAPORE = 71                     # € / t vapore

# ----- INFLAZIONE / AGGIUSTAMENTI GENERICI -----
INFLAZIONE_2022_SU_2021 = 0.025                         # +2,5 % su costi 2021

# ----- SMALTIMENTO RIFIUTI -----
COSTO_SMALTIMENTO_PER_TON_EMULSIONI = 10.24             # € / t emulsione

# ----- TRASPORTI -----
COSTO_TRASPORTO_2021_PER_TON = 40                       # € / t venduta
AUMENTO_COSTO_TRASPORTO_2022 = 0.08                     # +8 %
COSTO_TRASPORTO_2022_PER_TON = COSTO_TRASPORTO_2021_PER_TON * (1 + AUMENTO_COSTO_TRASPORTO_2022)

# ----- PROVVIGIONI -----
PROVVIGIONI_PERC_SU_POLVERI = 0.02                      # 2 % dell’imponibile vendita polveri

# ----- PERSONALE - CCNL -----
AUMENTO_CCNL_PER_PERSONA_PER_MESE = 50                  # € lordi / mese
NUMERO_DIPENDENTI_INTERESSATI = 100
MESE_ANNUALI = 12
TASSE = 0.4
AUMENTO_CCNL_TOTALE_ANNUO = AUMENTO_CCNL_PER_PERSONA_PER_MESE * NUMERO_DIPENDENTI_INTERESSATI * MESE_ANNUALI * (1 + TASSE)

# ----- MANUTENZIONI -----
RIBASSO_MANUTENZIONI_BUDGET = 150_000                   # -150 k€ vs 2021

# ----- AUMENTI % "in linea con 2021" -----
AUMENTO_GENERICO_2_5_PERC = 0.025                       # usato per molte voci di costo

# ----- INVESTIMENTO / AMMORTAMENTI -----
INVESTIMENTO_NUOVO_IMPIANTO = 750_000                   # €
QUOTA_PRIMO_ANNO = 0.0625

# ----- FINANZIARI -----
NUOVA_LINEA_DI_CREDITO = 3_000_000                      # €
TASSO_INTERESSE_NUOVA_LINEA = 0.05                      # 5 % annuo
DATA_AVVIO_LINEA = "2022-06-01"

# ----- IMPOSTE -----
ALIQUOTA_IMPOSTE_SUL_REDITO = 0.30                      # 30 % del risultato ante-imposte

# ----- FLAGS "non previsti" -----
PREVISTE_SVALUTAZIONI_CREDITI = False
PREVISTI_PROVENTI_FINANZIARI = False
PREVISTI_ONERI_STRAORDINARI = False
PREVISTI_PROVENTI_STRAORDINARI = False
PREVISTE_SVALUTAZIONI_ACCANTONAMENTI = False

# tassi di cambio fissi
EUR_TO_USD = 1.17
USD_TO_EUR = 1/EUR_TO_USD

# dazio
DAZIO_PERC = 0.065   # 6,5 %

BASE_PATH = r"..\input"