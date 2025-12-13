import re
from pathlib import Path
from datetime import datetime, date
import pandas as pd

from config import *  # tutte le vostre costanti

print("=== ANALISI SCOSTAMENTI MIX 2022 (da zero, robusto stile BASE) ===")

# -------------------------------------------------------
# PATHS
# -------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
INPUT = BASE / "input"
OUTPUT = BASE / "output"

# -------------------------------------------------------
# Loader: leggo tutti i CSV in input e output (come BASE)
# -------------------------------------------------------
def load_all_csv(folder, sep=";", decimal=",", thousands="."):
    out = {}
    for p in Path(folder).glob("*.csv"):
        try:
            df = pd.read_csv(p, sep=sep, decimal=decimal, thousands=thousands)
        except Exception:
            df = pd.read_csv(p, sep=sep, decimal=decimal, thousands=thousands, engine="python")
        out[p.name] = df
    return out

DATA = {"input": load_all_csv(INPUT), "output": load_all_csv(OUTPUT)}

def get_table(area, filename):
    if filename not in DATA[area]:
        raise FileNotFoundError(f"Non trovo {filename} in {area}/")
    return DATA[area][filename].copy()

def safe_to_csv(df, path, sep=";", decimal=","):
    try:
        df.to_csv(path, index=False, sep=sep, decimal=decimal)
        print(f"\nFile creato: {path}")
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        alt = str(path).replace(".csv", f"__LOCKED_{ts}.csv")
        df.to_csv(alt, index=False, sep=sep, decimal=decimal)
        print(f"\nATTENZIONE: {path} è bloccato (Excel aperto). Salvato: {alt}")

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def norm_voce(s: str) -> str:
    s = str(s).replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip().upper()

def to_num(x):
    return pd.to_numeric(x, errors="coerce").fillna(0.0)

def _v(df, col, voce):
    m = df["Voce"].astype(str).map(norm_voce).eq(norm_voce(voce))
    return float(df.loc[m, col].sum())

def _set(df, col, voce, value):
    m = df["Voce"].astype(str).map(norm_voce).eq(norm_voce(voce))
    df.loc[m, col] = float(value)

def famiglia_from_row(cat, articolo):
    cat = str(cat).strip()
    if cat == "MP":
        return "MP"
    if cat == "PCL":
        return "PCL"
    if cat == "PF":
        parts = str(articolo).split()
        return parts[-1][0] if parts else ""
    return ""

def pick_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

BASE_FILE = OUTPUT / "AnalisiDegliScostamentiBase.csv"  # deve esistere in output/

if not BASE_FILE.exists():
    raise FileNotFoundError(
        "Non trovo output/AnalisiDegliScostamentiBase.csv. "
        "Nel BASE salva anche questo file e rilancia."
    )

base_ok = pd.read_csv(BASE_FILE, sep=";", decimal=",", thousands=".")
out = base_ok[["Voce", "Budget", "Reale"]].copy()

out["Voce"] = out["Voce"].astype(str).str.strip()
out["Budget"] = to_num(out["Budget"])
out["Reale"]  = to_num(out["Reale"])

# -------------------------------------------------------
# Leggo vendite budget + consuntivo
# -------------------------------------------------------
bud = get_table("input", "budgetVendite2022.csv")
cons = get_table("input", "consuntivo2022.csv")

# === QUI IL FIX: nomi colonna del tuo CSV ===
col_q = pick_col(bud, ["Quantita (kg)", "Quantita", "Qta", "Q"])
col_p = pick_col(bud, ["P medio (e/kg)", "Prezzo_std", "Prezzo e/kg", "Prezzo", "Prezzo (€/kg)"])
col_c = pick_col(bud, ["CMP medio (e/kg)", "Costo_std", "CMP e/kg (con dazio)", "CMP e/kg", "Costo", "Costo (€/kg)", "MP con dazio"])

if col_q is None or col_p is None or col_c is None:
    raise KeyError(
        f"Nel budgetVendite2022.csv non trovo colonne standard (Q/Prezzo/Costo). "
        f"Trovate: {list(bud.columns)}"
    )

bud["Articolo"] = bud["Articolo"].astype(str).str.strip()
bud["Categoria"] = bud["Categoria"].astype(str).str.strip()

if "Famiglia" in bud.columns:
    bud["Famiglia"] = bud["Famiglia"].astype(str).str.strip()
else:
    bud["Famiglia"] = bud.apply(lambda r: famiglia_from_row(r["Categoria"], r["Articolo"]), axis=1)

