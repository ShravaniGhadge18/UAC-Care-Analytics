import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
# Must be the very first Streamlit command!
st.set_page_config(page_title="UAC System Analytics", layout="wide")

# --- Sidebar Theme & Context ---
# Adds the official contextual photo to the sidebar
image_url = "https://www.fairus.org/sites/default/files/styles/videos_1023x567/public/images/CBP-UAC-children-minors-flickr.jpg.webp?h=55f405d4&itok=ST2_FHHJ"
st.sidebar.image(image_url, caption="CBP Operations Context", use_column_width=True)
st.sidebar.markdown("---")

# --- Main Page Headers ---
st.title("System Capacity & Care Load Analytics")
st.markdown("Monitoring framework for the Unaccompanied Alien Children (UAC) care pipeline.")

# --- Load Data ---
@st.cache_data
def load_data():
    # Load the raw cleaned data
    data = pd.read_csv("Cleaned_UAC_Data.csv", parse_dates=["Date"])
    
    # Calculate all metrics securely inside Streamlit
    data['Total System Load'] = data['Children in CBP custody'] + data['Children in HHS Care']
    data['Net Daily Intake'] = data['Children transferred out of CBP custody'] - data['Children discharged from HHS Care']
    data['Care Load Growth Rate (%)'] = data['Total System Load'].pct_change() * 100
    data['Backlog Indicator (7-Day Net Intake)'] = data['Net Daily Intake'].rolling(window=7).sum()
    
    # Discharge Offset Ratio with division-by-zero handling
    data['Discharge Offset Ratio'] = data['Children discharged from HHS Care'] / data['Children transferred out of CBP custody']
    data['Discharge Offset Ratio'] = data['Discharge Offset Ratio'].replace([float('inf'), -float('inf')], 0).fillna(0)
    
    return data

df = load_data()

# --- Sidebar Controls ---
st.sidebar.header("Dashboard Controls")
start_date = st.sidebar.date_input("Start Date", df['Date'].min())
end_date = st.sidebar.date_input("End Date", df['Date'].max())

# Filter the dataframe based on user dates
mask = (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask]

# --- Export Data (Sidebar) ---
st.sidebar.markdown("---")
st.sidebar.subheader("Export Data")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="Download Filtered Data (CSV)",
    data=csv,
    file_name='uac_filtered_data.csv',
    mime='text/csv'
)

# Get the most recent day's data for the KPI cards
latest_data = filtered_df.iloc[-1]

# --- KPI Summary Cards ---
st.markdown("### Executive Summary Metrics (Latest Day)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Children Under Care", f"{int(latest_data['Total System Load']):,}", 
              f"{latest_data['Care Load Growth Rate (%)']:.2f}% day-over-day")
with col2:
    st.metric("Children in CBP Custody", f"{int(latest_data['Children in CBP custody']):,}")
with col3:
    st.metric("7-Day Backlog Accumulation", f"{latest_data['Backlog Indicator (7-Day Net Intake)']:.0f}")
with col4:
    st.metric("Discharge Offset Ratio", f"{latest_data['Discharge Offset Ratio']:.2f}", 
              help="Ratio of Discharges to Intake. < 1.0 means system is growing.")

st.markdown("---")

# --- Interactive Charts (Plotly) ---
st.markdown("### System Load Overview")
fig_load = px.line(filtered_df, x="Date", y=["Children in CBP custody", "Children in HHS Care", "Total System Load"], 
                   title="Care Load Across Facilities Over Time",
                   labels={"value": "Number of Children", "variable": "Custody Type"})
st.plotly_chart(fig_load, use_container_width=True)

st.markdown("### Net Intake Pressure")
# Create a bar chart where color depends on value (Red for positive/strain, Blue for negative/relief)
fig_net = px.bar(filtered_df, x="Date", y="Net Daily Intake",
                 color="Net Daily Intake",
                 color_continuous_scale=px.colors.diverging.RdBu_r,
                 title="Daily Net Intake (Transfers into HHS minus Discharges)")
st.plotly_chart(fig_net, use_container_width=True)

# --- View Raw Data Expander ---
st.markdown("---")
with st.expander("View Raw Filtered Data"):
    st.write("This table displays the daily metrics for the exact date range you selected above.")
    st.dataframe(filtered_df, use_container_width=True)
