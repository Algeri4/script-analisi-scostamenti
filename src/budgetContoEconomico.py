# ce_budget_2022.py
import pandas as pd
from datetime import date
from config import *

print("=== CE BUDGET 2022 ============")

# ---------- 1. lettura file ----------
ricavi     = pd.read_csv("../output/budgetRicavi.csv", sep=";", decimal=",")
var_cost   = pd.read_csv("../output/VariableCostsBudget.csv", sep=";", decimal=",")
fix_cost   = pd.read_csv("../output/FixedCostsBudget.csv", sep=";", decimal=",")
others     = pd.read_csv("../output/OthersBudget.csv", sep=";", decimal=",")

# funzione helper: se la voce non esiste restituisce 0
def val(df, voce, col="Valore Budget (euro)"):
    mask = df["Voce"].str.strip().eq(voce.strip())
    return df.loc[mask, col].sum()   # .sum() -> 0 se vuoto

# ---------- 2. RICAVI ----------
ricavi_pf      = ricavi[ricavi["Categoria"]=="PF"]["Ricavo"].sum()
ricavi_mp      = ricavi[ricavi["Categoria"]=="MP"]["Ricavo"].sum()
ricavi_pcl     = ricavi[ricavi["Categoria"]=="PCL"]["Ricavo"].sum()
# altri ricavi da config
altri_ricavi   = COSTO_TOT_SPESE_TRASPORTO_BUDGET - (QTA_PREMIO_YEAR22_BUDGET * COSTO_PER_UNITA_PREMIO_BUDGET)  # negativi = storno
variaz_prod    = 0
tot_ricavi     = ricavi_pf + ricavi_mp + ricavi_pcl + altri_ricavi + variaz_prod

# ---------- 3. COSTI MATERIE PRIME ----------
costo_mp = ricavi[ricavi["Categoria"].isin(["MP", "PCL", "PF"])]["Costo"].sum()
variaz_scorte  = 0
tot_costo_mp   = costo_mp + variaz_scorte

# ---------- 4. COSTI VARIABILI ----------
enel           = val(var_cost, "Energia elettrica")
metano         = val(var_cost, "Metano")
co2            = val(var_cost, "Quota CO₂")
mat_cons       = val(var_cost, "Materiali di consumo")
smalt_rif      = val(var_cost, "Pulizia e smaltimento rifiuti")
tot_var_prod   = enel + metano + mat_cons + smalt_rif + co2

# ---------- 5. COSTI DI VENDITA ----------
trasp          = val(var_cost, "Trasporti vendita")
provv          = val(var_cost, "Provvigioni su vendite")
tot_vendita    = trasp + provv

# ---------- 6. COSTI FISSI PRODUZIONE ----------
pers           = val(fix_cost, "Costo del personale")
manut          = val(fix_cost, "Manutenzioni")
altri_pers     = val(fix_cost, "Altri oneri del personale")
assic          = val(fix_cost, "Assicurazioni")
cons_tec       = val(fix_cost, "Consulenze tecniche e canoni acque")
god_terzi      = val(fix_cost, "Costo per godimento di beni di terzi")
tot_fissi_prod = pers + manut + altri_pers + assic + cons_tec + god_terzi

# ---------- 7. COSTI STRUTTURA ----------
cons_admin     = val(fix_cost, "Consulenze e amministrazioni")
spese_uff      = val(fix_cost, "Spese ufficio varie e oneri diversi di gestione")
imp_tasse      = val(fix_cost, "Imposte e tasse varie non sul reddito")
tot_strutt     = cons_admin + spese_uff + imp_tasse

# ---------- 8. ALTRI COSTI ----------
amm_imm        = val(others, "Ammortamenti immobilizzazioni immateriali")
amm_mat        = val(others, "Ammortamenti immobilizzazioni materiali")
sval_cred      = val(others, "Svalutazione crediti")
oneri_fin      = NUOVA_LINEA_DI_CREDITO * TASSO_INTERESSE_NUOVA_LINEA * (
                 (date(2022,12,31) - date.fromisoformat(DATA_AVVIO_LINEA)).days + 1 ) / 365
prov_fin       = 0
oneri_stra     = 0
prov_stra      = 0
sval_acc       = 0
imposte        = val(others, "Imposte sul reddito")

tot_ammort     = amm_imm + amm_mat + sval_cred
tot_altro      = tot_ammort + oneri_fin + prov_fin + oneri_stra + prov_stra + sval_acc + imposte

