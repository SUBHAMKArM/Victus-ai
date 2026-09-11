"""
Victus AI - Phone Control Server
Receive voice commands from your phone via local WiFi.
"""
import threading
import json
import os

HAS_FLASK = False
try:
    from flask import Flask, request, jsonify
    HAS_FLASK = True
except ImportError:
    pass


class PhoneServer:
    """Simple Flask API for phone → PC commands with optional token security."""

    def __init__(self, command_handler, port=None):
        self.command_handler = command_handler
        self.port = port or int(os.getenv("PHONE_SERVER_PORT", 5000))
        self.auth_token = os.getenv("PHONE_AUTH_TOKEN", "").strip()
        self.enabled = HAS_FLASK

        if not self.enabled:
            print("[!] Flask not installed. Phone control disabled.")
            return

        self.app = Flask(__name__)
        self.app.logger.disabled = True

        @self.app.route("/command", methods=["POST"])
        def handle_command():
            # Check authentication token if configured in .env
            if self.auth_token:
                provided_token = request.headers.get("X-Auth-Token") or request.args.get("token")
                if not provided_token and request.is_json:
                    provided_token = (request.get_json(silent=True) or {}).get("token")
                if provided_token != self.auth_token:
                    return jsonify({"error": "Unauthorized. Invalid or missing token."}), 401

            data = request.get_json(silent=True)
            if not data or "text" not in data:
                return jsonify({"error": "Send JSON with 'text' field"}), 400
            text = data["text"]
            print(f"  [PHONE] Received: {text}")
            # Run command in background
            threading.Thread(target=self.command_handler, args=(text,), daemon=True).start()
            return jsonify({"status": "ok", "received": text})

        @self.app.route("/status", methods=["GET"])
        def status():
            return jsonify({"status": "online", "name": "Victus AI"})

    def start(self):
        if not self.enabled:
            return
        thread = threading.Thread(
            target=lambda: self.app.run(host="0.0.0.0", port=self.port, debug=False, use_reloader=False),
            daemon=True
        )
        thread.start()
        print(f"[*] Phone server: http://0.0.0.0:{self.port}")
        print(f"[*] Send POST to /command with JSON: {{\"text\": \"open chrome\"}}")


if __name__ == "__main__":
    def test_handler(text):
        print(f"Would process: {text}")

    server = PhoneServer(test_handler)
    server.start()
    input("Server running. Press Enter to stop.\n")
