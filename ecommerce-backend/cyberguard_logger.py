import httpx

CYBERGUARD_URL = "http://127.0.0.1:9000/api/log"


async def send_to_cyberguard(payload: dict) -> None:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(CYBERGUARD_URL, json=payload)
    except Exception:
        # CyberGuard reachable nahi hai - chup chaap ignore karo,
        # BharatStore ka asli kaam kabhi block/fail nahi hona chahiye
        pass
