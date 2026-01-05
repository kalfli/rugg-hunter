"""
RUG HUNTER BOT V3.0 - STANDALONE
Fichier UNIQUE qui contient TOUT - Aucune dépendance externe
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
from datetime import datetime
from typing import Dict, Any
import json

# ============================================================================
# ÉTAT DU BOT
# ============================================================================

class BotState:
    def __init__(self):
        self.settings = {
            "TRADING_MODE": "PAPER",
            "AUTO_TRADING_ENABLED": False,
            "ACTIVE_STRATEGY": "CUSTOM",
            "ENABLE_ETH_DETECTION": True,
            "ENABLE_BSC_DETECTION": True,
            "ENABLE_SOL_DETECTION": False,
            "MIN_LIQUIDITY_USD": 5000,
            "MAX_POSITION_SIZE_USD": 500,
            "TAKE_PROFIT_1_PERCENT": 30,
            "TAKE_PROFIT_2_PERCENT": 50,
            "TAKE_PROFIT_3_PERCENT": 100,
            "STOP_LOSS_PERCENT": 15,
            "MAX_BUY_TAX": 10,
            "MAX_SELL_TAX": 15,
            "MIN_AUTO_TRADE_CONFIDENCE": 75,
        }
        
        self.stats = {
            "total_detections": 0,
            "trades_executed": 0,
            "honeypots_blocked": 0,
            "active_positions": 0,
            "total_pnl_usd": 0,
            "win_rate": 0,
            "start_time": datetime.utcnow().isoformat()
        }
        
        self.strategies = {
            "SCALPING": {"name": "⚡ Scalping", "tp1": 15, "tp2": 25, "tp3": 40, "sl": 8},
            "MOMENTUM": {"name": "🚀 Momentum", "tp1": 50, "tp2": 100, "tp3": 200, "sl": 15},
            "CONSERVATIVE": {"name": "🛡️ Conservateur", "tp1": 20, "tp2": 40, "tp3": 70, "sl": 10},
        }
        
        self.detections = []
        self.websockets = []

bot = BotState()

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="RUG HUNTER V3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HTML INTERFACE
# ============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🚀 Rug Hunter V3.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #0f1535 100%);
            color: white;
            min-height: 100vh;
        }
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 250px;
            height: 100vh;
            background: rgba(26, 31, 58, 0.95);
            padding: 20px;
            border-right: 1px solid #00ff88;
        }
        .logo {
            font-size: 1.5em;
            font-weight: bold;
            color: #00ff88;
            margin-bottom: 30px;
            text-align: center;
        }
        .status {
            background: rgba(0, 255, 136, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #00ff88;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #ff4444;
            display: inline-block;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        .status-dot.connected { background: #00ff88; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .nav-item {
            padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            cursor: pointer;
            transition: 0.3s;
        }
        .nav-item:hover { background: rgba(0, 255, 136, 0.1); }
        .nav-item.active { background: #00ff88; color: #000; font-weight: bold; }
        .main {
            margin-left: 250px;
            padding: 30px;
        }
        .page { display: none; }
        .page.active { display: block; animation: fadeIn 0.3s; }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .header {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 170, 255, 0.2));
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(26, 31, 58, 0.8);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(0, 255, 136, 0.2);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00ff88;
            margin: 10px 0;
        }
        .controls {
            background: rgba(26, 31, 58, 0.8);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .control-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .control-item {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .toggle {
            width: 50px;
            height: 25px;
            background: #444;
            border-radius: 25px;
            position: relative;
            cursor: pointer;
            transition: 0.3s;
        }
        .toggle.on { background: #00ff88; }
        .toggle::after {
            content: '';
            width: 21px;
            height: 21px;
            background: white;
            border-radius: 50%;
            position: absolute;
            top: 2px;
            left: 2px;
            transition: 0.3s;
        }
        .toggle.on::after { left: 27px; }
        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            background: linear-gradient(135deg, #00ff88, #00aaff);
            color: #000;
            transition: 0.3s;
        }
        .btn:hover { transform: translateY(-2px); }
        .input {
            width: 100%;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: white;
            margin: 10px 0;
        }
        .strategy-card {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-radius: 12px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 15px;
            cursor: pointer;
            transition: 0.3s;
        }
        .strategy-card:hover { border-color: #00ff88; }
        .strategy-card.active { border-color: #00ff88; background: rgba(0, 255, 136, 0.1); }
        .notif {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(26, 31, 58, 0.95);
            border: 2px solid #00ff88;
            padding: 15px 20px;
            border-radius: 10px;
            animation: slideIn 0.3s;
            z-index: 1000;
        }
        @keyframes slideIn {
            from { transform: translateX(400px); }
            to { transform: translateX(0); }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">🚀 RUG HUNTER<br>V3.0</div>
        <div class="status">
            <span class="status-dot" id="statusDot"></span>
            <span id="statusText">Déconnecté</span>
            <div style="margin-top: 10px; font-size: 0.9em;">
                Mode: <strong id="modeText">PAPER</strong><br>
                Stratégie: <strong id="stratText">CUSTOM</strong>
            </div>
        </div>
        <div class="nav-item active" onclick="showPage('dashboard')">📊 Dashboard</div>
        <div class="nav-item" onclick="showPage('strategies')">🎯 Stratégies</div>
        <div class="nav-item" onclick="showPage('trading')">💹 Trading</div>
        <div class="nav-item" onclick="showPage('settings')">⚙️ Configuration</div>
    </div>

    <div class="main">
        <!-- DASHBOARD -->
        <div id="dashboard" class="page active">
            <div class="header">
                <h1>📊 Dashboard Principal</h1>
                <p>Vue d'ensemble de votre bot</p>
            </div>
            <div class="stats">
                <div class="stat-card">
                    <div>🔍</div>
                    <div class="stat-value" id="statDetections">0</div>
                    <div>Détections</div>
                </div>
                <div class="stat-card">
                    <div>💹</div>
                    <div class="stat-value" id="statTrades">0</div>
                    <div>Trades</div>
                </div>
                <div class="stat-card">
                    <div>💰</div>
                    <div class="stat-value" id="statPnl">$0</div>
                    <div>PnL</div>
                </div>
                <div class="stat-card">
                    <div>🍯</div>
                    <div class="stat-value" id="statHoneypots">0</div>
                    <div>Honeypots</div>
                </div>
            </div>
            <div class="controls">
                <h2 style="margin-bottom: 15px;">🎮 Contrôles</h2>
                <div class="control-grid">
                    <div class="control-item">
                        <span>Auto-Trading</span>
                        <div class="toggle" id="toggleAuto" onclick="toggleSetting('AUTO_TRADING_ENABLED')"></div>
                    </div>
                    <div class="control-item">
                        <span>ETH</span>
                        <div class="toggle on" id="toggleETH" onclick="toggleSetting('ENABLE_ETH_DETECTION')"></div>
                    </div>
                    <div class="control-item">
                        <span>BSC</span>
                        <div class="toggle on" id="toggleBSC" onclick="toggleSetting('ENABLE_BSC_DETECTION')"></div>
                    </div>
                    <div class="control-item">
                        <span>SOL</span>
                        <div class="toggle" id="toggleSOL" onclick="toggleSetting('ENABLE_SOL_DETECTION')"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- STRATEGIES -->
        <div id="strategies" class="page">
            <div class="header">
                <h1>🎯 Stratégies</h1>
                <p>Choisissez votre stratégie de trading</p>
            </div>
            <div id="strategyList"></div>
        </div>

        <!-- TRADING -->
        <div id="trading" class="page">
            <div class="header">
                <h1>💹 Trading Manuel</h1>
                <p>Exécutez des trades en mode PAPER</p>
            </div>
            <div class="controls" style="max-width: 500px;">
                <input type="text" class="input" id="tradeAddr" placeholder="Adresse du token (0x...)">
                <input type="number" class="input" id="tradeAmount" placeholder="Montant (ETH)" value="0.1" step="0.01">
                <button class="btn" onclick="trade('BUY')">🚀 ACHETER</button>
                <button class="btn" onclick="trade('SELL')" style="margin-left: 10px; background: linear-gradient(135deg, #ff4444, #cc0000);">💸 VENDRE</button>
            </div>
        </div>

        <!-- SETTINGS -->
        <div id="settings" class="page">
            <div class="header">
                <h1>⚙️ Configuration</h1>
                <p>Paramètres du bot</p>
            </div>
            <div class="controls">
                <h3>💹 Trading</h3>
                <label>Liquidité Min (USD): <input type="number" class="input" id="setMinLiq" value="5000"></label>
                <label>Position Max (USD): <input type="number" class="input" id="setMaxPos" value="500"></label>
                <h3 style="margin-top: 20px;">🎯 Take Profit</h3>
                <label>TP 1 (%): <input type="number" class="input" id="setTP1" value="30"></label>
                <label>TP 2 (%): <input type="number" class="input" id="setTP2" value="50"></label>
                <label>TP 3 (%): <input type="number" class="input" id="setTP3" value="100"></label>
                <h3 style="margin-top: 20px;">🛑 Stop Loss</h3>
                <label>SL (%): <input type="number" class="input" id="setSL" value="15"></label>
                <button class="btn" onclick="saveSettings()" style="margin-top: 20px;">💾 Sauvegarder</button>
            </div>
        </div>
    </div>

    <script>
        const API = window.location.origin;
        let ws;

        function showPage(page) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById(page).classList.add('active');
            event.target.classList.add('active');
            console.log('📄 Page:', page);
        }

        function connectWS() {
            const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
            const url = `${proto}//${location.host}/ws`;
            console.log('🔌 Connecting to:', url);
            
            ws = new WebSocket(url);
            
            ws.onopen = () => {
                console.log('✅ WebSocket CONNECTED!');
                document.getElementById('statusDot').classList.add('connected');
                document.getElementById('statusText').textContent = 'Connecté';
                notif('✅ Connecté au bot');
            };
            
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                console.log('📨', data.type);
                if (data.type === 'stats') updateStats(data.data);
                if (data.type === 'settings') updateUI(data.data);
            };
            
            ws.onerror = (e) => console.error('❌ WS Error:', e);
            
            ws.onclose = () => {
                console.log('❌ WS Closed, reconnecting...');
                document.getElementById('statusDot').classList.remove('connected');
                document.getElementById('statusText').textContent = 'Déconnecté';
                setTimeout(connectWS, 5000);
            };
        }

        function updateStats(stats) {
            document.getElementById('statDetections').textContent = stats.total_detections;
            document.getElementById('statTrades').textContent = stats.trades_executed;
            document.getElementById('statPnl').textContent = '$' + stats.total_pnl_usd.toFixed(2);
            document.getElementById('statHoneypots').textContent = stats.honeypots_blocked;
        }

        function updateUI(settings) {
            document.getElementById('modeText').textContent = settings.TRADING_MODE;
            document.getElementById('stratText').textContent = settings.ACTIVE_STRATEGY;
            document.getElementById('toggleAuto').classList.toggle('on', settings.AUTO_TRADING_ENABLED);
            document.getElementById('toggleETH').classList.toggle('on', settings.ENABLE_ETH_DETECTION);
            document.getElementById('toggleBSC').classList.toggle('on', settings.ENABLE_BSC_DETECTION);
            document.getElementById('toggleSOL').classList.toggle('on', settings.ENABLE_SOL_DETECTION);
        }

        async function toggleSetting(key) {
            const toggle = event.target;
            const isOn = !toggle.classList.contains('on');
            
            const res = await fetch(`${API}/api/toggle`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key, value: isOn})
            });
            
            if (res.ok) {
                toggle.classList.toggle('on');
                notif(`✅ ${key}`);
            }
        }

        async function trade(action) {
            const addr = document.getElementById('tradeAddr').value;
            const amount = document.getElementById('tradeAmount').value;
            
            if (!addr) return notif('❌ Entrez une adresse');
            
            const res = await fetch(`${API}/api/trade`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action, address: addr, amount})
            });
            
            const data = await res.json();
            notif(data.success ? '✅ ' + data.message : '❌ ' + data.message);
        }

        async function saveSettings() {
            const settings = {
                MIN_LIQUIDITY_USD: parseInt(document.getElementById('setMinLiq').value),
                MAX_POSITION_SIZE_USD: parseInt(document.getElementById('setMaxPos').value),
                TAKE_PROFIT_1_PERCENT: parseInt(document.getElementById('setTP1').value),
                TAKE_PROFIT_2_PERCENT: parseInt(document.getElementById('setTP2').value),
                TAKE_PROFIT_3_PERCENT: parseInt(document.getElementById('setTP3').value),
                STOP_LOSS_PERCENT: parseInt(document.getElementById('setSL').value),
            };
            
            const res = await fetch(`${API}/api/settings`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            });
            
            if (res.ok) notif('✅ Paramètres sauvegardés');
        }

        async function loadStrategies() {
            const res = await fetch(`${API}/api/strategies`);
            const data = await res.json();
            const container = document.getElementById('strategyList');
            
            container.innerHTML = Object.keys(data).map(key => {
                const s = data[key];
                return `
                    <div class="strategy-card" onclick="applyStrategy('${key}')">
                        <h3>${s.name}</h3>
                        <p>TP: ${s.tp1}%/${s.tp2}%/${s.tp3}% | SL: ${s.sl}%</p>
                    </div>
                `;
            }).join('');
        }

        async function applyStrategy(name) {
            const res = await fetch(`${API}/api/strategy/${name}`, {method: 'POST'});
            if (res.ok) {
                notif(`✅ Stratégie: ${name}`);
                document.getElementById('stratText').textContent = name;
            }
        }

        function notif(msg) {
            const n = document.createElement('div');
            n.className = 'notif';
            n.textContent = msg;
            document.body.appendChild(n);
            setTimeout(() => n.remove(), 3000);
        }

        window.onload = () => {
            console.log('🚀 RUG HUNTER V3.0 STANDALONE');
            connectWS();
            loadStrategies();
            setInterval(async () => {
                const res = await fetch(`${API}/api/stats`);
                const data = await res.json();
                updateStats(data);
            }, 10000);
        };
    </script>
</body>
</html>
"""

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    return HTMLResponse(HTML_TEMPLATE)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    bot.websockets.append(websocket)
    print(f"📡 WebSocket connected (total: {len(bot.websockets)})")
    
    try:
        # Envoyer état initial
        await websocket.send_json({"type": "settings", "data": bot.settings})
        await websocket.send_json({"type": "stats", "data": get_stats()})
        
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        bot.websockets.remove(websocket)
        print(f"📡 WebSocket disconnected (remaining: {len(bot.websockets)})")

