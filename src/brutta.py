# test_somma_AVP.py
import pandas as pd

# 1. leggo il file
df = pd.read_csv('../output/budgetRicavi.csv',
                 sep=';', decimal=',')

# 2. filtro A + V + P
avp_df = df[df['Famiglia'].isin(['A', 'V', 'P'])]

# 3. somma ricavi
totale = avp_df['Ricavo'].sum()

# 4. output
print(f'Totale Ricavi famiglie A+V+P: {totale:,.2f} €')