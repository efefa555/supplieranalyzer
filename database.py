import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Définir le chemin de la base de données
DB_PATH = "data/suppliers.db"

# S'assurer que le répertoire data existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Créer le moteur SQLAlchemy
engine = create_engine(f'sqlite:///{DB_PATH}')
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Définir le modèle de données pour les fournisseurs
class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    nom_fournisseur = Column(String(100), nullable=False)
    date_commande = Column(Date, nullable=False)
    montant_commande = Column(Float, nullable=False)
    date_reception = Column(Date, nullable=True)
    date_paiement = Column(Date, nullable=True)
    delai_paiement = Column(Integer, nullable=True)
    jours_retard = Column(Integer, nullable=True)
    statut_paiement = Column(String(20), nullable=True)
    montant_penalite = Column(Float, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'Nom du fournisseur': self.nom_fournisseur,
            'Date de commande': self.date_commande,
            'Montant de la commande': self.montant_commande,
            'Date de réception': self.date_reception,
            'Date de paiement': self.date_paiement,
            'Délai de paiement': self.delai_paiement,
            'Jours de retard': self.jours_retard,
            'Statut du paiement': self.statut_paiement,
            'Montant pénalité': self.montant_penalite
        }

# Créer la base de données et les tables si elles n'existent pas
def init_db():
    Base.metadata.create_all(engine)
    print(f"Base de données initialisée dans {DB_PATH}")

# Fonction pour ajouter un fournisseur à la base de données
def add_supplier(supplier_data):
    session = Session()
    try:
        supplier = Supplier(
            nom_fournisseur=supplier_data['Nom du fournisseur'],
            date_commande=supplier_data['Date de commande'],
            montant_commande=float(supplier_data['Montant de la commande']),
            date_reception=supplier_data.get('Date de réception'),
            date_paiement=supplier_data.get('Date de paiement'),
            delai_paiement=supplier_data.get('Délai de paiement'),
            jours_retard=supplier_data.get('Jours de retard', 0),
            statut_paiement=supplier_data.get('Statut du paiement', 'Non déterminé'),
            montant_penalite=supplier_data.get('Montant pénalité', 0.0)
        )
        session.add(supplier)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de l'ajout du fournisseur: {e}")
        return False
    finally:
        session.close()

# Fonction pour récupérer tous les fournisseurs
def get_all_suppliers():
    session = Session()
    try:
        suppliers = session.query(Supplier).all()
        return [supplier.to_dict() for supplier in suppliers]
    except Exception as e:
        print(f"Erreur lors de la récupération des fournisseurs: {e}")
        return []
    finally:
        session.close()

# Fonction pour convertir un dataframe en liste de fournisseurs et les ajouter à la base
def add_suppliers_from_dataframe(df):
    success_count = 0
    total_count = len(df)
    
    for _, row in df.iterrows():
        supplier_data = row.to_dict()
        if add_supplier(supplier_data):
            success_count += 1
    
    return success_count, total_count

# Fonction pour récupérer les fournisseurs sous forme de dataframe
def get_suppliers_dataframe():
    suppliers = get_all_suppliers()
    if not suppliers:
        return pd.DataFrame()
    
    df = pd.DataFrame(suppliers)
    
    # Convertir les colonnes de date
    date_columns = ['Date de commande', 'Date de réception', 'Date de paiement']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    return df

# Fonction pour mettre à jour un fournisseur existant
def update_supplier(supplier_id, supplier_data):
    session = Session()
    try:
        supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier:
            if 'Nom du fournisseur' in supplier_data:
                supplier.nom_fournisseur = supplier_data['Nom du fournisseur']
            if 'Date de commande' in supplier_data:
                supplier.date_commande = supplier_data['Date de commande']
            if 'Montant de la commande' in supplier_data:
                supplier.montant_commande = supplier_data['Montant de la commande']
            if 'Date de réception' in supplier_data:
                supplier.date_reception = supplier_data['Date de réception']
            if 'Date de paiement' in supplier_data:
                supplier.date_paiement = supplier_data['Date de paiement']
            if 'Délai de paiement' in supplier_data:
                supplier.delai_paiement = supplier_data['Délai de paiement']
            if 'Jours de retard' in supplier_data:
                supplier.jours_retard = supplier_data['Jours de retard']
            if 'Statut du paiement' in supplier_data:
                supplier.statut_paiement = supplier_data['Statut du paiement']
            if 'Montant pénalité' in supplier_data:
                supplier.montant_penalite = supplier_data['Montant pénalité']
            
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la mise à jour du fournisseur: {e}")
        return False
    finally:
        session.close()

# Fonction pour supprimer un fournisseur
def delete_supplier(supplier_id):
    session = Session()
    try:
        supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier:
            session.delete(supplier)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la suppression du fournisseur: {e}")
        return False
    finally:
        session.close()

# Fonction pour supprimer tous les fournisseurs
def delete_all_suppliers():
    session = Session()
    try:
        session.query(Supplier).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la suppression de tous les fournisseurs: {e}")
        return False
    finally:
        session.close()

# Fonction pour vérifier si la base de données existe et contient des données
def db_has_data():
    try:
        # Vérifier si le fichier de base de données existe
        if not os.path.exists(DB_PATH):
            return False
        
        # Vérifier s'il y a des données dans la table suppliers
        session = Session()
        count = session.query(Supplier).count()
        session.close()
        
        return count > 0
    except Exception as e:
        print(f"Erreur lors de la vérification de la base de données: {e}")
        return False

# Initialiser la base de données au démarrage du module
init_db()