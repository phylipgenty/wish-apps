import httpx
from fastapi import HTTPException
from ..config import settings

class VTUService:
    def __init__(self):
        # Live API base URL (no trailing slash)
        self.base_url = "https://inlomax.com/api"
        self.api_key = settings.INLOMAX_API_KEY
        self.timeout = settings.INLOMAX_TIMEOUT

    async def _request(self, endpoint: str, payload: dict):
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)

        if resp.status_code != 200:
            raise HTTPException(502, f"Inlomax API error: {resp.text}")

        data = resp.json()
        if data.get("status") != "success":
            raise HTTPException(502, f"Inlomax transaction failed: {data.get('message', 'Unknown error')}")
        return data

    async def buy_airtime(self, phone: str, amount: float, network: str):
        service_ids = {"MTN": "1", "AIRTEL": "2", "GLO": "3", "9MOBILE": "4"}
        service_id = service_ids.get(network.upper())
        if not service_id:
            raise HTTPException(400, f"Unsupported network: {network}")

        payload = {
            "mobileNumber": phone,
            "amount": amount,
            "serviceID": service_id
        }
        return await self._request("airtime", payload)

    async def buy_data(self, phone: str, plan_id: str, network: str):
        # plan_id is already the numeric Service ID from your frontend dropdown
        payload = {
            "mobileNumber": phone,
            "serviceID": plan_id
        }
        return await self._request("data", payload)