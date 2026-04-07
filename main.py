import google.generativeai as genai
import csv

# Configuration Gemini
genai.configure(api_key="VOTRE_CLE_API")
model = genai.GenerativeModel('gemini-1.5-flash')

def traiter_releve_bancaire(chemin_fichier):
    # Les instructions basées sur votre PDF d'exigences
    instructions = """
    Tu es un expert comptable. Analyse ce relevé et exporte en CSV avec ces règles strictes :
    1. Colonnes : Code, date, compte, libellé, débit, crédit. [cite: 7]
    2. Code : Toujours '5141'. 
    3. Date : Convertir 'jj mm' en 'jj/mm/2025'. [cite: 9]
    4. Compte : 
       - Si libellé contient (frais, forfait, commission, taxe, droit de timbre, retrait) -> 61470000. 
       - Sinon -> 44970000. 
    5. Libellé : Max 27 caractères, garde les noms propres, garde seulement 6 derniers chiffres des chèques. [cite: 12, 13, 14]
    6. Montants (Débit/Crédit) : 
       - INTERDIT d'utiliser le point (.). Utilise UNIQUEMENT la VIRGULE (,) pour les décimales. 
       - Supprime les espaces des milliers (ex: 1 000,00 devient 1000,00). 
    """
    
    # Simulation d'envoi du fichier à Gemini
    # (En production, utilisez genai.upload_file pour les PDF/JPG)
    # response = model.generate_content([instructions, document])
    
    return "Fichier prêt pour import Sage."
