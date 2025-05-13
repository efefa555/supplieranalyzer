import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Résumé Audit",
    page_icon="📋",
    layout="wide"
)

# Header
st.title("Résumé d'Audit - Conformité Fournisseurs")
st.write("Synthèse automatique pour les auditeurs selon la loi 69-21")

# Check if data exists in session state
if 'processed_data' not in st.session_state or st.session_state['processed_data'].empty:
    st.warning("Aucune donnée n'est chargée. Veuillez retourner à la page principale pour charger des données.")
    st.stop()

# Get data from session state
data = st.session_state['processed_data']

# Add penalties calculation if not already done
if 'Montant pénalité' not in data.columns:
    # Standard delay based on Law 69-21 (assumed 60 days)
    standard_delay = 60
    interest_rate = 0.03  # 3% interest rate
    
    # Calculate days of delay beyond standard
    data['Jours de retard'] = data['Délai de paiement'].apply(
        lambda x: max(0, x - standard_delay)
    )
    
    # Calculate penalty amount based on the law
    data['Montant pénalité'] = (
        data['Montant de la commande'] * 
        interest_rate * 
        data['Jours de retard']
    ) / 365

# Sidebar filters
with st.sidebar:
    st.header("Filtres d'audit")
    
    # Date range filter
    date_min = data['Date de commande'].min()
    date_max = data['Date de commande'].max()
    
    audit_period = st.date_input(
        "Période d'audit",
        [date_min, date_max],
        min_value=date_min,
        max_value=date_max
    )
    
    # Filter by supplier
    suppliers = ["Tous"] + sorted(data['Nom du fournisseur'].unique().tolist())
    selected_supplier = st.selectbox("Fournisseur", suppliers)
    
    # Apply filters
    filtered_data = data.copy()
    
    if len(audit_period) == 2:
        filtered_data = filtered_data[
            (filtered_data['Date de commande'] >= pd.to_datetime(audit_period[0])) &
            (filtered_data['Date de commande'] <= pd.to_datetime(audit_period[1]))
        ]
    
    if selected_supplier != "Tous":
        filtered_data = filtered_data[filtered_data['Nom du fournisseur'] == selected_supplier]

# Calculate key audit metrics
total_invoices = filtered_data.shape[0]
non_compliant_invoices = filtered_data[filtered_data['Statut du paiement'] == 'En retard'].shape[0]
total_penalties = filtered_data['Montant pénalité'].sum()
compliance_rate = ((total_invoices - non_compliant_invoices) / total_invoices * 100) if total_invoices > 0 else 0

# Find supplier with most late payments
if non_compliant_invoices > 0:
    late_by_supplier = filtered_data[filtered_data['Statut du paiement'] == 'En retard'].groupby('Nom du fournisseur').size().reset_index(name='count')
    worst_supplier = late_by_supplier.loc[late_by_supplier['count'].idxmax(), 'Nom du fournisseur']
else:
    worst_supplier = "N/A"

# Determine audit position
if compliance_rate >= 90:
    audit_position = "Position favorable"
    position_color = "green"
elif compliance_rate >= 70:
    audit_position = "Position neutre"
    position_color = "orange"
else:
    audit_position = "Position d'alerte"
    position_color = "red"

# Display summary metrics
st.header("Indicateurs clés d'audit")

# Create two rows of metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Nombre total de factures", total_invoices)

with col2:
    st.metric("Factures non conformes", non_compliant_invoices)

with col3:
    st.metric("Taux de conformité", f"{compliance_rate:.1f}%")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total des pénalités calculées", f"{total_penalties:.2f} €")

with col2:
    st.metric("Fournisseur avec le plus de retards", worst_supplier)

with col3:
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; background-color: {'rgba(0, 255, 0, 0.2)' if position_color == 'green' else 'rgba(255, 165, 0, 0.2)' if position_color == 'orange' else 'rgba(255, 0, 0, 0.2)'}; text-align: center;">
            <h3 style="margin: 0; color: {'green' if position_color == 'green' else 'orange' if position_color == 'orange' else 'red'};">{audit_position}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

# Visual summary of compliance
st.header("Visualisation de la conformité")