bud["Q_budget"] = to_num(bud[col_q])
bud["Prezzo_std"] = to_num(bud[col_p])
bud["Costo_std"] = to_num(bud[col_c])

cons["Articolo"] = cons["Articolo"].astype(str).str.strip()
cons["Categoria"] = cons["Categoria"].astype(str).str.strip()
cons["Famiglia"] = cons.apply(lambda r: famiglia_from_row(r["Categoria"], r["Articolo"]), axis=1)

col_qc = pick_col(cons, ["Quantita (kg)", "Quantita", "Qta", "Q"])
if col_qc is None:
    raise KeyError(f"Nel consuntivo2022.csv non trovo la colonna quantità. Colonne: {list(cons.columns)}")

cons["Q_reale"] = to_num(cons[col_qc])

# -------------------------------------------------------
# Mix effettivo: Q reali × (prezzo/costo standard articolo)
# -------------------------------------------------------
std_lookup = bud[["Articolo", "Categoria", "Prezzo_std", "Costo_std"]].copy()

mix_eff = cons[["Articolo", "Categoria", "Famiglia", "Q_reale"]].merge(
    std_lookup, on=["Articolo", "Categoria"], how="left"
)
mix_eff["Prezzo_std"] = mix_eff["Prezzo_std"].fillna(0.0)
mix_eff["Costo_std"] = mix_eff["Costo_std"].fillna(0.0)
mix_eff["Ricavo_std"] = mix_eff["Q_reale"] * mix_eff["Prezzo_std"]
mix_eff["Costo_std_tot"] = mix_eff["Q_reale"] * mix_eff["Costo_std"]

# -------------------------------------------------------
# Mix standard: PF per famiglia (mix budget) con Q PF reale
# -------------------------------------------------------
bud_pf = bud[bud["Categoria"] == "PF"].copy()
q_pf_budget = float(bud_pf["Q_budget"].sum())
q_pf_reale = float(cons.loc[cons["Categoria"] == "PF", "Q_reale"].sum())

mix_pf_fam = (bud_pf.groupby("Famiglia")["Q_budget"].sum() / (q_pf_budget if q_pf_budget != 0 else 1)).fillna(0.0)

w_price = (bud_pf["Prezzo_std"] * bud_pf["Q_budget"]).groupby(bud_pf["Famiglia"]).sum()
w_cost  = (bud_pf["Costo_std"]  * bud_pf["Q_budget"]).groupby(bud_pf["Famiglia"]).sum()
w_q     = bud_pf["Q_budget"].groupby(bud_pf["Famiglia"]).sum().replace(0, 1)

pf_fam_price = (w_price / w_q).fillna(0.0)
pf_fam_cost  = (w_cost / w_q).fillna(0.0)

rows_pf = []
for fam in ["A", "V", "P"]:
    share = float(mix_pf_fam.get(fam, 0.0))
    q_fam = q_pf_reale * share
    rows_pf.append({
        "Categoria": "PF",
        "Famiglia": fam,
        "Q_std_mix": q_fam,
        "Prezzo_std": float(pf_fam_price.get(fam, 0.0)),
        "Costo_std": float(pf_fam_cost.get(fam, 0.0)),
    })

mix_std_pf = pd.DataFrame(rows_pf)
mix_std_pf["Ricavo_std"] = mix_std_pf["Q_std_mix"] * mix_std_pf["Prezzo_std"]
mix_std_pf["Costo_std_tot"] = mix_std_pf["Q_std_mix"] * mix_std_pf["Costo_std"]

def build_mix_std_cat(cat):
    bud_cat = bud[bud["Categoria"] == cat].copy()
    if bud_cat.empty:
        return pd.DataFrame(columns=["Categoria","Famiglia","Q_std_mix","Prezzo_std","Costo_std","Ricavo_std","Costo_std_tot"])

    q_bud_tot = float(bud_cat["Q_budget"].sum())
    q_real_tot = float(cons.loc[cons["Categoria"] == cat, "Q_reale"].sum())

    bud_cat["Q_std_mix"] = 0.0 if q_bud_tot == 0 else (bud_cat["Q_budget"] / q_bud_tot * q_real_tot)
    out_cat = bud_cat[["Categoria","Famiglia","Q_std_mix","Prezzo_std","Costo_std"]].copy()
    out_cat["Ricavo_std"] = out_cat["Q_std_mix"] * out_cat["Prezzo_std"]
    out_cat["Costo_std_tot"] = out_cat["Q_std_mix"] * out_cat["Costo_std"]
    return out_cat

