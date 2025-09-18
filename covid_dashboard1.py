# covid_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="COVID-19 Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🌍 COVID-19 Dashboard")
st.markdown("A professional dashboard tracking COVID-19 statistics globally")

# Database setup with real COVID-19 data structure
def init_db():
    conn = sqlite3.connect('covid_data.db')
    c = conn.cursor()
    
    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS covid_data
                 (date TEXT, country TEXT, country_code TEXT, continent TEXT, 
                 population INTEGER, total_cases INTEGER, new_cases INTEGER, 
                 total_deaths INTEGER, new_deaths INTEGER, 
                 total_tests INTEGER, new_tests INTEGER, 
                 positive_rate REAL, reproduction_rate REAL,
                 icu_patients INTEGER, hosp_patients INTEGER,
                 new_vaccinations INTEGER, total_vaccinations INTEGER,
                 people_vaccinated INTEGER, people_fully_vaccinated INTEGER)''')
    
    # Check if data exists
    c.execute("SELECT COUNT(*) FROM covid_data")
    if c.fetchone()[0] == 0:
        # Generate more realistic sample data
        from datetime import date, timedelta
        import random
        
        countries = [
            ('USA', 'US', 'North America', 331000000),
            ('India', 'IN', 'Asia', 1380000000),
            ('Brazil', 'BR', 'South America', 212000000),
            ('United Kingdom', 'UK', 'Europe', 67000000),
            ('Germany', 'DE', 'Europe', 83000000),
            ('France', 'FR', 'Europe', 67000000),
            ('Japan', 'JP', 'Asia', 126000000),
            ('South Africa', 'ZA', 'Africa', 59300000),
            ('Australia', 'AU', 'Oceania', 25000000),
            ('Mexico', 'MX', 'North America', 128000000)
        ]
        
        # Generate data for the past 12 months
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days)]
        
        data = []
        
        for country, country_code, continent, population in countries:
            # Different starting points for each country
            days_offset = random.randint(0, 30)
            
            # Different severity for each country
            severity = random.uniform(0.5, 2.0)
            
            cases = random.randint(100, 10000)
            deaths = random.randint(0, int(cases * 0.05))
            tests = random.randint(cases * 5, cases * 20)
            vaccinated = random.randint(0, int(population * 0.3))
            
            for i, d in enumerate(dates):
                # Skip early days for some countries
                if i < days_offset:
                    continue
                    
                # Simulate waves of infections
                wave_factor = 1 + 0.5 * np.sin(i / 30) + 0.3 * np.sin(i / 90)
                
                new_cases = max(0, int(random.randint(50, 500) * severity * wave_factor))
                new_deaths = max(0, int(new_cases * random.uniform(0.01, 0.05)))
                new_tests = max(0, int(new_cases * random.randint(5, 15)))
                new_vaccinations = max(0, int(random.randint(1000, 10000) * (1 - i/365)))
                
                cases += new_cases
                deaths += new_deaths
                tests += new_tests
                vaccinated += new_vaccinations
                
                # Add some randomness to reproduction rate
                reproduction_rate = random.uniform(0.8, 1.5) * wave_factor
                
                # Hospitalization metrics
                icu_patients = int(new_cases * random.uniform(0.01, 0.05))
                hosp_patients = int(new_cases * random.uniform(0.05, 0.15))
                
                # Calculate positive rate
                positive_rate = new_cases / new_tests if new_tests > 0 else 0
                
                data.append((
                    d.strftime('%Y-%m-%d'),
                    country,
                    country_code,
                    continent,
                    population,
                    cases,
                    new_cases,
                    deaths,
                    new_deaths,
                    tests,
                    new_tests,
                    positive_rate,
                    reproduction_rate,
                    icu_patients,
                    hosp_patients,
                    new_vaccinations,
                    vaccinated,
                    min(vaccinated, population),
                    min(int(vaccinated * 0.8), population)
                ))
        
        # Insert in batches to avoid memory issues
        batch_size = 1000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            c.executemany('INSERT INTO covid_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', batch)
        
        conn.commit()
        st.sidebar.success("Sample data generated successfully!")
    
    return conn

# Initialize database
conn = init_db()

# Sidebar filters
st.sidebar.header("Filters")

# Date range selector
min_date = pd.read_sql("SELECT MIN(date) FROM covid_data", conn).iloc[0,0]
max_date = pd.read_sql("SELECT MAX(date) FROM covid_data", conn).iloc[0,0]

date_range = st.sidebar.date_input(
    "Select date range",
    value=[datetime.strptime(min_date, '%Y-%m-%d').date(), 
           datetime.strptime(max_date, '%Y-%m-%d').date()],
    min_value=datetime.strptime(min_date, '%Y-%m-%d').date(),
    max_value=datetime.strptime(max_date, '%Y-%m-%d').date()
)

# Continent selector
continents = pd.read_sql("SELECT DISTINCT continent FROM covid_data ORDER BY continent", conn)
selected_continents = st.sidebar.multiselect(
    "Select continents",
    options=continents['continent'].tolist(),
    default=continents['continent'].tolist()
)

# Country multiselect (filtered by selected continents)
if selected_continents:
    countries_query = f"SELECT DISTINCT country FROM covid_data WHERE continent IN ({','.join(['?']*len(selected_continents))}) ORDER BY country"
    countries = pd.read_sql(countries_query, conn, params=selected_continents)
else:
    countries = pd.read_sql("SELECT DISTINCT country FROM covid_data ORDER BY country", conn)

selected_countries = st.sidebar.multiselect(
    "Select countries",
    options=countries['country'].tolist(),
    default=countries['country'].tolist()[:3]
)

# Metrics selector
metrics = {
    'new_cases': 'New Cases',
    'total_cases': 'Total Cases',
    'new_deaths': 'New Deaths',
    'total_deaths': 'Total Deaths',
    'new_tests': 'New Tests',
    'total_tests': 'Total Tests',
    'new_vaccinations': 'New Vaccinations',
    'total_vaccinations': 'Total Vaccinations',
    'reproduction_rate': 'Reproduction Rate',
    'positive_rate': 'Positive Rate'
}
selected_metric = st.sidebar.selectbox(
    "Select metric",
    options=list(metrics.keys()),
    format_func=lambda x: metrics[x]
)

# Data retrieval function
def get_data(metric, countries, start_date, end_date):
    if not countries:
        return pd.DataFrame()
        
    query = f"""
    SELECT date, country, {metric} as value
    FROM covid_data 
    WHERE country IN ({','.join(['?']*len(countries))})
    AND date BETWEEN ? AND ?
    ORDER BY date
    """
    
    params = countries + [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
    df = pd.read_sql(query, conn, params=params)
    return df

# Get summary statistics
def get_summary_stats():
    query = """
    SELECT 
        country,
        MAX(total_cases) as total_cases,
        MAX(total_deaths) as total_deaths,
        MAX(total_vaccinations) as total_vaccinations,
        MAX(people_fully_vaccinated) as people_fully_vaccinated,
        MAX(population) as population
    FROM covid_data 
    GROUP BY country
    """
    return pd.read_sql(query, conn)

# Main dashboard
if selected_countries and len(date_range) == 2:
    start_date, end_date = date_range
    
    # Get data
    df = get_data(selected_metric, selected_countries, start_date, end_date)
    summary_df = get_summary_stats()
    summary_df = summary_df[summary_df['country'].isin(selected_countries)]
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Trends", "Vaccination", "Raw Data"])
    
    with tab1:
        st.subheader("Key Metrics Overview")
        
        # Calculate worldwide totals
        total_cases = summary_df['total_cases'].sum()
        total_deaths = summary_df['total_deaths'].sum()
        total_vaccinations = summary_df['total_vaccinations'].sum()
        total_population = summary_df['population'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Cases", f"{total_cases:,}")
        with col2:
            st.metric("Total Deaths", f"{total_deaths:,}")
        with col3:
            st.metric("Total Vaccinations", f"{total_vaccinations:,}")
        with col4:
            st.metric("Fully Vaccinated", f"{summary_df['people_fully_vaccinated'].sum():,}")
        
        # Cases and deaths by country
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Total Cases by Country")
            fig = px.bar(summary_df, x='country', y='total_cases', 
                         color='country', height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Total Deaths by Country")
            fig = px.bar(summary_df, x='country', y='total_deaths', 
                         color='country', height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader(f"{metrics[selected_metric]} Trends")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Time series chart
            fig = px.line(df, x='date', y='value', color='country',
                          title=f"{metrics[selected_metric]} Over Time")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Latest values by country
            st.subheader(f"Latest Values")
            latest_data = df[df['date'] == end_date.strftime('%Y-%m-%d')]
            if not latest_data.empty:
                fig = px.pie(latest_data, values='value', names='country',
                             title=f"{metrics[selected_metric]} Distribution")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for the selected end date")
    
    with tab3:
        st.subheader("Vaccination Progress")
        
        # Vaccination data
        vax_df = get_data('people_fully_vaccinated', selected_countries, start_date, end_date)
        vax_summary = summary_df.copy()
        vax_summary['vaccination_rate'] = vax_summary['people_fully_vaccinated'] / vax_summary['population'] * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vaccination Rates by Country")
            fig = px.bar(vax_summary, x='country', y='vaccination_rate',
                         title="Percentage of Population Fully Vaccinated")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Vaccination Progress Over Time")
            if not vax_df.empty:
                fig = px.line(vax_df, x='date', y='value', color='country',
                              title="Fully Vaccinated People Over Time")
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Raw Data")
        st.dataframe(df.pivot(index='date', columns='country', values='value').fillna(0))
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='covid_data.csv',
            mime='text/csv',
        )
    
else:
    st.warning("Please select at least one country and a valid date range")

# Close connection
conn.close()

# Footer
st.markdown("---")
st.markdown("*Note*: This dashboard uses simulated data for demonstration purposes.")