"""
Standalone model training script.

Loads all price + supplemental data from the database and trains
XGBoost quantile models for every region/hay_type/grade/horizon segment.

Run:  python scripts/train_model.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    # Quick check — only train if we have data
    from app.database import AsyncSessionLocal, engine
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM hay_prices"))
        count = result.scalar()

    if not count or count < 100:
        logger.warning("Not enough data for training (found %s rows). Run seed_data.py first.", count)
        return

    logger.info("Starting model training with %d price records…", count)

    from app.ml.trainer import train_all
    summary = await train_all()
    logger.info("Training summary: %s", summary)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
