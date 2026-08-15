from pathlib import Path
from datetime import datetime
import csv, io, json, sqlite3, uuid, os
import warnings
import joblib, numpy as np, pandas as pd
warnings.filterwarnings("ignore", message="`sklearn.utils.parallel.delayed` should be used with `sklearn.utils.parallel.Parallel`")
from flask import Flask, jsonify, request, send_from_directory, session, redirect, Response
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from werkzeug.security import generate_password_hash, check_password_hash

ROOT=Path(__file__).resolve().parent.parent
FRONTEND=ROOT/"frontend"; AI=ROOT/"ai"; DB=ROOT/"data"/"pulseguard.db"

app=Flask(__name__,static_folder=str(FRONTEND),static_url_path="")
app.secret_key=os.environ.get("PULSEGUARD_SECRET_KEY","pulseguard-local-demo-secret-change-for-deployment")

FEATURES=["current_bpm","avg_bpm","min_bpm","max_bpm","std_bpm","change_bpm"]
clf_bundle=joblib.load(AI/"classifier.joblib") if (AI/"classifier.joblib").exists() else None
iso_bundle=joblib.load(AI/"anomaly_detector.joblib") if (AI/"anomaly_detector.joblib").exists() else None
metrics=json.loads((AI/"metrics.json").read_text()) if (AI/"metrics.json").exists() else {}

SCHEMA = {
    "users": """CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL, role TEXT DEFAULT 'USER', created_at TEXT NOT NULL)""",
    "sessions": """CREATE TABLE IF NOT EXISTS sessions(
      id TEXT PRIMARY KEY, user_id INTEGER, started_at TEXT, ended_at TEXT, readings INTEGER DEFAULT 0)""",
    "readings": """CREATE TABLE IF NOT EXISTS readings(
      id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, user_id INTEGER, timestamp TEXT, bpm REAL,
      rule_status TEXT, ai_status TEXT, confidence REAL, risk_score REAL,
      anomaly_score REAL, explanation TEXT)""",
    "notifications": """CREATE TABLE IF NOT EXISTS notifications(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, timestamp TEXT,
      severity TEXT, title TEXT, message TEXT, bpm REAL, risk_score REAL, read INTEGER DEFAULT 0)"""
}

def con():
    # IMPORTANT: opening a connection must never run CREATE TABLE / COMMIT.
    # Doing schema writes on every request caused the previous SQLite lock storm.
    c=sqlite3.connect(DB, timeout=15, check_same_thread=False)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA busy_timeout=15000")
    return c

def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(DB, timeout=30, check_same_thread=False)
    try:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA busy_timeout=30000")
        for sql in SCHEMA.values():
            c.execute(sql)
        c.commit()
    finally:
        c.close()

def db_write_with_retry(sql, params=(), retries=8):
    import time
    last=None
    for attempt in range(retries):
        c=None
        try:
            c=con()
            c.execute(sql, params)
            c.commit()
            return
        except sqlite3.OperationalError as e:
            last=e
            if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                raise
            time.sleep(min(1.5, 0.12*(2**attempt)))
        finally:
            if c is not None:
                c.close()
    raise last

init_db()

