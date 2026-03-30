"""
Weather Data Analysis & ML Temperature Prediction Pipeline
===========================================================
Steps: Preprocessing -> EDA -> Feature Engineering -> Model Training -> Evaluation

Input:  data/weather_data.csv (from ThingSpeak export)
Output: Charts, model comparison, predictions
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
import os

warnings.filterwarnings('ignore')

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
MODELS_DIR = os.path.join(BASE_DIR, "models")
INPUT_FILE = os.path.join(DATA_DIR, "weather_data.csv")

os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# ================================================================
# STEP 2: DATA LOADING & PREPROCESSING
# ================================================================
def load_and_preprocess():
    print("=" * 60)
    print("  Step 2: Data Loading & Preprocessing")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"  Raw data shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")

    # Parse timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    print(f"\n  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Total duration: {(df['timestamp'].max() - df['timestamp'].min()).days} days")

    # Check for missing values
    print(f"\n  Missing values:")
    print(f"    Temperature: {df['temperature'].isna().sum()}")
    print(f"    Humidity:    {df['humidity'].isna().sum()}")

    # Remove duplicates
    before = len(df)
    df = df.drop_duplicates(subset=['timestamp'])
    print(f"  Duplicates removed: {before - len(df)}")

    # Handle missing values (forward fill)
    df['temperature'] = df['temperature'].ffill()
    df['humidity'] = df['humidity'].ffill()

    # Remove outliers using IQR method for temperature
    Q1 = df['temperature'].quantile(0.25)
    Q3 = df['temperature'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    before = len(df)
    df = df[(df['temperature'] >= lower) & (df['temperature'] <= upper)]
    print(f"  Temperature outliers removed: {before - len(df)} (range: {lower:.1f} to {upper:.1f})")

    # Same for humidity
    Q1h = df['humidity'].quantile(0.25)
    Q3h = df['humidity'].quantile(0.75)
    IQRh = Q3h - Q1h
    lowerh = Q1h - 1.5 * IQRh
    upperh = Q3h + 1.5 * IQRh
    before = len(df)
    df = df[(df['humidity'] >= lowerh) & (df['humidity'] <= upperh)]
    print(f"  Humidity outliers removed: {before - len(df)} (range: {lowerh:.1f} to {upperh:.1f})")

    # Basic stats
    print(f"\n  After cleaning: {len(df)} rows")
    print(f"\n  Temperature stats:")
    print(f"    Min:  {df['temperature'].min():.1f} C")
    print(f"    Max:  {df['temperature'].max():.1f} C")
    print(f"    Mean: {df['temperature'].mean():.1f} C")
    print(f"    Std:  {df['temperature'].std():.1f} C")
    print(f"\n  Humidity stats:")
    print(f"    Min:  {df['humidity'].min():.1f} %")
    print(f"    Max:  {df['humidity'].max():.1f} %")
    print(f"    Mean: {df['humidity'].mean():.1f} %")

    # Save cleaned data
    clean_file = os.path.join(DATA_DIR, "weather_clean.csv")
    df.to_csv(clean_file, index=False)
    print(f"\n  [OK] Cleaned data saved: {clean_file}")

    return df


# ================================================================
# STEP 3: EXPLORATORY DATA ANALYSIS (EDA)
# ================================================================
def run_eda(df):
    print("\n" + "=" * 60)
    print("  Step 3: Exploratory Data Analysis")
    print("=" * 60)

    sns.set_theme(style="whitegrid", palette="deep")

    # --- Chart 1: Temperature & Humidity over time ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    ax1.plot(df['timestamp'], df['temperature'], color='#e74c3c', linewidth=0.5, alpha=0.8)
    ax1.set_ylabel('Temperature (C)', fontsize=12)
    ax1.set_title('Temperature Over Time', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    ax2.plot(df['timestamp'], df['humidity'], color='#3498db', linewidth=0.5, alpha=0.8)
    ax2.set_ylabel('Humidity (%)', fontsize=12)
    ax2.set_title('Humidity Over Time', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, alpha=0.3)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "01_time_series.png"), dpi=150)
    plt.close()
    print("  [OK] Chart 1: Time series plot saved")

    # --- Chart 2: Distribution of temperature & humidity ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.hist(df['temperature'], bins=50, color='#e74c3c', alpha=0.7, edgecolor='white')
    ax1.set_xlabel('Temperature (C)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Temperature Distribution')
    ax1.axvline(df['temperature'].mean(), color='black', linestyle='--', label=f"Mean: {df['temperature'].mean():.1f}C")
    ax1.legend()

    ax2.hist(df['humidity'], bins=50, color='#3498db', alpha=0.7, edgecolor='white')
    ax2.set_xlabel('Humidity (%)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Humidity Distribution')
    ax2.axvline(df['humidity'].mean(), color='black', linestyle='--', label=f"Mean: {df['humidity'].mean():.1f}%")
    ax2.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "02_distribution.png"), dpi=150)
    plt.close()
    print("  [OK] Chart 2: Distribution plot saved")

    # --- Chart 3: Temperature vs Humidity scatter ---
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(df['temperature'], df['humidity'], c=df['timestamp'].astype(np.int64),
                        cmap='viridis', alpha=0.3, s=5)
    ax.set_xlabel('Temperature (C)', fontsize=12)
    ax.set_ylabel('Humidity (%)', fontsize=12)
    ax.set_title('Temperature vs Humidity Correlation', fontsize=14, fontweight='bold')
    corr = df['temperature'].corr(df['humidity'])
    ax.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax.transAxes,
            fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "03_correlation.png"), dpi=150)
    plt.close()
    print(f"  [OK] Chart 3: Correlation plot (r = {corr:.3f})")

    # --- Chart 4: Hourly average temperature pattern ---
    df_temp = df.copy()
    df_temp['hour'] = df_temp['timestamp'].dt.hour
    hourly = df_temp.groupby('hour').agg({'temperature': ['mean', 'std'], 'humidity': ['mean', 'std']}).reset_index()
    hourly.columns = ['hour', 'temp_mean', 'temp_std', 'hum_mean', 'hum_std']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(hourly['hour'], hourly['temp_mean'], 'o-', color='#e74c3c', linewidth=2, markersize=6)
    ax1.fill_between(hourly['hour'], hourly['temp_mean'] - hourly['temp_std'],
                     hourly['temp_mean'] + hourly['temp_std'], alpha=0.2, color='#e74c3c')
    ax1.set_xlabel('Hour of Day')
    ax1.set_ylabel('Temperature (C)')
    ax1.set_title('Average Temperature by Hour')
    ax1.set_xticks(range(0, 24, 2))
    ax1.grid(True, alpha=0.3)

    ax2.plot(hourly['hour'], hourly['hum_mean'], 'o-', color='#3498db', linewidth=2, markersize=6)
    ax2.fill_between(hourly['hour'], hourly['hum_mean'] - hourly['hum_std'],
                     hourly['hum_mean'] + hourly['hum_std'], alpha=0.2, color='#3498db')
    ax2.set_xlabel('Hour of Day')
    ax2.set_ylabel('Humidity (%)')
    ax2.set_title('Average Humidity by Hour')
    ax2.set_xticks(range(0, 24, 2))
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "04_hourly_pattern.png"), dpi=150)
    plt.close()
    print("  [OK] Chart 4: Hourly pattern plot saved")

    # --- Chart 5: Daily temperature range (box plot) ---
    df_temp['date_only'] = df_temp['timestamp'].dt.date
    dates = sorted(df_temp['date_only'].unique())

    fig, ax = plt.subplots(figsize=(14, 6))
    daily_data = [df_temp[df_temp['date_only'] == d]['temperature'].values for d in dates]
    bp = ax.boxplot(daily_data, labels=[str(d)[5:] for d in dates], patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('#e74c3c')
        patch.set_alpha(0.6)
    ax.set_xlabel('Date (MM-DD)')
    ax.set_ylabel('Temperature (C)')
    ax.set_title('Daily Temperature Range (Box Plot)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "05_daily_boxplot.png"), dpi=150)
    plt.close()
    print("  [OK] Chart 5: Daily boxplot saved")

    # --- Chart 6: Heatmap - hour vs day ---
    df_temp['day_of_week'] = df_temp['timestamp'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = df_temp.pivot_table(values='temperature', index='day_of_week', columns='hour', aggfunc='mean')
    pivot = pivot.reindex(day_order)

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(pivot, cmap='RdYlBu_r', annot=False, fmt='.1f', ax=ax, cbar_kws={'label': 'Temperature (C)'})
    ax.set_title('Temperature Heatmap: Day of Week vs Hour of Day', fontsize=14, fontweight='bold')
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Day of Week')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "06_heatmap.png"), dpi=150)
    plt.close()
    print("  [OK] Chart 6: Heatmap saved")

    print(f"\n  All charts saved to: {CHARTS_DIR}")
    return df_temp


# ================================================================
# STEP 4: FEATURE ENGINEERING
# ================================================================
def engineer_features(df):
    print("\n" + "=" * 60)
    print("  Step 4: Feature Engineering")
    print("=" * 60)

    # Time-based features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Mon, 6=Sun
    df['day_of_month'] = df['timestamp'].dt.day
    df['is_daytime'] = ((df['hour'] >= 6) & (df['hour'] <= 18)).astype(int)

    # Cyclical encoding for hour (so 23 and 0 are close)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

    # Lag features (previous readings)
    for lag in [1, 3, 6, 12]:
        df[f'temp_lag_{lag}'] = df['temperature'].shift(lag)
        df[f'hum_lag_{lag}'] = df['humidity'].shift(lag)

    # Rolling averages
    for window in [6, 12, 24]:
        df[f'temp_rolling_{window}'] = df['temperature'].rolling(window=window).mean()
        df[f'hum_rolling_{window}'] = df['humidity'].rolling(window=window).mean()

    # Temperature rate of change
    df['temp_diff_1'] = df['temperature'].diff(1)
    df['temp_diff_3'] = df['temperature'].diff(3)

    # Drop rows with NaN from lag/rolling features
    before = len(df)
    df = df.dropna()
    print(f"  Rows after feature engineering: {len(df)} (dropped {before - len(df)} due to lag/rolling)")

    feature_cols = [
        'humidity', 'hour', 'day_of_week', 'is_daytime',
        'hour_sin', 'hour_cos',
        'temp_lag_1', 'temp_lag_3', 'temp_lag_6', 'temp_lag_12',
        'hum_lag_1', 'hum_lag_3', 'hum_lag_6', 'hum_lag_12',
        'temp_rolling_6', 'temp_rolling_12', 'temp_rolling_24',
        'hum_rolling_6', 'hum_rolling_12', 'hum_rolling_24',
        'temp_diff_1', 'temp_diff_3'
    ]

    print(f"  Total features: {len(feature_cols)}")
    print(f"  Features: {feature_cols}")

    return df, feature_cols


# ================================================================
# STEP 5 & 6: MODEL TRAINING
# ================================================================
def train_models(df, feature_cols):
    print("\n" + "=" * 60)
    print("  Steps 5 & 6: Train/Test Split & Model Training")
    print("=" * 60)

    target = 'temperature'
    X = df[feature_cols].values
    y = df[target].values

    # Time-based split (last 20% for testing — important for time series!)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    timestamps_test = df['timestamp'].values[split_idx:]

    print(f"  Training set: {len(X_train)} samples")
    print(f"  Testing set:  {len(X_test)} samples")
    print(f"  Split ratio:  80/20")

    # Scale features
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ---- Model 1: Linear Regression ----
    print("\n  Training Model 1: Linear Regression...")
    lr = LinearRegression()
    lr.fit(X_train_scaled, y_train)
    lr_pred = lr.predict(X_test_scaled)
    lr_metrics = evaluate(y_test, lr_pred, "Linear Regression")

    # ---- Model 2: Random Forest ----
    print("  Training Model 2: Random Forest...")
    rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(X_train_scaled, y_train)
    rf_pred = rf.predict(X_test_scaled)
    rf_metrics = evaluate(y_test, rf_pred, "Random Forest")

    # ---- Model 3: Gradient Boosting ----
    print("  Training Model 3: Gradient Boosting...")
    gb = GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42)
    gb.fit(X_train_scaled, y_train)
    gb_pred = gb.predict(X_test_scaled)
    gb_metrics = evaluate(y_test, gb_pred, "Gradient Boosting")

    return {
        'Linear Regression': {'pred': lr_pred, 'metrics': lr_metrics, 'model': lr},
        'Random Forest': {'pred': rf_pred, 'metrics': rf_metrics, 'model': rf},
        'Gradient Boosting': {'pred': gb_pred, 'metrics': gb_metrics, 'model': gb},
    }, y_test, timestamps_test, scaler, feature_cols, rf


def evaluate(y_true, y_pred, name):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    print(f"    {name}: RMSE={rmse:.3f}, MAE={mae:.3f}, R2={r2:.4f}, MAPE={mape:.2f}%")
    return {'rmse': rmse, 'mae': mae, 'r2': r2, 'mape': mape}


# ================================================================
# STEP 7 & 8: EVALUATION & VISUALIZATION
# ================================================================
def visualize_results(results, y_test, timestamps_test):
    print("\n" + "=" * 60)
    print("  Steps 7 & 8: Evaluation & Visualization")
    print("=" * 60)

    # --- Chart 7: Model Comparison Bar Chart ---
    models = list(results.keys())
    rmse_vals = [results[m]['metrics']['rmse'] for m in models]
    mae_vals = [results[m]['metrics']['mae'] for m in models]
    r2_vals = [results[m]['metrics']['r2'] for m in models]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    colors = ['#3498db', '#2ecc71', '#e74c3c']

    axes[0].bar(models, rmse_vals, color=colors)
    axes[0].set_title('RMSE (Lower = Better)', fontweight='bold')
    axes[0].set_ylabel('RMSE (C)')
    for i, v in enumerate(rmse_vals):
        axes[0].text(i, v + 0.01, f'{v:.3f}', ha='center', fontweight='bold')

    axes[1].bar(models, mae_vals, color=colors)
    axes[1].set_title('MAE (Lower = Better)', fontweight='bold')
    axes[1].set_ylabel('MAE (C)')
    for i, v in enumerate(mae_vals):
        axes[1].text(i, v + 0.01, f'{v:.3f}', ha='center', fontweight='bold')

    axes[2].bar(models, r2_vals, color=colors)
    axes[2].set_title('R-squared (Higher = Better)', fontweight='bold')
    axes[2].set_ylabel('R2 Score')
    for i, v in enumerate(r2_vals):
        axes[2].text(i, v + 0.005, f'{v:.4f}', ha='center', fontweight='bold')

    plt.suptitle('Model Comparison', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "07_model_comparison.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] Chart 7: Model comparison saved")

    # --- Chart 8: Predictions vs Actual (best model) ---
    best_model = min(results, key=lambda m: results[m]['metrics']['rmse'])
    best_pred = results[best_model]['pred']

    # Show last N points for clarity
    N = min(500, len(y_test))
    ts = pd.to_datetime(timestamps_test[-N:])

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(ts, y_test[-N:], label='Actual', color='#2c3e50', linewidth=1.5, alpha=0.8)
    ax.plot(ts, best_pred[-N:], label=f'Predicted ({best_model})', color='#e74c3c',
            linewidth=1.5, alpha=0.8, linestyle='--')
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Temperature (C)', fontsize=12)
    ax.set_title(f'Temperature Prediction: Actual vs {best_model}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %H:%M'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "08_prediction_vs_actual.png"), dpi=150)
    plt.close()
    print(f"  [OK] Chart 8: Prediction plot ({best_model})")

    # --- Chart 9: Scatter - Predicted vs Actual ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for i, (name, data) in enumerate(results.items()):
        pred = data['pred']
        ax = axes[i]
        ax.scatter(y_test, pred, alpha=0.3, s=5, color=colors[i])
        min_val = min(y_test.min(), pred.min())
        max_val = max(y_test.max(), pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect prediction')
        ax.set_xlabel('Actual Temperature (C)')
        ax.set_ylabel('Predicted Temperature (C)')
        ax.set_title(f'{name}\nR2 = {data["metrics"]["r2"]:.4f}')
        ax.legend()
        ax.grid(True, alpha=0.3)
    plt.suptitle('Predicted vs Actual (Closer to red line = better)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "09_scatter_pred_vs_actual.png"), dpi=150)
    plt.close()
    print("  [OK] Chart 9: Scatter plot saved")

    # --- Chart 10: Feature Importance (Random Forest) ---
    rf_model = results['Random Forest']['model']

    # Get feature names from the training
    feature_names = [
        'Humidity', 'Hour', 'Day of Week', 'Is Daytime',
        'Hour (sin)', 'Hour (cos)',
        'Temp Lag-1', 'Temp Lag-3', 'Temp Lag-6', 'Temp Lag-12',
        'Hum Lag-1', 'Hum Lag-3', 'Hum Lag-6', 'Hum Lag-12',
        'Temp Roll-6', 'Temp Roll-12', 'Temp Roll-24',
        'Hum Roll-6', 'Hum Roll-12', 'Hum Roll-24',
        'Temp Diff-1', 'Temp Diff-3'
    ]

    importances = rf_model.feature_importances_
    sorted_idx = np.argsort(importances)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(range(len(sorted_idx)), importances[sorted_idx], color='#2ecc71')
    ax.set_yticks(range(len(sorted_idx)))
    ax.set_yticklabels([feature_names[i] for i in sorted_idx])
    ax.set_xlabel('Importance')
    ax.set_title('Feature Importance (Random Forest)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "10_feature_importance.png"), dpi=150)
    plt.close()
    print("  [OK] Chart 10: Feature importance saved")

    # --- Final Summary ---
    print("\n" + "=" * 60)
    print("  FINAL RESULTS SUMMARY")
    print("=" * 60)
    print(f"\n  {'Model':<25} {'RMSE':>8} {'MAE':>8} {'R2':>8} {'MAPE':>8}")
    print("  " + "-" * 57)
    for name, data in results.items():
        m = data['metrics']
        print(f"  {name:<25} {m['rmse']:>8.3f} {m['mae']:>8.3f} {m['r2']:>8.4f} {m['mape']:>7.2f}%")
    print()
    print(f"  Best Model: {best_model}")
    print(f"  Best RMSE:  {results[best_model]['metrics']['rmse']:.3f} C")
    print(f"  Best R2:    {results[best_model]['metrics']['r2']:.4f}")
    print(f"\n  All charts saved to: {CHARTS_DIR}")
    print("  " + "=" * 58)

    return best_model


# ================================================================
# MAIN
# ================================================================
if __name__ == "__main__":
    print("\n  WEATHER DATA ANALYSIS & ML PREDICTION PIPELINE")
    print("  " + "=" * 50)

    # Step 2
    df = load_and_preprocess()

    # Step 3
    df = run_eda(df)

    # Step 4
    df, feature_cols = engineer_features(df)

    # Steps 5 & 6
    results, y_test, ts_test, scaler, features, rf = train_models(df, feature_cols)

    # Steps 7 & 8
    best = visualize_results(results, y_test, ts_test)

    print("\n  PIPELINE COMPLETE!")
    print(f"  Best model: {best}")
    print(f"  Check the 'charts' folder for all visualizations.")
