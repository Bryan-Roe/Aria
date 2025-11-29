"""
Selenium E2E test for Aria object sync using containerized Chrome.

This test uses Selenium with a remote Chrome instance (from Docker container).
It's ideal for CI/CD environments where you want isolated browser instances.

Requirements:
- selenium installed: pip install selenium
- Chrome container running: docker run -d -p 4444:4444 --shm-size=2g selenium/standalone-chrome:latest
- Or use SELENIUM_REMOTE_URL env var for custom Selenium Grid

Docker setup:
  docker run -d -p 4444:4444 -p 5900:5900 --shm-size=2g selenium/standalone-chrome:latest
  
  VNC viewer (optional): Connect to localhost:5900 to watch tests run (password: secret)
"""

import time
import requests
import socket
import subprocess
from pathlib import Path
import pytest
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conditionally import selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not installed")

# Skip all tests if selenium not available
pytestmark = pytest.mark.skipif(
    not SELENIUM_AVAILABLE,
    reason="Selenium not installed"
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ARIA_WEB = REPO_ROOT / 'aria_web'
SERVER_URL = os.environ.get('ARIA_SERVER_URL', 'http://localhost:8000')
SELENIUM_REMOTE_URL = os.environ.get('SELENIUM_REMOTE_URL', 'http://localhost:4444/wd/hub')


def is_port_open(port=8000, host='127.0.0.1'):
    """Check if a port is open."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.4)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def ensure_server_running():
    """Start the Aria server if not already running."""
    if is_port_open(8000):
        logger.info("Server already running")
        return None

    logger.info("Starting Aria server...")
    proc = subprocess.Popen(
        ["python3", "server.py"], 
        cwd=str(ARIA_WEB), 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )

    # Wait for server to be available
    for i in range(30):
        if is_port_open(8000):
            logger.info(f"Server started successfully after {i+1} attempts")
            return proc
        time.sleep(0.2)

    proc.kill()
    raise RuntimeError('Failed to start Aria server')


def wait_for_object(name, timeout=4.0):
    """Wait for an object to appear in server state."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{SERVER_URL}/api/aria/state", timeout=1.0)
            if r.ok and 'objects' in r.json() and name in r.json()['objects']:
                return r.json()['objects'][name]
        except Exception as e:
            logger.debug(f"Waiting for object {name}: {e}")
        time.sleep(0.12)
    return None


def is_selenium_hub_ready():
    """Check if Selenium hub is accessible."""
    try:
        response = requests.get(f"{SELENIUM_REMOTE_URL.rsplit('/wd/hub', 1)[0]}/wd/hub/status", timeout=2)
        if response.ok:
            status = response.json()
            if status.get('value', {}).get('ready'):
                logger.info("Selenium hub is ready")
                return True
            logger.warning(f"Selenium hub not ready: {status}")
    except Exception as e:
        logger.warning(f"Selenium hub not accessible: {e}")
    return False


def create_remote_driver(max_retries=3):
    """Create a remote WebDriver with retry logic."""
    # Check if Selenium hub is ready
    if not is_selenium_hub_ready():
        raise Exception("Selenium hub is not ready or not accessible")
    
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting to Selenium hub at {SELENIUM_REMOTE_URL} (attempt {attempt + 1}/{max_retries})...")
            driver = webdriver.Remote(
                command_executor=SELENIUM_REMOTE_URL,
                options=chrome_options
            )
            logger.info(f"Connected successfully. Session ID: {driver.session_id}")
            return driver
        except Exception as e:
            last_error = e
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    # All retries failed
    error_msg = f"Failed to connect to Selenium hub after {max_retries} attempts. Last error: {last_error}"
    logger.error(error_msg)
    raise Exception(error_msg)


@pytest.mark.selenium
def test_selenium_add_pickup_drop():
    """Test object sync using containerized Chrome via Selenium."""
    # Ensure server is running
    proc = ensure_server_running()
    started_proc = proc is not None

    # Generate unique object name
    name = f"e2e_sel_{int(time.time()*1000)}"

    driver = None
    try:
        # Create remote WebDriver
        try:
            driver = create_remote_driver()
        except Exception as e:
            pytest.skip(f"Selenium hub not available: {e}")
            return

        # Navigate to Aria web interface
        logger.info(f"Navigating to {SERVER_URL}")
        driver.get(SERVER_URL)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.info(f"Page loaded: {driver.title}")

        # Add object via JavaScript
        logger.info(f"Adding object '{name}' with emoji 🧸")
        driver.execute_script(f"addObject('{name}', '🧸')")
        
        # Wait for object to appear on server
        obj = wait_for_object(name, timeout=6.0)
        assert obj is not None, f"Server didn't report newly added object {name}"
        logger.info(f"Object added successfully: {obj}")

        # Pick it up
        logger.info(f"Picking up object '{name}'")
        driver.execute_script(f"pickUpObject('{name}')")

        # Wait for server state 'held'
        deadline = time.time() + 4.0
        held = False
        while time.time() < deadline:
            try:
                r = requests.get(f"{SERVER_URL}/api/aria/state", timeout=1.0)
                state = r.json().get('objects', {}).get(name, {}).get('state')
                if state == 'held':
                    held = True
                    logger.info(f"Object '{name}' is now held")
                    break
                logger.debug(f"Waiting for held state, current: {state}")
            except Exception as e:
                logger.debug(f"Error checking state: {e}")
            time.sleep(0.1)
        
        assert held, f'Object {name} not marked held on server after pickUpObject'

        # Drop
        logger.info(f"Dropping object '{name}'")
        driver.execute_script('dropObject()')
        dropped = wait_for_object(name, timeout=5.0)
        assert dropped is not None, f"Object {name} disappeared after drop"
        assert dropped.get('state') in ['on_stage', 'on_table'], f"Unexpected state after drop: {dropped.get('state')}"
        logger.info(f"Object dropped successfully: {dropped}")

        # Cleanup: remove object
        logger.info(f"Removing object '{name}'")
        r = requests.post(
            f"{SERVER_URL}/api/aria/object", 
            json={'action': 'remove', 'object': {'id': name}}
        )
        assert r.ok, f"Failed to remove object: {r.status_code} {r.text}"
        logger.info("Object removed successfully")

    finally:
        # Close browser
        if driver:
            logger.info("Closing browser session")
            driver.quit()

        # Stop server if we started it
        if started_proc and proc:
            logger.info("Stopping Aria server...")
            proc.kill()
            proc.wait(timeout=2)


if __name__ == "__main__":
    # Allow running this test directly
    pytest.main([__file__, "-v", "-s"])
