from pathlib import Path
import json, joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"/"heart_rate_training_data.csv"
AI=ROOT/"ai"
FEATURES=["current_bpm","avg_bpm","min_bpm","max_bpm","std_bpm","change_bpm"]

df=pd.read_csv(DATA)
X=df[FEATURES]; y=df["label"]
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,stratify=y,random_state=42)
clf=RandomForestClassifier(n_estimators=400,max_depth=10,min_samples_leaf=3,random_state=42,class_weight="balanced_subsample",n_jobs=-1)
clf.fit(Xtr,ytr)
pred=clf.predict(Xte)
normal=Xtr[ytr=="NORMAL"]
iso=IsolationForest(n_estimators=350,contamination=.22,random_state=42,n_jobs=-1).fit(normal)

p,r,f,_=precision_recall_fscore_support(yte,pred,average="weighted",zero_division=0)
metrics={
 "accuracy":round(float(accuracy_score(yte,pred)),4),
 "precision":round(float(p),4),"recall":round(float(r),4),"f1":round(float(f),4),
 "training_samples":int(len(Xtr)),"test_samples":int(len(Xte)),
 "confusion_matrix":confusion_matrix(yte,pred,labels=["NORMAL","UNUSUAL_PATTERN"]).tolist(),
 "classes":["NORMAL","UNUSUAL_PATTERN"],"features":FEATURES,
 "dataset":"Synthetic educational dataset","validation_note":"Not clinical validation."
}
joblib.dump({"model":clf,"features":FEATURES},AI/"classifier.joblib")
joblib.dump({"model":iso,"features":FEATURES},AI/"anomaly_detector.joblib")
(AI/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
print("=== PulseGuard AI model training ===")
print(f"Training samples: {len(Xtr)}")
print(f"Test samples: {len(Xte)}")
print(f"Accuracy: {metrics['accuracy']:.3f}")
print(f"Precision: {metrics['precision']:.3f}")
print(f"Recall: {metrics['recall']:.3f}")
print(f"F1: {metrics['f1']:.3f}")
print("Saved classifier.joblib, anomaly_detector.joblib and metrics.json")
