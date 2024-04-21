from dotenv import load_dotenv
import os

load_dotenv()

# Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")

# Deploy
PORT = os.environ.get("PORT")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Personal info
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

# T-Mobile
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")

# iProxy
IPROXY_LOGIN = os.environ.get("IPROXY_LOGIN")
IPROXY_PASS = os.environ.get("IPROXY_PASS")
IPROXY_TOKEN = os.environ.get("IPROXY_TOKEN")
AUTH_HEADER = {"Authorization": IPROXY_TOKEN}
BASE_API_URL = 'https://api.iproxy.online/v1/'

# Payment methods
PM_BINANCE_USDT_TRC20 = os.environ.get("PM_BINANCE_USDT_TRC20")
PM_BINANCE_PAYID = os.environ.get("PM_BINANCE_PAYID")
PM_PRIVATBANK = os.environ.get("PM_PRIVATBANK")
PM_PEKAOBANK = os.environ.get("PM_PEKAOBANK")