import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

df = pd.read_csv("dashboard_base_k5.csv")

# Sidebar for cluster selection
cluster = st.sidebar.selectbox("Select Cluster", sorted(df["cluster_k5"].unique()))
cluster_df = df[df["cluster_k5"] == cluster]

st.title("Subscriber Profiling for Term Deposits")

# Top Continuous variables
col1, col2, col3 = st.columns(3)
col1.metric("Average Balance", f"{int(cluster_df['balance'].mean()):,} €")
col2.metric("Average Age", f"{int(cluster_df['age'].mean())}")
col3.metric("Avg Education Level", cluster_df["education"].mode()[0])

# Type of Job Chart
job_counts = cluster_df["job"].value_counts().reset_index()
job_counts.columns = ["job", "subscribers_in_cluster"]

fig_job = px.bar(job_counts, x="job", y="subscribers_in_cluster", text="subscribers_in_cluster")
fig_job.update_traces(textposition="outside")
fig_job.update_layout(title="Type of Job", xaxis_title="", yaxis_title="Subscribers")

# Marital Status Chart
marital_cluster = cluster_df["marital"].value_counts().reset_index()
marital_cluster.columns = ["marital", "subscribers_in_cluster"]
marital_total = df["marital"].value_counts().reset_index()
marital_total.columns = ["marital", "total_marital_count"]
marital_df = pd.merge(marital_total, marital_cluster, on="marital", how="left").fillna(0)

fig_marital = go.Figure()
fig_marital.add_bar(x=marital_df["marital"], y=marital_df["subscribers_in_cluster"], name="In Cluster")
fig_marital.add_trace(go.Scatter(x=marital_df["marital"], y=marital_df["total_marital_count"],
                                 mode="lines+markers+text", text=marital_df["total_marital_count"].astype(int),
                                 textposition="top center", name="Total"))

fig_marital.update_layout(title="Marital Status", yaxis_title="Count")

# Display charts
col4, col5 = st.columns(2)
col4.plotly_chart(fig_job, use_container_width=True)
col5.plotly_chart(fig_marital, use_container_width=True)

# Donut Charts
def donut_chart(column, label_yes="Yes", label_no="No", title=""):
    values = cluster_df[column].value_counts(normalize=True)
    labels = [label_no, label_yes] if True in values.index else [label_yes, label_no]
    percentages = [round(values.get(False, 0) * 100, 1), round(values.get(True, 0) * 100, 1)]

    fig = go.Figure(data=[go.Pie(labels=labels, values=percentages, hole=.6, textinfo='label+percent')])
    fig.update_layout(title=title)
    return fig

col6, col7, col8 = st.columns(3)
col6.plotly_chart(donut_chart("has_default", title="Has credit in default?"), use_container_width=True)
col7.plotly_chart(donut_chart("has_loan", title="Has a personal loan?"), use_container_width=True)
col8.plotly_chart(donut_chart("has_housing", title="Has a housing loan?"), use_container_width=True)
