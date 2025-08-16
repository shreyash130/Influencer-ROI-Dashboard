import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO
import os

st.set_page_config(page_title="Influencer ROI Dashboard", layout="wide")

# Vercel-specific configurations
try:
    # Try to get the port from environment variable (for Vercel)
    port = int(os.environ.get("PORT", 8501))
except:
    port = 8501

# 1. ---- FILE UPLOADS ----
st.sidebar.header("Upload Your CSV Files")
inf_file = st.sidebar.file_uploader("Influencers", type=["csv"])
post_file = st.sidebar.file_uploader("Posts", type=["csv"])
trk_file  = st.sidebar.file_uploader("Tracking Data", type=["csv"])
payout_file = st.sidebar.file_uploader("Payouts", type=["csv"])

# 2. ---- MAIN LOGIC IF DATA PROVIDED ----
# Check if running on Vercel (or in demo mode) and load sample data if no files are uploaded
if inf_file and post_file and trk_file and payout_file:
    influencers = pd.read_csv(inf_file)
    posts = pd.read_csv(post_file)
    tracking = pd.read_csv(trk_file)
    payouts = pd.read_csv(payout_file)
else:
    # Load sample data for demo purposes (when deployed on Vercel or no files uploaded)
    st.info("No files uploaded. Loading sample data for demonstration.")
    st.info("In a production environment, please upload your own CSV files using the sidebar.")
    
    # Check if sample files exist in the current directory
    sample_files_exist = all([
        os.path.exists("influencers.csv"),
        os.path.exists("posts.csv"),
        os.path.exists("tracking_data.csv"),
        os.path.exists("payouts.csv")
    ])
    
    if sample_files_exist:
        influencers = pd.read_csv("influencers.csv")
        posts = pd.read_csv("posts.csv")
        tracking = pd.read_csv("tracking_data.csv")
        payouts = pd.read_csv("payouts.csv")
    else:
        # Create minimal sample data if files don't exist
        st.warning("Sample files not found. Creating minimal demo data.")
        influencers = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'name': ['AlexFit', 'VitaG', 'RishiRun', 'SabaLife'],
            'category': ['Fitness', 'Wellness', 'Fitness', 'Wellness'],
            'gender': ['M', 'F', 'M', 'F'],
            'followers': [120000, 95000, 66000, 180000],
            'platform': ['Instagram', 'YouTube', 'Twitter', 'Instagram']
        })
        
        posts = pd.DataFrame({
            'influencer_id': [1, 2, 3, 4],
            'platform': ['Instagram', 'YouTube', 'Twitter', 'Instagram'],
            'date': ['2025-06-01', '2025-06-02', '2025-06-03', '2025-06-04'],
            'url': ['url1', 'url2', 'url3', 'url4'],
            'caption': ['Try MB Power!', 'HKVitals review', 'Training Gritzo', 'Morning Wellness'],
            'reach': [30000, 18000, 9500, 42000],
            'likes': [1500, 500, 310, 2100],
            'comments': [130, 50, 17, 220]
        })
        
        tracking = pd.DataFrame({
            'source': ['Instagram', 'YouTube', 'Twitter', 'Instagram'],
            'campaign': ['SummerFit', 'HKLaunch', 'RunGritzo', 'WellnessBlast'],
            'influencer_id': [1, 2, 3, 4],
            'user_id': ['u122', 'u293', 'u456', 'u998'],
            'product': ['MB Protein', 'HKVitals', 'Gritzo', 'HKVitals'],
            'date': ['2025-06-01', '2025-06-02', '2025-06-03', '2025-06-04'],
            'orders': [10, 7, 2, 15],
            'revenue': [2500, 2000, 380, 3400]
        })
        
        payouts = pd.DataFrame({
            'influencer_id': [1, 2, 3, 4],
            'basis': ['post', 'post', 'order', 'post'],
            'rate': [5000, 4500, 180, 7000],
            'orders': [1, 1, 2, 1],
            'total_payout': [5000, 4500, 360, 7000]
        })

