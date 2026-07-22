from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import datetime
import platform
import time
import requests
import psutil
from duckduckgo_search import DDGS

app = Flask(__name__)
CORS(app)

# ---------- SEARCH (REAL DUCKDUCKGO) ----------

@app.get("/api/search")
def api_search():
    q = request.args.get("q", "").strip()

    results = DDGS().text(q, max_results=10)
    formatted = []
    for r in results:
        formatted.append({
            "title": r.get("title", "No title"),
            "href": r.get("href", "#"),
            "body": r.get("body", "")
        })

    return jsonify({
        "query": q,
        "results": formatted
    })


# ---------- NOTES API ----------

@app.post("/api/note")
def note():
    data = request.get_json(force=True) or {}
    text = data.get("text", "")
    os.makedirs("notes", exist_ok=True)
    name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt")
    path = os.path.join("notes", name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return jsonify({"status": "saved", "file": name})


# ---------- SIMPLE PING API ----------

@app.get("/api/ping")
def ping():
    return jsonify({
        "system": platform.system(),
        "release": platform.release(),
        "python": platform.python_version()
    })


# ---------- REAL WEATHER (OPEN-METEO) ----------

@app.get("/weather")
def weather_page():
    lat, lon = -35.509, 173.516  # approx Opononi

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true"
    )

    try:
        data = requests.get(url, timeout=5).json()
        w = data.get("current_weather", {})
        temp = w.get("temperature", "N/A")
        wind = w.get("windspeed", "N/A")
        code = w.get("weathercode", "N/A")
    except Exception:
        temp = wind = code = "N/A"

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Weather</title>
    </head>
    <body>
        <h2>Weather — Opononi</h2>
        <p><strong>Temperature:</strong> {temp}°C</p>
        <p><strong>Wind Speed:</strong> {wind} km/h</p>
        <p><strong>Weather Code:</strong> {code}</p>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


# ---------- REAL SYSTEM INFO (PSUTIL) ----------

@app.get("/system")
def system_page():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    boot = psutil.boot_time()
    uptime_hours = round((time.time() - boot) / 3600, 2)

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>System Info</title>
    </head>
    <body>
        <h2>System Info</h2>
        <p><strong>CPU Usage:</strong> {cpu}%</p>
        <p><strong>RAM Usage:</strong> {ram}%</p>
        <p><strong>Disk Usage:</strong> {disk}%</p>
        <p><strong>Uptime:</strong> {uptime_hours} hours</p>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


# ---------- DASHBOARD (CPU/RAM/DISK) ----------

@app.get("/dashboard")
def dashboard_page():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Dashboard</title>
    </head>
    <body>
        <h2>Amethyst Dashboard</h2>
        <p><strong>CPU Usage:</strong> {cpu}%</p>
        <p><strong>RAM Usage:</strong> {ram}%</p>
        <p><strong>Disk Usage:</strong> {disk}%</p>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


# ---------- TASK MANAGER (TOP PROCESSES) ----------

@app.get("/tasks")
def tasks_page():
    procs = []
    for p in psutil.process_iter(attrs=["pid", "name", "cpu_percent"]):
        procs.append(p.info)
    procs = sorted(procs, key=lambda x: x["cpu_percent"], reverse=True)[:10]

    rows = ""
    for p in procs:
        rows += f"<tr><td>{p['pid']}</td><td>{p['name']}</td><td>{p['cpu_percent']}%</td></tr>"

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Tasks</title>
    </head>
    <body>
        <h2>Top Processes</h2>
        <table>
            <tr><th>PID</th><th>Name</th><th>CPU%</th></tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


# ---------- NETWORK MONITOR (BASIC IO) ----------

@app.get("/network")
def network_page():
    io = psutil.net_io_counters()
    sent = round(io.bytes_sent / (1024 * 1024), 2)
    recv = round(io.bytes_recv / (1024 * 1024), 2)

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Network</title>
    </head>
    <body>
        <h2>Network IO</h2>
        <p><strong>Bytes Sent:</strong> {sent} MB</p>
        <p><strong>Bytes Received:</strong> {recv} MB</p>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
