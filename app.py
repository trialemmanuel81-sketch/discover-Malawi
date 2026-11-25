# ==========================================================
# DISCOVER MALAWI - ALL-IN-ONE WEBSITE + ADMIN + DATABASE
# FIXED VERSION - All 4 Improvements
# Install: pip install flask
# Run:     python app.py
# ==========================================================
import os
import sqlite3
import secrets
import hmac
from datetime import date
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, abort, send_file

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not app.secret_key or not ADMIN_PASSWORD:
    raise RuntimeError("Set SECRET_KEY and ADMIN_PASSWORD env vars before starting.")

DB = "discover_malawi.db"
OWNER_EMAIL = "trialemmanuel81@gmail.com"
OWNER_PHONE = "0997148648"
OWNER_WHATSAPP = "265997148648"
OWNER_ADDRESS = "Post Office Box 184, Luncheza, Thyolo, Malawi"
OWNER_NAME = "Trial Emmanuel"

# --- DATABASE (same as before) ---
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS businesses(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT NOT NULL,
        location TEXT NOT NULL, phone TEXT, email TEXT, description TEXT, image TEXT,
        package TEXT DEFAULT 'Basic', price INTEGER DEFAULT 0, approved INTEGER DEFAULT 0,
        featured INTEGER DEFAULT 0, payment_status TEXT DEFAULT 'Unpaid',
        payment_reference TEXT, expiry_date TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    con.execute("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT, business_id INTEGER, business_name TEXT,
        amount INTEGER NOT NULL, reference TEXT, payment_date TEXT, notes TEXT,
        FOREIGN KEY(business_id) REFERENCES businesses(id))""")
    con.commit(); con.close()
init_db()

def csrf_token():
    if "csrf" not in session: session["csrf"] = secrets.token_hex(24)
    return session["csrf"]
def check_csrf():
    if request.form.get("csrf") != session.get("csrf"): abort(400, "Invalid form token.")
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"): return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper
def clean(v, limit=2000): return (v or "").strip()[:limit]
def expired(expiry):
    if not expiry: return False
    try: return date.fromisoformat(expiry) < date.today()
    except ValueError: return False
def package_price(p): return {"Basic":10000,"Featured":25000,"Premium":50000}.get(p,0)
def listing_active(r): return r["approved"]==1 and not expired(r["expiry_date"])

BASE_STYLE = """
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:#f4f6f1;color:#18251e;line-height:1.55}
header{background:#063c35;color:white;padding:15px 4%;display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}
.logo{font-weight:900;font-size:23px;color:white;text-decoration:none}.logo span{color:#e9b64d}
nav a{color:white;text-decoration:none;margin:0 8px;font-weight:bold}
main{width:min(1150px,94%);margin:auto;padding:30px 0}button,.btn{display:inline-block;border:0;border-radius:9px;padding:11px 17px;background:#063c35;color:white;text-decoration:none;font-weight:bold;cursor:pointer}
.gold{background:#e9b64d;color:#17251e}input,select,textarea{width:100%;padding:12px;border:1px solid #d5ddd5;border-radius:9px;margin:5px 0 13px;font:inherit}
.card{background:white;padding:20px;border-radius:15px;margin-bottom:18px;box-shadow:0 5px 20px #00000008}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.stat{background:white;padding:20px;border-radius:14px}.stat b{font-size:28px;color:#0c5a4b}
table{width:100%;border-collapse:collapse;background:white}th,td{text-align:left;padding:12px;border-bottom:1px solid #e7ece7}th{background:#e8efe9}
.small{font-size:13px;color:#68746d}.badge{display:inline-block;padding:4px 9px;border-radius:20px;background:#e8efe9;color:#0c5a4b;font-size:12px;font-weight:bold}
.featured{background:#fff2ce;color:#855b12}.warning{background:#fff2d4;padding:13px;border-radius:10px}
footer{text-align:center;background:#063c35;color:white;padding:25px}
.hero{background:linear-gradient(90deg,#03231fdd,#03231f66),url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=85') center/cover;color:white;padding:90px 5%;border-radius:18px}
.hero h1{font-size:clamp(35px,6vw,68px);max-width:750px}.hero p{font-size:18px;max-width:650px}
.business img{height:190px;width:100%;object-fit:cover;border-radius:12px}
.searchrow{display:flex;gap:10px}.searchrow input{flex:1}.paybox{background:#fff8e1;border:1px solid #e9b64d;padding:15px;border-radius:12px}
@media(max-width:800px){.grid{grid-template-columns:repeat(2,1fr)}.stats{grid-template-columns:repeat(2,1fr)}}
@media(max-width:600px){.grid,.stats{grid-template-columns:1fr}.searchrow{display:block}}
"""

PUBLIC_TEMPLATE = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Discover Malawi - Tourism</title><style>{{style}}</style></head><body>
<header><a class="logo" href="/">DISCOVER <span>MALAWI</span></a>
<nav><a href="/">Home</a><a href="#destinations">Destinations</a><a href="#directory">Businesses</a><a href="#advertise">Advertise</a><a href="#contact">Contact</a></nav></header>
<main>
<section class="hero"><div class="badge">🇲🇼 THE WARM HEART OF AFRICA</div>
<h1>Discover the beauty of Malawi.</h1><p>Explore lakes, mountains, wildlife, culture and unforgettable adventures.</p>
<a class="btn gold" href="#destinations">Explore Malawi</a> <a class="btn" href="#directory">Find Businesses</a></section>

<section id="destinations"><h2>Explore Real Malawi Destinations</h2><div class="grid">
<div class="card business"><img src="https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=800&q=80"><h3>🏖️ Lake Malawi - Mangochi & Cape Maclear</h3><p>Crystal clear water, white sand beaches, snorkelling, kayaking and island trips to Mumbo Island. Best for honeymoon and family holidays.</p></div>
<div class="card business"><img src="https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80"><h3>⛰️ Mount Mulanje</h3><p>Malawi's highest mountain (3,002m). Hiking, waterfalls, Sapitwa Peak, tea estates at the foot. Guides and porters available in Mulanje town.</p></div>
<div class="card business"><img src="https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?auto=format&fit=crop&w=800&q=80"><h3>🦁 Nyika National Park</h3><p>Rolling grasslands, zebras, leopards, orchids and the highest national park in Malawi. Perfect for safari and mountain biking.</p></div>
<div class="card business"><img src="https://images.unsplash.com/photo-1549366021-9f761d450615?auto=format&fit=crop&w=800&q=80"><h3>🐘 Liwonde National Park</h3><p>Elephants, hippos, crocodiles and bird watching on the Shire River. Boat safaris and game drives from Liwonde town.</p></div>
<div class="card business"><img src="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=800&q=80"><h3>🌲 Zomba Plateau</h3><p>Cool forests, trout fishing, horse riding, waterfalls and views over Zomba town. Great for hiking and camping.</p></div>
<div class="card business"><img src="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=800&q=80"><h3>🍃 Thyolo Tea Estates - Luchenza</h3><p>Endless green tea fields, Satemwa Tea Estate tours, tasting, and scenic drives. Visit the home of Malawi tea near Luchenza, Thyolo.</p></div>
</div></section>

<section id="directory"><h2>Tourism Business Directory</h2>
<form class="searchrow" method="get" action="/"><input name="q" value="{{q}}" placeholder="Search business, town or service">
<select name="category"><option value="">All categories</option>{% for cat in categories %}<option value="{{cat}}" {% if category==cat %}selected{% endif %}>{{cat}}</option>{% endfor %}</select><button>Search</button></form>
<div class="grid">{% for b in businesses %}<div class="card business">
{% if b.image %}<img src="{{b.image}}">{% endif %}{% if b.featured %}<span class="badge featured">⭐ Featured</span>{% endif %}
<h3>{{b.name}}</h3><p><b>{{b.category}}</b></p><p>📍 {{b.location}}</p><p>{{b.description}}</p>
{% if b.phone %}<a class="btn" href="https://wa.me/{{b.phone|replace('+','')|replace(' ','')}}?text=Hello%20I%20found%20you%20on%20Discover%20Malawi" target="_blank">WhatsApp Business</a>{% endif %}</div>{% endfor %}</div>
{% if not businesses %}<div class="card">No businesses found. Try another search.</div>{% endif %}</section>

<section id="advertise" class="card"><h2>Promote Your Tourism Business</h2>
<div class="grid"><div><h3>Basic</h3><b>MWK 10,000/month</b><p>Standard listing</p></div><div><h3>Featured ⭐</h3><b>MWK 25,000/month</b><p>Top of search + Featured badge</p></div><div><h3>Premium 👑</h3><b>MWK 50,000/month</b><p>Top + Featured + Priority WhatsApp</p></div></div>

<div class="paybox"><h3>💳 How to Pay - Airtel Money / TNM Mpamba</h3>
<p><b>Step 1:</b> Fill the form below and submit.<br>
<b>Step 2:</b> Send payment to:<br>
<b>Airtel Money:</b> 0997148648 (Trial Emmanuel)<br>
<b>TNM Mpamba:</b> 0997148648 (Trial Emmanuel)<br>
<b>Step 3:</b> Send screenshot + your business name on WhatsApp: <a href="https://wa.me/265997148648">0997148648</a><br>
<b>Step 4:</b> We approve your listing within 24 hours after payment.</p>
<p class="small">Keep your transaction reference / SMS. No refund after listing is published.</p></div>

<h3>Business Application</h3>
<form method="post" action="/submit"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Business Name</label><input name="name" required>
<label>Category</label><select name="category" required><option>Accommodation</option><option>Tour Operator</option><option>Transport</option><option>Restaurant</option><option>Activity</option><option>Other</option></select>
<label>Location</label><input name="location" required>
<label>Phone/WhatsApp</label><input name="phone" required placeholder="265...">
<label>Email</label><input name="email" type="email">
<label>Description</label><textarea name="description" required></textarea>
<label>Image URL (optional)</label><input name="image" placeholder="https://...">
<label>Advertising package</label><select name="package"><option>Basic</option><option>Featured</option><option>Premium</option></select>
<button>Submit Application</button></form>
<p class="small">Applications are reviewed before publishing.</p></section>

<section id="contact" class="card"><h2>Contact Discover Malawi</h2>
<p>Email: <a href="mailto:{{owner_email}}">{{owner_email}}</a></p><p>Phone: <a href="tel:+265{{owner_phone}}">+265 {{owner_phone}}</a></p><p>Address: {{owner_address}}</p>
<a class="btn gold" href="https://wa.me/{{owner_whatsapp}}" target="_blank">WhatsApp Discover Malawi</a></section>
</main><footer>DISCOVER MALAWI 🇲🇼<br>Explore • Experience • Discover</footer></body></html>
"""

@app.route("/")
def home():
    q = clean(request.args.get("q"), 100).lower(); category = clean(request.args.get("category"), 100)
    con = db(); rows = con.execute("SELECT * FROM businesses WHERE approved=1 AND (expiry_date IS NULL OR expiry_date >= ?) ORDER BY featured DESC, name ASC", (date.today().isoformat(),)).fetchall(); con.close()
    businesses=[]
    for b in rows:
        text=" ".join([b["name"] or "",b["category"] or "",b["location"] or "",b["description"] or ""]).lower()
        if q and q not in text: continue
        if category and b["category"]!=category: continue
        businesses.append(b)
    categories=["Accommodation","Tour Operator","Transport","Restaurant","Activity","Other"]
    return render_template_string(PUBLIC_TEMPLATE, style=BASE_STYLE, businesses=businesses, categories=categories, q=q, category=category, csrf=csrf_token(), owner_email=OWNER_EMAIL, owner_phone=OWNER_PHONE, owner_whatsapp=OWNER_WHATSAPP, owner_address=OWNER_ADDRESS)

@app.route("/submit", methods=["POST"])
def submit_business():
    check_csrf()
    name=clean(request.form.get("name"),150); category=clean(request.form.get("category"),100); location=clean(request.form.get("location"),150)
    phone=clean(request.form.get("phone"),50); email=clean(request.form.get("email"),150); description=clean(request.form.get("description"),3000)
    image=clean(request.form.get("image"),500); package=clean(request.form.get("package"),50)
    if not name or not location or not phone or not description:
        flash("Please fill in all required fields."); return redirect("/#advertise")
    con=db(); con.execute("INSERT INTO businesses (name,category,location,phone,email,description,image,package,price,approved,featured,payment_status) VALUES(?,?,?,?,?,?,?,?,?,0,0,'Unpaid')", (name,category,location,phone,email,description,image,package,package_price(package))); con.commit(); con.close()
    return """<h2>Application received! ✅</h2><p>Thank you. Now pay via Airtel Money to <b>0997148648</b> and send screenshot on WhatsApp.</p><a href="/">Return to Discover Malawi</a>"""

# --- FIXED ADMIN LOGIN ---
LOGIN_TEMPLATE = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Login</title><style>{{style}}</style></head>
<body><main><div class="card" style="max-width:500px;margin:50px auto"><h1>🔐 Admin Login</h1>
{% for m in get_flashed_messages() %}<p class="warning">{{m}}</p>{% endfor %}
<form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><label>Administrator Password</label><input type="password" name="password" required><button>Login</button></form>
<p><a href="/">Back to public website</a></p></div></main></body></html>"""

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        check_csrf()
        # FIXED: constant-time compare, no re-hashing
        if hmac.compare_digest(request.form.get("password",""), ADMIN_PASSWORD):
            session.clear(); session["admin"]=True; session["csrf"]=secrets.token_hex(24); return redirect(url_for("dashboard"))
        flash("Incorrect password.")
    return render_template_string(LOGIN_TEMPLATE, style=BASE_STYLE, csrf=csrf_token())

@app.route("/admin/logout")
def admin_logout(): session.clear(); return redirect("/")

DASHBOARD_TEMPLATE = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin</title><style>{{style}}</style></head>
<body><header><a class="logo">DISCOVER <span>MALAWI ADMIN</span></a><nav><a href="/">Public Site</a><a href="/admin/logout">Logout</a></nav></header><main>
<h1>Admin Dashboard</h1><div class="stats">
<div class="stat"><span>Total Businesses</span><br><b>{{total}}</b></div><div class="stat"><span>Approved</span><br><b>{{approved}}</b></div>
<div class="stat"><span>Awaiting Review</span><br><b>{{pending}}</b></div><div class="stat"><span>Paid Revenue</span><br><b>MWK {{revenue}}</b></div></div>
<div style="margin:22px 0"><a class="btn" href="#add">➕ Add Business</a> <a class="btn gold" href="/admin/backup">💾 Download Backup</a></div>
<div class="card"><h2>Business Listings</h2><div style="overflow-x:auto"><table><thead><tr><th>Business</th><th>Category</th><th>Package</th><th>Approved</th><th>Payment</th><th>Featured</th><th>Expiry</th><th>Actions</th></tr></thead><tbody>
{% for b in businesses %}<tr><td><b>{{b.name}}</b><br><span class="small">{{b.location}}</span></td><td>{{b.category}}</td><td>{{b.package}}<br>MWK {{b.price}}</td>
<td>{{'Yes' if b.approved else 'No'}}</td><td>{{b.payment_status}}<br>{{b.payment_reference or ''}}</td><td>{{'⭐' if b.featured else '—'}}</td><td>{{b.expiry_date or 'Not set'}}</td><td>
<form method="post" action="/admin/approve/{{b.id}}"><input type="hidden" name="csrf" value="{{csrf}}"><button>{{'Unapprove' if b.approved else 'Approve'}}</button></form>
<form method="post" action="/admin/feature/{{b.id}}"><input type="hidden" name="csrf" value="{{csrf}}"><button class="gold">{{'Unfeature' if b.featured else 'Feature'}}</button></form>
<form method="post" action="/admin/payment/{{b.id}}"><input type="hidden" name="csrf" value="{{csrf}}"><label>Amount</label><input name="amount" type="number" value="{{b.price}}" min="0"><label>Reference</label><input name="reference" value="{{b.payment_reference or ''}}"><label>Expiry</label><input name="expiry" type="date" value="{{b.expiry_date or ''}}"><button>Save Payment</button></form>
<form method="post" action="/admin/delete/{{b.id}}" onsubmit="return confirm('Delete?')"><input type="hidden" name="csrf" value="{{csrf}}"><button style="background:#a52222">Delete</button></form></td></tr>{% endfor %}
</tbody></table></div></div>
<div class="card" id="add"><h2>Add Business Manually</h2><form method="post" action="/admin/add"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Business Name</label><input name="name" required><label>Category</label><select name="category"><option>Accommodation</option><option>Tour Operator</option><option>Transport</option><option>Restaurant</option><option>Activity</option><option>Other</option></select>
<label>Location</label><input name="location" required><label>Phone</label><input name="phone"><label>Email</label><input name="email"><label>Description</label><textarea name="description"></textarea><label>Image URL</label><input name="image"><label>Package</label><select name="package"><option>Basic</option><option>Featured</option><option>Premium</option></select><label>Approve immediately?</label><select name="approved"><option value="1">Yes</option><option value="0">No</option></select><button>Add Business</button></form></div>
<div class="card"><h2>Payment Records</h2><table><thead><tr><th>Date</th><th>Business</th><th>Amount</th><th>Reference</th><th>Notes</th></tr></thead><tbody>{% for p in payments %}<tr><td>{{p.payment_date}}</td><td>{{p.business_name}}</td><td>MWK {{p.amount}}</td><td>{{p.reference}}</td><td>{{p.notes}}</td></tr>{% endfor %}</tbody></table></div>
</main><footer>Discover Malawi Admin Panel</footer></body></html>"""

@app.route("/admin")
@admin_required
def dashboard():
    con=db(); businesses=con.execute("SELECT * FROM businesses ORDER BY created_at DESC").fetchall(); payments=con.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()
    total=len(businesses); approved=sum(1 for b in businesses if listing_active(b)); pending=sum(1 for b in businesses if not b["approved"])
    revenue=con.execute("SELECT COALESCE(SUM(amount),0) FROM payments").fetchone()[0]; con.close()
    return render_template_string(DASHBOARD_TEMPLATE, style=BASE_STYLE, businesses=businesses, payments=payments, total=total, approved=approved, pending=pending, revenue=revenue, csrf=csrf_token())

@app.route("/admin/add", methods=["POST"])
@admin_required
def admin_add():
    check_csrf(); name=clean(request.form.get("name"),150); category=clean(request.form.get("category"),100); location=clean(request.form.get("location"),150)
    phone=clean(request.form.get("phone"),50); email=clean(request.form.get("email"),150); description=clean(request.form.get("description"),3000); image=clean(request.form.get("image"),500); package=clean(request.form.get("package"),50); approved=int(request.form.get("approved","0"))
    con=db(); con.execute("INSERT INTO businesses (name,category,location,phone,email,description,image,package,price,approved) VALUES(?,?,?,?,?,?,?,?,?,?)", (name,category,location,phone,email,description,image,package,package_price(package),approved)); con.commit(); con.close(); flash("Business added."); return redirect("/admin")

@app.route("/admin/approve/<int:business_id>", methods=["POST"])
@admin_required
def admin_approve(business_id):
    check_csrf(); con=db(); row=con.execute("SELECT approved FROM businesses WHERE id=?", (business_id,)).fetchone()
    if row: con.execute("UPDATE businesses SET approved=? WHERE id=?", (0 if row["approved"] else 1, business_id))
    con.commit(); con.close(); return redirect("/admin")

@app.route("/admin/feature/<int:business_id>", methods=["POST"])
@admin_required
def admin_feature(business_id):
    check_csrf(); con=db(); row=con.execute("SELECT featured FROM businesses WHERE id=?", (business_id,)).fetchone()
    if row: con.execute("UPDATE businesses SET featured=? WHERE id=?", (0 if row["featured"] else 1, business_id))
    con.commit(); con.close(); return redirect("/admin")

@app.route("/admin/delete/<int:business_id>", methods=["POST"])
@admin_required
def admin_delete(business_id):
    check_csrf(); con=db(); con.execute("DELETE FROM businesses WHERE id=?", (business_id,)); con.execute("DELETE FROM payments WHERE business_id=?", (business_id,)); con.commit(); con.close(); return redirect("/admin")

@app.route("/admin/payment/<int:business_id>", methods=["POST"])
@admin_required
def admin_payment(business_id):
    check_csrf()
    try: amount=int(request.form.get("amount","0"))
    except ValueError: amount=0
    reference=clean(request.form.get("reference"),150); expiry=clean(request.form.get("expiry"),20)
    con=db(); b=con.execute("SELECT * FROM businesses WHERE id=?", (business_id,)).fetchone()
    if b:
        con.execute("UPDATE businesses SET payment_status='Paid',payment_reference=?,price=?,expiry_date=? WHERE id=?", (reference,amount,expiry or None,business_id))
        if amount>0: con.execute("INSERT INTO payments (business_id,business_name,amount,reference,payment_date,notes) VALUES(?,?,?,?,?,?)", (business_id,b["name"],amount,reference,date.today().isoformat(),"Admin recorded payment"))
    con.commit(); con.close(); return redirect("/admin")

@app.route("/admin/backup")
@admin_required
def backup():
    if not os.path.exists(DB): abort(404)
    return send_file(DB, as_attachment=True, download_name="discover_malawi_backup.db")

@app.errorhandler(400)
def bad_request(e): return "Bad request. Refresh and try again.", 400
@app.errorhandler(404)
def not_found(e): return "Page not found.", 404

if _name_ == '_main_':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