# Continue with the rest of the logic using the loaded data (either uploaded or sample)
# Optional: Add missing 'brand' column if not present
if "brand" not in tracking.columns:
    tracking["brand"] = tracking["product"].apply(lambda p: "MuscleBlaze" if "MB" in str(p) else ("HKVitals" if "HK" in str(p) else "Gritzo"))

# ----- MERGE AND PREP -----
merged = (
    tracking
    .merge(influencers, left_on='influencer_id', right_on='id', how='left')
    .merge(payouts, on='influencer_id', how='left', suffixes=('', '_payout'))
)
# If category is missing, fill with 'Unknown'
if 'category' not in merged.columns:
    merged['category'] = 'Unknown'
if 'gender' not in merged.columns:
    merged['gender'] = 'Unknown'

# 3. ---- FILTERS ----
st.sidebar.header("Filters")
brand_list = merged['brand'].dropna().unique().tolist()
product_list = merged['product'].dropna().unique().tolist()
platform_list = merged['platform'].dropna().unique().tolist()
cat_list = merged['category'].dropna().unique().tolist()
gender_list = merged['gender'].dropna().unique().tolist()

filt_brand = st.sidebar.multiselect("Brand", brand_list, default=brand_list)
filt_product = st.sidebar.multiselect("Product", product_list, default=product_list)
filt_platform = st.sidebar.multiselect("Platform", platform_list, default=platform_list)
filt_cat = st.sidebar.multiselect("Persona/Category", cat_list, default=cat_list)
filt_gender = st.sidebar.multiselect("Gender", gender_list, default=gender_list)
minfol, maxfol = int(influencers['followers'].min()), int(influencers['followers'].max())
foll_range = st.sidebar.slider("Follower Count", minfol, maxfol, (minfol, maxfol))

filtered = merged[
    (merged['brand'].isin(filt_brand)) &
    (merged['product'].isin(filt_product)) &
    (merged['platform'].isin(filt_platform)) &
    (merged['category'].isin(filt_cat)) &
    (merged['gender'].isin(filt_gender)) &
    (merged['followers'].between(foll_range[0], foll_range[1]))
].copy()

# ---- ROI & INCREMENTAL ROAS ----
filtered['ROAS'] = filtered['revenue'] / filtered['total_payout']
baseline = st.sidebar.number_input("Baseline Revenue (for incremental ROAS)", min_value=0, value=0)
filtered['incremental_ROAS'] = (filtered['revenue'] - baseline) / filtered['total_payout']

# 4. ---- DASHBOARD MAIN ----
st.title("Influencer Campaign ROI Dashboard")

## Summary KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"₹{int(filtered['revenue'].sum())}")
col2.metric("Total Payout", f"₹{int(filtered['total_payout'].sum())}")
col3.metric("Overall ROAS", f"{filtered['revenue'].sum()/filtered['total_payout'].sum():.2f}" if filtered['total_payout'].sum() else "-")
col4.metric("Incremental ROAS", f"{((filtered['revenue'].sum()-baseline)/filtered['total_payout'].sum()):.2f}" if filtered['total_payout'].sum() else "-")

# ---- Colorful Plotly Bar Chart ----
st.subheader("Revenue and Payout by Influencer")
bar_data = filtered.groupby('name').agg({'revenue':'sum','total_payout':'sum'}).reset_index()
fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(x=bar_data['name'], y=bar_data['revenue'], name='Revenue', marker_color='deepskyblue'))
fig_bar.add_trace(go.Bar(x=bar_data['name'], y=bar_data['total_payout'], name='Payout', marker_color='salmon'))
fig_bar.update_layout(barmode='group', xaxis_title="Influencer", yaxis_title="₹ Amount")
st.plotly_chart(fig_bar, use_container_width=True)

