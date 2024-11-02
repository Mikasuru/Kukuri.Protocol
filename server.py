import asyncio
import websockets
import json
from database import ChatDatabase
import base64
from PIL import Image
import io

class ChatServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.db = ChatDatabase()
        self.active_connections = {}  # {username: websocket}
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS unread_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            sender TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            FOREIGN KEY (username) REFERENCES users (username),
            FOREIGN KEY (sender) REFERENCES users (username)
        )
        ''')
        
        self.conn.commit()

    async def register_handler(self, websocket, data):
        username = data.get('username')
        password = data.get('password')
        
        if self.db.register_user(username, password):
            response = {'type': 'register', 'status': 'success'}
        else:
            response = {'type': 'register', 'status': 'error', 'message': 'Username already exists'}
        await websocket.send(json.dumps(response))
    
    async def login_handler(self, websocket, data):
        username = data.get('username')
        password = data.get('password')
        
        if self.db.verify_user(username, password):
            self.active_connections[username] = websocket
            self.db.update_user_status(username, True)
            
            contacts = []
            for user in self.db.get_all_users_with_profiles():
                if user['profile_image']:
                    user['profile_image'] = self.resize_image_base64(
                        user['profile_image'], 
                        max_size=(100, 100)
                    )
                if user['additional_image']:
                    user['additional_image'] = self.resize_image_base64(
                        user['additional_image'],
                        max_size=(200, 100)
                    )
                contacts.append(user)
            
            chat_history = self.db.get_user_chat_history(username)
            
            response = {
                'type': 'login',
                'status': 'success',
                'contacts': contacts,
                'chat_history': chat_history
            }
            
            await websocket.send(json.dumps(response))
            
            for other_username, other_ws in self.active_connections.items():
                if other_username != username:
                    try:
                        await other_ws.send(json.dumps({
                            'type': 'status_update',
                            'username': username,
                            'status': 'online'
                        }))
                    except Exception as e:
                        print(f"Error sending status update: {e}")
        else:
            await websocket.send(json.dumps({
                'type': 'login',
                'status': 'error',
                'message': 'Invalid username or password'
            }))
    
    async def message_handler(self, websocket, data):
        sender = data.get('sender')
        receiver = data.get('receiver')
        message_type = data.get('message_type')
        content = data.get('content')
        
        self.db.save_message(sender, receiver, message_type, content)
        
        if receiver in self.active_connections:
            await self.active_connections[receiver].send(json.dumps({
                'type': 'message',
                'sender': sender,
                'message_type': message_type,
                'content': content
            }))
    
    async def broadcast_status(self, username, is_online):
        status_message = json.dumps({
            'type': 'status_update',
            'username': username,
            'status': 'online' if is_online else 'offline'
        })
        
        for user, conn in self.active_connections.items():
            if user != username:
                try:
                    await conn.send(status_message)
                except:
                    pass
    
    def resize_image_base64(self, base64_str, max_size=(100, 100)):
        try:
            image_data = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(image_data))
            
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            buffered = io.BytesIO()
            image.save(buffered, format=image.format or 'JPEG')
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except:
            return base64_str

    async def register_handler(self, websocket, data):
        print(f"Received registration request: {data}")
        username = data.get('username')
        password = data.get('password')
        display_name = data.get('display_name')
        profile_image = data.get('profile_image')
        additional_image = data.get('additional_image')
        
        if not username or not password:
            response = {
                'type': 'register',
                'status': 'error',
                'message': 'Username and password required'
            }
        else:
            success = self.db.register_user(
                username, password, display_name, 
                profile_image, additional_image
            )
            
            if success:
                response = {'type': 'register', 'status': 'success'}
            else:
                response = {
                    'type': 'register',
                    'status': 'error',
                    'message': 'Username already exists'
                }
        
        await websocket.send(json.dumps(response))                

    async def handle_client(self, websocket, path):
        try:
            async for message in websocket:
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type == 'register':
                    await self.register_handler(websocket, data)
                elif message_type == 'login':
                    await self.login_handler(websocket, data)
                elif message_type == 'message':
                    await self.message_handler(websocket, data)
                elif message_type == 'profile_update':
                    await self.handle_profile_update(websocket, data)
                elif message_type == 'profile_request':
                    await self.handle_profile_request(websocket, data)
                
        except websockets.exceptions.ConnectionClosed:
            for username, conn in self.active_connections.items():
                if conn == websocket:
                    del self.active_connections[username]
                    self.db.update_user_status(username, False)
                    await self.broadcast_status(username, False)
                    break
    
    def save_unread_messages(self, username, unread_data):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM unread_messages WHERE username = ?", (username,))
        
        for sender, count in unread_data.items():
            cursor.execute(
                "INSERT INTO unread_messages (username, sender, count) VALUES (?, ?, ?)",
                (username, sender, count)
            )
        self.conn.commit()

    def get_unread_messages(self, username):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT sender, count FROM unread_messages WHERE username = ?",
            (username,)
        )
        return dict(cursor.fetchall())

    async def handle_profile_update(self, websocket, data):
        username = data.get('username')
        if not username or username not in self.active_connections:
            return
        
        success = self.db.update_profile(
            username=username,
            display_name=data.get('display_name'),
            status_message=data.get('status_message'),
            profile_picture=data.get('profile_picture'),
            current_theme=data.get('current_theme')
        )
        
        if success:
            profile = self.db.get_profile(username)
            update_message = {
                'type': 'profile_update',
                'username': username,
                'profile': profile
            }
            
            for other_username, other_ws in self.active_connections.items():
                try:
                    await other_ws.send(json.dumps(update_message))
                except:
                    pass
        
        await websocket.send(json.dumps({
            'type': 'profile_update_result',
            'status': 'success' if success else 'error'
        }))
    
    async def handle_profile_request(self, websocket, data):
        requested_username = data.get('requested_username')
        if not requested_username:
            return
        
        profile = self.db.get_profile(requested_username)
        if profile:
            await websocket.send(json.dumps({
                'type': 'profile_data',
                'profile': profile
            }))

    def run(self):
        start_server = websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            max_size=100 * 1024 * 1024  # 100MB
        )
        asyncio.get_event_loop().run_until_complete(start_server)
        print(f"Chat server running on ws://{self.host}:{self.port}")
        asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    server = ChatServer()
    server.run()