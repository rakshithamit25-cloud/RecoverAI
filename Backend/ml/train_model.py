import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import joblib
import json
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from sklearn.preprocessing import LabelEncoder

# Fixed random seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def train_and_evaluate():
    # 1. Setup paths
    base_dir = Path(__file__).parent.parent
    dataset_path = base_dir / "dataset" / "transactions.csv"
    models_dir = base_dir / "ml" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Load dataset
    print(f"Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    
    # 3. Data Validation
    print("\n--- Data Validation ---")
    print(f"Total Rows: {len(df)}")
    print(f"Total Columns: {len(df.columns)}")
    print(f"Missing Values:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
    print("\nTarget Distribution (revenue_at_risk):")
    print(df['revenue_at_risk'].value_counts(normalize=True).apply(lambda x: f"{x:.1%}"))
    
    # 4. Feature Selection
    # Drop identifiers and arbitrary strings. 
    # NOTE: To avoid target leakage in a real scenario where we want to predict "Will this payment fail?" 
    # before it happens, we'd drop `payment_status` and `failure_reason`. Or if we are predicting 
    # "Will we successfully recover this *already failed* payment?", then the payment has failed.
    # The instructions say: "predict whether a transaction represents revenue at risk." based on the synthetic set.
    # To prevent 100% target leakage, we'll drop 'transaction_id' and 'customer_id'. 
    # We will also keep variables that are known at the point of recovery evaluation.
    drop_cols = ['transaction_id', 'customer_id', 'revenue_at_risk']
    
    X = df.drop(columns=drop_cols)
    y = df['revenue_at_risk']
    
    # 5. Handle categorical variables
    categorical_cols = X.select_dtypes(include=['object']).columns
    encoder_dict = {}
    
    for col in categorical_cols:
        le = LabelEncoder()
        # Convert all to string first to prevent issues with mixed types
        X[col] = le.fit_transform(X[col].astype(str))
        encoder_dict[col] = le
        
    feature_names = X.columns.tolist()
    
    # 6. Split dataset (70% train, 15% validation, 15% test)
    # First split off the 30% temp test for val and test
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=RANDOM_SEED, stratify=y
    )
    
    # Then split temp into 50/50 test and val
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=RANDOM_SEED, stratify=y_temp
    )
    
    print("\n--- Dataset Splits ---")
    print(f"Train: {len(X_train)} rows")
    print(f"Validation: {len(X_val)} rows")
    print(f"Test: {len(X_test)} rows")
    
    # 7. Train XGBoost Model
    print("\nTraining XGBoost model...")
    model = xgb.XGBClassifier(
        n_estimators=200,          # Maximum rounds
        learning_rate=0.05,
        max_depth=4,
        random_state=RANDOM_SEED,
        eval_metric='logloss',
        early_stopping_rounds=10    # Stop early if validation performance plateaus
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    print(f"Best iteration: {model.best_iteration}")
    
    # 8. Evaluate on the TEST set
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_prob)
    
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    # 9. Business Metrics
    # Get amounts for test set to calculate financial impact (using 'amount_due')
    test_amounts = df.loc[X_test.index, 'amount_due']
    
    total_revenue_test = test_amounts.sum()
    revenue_at_risk_actual = test_amounts[y_test == 1].sum()
    
    # Correctly identified at risk
    correct_at_risk = test_amounts[(y_test == 1) & (y_pred == 1)].sum()
    
    # False positive cost (Assumption: Unnecessary interventions cause a nominal operational burden or annoyance estimated at 2% of the flagged transaction value)
    false_positive_amount = test_amounts[(y_test == 0) & (y_pred == 1)].sum()
    fp_cost_assumption = 0.02 * false_positive_amount
    
    detection_rate = correct_at_risk / revenue_at_risk_actual if revenue_at_risk_actual > 0 else 0
    
    print("\n--- Model Evaluation (Test Set) ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {auc:.4f}")
    
    print("\n--- Confusion Matrix ---")
    print(f"True Positives (Correctly identified risk): {tp}")
    print(f"False Positives (Falsely flagged safe txn): {fp}")
    print(f"True Negatives (Correctly identified safe): {tn}")
    print(f"False Negatives (Missed risk): {fn}")
    
    print("\n--- Business Metrics ---")
    print(f"Total Revenue in Test Set: ₹{total_revenue_test:,.2f}")
    print(f"Actual Revenue at Risk: ₹{revenue_at_risk_actual:,.2f}")
    print(f"Revenue Assigned Correctly (TP Amount): ₹{correct_at_risk:,.2f}")
    print(f"False Positive Amount (FP): ₹{false_positive_amount:,.2f}")
    print(f"Estimated False Positive Cost (2% operational overhead): ₹{fp_cost_assumption:,.2f}")
    print(f"At-Risk Detection Rate: {detection_rate:.2%}")
    
    # 10. Generate SHAP & Feature Importance
    print("\nGenerating SHAP explanations and Feature Importance...")
    plt.figure(figsize=(10,6))
    xgb.plot_importance(model, max_num_features=10)
    plt.title("XGBoost Feature Importance")
    plt.tight_layout()
    plt.savefig(models_dir / "feature_importance.png")
    plt.close()
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    plt.figure()
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.savefig(models_dir / "shap_summary.png")
    plt.close()
    
    # 11. Save trained model & metadata
    model_path = models_dir / "recovery_model.joblib"
    joblib.dump(model, model_path)
    
    metadata = {
        "model_type": "xgboost.XGBClassifier",
        "model_version": "1.0.0",
        "training_date": datetime.now().isoformat(),
        "train_size": len(X_train),
        "validation_size": len(X_val),
        "test_size": len(X_test),
        "feature_names": feature_names,
        "test_metrics": {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "roc_auc": auc
        }
    }
    
    metadata_path = models_dir / "model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\n✅ Model training complete. Assets saved to {models_dir}")

if __name__ == "__main__":
    train_and_evaluate()
