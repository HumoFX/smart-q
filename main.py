import asyncio

from fastapi import FastAPI, APIRouter
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect
import aiohttp

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

def get_user_json(uuid: str):
    return {
        "data": {
            "id": "uuid",
            "login": "login",
            "image": "https://gravatar.com/avatar/205e460b479e2e5b48aec07710c08d50",
            "email": "email@example.com",
            "phone_number": "+998998996779",
            "name": "Humo",
            "surname": "Otahanov",
            "patronymic": "Gulomboy o'g'li",
        },
        "messages": []
        
    }


async def get_user_data(uuid: str, mocked: bool = False):
    if mocked:
        return get_user_json(uuid)
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.smartq.one/api/v1/user/{uuid}") as resp:
            return await resp.json()


@router.get("/ping")
async def pong():
    return {"ping": "pong!"}


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
                user_data = await get_user_data(data, mocked=True)
                await websocket.send_json(user_data)
                await asyncio.sleep(1)
    except WebSocketDisconnect as e:
        logger.error(e)
        await websocket.close()
        serial_manager.disconnect()
        return
    # if websocket disconnect then close serial connection and websocket and stop loop




app.include_router(router)


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)