async def broadcast(message):
    dead = []
    for ws in bot.websockets:
        try:
            await ws.send_json(message)
        except:
            dead.append(ws)
    for ws in dead:
        try:
            bot.websockets.remove(ws)
        except:
            pass

def get_stats():
    # Créer une copie sans start_time
    stats_copy = {k: v for k, v in bot.stats.items() if k != "start_time"}
    stats_copy["uptime_seconds"] = 0  # Ou calculez le uptime si nécessaire
    return stats_copy

@app.get("/api/stats")
async def api_stats():
    return get_stats()

@app.get("/api/strategies")
async def api_strategies():
    return bot.strategies

@app.post("/api/toggle")
async def api_toggle(data: Dict[str, Any]):
    key = data.get("key")
    value = data.get("value")
    if key in bot.settings:
        bot.settings[key] = value
        print(f"✅ {key} = {value}")
        await broadcast({"type": "settings", "data": bot.settings})
        return {"success": True}
    return {"success": False}

@app.post("/api/settings")
async def api_settings(data: Dict[str, Any]):
    for key, value in data.items():
        if key in bot.settings:
            bot.settings[key] = value
    print(f"✅ Updated {len(data)} settings")
    await broadcast({"type": "settings", "data": bot.settings})
    return {"success": True}

@app.post("/api/strategy/{name}")
async def api_strategy(name: str):
    if name in bot.strategies:
        s = bot.strategies[name]
        bot.settings["ACTIVE_STRATEGY"] = name
        bot.settings["TAKE_PROFIT_1_PERCENT"] = s["tp1"]
        bot.settings["TAKE_PROFIT_2_PERCENT"] = s["tp2"]
        bot.settings["TAKE_PROFIT_3_PERCENT"] = s["tp3"]
        bot.settings["STOP_LOSS_PERCENT"] = s["sl"]
        print(f"✅ Strategy: {name}")
        await broadcast({"type": "settings", "data": bot.settings})
        return {"success": True}
    return {"success": False}

