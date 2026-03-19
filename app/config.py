import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EVAL_DIR = DATA_DIR / "eval"

DEFAULT_TICKER = "AAPL"
DEFAULT_PERIOD = "1y"
TRADING_DAYS = 252
TRANSACTION_COST_BPS = 10

# Set your Anthropic API key as environment variable ANTHROPIC_API_KEY
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def ensure_ssl_ca_bundle() -> None:
	"""Set SSL env vars to an ASCII-safe CA bundle path for curl-based clients."""
	if os.environ.get("CURL_CA_BUNDLE") and os.environ.get("SSL_CERT_FILE"):
		return

	try:
		import certifi

		source_bundle = Path(certifi.where())
		if not source_bundle.exists():
			return

		target_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "alphamemo"
		target_dir.mkdir(parents=True, exist_ok=True)
		target_bundle = target_dir / "cacert.pem"

		if (not target_bundle.exists()) or (target_bundle.stat().st_mtime < source_bundle.stat().st_mtime):
			shutil.copyfile(source_bundle, target_bundle)

		target_path = str(target_bundle)
		os.environ.setdefault("CURL_CA_BUNDLE", target_path)
		os.environ.setdefault("SSL_CERT_FILE", target_path)
	except Exception:
		# Keep app resilient and allow existing fallback behavior.
		return
