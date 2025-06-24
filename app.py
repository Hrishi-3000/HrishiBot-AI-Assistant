# app.py
from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime  # Add this
from google.generativeai import configure, GenerativeModel

app = Flask(__name__)

class HrishiBotWeb:
    def __init__(self):
        self.setup_constants()
        self.chat_history = []
        self.initialize_tts()
        
    def setup_constants(self):
        """Initialize all constant values"""
        # Get API key from environment variable
        self.API_KEY = os.environ.get('GOOGLE_API_KEY')
        if not self.API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
            
        self.API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.API_KEY}"
        self.HEADERS = {"Content-Type": "application/json"}
        self.is_muted = False
        self.last_response = ""
        self.conversation_context = []
        self.max_context_length = 5
        
        # Predefined responses
        self.predefined_responses = {
            "what's your name": "I am HrishiBot, your highly capable personal assistant, created by the visionary Hrishikesh!",
            "who created you": "I was created by Hrishikesh, a brilliant developer with a vision for intelligent assistants!",
            "hello": "Hello there! How can I assist you today?",
            "hi": "Hi! What can I do for you?",
            "how are you": "I'm functioning at optimal capacity, thank you for asking! How about you?",
            "thank you": "You're welcome! Is there anything else I can help with?",
            "goodbye": "Goodbye! Don't hesitate to return if you need more assistance!",
            "what can you do": "I can answer questions, help with research, generate content, and much more! Try asking me anything.",
            "tell me a joke": "Why don't scientists trust atoms? Because they make up everything!",
            "open google": "Opening Google in your browser...",
            "current time": f"The current time is {datetime.now().strftime('%H:%M:%S')}",
            "today's date": f"Today's date is {datetime.now().strftime('%Y-%m-%d')}",
            "your purpose": "My purpose is to assist, inform, and make your digital life easier!",
            "who are you": "I'm HrishiBot, your AI-powered personal assistant created by Hrishikesh!",
            "help": "I can answer questions, perform web searches, tell jokes, and more. Just ask!",
            "clear chat": "I've cleared our conversation history.",
            "mute": "I've muted voice responses. Use /mute again to unmute.",
            "unmute": "I've unmuted voice responses.",
            "about": "HrishiBot v2.1 - Created by Hrishikesh - A powerful AI assistant",
            "features": "I feature natural conversation, web integration, voice control, and more!",
            "settings": "You can adjust my behavior using commands like /mute, /theme, etc."
        }
        
    def initialize_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 1.0)
            voices = self.engine.getProperty('voices')
            if len(voices) > 0:
                for voice in voices:
                    if "female" in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    self.engine.setProperty('voice', voices[0].id)
        except Exception as e:
            print(f"Text-to-speech initialization failed: {str(e)}")
            self.engine = None
    
    def process_message(self, message):
        """Process incoming message and return response"""
        # Check for commands
        if message.startswith("/"):
            return self.process_command(message)
            
        # Add to conversation context
        self.update_conversation_context({"role": "user", "content": message})
        
        # Check predefined responses
        lower_input = message.lower()
        response = None
        
        for key, value in self.predefined_responses.items():
            if key in lower_input:
                response = value
                break
        
        if not response:
            response = self.get_gemini_response(message)
        
        self.last_response = response
        self.update_conversation_context({"role": "model", "content": response})
        
        # Add to chat history
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat_history.append({
            "timestamp": timestamp,
            "sender": "user",
            "message": message
        })
        self.chat_history.append({
            "timestamp": timestamp,
            "sender": "bot",
            "message": response
        })
        
        # Speak the response if not muted
        if not self.is_muted and self.engine:
            try:
                self.engine.say(response)
                self.engine.runAndWait()
            except Exception as e:
                print(f"Error in text-to-speech: {str(e)}")
        
        return response
    
    def get_gemini_response(self, prompt):
        """Get response from Gemini API"""
        if not prompt.strip():
            return "❌ Empty input. Please try again."
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": str(prompt)
                }]
            }]
        }
        
        try:
            response = requests.post(
                self.API_URL,
                headers=self.HEADERS,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            
            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "❌ No valid response from Gemini."
                
        except requests.exceptions.RequestException as e:
            return f"❌ Network Error: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected Error: {str(e)}"
    
    def process_command(self, command):
        """Process slash commands"""
        cmd = command.lower().split()[0]
        if cmd == "/clear":
            self.chat_history = []
            self.conversation_context = []
            return "Chat history cleared"
        elif cmd == "/mute":
            self.is_muted = not self.is_muted
            return "Voice responses muted" if self.is_muted else "Voice responses unmuted"
        elif cmd == "/help":
            return "Available commands:\n/clear - Clear chat history\n/mute - Toggle voice responses\n/export - Export chat to text\n/pdf - Create PDF of chat\n/voice - Voice input\n/theme - Change UI theme\n/about - Show bot info"
        elif cmd == "/about":
            return "HrishiBot - Personal Assistant\nVersion: 2.1\nCreated by: Hrishikesh"
        elif cmd == "/export":
            return self.export_chat()
        elif cmd == "/pdf":
            return self.create_pdf()
        elif cmd == "/voice":
            return self.process_voice_input()
        elif cmd == "/theme":
            return "Theme change functionality would go here"
        else:
            return f"Unknown command: {command}. Type /help for available commands."
    
    def update_conversation_context(self, message):
        """Update the conversation context"""
        self.conversation_context.append(message)
        if len(self.conversation_context) > self.max_context_length * 2:
            self.conversation_context = self.conversation_context[-self.max_context_length * 2:]
    
    def export_chat(self):
        """Export chat history to text file"""
        try:
            filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                for msg in self.chat_history:
                    f.write(f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}\n")
            return f"Chat exported to {filename}"
        except Exception as e:
            return f"❌ Export failed: {str(e)}"
    
    def create_pdf(self):
        """Create PDF from chat history"""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            for msg in self.chat_history:
                pdf.cell(0, 10, f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}", ln=True)
            
            filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(filename)
            return f"PDF created: {filename}"
        except Exception as e:
            return f"❌ PDF creation failed: {str(e)}"
    
    def process_voice_input(self):
        """Process voice input using speech recognition"""
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening...")
                audio = r.listen(source, timeout=5)
            
            text = r.recognize_google(audio)
            return f"Voice input processed: {text}"
        except sr.UnknownValueError:
            return "❌ Could not understand audio"
        except sr.RequestError as e:
            return f"❌ Speech recognition error: {str(e)}"
        except Exception as e:
            return f"❌ Voice input failed: {str(e)}"

# Initialize the bot
hrishibot = HrishiBotWeb()

@app.route("/")
def home():
    return render_template("index.html", chat_history=hrishibot.chat_history)

@app.route("/chat", methods=["POST"])
def chat():
    message = request.form.get("message", "").strip()
    if message:
        response = hrishibot.process_message(message)
        return jsonify({
            "status": "success",
            "response": response,
            "chat_history": hrishibot.chat_history
        })
    return jsonify({"status": "error", "message": "Empty message"})

@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    hrishibot.chat_history = []
    hrishibot.conversation_context = []
    return jsonify({"status": "success", "message": "Chat cleared"})

@app.route("/export_chat", methods=["POST"])
def export_chat():
    result = hrishibot.export_chat()
    return jsonify({"status": "success" if "exported" in result else "error", "message": result})

@app.route("/create_pdf", methods=["POST"])
def create_pdf():
    result = hrishibot.create_pdf()
    return jsonify({"status": "success" if "PDF created" in result else "error", "message": result})

@app.route("/voice_input", methods=["POST"])
def voice_input():
    result = hrishibot.process_voice_input()
    return jsonify({"status": "success" if "Voice input" in result else "error", "message": result})

if __name__ == "__main__":
    app.run(debug=True)
