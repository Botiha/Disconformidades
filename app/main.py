import asyncio
from app.steps.step1_bizagi import run_step1, setup_logging, load_config
from app.steps.step2_processing import run_step2

async def main():
    setup_logging()
    config = load_config()
    await run_step1(config)
    await run_step2(config)

if __name__ == "__main__":
    asyncio.run(main())
