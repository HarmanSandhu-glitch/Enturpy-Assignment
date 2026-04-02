"""Seed script — loads all sample JSON files into the database."""
import asyncio
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db
from backend.database import AsyncSessionFactory
from backend.auth.api_key import seed_api_keys
from backend.ingestion.fetcher import load_from_files


async def main():
    print("Initializing DB...")
    await init_db()
    async with AsyncSessionFactory() as session:
        await seed_api_keys(session)

    print("Loading sample data...")
    events = await load_from_files()
    print(f"Done. Price changes detected: {len(events)}")
    print("Dev API key: dev-key")


if __name__ == "__main__":
    asyncio.run(main())
