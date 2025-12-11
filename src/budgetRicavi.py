# budgetRicavi.py
from data_loader import load_all
from config import EUR_TO_USD, DAZIO_PERC
import pandas as pd
import os

# ---------- 1. carico tutti i fogli ----------
dfs = load_all()

# ---------- 2. reference rapide ----------
df_bv = dfs.get("budget_vendite")

# ---------- 3. fix nomi colonne ----------
df_bv.columns = ['Articolo', 'Categoria', 'Quantita (kg)',
                 'P medio (€/kg)', 'P medio ($/kg)',
                 'CMP medio (€/kg)', 'CMP medio ($/kg)', 'MP con dazio']

# ---------- 4. converto le colonne numeriche ----------
num_cols = ['Quantita (kg)',
            'P medio (€/kg)', 'P medio ($/kg)',
            'CMP medio (€/kg)', 'CMP medio ($/kg)']
for c in num_cols:
    df_bv[c] = pd.to_numeric(df_bv[c], errors='coerce')

# ---------- 5. colonna PREZZO EURO ----------
ha_prezzo_eur = df_bv['P medio (€/kg)'].notna()
df_bv['Prezzo €/kg'] = df_bv['P medio (€/kg)'].where(
    ha_prezzo_eur,
    df_bv['P medio ($/kg)'] / EUR_TO_USD)

# ---------- 6. colonna CMP EURO ----------
ha_cmp_eur = df_bv['CMP medio (€/kg)'].notna()
df_bv['CMP €/kg (con dazio)'] = df_bv['CMP medio (€/kg)'].where(
    ha_cmp_eur,
    df_bv['CMP medio ($/kg)'] / EUR_TO_USD)

# dazio 14 % solo se CMP era in dollari e riga marcata "x"
mask_dazio   = df_bv['MP con dazio'].str.lower() == 'x'
mask_dollari = ~ha_cmp_eur
df_bv.loc[mask_dazio & mask_dollari, 'CMP €/kg (con dazio)'] *= (1 + DAZIO_PERC)

# ---------- 7. colonne nuove ----------
# 7a Famiglia
def famiglia(row):
    cat = row['Categoria']
    if cat == 'MP':                         return 'MP'
    if cat == 'PCL':                        return 'PCL'
    if cat == 'PF':
        art = row['Articolo']
        # ultimo carattere dopo lo spazio: PF A1 → A, PF V3 → V, PF P4 → P
        return art.split()[-1][0]           # prima lettera dell’ultimo blocco
    return ''

df_bv['Famiglia'] = df_bv.apply(famiglia, axis=1)

# 7b Ricavo e Costo
df_bv['Ricavo'] = df_bv['Quantita (kg)'] * df_bv['Prezzo €/kg']
df_bv['Costo']  = df_bv['Quantita (kg)'] * df_bv['CMP €/kg (con dazio)']

# ---------- 8. tabella finale ----------
out = df_bv[['Articolo', 'Categoria', 'Famiglia',
             'Quantita (kg)', 'Prezzo €/kg', 'CMP €/kg (con dazio)',
             'Ricavo', 'Costo']].copy()

# arrotondo a 3 decimali
out = out.round({'Prezzo €/kg': 3, 'CMP €/kg (con dazio)': 3,
                 'Ricavo': 2, 'Costo': 2})

# ---------- 9. salvo ----------
os.makedirs('../output', exist_ok=True)
out.to_csv('../output/budgetRicavi.csv',
           index=False, sep=';', decimal=',')
print('File budgetRicavi.csv creato con successo.')
print(out.head())