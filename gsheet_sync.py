# # # gsheet_sync.py
# # import os
# # import gspread
# # import pandas as pd
# # from oauth2client.service_account import ServiceAccountCredentials
# # from db import get_collection

# # # Variables d'environnement (fichier .env ou valeurs par défaut)
# # GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "./credentials/service_account.json")
# # SHEET_ID = os.getenv("SHEET_ID", "14HCjCU-ejwi93ygofSetYDS0VlS4cXjcnjA9WqYx3Uk")
# # WORKSHEET_NAME = os.getenv("SHEET_WORKSHEET_NAME", "Feuille 2")

# # # Scopes Google API
# # scope = [
# #     "https://spreadsheets.google.com/feeds",
# #     "https://www.googleapis.com/auth/spreadsheets",
# #     "https://www.googleapis.com/auth/drive"
# # ]

# # def read_sheet_to_df():
# #     """Lit la feuille Google Sheets et retourne un DataFrame Pandas"""
# #     creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, scope)
# #     client = gspread.authorize(creds)
# #     sh = client.open_by_key(SHEET_ID)
# #     ws = sh.worksheet(WORKSHEET_NAME)
# #     data = ws.get_all_records()
# #     df = pd.DataFrame(data)

# #     # Nettoyage colonnes : éviter espaces/accents dans les clés
# #     df.columns = [c.strip() for c in df.columns]
# #     return df

# # def sync_sheet_to_mongo():
# #     """Synchronise la feuille Google Sheets vers MongoDB (upsert basé sur 'nom')"""
# #     df = read_sheet_to_df()
# #     coll = get_collection()

# #     count = 0
# #     for _, row in df.iterrows():
# #         doc = row.to_dict()
# #         # Remplacer NaN par None
# #         doc = {k: (None if pd.isna(v) else v) for k, v in doc.items()}

# #         if "nom" in doc and doc["nom"]:
# #             coll.update_one(
# #                 {"nom": doc["nom"]},   # condition pour trouver le resto existant
# #                 {"$set": doc},         # mise à jour complète des champs
# #                 upsert=True            # insère si n’existe pas
# #             )
# #             count += 1

# #     return count

# # if __name__ == "__main__":
# #     n = sync_sheet_to_mongo()
# #     print(f"{n} lignes synchronisées (upsert).")



# # gsheet_sync.py
# import os
# import gspread
# import pandas as pd
# from oauth2client.service_account import ServiceAccountCredentials
# from db import get_collection

# # Variables d'environnement
# GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "./credentials/service_account.json")
# SHEET_ID = os.getenv("SHEET_ID", "14HCjCU-ejwi93ygofSetYDS0VlS4cXjcnjA9WqYx3Uk")
# WORKSHEET_NAME = os.getenv("SHEET_WORKSHEET_NAME", "Feuille 2")

# # Scopes Google API
# scope = [
#     "https://spreadsheets.google.com/feeds",
#     "https://www.googleapis.com/auth/spreadsheets",
#     "https://www.googleapis.com/auth/drive"
# ]

# def get_gsheet_client():
#     """Retourne un client gspread autorisé"""
#     creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, scope)
#     return gspread.authorize(creds)

# def normalize_decimal(value):
#     """Convertit les virgules en points pour les nombres"""
#     if isinstance(value, str):
#         return value.replace(',', '.')
#     return value

# def read_sheet_to_df():
#     """Lit la feuille Google Sheets et retourne un DataFrame Pandas"""
#     client = get_gsheet_client()
#     sh = client.open_by_key(SHEET_ID)
#     ws = sh.worksheet(WORKSHEET_NAME)
#     data = ws.get_all_records()
#     df = pd.DataFrame(data)

#     # Nettoyage colonnes
#     df.columns = [c.strip().lower() for c in df.columns]
    

