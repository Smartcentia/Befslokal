import semantic_kernel as sk

import asyncio

async def test_sk():
    kernel = sk.Kernel()
    print(f"✅ Kernel initialized: {kernel}")
    return True

if __name__ == "__main__":
    asyncio.run(test_sk())
