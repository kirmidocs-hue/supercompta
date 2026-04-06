import streamlit as st
import pandas as pd
import pdfplumber
import io
from datetime import datetime

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="SUPER COMPTA - TANGER", layout="wide")
st.title("📂 SUPER COMPTA - Traitement Multi-Lignes")
st.sidebar.info("Utilisateur : FAISAL KARMI\nExpertise : Comptabilité Maroc (PCM)")

def format_maroc(n):
    try:
        return f"{float(n):.2f}".replace('.', ',')
    except:
        return "0,00"

def to_csv(df):
    return df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

tabs = st.tabs(["🏦 Relevés Bancaires (Multi-pages)", "🧾 Factures (TVA 20%)", "💰 Salaires (8 Lignes)"])

# --- 1. MODULE BANQUE : LECTURE COMPLÈTE DU PDF ---
with tabs[0]:
    st.header("Extraction de toutes les lignes du Relevé")
    uploaded_bank = st.file_uploader("Charger le Relevé PDF", type=['pdf'])
    
    if uploaded_bank:
        bank_data = []
        with pdfplumber.open(uploaded_bank) as pdf:
            for page in pdf.pages:
                table = page.extract_table() # Tente d'extraire les tableaux du PDF
                if table:
                    for row in table[1:]: # Saute l'en-tête du tableau
                        if row[0]: # Si la ligne n'est pas vide
                            # On adapte ici les colonnes selon un format standard
                            # Règle : Code 51410000 par défaut
                            date_val = row[0]
                            libelle = str(row[1])[:27] if row[1] else "TRANSACTION"
                            debit = row[2] if len(row) > 2 else "0"
                            credit = row[3] if len(row) > 3 else "0"
                            
                            bank_data.append([
                                "5141", date_val, "51410000", libelle, 
                                format_maroc(debit), format_maroc(credit)
                            ])
        
        if bank_data:
            df_bank = pd.DataFrame(bank_data, columns=["Code", "Date", "Compte", "Libellé", "Débit", "Crédit"])
            st.success(f"✅ {len(df_bank)} lignes extraites du relevé.")
            st.dataframe(df_bank)
            st.download_button("📥 Télécharger TOUT le relevé (CSV)", to_csv(df_bank), "banque_complet.csv")
        else:
            st.warning("Aucune donnée tabulaire détectée. Vérifiez le format du PDF.")

# --- 2. MODULE FACTURES (Multi-fichiers) ---
with tabs[1]:
    st.header("Journal des Achats (Multi-fichiers)")
    uploaded_files = st.file_uploader("Charger Factures (JPG/PDF)", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
    
    if uploaded_files:
        all_entries = []
        for f in uploaded_files:
            # Pour chaque fichier, on demande le montant (en attendant l'OCR complet)
            col1, col2 = st.columns(2)
            with col1: st.write(f"Fichier : {f.name}")
            with col2: ttc = st.number_input(f"Montant TTC ({f.name})", value=0.0, key=f.name)
            
            if ttc > 0:
                ht = ttc / 1.2
                tva = ttc - ht
                ref = f.name[:4] # Prend les 4 premiers caractères comme référence
                
                all_entries.extend([
                    ["ACH", "01/04/2026", ref, "61110000", "ACHAT MARCHANDISE", format_maroc(ht), "0,00"],
                    ["ACH", "01/04/2026", ref, "34550000", "ETAT TVA RECUP", format_maroc(tva), "0,00"],
                    ["ACH", "01/04/2026", ref, "44110000", "FOURNISSEUR", "0,00", format_maroc(ttc)]
                ])
        
        if all_entries:
            df_ach = pd.DataFrame(all_entries, columns=["Journal", "Date", "Réf", "Compte", "Libellé", "Débit", "Crédit"])
            st.dataframe(df_ach)
            st.download_button("📥 Télécharger Journal ACH (CSV)", to_csv(df_ach), "achats_global.csv")

# --- 3. MODULE SALAIRES (Stricte 8 Lignes) ---
with tabs[2]:
    # (Le code reste identique pour garantir vos 8 lignes obligatoires)
    st.header("Journal OD - Paie")
    # ... (Garder la logique de calcul avec les taux 16,98% et 4,11%)
