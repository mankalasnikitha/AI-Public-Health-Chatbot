import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
np.random.seed(42)
data = {
    "Income": np.random.randint(20000, 100000, 20),
    "Credit_Score": np.random.randint(400, 800, 20),
    "Age": np.random.randint(21, 60, 20)
}
df = pd.DataFrame(data)
df["Loan_Approved"] = np.where(
    (df["Income"] > 50000) & (df["Credit_Score"] > 650),
    "Yes",
    "No"
)
print("Dataset:\n")
print(df)
X = df[["Income", "Credit_Score", "Age"]]
y = df["Loan_Approved"]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.3, random_state=42
)
log_model = LogisticRegression(max_iter=1000)
log_model.fit(X_train, y_train)
log_pred = log_model.predict(X_test)
dt_model = DecisionTreeClassifier(random_state=42)
dt_model.fit(X_train, y_train)
dt_pred = dt_model.predict(X_test)
knn_model = KNeighborsClassifier(n_neighbors=3)
knn_model.fit(X_train, y_train)
knn_pred = knn_model.predict(X_test)
print("\nAccuracy Results:")
print("Logistic Regression:", accuracy_score(y_test, log_pred))
print("Decision Tree:", accuracy_score(y_test, dt_pred))
print("KNN:", accuracy_score(y_test, knn_pred))
print("\nEnter New Applicant Details")
income = float(input("Income: "))
credit = float(input("Credit Score: "))
age = float(input("Age: "))
new_df = pd.DataFrame([[income, credit, age]],
                      columns=["Income", "Credit_Score", "Age"])
new_scaled = scaler.transform(new_df)
print("\nPrediction Results:")
print("Logistic Regression:", log_model.predict(new_scaled)[0])
print("Decision Tree:", dt_model.predict(new_scaled)[0])
print("KNN:", knn_model.predict(new_scaled)[0])

