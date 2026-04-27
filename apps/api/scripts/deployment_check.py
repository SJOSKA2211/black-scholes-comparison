import os
import sys
import socket
import logging

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

def check_service(host, port, name, enabled_var=None):
    if enabled_var and os.getenv(enabled_var, "true").lower() != "true":
        logger.info(f"{name}_skipped")
        return True
    
    if host.lower() in ("none", "disabled"):
        logger.info(f"{name}_skipped_explicit")
        return True

    logger.info(f"checking_{name}_reachability: {host}:{port}")
    try:
        with socket.create_connection((host, port), timeout=2):
            logger.info(f"{name}_reachable")
            return True
    except Exception as e:
        logger.warning(f"{name}_unreachable: {str(e)}")
        # We don't fail for optional services, but we warn
        return True

def check_url_reachability(url_str, name):
    if not url_str:
        return True
    
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
            logger.warning(f"{name}_invalid_url: {url_str}")
            return True

        with socket.create_connection((host, port), timeout=2):
            logger.info(f"{name}_reachable")
            return True
    except Exception as e:
        logger.warning(f"{name}_unreachable: {str(e)}")
        return True

def main():
    logger.info("starting_deployment_checks")
    
    # 1. Environment Variables (Critical)
    if not check_env_vars():
        sys.exit(1)
        
    # 2. Redis
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        check_url_reachability(redis_url, "redis")
    else:
        check_service(
            os.getenv("REDIS_HOST", "redis"),
            int(os.getenv("REDIS_PORT", 6379)),
            "redis",
            "REDIS_ENABLED"
        )
    
    # 3. RabbitMQ
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    if rabbitmq_url:
        check_url_reachability(rabbitmq_url, "rabbitmq")
    else:
        check_service(
            os.getenv("RABBITMQ_HOST", "rabbitmq"),
            5672,
            "rabbitmq",
            "RABBITMQ_ENABLED"
        )
    
    # 4. MinIO
    minio_endpoint = os.getenv("MINIO_ENDPOINT")
    if minio_endpoint:
        # MinIO endpoint is usually host:port
        if ":" in minio_endpoint:
            host, port = minio_endpoint.split(":", 1)
            check_service(host, int(port), "minio", "MINIO_ENABLED")
        else:
            check_service(minio_endpoint, 9000, "minio", "MINIO_ENABLED")
    else:
        check_service(
            os.getenv("MINIO_HOST", "minio"),
            int(os.getenv("MINIO_PORT", 9000)),
            "minio",
            "MINIO_ENABLED"
        )

    logger.info("deployment_checks_passed")


if __name__ == "__main__":
    main()
