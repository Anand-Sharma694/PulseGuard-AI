from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app import app

def client():
    c=app.test_client(); assert c.post('/api/auth/login',json={'username':'demo','password':'pulse123'}).status_code==200; return c

def test_health():
    r=client().get('/api/health'); assert r.status_code==200; assert r.get_json()['database']=='ok'

def test_normal_prediction_is_not_threshold_alert():
    r=client().post('/api/predict',json={'history':[75]*10,'session_id':'t-normal'})
    assert r.status_code==200; d=r.get_json(); assert d['rule_status']=='NORMAL'; assert d['alert'] is False

def test_high_prediction_creates_alert():
    r=client().post('/api/predict',json={'history':[75,76,77,78,79,80,81,82,85,110],'session_id':'t-high'})
    assert r.status_code==200; d=r.get_json(); assert d['rule_status']=='HIGH'; assert d['alert'] is True

def test_low_prediction_creates_alert():
    r=client().post('/api/predict',json={'history':[75,76,77,78,79,80,81,82,75,55],'session_id':'t-low'})
    assert r.status_code==200; assert r.get_json()['rule_status']=='LOW'

def test_notifications_and_reports():
    c=client(); assert c.get('/api/notifications').status_code==200; assert c.get('/api/analytics').status_code==200; assert c.get('/api/report.pdf').mimetype=='application/pdf'; assert c.get('/api/export.csv').status_code==200
