from flask import Flask, request, redirect, render_template_string
import sqlite3
import string, random
import qrcode
import base64
from io import BytesIO
import os

app = Flask(__name__)

# 🔗 Dual mode
# LOCAL TEST: localhost
# REAL: set REAL_DOMAIN
LOCAL_MODE = True  # True = test on localhost, False = real domain
REAL_DOMAIN = "https://yourtool.com"  # Replace with your .com domain

# Database
def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS links (short TEXT, original TEXT)")
    conn.commit()
    conn.close()

init_db()

# Generate short code
def generate_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Clean UI
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ShortLink Tool</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
*{box-sizing:border-box;}
body{margin:0;font-family:Arial;background:#f1f3f6;}
.container{
    max-width:420px;
    margin:10px auto;
    background:white;
    padding:15px;
    border-radius:8px;
    box-shadow:0 4px 12px rgba(0,0,0,0.1);
    text-align:center;
}
h2{margin:5px 0;}
input{
    width:100%;
    padding:10px;
    border:1px solid #ccc;
    border-radius:5px;
    margin-top:8px;
}
button{
    width:100%;
    padding:12px;
    margin-top:10px;
    background:#007bff;
    color:white;
    border:none;
    border-radius:5px;
    cursor:pointer;
}
button:hover{background:#0056b3;}
.result{
    margin-top:10px;
    padding:8px;
    background:#f8f9fa;
    border-radius:5px;
}
a{
    word-break:break-all;
    color:#28a745;
    font-weight:bold;
    text-decoration:none;
}
img{margin-top:5px;}
@media(max-width:480px){
    .container{margin:5px;padding:10px;}
}
</style>
</head>
<body>

<div class="container">
<h2>🔗 ShortLink Generator</h2>

<form method="POST">
<input type="text" name="url" placeholder="Paste your long URL..." required>
<button type="submit">Generate Link</button>
</form>

{% if short_url %}
<div class="result">
<p><b>Your Short Link:</b></p>
<a href="{{short_url}}" target="_blank">{{short_url}}</a>
<p><b>QR Code:</b></p>
<img src="data:image/png;base64,{{qr}}" width="130">
</div>
{% endif %}

</div>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    short_url = None
    qr_img = None

    if request.method == "POST":
        original = request.form["url"]
        code = generate_code()

        # Save to DB
        conn = sqlite3.connect("links.db")
        c = conn.cursor()
        c.execute("INSERT INTO links VALUES (?,?)", (code, original))
        conn.commit()
        conn.close()

        # Decide base URL
        if LOCAL_MODE:
            base = request.host_url.rstrip("/")
        else:
            base = REAL_DOMAIN.rstrip("/")
            if not base.endswith(".com"):
                base += ".com"

        short_url = f"{base}/{code}"

        # QR code
        img = qrcode.make(short_url)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_img = base64.b64encode(buffer.getvalue()).decode()

    return render_template_string(HTML, short_url=short_url, qr=qr_img)

@app.route("/<code>")
def redirect_link(code):
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("SELECT original FROM links WHERE short=?", (code,))
    result = c.fetchone()
    conn.close()

    if result:
        return redirect(result[0])
    return "Link not found!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)