mix_std = pd.concat([mix_std_pf, build_mix_std_cat("MP"), build_mix_std_cat("PCL")], ignore_index=True)

# -------------------------------------------------------
# Scenario numbers
# -------------------------------------------------------
def scenario_numbers(df_items, q_col):
    ric_pf = float(df_items.loc[df_items["Categoria"] == "PF", "Ricavo_std"].sum())
    ric_mp = float(df_items.loc[df_items["Categoria"] == "MP", "Ricavo_std"].sum())
    ric_pcl = float(df_items.loc[df_items["Categoria"] == "PCL", "Ricavo_std"].sum())
    costo_mp_tot = float(df_items.loc[df_items["Categoria"].isin(["PF","MP","PCL"]), "Costo_std_tot"].sum())
    ric_polveri_p = float(df_items.loc[(df_items["Categoria"] == "PF") & (df_items["Famiglia"] == "P"), "Ricavo_std"].sum())

    fam_ton_pf = df_items.loc[df_items["Categoria"] == "PF"].groupby("Famiglia")[q_col].sum() / 1000.0
    tonA = float(fam_ton_pf.get("A", 0.0))
    tonV = float(fam_ton_pf.get("V", 0.0))
    tonP = float(fam_ton_pf.get("P", 0.0))
    tonPCL = float(df_items.loc[df_items["Categoria"] == "PCL", q_col].sum() / 1000.0)
    tonA += tonPCL

    return ric_pf, ric_mp, ric_pcl, costo_mp_tot, ric_polveri_p, tonA, tonV, tonP

# -------------------------------------------------------
# Costi variabili & CE mix
# -------------------------------------------------------
def compute_variable_costs_from_tons(ton_A, ton_V, ton_P, ricavi_polveri_p):
    ton_tot = ton_A + ton_V + ton_P

    vap_A = ton_A * CONS_TON_VAP_PER_TON_PF_A
    vap_V = ton_V * CONS_TON_VAP_PER_TON_PF_V
    vap_P = ton_P * FATTORE_EMULSIONI_VINILICHE_PER_P * CONS_TON_VAP_PER_TON_PF_V
    vap_tot = vap_A + vap_V + vap_P

    smc_tot = vap_tot * SMC_METANO_PER_TON_VAPORE
    prezzo_smc_2022 = 0.4733720930232559 * (1 + AUMENTO_COSTO_METANO_2022)
    costo_metano = smc_tot * prezzo_smc_2022

    kwh_A = ton_A * KWH_PER_TON_PF_A
    kwh_V = ton_V * KWH_PER_TON_PF_V
    kwh_P = ton_P * (KWH_PER_TON_PF_P + KWH_PER_TON_PF_V * FATTORE_EMULSIONI_VINILICHE_PER_P)
    kwh_serv = KWH_SERVIZI_GENERALI_MENSILI * 12
    kwh_tot = kwh_A + kwh_V + kwh_P + kwh_serv
    prezzo_kwh_2022 = 0.15721518991224825 * (1 + AUMENTO_COSTO_ENERGIA_ELETTRICA_2022)
    costo_eel = kwh_tot * prezzo_kwh_2022

    ton_co2 = vap_tot * QUOTA_CO2_DA_ACQUISTARE
    costo_co2 = ton_co2 * COSTO_QUOTA_CO2_PER_TON_VAPORE

    costo_mat_cons = 150_000 * (1 + INFLAZIONE_2022_SU_2021)

    ton_emuls = ton_V + ton_A + ton_P * FATTORE_EMULSIONI_VINILICHE_PER_P
    costo_smalt = ton_emuls * COSTO_SMALTIMENTO_PER_TON_EMULSIONI

    costo_trasp = ton_tot * COSTO_TRASPORTO_2022_PER_TON
    provv = ricavi_polveri_p * PROVVIGIONI_PERC_SU_POLVERI

    return {
        "costo_energia_tot": costo_eel + costo_metano + costo_co2,
        "materiali_consumo": costo_mat_cons,
        "pulizia_smalt": costo_smalt,
        "trasporti": costo_trasp,
        "provvigioni": provv,
    }

def val_budget(df, voce):
    df2 = df.copy()
    df2["Voce"] = df2["Voce"].astype(str).str.strip()
    m = df2["Voce"].map(norm_voce).eq(norm_voce(voce))
    return float(to_num(df2.loc[m, "Valore Budget (euro)"]).sum())

def oneri_fin_budget():
    inizio = date.fromisoformat(DATA_AVVIO_LINEA)
    fine_anno = date(inizio.year, 12, 31)
    giorni_attivi = (fine_anno - inizio).days + 1
    return NUOVA_LINEA_DI_CREDITO * TASSO_INTERESSE_NUOVA_LINEA * giorni_attivi / 365