#     # Normaliser les colonnes numériques (virgules → points)
#     # numeric_cols = ['marine', 'corentin', 'quentin']
#     # for col in numeric_cols:
#     #     if col in df.columns:
#     #         df[col] = df[col].apply(normalize_decimal)
#     #
#     #          df[col] = pd.to_numeric(df[col], errors='coerce')
    
#     # Convertir "combien de fois on a mangé" en entier
#     if 'combien de fois on a mangé' in df.columns:
#         df['combien de fois on a mangé'] = pd.to_numeric(
#             df['combien de fois on a mangé'], errors='coerce'
#         ).fillna(0).astype(int)
    
#     return df

# def sync_sheet_to_mongo():
#     """Synchronise Google Sheets → MongoDB (upsert basé sur 'nom')"""
#     df = read_sheet_to_df()
#     coll = get_collection()

#     # Supprimer tous les docs existants qui ne sont plus dans le sheet
#     sheet_names = set(df['nom'].tolist())
#     existing_docs = list(coll.find({}, {'nom': 1}))
    
#     for doc in existing_docs:
#         if doc.get('nom') and doc['nom'] not in sheet_names:
#             coll.delete_one({'nom': doc['nom']})
#             print(f"Supprimé de MongoDB: {doc['nom']}")

#     # Upsert les données du sheet
#     count = 0
#     for _, row in df.iterrows():
#         doc = row.to_dict()
#         doc = {k: (None if pd.isna(v) else v) for k, v in doc.items()}

#         if "nom" in doc and doc["nom"]:
#             coll.update_one(
#                 {"nom": doc["nom"]},
#                 {"$set": doc},
#                 upsert=True
#             )
#             count += 1

#     return count

# def sync_mongo_to_sheet():
#     """Synchronise MongoDB → Google Sheets (écrase complètement le sheet)"""
#     client = get_gsheet_client()
#     sh = client.open_by_key(SHEET_ID)
#     ws = sh.worksheet(WORKSHEET_NAME)
    
#     coll = get_collection()
#     docs = list(coll.find({}, {'_id': 0}))
    
#     if not docs:
#         return 0
    
#     # Créer DataFrame avec les colonnes dans le bon ordre
#     df = pd.DataFrame(docs)
    
#     # S'assurer que toutes les colonnes requises existent
#     required_cols = ['nom', 'marine', 'corentin', 'quentin', 'combien de fois on a mangé']
#     for col in required_cols:
#         if col not in df.columns:
#             df[col] = None
    
#     # Réorganiser les colonnes
#     df = df[required_cols]
    
#     # Remplacer les NaN par des chaînes vides
#     df = df.fillna('')
    
#     # Formater les nombres avec virgules pour Google Sheets
#     for col in ['marine', 'corentin', 'quentin']:
#         if col in df.columns:
#             df[col] = df[col].apply(lambda x: str(x).replace('.', ',') if x != '' else '')
    
#     # Effacer le sheet et écrire les nouvelles données
#     ws.clear()
    
#     # Écrire les en-têtes (avec majuscules)
#     headers = ['nom', 'Marine', 'Corentin', 'Quentin', 'combien de fois on a mangé']
#     ws.update('A1:E1', [headers])

#     # Écrire les données
#     if len(df) > 0:
#         data_rows = df.values.tolist()
#         ws.update(f'A2:E{len(data_rows)+1}', data_rows)

#     return len(df)

# def bidirectional_sync():
#     """Synchronisation bidirectionnelle complète"""
#     # 1. D'abord, sync Sheet → Mongo
#     count_from_sheet = sync_sheet_to_mongo()
    
#     # 2. Ensuite, sync Mongo → Sheet (pour inclure les modifications faites sur le site)
#     count_to_sheet = sync_mongo_to_sheet()
    
#     return count_from_sheet, count_to_sheet

# if __name__ == "__main__":
#     from_sheet, to_sheet = bidirectional_sync()
#     print(f"Synchronisé: {from_sheet} lignes depuis Sheet, {to_sheet} lignes vers Sheet")


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