col1, col2 = st.columns(2)

with col1:
    # Pie chart for compliance status
    compliance_data = pd.DataFrame({
        'Status': ['Conforme', 'Non conforme'],
        'Count': [total_invoices - non_compliant_invoices, non_compliant_invoices]
    })
    
    fig_pie = px.pie(
        compliance_data,
        values='Count',
        names='Status',
        title="Répartition des factures par statut de conformité",
        color='Status',
        color_discrete_map={'Conforme': 'green', 'Non conforme': 'red'},
        hole=0.4
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Histogram of delays by supplier
    if non_compliant_invoices > 0:
        late_payments = filtered_data[filtered_data['Statut du paiement'] == 'En retard']
        fig_hist = px.histogram(
            late_payments,
            x='Nom du fournisseur',
            title="Retards par fournisseur",
            color_discrete_sequence=['red']
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Aucun retard de paiement détecté dans la période sélectionnée.")

# Detailed compliance analysis
st.header("Analyse détaillée de la conformité")

# Trends over time
monthly_data = filtered_data.copy()
monthly_data['Mois'] = pd.to_datetime(monthly_data['Date de commande']).dt.to_period('M').astype(str)

# Group by month and calculate compliance rate
monthly_compliance = pd.DataFrame()
for month in monthly_data['Mois'].unique():
    month_data = monthly_data[monthly_data['Mois'] == month]
    if month_data.shape[0] > 0:
        compliant = month_data.shape[0] - month_data[month_data['Statut du paiement'] == 'En retard'].shape[0]
        compliance_rate = (compliant / month_data.shape[0]) * 100
    else:
        compliance_rate = 0
    monthly_compliance = pd.concat([monthly_compliance, pd.DataFrame([{'Mois': month, 'Taux de conformité': compliance_rate}])])

fig_trend = px.line(
    monthly_compliance,
    x='Mois',
    y='Taux de conformité',
    title="Évolution du taux de conformité par mois",
    markers=True,
    labels={'Taux de conformité': 'Taux de conformité (%)', 'Mois': 'Mois'}
)

# Add reference lines for compliance thresholds
fig_trend.add_hline(
    y=90,
    line_dash="dash",
    line_color="green",
    annotation_text="Seuil favorable",
    annotation_position="top right"
)

fig_trend.add_hline(
    y=70,
    line_dash="dash",
    line_color="orange",
    annotation_text="Seuil d'alerte",
    annotation_position="bottom right"
)

st.plotly_chart(fig_trend, use_container_width=True)

# Risk matrix: Supplier analysis
st.subheader("Matrice de risque fournisseurs")

# Calculate risk parameters for each supplier
supplier_risk = filtered_data.groupby('Nom du fournisseur').agg({
    'Montant de la commande': 'sum',  # Financial exposure
    'Délai de paiement': 'mean',  # Average payment delay
    'Statut du paiement': lambda x: (x == 'En retard').mean() * 100  # Late payment rate
}).reset_index()

supplier_risk.columns = ['Nom du fournisseur', 'Exposition financière', 'Délai moyen', 'Taux de retard (%)']

# Create bubble chart for risk visualization
fig_risk = px.scatter(
    supplier_risk,
    x='Délai moyen',
    y='Taux de retard (%)',
    size='Exposition financière',
    color='Taux de retard (%)',
    hover_name='Nom du fournisseur',
    title="Matrice de risque fournisseurs",
    color_continuous_scale=px.colors.sequential.Reds,
    labels={
        'Délai moyen': 'Délai moyen de paiement (jours)',
        'Taux de retard (%)': 'Taux de retard (%)',
        'Exposition financière': 'Exposition financière (€)'
    }
)

# Add reference lines
fig_risk.add_vline(
    x=60,
    line_dash="dash",
    line_color="red",
    annotation_text="Délai légal",
    annotation_position="top right"
)

fig_risk.add_hline(
    y=10,
    line_dash="dash",
    line_color="orange",
    annotation_text="Seuil d'alerte",
    annotation_position="bottom right"
)

st.plotly_chart(fig_risk, use_container_width=True)

# Display detailed non-compliant invoices
st.header("Détail des factures non conformes")

if non_compliant_invoices > 0:
    non_compliant_data = filtered_data[filtered_data['Statut du paiement'] == 'En retard'].sort_values('Délai de paiement', ascending=False)
    
    # Select and order columns for display
    display_cols = [
        'Nom du fournisseur',
        'Date de commande',
        'Date de paiement',
        'Montant de la commande',
        'Délai de paiement',
        'Jours de retard',
        'Montant pénalité'
    ]
    
    # Custom formatting function
    def highlight_delays(val):
        if isinstance(val, (int, float)) and val > 0:
            return f'background-color: rgba(255, 0, 0, {min(val/120, 0.8)})'
        return ''
    
    # Display with styling
    st.dataframe(
        non_compliant_data[display_cols].style.map(highlight_delays, subset=['Jours de retard']).format({
            'Date de commande': lambda x: x.strftime('%d/%m/%Y'),
            'Date de paiement': lambda x: x.strftime('%d/%m/%Y'),
            'Montant de la commande': '{:,.2f} €',
            'Montant pénalité': '{:,.2f} €'
        }),
        use_container_width=True
    )
else:
    st.success("Aucune facture non conforme détectée dans la période d'audit sélectionnée.")

# Audit recommendations
st.header("Recommandations d'audit")

# Generate audit recommendations based on findings
recommendations = []

if compliance_rate < 70:
    recommendations.append("🔴 **Urgence élevée**: Le taux de conformité est critique. Un plan d'action immédiat est nécessaire pour remédier aux retards de paiement.")
    recommendations.append("🔴 **Processus à réviser**: Examiner en profondeur le processus de validation et de paiement des factures pour identifier les goulets d'étranglement.")
elif compliance_rate < 90:
    recommendations.append("🟠 **Attention requise**: Le taux de conformité est moyen. Des améliorations sont nécessaires pour atteindre un niveau satisfaisant.")
    recommendations.append("🟠 **Processus à améliorer**: Optimiser le processus de traitement des factures pour réduire les délais.")
else:
    recommendations.append("🟢 **Performance satisfaisante**: Le taux de conformité est bon. Maintenir les bonnes pratiques en place.")

# Supplier-specific recommendations
if worst_supplier != "N/A":
    supplier_late_count = late_by_supplier.loc[late_by_supplier['Nom du fournisseur'] == worst_supplier, 'count'].iloc[0]
    supplier_late_rate = (supplier_late_count / filtered_data[filtered_data['Nom du fournisseur'] == worst_supplier].shape[0]) * 100
    
    if supplier_late_rate > 50:
        recommendations.append(f"🔴 **Fournisseur à risque élevé**: {worst_supplier} présente un taux de retard de {supplier_late_rate:.1f}%. Une révision des conditions de paiement est recommandée.")
    else:
        recommendations.append(f"🟠 **Fournisseur à surveiller**: {worst_supplier} présente le plus grand nombre de retards. Un suivi spécifique est recommandé.")

# Financial impact recommendations
if total_penalties > 5000:
    recommendations.append(f"🔴 **Impact financier significatif**: Les pénalités de retard s'élèvent à {total_penalties:.2f} €. Prévoir une provision pour risques.")
elif total_penalties > 1000:
    recommendations.append(f"🟠 **Impact financier modéré**: Les pénalités de retard s'élèvent à {total_penalties:.2f} €. Surveiller l'évolution de ce montant.")
else:
    recommendations.append(f"🟢 **Impact financier faible**: Les pénalités de retard s'élèvent à {total_penalties:.2f} €.")

# Process improvement recommendations
recommendations.append("""
🔵 **Améliorations recommandées**:
1. Mettre en place un système d'alerte pour les factures approchant de l'échéance
2. Standardiser le processus de validation des factures
3. Former les équipes sur les exigences de la loi 69-21
4. Établir un reporting mensuel de suivi des délais de paiement
""")

# Display recommendations
for rec in recommendations:
    st.markdown(rec)

# Final audit opinion
st.header("Opinion d'audit")

# Generate audit opinion based on compliance rate
if compliance_rate >= 90:
    st.success("""
    ### ✅ Opinion favorable
    
    Les délais de paiement sont globalement respectés, avec un taux de conformité satisfaisant. 
    L'entreprise démontre une bonne gestion de ses obligations envers ses fournisseurs conformément aux dispositions de la loi 69-21.
    
    Quelques points d'amélioration mineurs ont été identifiés pour maintenir cette performance.
    """)
elif compliance_rate >= 70:
    st.warning("""
    ### ⚠️ Opinion avec réserves
    
    Des cas significatifs de non-conformité ont été identifiés, bien que l'entreprise démontre une volonté de respecter les délais légaux.
    
    Des améliorations sont nécessaires pour se conformer pleinement aux dispositions de la loi 69-21.
    Un plan d'action devrait être mis en place pour améliorer le taux de conformité.
    """)
else:
    st.error("""
    ### ❌ Opinion défavorable
    
    Un nombre important de paiements ne respecte pas les délais légaux, exposant l'entreprise à des risques financiers et juridiques significatifs.
    
    Une refonte du processus de paiement est fortement recommandée pour se conformer aux dispositions de la loi 69-21.
    Un plan d'action urgent doit être mis en place pour remédier à cette situation.
    """)

# Export options
st.header("Exporter le rapport d'audit")

# Create a downloadable Excel report
def create_audit_report():
    # Create a BytesIO object
    output = pd.ExcelWriter('audit_report.xlsx', engine='xlsxwriter')
    
    # Write summary sheet
    summary_data = pd.DataFrame([
        {"Indicateur": "Nombre total de factures", "Valeur": total_invoices},
        {"Indicateur": "Factures non conformes", "Valeur": non_compliant_invoices},
        {"Indicateur": "Taux de conformité", "Valeur": f"{compliance_rate:.1f}%"},
        {"Indicateur": "Total des pénalités", "Valeur": f"{total_penalties:.2f} €"},
        {"Indicateur": "Fournisseur avec le plus de retards", "Valeur": worst_supplier},
        {"Indicateur": "Position d'audit", "Valeur": audit_position}
    ])
    
    summary_data.to_excel(output, sheet_name='Résumé', index=False)
    
    # Write non-compliant invoices
    if non_compliant_invoices > 0:
        non_compliant_data[display_cols].to_excel(output, sheet_name='Factures non conformes', index=False)
    
    # Write monthly compliance
    monthly_compliance.to_excel(output, sheet_name='Évolution mensuelle', index=False)
    
    # Write supplier risk
    supplier_risk.to_excel(output, sheet_name='Risque fournisseurs', index=False)
    
    # Save the workbook
    output.close()
    
    with open('audit_report.xlsx', 'rb') as f:
        return f.read()

# Create download button
report = create_audit_report()
st.download_button(
    label="Télécharger le rapport d'audit (Excel)",
    data=report,
    file_name=f"rapport_audit_fournisseurs_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Audit completion certificate
st.header("Certificat d'audit")

# Create a certificate-like display
certificate_date = datetime.now().strftime("%d/%m/%Y")

st.markdown(f"""
<div style="padding: 20px; border: 2px solid #1E88E5; border-radius: 10px; text-align: center; margin-top: 20px;">
    <h2 style="color: #1E88E5;">Certificat d'audit des délais de paiement</h2>
    <p>Cet audit a été réalisé conformément aux dispositions de la loi 69-21 relative aux délais de paiement.</p>
    <p>Période d'audit : du {audit_period[0].strftime('%d/%m/%Y')} au {audit_period[1].strftime('%d/%m/%Y')}</p>
    <p>Taux de conformité global : <b>{compliance_rate:.1f}%</b></p>
    <p>Position d'audit : <b style="color: {'green' if position_color == 'green' else 'orange' if position_color == 'orange' else 'red'};">{audit_position}</b></p>
    <p>Date de certification : {certificate_date}</p>
</div>
""", unsafe_allow_html=True)

# Final notes
st.info("""
**Note importante**: Ce rapport d'audit est généré automatiquement à partir des données fournies. 
Il doit être complété par une analyse humaine pour tenir compte des spécificités de l'entreprise et du contexte économique.
Les recommandations sont données à titre indicatif et doivent être adaptées à la situation particulière de l'entreprise.
""")
