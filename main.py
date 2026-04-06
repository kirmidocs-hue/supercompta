from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from datetime import datetime

app = FastAPI()

# --- UTILITAIRES DE FORMATAGE ---
def format_maroc(n):
    # Règle : Montant avec virgule et 2 décimales [cite: 42, 64, 116]
    return f"{n:.2f}".replace('.', ',')

def export_csv(df, filename):
    # Règle : Séparateur point-virgule [cite: 42, 84]
    stream = io.StringIO()
    df.to_csv(stream, index=False, sep=';', encoding='utf-8-sig')
    return StreamingResponse(
        io.BytesIO(stream.getvalue().encode()), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- 1. MODULE RELEVÉS BANCAIRES ---
@app.post("/upload-releve")
async def handle_releve(file: UploadFile = File(...)):
    # Simulation des données extraites (à lier avec pdfplumber)
    # Règle : Code 5141 partout [cite: 25]
    # Règle : Libellé max 27 caractères [cite: 34]
    cols = ["Code", "Date", "Compte", "Libellé", "Débit", "Crédit"]
    
    # Logique de compte automatique[cite: 31]:
    # Si "CNSS" -> 44410000 | Si "FRAIS" -> 61470000 | Sinon -> 44970000 [cite: 30, 31]
    
    df = pd.DataFrame(columns=cols)
    return export_csv(df, "releves_compta.csv")

# --- 2. MODULE FACTURES (Journal ACH) ---
@app.post("/upload-facture")
async def handle_facture(file: UploadFile = File(...)):
    # Données extraites par l'OCR (Exemple)
    ttc = 0.0  # Montant total lu [cite: 62]
    date_fac = "01/01/2024" 
    ref_fac = "0000" # Règle : 4 derniers chiffres [cite: 49]
    societe = "NOM_SOCIETE"

    # CALCULS FACTURES [cite: 63, 68, 74]
    ht = ttc / 1.2
    tva = ttc - ht

    # Création des 3 lignes obligatoires [cite: 44, 56]
    data = [
        ["ACH", date_fac, ref_fac, "61110000", societe, format_maroc(ht), "0,00"],
        ["ACH", date_fac, ref_fac, "34550000", societe, format_maroc(tva), "0,00"],
        ["ACH", date_fac, ref_fac, "44110000", societe, "0,00", format_maroc(ttc)]
    ]
    
    df = pd.DataFrame(data, columns=["CODE JOURNAL", "DATE", "RÉFÉRENCE", "COMPTE", "LIBELLÉ", "DÉBIT", "CRÉDIT"])
    return export_csv(df, "factures_compta.csv")

# --- 3. MODULE SALAIRES (Journal OD) ---
@app.post("/upload-salaires")
async def handle_salaires(file: UploadFile = File(...)):
    # Données sources (SB, Prime, IR) [cite: 86, 88, 89, 90]
    sb = 0.0 
    prime = 0.0
    ir = 0.0
    date_paie = "31/01/2024"
    
    # Règle Libellé : salaire mm/aa [cite: 110]
    date_obj = datetime.strptime(date_paie, "%d/%m/%Y")
    lib = f"salaire {date_obj.strftime('%m/%y')}"

    # CALCULS DÉBITS [cite: 112, 113, 114, 115]
    d61711 = sb
    d61712 = prime
    d61741 = sb * 0.1698  # Patronal CNSS
    d61743 = sb * 0.0411  # Patronal AMO
    
    # CALCULS CRÉDITS [cite: 118, 119]
    c4441_1 = sb * 0.2146 # Salarial CNSS
    c4441_2 = sb * 0.0637 # Salarial AMO
    c44525 = ir
    
    # CALCUL ÉQUILIBRE (Ligne 8 - Compte 44320000) 
    total_debit = d61711 + d61712 + d61741 + d61743
    total_credit_partiel = c4441_1 + c4441_2 + c44525
    c44320 = total_debit - total_credit_partiel

    # Génération des 8 lignes dans l'ordre exact [cite: 100, 101-108]
    rows = [
        ["OD", date_paie, "61711000", lib, format_maroc(d61711), "0,00"],
        ["OD", date_paie, "61712000", lib, format_maroc(d61712), "0,00"],
        ["OD", date_paie, "61741000", lib, format_maroc(d61741), "0,00"],
        ["OD", date_paie, "61743000", lib, format_maroc(d61743), "0,00"],
        ["OD", date_paie, "44410000", lib, "0,00", format_maroc(c4441_1)],
        ["OD", date_paie, "44410000", lib, "0,00", format_maroc(c4441_2)],
        ["OD", date_paie, "4452500",  lib, "0,00", format_maroc(c44525)],
        ["OD", date_paie, "44320000", lib, "0,00", format_maroc(c44320)]
    ]
    
    df = pd.DataFrame(rows, columns=["Type", "Date", "Compte", "Libellé", "Débit", "Crédit"])
    return export_csv(df, "salaires_compta.csv")