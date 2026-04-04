import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# Load data
df = pd.read_excel("Master_OD_Data.xlsx")

# Clean
df = df.fillna(0)

# Features (input)
X = df[[
    "HMR",
    "Average Running Hours",
    "Last Service HMR"
]]

# Target (output)
y = df["Next Service HMR"]

# Model
model = RandomForestRegressor(n_estimators=100)

model.fit(X, y)

# Save model
joblib.dump(model, "model.pkl")

print("✅ Model trained & saved")