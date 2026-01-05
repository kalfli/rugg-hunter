"""
Test Simple - Vérifie que FastAPI fonctionne
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Bot</title>
        <style>
            body {
                background: #0a0e27;
                color: white;
                font-family: Arial;
                padding: 50px;
                text-align: center;
            }
            .status {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: red;
                display: inline-block;
                margin-right: 10px;
            }
            .status.connected {
                background: lime;
            }
            button {
                padding: 10px 20px;
                margin: 10px;
                font-size: 16px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>🚀 Test Bot Interface</h1>
        <div>
            <span class="status" id="status"></span>
            <span id="statusText">Déconnecté</span>
        </div>
        <br><br>
        <button onclick="testAPI()">Test API</button>
        <button onclick="connectWS()">Test WebSocket</button>
        <br><br>
        <div id="output" style="background: #1a1f3a; padding: 20px; margin-top: 20px; text-align: left; max-width: 600px; margin-left: auto; margin-right: auto;"></div>
        
        <script>
            let ws = null;
            
            function log(msg) {
                document.getElementById('output').innerHTML += msg + '<br>';
            }
            
            async function testAPI() {
                log('🔍 Testing API...');
                try {
                    const response = await fetch('/api/health');
                    const data = await response.json();
                    log('✅ API works: ' + JSON.stringify(data));
                } catch (error) {
                    log('❌ API error: ' + error);
                }
            }
            
            function connectWS() {
                log('🔍 Testing WebSocket...');
                try {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const host = window.location.host;
                    const wsUrl = protocol + '//' + host + '/ws/test';
                    
                    log('Connecting to: ' + wsUrl);
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = () => {
                        log('✅ WebSocket connected!');
                        document.getElementById('status').classList.add('connected');
                        document.getElementById('statusText').textContent = 'Connecté';
                    };
                    
                    ws.onmessage = (event) => {
                        log('📨 Message: ' + event.data);
                    };
                    
                    ws.onerror = (error) => {
                        log('❌ WebSocket error: ' + error);
                    };
                    
                    ws.onclose = () => {
                        log('❌ WebSocket closed');
                        document.getElementById('status').classList.remove('connected');
                        document.getElementById('statusText').textContent = 'Déconnecté';
                    };
                } catch (error) {
                    log('❌ Error: ' + error);
                }
            }
        </script>
    </body>
    </html>
    """)

@app.get("/api/health")
async def health():
    print("✅ API health called")
    return {
        "status": "ok",
        "message": "API fonctionne!"
    }

@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    print("📡 WebSocket connection attempt")
    await websocket.accept()
    print("✅ WebSocket accepted")
    
    try:
        await websocket.send_text("Connecté au serveur!")
        
        while True:
            data = await websocket.receive_text()
            print(f"📨 Received: {data}")
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 STARTING TEST SERVER")
    print("=" * 60)
    print("Ouvrez: http://localhost:8000")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
