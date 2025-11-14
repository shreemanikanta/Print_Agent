import json
import time
import logging
import websocket
import base64
import base64
from escpos.printer import Network, Usb

# ===================================================
# 🔧 Load Configuration
# ===================================================
def load_config():
    """Load agent configuration from config.json"""
    try:
        with open("config.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please create one.")
        exit(1)
    except json.JSONDecodeError:
        print("❌ Invalid JSON format in config.json.")
        exit(1)
    except Exception as e:
        print(f"❌ Failed to load config.json: {e}")
        exit(1)

cfg = load_config()

ORG_ID = cfg.get("org_id")
API_KEY = cfg.get("api_key")
WS_BASE_URL = cfg.get("ws_url", "wss://api.yourdomain.com/ws/print/")
# PRINTER_TYPE = cfg.get("printer_type", "NETWORK").upper()
PRINTER_TYPE = cfg.get("printer_type", "USB").upper()
USB_VENDOR_ID = int(cfg.get("usb_vendor_id", "0x0000"), 16)
USB_PRODUCT_ID = int(cfg.get("usb_product_id", "0x0000"), 16)
LAN_IP = cfg.get("lan_ip", "127.0.0.1")
LAN_PORT = int(cfg.get("lan_port", 9100))

WS_URL = f"{WS_BASE_URL}{ORG_ID}/?key={API_KEY}"

# ===================================================
# 🪵 Logging Setup
# ===================================================
logging.basicConfig(
    filename="print_agent.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("PrintAgent")

# ===================================================
# 🖨️ Printer Handling
# ===================================================
def print_bill(text: str):
    """Send bill text to the configured printer."""
    try:
        if PRINTER_TYPE == "USB":
            printer = Usb(USB_VENDOR_ID, USB_PRODUCT_ID)
        else:
            printer = Network(LAN_IP, port=LAN_PORT)

        # printer.charcode('CP850')
        # printer._raw(b'\x1B\x21\x20')
        # printer._raw(b'\x1D\x57\x80\x02')
        # printer._raw(b'\x1B\x52\x08')
        # printer.set(align="center", width=2, height=2)
        printer.text(text + "\n")
        printer.cut(mode="PART")  #
        printer.close() 
        logger.info("✅ Bill printed successfully.")
        print("✅ Bill printed successfully.")
    except Exception as e:
        logger.error(f"❌ Print failed: {e}")
        print(f"❌ Print failed: {e}")

# ===================================================
# 🌐 WebSocket Event Handlers
# ===================================================
# def on_message(ws, message):
#     """Triggered when a new print job message is received."""
#     try:
#         data = json.loads(message)
#         logger.info(f"📩 Received print job: {data}")
#         print("📩 Received print job:", data)

#         text = data.get("text")
#         text = text.replace("₹", "Rs.")
#         if text:
#             print_bill(text)
#             time.sleep(0.5)
#         else:
#             logger.warning("⚠️ Received message without 'text' field.")
#             print("⚠️ Received message without 'text' field.")
#     except Exception as e:
#         logger.error(f"⚠️ Error processing message: {e}")
#         print(f"⚠️ Error processing message: {e}")

def on_message(ws, message):
    data = json.loads(message)

    if "escpos" in data:
        raw = base64.b64decode(data["escpos"])
        print(raw)
        printer = Usb(USB_VENDOR_ID, USB_PRODUCT_ID)
        printer._raw(raw)
        printer.close()
        time.sleep(0.5)
        print("🖨 Printed ESC/POS commands")
    else:
        print("⚠ No ESC/POS data received")


def on_error(ws, error):
    logger.error(f"⚠️ WebSocket Error: {error}")
    print(f"⚠️ WebSocket Error: {error}")

def on_close(ws, code, msg):
    """Handles disconnections and auto-reconnects."""
    logger.warning(f"🔌 Disconnected (code={code}, msg={msg}). Reconnecting in 5s...")
    print("🔌 Disconnected from server. Reconnecting in 5s...")
    time.sleep(5)
    connect_ws()

def on_open(ws):
    """Triggered once connection is established."""
    logger.info(f"🔗 Connected securely to {WS_URL}")
    print(f"🔗 Connected securely to {WS_URL}")

# ===================================================
# 🔁 WebSocket Connection Logic
# ===================================================
def connect_ws():
    """Establish WebSocket connection with auto-reconnect."""
    try:
        ws = websocket.WebSocketApp(
            WS_URL,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )
        ws.run_forever(reconnect=5)
    except KeyboardInterrupt:
        logger.info("🛑 Local Print Agent stopped manually.")
        print("🛑 Local Print Agent stopped.")
        exit(0)
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        print(f"❌ Connection failed: {e}")
        time.sleep(5)
        connect_ws()

# ===================================================
# 🚀 Main Entry Point
# ===================================================
if __name__ == "__main__":
    print("🚀 Starting Local Print Agent...")
    logger.info("🚀 Local Print Agent started.")
    print(f"Connecting to {WS_URL}")
    connect_ws()
