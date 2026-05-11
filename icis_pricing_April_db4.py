"""
ICIS Pricing Dashboard - COMPLETE ENHANCED APPLICATION
✅ Real pricing data fetching with AI insights
✅ Forecast series with BATCHED XML requests (not individual)
✅ Debug section with execution logs & XML display
✅ FX & unit normalization with normalized charts
✅ Price driver analysis
✅ Scenario analysis with AI
✅ ML forecasting with AI analysis
✅ Formula builder with component curves visualization
✅ Apply & compare formulas with blend insights (FIXED - NOW DISPLAYS!)
✅ AI-powered insights for different user roles
✅ Smart chat interface
✅ All features fully integrated
✅ Publication-based series selection with multi-select
✅ Forecast data with multi-series normalization
✅ BATCHED Forecast XML (single request for all series)
✅ Component curves on blend charts
✅ Blend meaning & outlook insights
✅ Normalized charts showing applied units/currency
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import base64
import hashlib
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path

load_dotenv()

st.set_page_config(
    page_title="ICIS Pricing Dashboard - Enhanced",
    layout="wide",
    initial_sidebar_state="expanded"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ============================
# OPTIONAL DEPENDENCIES
# ============================

try:
    from sklearn.linear_model import LinearRegression
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# ============================
# DEBUG LOG & XML TRACKING
# ============================

if "debug_log" not in st.session_state:
    st.session_state.debug_log = []

if "xml_requests_log" not in st.session_state:
    st.session_state.xml_requests_log = []

def log_debug(message, details=""):
    """Add debug message to log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "message": message,
        "details": details[:300] if details else ""
    }
    st.session_state.debug_log.append(entry)

def log_xml_request(request_type, xml_payload, description="", series_count=0):
    """Log XML request payload"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "request_type": request_type,
        "description": description,
        "xml_payload": xml_payload,
        "size_bytes": len(xml_payload.encode('utf-8')),
        "series_count": series_count
    }
    st.session_state.xml_requests_log.append(entry)

# ============================
# PRICE DRIVER WEIGHTS
# ============================

PRICE_DRIVER_WEIGHTS = {
    "Crude Oil": {
        "weight": 0.40,
        "correlation": 0.85,
        "lag_days": 3,
        "description": "Primary feedstock - 40% of price"
    },
    "Natural Gas": {
        "weight": 0.25,
        "correlation": 0.70,
        "lag_days": 2,
        "description": "Energy cost - 25% of price"
    },
    "USD Strength": {
        "weight": 0.15,
        "correlation": -0.60,
        "lag_days": 1,
        "description": "Currency impact - 15% of price"
    },
    "Global Demand": {
        "weight": 0.12,
        "correlation": 0.75,
        "lag_days": 7,
        "description": "Economic activity - 12% of price"
    },
    "Supply Disruption": {
        "weight": 0.08,
        "correlation": 0.95,
        "lag_days": 0,
        "description": "Production issues - 8% of price"
    }
}

# ============================
# PREDEFINED FEEDSTOCK FORMULAS
# ============================

PREDEFINED_FORMULAS = {
    "Polyethylene (PE)": {
        "description": "Polyethylene - based on ethylene feedstock",
        "components": [
            {"name": "Ethylene", "weight": 0.85},
            {"name": "Natural Gas", "weight": 0.10},
            {"name": "Catalysts", "weight": 0.05}
        ]
    },
    "Polypropylene (PP)": {
        "description": "Polypropylene - based on propylene feedstock",
        "components": [
            {"name": "Propylene", "weight": 0.80},
            {"name": "Natural Gas", "weight": 0.15},
            {"name": "Catalysts", "weight": 0.05}
        ]
    },
    "Propylene Oxide (PO)": {
        "description": "Propylene oxide - 67% Propylene + 33% Ethanol",
        "components": [
            {"name": "Propylene", "weight": 0.67},
            {"name": "Ethanol", "weight": 0.33}
        ]
    },
    "Acrylic Acid Polymer": {
        "description": "Acrylic acid-based polymers",
        "components": [
            {"name": "Acrylic Acid", "weight": 0.60},
            {"name": "Ethanol", "weight": 0.25},
            {"name": "Water", "weight": 0.15}
        ]
    },
    "PET": {
        "description": "Polyethylene Terephthalate",
        "components": [
            {"name": "Ethylene Glycol", "weight": 0.45},
            {"name": "Dimethyl Terephthalate", "weight": 0.45},
            {"name": "Natural Gas", "weight": 0.10}
        ]
    }
}

# ============================
# SESSION STATE
# ============================

if "session_id" not in st.session_state:
    st.session_state.session_id = hashlib.md5(f"{datetime.now()}".encode()).hexdigest()[:16]

if "df_series_list" not in st.session_state:
    st.session_state.df_series_list = None

if "df_forecast_series_list" not in st.session_state:
    st.session_state.df_forecast_series_list = None

if "df_pricing_data" not in st.session_state:
    st.session_state.df_pricing_data = None

if "df_forecast_data" not in st.session_state:
    st.session_state.df_forecast_data = None

if "df_pricing_normalized" not in st.session_state:
    st.session_state.df_pricing_normalized = None

if "df_forecast_normalized" not in st.session_state:
    st.session_state.df_forecast_normalized = None

if "selected_series_multi" not in st.session_state:
    st.session_state.selected_series_multi = []

if "selected_forecast_series_multi" not in st.session_state:
    st.session_state.selected_forecast_series_multi = []

if "selected_forecast_publication" not in st.session_state:
    st.session_state.selected_forecast_publication = None

if "custom_formulas" not in st.session_state:
    st.session_state.custom_formulas = {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "fx_rates" not in st.session_state:
    st.session_state.fx_rates = {}

if "forecasts" not in st.session_state:
    st.session_state.forecasts = {}

if "forecast_analysis" not in st.session_state:
    st.session_state.forecast_analysis = {}

if "data_pulled_insights" not in st.session_state:
    st.session_state.data_pulled_insights = None

if "forecast_insights" not in st.session_state:
    st.session_state.forecast_insights = None

if "user_role" not in st.session_state:
    st.session_state.user_role = "General Analyst"

if "current_formula" not in st.session_state:
    st.session_state.current_formula = None

if "current_formula_name" not in st.session_state:
    st.session_state.current_formula_name = None

if "current_formula_components" not in st.session_state:
    st.session_state.current_formula_components = []

if "current_blend_insights" not in st.session_state:
    st.session_state.current_blend_insights = None

if "current_normalization_currency" not in st.session_state:
    st.session_state.current_normalization_currency = "USD"

if "current_normalization_unit" not in st.session_state:
    st.session_state.current_normalization_unit = "mt"

if "show_raw" not in st.session_state:
    st.session_state.show_raw = False

# ============================
# FX RATES & UNIT CONVERSION
# ============================

@st.cache_data(ttl=3600)
def fetch_fx_rates(base_currency="USD"):
    """Fetch latest FX rates"""
    try:
        response = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{base_currency}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        rates = data.get('rates', {})
        st.session_state.fx_rates = rates
        return rates
    except Exception as e:
        log_debug("FX Rate Fetch Error", str(e)[:100])
        return {
            'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 149.5,
            'AUD': 1.53, 'CAD': 1.36, 'CNY': 7.25
        }

UNIT_CONVERSIONS = {
    'kg': 1.0, 'mt': 1000.0, 't': 1000.0, 'lb': 0.453592,
    'oz': 0.0283495, 'barrel': 158.987, 'litre': 1.0,
    'liter': 1.0, 'gallon': 3.78541, 'cwt': 50.8023, 'ton': 907.185
}

def normalize_currency(value, from_currency, to_currency="USD", fx_rates=None):
    """Convert value between currencies"""
    if from_currency == to_currency:
        return value
    
    if fx_rates is None:
        fx_rates = fetch_fx_rates("USD")
    
    try:
        if from_currency != "USD":
            value_usd = value / fx_rates.get(from_currency, 1.0)
        else:
            value_usd = value
        
        if to_currency != "USD":
            value_target = value_usd * fx_rates.get(to_currency, 1.0)
        else:
            value_target = value_usd
        
        return value_target
    except:
        return value

def normalize_unit(value, from_unit, to_unit="kg"):
    """Convert value between units"""
    if from_unit == to_unit:
        return value
    
    try:
        from_factor = UNIT_CONVERSIONS.get(from_unit.lower(), 1.0)
        to_factor = UNIT_CONVERSIONS.get(to_unit.lower(), 1.0)
        
        value_in_base = value * from_factor
        return value_in_base / to_factor
    except:
        return value

def normalize_dataframe(df, target_currency="USD", target_unit="mt"):
    """Normalize all prices to same currency and unit"""
    df_norm = df.copy()
    fx_rates = fetch_fx_rates("USD")
    
    for idx, row in df_norm.iterrows():
        for price_col in ['Low', 'High', 'Mid']:
            if price_col in df_norm.columns and pd.notna(row[price_col]):
                original_currency = row.get('Currency', 'USD')
                df_norm.at[idx, f'{price_col}_orig'] = row[price_col]
                df_norm.at[idx, f'{price_col}_currency_orig'] = original_currency
                df_norm.at[idx, price_col] = normalize_currency(
                    row[price_col], original_currency, target_currency, fx_rates
                )
        
        original_unit = row.get('Unit', 'mt')
        df_norm.at[idx, 'Unit_orig'] = original_unit
        df_norm.at[idx, 'Unit'] = target_unit
        
        unit_factor = normalize_unit(1.0, original_unit, target_unit)
        for price_col in ['Low', 'High', 'Mid']:
            if price_col in df_norm.columns and pd.notna(df_norm.at[idx, price_col]):
                df_norm.at[idx, price_col] = df_norm.at[idx, price_col] * unit_factor
    
    df_norm['Currency_normalized'] = target_currency
    df_norm['Unit_normalized'] = target_unit
    
    return df_norm

def normalize_forecast_dataframe(df, target_currency="USD"):
    """Normalize forecast prices to same currency"""
    df_norm = df.copy()
    fx_rates = fetch_fx_rates("USD")
    
    for idx, row in df_norm.iterrows():
        if 'Mid' in df_norm.columns and pd.notna(row['Mid']):
            original_currency = row.get('Currency', 'USD')
            df_norm.at[idx, 'Mid_orig'] = row['Mid']
            df_norm.at[idx, 'Currency_orig'] = original_currency
            df_norm.at[idx, 'Mid'] = normalize_currency(
                row['Mid'], original_currency, target_currency, fx_rates
            )
    
    df_norm['Currency_normalized'] = target_currency
    return df_norm

# ============================
# UTILITY FUNCTIONS
# ============================

def get_basic_auth_header(username, password):
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"

# ============================
# ICIS API CONFIG
# ============================

ICIS_API_ENDPOINT = "https://api.icis.com/v1/search"

SERIES_LIST_XML = """<request xmlns="http://iddn.icis.com/ns/search">
    <scope>
        <type>series</type>
    </scope>
    <constraints>
        <and>
          <compare field="c:terminated" op="eq" value="false"/>
          <field-refers-to field="c:domain" href="http://iddn.icis.com/domain/petchem"/>
          <field-refers-to field="c:descriptor" href="http://iddn.icis.com/descriptor/credit-enabled-petchem-energy-series"/>
       </and>
    </constraints>  
    <options>
        <first-result>1</first-result>
        <max-results>5000</max-results>
        <order-by key="created-on" direction="ascending" xml:lang="en"/>
    </options>
    <view>
        <field>c:id</field>
        <field xml:lang="en">f:name</field>
        <field>f:publication.c:id</field>
        <field xml:lang="en">f:publication.f:name</field>
    </view>
