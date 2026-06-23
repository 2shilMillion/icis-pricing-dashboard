import streamlit as st

st.set_page_config(
    page_title="Dashboard Tutorial",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# SESSION STATE
# ============================

if "current_slide" not in st.session_state:
    st.session_state.current_slide = 0

if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = set()

# ============================
# SLIDE CONTENT
# ============================

SLIDES = [
    {
        "title": "🛢️ ICIS Pricing Dashboard Tutorial",
        "sections": [
            ("Welcome", "Your complete solution for petrochemical market analysis!"),
            ("Features", "• Real-time market pricing data\n• AI-powered insights & forecasting\n• Custom formula blending\n• Multi-currency normalization"),
        ]
    },
    {
        "title": "🔐 Step 1: Authentication",
        "sections": [
            ("What to do", "Enter your ICIS API credentials in the sidebar"),
            ("Steps", "1. Input ICIS Username\n2. Input ICIS Password\n3. Select your user role (Trader, Producer, etc.)\n4. Credentials are used only for API calls"),
            ("⚠️ Important", "Never share your credentials. They're sent securely to ICIS API only."),
        ]
    },
    {
        "title": "📊 Step 2: Dashboard Overview",
        "sections": [
            ("Dashboard Metrics", "• Real Series - Number of pricing series selected\n• Forecast Series - Number of forecast series selected\n• Formulas - Custom blends you've created\n• Debug Events - API calls and system events logged"),
        ]
    },
    {
        "title": "🔍 Step 3: Real Series Selection",
        "sections": [
            ("How it works", "Select pricing series from available petrochemical publications"),
            ("Steps", "1. Click '🔄 Load Series' to fetch available series\n2. Select a publication from the dropdown\n3. Choose multiple series using multiselect\n4. Set date range (start and end dates)\n5. Click '📊 Fetch Pricing Data' to retrieve historical prices"),
            ("Key Points", "✅ Supports multi-select for comparing multiple products\n✅ Historical data typically available back 90+ days\n✅ Data normalized across different locations and currencies"),
        ]
    },
    {
        "title": "🔮 Step 4: Forecast Series (BATCHED)",
        "sections": [
            ("What it is", "Get forward-looking price forecasts using BATCHED XML requests"),
            ("Features", "📋 Multi-Publication - Browse forecasts across different ICIS publications\n🎯 Batch Request - All series fetched in ONE efficient request\n📊 Multi-Series - Compare forecasts across different products\n🔍 Debug View - See XML requests in Debug Logs tab"),
            ("Key Points", "✅ Forecasts typically available 1-2 years ahead\n✅ More efficient than individual requests\n✅ All forecasts normalized to same currency"),
        ]
    },
    {
        "title": "📈 Step 5: Pricing Data Analysis",
        "sections": [
            ("Features", "📊 Data Table - Browse all retrieved price records\n🤖 AI Analysis - Auto-generated insights when data loaded\n📈 Trend Charts - Visualize price movements over time"),
            ("What you see", "✅ Shows Low/High/Mid prices\n✅ Original currency and units displayed\n✅ AI provides market analysis"),
        ]
    },
    {
        "title": "📊 Step 6: Forecast Data Analysis",
        "sections": [
            ("Features", "🔮 Forecast Trends - Multi-series comparison charts\n💱 Currency Normalization - Convert all prices to target currency\n📊 Statistics - Mean, Min, Max, Std Dev by series\n🤖 AI Insights - Forward-looking market analysis"),
            ("Key Points", "✅ See where market is heading\n✅ Compare multiple products side-by-side\n✅ Identify volatility and risk"),
        ]
    },
    {
        "title": "💱 Step 7: Normalization",
        "sections": [
            ("What it does", "Normalize prices to consistent currency and units for fair comparison"),
            ("Steps", "1. Select target currency (USD, EUR, GBP, JPY, etc.)\n2. Select target unit (kg, mt, lb, gallon, etc.)\n3. Click '🔄 Normalize' to convert all prices\n4. Charts display normalized prices automatically"),
            ("Key Points", "✅ Real FX rates from external API\n✅ Handles any unit conversion\n✅ Original values preserved for reference"),
        ]
    },
    {
        "title": "🎯 Step 8: Price Drivers Analysis",
        "sections": [
            ("5 Key Drivers", "🛢️ Crude Oil - 40% weight, 0.85 correlation (Primary feedstock)\n⚡ Natural Gas - 25% weight, 0.70 correlation (Energy cost)\n💵 USD Strength - 15% weight, -0.60 correlation (Currency impact)\n🌍 Global Demand - 12% weight, 0.75 correlation (Economic activity)\n⛔ Supply Disruption - 8% weight, 0.95 correlation (Production issues)"),
            ("Why it matters", "✅ Weights sum to 100%\n✅ Correlations show historical relationships\n✅ Used in scenario analysis"),
        ]
    },
    {
        "title": "📈 Step 9: Scenario Analysis",
        "sections": [
            ("What it does", "Test 'what-if' scenarios to see price impact"),
            ("Steps", "1. Adjust sliders for each price driver\n2. Crude Oil: -20% to +20%\n3. Natural Gas: -20% to +20%\n4. USD Strength: -10% to +10%\n5. Global Demand: -20% to +20%\n6. Click 'Run Scenario' to calculate impacts\n7. See resulting price change"),
            ("Use cases", "✅ Identify upside/downside risks\n✅ Useful for hedging decisions\n✅ Stress test your positions"),
        ]
    },
    {
        "title": "🔮 Step 10: ML Forecasting",
        "sections": [
            ("Features", "📊 Linear Regression - Identifies price trends\n📉 Confidence Bands - Shows forecast uncertainty\n⬆️⬇️ Trend Detection - Up or Down arrows\n🔢 Multiple Series - Forecast each product separately"),
            ("How to use", "1. Set forecast horizon (7-90 days)\n2. Click 'Generate Forecasts'\n3. View historical data + forecast with confidence bands\n4. Trend shown with % change indicator"),
        ]
    },
    {
        "title": "🧮 Step 11: Formula Builder",
        "sections": [
            ("What it does", "Create custom product blends from component series"),
            ("Steps", "1. Enter formula name (e.g., 'My Custom Blend')\n2. Select number of components (2-6)\n3. For each component: Choose series + set weight %\n4. Weights must sum to 100%\n5. Click 'Create Formula' to save"),
            ("Predefined", "✅ PE (Polyethylene)\n✅ PP (Polypropylene)\n✅ PO (Propylene Oxide)\n✅ PET (Polyethylene Terephthalate)"),
        ]
    },
    {
        "title": "📊 Step 12: Apply Formulas",
        "sections": [
            ("Features", "📈 Component Curves - Dashed lines show each component\n🧬 Blend Price - White solid line shows weighted blend\n📊 Component Visualization - Hover to see individual prices\n🤖 Blend Insights - AI analysis of formula performance"),
            ("Steps", "1. Select a formula from dropdown\n2. Click '📈 Calculate & Visualize'\n3. Review avg/min/max/volatility metrics\n4. Analyze component curves vs blend price\n5. Click '🧠 Generate Insights' for AI analysis"),
        ]
    },
    {
        "title": "📈 Step 13: Compare Formulas",
        "sections": [
            ("What it does", "Compare multiple blends side-by-side"),
            ("Steps", "1. Select multiple formulas in multiselect\n2. Click 'Compare' button\n3. View price trends for all formulas together\n4. See comparison statistics table\n5. Identify best-performing blend"),
            ("Benefits", "✅ Compare up to 10+ formulas at once\n✅ Line colors help distinguish formulas\n✅ Statistics show Mean/Min/Max/Std Dev"),
        ]
    },
    {
        "title": "🤖 Step 14: AI Insights",
        "sections": [
            ("Role-Based Analysis", "🔍 General Analyst - Market overview and trends\n💼 Trader - Entry/exit points and volatility\n🏭 Producer - Cost analysis and margin impact\n📦 Supplier - Competitive positioning\n⚠️ Risk Manager - Hedging strategies and VaR"),
            ("Key Features", "✅ Role-specific language and recommendations\n✅ Powered by Groq LLM API\n✅ Generated from real market data\n✅ Appears automatically when data loaded"),
        ]
    },
    {
        "title": "💬 Step 15: Smart Chat",
        "sections": [
            ("What you can ask", "• What's driving propylene prices higher?\n• How would a crude oil spike affect my blend?\n• Which component has highest volatility?\n• What's the outlook for Q2?\n• How should I hedge this position?"),
            ("How it works", "✅ Chat history preserved in session\n✅ Context-aware responses\n✅ Petrochemical market expertise\n✅ Powered by Groq LLM"),
        ]
    },
    {
        "title": "🔍 Step 16: XML API Scripts & Debugging",
        "sections": [
            ("What's shown", "📋 XML Requests Log - See all API payloads\n📊 Request Statistics - Count and size of requests\n🎯 Batched Requests - Verify multi-series batching\n⏰ Timestamps - Track when requests were made\n🐛 Debug Events - System logs and errors"),
            ("Useful for", "✅ See how API calls are made\n✅ Verify batched requests are working\n✅ Troubleshoot API issues\n✅ Learn ICIS API format"),
        ]
    },
    {
        "title": "⭐ Pro Tips & Best Practices",
        "sections": [
            ("Pro Tips", "🎯 Start Small - Fetch 2-3 series first, then expand\n💱 Always Normalize - Makes apples-to-apples comparison\n🔮 Use Forecasts - Plan hedges based on outlook\n📊 Bookmark Slides - Save important tutorial pages\n🤖 Review AI Insights - They're based on real data\n📈 Track Formulas - Monitor blend prices over time\n⏰ Set Alerts - Check forecasts weekly\n🔐 Secure Credentials - Use environment variables"),
        ]
    },
    {
        "title": "❓ FAQ & Common Questions",
        "sections": [
            ("Q&A", "❓ How often is data updated?\n✅ Real-time from ICIS API\n\n❓ Can I export data?\n✅ Yes, download CSVs from data tables\n\n❓ How far back is historical data?\n✅ Typically 90+ days\n\n❓ Can I create unlimited formulas?\n✅ Yes, no limit\n\n❓ What if API fails?\n✅ Check credentials or XML in Debug tab\n\n❓ How accurate are forecasts?\n✅ Based on historical trends + ML\n\n❓ Can I use multiple currencies?\n✅ Yes, normalize to any currency"),
        ]
    },
    {
        "title": "🎉 You're Ready!",
        "sections": [
            ("Next Steps", "👉 Go to **📊 Dashboard** tab to start\n👉 Authenticate with your ICIS credentials\n👉 Select pricing and forecast series\n👉 Explore AI insights and create formulas\n👉 Use chat to ask questions\n👉 Review XML and debug logs as needed"),
            ("Remember", "✅ Bookmark tutorial for later reference\n✅ Check Debug Logs if something doesn't work\n✅ Use Chat for market questions\n✅ Formulas are saved in session state"),
        ]
    }
]

# ============================
# UI
# ============================

st.title("📚 Dashboard Tutorial")
st.write("Learn how to use every feature of the ICIS Pricing Dashboard")

# ============================
# NAVIGATION
# ============================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("⏮️ Start", use_container_width=True):
        st.session_state.current_slide = 0
        st.rerun()

with col2:
    if st.button("⬅️ Previous", use_container_width=True):
        st.session_state.current_slide = max(0, st.session_state.current_slide - 1)
        st.rerun()

with col3:
    slide_select = st.selectbox(
        "Jump to Slide",
        range(len(SLIDES)),
        index=st.session_state.current_slide,
        format_func=lambda x: f"{x+1}. {SLIDES[x]['title'][:35]}..."
    )
    if slide_select != st.session_state.current_slide:
        st.session_state.current_slide = slide_select
        st.rerun()

with col4:
    if st.button("➡️ Next", use_container_width=True):
        st.session_state.current_slide = min(len(SLIDES)-1, st.session_state.current_slide + 1)
        st.rerun()

with col5:
    if st.button("⏭️ End", use_container_width=True):
        st.session_state.current_slide = len(SLIDES) - 1
        st.rerun()

# ============================
# PROGRESS BAR
# ============================

progress = (st.session_state.current_slide + 1) / len(SLIDES)
st.progress(progress, text=f"Slide {st.session_state.current_slide + 1} of {len(SLIDES)}")

st.divider()

# ============================
# CURRENT SLIDE
# ============================

slide = SLIDES[st.session_state.current_slide]

# Title with bookmark
col1, col2 = st.columns([0.95, 0.05])
with col1:
    st.markdown(f"## {slide['title']}")
with col2:
    if st.button("⭐", key=f"bookmark_{st.session_state.current_slide}"):
        if st.session_state.current_slide in st.session_state.bookmarks:
            st.session_state.bookmarks.remove(st.session_state.current_slide)
        else:
            st.session_state.bookmarks.add(st.session_state.current_slide)
        st.rerun()

# Sections
for section_title, section_content in slide["sections"]:
    with st.expander(f"📌 {section_title}", expanded=True):
        st.write(section_content)

st.divider()

# ============================
# BOOKMARKS
# ============================

if st.session_state.bookmarks:
    st.subheader("⭐ Your Bookmarks")
    
    bookmark_list = sorted(list(st.session_state.bookmarks))
    cols = st.columns(min(3, len(bookmark_list)))
    
    for idx, slide_num in enumerate(bookmark_list):
        with cols[idx % len(cols)]:
            if st.button(
                f"📌 {SLIDES[slide_num]['title'][:25]}...",
                use_container_width=True,
                key=f"jump_{slide_num}"
            ):
                st.session_state.current_slide = slide_num
                st.rerun()

st.divider()

# Footer
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"Total Slides: {len(SLIDES)}")
with col2:
    st.caption(f"Current: Slide {st.session_state.current_slide + 1}")
with col3:
    st.caption(f"Bookmarked: {len(st.session_state.bookmarks)}")