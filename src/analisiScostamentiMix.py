import pandas as pd
from datetime import date
from config import *

print("=== ANALISI SCOSTAMENTI MIX 2022 ===")

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def _to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def val(df, voce, col):
    m = df["Voce"].astype(str).str.strip().eq(voce.strip())
    return float(df.loc[m, col].sum())

def famiglia_from_row(cat, articolo):
    cat = str(cat).strip()
    if cat == "MP":
        return "MP"
    if cat == "PCL":
        return "PCL"
    if cat == "PF":
        a = str(articolo)
        parts = a.split()
        if not parts:
            return ""
        return parts[-1][0]  # A/V/P
    return ""

def compute_variable_costs_from_tons(ton_A, ton_V, ton_P):
    """
    Replica la logica del vostro VariableCostsBudget, parametrizzata sulle tonnellate.
    """
    ton_tot = ton_A + ton_V + ton_P

    # vapore
    vap_A = ton_A * CONS_TON_VAP_PER_TON_PF_A
    vap_V = ton_V * CONS_TON_VAP_PER_TON_PF_V
    vap_P = ton_P * FATTORE_EMULSIONI_VINILICHE_PER_P * CONS_TON_VAP_PER_TON_PF_V
    vap_tot = vap_A + vap_V + vap_P

    # metano
    smc_tot = vap_tot * SMC_METANO_PER_TON_VAPORE
    prezzo_smc_2022 = 0.4733720930232559 * (1 + AUMENTO_COSTO_METANO_2022)
    costo_metano = smc_tot * prezzo_smc_2022

    # energia elettrica
    kwh_A = ton_A * KWH_PER_TON_PF_A
    kwh_V = ton_V * KWH_PER_TON_PF_V
    kwh_P = ton_P * (KWH_PER_TON_PF_P + KWH_PER_TON_PF_V * FATTORE_EMULSIONI_VINILICHE_PER_P)
    kwh_serv = KWH_SERVIZI_GENERALI_MENSILI * 12
    kwh_tot = kwh_A + kwh_V + kwh_P + kwh_serv
    prezzo_kwh_2022 = 0.15721518991224825 * (1 + AUMENTO_COSTO_ENERGIA_ELETTRICA_2022)
    costo_eel = kwh_tot * prezzo_kwh_2022

    # CO2
    ton_co2 = vap_tot * QUOTA_CO2_DA_ACQUISTARE
    costo_co2 = ton_co2 * COSTO_QUOTA_CO2_PER_TON_VAPORE

    # materiali di consumo
    costo_mat_cons = 150_000 * (1 + INFLAZIONE_2022_SU_2021)

    # pulizia/smaltimento rifiuti (versione "corretta": include A + V + P*fattore)
    ton_emuls = ton_V + ton_A + ton_P * FATTORE_EMULSIONI_VINILICHE_PER_P
    costo_smalt = ton_emuls * COSTO_SMALTIMENTO_PER_TON_EMULSIONI

    # trasporti
    costo_trasp = ton_tot * COSTO_TRASPORTO_2022_PER_TON

    return {
        "Energia elettrica": costo_eel,
        "Metano": costo_metano,
        "Quota CO₂": costo_co2,
        "Materiali di consumo": costo_mat_cons,
        "Pulizia e smaltimento rifiuti": costo_smalt,
        "Trasporti vendita": costo_trasp
    }

