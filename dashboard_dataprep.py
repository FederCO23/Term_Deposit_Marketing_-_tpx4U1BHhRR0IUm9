# %% [markdown]
# This notebook is a helper to prepare the data for the dashboard construction

# %% [markdown]
# ----

# %%
import duckdb
import pandas

# %%
# Load directly into DuckDB from CSV
con = duckdb.connect()
con.execute("""
    CREATE OR REPLACE TABLE term_deposit AS
    SELECT * FROM read_csv_auto('term-deposit-marketing.csv', header=True)
""")

# %%
# Filter the pre-call features for client segmentation and the subscribers (y=1)
con.execute("""
    CREATE OR REPLACE VIEW term_deposit_clean AS
    SELECT
        age,
        job,
        marital,
        education,
        "default" AS has_default,
        balance,
        housing AS has_housing,
        loan AS has_loan,
        y AS target
    FROM term_deposit
    WHERE target = True;
""")

# %%
con.execute("""
    SELECT
    COUNT(*)
    FROM term_deposit_clean;
""").fetchdf()

# %%
# Check the first few rows
con.execute("SELECT * FROM term_deposit_clean LIMIT 10").fetchdf()


# %%
mean_age, std_age, mean_balance, std_balance = con.execute("""
    SELECT
       AVG(age) AS mean_age,
       STDDEV_SAMP(age) AS std_age,
       AVG(LOG(ABS(balance) + 1)) AS mean_balance,
       STDDEV_SAMP(LOG(ABS(balance) + 1)) AS std_balance
    FROM term_deposit_clean
""").fetchone()


# %%
con.execute(f"""
CREATE OR REPLACE VIEW term_deposit_clean_encoded AS
SELECT

    -- Pre-call original columns
    age,
    job,
    marital,
    education,
    has_default,
    balance,
    has_housing,
    has_loan,

    -- Standardize age manually
    (age - {mean_age}) / {std_age} AS age_t,

    -- Log-transform + standardize balance
    SIGN(balance) AS balance_sign,
    (LOG(ABS(balance) + 1) - {mean_balance}) / {std_balance} AS balance_t,

    -- One-hot encode job
    (job = 'admin.')::INT AS job_admin,
    (job = 'blue-collar')::INT AS job_bluecollar,
    (job = 'technician')::INT AS job_technician,
    (job = 'services')::INT AS job_services,
    (job = 'management')::INT AS job_management,
    (job = 'retired')::INT AS job_retired,
    (job = 'self-employed')::INT AS job_selfemployed,
    (job = 'entrepreneur')::INT AS job_entrepreneur,
    (job = 'unemployed')::INT AS job_unemployed,
    (job = 'housemaid')::INT AS job_housemaid,
    (job = 'student')::INT AS job_student,
    (job = 'unknown')::INT AS job_unknown,

    -- One-hot encode marital
    (marital = 'married')::INT AS marital_married,
    (marital = 'single')::INT AS marital_single,
    (marital = 'divorced')::INT AS marital_divorced,
    (marital = 'unknown')::INT AS marital_unknown,

    -- Ordinal encode education
    CASE 
        WHEN education = 'unknown' THEN -1
        WHEN education = 'primary' THEN 0
        WHEN education = 'secondary' THEN 1
        WHEN education = 'tertiary' THEN 2
    END AS education_ord,

    -- Binary encode default, housing, loan
    (has_default = 'yes')::INT AS default_bin,
    (has_housing = 'yes')::INT AS housing_bin,
    (has_loan = 'yes')::INT AS loan_bin,

    -- Binary encode target
    (target = 'yes')::INT AS target_bin

FROM term_deposit_clean
""")

# %%
con.execute("SELECT * FROM term_deposit_clean_encoded LIMIT 10").fetchdf()

# %%
df_base = con.execute("SELECT * FROM term_deposit_clean_encoded").fetchdf()

# %%
df_before_kmeans = con.execute(f"""
    SELECT
        age_t,
        balance_sign,
        balance_t,
        job_admin,
        job_bluecollar,
        job_technician,
        job_services,
        job_management,
        job_retired,
        job_selfemployed,
        job_entrepreneur,
        job_unemployed,
        job_housemaid,
        job_student,
        job_unknown,
        marital_married,
        marital_single,
        marital_divorced,
        marital_unknown,
        education_ord,
        default_bin,
        housing_bin,
        loan_bin,
    FROM term_deposit_clean_encoded
    """).fetchdf()

# %%
df_before_kmeans.shape

# %%
from sklearn.cluster import KMeans


# %%
seed = 23  # same seed used for the notebook part 2

# %%
kmeans_5 = KMeans(n_clusters=5, n_init='auto', random_state=seed).fit(df_before_kmeans)
labels_5 = kmeans_5.labels_


# %%
df_before_kmeans['cluster_k5'] = labels_5

# %%
df_before_kmeans.head()

# %%
# Adding the labels_5 clustering results as a new column to the base DataFrame
df_base['cluster_k5'] = labels_5

# %%
df_base.head()

# %%
df_base.to_csv("dashboard_base_k5.csv", index=False)

# %% [markdown]
# ----

# %% [markdown]
# #### Prepare the table for the Radar visualization

# %%
grouped = df_base.groupby('cluster_k5').agg({
    'age': 'mean',
    'balance': 'mean',
    'education_ord': 'mean'
}).reset_index()
    


# %%
grouped.head()

# %%
# Rename columns for clarity
grouped.columns = ['cluster_k5', 'avg_age', 'avg_balance', 'avg_education_ord']

# %%
population_avg = pandas.DataFrame([{
    'cluster_k5': -1,
    'avg_age': df_base['age'].mean(),
    'avg_balance': df_base['balance'].mean(),
    'avg_education_ord': df_base['education_ord'].mean()
}])

# %%
combined = pandas.concat([grouped, population_avg], ignore_index=True)

# %%
combined[['avg_age', 'avg_balance', 'avg_education_ord']] = combined[['avg_age', 'avg_balance', 'avg_education_ord']].round(2)

# %%
from sklearn.preprocessing import MinMaxScaler


# %%
scaler = MinMaxScaler()
normalized_values = scaler.fit_transform(combined[['avg_age', 'avg_balance', 'avg_education_ord']])
normalized_df = pandas.DataFrame(normalized_values, columns=['norm_age', 'norm_balance', 'norm_education_ord'])




# %%
combined_final = pandas.concat([combined, normalized_df], axis=1)


# %%
combined_final

# %%
# Step 7: Create long format with norm and abs values
df_abs = pandas.melt(combined_final, id_vars='cluster_k5',
                 value_vars=['avg_age', 'avg_balance', 'avg_education_ord'],
                 var_name='metric_type', value_name='abs_value')

df_norm = pandas.melt(combined_final, id_vars='cluster_k5',
                  value_vars=['norm_age', 'norm_balance', 'norm_education_ord'],
                  var_name='metric_type', value_name='norm_value')



# %%
df_abs

# %%
df_norm

# %%
# Clean metric_type in normalized version
df_norm['metric_type'] = df_norm['metric_type'].str.replace('norm_', 'avg_')

# Step 8: Merge both on cluster + metric
df_radar = pandas.merge(df_norm, df_abs, on=['cluster_k5', 'metric_type'])


# %%
df_radar

# %%
df_radar.to_csv("radar_linearchart.csv", index=False)

# %%



