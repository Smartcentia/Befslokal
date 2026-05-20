import asyncio
import json
import asyncpg
import httpx
import os
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

async def download_image(url: str, property_id: str, output_dir: Path) -> str:
    """Download image and save to output directory"""
    if not url:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            
            # Get file extension from URL
            ext = url.split(".")[-1].split("?")[0]
            if ext not in ["jpg", "jpeg", "png", "webp"]:
                ext = "jpg"
            
            # Save file
            filename = f"{property_id}.{ext}"
            filepath = output_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✓ Downloaded image: {filename}")
            return str(filepath)
    except Exception as e:
        print(f"✗ Failed to download {url}: {e}")
        return None

async def main():
    # Load matches
    with open("bufdir_matches.json", "r") as f:
        matches = json.load(f)
    
    print(f"Processing {len(matches)} matched properties...")
    
    # Create images directory
    images_dir = Path("../frontend/public/bufdir_images")
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    try:
        for match in matches:
            inst = match["institution"]
            prop = match["property"]
            property_id = prop["id"]
            
            print(f"\n=== Processing: {inst['name']} ===")
            
            # Download image if available
            image_path = None
            if inst.get("image_url"):
                image_path = await download_image(inst["image_url"], property_id, images_dir)
            
            # Prepare enriched data
            bufdir_data = {
                "bufdir_id": inst.get("id"),
                "bufdir_name": inst.get("name"),
                "bufdir_url": inst.get("bufdir_url"),
                "legal_bases": inst.get("legal_bases", []),
                "owner_type": inst.get("owner_type"),
                "email": inst.get("email"),
                "phone": inst.get("phone"),
                "location": inst.get("location"),
                "description": inst.get("description"),
                "image_path": f"/bufdir_images/{Path(image_path).name}" if image_path else None
            }
            
            # Update property external_data
            await conn.execute("""
                UPDATE properties
                SET external_data = COALESCE(external_data, '{}'::jsonb) || $1::jsonb
                WHERE property_id = $2
            """, json.dumps({"bufdir": bufdir_data}), property_id)
            
            print(f"✓ Updated database for property {prop['name']}")
            print(f"  - Legal bases: {', '.join(bufdir_data['legal_bases'])}")
            print(f"  - Owner type: {bufdir_data['owner_type']}")
            print(f"  - Contact: {bufdir_data['email'] or 'N/A'}")
        
        print(f"\n=== Summary ===")
        print(f"Updated {len(matches)} properties with Bufdir data")
        print(f"Images saved to: {images_dir}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
