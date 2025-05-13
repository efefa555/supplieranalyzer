import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import io

# Constants for Law 69-21
PENALTY_INTEREST_RATE = 0.03  # 3% as an example from Law 69-21

def load_sample_data():
    """
    Create a DataFrame with columns needed for the application
    Returns a DataFrame with sample structure but no data
    """
    df = pd.DataFrame(columns=[
        'Nom du fournisseur',
        'Date de commande',
        'Montant de la commande',
        'Date de réception',
        'Date de paiement',
        'Délai de paiement',
        'Statut du paiement'
    ])
    return df

def process_data(df):
    """
    Process the uploaded data to calculate payment delays and status
    """
    if df.empty:
        return df
    
    # Ensure date columns are datetime objects
    date_columns = ['Date de commande', 'Date de réception', 'Date de paiement']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calculate payment delay
    if 'Date de commande' in df.columns and 'Date de paiement' in df.columns:
        df['Délai de paiement'] = (df['Date de paiement'] - df['Date de commande']).dt.days
    
    # Determine payment status (assuming 60 days is the standard delay)
    # This threshold can be adjusted based on Law 69-21 specifications
    standard_delay = 60
    if 'Délai de paiement' in df.columns:
        df['Statut du paiement'] = df['Délai de paiement'].apply(
            lambda x: 'Dans les délais' if x <= standard_delay else 'En retard'
        )
    
    # Ensure monetary values are numeric
    if 'Montant de la commande' in df.columns:
        df['Montant de la commande'] = pd.to_numeric(df['Montant de la commande'], errors='coerce')
    
    return df

def calculate_penalties(df):
    """
    Calculate penalties for late payments according to Law 69-21
    """
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    df_with_penalties = df.copy()
    
    # Standard delay based on Law 69-21 (assumed 60 days)
    standard_delay = 60
    
    # Calculate days of delay beyond standard
    df_with_penalties['Jours de retard'] = df_with_penalties['Délai de paiement'].apply(
        lambda x: max(0, x - standard_delay)
    )
    
    # Calculate penalty amount based on the law
    # Penalty = (Amount * Interest Rate * Days of Delay) / 365
    df_with_penalties['Montant pénalité'] = (
        df_with_penalties['Montant de la commande'] * 
        PENALTY_INTEREST_RATE * 
        df_with_penalties['Jours de retard']
    ) / 365
    
    return df_with_penalties

def calculate_bfr(stock, creances_clients, dettes_fournisseurs):
    """
    Calculate BFR (Working Capital Requirement)
    BFR = Stock + Accounts Receivable - Accounts Payable
    """
    return stock + creances_clients - dettes_fournisseurs

def calculate_dpo(dettes_fournisseurs, achats_ttc):
    """
    Calculate DPO (Days Payable Outstanding)
    DPO = (Accounts Payable / Purchases) * 365
    """
    return (dettes_fournisseurs / achats_ttc) * 365 if achats_ttc != 0 else 0

def calculate_cash_ratio(tresorerie, dettes_fournisseurs):
    """
    Calculate Cash Ratio
    Cash Ratio = Cash / Accounts Payable
    """
    return tresorerie / dettes_fournisseurs if dettes_fournisseurs != 0 else 0

def calculate_current_ratio(actifs_court_terme, passifs_court_terme):
    """
    Calculate Current Ratio
    Current Ratio = Current Assets / Current Liabilities
    """
    return actifs_court_terme / passifs_court_terme if passifs_court_terme != 0 else 0

def create_gauge_chart(value, min_val, max_val, threshold_bad, threshold_good, title):
    """
    Create a gauge chart for visualization of financial metrics
    """
    # Determine color based on thresholds
    if value <= threshold_bad:
        color = "red"
    elif value >= threshold_good:
        color = "green"
    else:
        color = "orange"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': color},
            'steps': [
                {'range': [min_val, threshold_bad], 'color': "lightgray"},
                {'range': [threshold_bad, threshold_good], 'color': "gray"},
                {'range': [threshold_good, max_val], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    return fig

def get_download_link(df, filename="donnees_fournisseurs.xlsx"):
    """
    Generate a download link for a DataFrame
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Données')
    
    output.seek(0)
    return output