def compute_ce_mix(ric_pf, ric_mp, ric_pcl, costo_mp_tot, ric_polveri_p, tonA, tonV, tonP, fixed_df, others_df, altri_ricavi):
    varc = compute_variable_costs_from_tons(tonA, tonV, tonP, ric_polveri_p)

    variaz_prod = 0.0
    variaz_scorte = 0.0

    A_tot = ric_pf + ric_mp + ric_pcl + altri_ricavi + variaz_prod
    acquisto_mp = -costo_mp_tot
    B_tot = acquisto_mp + variaz_scorte

    costo_energia = -varc["costo_energia_tot"]
    mat_cons = -varc["materiali_consumo"]
    smalt = -varc["pulizia_smalt"]
    C_tot = costo_energia + mat_cons + smalt

    trasp = -varc["trasporti"]
    provv = -varc["provvigioni"]
    D_tot = trasp + provv

    E = A_tot + B_tot + C_tot + D_tot

    pers = -val_budget(fixed_df, "Costo del personale")
    manut = -val_budget(fixed_df, "Manutenzioni")
    altri_p = -val_budget(fixed_df, "Altri oneri del personale")
    assic = -val_budget(fixed_df, "Assicurazioni")
    cons_tec = -val_budget(fixed_df, "Consulenze tecniche e canoni acque")
    god_terzi = -val_budget(fixed_df, "Costo per godimento di beni di terzi")
    F = pers + manut + altri_p + assic + cons_tec + god_terzi

    cons_admin = -val_budget(fixed_df, "Consulenze e amministrazioni")
    spese_uff = -val_budget(fixed_df, "Spese ufficio varie e oneri diversi di gestione")
    imp_tasse = -val_budget(fixed_df, "Imposte e tasse varie non sul reddito")
    G = cons_admin + spese_uff + imp_tasse

    H = E + F + G

    amm_imm = -val_budget(others_df, "Ammortamenti immobilizzazioni immateriali")
    amm_mat = -val_budget(others_df, "Ammortamenti immobilizzazioni materiali")
    sval = -val_budget(others_df, "Svalutazione crediti")
    I = amm_imm + amm_mat + sval

    L = H + I

    of = -oneri_fin_budget()
    proventi_fin = 0.0
    M = of + proventi_fin

    N = L + M

    O = 0.0
    P = N + O

    imposte = P * ALIQUOTA_IMPOSTE_SUL_REDITO

    return {
        "RICAVI DELLE VENDITE DI PRODOTTI FINITI": ric_pf,
        "RICAVI DELLE VENDITE DI MATERIE PRIME - RIADDEBITI MP A GAMMA": ric_mp,
        "RICAVI CONTO LAVORAZIONE - GAMMA E POLIKEMIA": ric_pcl,
        "ALTRI RICAVI E LAVORI IN ECONOMIA": altri_ricavi,
        "VARIAZIONE PRODOTTI FINITI": variaz_prod,
        "A)  TOTALE RICAVI PRODUZIONE": A_tot,
        "ACQUISTO MATERIE PRIME": acquisto_mp,
        "VARIAZIONE SCORTE": variaz_scorte,
        "B)  TOTALE COSTI MATERIE PRIME": B_tot,
        "COSTO ENERGIA TOTALE": costo_energia,
        "MATERIALI DI CONSUMO": mat_cons,
        "PULIZIA E SMALTIMENTO RIFIUTI": smalt,
        "C)  COSTI VARIABILI DI PRODUZIONE": C_tot,
        "TRASPORTI E ONERI DI VENDITA + ACQUISTO": trasp,
        "COSTO DI VENDITA - PROVVIGIONI-ENASARCO": provv,
        "D)  TOTALE COSTI DI VENDITA": D_tot,
        "E)  MARGINE OPERATIVO LORDO (A-B-C-D)": E,
        "COSTO DEL PERSONALE": pers,
        "MANUTENZIONI": manut,
        "ALTRI ONERI DEL PERSONALE": altri_p,
        "ASSICURAZIONI": assic,
        "CONSULENZE TECNICHE E CANONI ACQUE": cons_tec,
        "COSTO PER GODIMENTO DI BENI DI TERZI": god_terzi,
        "F) TOTALE COSTI FISSI DI PRODUZIONE": F,
        "CONSULENZE E AMMINISTRATORI": cons_admin,
        "SPESE UFFICIO VARIE E ONERI DIVERSI DI GESTIONE": spese_uff,
        "IMPOSTE E TASSE VARIE NON SUL REDDITO": imp_tasse,
        "G) TOTALE COSTI STRUTTURA COMM./AMM.VA": G,
        "H) REDDITO OPERATIVO (EBITDA) (E-F-G)": H,
        "AMMORTAMENTI IMMOBILIZZAZIONI IMMATERIALI": amm_imm,
        "AMMORTAMENTI IMMOBILIZZAZIONI MATERIALI": amm_mat,
        "SVALUTAZIONE CREDITI": sval,
        "I) TOTALE AMMORTAMENTI": I,
        "L) MARGINE OPERATIVO NETTO (EBIT) (H-I)": L,
        "(ONERI FINANZIARI)": of,
        "PROVENTI FINANZIARI": proventi_fin,
        "M)  ONERI E PROVENTI FINANZIARI NETTI": M,
        "N) REDDITO OPERATIVO GESTIONE CARATTERISTICA (L-M)": N,
        "O) ONERI E PROVENTI STRAORDINARI NETTI": O,
        "P) RISULTATO ANTE IMPOSTE (N-O)": P,
        "IMPOSTE SUL REDDITO": -imposte,
        "RISULTATO NETTO": P - imposte,
    }

