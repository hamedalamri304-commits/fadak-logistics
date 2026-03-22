#!/usr/bin/env python3
"""
فدك اللوجستية — نظام إدارة الأسطول
PostgreSQL (cloud) + SQLite (local)
"""
from flask import Flask, request, jsonify, send_from_directory, render_template_string, session, redirect
import os, uuid, hashlib, functools

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY','fadak-logistics-2026-xK9mP3qR-secure')

# ═══ DATABASE ════════════════════════════════════════════════
DATABASE_URL = os.environ.get('DATABASE_URL','')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://','postgresql://',1)
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2, psycopg2.extras
    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    def qfetch(conn, sql, p=()):
        sql = sql.replace('?','%s')
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, p); return [dict(r) for r in cur.fetchall()]
    def qfetchone(conn, sql, p=()):
        sql = sql.replace('?','%s')
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, p); r=cur.fetchone(); return dict(r) if r else None
    def qexec(conn, sql, p=()):
        sql = sql.replace('?','%s')
        cur = conn.cursor(); cur.execute(sql, p); return cur
else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__),'fadak.db')
    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row; return conn
    def qfetch(conn, sql, p=()):
        return [dict(r) for r in conn.execute(sql,p).fetchall()]
    def qfetchone(conn, sql, p=()):
        r = conn.execute(sql,p).fetchone(); return dict(r) if r else None
    def qexec(conn, sql, p=()):
        return conn.execute(sql, p)

# ═══ USERS ═══════════════════════════════════════════════════
USERS = {
    'admin':   hashlib.sha256(os.environ.get('ADMIN_PASS','fadak2026').encode()).hexdigest(),
    'manager': hashlib.sha256(os.environ.get('MANAGER_PASS','manager123').encode()).hexdigest(),
}
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @functools.wraps(f)
    def wrap(*a,**kw):
        if not session.get('logged_in'):
            return jsonify({'error':'unauthorized'}),401 if request.path.startswith('/api/') else redirect('/login')
        return f(*a,**kw)
    return wrap