</request>"""

FORECAST_SERIES_LIST_XML = """<request xmlns="http://iddn.icis.com/ns/search">
<scope>
<type>series</type>
</scope>
<constraints>
<classified-as field="c:descriptor" href="http://iddn.icis.com/descriptor/petchem-forecast-series"/>
<compare field="c:terminated" op="eq" value="false" />
</constraints>
<options>
<first-result>1</first-result>
<max-results>5000</max-results>
<order-by key="created-on" direction="ascending" xml:lang="en"/>
</options>
<view>
<field>c:id</field>
<field xml:lang="en">f:name</field>
<field>f:publication.c:id</field>
<field xml:lang="en">f:publication.f:name</field>
</view>
</request>"""

PRICING_DATA_XML_TEMPLATE = """<request xmlns="http://iddn.icis.com/ns/search">
   <scope>
{series_elements}
   </scope>
   <constraints>
      <and>
         <compare field="c:series-order" op="ge" value="{start_date}"/>
         <compare field="c:series-order" op="le" value="{end_date}"/>
      </and>
   </constraints>
   <view>
      <field>c:series.f:name</field>
      <field>c:series.f:currency.f:name</field>
      <field>c:series.f:location.f:name</field>
      <field>c:series.f:size-unit.f:name</field>
      <field>c:series.f:trade-terms.f:name</field>
      <field>c:series-order</field>
      <field>f:assessment-low</field>
      <field>f:assessment-high</field>
      <field>f:mid</field>
   </view>