def compute_ce_standard(
    ricavi_pf, ricavi_mp, ricavi_pcl, costo_mp,
    ricavi_polveri_p, ton_A, ton_V, ton_P,
    fixed_costs_df, others_df
):
    """
    Costruisce un CE "standard" (Mix Standard / Mix Effettivo) coerente con ce_budget_2022.py
    """
    # altri ricavi e variazioni come nel vostro CE budget
    altri_ricavi = COSTO_TOT_SPESE_TRASPORTO_BUDGET - (QTA_PREMIO_YEAR22_BUDGET * COSTO_PER_UNITA_PREMIO_BUDGET)
    variaz_prod = 0.0
    variaz_scorte = 0.0

    # costi variabili da ton
    var_costs = compute_variable_costs_from_tons(ton_A, ton_V, ton_P)
    enel = var_costs["Energia elettrica"]
    metano = var_costs["Metano"]
    co2 = var_costs["Quota CO₂"]
    mat_cons = var_costs["Materiali di consumo"]
    smalt_rif = var_costs["Pulizia e smaltimento rifiuti"]
    trasp = var_costs["Trasporti vendita"]

    provv = ricavi_polveri_p * PROVVIGIONI_PERC_SU_POLVERI

    tot_ricavi = ricavi_pf + ricavi_mp + ricavi_pcl + altri_ricavi + variaz_prod
    tot_costo_mp = costo_mp + variaz_scorte

    tot_var_prod = enel + metano + co2 + mat_cons + smalt_rif
    tot_vendita = trasp + provv

    # fissi (da output FixedCostsBudget.csv)
    pers = val(fixed_costs_df, "Costo del personale", "Valore Budget (euro)")
    manut = val(fixed_costs_df, "Manutenzioni", "Valore Budget (euro)")
    altri_pers = val(fixed_costs_df, "Altri oneri del personale", "Valore Budget (euro)")
    assic = val(fixed_costs_df, "Assicurazioni", "Valore Budget (euro)")
    cons_tec = val(fixed_costs_df, "Consulenze tecniche e canoni acque", "Valore Budget (euro)")
    god_terzi = val(fixed_costs_df, "Costo per godimento di beni di terzi", "Valore Budget (euro)")
    tot_fissi_prod = pers + manut + altri_pers + assic + cons_tec + god_terzi

    cons_admin = val(fixed_costs_df, "Consulenze e amministrazioni", "Valore Budget (euro)")
    spese_uff = val(fixed_costs_df, "Spese ufficio varie e oneri diversi di gestione", "Valore Budget (euro)")
    imp_tasse = val(fixed_costs_df, "Imposte e tasse varie non sul reddito", "Valore Budget (euro)")
    tot_strutt = cons_admin + spese_uff + imp_tasse

    # altri costi (da output OthersBudget.csv)
    amm_imm = val(others_df, "Ammortamenti immobilizzazioni immateriali", "Valore Budget (euro)")
    amm_mat = val(others_df, "Ammortamenti immobilizzazioni materiali", "Valore Budget (euro)")
    sval_cred = val(others_df, "Svalutazione crediti", "Valore Budget (euro)")
    tot_ammort = amm_imm + amm_mat + sval_cred

    inizio = date.fromisoformat(DATA_AVVIO_LINEA)
    fine_anno = date(inizio.year, 12, 31)
    giorni_attivi = (fine_anno - inizio).days + 1
    oneri_fin = NUOVA_LINEA_DI_CREDITO * TASSO_INTERESSE_NUOVA_LINEA * giorni_attivi / 365

    prov_fin = 0.0
    oneri_stra = 0.0
    prov_stra = 0.0
    sval_acc = 0.0

    marg_op_lordo = tot_ricavi - tot_costo_mp - tot_var_prod - tot_vendita
    ebitda = marg_op_lordo + tot_fissi_prod + tot_strutt
    ebit = ebitda - tot_ammort
    oneri_net_fin = oneri_fin + prov_fin
    redd_op_caratt = ebit - oneri_net_fin
    redd_ante_imp = redd_op_caratt
    imposte = redd_ante_imp * ALIQUOTA_IMPOSTE_SUL_REDITO
    ris_netto = redd_ante_imp - imposte

    # Mappa voci (allineata a CE_Budget_2022.csv)
    return {
        "RICAVI DELLE VENDITE DI PRODOTTI FINITI": ricavi_pf,
        "RICAVI DELLE VENDITE DI MATERIE PRIME - RIADDEBITI MP A GAMMA": ricavi_mp,
        "RICAVI CONTO LAVORAZIONE - GAMMA E POLIKEMIA": ricavi_pcl,
        "ALTRI RICAVI E LAVORI IN ECONOMIA": altri_ricavi,
        "VARIAZIONE PRODOTTI FINITI": variaz_prod,
        "A)  TOTALE RICAVI PRODUZIONE": tot_ricavi,
        "ACQUISTO MATERIE PRIME": -costo_mp,
        "VARIAZIONE SCORTE": variaz_scorte,
        "B)  TOTALE COSTI MATERIE PRIME": -tot_costo_mp,
        "COSTO ENERGIA TOTALE": -(enel + metano + co2),
        "MATERIALI DI CONSUMO": -mat_cons,
        "PULIZIA E SMALTIMENTO RIFIUTI": -smalt_rif,
        "C)  COSTI VARIABILI DI PRODUZIONE": -tot_var_prod,
        "TRASPORTI E ONERI DI VENDITA + ACQUISTO": -trasp,
        "COSTO DI VENDITA - PROVVIGIONI-ENASARCO": -provv,
        "D)  TOTALE COSTI DI VENDITA": -tot_vendita,
        "E)  MARGINE OPERATIVO LORDO (A-B-C-D)": marg_op_lordo,
        "COSTO DEL PERSONALE": -pers,
        "MANUTENZIONI": -manut,
        "ALTRI ONERI DEL PERSONALE": -altri_pers,
        "ASSICURAZIONI": -assic,
        "CONSULENZE TECNICHE E CANONI ACQUE": -cons_tec,
        "COSTO PER GODIMENTO DI BENI DI TERZI": -god_terzi,
        "F) TOTALE COSTI FISSI DI PRODUZIONE": -tot_fissi_prod,
        "CONSULENZE E AMMINISTRATORI": -cons_admin,
        "SPESE UFFICIO VARIE E ONERI DIVERSI DI GESTIONE": -spese_uff,
        "IMPOSTE E TASSE VARIE NON SUL REDDITO": -imp_tasse,
        "G) TOTALE COSTI STRUTTURA COMM./AMM.VA": -tot_strutt,
        "H) REDDITO OPERATIVO (EBITDA) (E-F-G)": ebitda,
        "AMMORTAMENTI IMMOBILIZZAZIONI IMMATERIALI": -amm_imm,
        "AMMORTAMENTI IMMOBILIZZAZIONI MATERIALI": -amm_mat,
        "SVALUTAZIONE CREDITI": -sval_cred,
        "I) TOTALE AMMORTAMENTI": -tot_ammort,
        "L) MARGINE OPERATIVO NETTO (EBIT) (H-I)": ebit,
        "(ONERI FINANZIARI)": -oneri_fin,
        "PROVENTI FINANZIARI": prov_fin,
        "M)  ONERI E PROVENTI FINANZIARI NETTI": -(oneri_net_fin),
        "N) REDDITO OPERATIVO GESTIONE CARATTERISTICA (L-M)": redd_op_caratt,
        "(ONERI STRAORDINARI)": -oneri_stra,
        "PROVENTI STRAORDINARI": prov_stra,
        "(SVALUTAZIONI-ACCANTONAMENTI)": -sval_acc,
        "O) ONERI E PROVENTI STRAORDINARI NETTI": 0.0,
        "P) RISULTATO ANTE IMPOSTE (N-O)": redd_ante_imp,
        "IMPOSTE SUL REDDITO": -imposte,
        "RISULTATO NETTO": ris_netto
    }