# -------------------------------------------------------
# altri ricavi budget vs reale (da config.py)
# -------------------------------------------------------
altri_ricavi_budget = _v(out, "Budget", "ALTRI RICAVI E LAVORI IN ECONOMIA")
altri_ricavi_reale  = _v(out, "Reale",  "ALTRI RICAVI E LAVORI IN ECONOMIA")

print("DEBUG ALTRI RICAVI | Budget:", round(altri_ricavi_budget, 2),
      "| Reale:", round(altri_ricavi_reale, 2))

# -------------------------------------------------------
# Calcolo CE Mix Standard / Mix Effettivo
# -------------------------------------------------------
fixed_costs = get_table("output", "FixedCostsBudget.csv")
others = get_table("output", "OthersBudget.csv")

ms = scenario_numbers(mix_std, "Q_std_mix")
me = scenario_numbers(mix_eff, "Q_reale")

ce_ms = compute_ce_mix(*ms, fixed_costs, others, altri_ricavi=altri_ricavi_budget)
ce_me = compute_ce_mix(*me, fixed_costs, others, altri_ricavi=altri_ricavi_reale)

ce_ms = {norm_voce(k): float(v) for k, v in ce_ms.items()}
ce_me = {norm_voce(k): float(v) for k, v in ce_me.items()}

# -------------------------------------------------------
# Mappo su out + fisso voci fisse = Budget nei mix
# -------------------------------------------------------
out["_k"] = out["Voce"].map(norm_voce)
out["Mix Standard"] = out["_k"].map(lambda v: ce_ms.get(v, 0.0))
out["Mix Effettivo"] = out["_k"].map(lambda v: ce_me.get(v, 0.0))
out.drop(columns=["_k"], inplace=True)

# -------------------------------------------------------
# Delta + check + round
# -------------------------------------------------------
out["Δ Reale-Budget"] = out["Reale"] - out["Budget"]
out["Δ Mix Standard-Budget"] = out["Mix Standard"] - out["Budget"]
out["Δ Mix Effettivo-Standard"] = out["Mix Effettivo"] - out["Mix Standard"]
out["Δ Mix Reale-Effettivo"] = out["Reale"] - out["Mix Effettivo"]
out["Somma Δ Verifica"] = out["Δ Mix Standard-Budget"] + out["Δ Mix Effettivo-Standard"] + out["Δ Mix Reale-Effettivo"]
out["CHECK"] = out["Δ Reale-Budget"] - out["Somma Δ Verifica"]

for c in ["Budget","Reale","Mix Standard","Mix Effettivo",
          "Δ Reale-Budget","Δ Mix Standard-Budget","Δ Mix Effettivo-Standard","Δ Mix Reale-Effettivo",
          "Somma Δ Verifica","CHECK"]:
    out[c] = out[c].round(2)

out = out[[
    "Voce","Budget","Reale","Δ Reale-Budget",
    "Mix Standard","Δ Mix Standard-Budget",
    "Mix Effettivo","Δ Mix Effettivo-Standard",
    "Δ Mix Reale-Effettivo","Somma Δ Verifica","CHECK"
]]

# -------------------------------------------------------
# Salvo
# -------------------------------------------------------
safe_to_csv(out, OUTPUT / "AnalisiDegliScostamenti.csv")
print("\nFatto.")

