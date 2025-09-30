# gsheet_sync.py
import os
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials



# Variables d'environnement
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "./credentials/service_account.json")
SHEET_ID = os.getenv("SHEET_ID", "14HCjCU-ejwi93ygofSetYDS0VlS4cXjcnjA9WqYx3Uk")
WORKSHEET_NAME = os.getenv("SHEET_WORKSHEET_NAME", "Feuille 2")

# Scopes Google API
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gsheet_client():
    """Retourne un client gspread autorisé"""
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, scope)
    return gspread.authorize(creds)

def normalize_decimal(value):
    """Convertit les virgules en points pour les nombres"""
    if isinstance(value, str):
        return value.replace(',', '.')
    return value

def read_sheet_to_df():
    """Lit la feuille Google Sheets et retourne un DataFrame Pandas"""
    client = get_gsheet_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    data = ws.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        return df

    # Nettoyage colonnes - garder la casse originale
    df.columns = [c.strip() for c in df.columns]
    
    # Normaliser les colonnes numériques (virgules → points)
    numeric_cols = ['Marine', 'Corentin', 'Quentin']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(normalize_decimal)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convertir "combien de fois on a mangé" en entier
    if 'combien de fois on a mangé' in df.columns:
        df['combien de fois on a mangé'] = pd.to_numeric(
            df['combien de fois on a mangé'], errors='coerce'
        ).fillna(0).astype(int)
    
    return df

def add_restaurant_to_sheet(nom, marine, corentin, quentin, visites):
    """Ajoute un nouveau restaurant directement dans Google Sheets"""
    client = get_gsheet_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    
    # # Calculer la moyenne
    # moyenne = round((marine + corentin + quentin) / 3, 2)
    
    # # Formater avec virgules pour Google Sheets
    # marine_str = str(marine).replace('.', ',')
    # corentin_str = str(corentin).replace('.', ',')
    # quentin_str = str(quentin).replace('.', ',')
    # moyenne_str = str(moyenne).replace('.', ',')
    
    # Ajouter la ligne à la fin
    new_row = [nom, marine_str, corentin_str, quentin_str, visites]
    ws.append_row(new_row)
    
    return True

def update_restaurant_in_sheet(nom, marine, corentin, quentin, visites):
    """Met à jour un restaurant existant dans Google Sheets"""
    client = get_gsheet_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    
    # Trouver la ligne du restaurant
    try:
        cell = ws.find(nom)
        row_number = cell.row
        
        # # Calculer la moyenne
        # moyenne = round((marine + corentin + quentin) / 3, 2)
        
        # # Formater avec virgules
        # marine_str = str(marine).replace('.', ',')
        # corentin_str = str(corentin).replace('.', ',')
        # quentin_str = str(quentin).replace('.', ',')
        # moyenne_str = str(moyenne).replace('.', ',')
        
        # Mettre à jour la ligne
        updated_row = [nom, marine_str, corentin_str, quentin_str, visites]
        ws.update(f'A{row_number}:E{row_number}', [updated_row])

        return True
    except gspread.exceptions.CellNotFound:
        return False

def delete_restaurant_from_sheet(nom):
    """Supprime un restaurant de Google Sheets"""
    client = get_gsheet_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    
    try:
        cell = ws.find(nom)
        ws.delete_rows(cell.row)
        return True
    except gspread.exceptions.CellNotFound:
        return False

def restaurant_exists(nom):
    """Vérifie si un restaurant existe déjà dans Google Sheets"""
    df = read_sheet_to_df()
    if df.empty:
        return False
    return nom in df['nom'].values

if __name__ == "__main__":
    # Test de lecture
    df = read_sheet_to_df()
    print(f"Lecture de {len(df)} restaurants depuis Google Sheets")
    print(df.head())