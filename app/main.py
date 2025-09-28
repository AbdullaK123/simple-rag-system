from app.config.logging import logger, setup_logging

def main():
    # Ensure logging is configured (idempotent)
    setup_logging()
    logger.info("Hello from app!")


if __name__ == "__main__":
    main()
