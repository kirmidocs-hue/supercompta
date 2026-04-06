import streamlit as st
import pandas as pd
import io
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="SUPER COMPTA - FAISAL KARMI", layout="wide")

st.title("📂 SUPER COMPTA - Automatisation Comptable")
st.subheader("Expertise : Faisal Karmi | Localisation : Tanger")

# --- UTILITAIRES DE FORMATAGE ---
def format_maroc(n):
    # Règle : Montant avec virgule et 2 décimales
    return f"{n:.2f}".replace('.', ',')

def convert_df_to_csv(df):
    # Règle : Séparateur point-virgule et encodage Excel
    return df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

# --- ONGLETS POUR CHAQUE MODULE ---
tab1, tab2, tab3 = st.tabs(["📊 Relevés Bancaires", "🧾 Factures (ACH)", "💰 Salaires (OD)"])

# --- 1. MODULE RELEVÉS ---
with tab1:
    st.header("Traitement des Relevés")
    file_releve = st.file_uploader("Charger le relevé (Excel/CSV)", key="releve")
    if file_releve:
        # Logique simplifiée pour l'exemple
        cols = ["Code", "Date", "Compte", "Libellé", "Débit", "Crédit"]
        df_releve = pd.DataFrame([["5141", "01/03/2026", "51410000", "VIREMENT RECU", "0,00", "1500,00"]], columns=cols)
        st.dataframe(df_releve)
        st.download_button("📥 Télécharger CSV (Virgules)", convert_df_to_csv(df_releve), "releves_compta.csv", "text/csv")

# --- 2. MODULE FACTURES (Journal ACH) ---
with tab2:
    st.header("Journal des Achats")
    file_facture = st.file_uploader("Charger les factures", key="facture")
    if file_facture:
        ttc = st.number_input("Montant TTC Lu", value=1200.0)
        ht = ttc / 1.2
        tva = ttc - ht
        
        data = [
            ["ACH", "01/03/2026", "0000", "61110000", "ACHAT MARCHANDISE", format_maroc(ht), "0,00"],
            ["ACH", "01/03/2026", "0000", "34550000", "ETAT TVA RECUP", format_maroc(tva), "0,00"],
            ["ACH", "01/03/2026", "0000", "44110000", "FOURNISSEUR", "0,00", format_maroc(ttc)]
        ]
        df_fac = pd.DataFrame(data, columns=["CODE JOURNAL", "DATE", "RÉFÉRENCE", "COMPTE", "LIBELLÉ", "DÉBIT", "CRÉDIT"])
        st.table(df_fac)
        st.download_button("📥 Télécharger Journal ACH", convert_df_to_csv(df_fac), "factures_compta.csv", "text/csv")

# --- 3. MODULE SALAIRES (Journal OD) ---
with tab3:
    st.header("Génération des 8 Lignes de Salaire")
    sb = st.number_input("Salaire Brut (SB)", value=0.0)
    prime = st.number_input("Primes", value=0.0)
    ir = st.number_input("IR (Retenue)", value=0.0)
    
    if st.button("Calculer les 8 lignes"):
        date_paie = datetime.now().strftime("%d/%m/%Y")
        lib = f"salaire {datetime.now().strftime('%m/%y')}"
        
        # CALCULS DÉBITS (Règles strictes)
        d61711, d61712 = sb, prime
        d61741 = sb * 0.1698  # Patronal CNSS
        d61743 = sb * 0.0411  # Patronal AMO
        
        # CALCULS CRÉDITS
        c4441_1 = sb * 0.2146 # Part globale CNSS
        c4441_2 = sb * 0.0637 # Part globale AMO
        c44525 = ir
        
        # ÉQUILIBRE LIGNE 8 (Compte 44320000)
        c44320 = (d61711 + d61712 + d61741 + d61743) - (c4441_1 + c4441_2 + c44525)

        rows = [
            ["OD", date_paie, "61711000", lib, format_maroc(d61711), "0,00"],
            ["OD", date_paie, "61712000", lib, format_maroc(d61712), "0,00"],
            ["OD", date_paie, "61741000", lib, format_maroc(d61741), "0,00"],
            ["OD", date_paie, "61743000", lib, format_maroc(d61743), "0,00"],
            ["OD", date_paie, "44410000", lib, "0,00", format_maroc(c4441_1)],
            ["OD", date_paie, "44410000", lib, "0,00", format_maroc(c4441_2)],
            ["OD", date_paie, "44525000", lib, "0,00", format_maroc(c44525)],
            ["OD", date_paie, "44320000", lib, "0,00", format_maroc(c44320)]
        ]
        
        df_sal = pd.DataFrame(rows, columns=["Type", "Date", "Compte", "Libellé", "Débit", "Crédit"])
        st.table(df_sal)
        st.download_button("📥 Télécharger Journal OD", convert_df_to_csv(df_sal), "salaires_compta.csv", "text/csv")