@app.post("/api/trade")
async def api_trade(data: Dict[str, Any]):
    action = data.get("action")
    bot.stats["trades_executed"] += 1
    await broadcast({"type": "stats", "data": get_stats()})
    print(f"📈 Trade: {action}")
    return {"success": True, "message": f"PAPER: {action} executed"}

# ============================================================================
# TÂCHES DE FOND
# ============================================================================

async def broadcast_stats():
    while True:
        await asyncio.sleep(5)
        await broadcast({"type": "stats", "data": get_stats()})

async def simulate_detections():
    await asyncio.sleep(10)
    counter = 0
    while True:
        await asyncio.sleep(30)
        if bot.settings["AUTO_TRADING_ENABLED"]:
            counter += 1
            bot.stats["total_detections"] += 1
            print(f"🔍 Detection #{counter}")
            await broadcast({"type": "stats", "data": get_stats()})

@app.on_event("startup")
async def startup():
    print("=" * 60)
    print("🚀 RUG HUNTER V3.0 - STANDALONE")
    print("=" * 60)
    print("📊 Mode: PAPER")
    print("✅ BOT READY!")
    print("=" * 60)
    print("🌐 Ouvrez: http://localhost:8000")
    print("=" * 60)
    asyncio.create_task(broadcast_stats())
    asyncio.create_task(simulate_detections())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
