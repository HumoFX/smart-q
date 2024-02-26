import asyncio
import uuid
from dataclasses import dataclass

from fastapi import FastAPI, APIRouter
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect
import aiohttp
import json
import ast

from reader.app import SerialManager

from loguru import logger

app = FastAPI(
    title="SMART-Q API",
    description="API for SMART-Q",
)

router = APIRouter(
    prefix="/api/v1",
    tags=["api"],
    responses={404: {"description": "Not found"}},
)

def get_uuid():
    return uuid.uuid4()


def get_user_json(uuid: str):
    return {
        "id": uuid,
        "data": {
            "full_name": "Humo Otahanov Gulomboy o'g'li",
            "images": [
                {
                    "url": "https://robohash.org/c28be6a9c3d77bb98112d765d6e6dea5?set=set4&bgset=&size=600x600",
                    "type": "photo"
                }
            ],
            "email": "email@example.com",
            "phone_number": "+998998996779",
        },
        "messages": []

    }


<<<<<<< HEAD
async def get_user_data(uuid, mocked: bool = False):
=======
@dataclass
class ApiGateway:
    base_url: str = None
    headers: dict = None
    timeout: int = 30
    session: aiohttp.ClientSession = None

    async def get(self, url: str, **kwargs):
        url = f"{self.base_url}/{url}"
        async with self.session.get(url, **kwargs) as response:
            return await response.json()

    async def post(self, url: str, **kwargs):
        url = f"{self.base_url}/{url}"
        async with self.session.post(url, **kwargs) as response:
            return await response.json()


async def get_user_data(uuid: str, mocked: bool = False):
>>>>>>> 02f1b3b14457b82f30734683f613a35d41c531bb
    if mocked:
        return get_user_json(uuid)
    async with aiohttp.ClientSession() as session:
        print(type(uuid))
        str_uuid= uuid.replace("'", '"')
        print(type(str_uuid))
        print(str_uuid)
        str_dict = str_uuid.replace("UUID(", "").replace(")", "")
        print(str_dict)
        data = ast.literal_eval(str_dict)
        # data = json.loads(str_uuid)
        # print(json.loads(uuid.encode("utf-8")))
        # str_dict = eval(uuid)
        # print({"scan": str_dict})
        async with session.post(f"http://192.168.0.106:8000/api/v1/admin/smart-q", json=data
                                ) as resp:
            return await resp.json()


@router.get("/ping")
async def pong():
    return {"ping": "pong!"}


@router.get("/{path:path}")
async def catch_all(
        path: str,
):
    api_gateway = ApiGateway()
    return await api_gateway.get(path)


@router.post("/{path:path}")
async def catch_all(
        path: str,
        body: dict
):
    api_gateway = ApiGateway()
    return await api_gateway.post(path, json=body)


@router.get("/device_status")
async def device_status():
    # check serial connection
    serial_manager = SerialManager()
    if serial_manager.is_connected():
        return {"status": "connected"}
    else:
        try:
            serial_manager.connect()
            return {"status": "connected"}
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, q: str = None):
    await websocket.accept()
    serial_manager = SerialManager()
    logger.info(f"Client state: {websocket.client_state} client: {websocket.client}")
    # if websocket disconnect then close serial connection and websocket and stop loop
    if websocket.client_state != WebSocketState.CONNECTED:
        logger.info(f"Client state: {websocket.client_state}")
        serial_manager.disconnect()
        await websocket.close()
        return
    try:
        serial_manager.connect()
    except Exception as e:
        await websocket.send_text(str(e))
        await websocket.close()
        return
    if serial_manager.is_connected():
        await websocket.send_text("Device connected")
    try:
        while True:
            # if websocket disconnect then close serial connection and websocket and stop loop
            logger.info(f"Client state: {websocket.client_state}")

            if websocket.client_state != WebSocketState.CONNECTED:
                logger.info(f"Client state: {websocket.client_state}")
                serial_manager.disconnect()
                await websocket.close()
                break
            if not serial_manager.is_connected():
                await websocket.send_text("Device not found")
                break
            data = await serial_manager.read()
            if data:
                user_data = await get_user_data(data, mocked=False)
                await websocket.send_json(user_data)
                await asyncio.sleep(1)
    except WebSocketDisconnect as e:
        logger.error(e)
        await websocket.close()
        serial_manager.disconnect()
        return
    # if websocket disconnect then close serial connection and websocket and stop loop


app.include_router(router)
<<<<<<< HEAD


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
=======
>>>>>>> 02f1b3b14457b82f30734683f613a35d41c531bb
