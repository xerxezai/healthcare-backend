#!/usr/bin/env python
"""
Dr. Max AI Chatbot WebSocket Server
Real-time chat server with OpenAI integration for medical assistance
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from pathlib import Path

# Add Django settings to the path
sys.path.append(str(Path(__file__).parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from secureneat.services.openai_service import openai_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DrMaxChatBot:
    def __init__(self):
        self.connected_clients = set()
        self.chat_rooms = {}  # roomId -> list of messages
        
    async def register_client(self, websocket, user_id, room_id):
        """Register a new client connection"""
        self.connected_clients.add(websocket)
        websocket.user_id = user_id
        websocket.room_id = room_id
        
        logger.info(f"Client {user_id} connected to room {room_id}")
        
        # Send connection confirmation
        await websocket.send(json.dumps({
            "type": "status",
            "text": "Connected to Dr. Max AI. How can I help you today?",
            "sender": "bot"
        }))
        
        # Send chat history if available
        if room_id in self.chat_rooms:
            await websocket.send(json.dumps({
                "type": "history",
                "messages": self.chat_rooms[room_id]
            }))

    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.connected_clients.discard(websocket)
        if hasattr(websocket, 'user_id'):
            logger.info(f"Client {websocket.user_id} disconnected")

    async def handle_message(self, websocket, message_data):
        """Handle incoming message from client"""
        try:
            message_type = message_data.get("type")
            room_id = message_data.get("roomId")
            
            if message_type == "message":
                await self.handle_chat_message(websocket, message_data)
            elif message_type == "new_chat":
                await self.handle_new_chat(websocket, room_id)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Error processing your message: {str(e)}"
            }))

    async def handle_chat_message(self, websocket, message_data):
        """Handle chat message and generate AI response"""
        user_message = message_data.get("message", "").strip()
        room_id = message_data.get("roomId")
        user_id = message_data.get("userId")
        
        if not user_message:
            return
            
        # Store user message
        if room_id not in self.chat_rooms:
            self.chat_rooms[room_id] = []
            
        user_msg = {
            "id": f"user_{len(self.chat_rooms[room_id])}",
            "content": user_message,
            "sender": "user",
            "timestamp": asyncio.get_event_loop().time()
        }
        self.chat_rooms[room_id].append(user_msg)
        
        # Generate unique message ID for streaming response
        message_id = f"bot_{len(self.chat_rooms[room_id])}"
        
        # Start AI response
        await websocket.send(json.dumps({
            "type": "llm_response_start",
            "message_id": message_id,
            "sender": "bot",
            "initial_text": ""
        }))
        
        try:
            # Get AI response from OpenAI service
            ai_response = await self.get_ai_response(user_message)
            
            # Stream the response
            await self.stream_response(websocket, message_id, ai_response)
            
            # Store bot response
            bot_msg = {
                "id": message_id,
                "content": ai_response,
                "sender": "bot", 
                "timestamp": asyncio.get_event_loop().time()
            }
            self.chat_rooms[room_id].append(bot_msg)
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            error_response = f"I apologize, but I'm experiencing technical difficulties. Please try again or ask me something else about medical topics."
            
            await self.stream_response(websocket, message_id, error_response)

    async def get_ai_response(self, user_message):
        """Get response from OpenAI service"""
        try:
            # Use the existing OpenAI service
            response = openai_service.get_chat_response(user_message)
            return response
        except Exception as e:
            logger.error(f"OpenAI service error: {e}")
            # Fallback response
            return f"I understand you're asking about: '{user_message}'. As Dr. Max, I'm here to help with medical questions. Could you please rephrase your question or ask about a specific medical topic? I can assist with symptoms, conditions, treatments, and medical education."

    async def stream_response(self, websocket, message_id, response_text):
        """Stream AI response in chunks for real-time effect"""
        words = response_text.split()
        current_text = ""
        
        for i, word in enumerate(words):
            current_text += word + " "
            
            # Send chunk update
            await websocket.send(json.dumps({
                "type": "llm_response_chunk",
                "message_id": message_id,
                "delta": word + " "
            }))
            
            # Small delay for streaming effect
            await asyncio.sleep(0.05)
        
        # End streaming
        await websocket.send(json.dumps({
            "type": "llm_response_end",
            "message_id": message_id
        }))

    async def handle_new_chat(self, websocket, room_id):
        """Handle new chat request"""
        if room_id in self.chat_rooms:
            del self.chat_rooms[room_id]
            
        await websocket.send(json.dumps({
            "type": "status",
            "text": "New chat started. How can I help you with your medical questions?",
            "sender": "bot"
        }))

# Global chatbot instance
chatbot = DrMaxChatBot()

async def handle_client(websocket):
    """Handle WebSocket client connection"""
    try:
        # Get path from websocket object
        path = websocket.path or ""
        
        # Parse query parameters
        import urllib.parse
        query_params = urllib.parse.parse_qs(path.split('?')[1] if '?' in path else '')
        user_id = query_params.get('userId', ['anonymous'])[0]
        room_id = query_params.get('roomId', ['default'])[0]
        
        # Register client
        await chatbot.register_client(websocket, user_id, room_id)
        
        # Listen for messages
        async for message in websocket:
            try:
                message_data = json.loads(message)
                await chatbot.handle_message(websocket, message_data)
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid message format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "type": "error", 
                    "message": "Error processing your message"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await chatbot.unregister_client(websocket)

async def main():
    """Start the WebSocket server"""
    host = "localhost"
    port = 5161
    
    logger.info(f"🤖 Dr. Max AI Chatbot Server starting on {host}:{port}")
    logger.info("📡 Waiting for connections...")
    
    try:
        # Test OpenAI connection
        test_response = openai_service.get_chat_response("Hello, can you help me?")
        logger.info("✅ OpenAI service connection verified")
    except Exception as e:
        logger.warning(f"⚠️  OpenAI service issue: {e}")
        logger.info("🔄 Server will continue with fallback responses")
    
    server = await websockets.serve(
        handle_client,
        host,
        port,
        ping_interval=20,
        ping_timeout=10
    )
    
    logger.info(f"🚀 Dr. Max AI Chatbot Server is running!")
    logger.info(f"🌐 WebSocket URL: ws://{host}:{port}")
    logger.info("💬 Ready to assist with medical questions")
    
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        logger.info("🛑 Server shutting down...")
        server.close()
        await server.wait_closed()
        logger.info("👋 Dr. Max AI Chatbot Server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Dr. Max AI Chatbot Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
