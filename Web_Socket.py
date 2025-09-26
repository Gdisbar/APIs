import os
import asyncio
import redis.asyncio as async_redis
import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

load_dotenv()
app = FastAPI()

# Simple Redis connection (no password for local)
redis_client = async_redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

# MySQL connection
def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="acro0",
        password=os.getenv("MySQL_passwd"),
        database="TestDB",
        auth_plugin="mysql_native_password"
    )

# Simple Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        print(f"📢 Broadcasting to {len(self.active_connections)} clients: {message}")
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                print(f"✅ Sent to client successfully")
            except Exception as e:
                print(f"❌ Failed to send to client: {e}")
                disconnected.append(connection)
        
        # Remove failed connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
        <head><title>Simple WebSocket Test</title></head>
        <body>
            <h1>WebSocket Test</h1>
            <div id="status">Connecting...</div>
            <form id="form">
                <input type="text" id="messageText" placeholder="Type message..."/>
                <button type="submit">Send</button>
            </form>
            <ul id="messages"></ul>
            <script>
                const ws = new WebSocket("ws://localhost:8000/ws");
                const status = document.getElementById('status');
                const messages = document.getElementById('messages');
                
                ws.onopen = function() {
                    status.textContent = "Connected ✅";
                    status.style.color = "green";
                    console.log("WebSocket connected");
                };
                
                ws.onclose = function() {
                    status.textContent = "Disconnected ❌";
                    status.style.color = "red";
                    console.log("WebSocket disconnected");
                };
                
                ws.onerror = function(error) {
                    status.textContent = "Error ⚠️";
                    status.style.color = "orange";
                    console.error("WebSocket error:", error);
                };
                
                ws.onmessage = function(event) {
                    console.log("Received:", event.data);
                    const li = document.createElement('li');
                    li.textContent = event.data;
                    messages.appendChild(li);
                };
                
                document.getElementById('form').onsubmit = function(e) {
                    e.preventDefault();
                    const input = document.getElementById('messageText');
                    if (input.value.trim()) {
                        console.log("Sending:", input.value);
                        ws.send(input.value);
                        input.value = '';
                    }
                };
            </script>
            <style>
                body { font-family: Arial; padding: 20px; max-width: 600px; }
                input { width: 70%; padding: 8px; }
                button { width: 25%; padding: 8px; }
                #messages { border: 1px solid #ccc; height: 300px; overflow-y: auto; padding: 10px; }
                #status { margin: 10px 0; font-weight: bold; }
            </style>
        </body>
    </html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            print(f"📨 Received from client: '{data}'")
            
            # Test MySQL connection and save
            try:
                print("🔍 Testing MySQL connection...")
                conn = get_mysql_connection()
                cursor = conn.cursor()
                
                # Insert message
                cursor.execute("INSERT INTO ChatMessages (message) VALUES (%s)", (data,))
                conn.commit()
                message_id = cursor.lastrowid
                print(f"✅ MySQL: Saved message #{message_id}")
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"❌ MySQL Error: {e}")
                # Continue even if MySQL fails
            
            # Broadcast to all clients
            broadcast_message = f"User: {data}"
            await manager.broadcast(broadcast_message)
            
    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

# Health check endpoints
@app.get("/test-mysql")
async def test_mysql():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ChatMessages")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"status": "success", "message_count": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/test-redis")
async def test_redis():
    try:
        await redis_client.ping()
        return {"status": "success", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Startup
@app.on_event("startup")
async def startup():
    print("🚀 Starting application...")
    
    # Test MySQL
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TestDB.ChatMessages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ MySQL: Table ready")
    except Exception as e:
        print(f"❌ MySQL startup error: {e}")
    
    # Test Redis
    try:
        await redis_client.ping()
        print("✅ Redis: Connected")
    except Exception as e:
        print(f"❌ Redis startup error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)



# >> PUBSUB CHANNELS *
# >> PUBLISH chat "Hello from Redis CLI"
# >> PUBSUB NUMSUB chat
# >> KEYS *