# ---- Post performance ----
st.subheader("Post Engagement (by Influencer and Platform)")
post_stats = posts.groupby(['influencer_id','platform']).agg(
    total_reach=pd.NamedAgg(column='reach', aggfunc='sum'),
    avg_likes=pd.NamedAgg(column='likes', aggfunc='mean'),
    avg_comments=pd.NamedAgg(column='comments', aggfunc='mean'),
    post_count=pd.NamedAgg(column='url', aggfunc='count')
).reset_index()
post_stats = post_stats.merge(influencers[['id','name']], left_on='influencer_id', right_on='id', how='left')
st.dataframe(post_stats[['name','platform','post_count','total_reach','avg_likes','avg_comments']])

# ---- Leaderboard & Insights ----
st.subheader("Top Influencers")
top_inf = filtered.groupby(['influencer_id','name','category']).agg(
    total_rev=pd.NamedAgg(column='revenue', aggfunc='sum'),
    payout_sum=pd.NamedAgg(column='total_payout', aggfunc='sum'),
    orders_sum=pd.NamedAgg(column='orders', aggfunc='sum'),
    roas=pd.NamedAgg(column='ROAS', aggfunc='mean'),
    incr_roas=pd.NamedAgg(column='incremental_ROAS', aggfunc='mean')
).sort_values('roas', ascending=False).reset_index()
st.dataframe(top_inf[['name','category','total_rev','payout_sum','orders_sum','roas','incr_roas']].head(10))

st.subheader("Best Personas (Category avg ROAS)")
persona_stats = filtered.groupby("category")['ROAS'].mean().sort_values(ascending=False)
st.dataframe(persona_stats)
st.subheader("Poor ROIs (lowest incremental ROAS)")
poor_roi = filtered.sort_values('incremental_ROAS').head(5)
st.dataframe(poor_roi[['name','brand','platform','product','incremental_ROAS','revenue','total_payout']])

# ---- Campaign/Influencer Table ----
st.subheader("Detailed Campaign Table")
st.dataframe(filtered[['brand','campaign','name','platform','product','orders','revenue','total_payout','ROAS','incremental_ROAS']])

# ---- Export to CSV ----
st.download_button('Export Filtered Data as CSV', filtered.to_csv(index=False), file_name='filtered_data.csv')

# ---- PDF Export (chart+table) ----
def export_pdf(dataframe, persona_stats, top_inf):
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        # Main bar chart
        fig, ax = plt.subplots(figsize=(8,5))
        names = dataframe['name']
        rev = dataframe['revenue']
        payout = dataframe['total_payout']
        ax.bar(names, rev, label='Revenue', color='deepskyblue')
        ax.bar(names, payout, label='Payout', color='salmon', alpha=0.7)
        ax.set_title('Revenue vs Payout by Influencer')
        ax.legend()
        plt.xticks(rotation=45, ha='right')
        pdf.savefig(fig)
        plt.close(fig)

        # Campaign table
        fig, ax = plt.subplots(figsize=(10,6))
        ax.axis('off')
        tbl = ax.table(
            cellText=dataframe[['brand','campaign','name','platform','product','orders','revenue','total_payout','ROAS','incremental_ROAS']].values,
            colLabels=['Brand','Campaign','Name','Platform','Product','Orders','Revenue','Payout','ROAS','Inc.ROAS'],
            loc='center'
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1.1, 1.1)
        pdf.savefig(fig)
        plt.close(fig)

        # Persona Table
        fig, ax = plt.subplots()
        ax.axis('off')
        tbl = ax.table(cellText=[(k, f"{v:.2f}") for k, v in persona_stats.items()],
                    colLabels=['Persona','Avg ROAS'])
        pdf.savefig(fig)
        plt.close(fig)

        # Top influencer
        fig, ax = plt.subplots()
        ax.axis('off')
        tbl = ax.table(
            cellText=top_inf[['name','category','total_rev','payout_sum','orders_sum','roas','incr_roas']].round(2).values,
            colLabels=['Name','Category','Revenue','Payout','Orders','ROAS','Inc.ROAS'])
        pdf.savefig(fig)
        plt.close(fig)

    buf.seek(0)
    return buf

pdf_data = export_pdf(filtered, persona_stats, top_inf)
st.download_button("Export Dashboard as PDF", pdf_data, file_name="influencer_dashboard.pdf", mime="application/pdf")