def scenario_numbers(df_items, q_col):
    # ricavi per categoria
    ric_pf = df_items[df_items["Categoria"] == "PF"]["Ricavo_std"].sum()
    ric_mp = df_items[df_items["Categoria"] == "MP"]["Ricavo_std"].sum()
    ric_pcl = df_items[df_items["Categoria"] == "PCL"]["Ricavo_std"].sum()

    # costo MP = costi standard tot su MP+PCL+PF
    costo_mp = df_items[df_items["Categoria"].isin(["MP", "PCL", "PF"])]["Costo_std_tot"].sum()

    # ricavi polveri (famiglia P) per provvigioni
    fam_col = "Famiglia"
    if fam_col not in df_items.columns:
        if "Famiglia_cons" in df_items.columns:
            fam_col = "Famiglia_cons"
        elif "Famiglia_std" in df_items.columns:
            fam_col = "Famiglia_std"

    ric_p = df_items[(df_items["Categoria"] == "PF") & (df_items[fam_col] == "P")]["Ricavo_std"].sum()

    # tonnellate PF per famiglie A/V/P
    fam_ton_pf = df_items[df_items["Categoria"] == "PF"].groupby(fam_col)[q_col].sum() / 1000.0
    ton_A = float(fam_ton_pf.get("A", 0.0))
    ton_V = float(fam_ton_pf.get("V", 0.0))
    ton_P = float(fam_ton_pf.get("P", 0.0))

    # aggiungo PCL su A (come nel vostro var_cost)
    ton_pcl = float(df_items[df_items["Categoria"] == "PCL"][q_col].sum() / 1000.0)
    ton_A = ton_A + ton_pcl

    return ric_pf, ric_mp, ric_pcl, costo_mp, ric_p, ton_A, ton_V, ton_P

# -------------------------------------------------------
# 1) Letture principali
# -------------------------------------------------------
ce_budget = pd.read_csv("../output/CE_Budget_2022.csv", sep=";", decimal=",", thousands=".")
ce_budget.columns = ["Voce", "Budget"]
ce_budget["Voce"] = ce_budget["Voce"].astype(str).str.strip()
ce_budget["Budget"] = _to_num(ce_budget["Budget"])