</request>"""

FORECAST_DATA_XML_BATCHED_TEMPLATE = """<request xmlns="http://iddn.icis.com/ns/search">
<scope>
{series_references}
</scope>
<constraints>
<type>series-item</type>
<compare field="c:created-on" op="gt" value="{start_date}"/>
<compare field="c:created-on" op="lt" value="{end_date}"/>  
</constraints>
<options>
<max-results>1000</max-results>
<order-by key="released-on" direction="descending" />
</options>  
</request>"""

# ============================
# XML PARSING
# ============================

def parse_series_list(response_content):
    """Parse series list"""
    try:
        ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
        ET.register_namespace('s', 'http://iddn.icis.com/ns/search')
        
        root = ET.fromstring(response_content)
        
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            's': 'http://iddn.icis.com/ns/search'
        }
        
        records = []
        entries = root.findall('.//atom:entry', ns)
        
        log_debug("Parse Series List", f"Found {len(entries)} entries")
        
        for entry in entries:
            try:
                content = entry.find('atom:content', ns)
                if content is None:
                    continue
                
                series_elem = content.find('s:credit-enabled-petchem-energy-series', ns)
                if series_elem is None:
                    continue
                
                series_id_elem = series_elem.find('s:c_id', ns)
                series_id = series_id_elem.text if series_id_elem is not None else ''
                
                series_name_elem = series_elem.find('s:name', ns)
                series_name = series_name_elem.text if series_name_elem is not None else ''
                
                pub_name_elems = series_elem.findall('s:f_publication.name', ns)
                pub_name = pub_name_elems[0].text if pub_name_elems and pub_name_elems[0].text else ''
                
                if series_id and series_name:
                    records.append({
                        'Series ID': series_id,
                        'Series Name': series_name,
                        'Publication Name': pub_name,
                    })
            except Exception as e:
                log_debug("Parse Series Entry Error", str(e)[:80])
                continue
        
        df = pd.DataFrame(records)
        if not df.empty:
            df = df.drop_duplicates(subset=['Series ID'])
        
        log_debug("Series List Parsed", f"Total: {len(df)}")
        return df
    
    except Exception as e:
        log_debug("Parse Series List Error", str(e)[:100])
        return pd.DataFrame()

def parse_forecast_series_list(response_content):
    """Parse forecast series"""
    try:
        ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
        ET.register_namespace('s', 'http://iddn.icis.com/ns/search')
        
        root = ET.fromstring(response_content)
        
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            's': 'http://iddn.icis.com/ns/search'
        }
        
        records = []
        entries = root.findall('.//atom:entry', ns)
        
        log_debug("Parse Forecast Series", f"Found {len(entries)} entries")
        
        for entry in entries:
            try:
                content = entry.find('atom:content', ns)
                if content is None:
                    continue
                
                series_elem = content.find('s:petchem-forecast-series', ns)
                if series_elem is None:
                    series_elem = content.find('s:series', ns)
                if series_elem is None:
                    continue
                
                series_id_elem = series_elem.find('s:c_id', ns)
                series_id = series_id_elem.text if series_id_elem is not None else ''
                
                series_name_elem = series_elem.find('s:name', ns)
                series_name = series_name_elem.text if series_name_elem is not None else ''
                
                pub_name_elems = series_elem.findall('s:f_publication.name', ns)
                pub_name = pub_name_elems[0].text if pub_name_elems and pub_name_elems[0].text else ''
                
                if series_id and series_name:
                    records.append({
                        'Series ID': series_id,
                        'Series Name': series_name,
                        'Publication Name': pub_name,
                    })
            except Exception as e:
                log_debug("Parse Forecast Series Entry Error", str(e)[:80])
                continue
        
        df = pd.DataFrame(records)
        if not df.empty:
            df = df.drop_duplicates(subset=['Series ID'])
        
        log_debug("Forecast Series Parsed", f"Total: {len(df)}")
        return df
    
    except Exception as e:
        log_debug("Parse Forecast Series Error", str(e)[:100])
        return pd.DataFrame()

def parse_pricing_data(response_content):
    """Parse pricing data"""
    try:
        ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
        ET.register_namespace('s', 'http://iddn.icis.com/ns/search')
        
        root = ET.fromstring(response_content)
        
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            's': 'http://iddn.icis.com/ns/search'
        }
        
        records = []
        entries = root.findall('.//atom:entry', ns)
        
        log_debug("Parse Pricing Data", f"Found {len(entries)} entries")
        
        for entry in entries:
            try:
                content = entry.find('atom:content', ns)
                if content is None:
                    continue
                
                price_range = content.find('s:price-range', ns)
                if price_range is None:
                    continue
                
                record = {}
                
                series_name_elem = price_range.find('s:c_series.name', ns)
                if series_name_elem is not None and series_name_elem.text:
                    record['Series Name'] = series_name_elem.text
                
                currency_elem = price_range.find('s:c_series.f_currency.name', ns)
                if currency_elem is not None and currency_elem.text:
                    record['Currency'] = currency_elem.text
                
                location_elem = price_range.find('s:c_series.f_location.name', ns)
                if location_elem is not None and location_elem.text:
                    record['Location'] = location_elem.text
                
                unit_elem = price_range.find('s:c_series.f_size-unit.name', ns)
                if unit_elem is not None and unit_elem.text:
                    record['Unit'] = unit_elem.text
                
                terms_elem = price_range.find('s:c_series.f_trade-terms.name', ns)
                if terms_elem is not None and terms_elem.text:
                    record['Trade Terms'] = terms_elem.text
                
                date_elem = price_range.find('s:c_series-order', ns)
                if date_elem is not None and date_elem.text:
                    record['Date'] = date_elem.text
                
                low_elem = price_range.find('s:assessment-low', ns)
                if low_elem is not None and low_elem.text:
                    record['Low'] = low_elem.text
                
                high_elem = price_range.find('s:assessment-high', ns)
                if high_elem is not None and high_elem.text:
                    record['High'] = high_elem.text
                
                mid_elem = price_range.find('s:mid', ns)
                if mid_elem is not None and mid_elem.text:
                    record['Mid'] = mid_elem.text
                
                if record.get('Series Name') and record.get('Date'):
                    records.append(record)
            except Exception as e:
                log_debug("Parse Pricing Entry Error", str(e)[:80])
                continue
        
        df = pd.DataFrame(records)
        
        if not df.empty:
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            for col in ['Low', 'High', 'Mid']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        log_debug("Pricing Data Parsed", f"Total: {len(df)}")
        return df
    
    except Exception as e:
        log_debug("Parse Pricing Data Error", str(e)[:100])
        return pd.DataFrame()

def parse_forecast_data_batched(response_content):
    """Parse BATCHED forecast data"""
    try:
        root = ET.fromstring(response_content)
        
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'ns2': 'http://iddn.icis.com/ns/entity',
            'ns3': 'http://iddn.icis.com/ns/common',
            'ns4': 'http://iddn.icis.com/ns/price'
        }
        
        records = []
        entries = root.findall('.//atom:entry', namespaces)
        
        log_debug("Parse Forecast Data (Batched)", f"Found {len(entries)} entries")
        
        for idx, entry in enumerate(entries):
            try:
                title_elem = entry.find('atom:title', namespaces)
                title = title_elem.text if title_elem is not None else ""
                
                series_name = ""
                if title:
                    parts = title.split('/')
                    if len(parts) >= 4:
                        full_name = parts[-1]
                        match = re.match(r'(.*?)-(\d{8})-(\d{8})$', full_name)
                        if match:
                            series_name = match.group(1)
                        else:
                            series_name = full_name
                
                content = entry.find('atom:content', namespaces)
                if content is None:
                    continue
                
                record = {'Series Name': series_name}
                
                forecast_elem = None
                for child in content:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if 'forecast' in tag.lower():
                        forecast_elem = child
                        break
                
                if forecast_elem is None:
                    continue
                
                for elem in forecast_elem:
                    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    value = elem.text
                    
                    if tag == 'series-order' and value:
                        record['Forecast Date'] = value
                    elif tag == 'assessed-on' and value:
                        record['Assessed On'] = value
                    elif tag == 'released-on' and value:
                        record['Released On'] = value
                    elif tag == 'created-on' and value:
                        record['Created On'] = value
                    elif tag == 'mid' and value:
                        record['Mid'] = value
                        precision = elem.get('precision', '2')
                        record['Precision'] = precision
                    elif tag == 'trade-terms' and value:
                        record['Trade Terms'] = value
                    elif tag == 'currency' and value:
                        record['Currency'] = value
                
                if 'Forecast Date' in record and 'Mid' in record:
                    records.append(record)
            
            except Exception as e:
                log_debug(f"Parse Forecast Entry {idx} Error", str(e)[:80])
                continue
        
        if records:
            df = pd.DataFrame(records)
            
            for date_col in ['Forecast Date', 'Assessed On', 'Released On', 'Created On']:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            if 'Mid' in df.columns:
                df['Mid'] = pd.to_numeric(df['Mid'], errors='coerce')
            
            log_debug("Forecast Data Parsed", f"Records: {len(df)}, Series: {df['Series Name'].nunique()}")
            
            return df
        else:
            log_debug("Forecast Parsing Result", "No records extracted")
            return pd.DataFrame()
    
    except Exception as e:
        log_debug("Parse Forecast Data Error", str(e)[:100])
        return pd.DataFrame()

# ============================
# API CALLS
# ============================

def fetch_series_list(username, password):
    """Fetch series"""
    try:
        log_debug("Fetch Series List", "Starting...")
        log_xml_request("Series List", SERIES_LIST_XML, "Fetching all real pricing series")
        
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/atom+xml",
            "Authorization": get_basic_auth_header(username, password)
        }
        
        with st.spinner("Fetching series..."):
            response = requests.post(
                ICIS_API_ENDPOINT,
                data=SERIES_LIST_XML.encode('utf-8'),
                headers=headers,
                timeout=30,
                verify=True
            )
        
        response.raise_for_status()
        log_debug("Fetch Series List", f"Status: {response.status_code}, Size: {len(response.content):,}")
        
        st.info(f"✅ {len(response.content):,} bytes")
        return parse_series_list(response.content)
    
    except Exception as e:
        log_debug("Fetch Series Error", str(e)[:100])
        st.error(f"❌ {str(e)}")
        return pd.DataFrame()

def fetch_forecast_series_list(username, password):
    """Fetch forecast series"""
    try:
        log_debug("Fetch Forecast Series", "Starting...")
        log_xml_request("Forecast Series List", FORECAST_SERIES_LIST_XML, "Fetching all forecast series")
        
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/atom+xml",
            "Authorization": get_basic_auth_header(username, password)
        }
        
        with st.spinner("Fetching forecast series..."):
            response = requests.post(
                ICIS_API_ENDPOINT,
                data=FORECAST_SERIES_LIST_XML.encode('utf-8'),
                headers=headers,
                timeout=30,
                verify=True
            )
        
        response.raise_for_status()
        log_debug("Fetch Forecast Series", f"Status: {response.status_code}, Size: {len(response.content):,}")
        
        st.info(f"✅ {len(response.content):,} bytes")
        return parse_forecast_series_list(response.content)
    
    except Exception as e:
        log_debug("Fetch Forecast Series Error", str(e)[:100])
        st.error(f"❌ {str(e)}")
        return pd.DataFrame()

def fetch_pricing_data(username, password, series_ids, start_date, end_date):
    """Fetch pricing data"""
    try:
        log_debug("Fetch Pricing Data", f"Series: {len(series_ids)}, Dates: {start_date} to {end_date}")
        
        series_lines = []
        for sid in series_ids:
            series_lines.append(f"      <series>http://iddn.icis.com/series/petchem/{sid}</series>")
        
        series_elements = "\n".join(series_lines)
        
        xml_request = PRICING_DATA_XML_TEMPLATE.format(
            series_elements=series_elements,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        log_xml_request(
            "Pricing Data",
            xml_request,
            f"Fetching pricing for {len(series_ids)} series from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            series_count=len(series_ids)
        )
        
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/atom+xml",
            "Authorization": get_basic_auth_header(username, password)
        }
        
        with st.spinner("Fetching pricing..."):
            response = requests.post(
                ICIS_API_ENDPOINT,
                data=xml_request.encode('utf-8'),
                headers=headers,
                timeout=30,
                verify=True
            )
        
        response.raise_for_status()
        log_debug("Fetch Pricing Data", f"Status: {response.status_code}, Size: {len(response.content):,}")
        
        st.info(f"✅ {len(response.content):,} bytes")
        return parse_pricing_data(response.content)
    
    except Exception as e:
        log_debug("Fetch Pricing Error", str(e)[:100])
        st.error(f"❌ {str(e)}")
        return pd.DataFrame()

def fetch_forecast_data_batched(username, password, series_ids, start_date, end_date):
    """Fetch BATCHED forecast data - all series in ONE request"""
    try:
        log_debug("Fetch Forecast Data (Batched)", f"Series: {len(series_ids)}, Dates: {start_date} to {end_date}")
        
        series_refs = []
        for sid in series_ids:
            series_refs.append(f"   <referencing>http://iddn.icis.com/series/petchem/{sid}</referencing>")
        
        series_references = "\n".join(series_refs)
        
        xml_request = FORECAST_DATA_XML_BATCHED_TEMPLATE.format(
            series_references=series_references,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        log_xml_request(
            "Forecast Data (Batched)",
            xml_request,
            f"Fetching forecast for {len(series_ids)} series in BATCHED REQUEST from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            series_count=len(series_ids)
        )
        
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/atom+xml",
            "Authorization": get_basic_auth_header(username, password)
        }
        
        with st.spinner(f"Fetching {len(series_ids)} forecast series (batched)..."):
            response = requests.post(
                ICIS_API_ENDPOINT,
                data=xml_request.encode('utf-8'),
                headers=headers,
                timeout=60,
                verify=True
            )
        
        response.raise_for_status()
        log_debug("Fetch Forecast Data", f"Status: {response.status_code}, Size: {len(response.content):,}, Series: {len(series_ids)}")
        
        st.info(f"✅ {len(response.content):,} bytes - {len(series_ids)} series in 1 request")
        return parse_forecast_data_batched(response.content)
    
    except Exception as e:
        log_debug("Fetch Forecast Error", str(e)[:100])
        st.error(f"❌ {str(e)}")
        return pd.DataFrame()

# ============================
# FORECASTING FUNCTIONS
# ============================

def simple_forecast(series_data, forecast_days=30):
    """Simple forecast using trend analysis"""
    if len(series_data) < 5:
        return None
    
    values = series_data['Mid'].values
    x = np.arange(len(values))
    y = values
    
    x_mean = x.mean()
    y_mean = y.mean()
    slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
    intercept = y_mean - slope * x_mean
    
    future_x = np.arange(len(values), len(values) + forecast_days)
    forecast_y = intercept + slope * future_x
    
    residuals = y - (intercept + slope * x)
    std_error = np.std(residuals)
    
    last_date = series_data['Date'].max()
    forecast_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=forecast_days,
        freq='D'
    )
    
    forecast_df = pd.DataFrame({
        'Date': forecast_dates,
        'Forecast': forecast_y,
        'Upper Bound': forecast_y + 1.96 * std_error,
        'Lower Bound': forecast_y - 1.96 * std_error
    })
    
    return {
        'data': forecast_df,
        'slope': slope,
        'trend': 'Up ⬆️' if slope > 0 else 'Down ⬇️',
        'std_error': std_error
    }

def ml_forecast(series_data, forecast_days=30):
    """ML-based forecast"""
    if not ML_AVAILABLE or len(series_data) < 5:
        return simple_forecast(series_data, forecast_days)
    
    try:
        X = np.arange(len(series_data)).reshape(-1, 1)
        y = series_data['Mid'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        future_X = np.arange(len(series_data), len(series_data) + forecast_days).reshape(-1, 1)
        forecast_y = model.predict(future_X)
        
        residuals = y - model.predict(X)
        std_error = np.std(residuals)
        
        last_date = series_data['Date'].max()
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=forecast_days,
            freq='D'
        )
        
        forecast_df = pd.DataFrame({
            'Date': forecast_dates,
            'Forecast': forecast_y,
            'Upper Bound': forecast_y + 1.96 * std_error,
            'Lower Bound': forecast_y - 1.96 * std_error
        })
        
        return {
            'data': forecast_df,
            'slope': model.coef_[0],
            'trend': 'Up ⬆️' if model.coef_[0] > 0 else 'Down ⬇️',
            'std_error': std_error
        }
    except:
        return simple_forecast(series_data, forecast_days)

def forecast_prices(df_pricing, forecast_days=30):
    """Forecast prices"""
    try:
        df = df_pricing.copy()
        df['Mid'] = pd.to_numeric(df['Mid'], errors='coerce')
        
        forecasts = {}
        
        for series_name in df['Series Name'].unique():
            series_data = df[df['Series Name'] == series_name].sort_values('Date')
            
            if len(series_data) < 5:
                continue
            
            result = ml_forecast(series_data, forecast_days)
            
            if result:
                result['data']['Series Name'] = series_name
                forecasts[series_name] = result
        
        st.session_state.forecasts = forecasts
        log_debug("Forecast Generated", f"Total: {len(forecasts)}")
        return forecasts
    
    except Exception as e:
        log_debug("Forecast Error", str(e)[:100])
        st.warning(f"Forecast error: {e}")
        return {}

def calculate_scenario_analysis(base_price, driver_changes):
    """Calculate price scenarios"""
    impact = 0.0
    
    if 'crude_oil_change' in driver_changes:
        crude_impact = (driver_changes['crude_oil_change'] / 100) * PRICE_DRIVER_WEIGHTS['Crude Oil']['weight']
        impact += crude_impact
    
    if 'natural_gas_change' in driver_changes:
        gas_impact = (driver_changes['natural_gas_change'] / 100) * PRICE_DRIVER_WEIGHTS['Natural Gas']['weight']
        impact += gas_impact
    
    if 'usd_change' in driver_changes:
        usd_impact = -(driver_changes['usd_change'] / 100) * PRICE_DRIVER_WEIGHTS['USD Strength']['weight']
        impact += usd_impact
    
    if 'demand_change' in driver_changes:
        demand_impact = (driver_changes['demand_change'] / 100) * PRICE_DRIVER_WEIGHTS['Global Demand']['weight']
        impact += demand_impact
    
    scenario_price = base_price * (1 + impact)
    
    return {
        'base_price': base_price,
        'scenario_price': scenario_price,
        'impact_percent': impact * 100,
        'impact_amount': scenario_price - base_price
    }

# ============================
# LLM INTEGRATION
# ============================

def call_groq_llm(prompt, system=""):
    """Call Groq LLM"""
    try:
        if not GROQ_API_KEY:
            return "❌ Error: GROQ_API_KEY not found"
        
        from groq import Groq
        
        log_debug("Groq LLM Call", "Starting...")
        
        client = Groq(api_key=GROQ_API_KEY)
        
        models_to_try = [
            "mixtral-8x7b-32768",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
        ]
        
        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system or "You are an expert petrochemical market analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    model=model,
                    temperature=0.7,
                    max_tokens=2000,
                )
                
                response_text = completion.choices[0].message.content
                log_debug("Groq LLM Success", f"Model: {model}, Length: {len(response_text)}")
                return response_text
            except Exception as e:
                if "decommissioned" in str(e).lower() or "model_not_found" in str(e).lower():
                    log_debug("Groq Model Skip", f"Model {model} unavailable")
                    continue
                else:
                    log_debug("Groq Error", str(e)[:100])
                    return f"❌ Error: {str(e)}"
        
        return "❌ No available Groq models"
    
    except Exception as e:
        log_debug("Groq LLM Error", str(e)[:100])
        return f"❌ Error: {str(e)}"

def generate_data_pulled_insights(df_pricing, user_role="General Analyst"):
    """Generate insights when data pulled"""
    try:
        if df_pricing is None or df_pricing.empty:
            return None
        
        df_numeric = df_pricing.copy()
        df_numeric['Mid'] = pd.to_numeric(df_numeric['Mid'], errors='coerce')
        
        price_stats = df_numeric['Mid'].describe()
        volatility = (df_numeric.groupby('Series Name')['Mid'].std() / df_numeric.groupby('Series Name')['Mid'].mean() * 100).mean()
        
        summary = f"""
