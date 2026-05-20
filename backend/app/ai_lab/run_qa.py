import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from app.ai_lab.plugins.browser_plugin import BrowserPlugin

async def run_smoke_test():
    print("🕵️‍♂️ Starting QA Agent (Local Smoke Test)...")
    browser = BrowserPlugin()
    
    base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    targets = [
        f"{base_url}",
        f"{base_url}/dashboard",
        f"{base_url}/properties",
        f"{base_url}/lab" 
    ]
    
    results = []
    
    for url in targets:
        print(f"\n🌐 Visiting: {url} ...")
        
        # 1. Fetch
        page_data = browser.fetch_page(url)
        status = page_data.get("status")
        
        if status == "error":
            print(f"❌ Connection Failed: {page_data.get('message')}")
            results.append({"url": url, "status": "FAIL", "details": "Connection Error"})
            continue
            
        load_time = page_data.get("load_time_ms")
        print(f"✅ Status: {status} | ⏱️ Load: {load_time}ms")
        
        # 2. A11y Check
        html = page_data.get("html", "")
        a11y_report = browser.check_accessibility(html)
        score = a11y_report.get("score")
        issues = a11y_report.get("issues", [])
        
        print(f"♿ A11y Score: {score}/100")
        if issues:
            for issue in issues:
                print(f"   ⚠️ {issue}")
        else:
            print("   ✨ No obvious accessibility issues found.")
            
        # 3. Content Check
        text = browser.extract_text(html)
        print(f"📄 Content Preview: {text[:100].replace(chr(10), ' ')}...")
        
        results.append({
            "url": url,
            "status": "PASS" if status == 200 else "WARN",
            "load_time": load_time,
            "a11y_score": score
        })
        
    print("\n" + "="*40)
    print("📊 TEST SUMMARY")
    print("="*40)
    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"{icon} {r['url']:<35} | {r['status']} | {r['load_time']}ms | A11y: {r.get('a11y_score', 0)}")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
