import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import process_data

# Page configuration
st.set_page_config(
    page_title="Analyse des Retards",
    page_icon="📊",
    layout="wide"
)

# Header
st.title("Analyse des Retards de Paiement")
st.write("Analysez les retards de paiement par fournisseur et par période")

# Check if data exists in session state
if 'processed_data' not in st.session_state or st.session_state['processed_data'].empty:
    st.warning("Aucune donnée n'est chargée. Veuillez retourner à la page principale pour charger des données.")
    st.stop()

# Get data from session state
data = st.session_state['processed_data']

# Sidebar filters
with st.sidebar:
    st.header("Filtres")
    
    # Filter by supplier
    suppliers = ["Tous"] + sorted(data['Nom du fournisseur'].unique().tolist())
    selected_supplier = st.selectbox("Fournisseur", suppliers, key="supplier_filter_delay")
    
    # Filter by delay
    min_delay = int(data['Délai de paiement'].min()) if 'Délai de paiement' in data.columns else 0
    max_delay = int(data['Délai de paiement'].max()) if 'Délai de paiement' in data.columns else 100
    
    delay_range = st.slider(
        "Délai de paiement (jours)",
        min_delay,
        max_delay,
        (min_delay, max_delay)
    )
    
    # Filter by payment status
    statuses = ["Tous", "Dans les délais", "En retard"]
    selected_status = st.selectbox("Statut de paiement", statuses, key="status_filter_delay")
    
    # Apply filters
    filtered_data = data.copy()
    
    if selected_supplier != "Tous":
        filtered_data = filtered_data[filtered_data['Nom du fournisseur'] == selected_supplier]
    
    filtered_data = filtered_data[
        (filtered_data['Délai de paiement'] >= delay_range[0]) &
        (filtered_data['Délai de paiement'] <= delay_range[1])
    ]
    
    if selected_status != "Tous":
        filtered_data = filtered_data[filtered_data['Statut du paiement'] == selected_status]

# Main content
st.header("Tableau des retards de paiement")

# Summary metrics
col1, col2, col3 = st.columns(3)

with col1:
    avg_delay = filtered_data['Délai de paiement'].mean()
    st.metric("Délai moyen de paiement", f"{avg_delay:.1f} jours")
    
with col2:
    late_payments = filtered_data[filtered_data['Statut du paiement'] == 'En retard'].shape[0]
    late_payments_pct = late_payments / filtered_data.shape[0] * 100 if filtered_data.shape[0] > 0 else 0
    st.metric("Paiements en retard", f"{late_payments} ({late_payments_pct:.1f}%)")
    
with col3:
    max_delay = filtered_data['Délai de paiement'].max()
    st.metric("Délai maximum", f"{max_delay:.0f} jours")

# Create visualizations
st.subheader("Visualisation des retards")

# Create 2 columns for charts
col1, col2 = st.columns(2)

with col1:
    # Delay distribution
    fig_delay_dist = px.histogram(
        filtered_data,
        x='Délai de paiement',
        color='Statut du paiement',
        nbins=20,
        title="Distribution des délais de paiement",
        labels={'Délai de paiement': 'Délai (jours)', 'count': 'Nombre de paiements'}
    )
    st.plotly_chart(fig_delay_dist, use_container_width=True)
    
with col2:
    # Average delay by supplier
    avg_delay_by_supplier = filtered_data.groupby('Nom du fournisseur')['Délai de paiement'].mean().reset_index()
    avg_delay_by_supplier = avg_delay_by_supplier.sort_values('Délai de paiement', ascending=False)
    
    fig_avg_delay = px.bar(
        avg_delay_by_supplier,
        x='Nom du fournisseur',
        y='Délai de paiement',
        title="Délai moyen par fournisseur",
        color='Délai de paiement',
        color_continuous_scale=px.colors.sequential.Reds,
        labels={'Délai de paiement': 'Délai moyen (jours)', 'Nom du fournisseur': 'Fournisseur'}
    )
    st.plotly_chart(fig_avg_delay, use_container_width=True)

# Delays over time
st.subheader("Évolution des retards dans le temps")

# Convert dates to month for time series analysis
filtered_data['Mois commande'] = pd.to_datetime(filtered_data['Date de commande']).dt.to_period('M').astype(str)

# Group by month and calculate average delay
delay_by_month = filtered_data.groupby('Mois commande')['Délai de paiement'].mean().reset_index()

fig_time_series = px.line(
    delay_by_month,
    x='Mois commande',
    y='Délai de paiement',
    title="Évolution du délai moyen de paiement par mois",
    markers=True,
    labels={'Délai de paiement': 'Délai moyen (jours)', 'Mois commande': 'Mois'}
)

# Add a horizontal line for the standard delay (e.g., 60 days)
fig_time_series.add_hline(
    y=60,
    line_dash="dash",
    line_color="red",
    annotation_text="Délai standard (60 jours)",
    annotation_position="top right"
)

st.plotly_chart(fig_time_series, use_container_width=True)

# Display detailed data
st.subheader("Données détaillées des retards")

# Sort by delay in descending order to highlight the longest delays
sorted_data = filtered_data.sort_values('Délai de paiement', ascending=False)

# Add color-coding for status
def highlight_status(val):
    if val == 'En retard':
        return 'background-color: rgba(255, 0, 0, 0.2)'
    elif val == 'Dans les délais':
        return 'background-color: rgba(0, 255, 0, 0.2)'
    return ''

# Display with styling
st.dataframe(
    sorted_data.style.applymap(highlight_status, subset=['Statut du paiement']),
    use_container_width=True
)

# Add summary analysis and recommendations
st.header("Analyse et Recommandations")

# Calculate metrics for analysis
late_payment_avg_delay = filtered_data[filtered_data['Statut du paiement'] == 'En retard']['Délai de paiement'].mean()
worst_supplier = avg_delay_by_supplier.iloc[0]['Nom du fournisseur'] if not avg_delay_by_supplier.empty else "N/A"
worst_supplier_delay = avg_delay_by_supplier.iloc[0]['Délai de paiement'] if not avg_delay_by_supplier.empty else 0

# Create a markdown with analysis
analysis_text = f"""
### Points clés à retenir:

1. **Délai moyen des paiements en retard**: {late_payment_avg_delay:.1f} jours
2. **Fournisseur avec le délai le plus long**: {worst_supplier} ({worst_supplier_delay:.1f} jours)
3. **Pourcentage de paiements en retard**: {late_payments_pct:.1f}%

### Recommandations:

"""

# Dynamic recommendations based on the data
if late_payments_pct > 30:
    analysis_text += "- **Urgence élevée**: Le taux de paiements en retard est très élevé, ce qui pourrait nuire aux relations fournisseurs et entraîner des pénalités importantes.\n"
elif late_payments_pct > 15:
    analysis_text += "- **Attention requise**: Le taux de paiements en retard mérite une attention particulière.\n"
else:
    analysis_text += "- **Bonne performance**: Le taux de paiements en retard est relativement bas.\n"

if worst_supplier_delay > 90:
    analysis_text += f"- **Action prioritaire**: Examiner les paiements à {worst_supplier} qui présente des délais excessivement longs.\n"

analysis_text += """
- Mettre en place un système d'alerte précoce pour les factures approchant de leur échéance.
- Examiner les processus internes de validation et d'approbation des factures pour identifier les goulets d'étranglement.
- Envisager des accords de paiement spécifiques avec les fournisseurs qui ont régulièrement des retards.
"""

st.markdown(analysis_text)