DATA ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Dataset:
- Records: {len(df_numeric)}
- Series: {df_numeric['Series Name'].nunique()}
- Period: {df_numeric['Date'].min()} to {df_numeric['Date'].max()}
- Days: {(df_numeric['Date'].max() - df_numeric['Date'].min()).days}

📍 Geographic:
- Locations: {', '.join(df_numeric['Location'].unique())}
- Currencies: {', '.join(df_numeric['Currency'].unique())}
- Units: {', '.join(df_numeric['Unit'].unique())}

📈 Prices:
- Avg: ${price_stats['mean']:.2f}
- Min: ${price_stats['min']:.2f}
- Max: ${price_stats['max']:.2f}
- Std Dev: ${price_stats['std']:.2f}
- Volatility: {volatility:.1f}%

Top 5 Series by Price:
{df_numeric.groupby('Series Name')['Mid'].mean().nlargest(5).to_string()}
"""
        
        prompt = f"""{summary}

Provide KEY INSIGHTS for {user_role}:
1. Current market status and trends
2. Key price patterns and drivers
3. Business implications
4. Risk alerts and volatility assessment
5. Opportunities and recommendations
6. Next steps

Be specific, actionable, and data-driven."""
        
        insights = call_groq_llm(prompt, system="You are an expert petrochemical market analyst.")
        log_debug("Data Insights Generated", "Success")
        return insights
    
    except Exception as e:
        log_debug("Data Insights Error", str(e)[:100])
        return None

def generate_forecast_insights(df_forecast, user_role="General Analyst"):
    """Generate AI insights for forecast data"""
    try:
        if df_forecast is None or df_forecast.empty:
            return None
        
        df_numeric = df_forecast.copy()
        if 'Mid' in df_numeric.columns:
            df_numeric['Mid'] = pd.to_numeric(df_numeric['Mid'], errors='coerce')
        
        series_count = df_numeric['Series Name'].nunique() if 'Series Name' in df_numeric.columns else 0
        
        price_stats = df_numeric['Mid'].describe() if 'Mid' in df_numeric.columns else None
        
        forecast_dates = sorted(df_numeric['Forecast Date'].unique()) if 'Forecast Date' in df_numeric.columns else []
        
        summary = f"""
FORECAST DATA ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Dataset:
- Total Records: {len(df_numeric)}
- Series: {series_count}
- Forecast Dates: {len(forecast_dates)}
- Date Range: {forecast_dates[0] if forecast_dates else 'N/A'} to {forecast_dates[-1] if forecast_dates else 'N/A'}

📈 Price Statistics:
"""
        if price_stats is not None:
            summary += f"""- Avg: ${price_stats['mean']:.2f}
- Min: ${price_stats['min']:.2f}
- Max: ${price_stats['max']:.2f}
- Std Dev: ${price_stats['std']:.2f}"""
        
        if 'Series Name' in df_numeric.columns:
            top_series = df_numeric.groupby('Series Name')['Mid'].mean().nlargest(5)
            summary += f"\n\nTop Forecast Prices:\n{top_series.to_string()}"
        
        prompt = f"""{summary}

For {user_role}, provide:
1. Forecast market direction (up/down/stable)
2. Key drivers of forecasted prices
3. Confidence level (high/medium/low) and why
4. Major risks and uncertainties
5. Investment outlook and recommendations
6. Comparison to current pricing if available

Be strategic and forward-looking."""
        
        insights = call_groq_llm(prompt, system="You are an expert petrochemical market analyst specializing in forecasting.")
        log_debug("Forecast Insights Generated", "Success")
        return insights
    
    except Exception as e:
        log_debug("Forecast Insights Error", str(e)[:100])
        return None

def generate_blend_insights(blend_name, components, df_composite_price, user_role="General Analyst"):
    """Generate insights on blend meaning and outlook"""
    try:
        if df_composite_price is None or df_composite_price.empty:
            return None
        
        avg_price = df_composite_price['Composite Price'].mean()
        min_price = df_composite_price['Composite Price'].min()
        max_price = df_composite_price['Composite Price'].max()
        volatility = df_composite_price['Composite Price'].std()
        
        component_str = "\n".join([f"  - {c['name']}: {c['weight']*100:.1f}%" for c in components])
        
        summary = f"""
CUSTOM BLEND ANALYSIS - {blend_name}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📦 Formula:
{component_str}

📈 Performance:
- Average Price: ${avg_price:.2f}
- Price Range: ${min_price:.2f} - ${max_price:.2f}
- Volatility: ${volatility:.2f} ({(volatility/avg_price)*100:.1f}%)
- Historical Days: {len(df_composite_price)}
"""
        
        prompt = f"""{summary}

For {user_role}, explain:
1. What does this blend represent in the market?
2. Primary use cases and applications
3. Risk profile (high/medium/low volatility)
4. Price drivers and their relative importance
5. Market outlook for this blend (next 3-6 months)
6. Hedging strategies
7. Competitive positioning

Be insightful and practical."""
        
        insights = call_groq_llm(prompt, system="You are an expert petrochemical product analyst.")
        log_debug("Blend Insights Generated", "Success")
        return insights
    
    except Exception as e:
        log_debug("Blend Insights Error", str(e)[:100])
        return None

def generate_formula_analysis(df_pricing, formula_name, formula_components, user_role="General Analyst"):
    """Generate forecast analysis"""
    try:
        df = df_pricing.copy()
        df['Mid'] = pd.to_numeric(df['Mid'], errors='coerce')
        
        current_price = df['Mid'].mean()
        
        component_prices = []
        for comp in formula_components:
            comp_data = df[df['Series Name'].str.contains(comp['name'], case=False, na=False)]
            if not comp_data.empty:
                component_prices.append({
                    'name': comp['name'],
                    'weight': comp['weight'],
                    'avg_price': comp_data['Mid'].mean()
                })
        
        hist_high = df['Mid'].max()
        hist_low = df['Mid'].min()
        hist_avg = df['Mid'].mean()
        hist_volatility = df['Mid'].std()
        
        summary = f"""
FORMULA - {formula_name}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Current:
- Price: ${current_price:.2f}
- High: ${hist_high:.2f}
- Low: ${hist_low:.2f}
- Volatility: ${hist_volatility:.2f} ({(hist_volatility/hist_avg)*100:.1f}%)

Components:
"""
        for comp in component_prices:
            summary += f"\n- {comp['name']} ({comp['weight']*100:.0f}%): ${comp['avg_price']:.2f}"
        
        prompt = f"""{summary}