def seed_demo():
    c=con()
    row=c.execute("SELECT id FROM users WHERE username=?",("demo",)).fetchone()
    if not row:
        c.execute("INSERT INTO users(name,username,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                  ("Demo User","demo",generate_password_hash("pulse123"),"USER",datetime.now().isoformat(timespec="seconds")))
        c.commit()
    c.close()

seed_demo()

def current_user():
    uid=session.get("user_id")
    if not uid: return None
    c=con(); r=c.execute("SELECT id,name,username,role FROM users WHERE id=?",(uid,)).fetchone(); c.close()
    return r

def rule(b): return "LOW" if b<60 else ("HIGH" if b>100 else "NORMAL")

def feat(history):
    a=np.asarray(history[-20:],dtype=float)
    cur=float(a[-1])
    return pd.DataFrame([{
        "current_bpm":cur,"avg_bpm":float(a.mean()),"min_bpm":float(a.min()),
        "max_bpm":float(a.max()),"std_bpm":float(a.std()),
        "change_bpm":float(cur-a[-2]) if len(a)>1 else 0
    }],columns=FEATURES)

def risk(bpm, ai, confidence, std):
    # Demonstration risk is driven primarily by the explicit BPM thresholds.
    # AI contributes only when the combined anomaly gate is satisfied.
    score=0
    if bpm<60 or bpm>100: score+=55
    if bpm<50 or bpm>115: score+=15
    if std>15: score+=10
    if ai!="NORMAL": score+=20*confidence
    return int(max(0,min(100,round(score))))

def explain(f, ai_status):
    reasons=[]
    b=f.current_bpm.iloc[0]; avg=f.avg_bpm.iloc[0]; ch=f.change_bpm.iloc[0]; sd=f.std_bpm.iloc[0]
    if b<60: reasons.append("the current BPM is below the demonstration lower threshold")
    elif b>100: reasons.append("the current BPM is above the demonstration upper threshold")
    if abs(b-avg)>12: reasons.append("the current BPM differs noticeably from the recent average")
    if sd>12: reasons.append("recent BPM variability is elevated")
    if abs(ch)>15: reasons.append("the latest BPM change is large")
    if ai_status!="NORMAL": reasons.append("the anomaly detector found the pattern different from its learned normal profile")
    if not reasons:
        return "The AI sees a pattern that is consistent with the learned normal demonstration profile."
    return "The AI flagged this window because " + "; ".join(reasons) + "."

@app.get("/")
def home():
    if current_user(): return redirect("/app")
    return send_from_directory(FRONTEND,"landing.html")

@app.get("/login")
def login_page(): return send_from_directory(FRONTEND,"login.html")

@app.get("/register")
def register_page(): return send_from_directory(FRONTEND,"register.html")

@app.get("/app")
def dashboard():
    if not current_user(): return redirect("/login")
    return send_from_directory(FRONTEND,"app.html")

@app.post("/api/auth/register")
def register():
    data=request.get_json(force=True) or {}
    name=str(data.get("name","")).strip()
    username=str(data.get("username","")).strip().lower()
    password=str(data.get("password",""))
    if len(name)<2 or len(username)<3 or len(password)<6:
        return jsonify(error="Enter a name, username (3+ characters), and password (6+ characters)."),400
    c=con()
    try:
        c.execute("INSERT INTO users(name,username,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                  (name,username,generate_password_hash(password),"USER",datetime.now().isoformat(timespec="seconds")))
        c.commit()
        uid=c.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone()[0]
    except sqlite3.IntegrityError:
        c.close(); return jsonify(error="That username already exists."),409
    c.close(); session["user_id"]=uid
    return jsonify(ok=True)

@app.post("/api/auth/login")
def login():
    data=request.get_json(force=True) or {}
    username=str(data.get("username","")).strip().lower()
    password=str(data.get("password",""))
    c=con(); r=c.execute("SELECT id,password_hash FROM users WHERE username=?",(username,)).fetchone(); c.close()
    if not r or not check_password_hash(r[1],password):
        return jsonify(error="Invalid username or password."),401
    session["user_id"]=r[0]
    return jsonify(ok=True)

@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify(ok=True)

@app.get("/api/auth/me")
def me():
    u=current_user()
    if not u: return jsonify(authenticated=False)
    return jsonify(authenticated=True,user={"id":u[0],"name":u[1],"username":u[2],"role":u[3]})

@app.get("/api/health")
def health():
    try:
        c=con()
        c.execute("SELECT 1").fetchone()
        journal=c.execute("PRAGMA journal_mode").fetchone()[0]
        c.close()
        return jsonify(status="online",database="ok",journal_mode=journal,
                       ai_ready=bool(clf_bundle and iso_bundle),version="FINAL-1.0",
                       time=datetime.now().isoformat(timespec="seconds"))
    except Exception as e:
        return jsonify(status="error",database=str(e),ai_ready=False,version="FINAL-1.0"),500

@app.get("/api/metrics")
def get_metrics(): return jsonify(metrics)

@app.post("/api/session/start")
def session_start():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    sid=uuid.uuid4().hex[:12]; now=datetime.now().isoformat(timespec="seconds")
    c=con(); c.execute("INSERT INTO sessions(id,user_id,started_at) VALUES(?,?,?)",(sid,u[0],now)); c.commit(); c.close()
    return jsonify(session_id=sid,started_at=now)

@app.post("/api/session/end")
def session_end():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    sid=(request.get_json(force=True) or {}).get("session_id")
    if not sid:return jsonify(error="session_id required"),400
    now=datetime.now().isoformat(timespec="seconds"); c=con()
    count=c.execute("SELECT COUNT(*) FROM readings WHERE session_id=? AND user_id=?",(sid,u[0])).fetchone()[0]
    c.execute("UPDATE sessions SET ended_at=?,readings=? WHERE id=? AND user_id=?",(now,count,sid,u[0])); c.commit(); c.close()
    return jsonify(session_id=sid,ended_at=now,readings=count)

@app.post("/api/predict")
def predict():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    if not clf_bundle or not iso_bundle:return jsonify(error="AI models missing. Run: python ai/train_models.py"),500
    data=request.get_json(force=True) or {}
    history=data.get("history",[]); sid=data.get("session_id")
    if not history:return jsonify(error="No BPM history supplied"),400
    f=feat(history); clf=clf_bundle["model"]; iso=iso_bundle["model"]
    pred=str(clf.predict(f)[0]); confidence=float(max(clf.predict_proba(f)[0]))
    anomaly=int(iso.predict(f)[0])==-1
    # Avoid letting a single noisy model vote create an alert. Require both
    # ML signals to agree, and wait for enough samples for a meaningful window.
    bpm=float(f.current_bpm.iloc[0]); rs=rule(bpm)
    enough_history=len(history)>=10
    std=float(f.std_bpm.iloc[0]); change=abs(float(f.change_bpm.iloc[0]))
    # AI is advisory for in-range BPM. A single noisy normal-range reading
    # must never become an alert. Require a strong signal in the current
    # feature window in addition to agreement from both models.
    pattern_signal=(std >= 15.0 or change >= 25.0 or bpm < 50 or bpm > 115)
    ml_unusual=bool(enough_history and pred=="UNUSUAL_PATTERN" and anomaly and pattern_signal)
    ai_status="UNUSUAL_PATTERN" if ml_unusual else "NORMAL"
    score=risk(bpm,ai_status,confidence,float(f.std_bpm.iloc[0]))
    explanation=explain(f,ai_status)
    ts=datetime.now().isoformat(timespec="seconds")
    anomaly_score=float(iso.decision_function(f)[0])
    created_alert=False
    reading_sql = """INSERT INTO readings(
        session_id,user_id,timestamp,bpm,rule_status,ai_status,confidence,
        risk_score,anomaly_score,explanation
    ) VALUES(?,?,?,?,?,?,?,?,?,?)"""
    db_write_with_retry(reading_sql, (
        sid,u[0],ts,bpm,rs,ai_status,confidence,score,anomaly_score,explanation
    ))

    # Only genuine threshold abnormalities or a confirmed AI pattern create alerts.
    if rs != "NORMAL" or ai_status != "NORMAL":
        severity = "HIGH" if rs != "NORMAL" else "ATTENTION"
        if rs == "HIGH":
            title = "High heart rate detected"
        elif rs == "LOW":
            title = "Low heart rate detected"
        else:
            title = "AI pattern needs attention"
        message = f"Demonstration reading: BPM {bpm:.0f}. {explanation}"
        # Suppress duplicate alerts generated by the dashboard polling loop.
        c=con()
        from datetime import timedelta
        cutoff=(datetime.now()-timedelta(seconds=12)).isoformat(timespec="seconds")
        recent=c.execute(
            """SELECT id FROM notifications
               WHERE user_id=? AND severity=? AND bpm=? AND timestamp>=?
               ORDER BY id DESC LIMIT 1""",
            (u[0],severity,bpm,cutoff)
        ).fetchone()
        c.close()
        if recent is None:
            db_write_with_retry(
                """INSERT INTO notifications(
                    user_id,timestamp,severity,title,message,bpm,risk_score
                ) VALUES(?,?,?,?,?,?,?)""",
                (u[0],ts,severity,title,message,bpm,score)
            )
            created_alert=True

    # `alert` describes the current clinical-demo decision, not whether a
    # duplicate notification row was inserted. This keeps API semantics stable
    # when dashboard polling suppression prevents a second notification.
    alert_condition = (rs != "NORMAL" or ai_status != "NORMAL")
    return jsonify(timestamp=ts,bpm=round(bpm,1),rule_status=rs,ai_status=ai_status,
                   confidence=round(confidence,3),risk_score=score,anomaly_score=round(anomaly_score,4),
                   alert=alert_condition,notification_created=created_alert,threshold_alert=rs!="NORMAL",
                   explanation=explanation,features={k:round(float(f[k].iloc[0]),2) for k in FEATURES})

@app.get("/api/alert-policy")
def alert_policy():
    return jsonify(
        lower_bpm=60, upper_bpm=100,
        ai_min_history=10, ai_min_std=15.0, ai_min_change=25.0,
        duplicate_suppression_seconds=15,
        note="Normal-range single readings do not create alerts."
    )

@app.get("/api/history")
def history():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    c=con()
    rows=c.execute("""SELECT timestamp,bpm,rule_status,ai_status,confidence,risk_score,explanation
                      FROM readings WHERE user_id=? ORDER BY id DESC LIMIT 200""",(u[0],)).fetchall()
    c.close()
    return jsonify([{"timestamp":r[0],"bpm":r[1],"rule":r[2],"ai":r[3],"confidence":r[4],"risk":r[5],"explanation":r[6]} for r in rows])

@app.get("/api/export.csv")
def export_csv():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    c=con()
    rows=c.execute("""SELECT timestamp,bpm,rule_status,ai_status,confidence,risk_score,anomaly_score,explanation
                      FROM readings WHERE user_id=? ORDER BY id""",(u[0],)).fetchall(); c.close()
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(["timestamp","bpm","rule_status","ai_status","confidence","risk_score","anomaly_score","explanation"]); w.writerows(rows)
    return Response(out.getvalue(),mimetype="text/csv",
                    headers={"Content-Disposition":"attachment; filename=pulseguard_readings.csv"})


@app.get("/api/notifications")
def notifications():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    c=con()
    rows=c.execute("""SELECT id,timestamp,severity,title,message,bpm,risk_score,read
                      FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 50""",(u[0],)).fetchall()
    c.close()
    return jsonify([{"id":r[0],"timestamp":r[1],"severity":r[2],"title":r[3],"message":r[4],
                     "bpm":r[5],"risk":r[6],"read":bool(r[7])} for r in rows])

@app.post("/api/notifications/<int:nid>/read")
def notification_read(nid):
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    c=con(); c.execute("UPDATE notifications SET read=1 WHERE id=? AND user_id=?",(nid,u[0])); c.commit(); c.close()
    return jsonify(ok=True)

@app.post("/api/notifications/read-all")
def notifications_read_all():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    c=con(); c.execute("UPDATE notifications SET read=1 WHERE user_id=?",(u[0],)); c.commit(); c.close()
    return jsonify(ok=True)

@app.get("/api/analytics")
def analytics():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    c=con()
    rows=c.execute("""SELECT bpm,rule_status,ai_status,confidence,risk_score,timestamp
                      FROM readings WHERE user_id=? ORDER BY id""",(u[0],)).fetchall()
    sessions=c.execute("""SELECT id,started_at,ended_at,readings FROM sessions
                          WHERE user_id=? ORDER BY started_at DESC LIMIT 30""",(u[0],)).fetchall()
    c.close()
    if not rows:
        return jsonify(total_readings=0,avg_bpm=None,min_bpm=None,max_bpm=None,
                       abnormal_count=0,ai_unusual_count=0,avg_risk=None,
                       avg_confidence=None,stability=None,sessions=[])
    bpms=[float(r[0]) for r in rows]
    risks=[float(r[4]) for r in rows]
    conf=[float(r[3]) for r in rows]
    abnormal=sum(1 for r in rows if r[1]!="NORMAL")
    unusual=sum(1 for r in rows if r[2]!="NORMAL")
    mean=sum(bpms)/len(bpms)
    variance=sum((x-mean)**2 for x in bpms)/len(bpms)
    stability=max(0, min(100, round(100-(variance**0.5)*5)))
    return jsonify(
        total_readings=len(rows), avg_bpm=round(mean,1), min_bpm=min(bpms),
        max_bpm=max(bpms), abnormal_count=abnormal, ai_unusual_count=unusual,
        avg_risk=round(sum(risks)/len(risks),1),
        avg_confidence=round(sum(conf)/len(conf),3),
        stability=stability,
        sessions=[{"id":r[0],"started_at":r[1],"ended_at":r[2],"readings":r[3]} for r in sessions],
        timeline=[{"timestamp":r[5],"bpm":r[0],"rule":r[1],"ai":r[2],"risk":r[4]} for r in rows[-100:]]
    )

@app.get("/api/report.pdf")
def report_pdf():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    c=con()
    user=c.execute("SELECT name,username FROM users WHERE id=?",(u[0],)).fetchone()
    rows=c.execute("""SELECT timestamp,bpm,rule_status,ai_status,confidence,risk_score,explanation
                      FROM readings WHERE user_id=? ORDER BY id DESC LIMIT 100""",(u[0],)).fetchall()
    c.close()

    bpms=[float(r[1]) for r in rows]
    avg=sum(bpms)/len(bpms) if bpms else 0
    mn=min(bpms) if bpms else 0
    mx=max(bpms) if bpms else 0
    abnormal=sum(1 for r in rows if r[2]!="NORMAL")
    unusual=sum(1 for r in rows if r[3]!="NORMAL")
    avg_risk=sum(float(r[5]) for r in rows)/len(rows) if rows else 0

    from io import BytesIO
    buf=BytesIO()
    pdf=canvas.Canvas(buf,pagesize=A4)
    W,H=A4
    y=H-25*mm

    pdf.setFont("Helvetica-Bold",20)
    pdf.drawString(20*mm,y,"PulseGuard AI")
    y-=9*mm
    pdf.setFont("Helvetica",10)
    pdf.drawString(20*mm,y,"Personal Monitoring Summary")
    y-=12*mm

    pdf.setFont("Helvetica-Bold",11)
    pdf.drawString(20*mm,y,"Account")
    pdf.setFont("Helvetica",10)
    pdf.drawString(55*mm,y,f"{user[0]}  ({user[1]})")
    y-=8*mm

    pdf.setFont("Helvetica-Bold",11)
    pdf.drawString(20*mm,y,"Summary")
    y-=7*mm
    summary=[
        f"Readings analyzed: {len(rows)}",
        f"Average BPM: {avg:.1f}",
        f"Minimum BPM: {mn:.0f}",
        f"Maximum BPM: {mx:.0f}",
        f"Threshold-abnormal events: {abnormal}",
        f"AI unusual-pattern events: {unusual}",
        f"Average demonstration risk score: {avg_risk:.1f}/100",
    ]
    pdf.setFont("Helvetica",10)
    for line in summary:
        pdf.drawString(24*mm,y,line); y-=6*mm

    y-=4*mm
    pdf.setFont("Helvetica-Bold",11)
    pdf.drawString(20*mm,y,"Recent events")
    y-=7*mm
    pdf.setFont("Helvetica",8)
    for r in rows[:18]:
        line=f"{r[0]} | BPM {float(r[1]):.0f} | {r[2]} | {r[3]} | Risk {float(r[5]):.0f}"
        pdf.drawString(20*mm,y,line[:105])
        y-=5*mm
        if y<25*mm:
            pdf.showPage(); y=H-25*mm; pdf.setFont("Helvetica",8)

    if y<42*mm:
        pdf.showPage(); y=H-25*mm
    pdf.setFont("Helvetica-Bold",9)
    pdf.drawString(20*mm,y,"Responsible-use note")
    y-=5*mm
    pdf.setFont("Helvetica",8)
    note=("This report summarizes an educational software prototype. "
          "Its current readings are simulated and its ML models use synthetic training data. "
          "It is not a medical diagnosis, clinical assessment, or treatment recommendation.")
    for line in [note[i:i+105] for i in range(0,len(note),105)]:
        pdf.drawString(20*mm,y,line); y-=4.5*mm

    pdf.save()
    buf.seek(0)
    return Response(buf.getvalue(),mimetype="application/pdf",
                    headers={"Content-Disposition":"attachment; filename=pulseguard_monitoring_report.pdf"})


@app.post("/api/reset")
def reset():
    u=current_user()
    if not u:return jsonify(error="Login required"),401
    c=con(); c.execute("DELETE FROM readings WHERE user_id=?",(u[0],)); c.execute("DELETE FROM sessions WHERE user_id=?",(u[0],)); c.execute("DELETE FROM notifications WHERE user_id=?",(u[0],)); c.commit(); c.close()
    return jsonify(ok=True)

if __name__=="__main__":
    app.run(host="127.0.0.1",port=int(os.environ.get("PORT","5000")),debug=os.environ.get("PULSEGUARD_DEBUG","0")=="1")
