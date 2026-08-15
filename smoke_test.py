import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from backend.app import app
c=app.test_client()
assert c.get('/api/health').status_code == 200
assert c.get('/api/health').get_json()['database'] == 'ok'
assert c.post('/api/auth/login', json={'username':'demo','password':'pulse123'}).status_code == 200
assert c.post('/api/predict', json={'history':[75]*10,'session_id':'smoke'}).status_code == 200
high=c.post('/api/predict', json={'history':[75,76,77,78,79,80,81,82,85,110],'session_id':'smoke'}).get_json()
assert high['rule_status']=='HIGH'
assert high['alert'] is True
assert c.get('/api/notifications').status_code == 200
assert c.get('/api/analytics').status_code == 200
assert c.get('/api/report.pdf').status_code == 200
print('PulseGuard FINAL smoke test: PASS')