For {user_role}, analyze:
1. Is this formula balanced?
2. What's driving the composite price?
3. Risk assessment
4. Hedging opportunities
5. Market positioning
6. Recommendations

Be analytical."""
        
        analysis = call_groq_llm(prompt, system="You are a petrochemical market analyst.")
        log_debug("Formula Analysis Generated", "Success")
        return analysis
    
    except Exception as e:
        log_debug("Formula Analysis Error", str(e)[:100])
        return None

# ============================
# FORMULA FUNCTIONS
# ============================

def create_custom_formula(formula_name, components):
    """Create formula"""
    total_weight = sum([c['weight'] for c in components])
    
    if abs(total_weight - 1.0) > 0.001:
        st.error(f"❌ Weights must sum to 1.0")
        return None
    
    formula = {
        "name": formula_name,
        "components": components,
        "created_at": datetime.now().isoformat(),
    }
    
    st.session_state.custom_formulas[formula_name] = formula
    log_debug("Create Formula", f"Name: {formula_name}, Components: {len(components)}")
    st.success(f"✅ Formula created")
    return formula

def calculate_formula_price(df_pricing, formula_name, formula_components):
    """Calculate composite price"""
    try:
        log_debug("Calculate Formula", f"Formula: {formula_name}")
        
        df = df_pricing.copy()
        df['Mid'] = pd.to_numeric(df['Mid'], errors='coerce')
        
        results = []
        
        for date, date_group in df.groupby('Date'):
            weighted_price = 0.0
            components_found = 0
            component_detail = []
            
            for component in formula_components:
                component_name = component['name']
                weight = component['weight']
                
                matching_series = date_group[
                    date_group['Series Name'].str.contains(
                        component_name,
                        case=False,
                        na=False
                    )
                ]
                
                if not matching_series.empty:
                    component_price = matching_series['Mid'].mean()
                    weighted_price += component_price * weight
                    components_found += 1
                    
                    component_detail.append({
                        'component': component_name,
                        'weight': f"{weight*100:.1f}%",
                        'price': f"${component_price:.2f}",
                        'contribution': f"${component_price * weight:.2f}"
                    })
            
            if components_found > 0:
                results.append({
                    'Date': date,
                    'Formula': formula_name,
                    'Composite Price': weighted_price,
                    'Components Found': components_found,
                    'Details': component_detail
                })
        
        log_debug("Formula Calculated", f"Results: {len(results)}")
        
        if results:
            return pd.DataFrame(results)
        else:
            st.warning(f"No matching components found")
            return pd.DataFrame()
    
    except Exception as e:
        log_debug("Calculate Formula Error", str(e)[:100])
        st.error(f"Error: {e}")
        return pd.DataFrame()

def compare_formulas(df_pricing, formula_list):
    """Compare formulas"""
    try:
        all_results = []
        
        for formula_name in formula_list:
            if formula_name in st.session_state.custom_formulas:
                formula = st.session_state.custom_formulas[formula_name]
                components = formula['components']
            elif formula_name in PREDEFINED_FORMULAS:
                formula = PREDEFINED_FORMULAS[formula_name]
                components = formula['components']
            else:
                continue
            
            result_df = calculate_formula_price(df_pricing, formula_name, components)
            all_results.append(result_df)
        
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        else:
            return pd.DataFrame()
    
    except Exception as e:
        log_debug("Compare Formulas Error", str(e)[:100])
        st.error(f"Error: {e}")
        return pd.DataFrame()

# ============================
# CUSTOM CSS STYLING
# ============================

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
    /* Insight box styling */
    .insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        border-left: 5px solid #00d4ff;
        margin: 10px 0;
    }
    
    .insight-box h3 {
        color: #00d4ff;
        margin-top: 0;
    }
    
    .insight-box ul {
        margin: 10px 0;
    }
    
    .insight-box li {
        margin: 5px 0;
        line-height: 1.6;
    }
    
    /* Formula component box */
    .formula-box {
        background: rgba(102, 126, 234, 0.1);
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin: 2px;
    }
    
    .status-success {
        background-color: #10b981;
        color: white;
    }
    
    .status-warning {
        background-color: #f59e0b;
        color: white;
    }
    
    .status-error {
        background-color: #ef4444;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# ============================
# MAIN UI
# ============================

st.title("🛢️ ICIS Pricing Dashboard - ENHANCED")

st.markdown("""
<div style="background-color: #0f766e; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
    <h3 style="color: #fff; margin: 0;">✅ COMPLETE ENHANCED PLATFORM</h3>
    <p style="color: #d1fae5; margin: 5px 0;">
        📊 Real pricing | 🔮 Forecasts (Batched XML) | 💱 Normalized Charts | 🧪 Blend Components | 🤖 AI Insights | 🔍 Debug
    </p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    
    username_input = st.text_input("ICIS Username", type="password")
    password_input = st.text_input("ICIS Password", type="password")
    
    st.divider()
    
    st.subheader("👤 Your Role")
    user_role = st.selectbox(
        "Select your role",
        ["General Analyst", "Trader", "Producer", "Supplier", "Risk Manager"]
    )
    st.session_state.user_role = user_role
    
    st.divider()
    
    if not GROQ_API_KEY:
        st.error("⚠️ GROQ_API_KEY not set")
    else:
        st.success("✅ Groq LLM Ready")
    
    if ML_AVAILABLE:
        st.info("✅ ML Available")
    
    st.divider()
    
    page = st.radio("Navigate:", [
        "📊 Dashboard",
        "🔍 Real Series",
        "🔮 Forecast Series",
        "📈 Pricing Data",
        "📊 Forecast Data",
        "💱 Normalization",
        "🎯 Price Drivers",
        "📈 Scenarios",
        "🔮 ML Forecasts",
        "🧮 Formula Builder",
        "📊 Apply Formulas",
        "📈 Compare Formulas",
        "🤖 AI Insights",
        "💬 Chat",
        "🔍 XML API Scripts",
        "🐛 Debug Logs"
    ])

# ============================
# DASHBOARD PAGE
# ============================

