import os
import sys
import socket
import logging
import time

# Configure minimal logging for deployment check
logging.basicConfig(level=logging.INFO, format='{"step": "deploy_check", "event": "%(message)s"}')
logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
]

def check_env_vars():
    logger.info("checking_env_vars")
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        logger.error(f"missing_env_vars: {', '.join(missing)}")
        return False
    logger.info("env_vars_ok")
    return True

def check_service(host, port, name, retries=3):
    """
    Check if a service is reachable. 
    Strictly follows Zero-Mock: Infrastructure is mandatory.
    """
    for i in range(retries):
        logger.info(f"checking_{name}_reachability: {host}:{port} (attempt {i+1}/{retries})")
        try:
            with socket.create_connection((host, port), timeout=3):
                logger.info(f"{name}_reachable")
                return True
        except Exception as e:
            if i < retries - 1:
                time.sleep(2)
                continue
            logger.error(f"{name}_unreachable_error: {str(e)}. Zero-Mock Violation.")
            if host in ("redis", "rabbitmq", "minio"):
                logger.info(f"TIP: Hostname '{host}' looks like a local Docker name. Ensure it is correct for production.")
            return False
    return False


def check_url_reachability(url_str, name):
    if not url_str:
        logger.error(f"{name}_url_missing")
        return False
    
    logger.info(f"checking_{name}_url_reachability: {url_str}")
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url_str)
        host = parsed.hostname
        port = parsed.port
        
        # Default ports if missing in URL
        if not port:
            if parsed.scheme == "redis": port = 6379
            elif parsed.scheme in ("amqp", "amqps"): port = 5672
            elif parsed.scheme in ("http", "https"): port = 80 if parsed.scheme == "http" else 443
            else: port = 80

        if not host:
            logger.error(f"{name}_invalid_url: {url_str}")
            return False

        with socket.create_connection((host, port), timeout=3):
            logger.info(f"{name}_reachable")
            return True
    except Exception as e:
        logger.error(f"{name}_unreachable: {str(e)}")
        return False

def main():
    logger.info("starting_deployment_checks")
    
    # 1. Environment Variables (Critical)
    if not check_env_vars():
        sys.exit(1)
        
    # 2. Redis
    redis_url = os.getenv("REDIS_URL")
    redis_ok = False
    if redis_url:
        redis_ok = check_url_reachability(redis_url, "redis")
    else:
        redis_ok = check_service(
            os.getenv("REDIS_HOST", "redis"),
            int(os.getenv("REDIS_PORT", 6379)),
            "redis"
        )
    if not redis_ok:
        sys.exit(1)
    
    # 3. RabbitMQ
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    rabbitmq_ok = False
    if rabbitmq_url:
        rabbitmq_ok = check_url_reachability(rabbitmq_url, "rabbitmq")
    else:
        rabbitmq_ok = check_service(
            os.getenv("RABBITMQ_HOST", "rabbitmq"),
            5672,
            "rabbitmq"
        )
    if not rabbitmq_ok:
        sys.exit(1)
    
    # 4. MinIO
    minio_endpoint = os.getenv("MINIO_ENDPOINT")
    minio_ok = False
    if minio_endpoint:
        # MinIO endpoint is usually host:port
        if ":" in minio_endpoint:
            host, port = minio_endpoint.split(":", 1)
            minio_ok = check_service(host, int(port), "minio")
        else:
            minio_ok = check_service(minio_endpoint, 9000, "minio")
    else:
        minio_ok = check_service(
            os.getenv("MINIO_HOST", "minio"),
            int(os.getenv("MINIO_PORT", 9000)),
            "minio"
        )
    if not minio_ok:
        sys.exit(1)

    logger.info("deployment_checks_passed")


if __name__ == "__main__":
    main()
