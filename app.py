# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import requests
import json
import speech_recognition as sr
from fpdf import FPDF
import pyttsx3
import os
import platform
import webbrowser
import markdown
import html2text
import re
from bs4 import BeautifulSoup
import subprocess
import time

app = Flask(__name__)

class HrishiBotWeb:
    def __init__(self):
        self.setup_constants()
        self.chat_history = []
        self.initialize_tts()
        
    def setup_constants(self):
        """Initialize all constant values"""
        self.API_KEY = "----------------------------"
        self.API_URL = f"------------------key={self.API_KEY}"
        self.HEADERS = {"Content-Type": "application/json"}
        self.is_muted = False
        self.last_response = ""
        self.conversation_context = []
        self.max_context_length = 5
        
        # Predefined responses (same as before)
        self.predefined_responses = {
            "what's your name": "I am HrishiBot, your highly capable personal assistant, created by the visionary Hrishikesh!",
            # ... (rest of your predefined responses)
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
            return "Available commands: /clear, /export, /pdf, /voice, /theme, /mute, /help, /about"
        elif cmd == "/about":
            return "HrishiBot - Personal Assistant\nVersion: 2.1\nCreated by: Hrishikesh"
        else:
            return f"Unknown command: {command}. Type /help for available commands."
    
    def update_conversation_context(self, message):
        """Update the conversation context"""
        self.conversation_context.append(message)
        if len(self.conversation_context) > self.max_context_length * 2:
            self.conversation_context = self.conversation_context[-self.max_context_length * 2:]

# Initialize the bot
hrishibot = HrishiBotWeb()

@app.route("/")
def home():
    return render_template("index.html", chat_history=hrishibot.chat_history)

@app.route("/send_message", methods=["POST"])
def send_message():
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

if __name__ == "__main__":
    app.run(debug=True)