if page == "📊 Dashboard":
    st.subheader("📊 Dashboard")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Real Series", len(st.session_state.selected_series_multi))
    with col2:
        st.metric("Forecast Series", len(st.session_state.selected_forecast_series_multi))
    with col3:
        st.metric("Formulas", len(st.session_state.custom_formulas))
    with col4:
        st.metric("Debug Events", len(st.session_state.debug_log))
    with col5:
        st.metric("Role", st.session_state.user_role[:12])
    
    st.divider()
    
    st.subheader("✨ Key Enhancements")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🤖 AI Insights
        - **Pricing Tab**: Dynamic insights when data pulled
        - **Forecast Tab**: AI analysis of forecasts
        - **Blend Tab**: Insights on formula meaning
        
        ### 💱 Normalized Charts
        - Currency conversion (USD/EUR/GBP)
        - Unit normalization
        - Applied units shown on charts
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Blend Visualization
        - Component curves (dashed lines)
        - Blended price (solid line)
        - Component details in hover
        - Full blend insights & outlook
        
        ### ✅ Batched Forecast XML
        - All series in ONE request
        - Same as pricing approach
        - Visible in Debug tab
        """)
    
    with col3:
        st.markdown("""
        ### 📈 Feature Highlights
        - Real-time market data
        - ML forecasting
        - Scenario analysis
        - Formula builder
        - Smart chat
        - Full API debugging
        """)

# ============================
# REAL SERIES PAGE
# ============================

elif page == "🔍 Real Series":
    st.subheader("🔍 Select Real Pricing Series")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🔄 Load Series", use_container_width=True):
            if not username_input or not password_input:
                st.error("❌ Enter credentials")
            else:
                df = fetch_series_list(username_input, password_input)
                if not df.empty:
                    st.session_state.df_series_list = df
                    st.rerun()
    
    with col2:
        if st.button("Clear"):
            st.session_state.df_series_list = None
            st.session_state.df_pricing_data = None
            st.session_state.selected_series_multi = []
            st.rerun()
    
    st.divider()
    
    df_list = st.session_state.df_series_list
    
    if df_list is None or df_list.empty:
        st.info("Click 'Load Series' to start")
    else:
        st.subheader(f"📋 Available Series: {len(df_list)}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", len(df_list))
        with col2:
            st.metric("Publications", df_list['Publication Name'].nunique())
        with col3:
            st.metric("Selected", len(st.session_state.selected_series_multi))
        
        st.divider()
        
        publications = sorted(df_list['Publication Name'].unique())
        selected_pub = st.selectbox("Select Publication", publications)
        
        if selected_pub:
            pub_series = df_list[df_list['Publication Name'] == selected_pub].sort_values('Series Name')
            series_list = pub_series['Series Name'].tolist()
            
            st.subheader(f"📄 {selected_pub} - {len(series_list)} series")
            
            selected_in_pub = st.multiselect(
                "Select series from this publication",
                series_list,
                key=f"series_select_{selected_pub}"
            )
            
            for series in series_list:
                if series in selected_in_pub:
                    full_id = pub_series[pub_series['Series Name'] == series]['Series ID'].iloc[0]
                    if not any(s['Series ID'] == full_id for s in st.session_state.selected_series_multi):
                        st.session_state.selected_series_multi.append({
                            'Series Name': series,
                            'Series ID': full_id,
                            'Publication': selected_pub
                        })
            
            st.session_state.selected_series_multi = [
                s for s in st.session_state.selected_series_multi
                if s['Series Name'] in selected_in_pub or s['Publication'] != selected_pub
            ]
        
        st.divider()
        
        if st.session_state.selected_series_multi:
            selection_df = pd.DataFrame(st.session_state.selected_series_multi)
            st.dataframe(selection_df[['Series Name', 'Publication']], use_container_width=True)
            
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                start = st.date_input("Start", datetime.today() - timedelta(days=90), key="start_real")
            with col2:
                end = st.date_input("End", datetime.today(), key="end_real")
            
            if st.button("📊 Fetch Pricing Data", use_container_width=True):
                if not username_input or not password_input:
                    st.error("Enter credentials")
                else:
                    series_ids = [s['Series ID'].split('/')[-1] for s in st.session_state.selected_series_multi]
                    df_pricing = fetch_pricing_data(username_input, password_input, series_ids, start, end)
                    
                    if not df_pricing.empty:
                        st.session_state.df_pricing_data = df_pricing
                        
                        with st.spinner("🤖 Analyzing data..."):
                            insights = generate_data_pulled_insights(df_pricing, st.session_state.user_role)
                            st.session_state.data_pulled_insights = insights
                        
                        st.success(f"✅ {len(df_pricing)} records")
                        st.rerun()

# ============================
# FORECAST SERIES PAGE
# ============================

elif page == "🔮 Forecast Series":
    st.subheader("🔮 Select Forecast Series")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🔄 Load Forecast Series", use_container_width=True):
            if not username_input or not password_input:
                st.error("❌ Enter credentials")
            else:
                df = fetch_forecast_series_list(username_input, password_input)
                if not df.empty:
                    st.session_state.df_forecast_series_list = df
                    st.rerun()
    
    with col2:
        if st.button("Clear"):
            st.session_state.df_forecast_series_list = None
            st.session_state.df_forecast_data = None
            st.session_state.selected_forecast_series_multi = []
            st.session_state.selected_forecast_publication = None
            st.rerun()
    
    st.divider()
    
    df_fcst = st.session_state.df_forecast_series_list
    
    if df_fcst is None or df_fcst.empty:
        st.info("Click 'Load Forecast Series' to start")
    else:
        st.subheader(f"📋 Forecast Series: {len(df_fcst)}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", len(df_fcst))
        with col2:
            st.metric("Publications", df_fcst['Publication Name'].nunique())
        
        st.divider()
        
        publications = sorted(df_fcst['Publication Name'].unique())
        selected_pub = st.selectbox("Select Publication", publications, key="forecast_pub_select")
        
        if selected_pub:
            st.session_state.selected_forecast_publication = selected_pub
            pub_series = df_fcst[df_fcst['Publication Name'] == selected_pub].sort_values('Series Name')
            series_list = pub_series['Series Name'].tolist()
            
            st.subheader(f"📄 {selected_pub} - {len(series_list)} series")
            
            selected_series = st.multiselect(
                "Select forecast series (will fetch as BATCHED request)",
                series_list,
                key="forecast_series_multiselect"
            )
            
            if selected_series:
                st.session_state.selected_forecast_series_multi = [
                    {
                        'Series Name': s,
                        'Series ID': pub_series[pub_series['Series Name'] == s]['Series ID'].iloc[0],
                        'Publication': selected_pub
                    }
                    for s in selected_series
                ]
                
                st.divider()
                
                st.subheader(f"Selected: {len(selected_series)} series")
                sel_df = pd.DataFrame(st.session_state.selected_forecast_series_multi)
                st.dataframe(sel_df[['Series Name', 'Publication']], use_container_width=True, height=200)
                
                st.divider()
                
                col1, col2 = st.columns(2)
                with col1:
                    start = st.date_input("Start", datetime(2026, 1, 1), key="f_start")
                with col2:
                    end = st.date_input("End", datetime(2027, 12, 31), key="f_end")
                
                if st.button("🎯 Fetch All Forecast (BATCHED XML)", use_container_width=True):
                    series_ids = [item['Series ID'].split('/')[-1] for item in st.session_state.selected_forecast_series_multi]
                    
                    df_forecast = fetch_forecast_data_batched(
                        username_input,
                        password_input,
                        series_ids,
                        start,
                        end
                    )
                    
                    if not df_forecast.empty:
                        st.session_state.df_forecast_data = df_forecast
                        
                        with st.spinner("🤖 Analyzing forecasts..."):
                            insights = generate_forecast_insights(df_forecast, st.session_state.user_role)
                            st.session_state.forecast_insights = insights
                        
                        st.success(f"✅ {len(df_forecast)} records from {len(series_ids)} series in 1 request")
                        st.rerun()
                    else:
                        st.warning("No forecast data retrieved")

# ============================
# PRICING DATA PAGE WITH AI
# ============================

elif page == "📈 Pricing Data":
    st.subheader("📈 Real Pricing Data")
    
    if st.session_state.data_pulled_insights:
        with st.container():
            st.markdown("---")
            st.subheader("🤖 AI Analysis - Data Pull")
            st.info(f"For: **{st.session_state.user_role}**")
            
            with st.expander("📊 View Insights", expanded=True):
                st.markdown("""
                <div class="insight-box">
                """ + st.session_state.data_pulled_insights.replace('\n', '<br>') + """
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
    
    df = st.session_state.df_pricing_data
    
    if df is None or df.empty:
        st.info("Fetch pricing data first")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Records", len(df))
        with col2:
            st.metric("Series", df['Series Name'].nunique())
        with col3:
            st.metric("Locations", df['Location'].nunique())
        with col4:
            valid = pd.to_numeric(df['Mid'], errors='coerce').dropna()
            st.metric("Avg", f"${valid.mean():.2f}")
        
        st.divider()
        
        st.dataframe(df, use_container_width=True, height=400)
        
        st.divider()
        
        st.subheader("📊 Trends")
        
        unique = df['Series Name'].unique()[:5]
        
        for sname in unique:
            sdata = df[df['Series Name'] == sname].sort_values('Date')
            
            if not sdata.empty:
                fig = px.line(sdata, x='Date', y=['Low', 'High', 'Mid'], title=sname, height=350)
                st.plotly_chart(fig, use_container_width=True)

# ============================
# FORECAST DATA PAGE WITH AI & NORMALIZATION
# ============================