# ---------- 9. CALCOLI CE ----------
marg_op_lordo   = tot_ricavi - tot_costo_mp - tot_var_prod - tot_vendita
ebitda          = marg_op_lordo + tot_fissi_prod + tot_strutt
ebit            = ebitda - tot_ammort
oneri_net_fin   = oneri_fin + prov_fin
redd_op_caratt  = ebit - oneri_net_fin
redd_ante_imp   = redd_op_caratt   # straordinari = 0
imposte = redd_ante_imp * ALIQUOTA_IMPOSTE_SUL_REDITO
ris_netto       = redd_ante_imp - imposte

# ---------- 10. STAMPA FORMATTA CE ----------
ce_rows = [
    ("RICAVI DELLE VENDITE DI PRODOTTI FINITI", ricavi_pf),
    ("RICAVI DELLE VENDITE DI MATERIE PRIME - RIADDEBITI MP A GAMMA", ricavi_mp),
    ("RICAVI CONTO LAVORAZIONE - GAMMA E POLIKEMIA", ricavi_pcl),
    ("ALTRI RICAVI E LAVORI IN ECONOMIA", altri_ricavi),
    ("VARIAZIONE PRODOTTI FINITI", variaz_prod),
    ("A)  TOTALE RICAVI PRODUZIONE", tot_ricavi),
    ("ACQUISTO MATERIE PRIME ", -costo_mp),
    ("VARIAZIONE SCORTE", variaz_scorte),
    ("B)  TOTALE COSTI MATERIE PRIME", -tot_costo_mp),
    ("COSTO ENERGIA TOTALE", -enel -metano -co2),
    ("MATERIALI DI CONSUMO", -mat_cons),
    ("PULIZIA E SMALTIMENTO RIFIUTI", -smalt_rif),
    ("C)  COSTI VARIABILI DI PRODUZIONE", -tot_var_prod),
    ("TRASPORTI E ONERI DI VENDITA + ACQUISTO", -trasp),
    ("COSTO DI VENDITA - PROVVIGIONI-ENASARCO", -provv),
    ("D)  TOTALE COSTI DI VENDITA", -tot_vendita),
    ("E)  MARGINE OPERATIVO LORDO (A-B-C-D)", marg_op_lordo),
    ("COSTO DEL PERSONALE", -pers),
    ("MANUTENZIONI", -manut),
    ("ALTRI ONERI DEL PERSONALE", -altri_pers),
    ("ASSICURAZIONI", -assic),
    ("CONSULENZE TECNICHE E CANONI ACQUE", -cons_tec),
    ("COSTO PER GODIMENTO DI BENI DI TERZI", -god_terzi),
    ("F) TOTALE COSTI FISSI DI PRODUZIONE", -tot_fissi_prod),
    ("CONSULENZE E AMMINISTRATORI ", -cons_admin),
    ("SPESE UFFICIO VARIE E ONERI DIVERSI DI GESTIONE", -spese_uff),
    ("IMPOSTE E TASSE VARIE NON SUL REDDITO", -imp_tasse),
    ("G) TOTALE COSTI STRUTTURA COMM./AMM.VA", -tot_strutt),
    ("H) REDDITO OPERATIVO (EBITDA) (E-F-G)", ebitda),
    ("AMMORTAMENTI IMMOBILIZZAZIONI IMMATERIALI", -amm_imm),
    ("AMMORTAMENTI IMMOBILIZZAZIONI MATERIALI", -amm_mat),
    ("SVALUTAZIONE CREDITI", -sval_cred),
    ("I) TOTALE AMMORTAMENTI", -tot_ammort),
    ("L) MARGINE OPERATIVO NETTO (EBIT) (H-I)", ebit),
    ("(ONERI FINANZIARI)", -oneri_fin),
    ("PROVENTI FINANZIARI", prov_fin),
    ("M)  ONERI E PROVENTI FINANZIARI NETTI", -oneri_net_fin),
    ("N) REDDITO OPERATIVO GESTIONE CARATTERISTICA (L-M)", redd_op_caratt),
    ("(ONERI STRAORDINARI)", -oneri_stra),
    ("PROVENTI STRAORDINARI", prov_stra),
    ("(SVALUTAZIONI-ACCANTONAMENTI)", -sval_acc),
    ("O) ONERI E PROVENTI STRAORDINARI NETTI", 0),
    ("P) RISULTATO ANTE IMPOSTE (N-O)", redd_ante_imp),
    ("IMPOSTE SUL REDDITO", -imposte),
    ("RISULTATO NETTO", ris_netto)
]

print("\nCE BUDGET 2022:")
for desc, imp in ce_rows:
    print(f"{desc:<55} {imp:>15,.2f}")

# ---------- 11. salva ----------
ce_out = pd.DataFrame(ce_rows, columns=["Voce", "Valore (euro)"])
ce_out.to_csv("../output/CE_Budget_2022.csv", index=False, sep=";", decimal=",")
print("\nFile CE_Budget_2022.csv creato.")