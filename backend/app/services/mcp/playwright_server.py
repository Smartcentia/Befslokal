import logging
import base64
from playwright.async_api import async_playwright, Page, Browser, Playwright
from app.services.mcp.handler import mcp_handler

logger = logging.getLogger(__name__)

class PlaywrightSession:
    """
    Singleton to manage a persistent browser session.
    This allows agents to perform multi-step workflows (login -> navigate -> extract).
    """
    _instance = None
    
    def __init__(self):
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.page: Page = None
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PlaywrightSession()
        return cls._instance
        
    async def start(self):
        if not self.playwright:
            logger.info("Starting Playwright...")
            self.playwright = await async_playwright().start()
        
        if not self.browser:
            logger.info("Launching Chromium...")
            self.browser = await self.playwright.chromium.launch(headless=True)
            
        if not self.page:
            logger.info("Creating new page context...")
            self.page = await self.browser.new_page()
            
    async def ensure_active(self):
        if not self.page or self.page.is_closed():
            await self.start()
            
    async def stop(self):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.browser = None
        self.playwright = None

# Global session instance
session = PlaywrightSession.get_instance()

@mcp_handler.register_tool(
    name="browser_navigate",
    description="Navigate the browser to a specific URL.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to navigate to"}
        },
        "required": ["url"]
    }
)
async def browser_navigate_tool(url: str):
    try:
        await session.ensure_active()
        await session.page.goto(url, timeout=30000)
        title = await session.page.title()
        return f"Successfully navigated to {url}. Page Title: {title}"
    except Exception as e:
        logger.error(f"Browser navigation failed: {e}")
        return f"Error navigating to {url}: {str(e)}"

@mcp_handler.register_tool(
    name="browser_click",
    description="Click an element on the current page identified by a CSS selector.",
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector for the element to click"}
        },
        "required": ["selector"]
    }
)
async def browser_click_tool(selector: str):
    try:
        await session.ensure_active()
        await session.page.click(selector, timeout=5000)
        return f"Clicked element: {selector}"
    except Exception as e:
        logger.error(f"Browser click failed: {e}")
        return f"Error clicking {selector}: {str(e)}"

@mcp_handler.register_tool(
    name="browser_fill",
    description="Fill a text input on the current page.",
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector for the input field"},
            "value": {"type": "string", "description": "The value to type into the field"}
        },
        "required": ["selector", "value"]
    }
)
async def browser_fill_tool(selector: str, value: str):
    try:
        await session.ensure_active()
        await session.page.fill(selector, value, timeout=5000)
        return f"Filled {selector} with value."
    except Exception as e:
        logger.error(f"Browser fill failed: {e}")
        return f"Error filling {selector}: {str(e)}"

@mcp_handler.register_tool(
    name="browser_get_content",
    description="Get the text content of the current page.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def browser_get_content_tool():
    try:
        await session.ensure_active()
        # Get body text, maybe clean it up?
        # innerText is usually better than content for reading
        text = await session.page.evaluate("document.body.innerText")
        return text[:10000] # Limit response size
    except Exception as e:
        logger.error(f"Browser get content failed: {e}")
        return f"Error getting content: {str(e)}"

@mcp_handler.register_tool(
    name="browser_screenshot",
    description="Take a screenshot of the current page. Returns a base64 encoded string.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def browser_screenshot_tool():
    try:
        await session.ensure_active()
        screenshot_bytes = await session.page.screenshot(full_page=False)
        base64_str = base64.b64encode(screenshot_bytes).decode('utf-8')
        return f"Screenshot taken (base64 size: {len(base64_str)} chars). [BASE64_IMAGE]"
    except Exception as e:
        logger.error(f"Browser screenshot failed: {e}")
        return f"Error taking screenshot: {str(e)}"

@mcp_handler.register_tool(
    name="browser_evaluate",
    description="Execute JavaScript in the current page context.",
    parameters={
        "type": "object",
        "properties": {
            "script": {"type": "string", "description": "JavaScript code to execute"}
        },
        "required": ["script"]
    }
)
async def browser_evaluate_tool(script: str):
    try:
        await session.ensure_active()
        result = await session.page.evaluate(script)
        return str(result)
    except Exception as e:
        logger.error(f"Browser evaluate failed: {e}")
        return f"Error evaluating script: {str(e)}"
