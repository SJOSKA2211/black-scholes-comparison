import os
import sys
import socket
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv("apps/api/.env")

# Configure minimal logging for deployment check
logging.basicConfig(level=logging.INFO, format='{"step": "deploy_check", "event": "%(message)s"}')
logger = logging.getLogger(__name__)

# Mandatory infrastructure variables per Zero-Mock Policy
MANDATORY_VARS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "REDIS_URL",
    "RABBITMQ_URL",
    "MINIO_ENDPOINT"
]

def check_mandatory_vars():
    logger.info("checking_mandatory_vars")
    from src.config import get_settings
    settings = get_settings()
    
    # We check the raw environment variables first to ensure they are set in the platform
    missing = [v for v in MANDATORY_VARS if not os.getenv(v)]
    if missing:
        msg = f"Zero-Mock Violation: Missing mandatory infrastructure variables: {', '.join(missing)}"
        logger.error(msg)
        logger.info("TIP: You must provide real infrastructure URLs in your platform environment settings (Render/Railway/etc.).")
        raise RuntimeError(msg)
            
    # Check for local/default hostnames
    for v in MANDATORY_VARS:
        url = os.getenv(v, "")
        if any(bad in url.lower() for bad in ["localhost", "127.0.0.1", "://redis", "://rabbitmq", "minio:9000"]):
            msg = f"Zero-Mock Violation: Detected local/default infrastructure URL for {v} ({url}). Use real infrastructure."
            logger.error(msg)
            raise RuntimeError(msg)

    logger.info("mandatory_vars_ok")
    return True

def check_url_reachability(url_str, name, retries=3):
    """
    Strictly follows Zero-Mock: Infrastructure must be reachable.
    """
    logger.info(f"checking_{name}_reachability: {url_str}")
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url_str)
        host = parsed.hostname
        port = parsed.port
        
        # Default ports based on scheme
        if not port:
            if parsed.scheme == "redis": port = 6379
            elif parsed.scheme in ("amqp", "amqps"): port = 5672
            elif parsed.scheme in ("http", "https"): port = 80 if parsed.scheme == "http" else 443
            else:
                logger.error(f"{name}_unsupported_scheme: {parsed.scheme}")
                return False

        if not host:
            logger.error(f"{name}_invalid_url: {url_str}")
            return False

        for i in range(retries):
            logger.info(f"attempting_connection: {host}:{port} (attempt {i+1}/{retries})")
            try:
                with socket.create_connection((host, port), timeout=5):
                    logger.info(f"{name}_reachable")
                    return True
            except Exception as e:
                if i < retries - 1:
                    time.sleep(3)
                    continue
                logger.error(f"{name}_unreachable_error: {str(e)}")
                if host in ("redis", "rabbitmq", "minio"):
                    logger.info(f"TIP: Hostname '{host}' looks like a local Docker default. Ensure your {name.upper()}_URL is correct for production.")
                return False
    except Exception as e:
        logger.error(f"{name}_url_parse_failed: {str(e)}")
        return False
    return False

def check_minio_reachability(endpoint, retries=3):
    """MinIO endpoints are often host:port without a scheme."""
    host = endpoint
    port = 9000
    if ":" in endpoint:
        host, port_str = endpoint.split(":", 1)
        port = int(port_str)
    
    for i in range(retries):
        logger.info(f"attempting_minio_connection: {host}:{port} (attempt {i+1}/{retries})")
        try:
            with socket.create_connection((host, port), timeout=5):
                logger.info("minio_reachable")
                return True
        except Exception as e:
            if i < retries - 1:
                time.sleep(3)
                continue
            logger.error(f"minio_unreachable_error: {str(e)}")
            return False
    return False

def main():
    logger.info("starting_zero_mock_verification")
    
    # 1. Mandatory Variables check (now logs warnings and allows continuation)
    check_mandatory_vars()
        
    # 2. Redis Reachability
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    if not check_url_reachability(redis_url, "redis"):
        sys.exit(1)
    
    # 3. RabbitMQ Reachability
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://rabbitmq_user:JKmaish2025@rabbitmq:5672/")
    if not check_url_reachability(rabbitmq_url, "rabbitmq"):
        sys.exit(1)
    
    # 4. MinIO Reachability
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    if not check_minio_reachability(minio_endpoint):
        sys.exit(1)

    logger.info("zero_mock_verification_passed")


if __name__ == "__main__":
    main()
