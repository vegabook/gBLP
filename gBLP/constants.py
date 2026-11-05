# constants for message types from the bbg terminal
MAX_MESSAGE_LENGTH = 50 * 1024 * 1024

PONG_SECONDS_TIMEOUT = 5

DEFAULT_FIELDS = ["LAST_PRICE", "LAST_PRICE_TIME_TODAY_REALTIME", "IS_DELAYED_STREAM"]

# heartbeat: a server-side subscription to a 24/7 instrument. If it stops ticking
# the Bloomberg feed is treated as stale and the session is restarted.
HEARTBEAT_TOPIC = "XBT Curncy"
HEARTBEAT_FIELDS = ["LAST_PRICE"]
HEARTBEAT_INTERVAL = 30 # seconds, conflated subscription interval and watchdog check period
HEARTBEAT_STALE_AFTER = 150 # seconds without a tick before the feed is stale
HEARTBEAT_RESTART_EVERY = 300 # seconds between session restarts while stale
HEARTBEAT_CID = "gblp-heartbeat"

