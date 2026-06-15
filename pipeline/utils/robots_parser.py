"""
utils/robots_parser.py — Robots.txt parsing engine.
"""

import urllib.robotparser
import requests
from pipeline.utils.logger import get_logger

logger = get_logger("robots_parser")


class RobotsParser:
    """
    Standard, robust robots.txt parser using Python's urllib.robotparser.
    Maintains a local cache of the parsed policies.
    """
    def __init__(self, site_url: str):
        # Remove trailing slash to construct standard robots.txt URL
        self.site_url = site_url.rstrip("/")
        self.robots_url = f"{self.site_url}/robots.txt"
        self.rp = urllib.robotparser.RobotFileParser()
        self.is_loaded = False

    def load(self) -> None:
        """Fetch and parse robots.txt rules from the target site."""
        try:
            logger.info(f"[robots] Fetching robots.txt rules from: {self.robots_url}")
            resp = requests.get(self.robots_url, timeout=10)
            if resp.status_code == 200:
                # Standard robotparser parses line-by-line
                self.rp.parse(resp.text.splitlines())
                self.is_loaded = True
                logger.info("[robots] Successfully loaded robots.txt rules.")
            else:
                logger.warning(f"[robots] Robots.txt returned status: {resp.status_code}. Defaulting to allow all.")
        except Exception as e:
            logger.error(f"[robots] Failed to load robots.txt rules: {e}. Defaulting to allow all.")

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if a given URL path is allowed for crawling.
        Always returns True if robots.txt could not be loaded or parsed.
        """
        if not self.is_loaded:
            return True
        try:
            return self.rp.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning(f"[robots] Error checking rules for '{url}': {e}. Assuming allowed.")
            return True