ce_reale = pd.read_csv(
    "../input/contoEconomicoConsuntivo2022.csv",
    sep=";",
    decimal=",",
    thousands=".",
    header=None,
    names=["Voce", "Reale"]
)
ce_reale["Voce"] = ce_reale["Voce"].astype(str).str.strip()
ce_reale["Reale"] = _to_num(ce_reale["Reale"])

bud_items = pd.read_csv("../output/budgetRicavi.csv", sep=";", decimal=",", thousands=".")
cons_items = pd.read_csv("../input/consuntivo2022.csv", sep=";", decimal=",", thousands=".")

# -------------------------------------------------------
# 2) Normalizzo budget items (standard)
# -------------------------------------------------------
bud_items["Articolo"] = bud_items["Articolo"].astype(str).str.strip()
bud_items["Categoria"] = bud_items["Categoria"].astype(str).str.strip()
bud_items["Famiglia"] = bud_items["Famiglia"].astype(str).str.strip()

bud_items["Quantita (kg)"] = _to_num(bud_items["Quantita (kg)"])
bud_items["Prezzo_std"] = _to_num(bud_items["Prezzo e/kg"])
bud_items["Costo_std"] = _to_num(bud_items["CMP e/kg (con dazio)"])

std_lookup = bud_items[["Articolo", "Categoria", "Famiglia", "Prezzo_std", "Costo_std"]].copy()

# -------------------------------------------------------
# 3) Normalizzo consuntivo items (q reali)
# -------------------------------------------------------
cons_items["Articolo"] = cons_items["Articolo"].astype(str).str.strip()
cons_items["Categoria"] = cons_items["Categoria"].astype(str).str.strip()
cons_items["Famiglia"] = cons_items.apply(lambda r: famiglia_from_row(r["Categoria"], r["Articolo"]), axis=1)

cons_items["Q_reale"] = _to_num(cons_items["Quantita (kg)"])

# -------------------------------------------------------
# 4) MIX EFFETTIVO (q reali per articolo, prezzi/costi standard)
# -------------------------------------------------------
mix_eff = pd.merge(
    cons_items[["Articolo", "Categoria", "Famiglia", "Q_reale"]],
    std_lookup,
    on=["Articolo", "Categoria"],
    how="left",
    suffixes=("_cons", "_std")
)

# Famiglia robusta
if "Famiglia" not in mix_eff.columns:
    if "Famiglia_cons" in mix_eff.columns:
        mix_eff["Famiglia"] = mix_eff["Famiglia_cons"]
    elif "Famiglia_std" in mix_eff.columns:
        mix_eff["Famiglia"] = mix_eff["Famiglia_std"]
    else:
        mix_eff["Famiglia"] = ""

mix_eff["Prezzo_std"] = mix_eff["Prezzo_std"].fillna(0.0)
mix_eff["Costo_std"] = mix_eff["Costo_std"].fillna(0.0)

mix_eff["Ricavo_std"] = mix_eff["Q_reale"] * mix_eff["Prezzo_std"]
mix_eff["Costo_std_tot"] = mix_eff["Q_reale"] * mix_eff["Costo_std"]

# -------------------------------------------------------
# 5) MIX STANDARD (q tot reali per categoria ripartiti con mix budget)
# -------------------------------------------------------
bud_qty = bud_items.groupby(["Categoria", "Articolo"], as_index=False)["Quantita (kg)"].sum()
bud_tot_cat = bud_qty.groupby("Categoria")["Quantita (kg)"].sum().to_dict()
real_tot_cat = cons_items.groupby("Categoria")["Q_reale"].sum().to_dict()

mix_std = bud_qty.copy()
mix_std["Q_std_mix"] = mix_std.apply(
    lambda r: (real_tot_cat.get(r["Categoria"], 0.0) * (r["Quantita (kg)"] / bud_tot_cat.get(r["Categoria"], 1.0)))
    if bud_tot_cat.get(r["Categoria"], 0.0) != 0 else 0.0,
    axis=1
)

mix_std = pd.merge(
    mix_std[["Categoria", "Articolo", "Q_std_mix"]],
    std_lookup,
    on=["Articolo", "Categoria"],
    how="left",
    suffixes=("_mix", "_std")
)

