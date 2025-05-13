import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Suivi Trésorerie",
    page_icon="💵",
    layout="wide"
)

# Header
st.title("Suivi de Trésorerie")
st.write("Prévisions et suivi des décaissements liés aux fournisseurs")

# Check if data exists in session state
if 'processed_data' not in st.session_state or st.session_state['processed_data'].empty:
    st.warning("Aucune donnée n'est chargée. Veuillez retourner à la page principale pour charger des données.")
    st.stop()

# Get data from session state
data = st.session_state['processed_data']

# Initialize treasury_data in session state if it doesn't exist
if 'treasury_data' not in st.session_state:
    # Get unique suppliers from the data
    suppliers = data['Nom du fournisseur'].unique().tolist()
    
    # Create initial treasury data with some example records
    today = datetime.now()
    initial_balance = 100000  # Example initial balance
    
    treasury_data = []
    
    # Add initial balance
    treasury_data.append({
        'Date': today.strftime('%Y-%m-%d'),
        'Type': 'Solde initial',
        'Fournisseur': '',
        'Montant prévu': initial_balance,
        'Montant payé': initial_balance,
        'Écart': 0,
        'Solde': initial_balance
    })
    
    # Generate some example future payments based on supplier data
    current_balance = initial_balance
    for i in range(1, 11):  # Generate 10 example payments
        payment_date = today + timedelta(days=i*7)  # Weekly payments
        supplier = np.random.choice(suppliers)
        amount = np.random.randint(5000, 20000)
        
        # Sometimes create a difference between expected and actual
        paid_amount = amount * np.random.uniform(0.9, 1.1) if i % 3 == 0 else amount
        difference = amount - paid_amount
        
        current_balance -= paid_amount
        
        treasury_data.append({
            'Date': payment_date.strftime('%Y-%m-%d'),
            'Type': 'Décaissement',
            'Fournisseur': supplier,
            'Montant prévu': amount,
            'Montant payé': paid_amount,
            'Écart': difference,
            'Solde': current_balance
        })
    
    st.session_state['treasury_data'] = pd.DataFrame(treasury_data)
    st.session_state['initial_balance'] = initial_balance

# Get treasury data from session state
treasury_data = st.session_state['treasury_data']

# Input section for new treasury entry
st.header("Ajouter un mouvement de trésorerie")

