# # db.py
# import os
# from pymongo import MongoClient
# from dotenv import load_dotenv


# load_dotenv()
# MONGO_URI = os.getenv('MONGO_URI')
# DB_NAME = os.getenv('DB_NAME','restaurants_db')


# if not MONGO_URI:
#     raise RuntimeError('MONGO_URI non défini')


# client = MongoClient(MONGO_URI)
# db = client[DB_NAME]


# def get_collection(name=None):
#     return db[name or os.getenv('COLL_NAME','notations')]

# db.py
# Ce fichier n'est plus utilisé - Google Sheets est maintenant la source unique de données
# Conservé pour compatibilité si d'autres fichiers l'importent

def get_collection(name=None):
    """
    DEPRECATED: MongoDB n'est plus utilisé.
    Google Sheets est maintenant la source unique de données.
    """
    raise NotImplementedError(
        "MongoDB n'est plus utilisé. "
        "Utilisez les fonctions de gsheet_sync.py pour interagir avec Google Sheets."
    )