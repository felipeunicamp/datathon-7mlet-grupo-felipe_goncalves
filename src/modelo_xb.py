import pandas as pd
import xgboost as xb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

#arms são as opções possíveis
#decisions é o histórico
#rewards é a recompensa para as respectivas escolhas


data = pd.read_csv('Bank_Personal_Loan_Modelling(1).csv')
df = data[['Age', 'Experience', 'Income','Family','Education','Securities Account',
       'CD Account', 'Online', 'CreditCard','Personal Loan']]

#-------
#Experiencia (-1,-2,-3)
#Income -> Valores com pouco exemplares
#-------

df = df[df['Experience']>=0]

X = df[['Age', 'Experience', 'Income','Family','Education','Securities Account',
       'CD Account', 'Online', 'CreditCard']]
y = df['Personal Loan']

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)

model = xb.XGBClassifier(eval_metric='mlogloss',random_state=42)
model.fit(X_train,y_train)
previsoes = model.predict(X_test)
acuracia = accuracy_score(y_test, previsoes)
model.save_model('modelo_xgboost.json')

print(f"Acurácia do XGBoost: {100*acuracia:.2f}")