with st.form("new_treasury_entry"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        entry_date = st.date_input(
            "Date prévue",
            value=datetime.now() + timedelta(days=7)  # Default to 1 week in the future
        )
        
        entry_type = st.selectbox(
            "Type de mouvement",
            ["Décaissement", "Encaissement", "Autre"]
        )
    
    with col2:
        suppliers = [""] + sorted(data['Nom du fournisseur'].unique().tolist())
        entry_supplier = st.selectbox("Fournisseur", suppliers)
        
        entry_amount_expected = st.number_input(
            "Montant prévu",
            min_value=0.0,
            value=10000.0,
            step=1000.0,
            format="%.2f"
        )
    
    with col3:
        entry_amount_paid = st.number_input(
            "Montant réel payé",
            min_value=0.0,
            value=10000.0,
            step=1000.0,
            format="%.2f",
            help="Laissez à 0 si le paiement n'a pas encore été effectué"
        )
        
        entry_notes = st.text_input("Notes (optionnel)")
    
    submit_button = st.form_submit_button(label="Ajouter le mouvement")
    
    if submit_button:
        # Calculate difference
        difference = entry_amount_expected - entry_amount_paid
        
        # Calculate new balance
        if entry_type == "Décaissement":
            new_balance = treasury_data['Solde'].iloc[-1] - entry_amount_paid
        elif entry_type == "Encaissement":
            new_balance = treasury_data['Solde'].iloc[-1] + entry_amount_paid
        else:
            new_balance = treasury_data['Solde'].iloc[-1]  # No change for "Autre"
        
        # Create new entry
        new_entry = pd.DataFrame([{
            'Date': entry_date.strftime('%Y-%m-%d'),
            'Type': entry_type,
            'Fournisseur': entry_supplier,
            'Montant prévu': entry_amount_expected,
            'Montant payé': entry_amount_paid,
            'Écart': difference,
            'Solde': new_balance,
            'Notes': entry_notes
        }])
        
        # Append to treasury data
        st.session_state['treasury_data'] = pd.concat([treasury_data, new_entry], ignore_index=True)
        
        # Sort by date
        st.session_state['treasury_data'] = st.session_state['treasury_data'].sort_values('Date')
        
        st.success("Mouvement ajouté avec succès!")
        st.rerun()  # Refresh the page to show the new entry

# Get updated treasury data
treasury_data = st.session_state['treasury_data']

# Convert Date column to datetime
treasury_data['Date'] = pd.to_datetime(treasury_data['Date'])

# Sidebar filters
with st.sidebar:
    st.header("Filtres")
    
    # Date range filter
    date_min = treasury_data['Date'].min()
    date_max = treasury_data['Date'].max() + timedelta(days=30)  # Add a month to include future projections
    
    date_range = st.date_input(
        "Période",
        [date_min, date_max],
        min_value=date_min,
        max_value=date_max
    )
    
    # Transaction type filter
    types = ["Tous"] + treasury_data['Type'].unique().tolist()
    selected_type = st.selectbox("Type de mouvement", types)
    
    # Apply filters
    filtered_treasury = treasury_data.copy()
    
    if len(date_range) == 2:
        filtered_treasury = filtered_treasury[
            (filtered_treasury['Date'] >= pd.to_datetime(date_range[0])) &
            (filtered_treasury['Date'] <= pd.to_datetime(date_range[1]))
        ]
    
    if selected_type != "Tous":
        filtered_treasury = filtered_treasury[filtered_treasury['Type'] == selected_type]

# Treasury overview
st.header("Aperçu de la trésorerie")

# Key metrics
col1, col2, col3 = st.columns(3)

with col1:
    current_balance = treasury_data['Solde'].iloc[-1]
    st.metric("Solde actuel", f"{current_balance:,.2f} €")

with col2:
    # Upcoming payments
    future_payments = treasury_data[
        (treasury_data['Date'] > datetime.now()) & 
        (treasury_data['Type'] == 'Décaissement')
    ]['Montant prévu'].sum()
    
    st.metric("Paiements à venir (30j)", f"{future_payments:,.2f} €")

with col3:
    # Projected balance (30 days)
    projected_balance = current_balance
    
    # Subtract upcoming payments
    upcoming_payments = treasury_data[
        (treasury_data['Date'] > datetime.now()) & 
        (treasury_data['Date'] <= datetime.now() + timedelta(days=30))
    ]
    
    for _, row in upcoming_payments.iterrows():
        if row['Type'] == 'Décaissement':
            projected_balance -= row['Montant prévu']
        elif row['Type'] == 'Encaissement':
            projected_balance += row['Montant prévu']
    
    balance_change = projected_balance - current_balance
    delta_color = "normal" if balance_change >= 0 else "inverse"
    
    st.metric(
        "Solde projeté (30j)", 
        f"{projected_balance:,.2f} €", 
        delta=f"{balance_change:,.2f} €",
        delta_color=delta_color
    )

# Cash flow chart
st.subheader("Évolution du solde de trésorerie")

# Prepare data for chart (include all data for proper timeline)
cash_flow_data = treasury_data.copy()
cash_flow_data = cash_flow_data.sort_values('Date')

# Add today's marker
today = datetime.now().strftime('%Y-%m-%d')

# Create the chart
fig = px.line(
    cash_flow_data,
    x='Date',
    y='Solde',
    title="Évolution du solde de trésorerie",
    labels={'Solde': 'Solde (€)', 'Date': 'Date'},
    markers=True
)

# Add a vertical line for today
fig.add_vline(
    x=datetime.now(),
    line_dash="dash",
    line_color="red",
    annotation_text="Aujourd'hui",
    annotation_position="top right"
)

# Add a horizontal line at 0 to highlight negative balance
fig.add_hline(
    y=0,
    line_dash="dash",
    line_color="red",
    annotation_text="Solde nul",
    annotation_position="bottom right"
)

st.plotly_chart(fig, use_container_width=True)

# Monthly cash flow analysis
st.subheader("Analyse des flux mensuels")

# Add month column for aggregation
treasury_data['Mois'] = treasury_data['Date'].dt.to_period('M').astype(str)

# Group by month and transaction type
monthly_cash_flow = treasury_data.groupby(['Mois', 'Type'])['Montant payé'].sum().reset_index()

# Pivot the data
monthly_pivot = monthly_cash_flow.pivot(index='Mois', columns='Type', values='Montant payé').reset_index()
monthly_pivot = monthly_pivot.fillna(0)

# Calculate net cash flow if we have both inflows and outflows
if 'Encaissement' in monthly_pivot.columns and 'Décaissement' in monthly_pivot.columns:
    monthly_pivot['Flux net'] = monthly_pivot['Encaissement'] - monthly_pivot['Décaissement']

# Create a bar chart for monthly cash flow
if 'Flux net' in monthly_pivot.columns:
    # If we have net flow data
    fig_monthly = px.bar(
        monthly_pivot,
        x='Mois',
        y=['Encaissement', 'Décaissement', 'Flux net'],
        title="Flux de trésorerie mensuels",
        barmode='group',
        labels={'value': 'Montant (€)', 'Mois': 'Mois', 'variable': 'Type'}
    )
else:
    # If we only have one type of flow
    flow_cols = [col for col in monthly_pivot.columns if col != 'Mois']
    fig_monthly = px.bar(
        monthly_pivot,
        x='Mois',
        y=flow_cols,
        title="Flux de trésorerie mensuels",
        barmode='group',
        labels={'value': 'Montant (€)', 'Mois': 'Mois', 'variable': 'Type'}
    )

st.plotly_chart(fig_monthly, use_container_width=True)

# Supplier payment analysis
if 'Fournisseur' in treasury_data.columns and treasury_data['Fournisseur'].notna().any():
    st.subheader("Analyse des paiements par fournisseur")
    
    # Filter for payments only
    payments_data = treasury_data[
        (treasury_data['Type'] == 'Décaissement') & 
        (treasury_data['Fournisseur'] != '')
    ]
    
    if not payments_data.empty:
        # Group by supplier
        supplier_payments = payments_data.groupby('Fournisseur')['Montant payé'].sum().reset_index()
        supplier_payments = supplier_payments.sort_values('Montant payé', ascending=False)
        
        # Create pie chart
        fig_suppliers = px.pie(
            supplier_payments,
            values='Montant payé',
            names='Fournisseur',
            title="Répartition des paiements par fournisseur",
            hole=0.4
        )
        fig_suppliers.update_traces(textposition='inside', textinfo='percent+label')
        
        st.plotly_chart(fig_suppliers, use_container_width=True)
    else:
        st.info("Aucune donnée de paiement fournisseur disponible.")

# Detailed treasury table
st.header("Détail des mouvements de trésorerie")

# Format the Date column for display
filtered_treasury['Date formatée'] = filtered_treasury['Date'].dt.strftime('%d/%m/%Y')

# Select and order columns for display
display_cols = [
    'Date formatée',
    'Type',
    'Fournisseur',
    'Montant prévu',
    'Montant payé',
    'Écart',
    'Solde'
]

if 'Notes' in filtered_treasury.columns:
    display_cols.append('Notes')

# Custom formatter for the dataframe
def highlight_deficit(val):
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red'
    return ''

# Sort by date
sorted_treasury = filtered_treasury.sort_values('Date')

# Display with styling
st.dataframe(
    sorted_treasury[display_cols].style.applymap(highlight_deficit, subset=['Écart', 'Solde']).format({
        'Montant prévu': '{:,.2f} €',
        'Montant payé': '{:,.2f} €',
        'Écart': '{:,.2f} €',
        'Solde': '{:,.2f} €'
    }),
    use_container_width=True
)

# Treasury planning and recommendations
st.header("Planification et recommandations")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Points d'attention")
    
    # Check for potential issues
    future_treasury = treasury_data[treasury_data['Date'] > datetime.now()]
    daily_balances = future_treasury.sort_values('Date')
    
    # Check for negative balance periods
    negative_periods = []
    current_period = None
    
    for idx, row in daily_balances.iterrows():
        if row['Solde'] < 0 and current_period is None:
            current_period = {
                'start_date': row['Date'],
                'min_balance': row['Solde']
            }
        elif row['Solde'] < 0 and current_period is not None:
            current_period['min_balance'] = min(current_period['min_balance'], row['Solde'])
            current_period['end_date'] = row['Date']
        elif row['Solde'] >= 0 and current_period is not None:
            current_period['end_date'] = row['Date'] - timedelta(days=1)
            negative_periods.append(current_period)
            current_period = None
    
    # Add the last period if it's still open
    if current_period is not None:
        current_period['end_date'] = daily_balances.iloc[-1]['Date']
        negative_periods.append(current_period)
    
    if negative_periods:
        for period in negative_periods:
            start_str = period['start_date'].strftime('%d/%m/%Y')
            end_str = period['end_date'].strftime('%d/%m/%Y')
            st.warning(f"⚠️ **Solde négatif** du {start_str} au {end_str} (minimum: {period['min_balance']:,.2f} €)")
    else:
        st.success("✅ Aucune période de solde négatif prévue dans l'horizon actuel.")
    
    # Check for large payments
    large_payments = future_treasury[
        future_treasury['Type'] == 'Décaissement'
    ].sort_values('Montant prévu', ascending=False).head(3)
    
    if not large_payments.empty:
        st.info("📌 **Paiements importants à venir:**")
        for idx, row in large_payments.iterrows():
            date_str = row['Date'].strftime('%d/%m/%Y')
            st.write(f"- {date_str}: {row['Montant prévu']:,.2f} € ({row['Fournisseur'] if row['Fournisseur'] else 'Non spécifié'})")

with col2:
    st.subheader("Recommandations")
    
    # Generate context-specific recommendations
    recommendations = []
    
    # Check for cash flow issues
    if any(period['min_balance'] < -10000 for period in negative_periods):
        recommendations.append("🔴 **Urgent**: Prévoir un financement à court terme pour couvrir les périodes de solde fortement négatif.")
    elif negative_periods:
        recommendations.append("🟠 **Important**: Échelonner certains paiements pour éviter les périodes de solde négatif.")
    
    # Check for payment concentration
    monthly_payments = treasury_data[treasury_data['Type'] == 'Décaissement'].groupby(treasury_data['Date'].dt.to_period('M'))['Montant prévu'].sum()
    if monthly_payments.max() > 1.5 * monthly_payments.mean():
        high_month = monthly_payments.idxmax()
        recommendations.append(f"🟠 **Important**: Les paiements sont trop concentrés en {high_month}. Envisager de mieux répartir les échéances.")
    
    # Check supplier concentration
    if 'Fournisseur' in treasury_data.columns:
        supplier_concentration = treasury_data[treasury_data['Type'] == 'Décaissement'].groupby('Fournisseur')['Montant prévu'].sum()
        if supplier_concentration.max() > 0.4 * supplier_concentration.sum():
            top_supplier = supplier_concentration.idxmax()
            recommendations.append(f"🟡 **À surveiller**: Forte concentration des paiements vers {top_supplier}. Diversifier les fournisseurs pourrait réduire les risques.")
    
    # General recommendations
    recommendations.extend([
        "🟢 Maintenir une réserve de trésorerie d'au moins 30 jours de dépenses moyennes.",
        "🟢 Mettre à jour régulièrement les prévisions de trésorerie à mesure que de nouvelles informations sont disponibles.",
        "🟢 Négocier des délais de paiement plus longs avec les fournisseurs lorsque c'est possible, tout en respectant la loi 69-21."
    ])
    
    # Display recommendations
    for rec in recommendations:
        st.markdown(rec)

# Scenario planning tool
st.header("Planification de scénarios")

with st.expander("Outils de planification"):
    st.write("Utilisez cet outil pour tester différents scénarios de trésorerie.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Adjust initial balance
        new_initial_balance = st.number_input(
            "Solde initial",
            min_value=0.0,
            value=float(st.session_state['initial_balance']),
            step=10000.0,
            format="%.2f"
        )
        
        # Delay payment option
        delay_days = st.slider(
            "Retarder tous les paiements futurs de (jours)",
            min_value=0,
            max_value=30,
            value=0
        )
    
    with col2:
        # Reduce payments option
        payment_reduction = st.slider(
            "Réduire tous les paiements futurs de (%)",
            min_value=0,
            max_value=50,
            value=0
        )
        
        # Add emergency funding
        emergency_funding = st.number_input(
            "Ajouter un financement d'urgence",
            min_value=0.0,
            value=0.0,
            step=10000.0,
            format="%.2f"
        )
    
    if st.button("Simuler ce scénario"):
        # Create a copy of the original data
        scenario_data = treasury_data.copy()
        
        # Adjust initial balance
        balance_diff = new_initial_balance - st.session_state['initial_balance']
        scenario_data.loc[0, 'Montant prévu'] = new_initial_balance
        scenario_data.loc[0, 'Montant payé'] = new_initial_balance
        scenario_data.loc[0, 'Solde'] = new_initial_balance
        
        # Update all subsequent balances by the same amount
        for i in range(1, len(scenario_data)):
            scenario_data.loc[i, 'Solde'] += balance_diff
        
        # Delay future payments
        if delay_days > 0:
            today = datetime.now()
            future_indices = scenario_data[scenario_data['Date'] > today].index
            scenario_data.loc[future_indices, 'Date'] = scenario_data.loc[future_indices, 'Date'] + timedelta(days=delay_days)
        
        # Reduce future payments
        if payment_reduction > 0:
            today = datetime.now()
            future_payment_indices = scenario_data[
                (scenario_data['Date'] > today) & 
                (scenario_data['Type'] == 'Décaissement')
            ].index
            
            reduction_factor = 1 - (payment_reduction / 100)
            scenario_data.loc[future_payment_indices, 'Montant prévu'] *= reduction_factor
            scenario_data.loc[future_payment_indices, 'Montant payé'] *= reduction_factor
            
            # Recalculate balances
            current_balance = scenario_data.loc[0, 'Solde']
            for i in range(1, len(scenario_data)):
                if scenario_data.loc[i, 'Type'] == 'Décaissement':
                    current_balance -= scenario_data.loc[i, 'Montant payé']
                elif scenario_data.loc[i, 'Type'] == 'Encaissement':
                    current_balance += scenario_data.loc[i, 'Montant payé']
                scenario_data.loc[i, 'Solde'] = current_balance
        
        # Add emergency funding
        if emergency_funding > 0:
            # Find the earliest future date
            today = datetime.now()
            future_dates = scenario_data[scenario_data['Date'] > today]['Date']
            
            if not future_dates.empty:
                funding_date = future_dates.min()
                
                # Create a new entry for the emergency funding
                funding_entry = pd.DataFrame([{
                    'Date': funding_date,
                    'Type': 'Encaissement',
                    'Fournisseur': 'Financement d\'urgence',
                    'Montant prévu': emergency_funding,
                    'Montant payé': emergency_funding,
                    'Écart': 0,
                    'Solde': 0,  # Will be calculated below
                    'Notes': 'Financement d\'urgence (simulation)'
                }])
                
                # Add to scenario data
                scenario_data = pd.concat([scenario_data, funding_entry], ignore_index=True)
                
                # Sort by date
                scenario_data = scenario_data.sort_values('Date')
                
                # Recalculate balances
                current_balance = scenario_data.iloc[0]['Solde']
                for i in range(1, len(scenario_data)):
                    if scenario_data.iloc[i]['Type'] == 'Décaissement':
                        current_balance -= scenario_data.iloc[i]['Montant payé']
                    elif scenario_data.iloc[i]['Type'] == 'Encaissement':
                        current_balance += scenario_data.iloc[i]['Montant payé']
                    scenario_data.iloc[i, scenario_data.columns.get_loc('Solde')] = current_balance
        
        # Create the chart for the scenario
        fig_scenario = px.line(
            scenario_data,
            x='Date',
            y='Solde',
            title="Simulation: Évolution du solde de trésorerie",
            labels={'Solde': 'Solde (€)', 'Date': 'Date'},
            markers=True
        )
        
        # Add a vertical line for today
        fig_scenario.add_vline(
            x=today,
            line_dash="dash",
            line_color="red",
            annotation_text="Aujourd'hui",
            annotation_position="top right"
        )
        
        # Add a horizontal line at 0 to highlight negative balance
        fig_scenario.add_hline(
            y=0,
            line_dash="dash",
            line_color="red",
            annotation_text="Solde nul",
            annotation_position="bottom right"
        )
        
        st.plotly_chart(fig_scenario, use_container_width=True)
        
        # Show lowest projected balance
        future_scenario_data = scenario_data[scenario_data['Date'] > today]
        min_balance = future_scenario_data['Solde'].min()
        min_date = future_scenario_data.loc[future_scenario_data['Solde'].idxmin(), 'Date']
        
        st.metric(
            "Solde minimum projeté", 
            f"{min_balance:,.2f} €",
            help=f"Le solde minimum est atteint le {min_date.strftime('%d/%m/%Y')}"
        )
        
        if min_balance < 0:
            st.warning("⚠️ Ce scénario génère un solde négatif. Des mesures supplémentaires peuvent être nécessaires.")
        else:
            st.success("✅ Ce scénario maintient un solde positif tout au long de la période.")
