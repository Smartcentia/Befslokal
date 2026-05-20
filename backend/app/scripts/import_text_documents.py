import asyncio
import os
import sys
import glob

# Add backend to path
sys.path.append(os.getcwd())
# Also add backend folder itself if running from root
if os.path.exists("backend"):
    sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
# Try loading env from backend/.env or .env
if os.path.exists(os.path.join(os.getcwd(), 'backend', '.env')):
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
else:
    load_dotenv(os.path.join(os.getcwd(), '.env'))

from sqlalchemy import select, func, text as sql_text
from sqlalchemy.orm import selectinload

# Import base to register all models
from app.db.base import Base 
# TextContent model
from app.models.text_content import TextContent

# Services
from app.db.session import SessionLocal
from app.services.text_processor import chunk_text
from app.services.embeddings import generate_embeddings

async def import_text_documents():
    docs_dir = "backend/docs"
    # Helper for paths
    if not os.path.exists(docs_dir):
        if os.path.exists("docs"):
            docs_dir = "docs"
        elif os.path.exists("../docs"):
            docs_dir = "../docs"
        else:
            print(f"Error: Docs directory not found at {docs_dir}")
            return

    print(f"Importing documents from: {docs_dir}")
    
    # Get all .txt and .md files
    files = glob.glob(os.path.join(docs_dir, "*.txt")) + glob.glob(os.path.join(docs_dir, "*.md"))
    
    print(f"Found {len(files)} files to import.")
    
    async with SessionLocal() as session:
        imported_count = 0
        skipped_count = 0
        
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Skip CSV/Excel instructions or raw data definitions if not useful as text
            if "CSV" in filename or "import" in filename.lower():
                 # Maybe skip import instructions?
                 pass
            
            # Check if already imported
            # We use source_file as the identifier
            stmt = select(TextContent).where(TextContent.source_file == filename).limit(1)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"Skipping {filename} (already imported)")
                skipped_count += 1
                continue
                
            print(f"Importing {filename}...")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue
                
            # Chunk content
            chunks = chunk_text(content, chunk_size=1500, chunk_overlap=200)
            
            if not chunks:
                print(f"Warning: No content in {filename}")
                continue
                
            # Generate embeddings
            try:
                embeddings = generate_embeddings(chunks)
            except Exception as e:
                print(f"Error generating embeddings for {filename}: {e}")
                continue

            # Save to DB
            for i, chunk_str in enumerate(chunks):
                text_doc = TextContent(
                    source_type="documentation",
                    source_file=filename,
                    content=chunk_str,
                    chunk_index=i,
                    category="manual_import",
                    search_vector=func.to_tsvector('norwegian', chunk_str),
                    embedding=embeddings[i]
                )
                session.add(text_doc)
            
            imported_count += 1
            print(f"Imported {filename} ({len(chunks)} chunks)")
            
        await session.commit()
        print(f"Finished. Imported: {imported_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    asyncio.run(import_text_documents())
