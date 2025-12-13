# run_all.py
import subprocess
import sys
from pathlib import Path

scripts = [
    "budgetRicavi.py",
    "budgetCostiVariabili.py",
    "budgetCostiFissi.py",
    "budgetAltriCosti.py",
    "budgetContoEconomico.py",
    "analisiScostamentiMix.py"
]

base_dir = Path(__file__).parent

for script in scripts:
    print(f"\n{'='*60}")
    print(f"LANCIO  {script}")
    print('='*60)
    try:
        subprocess.run([sys.executable, base_dir / script], check=True)
        print(f"\nFINE  {script}  ✔")
    except subprocess.CalledProcessError as e:
        print(f"\nERRORE durante {script}  ✘")
        print(e)
        break
else:
    print("\n" + "="*60)
    print("TUTTI GLI SCRIPT SONO TERMINATI CON SUCCESSO")
    print("="*60)