# ═══ INIT DB ══════════════════════════════════════════════════
def init_db():
    conn = get_db()
    if USE_PG:
        qexec(conn,"""CREATE TABLE IF NOT EXISTS vehicles(
            id TEXT PRIMARY KEY, plate TEXT NOT NULL UNIQUE,
            driver TEXT NOT NULL, salary REAL DEFAULT 250,
            housing REAL DEFAULT 25, tare INTEGER DEFAULT 26320,
            type TEXT DEFAULT 'MAN', created_at TIMESTAMP DEFAULT NOW())""")
        qexec(conn,"""CREATE TABLE IF NOT EXISTS trips(
            id TEXT PRIMARY KEY, date TEXT NOT NULL, invoice TEXT NOT NULL,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id),
            tons REAL NOT NULL, price REAL DEFAULT 0.40, total REAL NOT NULL,
            source TEXT DEFAULT 'RADOA', created_at TIMESTAMP DEFAULT NOW())""")
        qexec(conn,"""CREATE TABLE IF NOT EXISTS diesel(
            id TEXT PRIMARY KEY, date TEXT NOT NULL,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id),
            liters REAL NOT NULL, price_per_liter REAL DEFAULT 0.258,
            cost REAL NOT NULL, created_at TIMESTAMP DEFAULT NOW())""")
    else:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles(id TEXT PRIMARY KEY,plate TEXT NOT NULL UNIQUE,
        driver TEXT NOT NULL,salary REAL DEFAULT 250,housing REAL DEFAULT 25,
        tare INTEGER DEFAULT 26320,type TEXT DEFAULT 'MAN',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS trips(id TEXT PRIMARY KEY,date TEXT NOT NULL,invoice TEXT NOT NULL,
        vehicle_id TEXT NOT NULL,tons REAL NOT NULL,price REAL DEFAULT 0.40,total REAL NOT NULL,
        source TEXT DEFAULT 'RADOA',created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(vehicle_id) REFERENCES vehicles(id));
        CREATE TABLE IF NOT EXISTS diesel(id TEXT PRIMARY KEY,date TEXT NOT NULL,
        vehicle_id TEXT NOT NULL,liters REAL NOT NULL,price_per_liter REAL DEFAULT 0.258,
        cost REAL NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(vehicle_id) REFERENCES vehicles(id));""")
    conn.commit()
    if not qfetchone(conn,"SELECT 1 FROM vehicles LIMIT 1"):
        seed_data(conn)
    conn.close()

def uid(): return str(uuid.uuid4())[:8]

def seed_data(conn):
    for v in [('v1','2788 RH','تصور حسين',250,25,26320,'MAN'),
               ('v2','3843/DY','جمشيد علي',250,25,26320,'MAN'),
               ('v3','1033 YD','علي رازا',  250,25,27110,'MAN')]:
        qexec(conn,"INSERT INTO vehicles(id,plate,driver,salary,housing,tare,type) VALUES(?,?,?,?,?,?,?)",v)
    trips=[
        ('2026-03-01','115324','v1',82.82),('2026-03-01','115377','v1',86.22),('2026-03-01','115403','v1',80.94),('2026-03-01','115352','v1',81.98),
        ('2026-03-02','115438','v1',80.74),('2026-03-02','115455','v1',84.68),('2026-03-03','15502','v1',85.98),('2026-03-03','115484','v1',83.68),
        ('2026-03-03','115548','v1',77.34),('2026-03-03','115521','v1',87.84),('2026-03-04','115578','v1',87.42),('2026-03-04','115588','v1',87.72),
        ('2026-03-04','115610','v1',83.22),('2026-03-04','115575','v1',82.12),('2026-03-04','115600','v1',86.70),('2026-03-04','115626','v1',88.36),
        ('2026-03-05','39564','v1',82.21),('2026-03-05','39557','v1',82.51),('2026-03-05','39513','v1',79.40),('2026-03-05','39529','v1',83.84),
        ('2026-03-05','39562','v1',87.28),('2026-03-05','39524','v1',82.98),('2026-03-05','39544','v1',83.41),('2026-03-07','115752','v1',82.22),
        ('2026-03-09','39709','v1',89.37),('2026-03-09','39703','v1',89.01),('2026-03-09','39694','v1',86.48),('2026-03-09','39685','v1',89.80),
        ('2026-03-10','39773','v1',83.42),('2026-03-10','39739','v1',88.35),('2026-03-10','39752','v1',86.61),('2026-03-10','39716','v1',79.39),
        ('2026-03-10','39766','v1',86.26),('2026-03-11','39800','v1',86.63),('2026-03-11','39805','v1',82.35),('2026-03-11','39779','v1',87.36),
        ('2026-03-11','39788','v1',81.64),('2026-03-11','39774','v1',85.81),('2026-03-12','39854','v1',8.69),('2026-03-12','39842','v1',84.99),
        ('2026-03-12','39834','v1',80.31),('2026-03-12','39813','v1',90.50),('2026-03-12','39820','v1',83.30),('2026-03-14','39861','v1',82.42),
        ('2026-03-14','39864','v1',79.06),('2026-03-14','39857','v1',89.23),('2026-03-14','39875','v1',82.57),('2026-03-14','39869','v1',81.75),
        ('2026-03-14','39878','v1',87.27),('2026-03-15','39883','v1',85.25),('2026-03-15','39893','v1',88.63),('2026-03-15','39900','v1',86.60),
        ('2026-03-15','39911','v1',81.96),('2026-03-16','INV99','v1',84.67),('2026-03-16','INV100','v1',83.57),('2026-03-16','INV101','v1',83.51),
        ('2026-03-16','INV102','v1',84.82),('2026-03-17','INV103','v1',77.98),('2026-03-17','INV104','v1',84.40),('2026-03-17','INV105','v1',78.42),
        ('2026-03-17','INV106','v1',82.34),
        ('2026-03-01','115374','v2',80.94),('2026-03-01','115398','v2',78.24),('2026-03-01','115349','v2',82.44),('2026-03-01','115319','v2',71.82),
        ('2026-03-02','115447','v2',76.92),('2026-03-02','115424','v2',81.60),('2026-03-03','115516','v2',81.26),('2026-03-03','115479','v2',77.40),
        ('2026-03-03','115496','v2',79.30),('2026-03-04','115576','v2',76.66),('2026-03-04','115603','v2',87.12),('2026-03-04','115591','v2',86.52),
        ('2026-03-04','115581','v2',84.60),('2026-03-04','115569','v2',72.26),('2026-03-04','115614','v2',88.60),('2026-03-04','115627','v2',78.52),
        ('2026-03-05','115633','v2',87.62),('2026-03-05','115648','v2',85.76),('2026-03-05','39561','v2',84.73),('2026-03-05','39545','v2',85.42),
        ('2026-03-05','39532','v2',86.55),('2026-03-05','39554','v2',85.29),('2026-03-09','39704','v2',82.67),('2026-03-10','39730','v2',87.99),
        ('2026-03-10','39769','v2',74.27),('2026-03-10','39713','v2',77.54),('2026-03-10','39746','v2',85.55),('2026-03-10','39757','v2',86.39),
        ('2026-03-11','39803','v2',86.77),('2026-03-11','39799','v2',84.93),('2026-03-11','39788b','v2',82.69),('2026-03-12','39821','v2',76.72),
        ('2026-03-12','39835','v2',79.75),('2026-03-12','39843','v2',81.35),('2026-03-12','39853','v2',78.15),('2026-03-14','39863','v2',78.94),
        ('2026-03-14','39859','v2',86.08),('2026-03-14','39856','v2',87.21),('2026-03-14','39876','v2',79.98),('2026-03-14','39871','v2',78.88),
        ('2026-03-14','39865','v2',84.00),('2026-03-15','39898','v2',89.46),('2026-03-15','39890','v2',83.32),('2026-03-15','39908','v2',83.79),
        ('2026-03-15','39882','v2',82.42),
        ('2026-03-01','115365','v3',87.36),('2026-03-01','115407','v3',78.36),('2026-03-01','115438b','v3',84.00),('2026-03-01','115432','v3',82.68),
        ('2026-03-02','115459','v3',84.68),('2026-03-02','115440','v3',87.90),('2026-03-03','115553','v3',84.86),('2026-03-03','115625','v3',85.78),
        ('2026-03-03','115510','v3',84.06),('2026-03-03','115430','v3',80.38),('2026-03-04','115620','v3',90.44),('2026-03-04','115584','v3',87.14),
        ('2026-03-04','115577','v3',84.46),('2026-03-04','115606','v3',84.70),('2026-03-04','115596','v3',88.10),('2026-03-04','115572','v3',80.72),
        ('2026-03-05','39558','v3',86.73),('2026-03-05','39515','v3',80.78),('2026-03-05','39565','v3',77.19),('2026-03-05','39525','v3',83.11),
        ('2026-03-05','39540','v3',86.00),('2026-03-05','39548','v3',85.70),('2026-03-05','39563','v3',85.43),('2026-03-09','39705','v3',92.21),
        ('2026-03-09','39711','v3',92.35),('2026-03-10','39772','v3',79.59),('2026-03-10','39717','v3',88.81),('2026-03-10','39764','v3',87.36),
        ('2026-03-10','39751','v3',92.04),('2026-03-10','39731','v3',91.27),('2026-03-12','39830','v3',78.98),('2026-03-12','39822','v3',77.77),
        ('2026-03-12','39845','v3',83.64),('2026-03-12','39854b','v3',82.98),('2026-03-12','39614','v3',92.61),('2026-03-14','116988','v3',82.76),
        ('2026-03-14','39874','v3',84.42),('2026-03-14','39882b','v3',88.36),('2026-03-14','39866','v3',74.67),('2026-03-14','39858b','v3',86.24),
        ('2026-03-14','39879','v3',82.76),('2026-03-15','39905','v3',87.74),('2026-03-15','39904','v3',84.20),('2026-03-15','39884','v3',86.24),
        ('2026-03-15','39912','v3',82.05),('2026-03-16','39929','v3',76.12),('2026-03-16','39956','v3',84.59),('2026-03-16','39921','v3',92.26),
        ('2026-03-16','39928','v3',82.40),('2026-03-16','39943','v3',58.23),('2026-03-17','39950','v3',78.11),('2026-03-17','39943b','v3',78.20),
        ('2026-03-17','39954','v3',81.13),('2026-03-17','39961','v3',81.10),('2026-03-18','39968','v3',78.32),('2026-03-18','39983','v3',79.32),
        ('2026-03-18','39977','v3',81.38),('2026-03-18','39986','v3',83.85),
    ]
    for date,inv,vid,tons in trips:
        qexec(conn,"INSERT INTO trips(id,date,invoice,vehicle_id,tons,price,total) VALUES(?,?,?,?,?,?,?)",
              (uid(),date,inv,vid,tons,0.40,round(tons*0.40,2)))
    for vid,date,liters,cost in [
        ('v1','2026-03-03',306.83,79.160),('v1','2026-03-07',278.14,71.760),
        ('v1','2026-03-10',242.55,62.580),('v1','2026-03-11',187.58,48.400),
        ('v1','2026-03-14',293.02,75.600),('v1','2026-03-16',334.04,86.180),('v1','2026-03-17',136.08,35.110),
        ('v2','2026-03-03',350.03,90.310),('v2','2026-03-04',218.76,56.440),
        ('v2','2026-03-09',424.83,109.610),('v2','2026-03-11',433.53,111.850),
        ('v2','2026-03-12',212.37,54.790),('v2','2026-03-15',388.51,100.240),
        ('v3','2026-03-01',300.09,77.423),('v3','2026-03-05',251.82,64.970),
        ('v3','2026-03-05',498.03,128.492),('v3','2026-03-10',175.03,45.158),
        ('v3','2026-03-12',230.01,59.343),('v3','2026-03-15',300.24,77.462),('v3','2026-03-17',370.61,95.617),
    ]:
        qexec(conn,"INSERT INTO diesel(id,date,vehicle_id,liters,price_per_liter,cost) VALUES(?,?,?,?,?,?)",
              (uid(),date,vid,liters,round(cost/liters,4),cost))
    conn.commit()

# ═══ LOGIN PAGE ═══════════════════════════════════════════════
LOGIN_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>فدك اللوجستية — دخول</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Tajawal:wght@700;900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Cairo',sans-serif;background:#0B1E3D;min-height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative}
body::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 25% 50%,rgba(10,123,106,.22) 0%,transparent 55%),radial-gradient(ellipse at 75% 30%,rgba(200,148,15,.1) 0%,transparent 50%)}
canvas{position:absolute;inset:0;pointer-events:none}
.box{background:rgba(255,255,255,.05);backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);border:1px solid rgba(255,255,255,.12);border-radius:24px;padding:52px 44px;width:420px;max-width:95vw;position:relative;box-shadow:0 40px 100px rgba(0,0,0,.6)}
.top{text-align:center;margin-bottom:40px}
.ico{font-size:52px;display:block;margin-bottom:14px;animation:bob 3s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
h1{font-family:'Tajawal';font-size:26px;font-weight:900;color:#fff;margin-bottom:6px}
.sub{font-size:11px;color:rgba(255,255,255,.38);letter-spacing:.8px}
.pill{display:inline-flex;align-items:center;gap:7px;background:rgba(10,123,106,.35);border:1px solid rgba(13,158,136,.6);color:rgba(255,255,255,.8);font-size:10px;padding:5px 16px;border-radius:20px;margin-top:12px}
.pulse{width:7px;height:7px;background:#0D9E88;border-radius:50%;animation:p 2s infinite}
@keyframes p{0%,100%{opacity:.3;transform:scale(.8)}50%{opacity:1;transform:scale(1)}}
.fg{margin-bottom:22px}
.fg label{display:block;font-size:10px;font-weight:700;color:rgba(255,255,255,.45);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:9px}
.fg input{width:100%;padding:14px 18px;background:rgba(255,255,255,.07);border:1.5px solid rgba(255,255,255,.1);border-radius:12px;font-family:'Cairo';font-size:14px;color:#fff;transition:.25s;text-align:right}
.fg input:focus{outline:none;border-color:#0D9E88;background:rgba(13,158,136,.1);box-shadow:0 0 0 4px rgba(13,158,136,.15)}
.fg input::placeholder{color:rgba(255,255,255,.18)}
.btn{width:100%;padding:15px;background:linear-gradient(135deg,#0A7B6A,#0F9E8A);border:none;border-radius:12px;font-family:'Cairo';font-size:15px;font-weight:700;color:#fff;cursor:pointer;transition:.25s;margin-top:4px;letter-spacing:.5px;box-shadow:0 4px 20px rgba(10,123,106,.3)}
.btn:hover{transform:translateY(-2px);box-shadow:0 10px 32px rgba(10,123,106,.5)}
.btn:active{transform:translateY(0)}
.err{background:rgba(192,57,43,.12);border:1px solid rgba(192,57,43,.4);border-radius:10px;padding:12px;color:#FF8A80;font-size:12px;text-align:center;margin-bottom:20px}
.foot{text-align:center;margin-top:30px;font-size:10px;color:rgba(255,255,255,.15);letter-spacing:.5px}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div class="box">
  <div class="top">
    <span class="ico">🚛</span>
    <h1>فدك اللوجستية</h1>
    <div class="sub">FADAK LOGISTICS · FLEET MANAGEMENT</div>
    <div class="pill"><span class="pulse"></span>Contract E2310 · ABU HAFIDH INT.</div>
  </div>
  {% if error %}<div class="err">⚠️ {{ error }}</div>{% endif %}
  <form method="POST" action="/login">
    <div class="fg">
      <label>اسم المستخدم</label>
      <input type="text" name="username" placeholder="username" required autofocus autocomplete="username">
    </div>
    <div class="fg">
      <label>كلمة المرور</label>
      <input type="password" name="password" placeholder="••••••••" required autocomplete="current-password">
    </div>
    <button type="submit" class="btn">🔐 &nbsp; تسجيل الدخول</button>
  </form>
  <div class="foot">نظام محمي وآمن · جميع الحقوق محفوظة 2026</div>
</div>
<script>
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
let W,H,stars=[];
function resize(){W=cv.width=innerWidth;H=cv.height=innerHeight;stars=[];
  for(let i=0;i<160;i++) stars.push({x:Math.random()*W,y:Math.random()*H,
    r:Math.random()*1.2+.2,a:Math.random(),da:Math.random()*.004+.001});}
function draw(){ctx.clearRect(0,0,W,H);
  stars.forEach(s=>{s.a+=s.da;if(s.a>1||s.a<0)s.da*=-1;
    ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);
    ctx.fillStyle=`rgba(255,255,255,${s.a*.5})`;ctx.fill();});
  requestAnimationFrame(draw);}
resize();draw();window.addEventListener('resize',resize);
</script>
</body>
</html>"""

# ═══ AUTH ═════════════════════════════════════════════════════
@app.route('/login', methods=['GET','POST'])
def login():
    err = None
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','')
        if u in USERS and USERS[u] == hash_pw(p):
            session['logged_in'] = True
            session['username']  = u
            return redirect('/')
        err = 'اسم المستخدم أو كلمة المرور غير صحيحة'
    return render_template_string(LOGIN_HTML, error=err)

@app.route('/logout')
def logout():
    session.clear(); return redirect('/login')

# ═══ MAIN INDEX ════════════════════════════════════════════════
@app.route('/')
@login_required
def index():
    return send_from_directory(os.path.dirname(__file__),'index.html')

# ═══ API ══════════════════════════════════════════════════════
@app.route('/api/vehicles', methods=['GET'])
@login_required
def api_vehicles_get():
    conn=get_db()
    vlist=qfetch(conn,"SELECT * FROM vehicles ORDER BY plate")
    for v in vlist:
        td=qfetchone(conn,"SELECT COUNT(*) as cnt,SUM(total) as rev FROM trips WHERE vehicle_id=?",(v['id'],))
        dd=qfetchone(conn,"SELECT SUM(cost) as dc FROM diesel WHERE vehicle_id=?",(v['id'],))
        v['trip_count']=td['cnt'] or 0
        v['revenue']=round(td['rev'] or 0,2)
        v['diesel_cost']=round(dd['dc'] or 0,3)
        v['net_revenue']=round(v['revenue']-v['diesel_cost'],2)
    conn.close(); return jsonify(vlist)

@app.route('/api/vehicles', methods=['POST'])
@login_required
def api_vehicles_post():
    d=request.json; conn=get_db()
    vid='v'+str(uuid.uuid4())[:6]
    qexec(conn,"INSERT INTO vehicles(id,plate,driver,salary,housing,tare,type) VALUES(?,?,?,?,?,?,?)",
          (vid,d['plate'],d['driver'],d.get('salary',250),d.get('housing',25),d.get('tare',26320),d.get('type','MAN')))
    conn.commit(); conn.close(); return jsonify({'ok':True,'id':vid})

@app.route('/api/vehicles/<vid>', methods=['PUT'])
@login_required
def api_vehicles_put(vid):
    d=request.json; conn=get_db()
    qexec(conn,"UPDATE vehicles SET driver=?,salary=?,housing=?,tare=?,type=? WHERE id=?",
          (d['driver'],d['salary'],d['housing'],d['tare'],d.get('type','MAN'),vid))
    conn.commit(); conn.close(); return jsonify({'ok':True})

@app.route('/api/vehicles/<vid>', methods=['DELETE'])
@login_required
def api_vehicles_del(vid):
    conn=get_db(); qexec(conn,"DELETE FROM vehicles WHERE id=?",(vid,))
    conn.commit(); conn.close(); return jsonify({'ok':True})

@app.route('/api/trips', methods=['GET'])
@login_required
def api_trips_get():
    conn=get_db()
    vid=request.args.get('vehicle_id',''); date=request.args.get('date','')
    q="SELECT t.*,v.plate,v.driver FROM trips t JOIN vehicles v ON t.vehicle_id=v.id WHERE 1=1"
    p=[]
    if vid: q+=" AND t.vehicle_id=?"; p.append(vid)
    if date: q+=" AND t.date=?"; p.append(date)
    q+=" ORDER BY t.date,t.invoice"
    r=qfetch(conn,q,p); conn.close(); return jsonify(r)

@app.route('/api/trips', methods=['POST'])
@login_required
def api_trips_post():
    d=request.json; conn=get_db()
    tid=uid(); tons=round(float(d['tons']),2); total=round(tons*0.40,2)
    qexec(conn,"INSERT INTO trips(id,date,invoice,vehicle_id,tons,price,total,source) VALUES(?,?,?,?,?,?,?,?)",
          (tid,d['date'],d['invoice'],d['vehicle_id'],tons,0.40,total,d.get('source','RADOA')))
    if d.get('diesel_liters') and float(d['diesel_liters'])>0:
        l=float(d['diesel_liters']); p=float(d.get('diesel_price',0.258))
        qexec(conn,"INSERT INTO diesel(id,date,vehicle_id,liters,price_per_liter,cost) VALUES(?,?,?,?,?,?)",
              (uid(),d['date'],d['vehicle_id'],l,p,round(l*p,3)))
    conn.commit(); conn.close(); return jsonify({'ok':True,'id':tid,'total':total})

@app.route('/api/trips/<tid>', methods=['DELETE'])
@login_required
def api_trips_del(tid):
    conn=get_db(); qexec(conn,"DELETE FROM trips WHERE id=?",(tid,))
    conn.commit(); conn.close(); return jsonify({'ok':True})

@app.route('/api/diesel', methods=['GET'])
@login_required
def api_diesel_get():
    conn=get_db(); vid=request.args.get('vehicle_id','')
    q="SELECT d.*,v.plate FROM diesel d JOIN vehicles v ON d.vehicle_id=v.id WHERE 1=1"
    p=[]
    if vid: q+=" AND d.vehicle_id=?"; p.append(vid)
    r=qfetch(conn,q+' ORDER BY d.date',p); conn.close(); return jsonify(r)

@app.route('/api/diesel', methods=['POST'])
@login_required
def api_diesel_post():
    d=request.json; l=float(d['liters']); p=float(d.get('price_per_liter',0.258))
    cost=round(l*p,3); conn=get_db()
    qexec(conn,"INSERT INTO diesel(id,date,vehicle_id,liters,price_per_liter,cost) VALUES(?,?,?,?,?,?)",
          (uid(),d['date'],d['vehicle_id'],l,p,cost))
    conn.commit(); conn.close(); return jsonify({'ok':True,'cost':cost})

@app.route('/api/diesel/<did>', methods=['DELETE'])
@login_required
def api_diesel_del(did):
    conn=get_db(); qexec(conn,"DELETE FROM diesel WHERE id=?",(did,))
    conn.commit(); conn.close(); return jsonify({'ok':True})

@app.route('/api/stats')
@login_required
def api_stats():
    conn=get_db()
    r1=qfetchone(conn,"SELECT SUM(total) as rev,COUNT(*) as cnt FROM trips")
    r2=qfetchone(conn,"SELECT SUM(cost) as dc FROM diesel")
    daily=qfetch(conn,"SELECT date,vehicle_id,COUNT(*) as trips,SUM(total) as rev FROM trips GROUP BY date,vehicle_id ORDER BY date")
    conn.close()
    tv=r1['rev'] or 0; td=r2['dc'] or 0
    return jsonify({'total_revenue':round(tv,2),'total_trips':r1['cnt'] or 0,
                    'total_diesel':round(td,3),'net_revenue':round(tv-td,2),'daily':daily})

@app.route('/api/salary')
@login_required
def api_salary():
    conn=get_db()
    vlist=qfetch(conn,"SELECT * FROM vehicles"); res=[]
    for v in vlist:
        rows=qfetch(conn,"SELECT date,COUNT(*) as n FROM trips WHERE vehicle_id=? GROUP BY date",(v['id'],))
        daily={r['date']:r['n'] for r in rows}
        bonus=sum(_bonus(n) for n in daily.values())
        res.append({'vehicle':v,'trip_count':sum(daily.values()),'work_days':len(daily),
                    'bonus':bonus,'net_salary':v['salary']+v['housing']+bonus,'daily':daily})
    conn.close(); return jsonify(res)

def _bonus(n):
    b=0
    for i in range(2,n+1): b+=2 if i<=5 else(4 if i==6 else(5 if i==7 else 0))
    return b

# ═══ RUN ══════════════════════════════════════════════════════
if __name__=='__main__':
    init_db()
    db_mode="PostgreSQL ☁️" if USE_PG else "SQLite 💾 (local)"
    print(f"\n{'═'*52}")
    print(f"  🚛  فدك اللوجستية — Fleet System")
    print(f"  🗄️   DB: {db_mode}")
    print(f"  🌐  http://localhost:{os.environ.get('PORT',5000)}")
    print(f"{'═'*52}\n")
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=False)
