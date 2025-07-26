import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

df = pd.read_csv("..\dashboard_base_k5.csv")

st.set_page_config(layout="wide")
st.title("Subscriber Profiling for Term Deposits")

cluster_labels = {
    0: "0. Young, Educated Singles",
    1: "1. Older Married Retirees",
    2: "2. Blue-Collar Loan Holders",
    3: "3. Educated Married Professionals",
    4: "4. Financially Struggling Divorced"
}

st.markdown("### Select Cluster(s)")
selected_labels = st.multiselect(
    label="",
    options=list(cluster_labels.values()),
    default=list(cluster_labels.values()),  # All selected by default
    label_visibility="collapsed"
)

selected_clusters = [k for k, v in cluster_labels.items() if v in selected_labels]

df_cluster = df[df["cluster_k5"].isin(selected_clusters)]

# 1st Row: Gauge Charts
col1, col2, col3 = st.columns(3)

overall_avg_balance = df["balance"].mean()  # Mean over all subscribers

with col1:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=df_cluster["balance"].mean(),
        number={'suffix': " €"},
        title={'text': "Average Balance"},
        gauge={
            'axis': {'range': [0, 2500]},
            'bar': {'color': "crimson"},
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': overall_avg_balance},
            }
    ))
    st.plotly_chart(fig, use_container_width=True)

overall_age_balance = df["age"].mean()  # Mean over all subscribers

with col2:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=df_cluster["age"].mean(),
        title={'text': "Average Age"},
        gauge={
            'axis': {'range': [30, 60]},
            'bar': {'color': "green"},
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': overall_age_balance},
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

with col3:
    edu_order = {"primary": 0, "secondary": 1, "tertiary": 2}

    edu_mode = df_cluster["education"].mode().values[0]
    edu_value = edu_order.get(edu_mode.lower(), 1)

    # Reference (all subscribers)
    overall_education_mode = df["education"].mode().values[0]
    overall_education_value = edu_order.get(overall_education_mode.lower(), 1)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=edu_value,
        title={'text': "Avg Education Level"},
        gauge={
            'axis': {'range': [0, 2], 'tickvals': [0, 1, 2], 'ticktext': ['Primary', 'Secondary', 'Tertiary']},
            'bar': {'color': "steelblue"},
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': overall_education_value
            },
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# 2nd Row: Job & Marital charts side-by-side
col4, col5 = st.columns(2)

with col4:
    st.subheader("Type of Job")

    job_counts_all = df['job'].value_counts()
    job_counts_cluster = df_cluster['job'].value_counts()
    job_df = pd.DataFrame({
        'Total Subscribers': job_counts_all,
        'Cluster Subscribers': job_counts_cluster
    }).fillna(0)

    job_df = job_df.sort_values(by='Total Subscribers', ascending=False)

    fig_job = go.Figure()
    fig_job.add_trace(go.Bar(
        x=job_df.index,
        y=job_df['Cluster Subscribers'],
        name='Subscribers in Cluster',
        marker_color='gold'
    ))
    fig_job.add_trace(go.Scatter(
        x=job_df.index,
        y=job_df['Total Subscribers'],
        name='Total Subscribers',
        mode='lines+markers+text',
        text=job_df['Total Subscribers'].astype(int),
        textposition='top center',
        line=dict(color='royalblue', width=2)
    ))

    fig_job.update_layout(
        barmode='group',
        xaxis_tickangle=-45,
        height=400,
        legend=dict(x=0.8, y=1.1)
    )
    st.plotly_chart(fig_job, use_container_width=True)

with col5:
    st.subheader("Marital Status")

    marital_counts_all = df['marital'].value_counts()
    marital_counts_cluster = df_cluster['marital'].value_counts()
    marital_df = pd.DataFrame({
        'Total Subscribers': marital_counts_all,
        'Cluster Subscribers': marital_counts_cluster
    }).fillna(0)

    marital_df = marital_df.sort_values(by='Total Subscribers', ascending=False)

    fig_marital = go.Figure()
    fig_marital.add_trace(go.Bar(
        x=marital_df.index,
        y=marital_df['Cluster Subscribers'],
        name='Subscribers in Cluster',
        marker_color='gold'
    ))
    fig_marital.add_trace(go.Scatter(
        x=marital_df.index,
        y=marital_df['Total Subscribers'],
        name='Total Subscribers',
        mode='lines+markers+text',
        text=marital_df['Total Subscribers'].astype(int),
        textposition='top center',
        line=dict(color='royalblue', width=2)
    ))

    fig_marital.update_layout(
        barmode='group',
        height=400,
        legend=dict(x=0.85, y=1.2)
    )
    st.plotly_chart(fig_marital, use_container_width=True)

# 3rd Row: Pie charts
col6, col7, col8 = st.columns(3)
with col6:
    st.subheader("Has credit in default?")
    default_data = df_cluster["has_default"].value_counts(normalize=True).mul(100).reset_index()
    default_data.columns = ["Default", "Percentage"]
    fig_default = px.pie(default_data, values="Percentage", names="Default", hole=0.4)
    st.plotly_chart(fig_default, use_container_width=True)

with col7:
    st.subheader("Has a personal loan?")
    loan_data = df_cluster["has_loan"].value_counts(normalize=True).mul(100).reset_index()
    loan_data.columns = ["Loan", "Percentage"]
    fig_loan = px.pie(loan_data, values="Percentage", names="Loan", hole=0.4)
    st.plotly_chart(fig_loan, use_container_width=True)

with col8:
    st.subheader("Has a housing loan?")
    housing_data = df_cluster["has_housing"].value_counts(normalize=True).mul(100).reset_index()
    housing_data.columns = ["Housing", "Percentage"]
    fig_housing = px.pie(housing_data, values="Percentage", names="Housing", hole=0.4)
    st.plotly_chart(fig_housing, use_container_width=True)