if "Famiglia" not in mix_std.columns:
    if "Famiglia_std" in mix_std.columns:
        mix_std["Famiglia"] = mix_std["Famiglia_std"]
    else:
        mix_std["Famiglia"] = ""

mix_std = mix_std.fillna(0.0)
mix_std["Ricavo_std"] = mix_std["Q_std_mix"] * mix_std["Prezzo_std"]
mix_std["Costo_std_tot"] = mix_std["Q_std_mix"] * mix_std["Costo_std"]

# -------------------------------------------------------
# 6) Carico fissi e altri costi (standard)
# -------------------------------------------------------
fixed_costs = pd.read_csv("../output/FixedCostsBudget.csv", sep=";", decimal=",", thousands=".")
others = pd.read_csv("../output/OthersBudget.csv", sep=";", decimal=",", thousands=".")

# -------------------------------------------------------
# 7) Numeri scenario e CE standard
# -------------------------------------------------------
ric_pf_me, ric_mp_me, ric_pcl_me, costo_mp_me, ric_p_me, tonA_me, tonV_me, tonP_me = scenario_numbers(mix_eff, "Q_reale")
ric_pf_ms, ric_mp_ms, ric_pcl_ms, costo_mp_ms, ric_p_ms, tonA_ms, tonV_ms, tonP_ms = scenario_numbers(mix_std, "Q_std_mix")

ce_mix_standard = compute_ce_standard(
    ricavi_pf=ric_pf_ms,
    ricavi_mp=ric_mp_ms,
    ricavi_pcl=ric_pcl_ms,
    costo_mp=costo_mp_ms,
    ricavi_polveri_p=ric_p_ms,
    ton_A=tonA_ms, ton_V=tonV_ms, ton_P=tonP_ms,
    fixed_costs_df=fixed_costs,
    others_df=others
)

ce_mix_effettivo = compute_ce_standard(
    ricavi_pf=ric_pf_me,
    ricavi_mp=ric_mp_me,
    ricavi_pcl=ric_pcl_me,
    costo_mp=costo_mp_me,
    ricavi_polveri_p=ric_p_me,
    ton_A=tonA_me, ton_V=tonV_me, ton_P=tonP_me,
    fixed_costs_df=fixed_costs,
    others_df=others
)

# -------------------------------------------------------
# 8) Tabella finale (come Excel)
# -------------------------------------------------------
out = ce_budget.copy()
out = pd.merge(out, ce_reale, on="Voce", how="left").fillna(0.0)

out["Mix Standard"] = out["Voce"].map(lambda v: ce_mix_standard.get(v, 0.0)).round(2)
out["Mix Effettivo"] = out["Voce"].map(lambda v: ce_mix_effettivo.get(v, 0.0)).round(2)

out["Δ Reale-Budget"] = (out["Reale"] - out["Budget"]).round(2)
out["Δ Mix Standard-Budget"] = (out["Mix Standard"] - out["Budget"]).round(2)
out["Δ Mix Effettivo-Standard"] = (out["Mix Effettivo"] - out["Mix Standard"]).round(2)
out["Δ Mix Reale-Effettivo"] = (out["Reale"] - out["Mix Effettivo"]).round(2)

out["Somma Δ Verifica"] = (
    out["Δ Mix Standard-Budget"]
    + out["Δ Mix Effettivo-Standard"]
    + out["Δ Mix Reale-Effettivo"]
).round(2)

out["CHECK"] = (
    out["Δ Reale-Budget"] - out["Somma Δ Verifica"]
).round(2)

out = out[[
    "Voce", "Budget", "Reale", "Δ Reale-Budget",
    "Mix Standard", "Δ Mix Standard-Budget",
    "Mix Effettivo", "Δ Mix Effettivo-Standard",
    "Δ Mix Reale-Effettivo",
    "Somma Δ Verifica", "CHECK"
]]

# -------------------------------------------------------
# 9) Stampe utili
# -------------------------------------------------------
print("\n--- Debug colonne (mix_eff / mix_std) ---")
print("mix_eff columns:", mix_eff.columns.tolist())
print("mix_std columns:", mix_std.columns.tolist())

print("\n--- Controllo CHECK (ultime 15 righe) ---")
print(out[["Voce", "CHECK"]].tail(15))

# -------------------------------------------------------
# 10) Salvataggio
# -------------------------------------------------------
out.to_csv("../output/AnalisiDegliScostamenti.csv", index=False, sep=";", decimal=",")

print("\nFile AnalisiDegliScostamenti.csv creato (con MIX).")