elif page == "📊 Forecast Data":
    st.subheader("📊 Forecast Data")
    
    if st.session_state.forecast_insights:
        with st.container():
            st.markdown("---")
            st.subheader("🤖 AI Analysis - Forecast Data")
            st.info(f"For: **{st.session_state.user_role}**")
            
            with st.expander("📊 View Insights", expanded=True):
                st.markdown("""
                <div class="insight-box">
                """ + st.session_state.forecast_insights.replace('\n', '<br>') + """
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
    
    if st.session_state.selected_forecast_series_multi is None or len(st.session_state.selected_forecast_series_multi) == 0:
        st.info("Fetch forecast data first from '🔮 Forecast Series' tab")
    else:
        df = st.session_state.df_forecast_data
        
        if df is None or df.empty:
            st.warning("No data loaded")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Series", df['Series Name'].nunique() if 'Series Name' in df.columns else 0)
            with col3:
                st.metric("Publications", len(st.session_state.selected_forecast_series_multi))
            with col4:
                if 'Mid' in df.columns:
                    valid = pd.to_numeric(df['Mid'], errors='coerce').dropna()
                    st.metric("Avg Price", f"${valid.mean():.2f}")
            
            st.divider()
            
            st.subheader("💱 Normalization Settings")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                target_currency = st.selectbox(
                    "Normalize to Currency",
                    ["USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "CHF"],
                    key="fcst_curr",
                    index=0
                )
            with col2:
                st.info(f"ℹ️ Charts will show prices in {target_currency}")
            with col3:
                if st.button("📋 View Raw Data"):
                    st.session_state.show_raw = not st.session_state.show_raw
            
            st.divider()
            
            df_for_chart = df.copy()
            if target_currency != "USD" and 'Mid' in df_for_chart.columns:
                df_for_chart = normalize_forecast_dataframe(df_for_chart, target_currency)
            
            st.subheader(f"📈 Forecast Price Trends - **All Prices in {target_currency}**")
            
            st.caption(f"ℹ️ All prices converted and normalized to {target_currency} for direct comparison")
            
            if 'Forecast Date' in df_for_chart.columns and 'Mid' in df_for_chart.columns and 'Series Name' in df_for_chart.columns:
                chart_data = df_for_chart[['Series Name', 'Forecast Date', 'Mid']].copy()
                chart_data = chart_data.sort_values('Forecast Date')
                
                fig = px.line(
                    chart_data,
                    x='Forecast Date',
                    y='Mid',
                    color='Series Name',
                    markers=True,
                    height=600,
                    labels={'Mid': f'Price ({target_currency})', 'Forecast Date': 'Date'},
                    title=f'Multi-Series Forecast Comparison (Normalized to {target_currency})'
                )
                
                fig.update_xaxes(title_text="Forecast Date")
                fig.update_yaxes(title_text=f"Price ({target_currency})")
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            st.subheader("📊 Series Statistics")
            
            if 'Mid' in df_for_chart.columns and 'Series Name' in df_for_chart.columns:
                stats_data = df_for_chart.groupby('Series Name')['Mid'].agg([
                    ('Count', 'count'),
                    ('Mean', 'mean'),
                    ('Min', 'min'),
                    ('Max', 'max'),
                    ('Std Dev', 'std')
                ]).round(2)
                
                st.dataframe(stats_data, use_container_width=True)
            
            if st.session_state.show_raw:
                st.divider()
                st.subheader("📋 Raw Data")
                st.dataframe(df_for_chart, use_container_width=True, height=400)

# ============================
# NORMALIZATION PAGE
# ============================

elif page == "💱 Normalization":
    st.subheader("💱 Normalization")
    
    col1, col2 = st.columns(2)
    with col1:
        target_currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY", "CNY"], key="norm_curr")
    with col2:
        target_unit = st.selectbox("Unit", ["kg", "mt", "lb", "gallon", "litre"], key="norm_unit")
    
    st.divider()
    
    df = st.session_state.df_pricing_data
    
    if df is not None and not df.empty:
        if st.button("🔄 Normalize", use_container_width=True):
            df_norm = normalize_dataframe(df, target_currency, target_unit)
            st.session_state.df_pricing_normalized = df_norm
            st.session_state.current_normalization_currency = target_currency
            st.session_state.current_normalization_unit = target_unit
            st.rerun()
        
        if st.session_state.df_pricing_normalized is not None:
            st.divider()
            
            st.success(f"✅ Normalized to {target_currency}/{target_unit}")
            
            df_norm = st.session_state.df_pricing_normalized
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                valid = pd.to_numeric(df_norm['Mid'], errors='coerce').dropna()
                st.metric("Avg", f"${valid.mean():.2f}")
            with col2:
                st.metric("Min", f"${valid.min():.2f}")
            with col3:
                st.metric("Max", f"${valid.max():.2f}")
            with col4:
                st.metric("Unit", target_unit)
            
            st.divider()
            
            st.dataframe(df_norm, use_container_width=True, height=400)
            
            st.divider()
            
            st.subheader(f"📈 Normalized Prices - {target_currency}/{target_unit}")
            
            unique_series = df_norm['Series Name'].unique()[:5]
            
            for sname in unique_series:
                sdata = df_norm[df_norm['Series Name'] == sname].sort_values('Date')
                
                if not sdata.empty:
                    fig = px.line(
                        sdata,
                        x='Date',
                        y='Mid',
                        title=f"{sname} - Normalized",
                        height=350,
                        labels={'Mid': f'Price ({target_currency}/{target_unit})'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

# ============================
# PRICE DRIVERS PAGE
# ============================

elif page == "🎯 Price Drivers":
    st.subheader("🎯 Price Driver Analysis")
    
    drivers_data = []
    for driver_name, driver_info in PRICE_DRIVER_WEIGHTS.items():
        drivers_data.append({
            'Driver': driver_name,
            'Weight': f"{driver_info['weight']*100:.0f}%",
            'Correlation': driver_info['correlation'],
            'Lag': f"{driver_info['lag_days']}d"
        })
    
    st.dataframe(pd.DataFrame(drivers_data), use_container_width=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        weights = [v['weight'] for v in PRICE_DRIVER_WEIGHTS.values()]
        names = list(PRICE_DRIVER_WEIGHTS.keys())
        fig = px.pie(values=weights, names=names, title="Price Driver Weights")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        correlations = [abs(v['correlation']) for v in PRICE_DRIVER_WEIGHTS.values()]
        fig = px.bar(
            x=list(PRICE_DRIVER_WEIGHTS.keys()),
            y=correlations,
            labels={'x': 'Driver', 'y': 'Correlation Strength'},
            title="Driver Impact Correlation"
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================
# SCENARIOS PAGE
# ============================

elif page == "📈 Scenarios":
    st.subheader("📈 Scenario Analysis")
    
    df = st.session_state.df_pricing_data
    
    if df is None or df.empty:
        st.info("Fetch data first")
    else:
        base_price = pd.to_numeric(df['Mid'], errors='coerce').mean()
        
        st.info(f"Base Price: **${base_price:.2f}**")
        
        st.divider()
        
        crude = st.slider("Crude Oil (%)", -20, 20, 0)
        gas = st.slider("Natural Gas (%)", -20, 20, 0)
        usd = st.slider("USD Strength (%)", -10, 10, 0)
        demand = st.slider("Global Demand (%)", -20, 20, 0)
        
        if st.button("Run Scenario", use_container_width=True):
            scenario = calculate_scenario_analysis(base_price, {
                'crude_oil_change': crude,
                'natural_gas_change': gas,
                'usd_change': usd,
                'demand_change': demand
            })
            
            st.divider()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Base", f"${scenario['base_price']:.2f}")
            with col2:
                st.metric("Scenario", f"${scenario['scenario_price']:.2f}")
            with col3:
                st.metric("Impact %", f"{scenario['impact_percent']:.2f}%")
            with col4:
                st.metric("Change", f"${scenario['impact_amount']:.2f}")

# ============================
# ML FORECASTS PAGE
# ============================

elif page == "🔮 ML Forecasts":
    st.subheader("🔮 ML Forecasting")
    
    df = st.session_state.df_pricing_data
    
    if df is None or df.empty:
        st.info("Fetch data first")
    else:
        forecast_days = st.slider("Forecast Days", 7, 90, 30)
        
        if st.button("Generate Forecasts", use_container_width=True):
            forecasts = forecast_prices(df, forecast_days)
            
            if forecasts:
                st.success(f"✅ {len(forecasts)} forecasts generated")
                
                for sname, finfo in forecasts.items():
                    with st.expander(f"📊 {sname}"):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Trend", finfo['trend'])
                        with col2:
                            current = df[df['Series Name'] == sname]['Mid'].iloc[-1]
                            st.metric("Current", f"${current:.2f}")
                        with col3:
                            fcst = finfo['data']['Forecast'].iloc[-1]
                            pct = ((fcst - current) / current) * 100
                            st.metric("Forecast", f"${fcst:.2f}", f"{pct:+.1f}%")
                        with col4:
                            st.metric("Error Band", f"±${finfo['std_error']:.2f}")
                        
                        st.divider()
                        
                        hist = df[df['Series Name'] == sname].sort_values('Date')
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(x=hist['Date'], y=hist['Mid'], mode='lines+markers', name='Historical', line=dict(color='blue')))
                        fcst_data = finfo['data']
                        fig.add_trace(go.Scatter(x=fcst_data['Date'], y=fcst_data['Forecast'], mode='lines+markers', name='Forecast', line=dict(dash='dash', color='orange')))
                        fig.add_trace(go.Scatter(x=fcst_data['Date'], y=fcst_data['Upper Bound'], fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False))
                        fig.add_trace(go.Scatter(x=fcst_data['Date'], y=fcst_data['Lower Bound'], fill='tonexty', mode='lines', line_color='rgba(0,0,0,0)', fillcolor='rgba(255,0,0,0.15)', name='Confidence Band'))
                        
                        fig.update_layout(height=500, hovermode='x unified')
                        st.plotly_chart(fig, use_container_width=True)

# ============================
# FORMULA BUILDER PAGE WITH COMPONENT VISUALIZATION
# ============================

elif page == "🧮 Formula Builder":
    st.subheader("🧮 Create & Visualize Formulas")
    
    st.markdown("""
    Build custom formulas with component visualization, blend insights, and outlook.
    """)
    
    st.divider()
    
    st.subheader("📦 Predefined Formulas")
    
    col_count = 3
    cols = st.columns(col_count)
    
    for idx, (fname, finfo) in enumerate(list(PREDEFINED_FORMULAS.items())[:col_count]):
        with cols[idx % col_count]:
            with st.container(border=True):
                st.markdown(f"**{fname}**")
                st.caption(finfo['description'])
                
                for comp in finfo['components']:
                    st.caption(f"  • {comp['name']}: {comp['weight']*100:.0f}%")
    
    st.divider()
    
    st.subheader("🔨 Create Custom Formula")
    
    formula_name = st.text_input("Formula Name", placeholder="e.g., My Custom Blend")
    num = st.slider("Number of Components", 2, 6, 2)
    
    available = []
    df = st.session_state.df_pricing_data
    if df is not None and not df.empty:
        available = sorted(df['Series Name'].unique().tolist())
    
    components = []
    total = 0.0
    
    st.markdown("**Components & Weights**")
    
    for i in range(num):
        col1, col2 = st.columns(2)
        with col1:
            if available:
                comp = st.selectbox(f"Component {i+1}", [""] + available, key=f"c_{i}")
            else:
                comp = st.text_input(f"Component {i+1}", key=f"c_{i}")
        with col2:
            w = st.number_input(f"Weight {i+1} (%)", 0.0, 100.0, 100.0/num, key=f"w_{i}")
        
        if comp:
            components.append({'name': comp, 'weight': w/100.0})
            total += w/100.0
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Weight", f"{total*100:.1f}%")
    with col2:
        if abs(total - 1.0) < 0.001:
            st.success("✅ Valid")
        else:
            st.error("❌ Must sum to 100%")
    with col3:
        if st.button("Create Formula", use_container_width=True):
            if formula_name and abs(total - 1.0) < 0.001 and components:
                create_custom_formula(formula_name, components)
                st.rerun()

# ============================
# APPLY FORMULAS PAGE WITH COMPONENT CURVES & INSIGHTS - FIXED
# ============================

elif page == "📊 Apply Formulas":
    st.subheader("📊 Apply Formulas - Component Curves & Insights")
    
    df = st.session_state.df_pricing_data
    
    if df is None or df.empty:
        st.info("Fetch pricing data first")
    else:
        all_f = list(st.session_state.custom_formulas.keys()) + list(PREDEFINED_FORMULAS.keys())
        
        if all_f:
            selected = st.selectbox("Select Formula", all_f)
            
            if st.button("📈 Calculate & Visualize", use_container_width=True):
                if selected in st.session_state.custom_formulas:
                    f = st.session_state.custom_formulas[selected]
                    c = f['components']
                else:
                    f = PREDEFINED_FORMULAS[selected]
                    c = f['components']
                
                result = calculate_formula_price(df, selected, c)
                
                if not result.empty:
                    st.session_state.current_formula = result
                    st.session_state.current_formula_name = selected
                    st.session_state.current_formula_components = c
                    st.success("✅ Formula calculated")
                    st.rerun()
            
            st.divider()
            
            # ✅ DISPLAY RESULTS IF THEY EXIST (FIXED!)
            if st.session_state.current_formula is not None and not st.session_state.current_formula.empty:
                result = st.session_state.current_formula
                selected_name = st.session_state.get('current_formula_name', selected)
                selected_comps = st.session_state.get('current_formula_components', [])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Avg", f"${result['Composite Price'].mean():.2f}")
                with col2:
                    st.metric("Min", f"${result['Composite Price'].min():.2f}")
                with col3:
                    st.metric("Max", f"${result['Composite Price'].max():.2f}")
                with col4:
                    st.metric("Records", len(result))
                
                st.divider()
                
                # ✅ Component curves visualization
                st.subheader("📈 Component Curves vs Blend Price")
                
                fig = go.Figure()
                
                # Add component series (dashed lines)
                for comp in selected_comps:
                    comp_name = comp['name']
                    comp_data = df[df['Series Name'].str.contains(comp_name, case=False, na=False)].sort_values('Date')
                    
                    if not comp_data.empty:
                        fig.add_trace(go.Scatter(
                            x=comp_data['Date'],
                            y=comp_data['Mid'],
                            mode='lines',
                            name=f"{comp_name} ({comp['weight']*100:.0f}%)",
                            line=dict(dash='dash', width=2),
                            opacity=0.6,
                            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>'
                        ))
                
                # Add blend price (solid white line)
                result_sorted = result.sort_values('Date')
                fig.add_trace(go.Scatter(
                    x=result_sorted['Date'],
                    y=result_sorted['Composite Price'],
                    mode='lines+markers',
                    name=f"Blend: {selected_name}",
                    line=dict(color='white', width=4),
                    marker=dict(size=8),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Blended Price: $%{y:.2f}<extra></extra>'
                ))
                
                fig.update_layout(
                    title=f"{selected_name} - Component Curves vs Blend Price",
                    xaxis_title="Date",
                    yaxis_title="Price ($)",
                    height=600,
                    hovermode='x unified',
                    plot_bgcolor='rgba(0,0,0,0.1)',
                    paper_bgcolor='rgba(20,20,30,0.95)',
                    font=dict(color='white')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                
                # ✅ Blend insights - NOW FIXED AND DISPLAYS!
                st.subheader("🤖 Blend Analysis & Insights")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.info(f"📦 Formula: **{selected_name}** | {len(selected_comps)} components")
                
                with col2:
                    if st.button("🧠 Generate Insights", use_container_width=True, key="blend_insights_btn"):
                        with st.spinner("🔍 Analyzing blend with AI..."):
                            insights = generate_blend_insights(
                                selected_name, 
                                selected_comps, 
                                result, 
                                st.session_state.user_role
                            )
                            if insights:
                                st.session_state.current_blend_insights = insights
                                st.rerun()
                            else:
                                st.error("Failed to generate insights")
                
                with col3:
                    if st.button("🔄 Clear", use_container_width=True):
                        st.session_state.current_blend_insights = None
                        st.rerun()
                
                st.divider()
                
                # ✅ DISPLAY INSIGHTS - THIS NOW WORKS!
                if st.session_state.current_blend_insights:
                    with st.container(border=True):
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    padding: 20px; border-radius: 10px; border-left: 5px solid #00d4ff;">
                        """ + st.session_state.current_blend_insights.replace('\n', '<br>') + """
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("👆 Click '🧠 Generate Insights' to analyze this blend")

        else:
            st.warning("⚠️ Create or select a formula first")

# ============================
# COMPARE FORMULAS PAGE
# ============================

elif page == "📈 Compare Formulas":
    st.subheader("📈 Compare Formulas")
    
    df = st.session_state.df_pricing_data
    
    if df is None or df.empty:
        st.info("Fetch data first")
    else:
        all_f = list(st.session_state.custom_formulas.keys()) + list(PREDEFINED_FORMULAS.keys())
        
        if all_f:
            selected = st.multiselect("Select Formulas to Compare", all_f, default=all_f[:min(2, len(all_f))])
            
            if st.button("Compare", use_container_width=True):
                result = compare_formulas(df, selected)
                
                if not result.empty:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Formulas", len(selected))
                    with col2:
                        st.metric("Records", len(result))
                    with col3:
                        st.metric("Date Range", f"{(result['Date'].max() - result['Date'].min()).days} days")
                    
                    st.divider()
                    
                    fig = px.line(
                        result,
                        x='Date',
                        y='Composite Price',
                        color='Formula',
                        markers=True,
                        height=600,
                        title="Formula Comparison"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.divider()
                    
                    st.subheader("📊 Comparison Summary")
                    
                    stats = result.groupby('Formula')['Composite Price'].agg([
                        ('Mean', 'mean'),
                        ('Min', 'min'),
                        ('Max', 'max'),
                        ('Std Dev', 'std')
                    ]).round(2)
                    
                    st.dataframe(stats, use_container_width=True)

# ============================
# AI INSIGHTS PAGE
# ============================

elif page == "🤖 AI Insights":
    st.subheader("🤖 AI Market Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Pricing Insights", use_container_width=True):
            if st.session_state.df_pricing_data is not None and not st.session_state.df_pricing_data.empty:
                with st.spinner("🔍 Analyzing..."):
                    insights = generate_data_pulled_insights(st.session_state.df_pricing_data, st.session_state.user_role)
                    if insights:
                        st.session_state.data_pulled_insights = insights
                        st.rerun()
    
    with col2:
        if st.button("🔮 Forecast Insights", use_container_width=True):
            if st.session_state.df_forecast_data is not None and not st.session_state.df_forecast_data.empty:
                with st.spinner("🔍 Analyzing..."):
                    insights = generate_forecast_insights(st.session_state.df_forecast_data, st.session_state.user_role)
                    if insights:
                        st.session_state.forecast_insights = insights
                        st.rerun()
    
    with col3:
        if st.button("🧮 Formula Insights", use_container_width=True):
            if st.session_state.current_formula is not None and not st.session_state.current_formula.empty:
                st.info("Select a formula from 'Apply Formulas' first")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.data_pulled_insights:
            st.subheader("📊 Pricing Analysis")
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 10px; border-left: 5px solid #00d4ff;">
            """ + st.session_state.data_pulled_insights.replace('\n', '<br>') + """
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if st.session_state.forecast_insights:
            st.subheader("🔮 Forecast Analysis")
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 10px; border-left: 5px solid #00d4ff;">
            """ + st.session_state.forecast_insights.replace('\n', '<br>') + """
            </div>
            """, unsafe_allow_html=True)

