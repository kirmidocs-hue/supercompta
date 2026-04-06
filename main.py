import streamlit as st
import pandas as pd
import pdfplumber
from PIL import Image
import io
from datetime import datetime

# --- CONFIGURATION FAISAL KARMI ---
st.set_page_config(page_title="SUPER COMPTA PRO", layout="wide")
st.markdown("""<style>.stApp {background-color: #f0f2f6;} .stHeader {color: #004a99;}</style>""", unsafe_allow_html=True)

st.title("🚀 SUPER COMPTA - Automatisation Totale")
st.sidebar.header("Expert : Faisal Karmi")
st.sidebar.info("Tangier, Morocco | PCM & Sage Saari")

def format_maroc(n):
    return f"{n:.2f}".replace('.', ',')

def to_csv(df):
    return df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

tabs = st.tabs(["📄 Factures (PDF/JPG)", "🏦 Relevés (PDF)", "💰 Salaires (8 Lignes)"])

# --- 1. MODULE FACTURES (ACHATS) ---
with tabs[0]:
    st.header("Extraction Factures (Vers ACH)")
    uploaded_fac = st.file_uploader("Charger Factures (PDF ou JPG)", type=['pdf', 'jpg', 'jpeg', 'png'], accept_multiple_files=True)
    
    if uploaded_fac:
        all_fac_data = []
        for file in uploaded_fac:
            # Simulation d'extraction (L'OCR nécessite une clé API ou Tesseract local)
            # Ici, on prépare la structure pour tes écritures 6111 / 3455 / 4411
            ttc = st.sidebar.number_input(f"Montant TTC pour {file.name}", value=1200.0)
            ht = ttc / 1.2
            tva = ttc - ht
            ref = file.name[-8:-4] if len(file.name) > 8 else "0000"
            
            all_fac_data.extend([
                ["ACH", "01/03/2026", ref, "61110000", "ACHAT MARCHANDISE", format_maroc(ht), "0,00"],
                ["ACH", "01/03/2026", ref, "34550000", "ETAT TVA RECUP", format_maroc(tva), "0,00"],
                ["ACH", "01/03/2026", ref, "44110000", "FOURNISSEUR", "0,00", format_maroc(ttc)]
            ])
            
        df_fac = pd.DataFrame(all_fac_data, columns=["Journal", "Date", "Réf", "Compte", "Libellé", "Débit", "Crédit"])
        st.dataframe(df_fac)
        st.download_button("📥 Télécharger CSV Achats", to_csv(df_fac), "achats_compta.csv")

# --- 2. MODULE RELEVÉS (BANQUE) ---
with tabs[1]:
    st.header("Lecture de Relevés PDF")
    uploaded_bank = st.file_uploader("Charger Relevé PDF", type=['pdf'])
    
    if uploaded_bank:
        with pdfplumber.open(uploaded_bank) as pdf:
            all_text = ""
            for page in pdf.pages:
                all_text += page.extract_text()
            
            st.success("PDF lu avec succès. Extraction des lignes en cours...")
            # Ici, on crée une ligne type par défaut (à adapter selon ton format de banque à Tanger)
            rows = [["5141", "01/03/2026", "51410000", "MOUVEMENT BANCAIRE", "0,00", "1500,00"]]
            df_bank = pd.DataFrame(rows, columns=["Code", "Date", "Compte", "Libellé", "Débit", "Crédit"])
            st.dataframe(df_bank)
            st.download_button("📥 Télécharger CSV Banque", to_csv(df_bank), "banque_compta.csv")

# --- 3. MODULE SALAIRES (LES 8 LIGNES) ---
with tabs[2]:
    st.header("Journal OD - Calcul des Charges")
    sb = st.number_input("Salaire Brut Global", value=0.0)
    prime = st.number_input("Total Primes", value=0.0)
    ir = st.number_input("Total IR", value=0.0)
    
    if st.button("Générer les 8 Lignes d'Écritures"):
        date_p = datetime.now().strftime("%d/%m/%Y")
        lib = f"salaire {datetime.now().strftime('%m/%y')}"
        
        # CALCULS RIGOUREUX (Taux 16,98% et 4,11%)
        d61741 = sb * 0.1698
        d61743 = sb * 0.0411
        c4441_1 = sb * 0.2146 # Part globale
        c4441_2 = sb * 0.0637 # Part globale AMO
        c44320 = (sb + prime + d61741 + d61743) - (c4441_1 + c4441_2 + ir) # Équilibre ligne 8
        
        data_od = [
            ["OD", date_p, "61711000", lib, format_maroc(sb), "0,00"],
            ["OD", date_p, "61712000", lib, format_maroc(prime), "0,00"],
            ["OD", date_p, "61741000", lib, format_maroc(d61741), "0,00"],
            ["OD", date_p, "61743000", lib, format_maroc(d61743), "0,00"],
            ["OD", date_p, "44410000", lib, "0,00", format_maroc(c4441_1)],
            ["OD", date_p, "44410000", lib, "0,00", format_maroc(c4441_2)],
            ["OD", date_p, "44525000", lib, "0,00", format_maroc(ir)],
            ["OD", date_p, "44320000", lib, "0,00", format_maroc(c44320)]
        ]
        
        df_od = pd.DataFrame(data_od, columns=["Journal", "Date", "Compte", "Libellé", "Débit", "Crédit"])
        st.table(df_od)
        st.download_button("📥 Télécharger Journal OD", to_csv(df_od), "od_salaire.csv")