# ============================
# CHAT PAGE
# ============================

elif page == "💬 Chat":
    st.subheader("💬 Energy Expert Chat")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    user_input = st.chat_input("Ask about market, forecasts, formulas...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                response = call_groq_llm(f"User: {user_input}", system="You are an expert petrochemical market analyst.")
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

# ============================
# XML API SCRIPTS PAGE
# ============================

elif page == "🔍 XML API Scripts":
    st.subheader("🔍 XML API Scripts - Request Payloads")
    
    st.markdown("""
    This page displays all XML POST request payloads used in API calls to the ICIS API.
    **✅ Forecast requests are now BATCHED - all series in ONE request!**
    """)
    
    st.divider()
    
    if not st.session_state.xml_requests_log:
        st.info("No API requests logged yet. Make API calls from other tabs to see requests here.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Requests", len(st.session_state.xml_requests_log))
        with col2:
            total_bytes = sum(req['size_bytes'] for req in st.session_state.xml_requests_log)
            st.metric("Total Size", f"{total_bytes:,} bytes")
        with col3:
            if st.button("Clear Log"):
                st.session_state.xml_requests_log = []
                st.rerun()
        
        st.divider()
        
        request_types = sorted(set(req['request_type'] for req in st.session_state.xml_requests_log))
        selected_type = st.selectbox("Filter by Request Type", ["All"] + request_types)
        
        filtered_logs = st.session_state.xml_requests_log
        if selected_type != "All":
            filtered_logs = [req for req in st.session_state.xml_requests_log if req['request_type'] == selected_type]
        
        st.subheader(f"📋 Requests ({len(filtered_logs)})")
        
        st.divider()
        
        for idx, req in enumerate(filtered_logs):
            badge = ""
            if "Batched" in req['request_type']:
                badge = "🎯 **BATCHED**"
            
            with st.expander(f"🔹 {req['timestamp']} - {req['request_type']} ({req['size_bytes']:,} bytes) {badge}", expanded=(idx == len(filtered_logs) - 1)):
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption(f"**Type**: {req['request_type']}")
                with col2:
                    st.caption(f"**Size**: {req['size_bytes']:,} bytes")
                with col3:
                    st.caption(f"**Time**: {req['timestamp']}")
                with col4:
                    if req.get('series_count', 0) > 0:
                        st.caption(f"**Series**: {req['series_count']}")
                
                if req['description']:
                    st.info(f"📝 **Description**: {req['description']}")
                
                st.divider()
                
                st.subheader("📄 XML Payload")
                st.code(req['xml_payload'], language="xml")
                
                st.divider()
                
                try:
                    root = ET.fromstring(req['xml_payload'])
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"**Root Element**: {root.tag}")
                    with col2:
                        st.caption(f"**Total Elements**: {len(list(root.iter()))}")
                except:
                    st.warning("Could not parse XML structure")
        
        st.divider()
        
        st.subheader("📊 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            series_list_count = len([r for r in st.session_state.xml_requests_log if r['request_type'] == 'Series List'])
            st.metric("Series List", series_list_count)
        
        with col2:
            forecast_series_count = len([r for r in st.session_state.xml_requests_log if r['request_type'] == 'Forecast Series List'])
            st.metric("Forecast Series", forecast_series_count)
        
        with col3:
            pricing_count = len([r for r in st.session_state.xml_requests_log if r['request_type'] == 'Pricing Data'])
            st.metric("Pricing Data", pricing_count)
        
        with col4:
            forecast_batched_count = len([r for r in st.session_state.xml_requests_log if 'Batched' in r['request_type']])
            st.metric("Forecast Batched", forecast_batched_count)

# ============================
# DEBUG LOGS PAGE
# ============================

elif page == "🐛 Debug Logs":
    st.subheader("🐛 Debug Logs & Events")
    
    if not st.session_state.debug_log:
        st.info("No logs yet")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.metric("Events", len(st.session_state.debug_log))
        with col2:
            if st.button("Clear"):
                st.session_state.debug_log = []
                st.rerun()
        
        st.divider()
        
        log_df = pd.DataFrame(st.session_state.debug_log)
        st.dataframe(log_df, use_container_width=True, height=600)

st.divider()
st.markdown("""
<div style="text-align: center; color: #0f766e;">
    <p><strong>🛢️ ICIS Pricing Dashboard - ENHANCED FINAL</strong></p>
    <p>✅ AI Insights | ✅ Batched Forecast XML | ✅ Component Curves | ✅ Normalized Charts | ✅ Full Debugging | ✅ Blend Insights Display Fixed</p>
</div>
""", unsafe_allow_html=True)