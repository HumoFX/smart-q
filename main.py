import asyncio

from fastapi import FastAPI, APIRouter
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect

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
    try:
        while True:
            # if websocket disconnect then close serial connection and websocket and stop loop
            # logger.info(f"Client state: {websocket.client_state}")

            if websocket.client_state != WebSocketState.CONNECTED:
                logger.info(f"Client state: {websocket.client_state}")
                serial_manager.disconnect()
                await websocket.close()
                break
            if not serial_manager.is_connected():
                await websocket.send_text("Device not found")
                break
            data = serial_manager.read()
            if data:
                await websocket.send_text(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect as e:
        logger.error(e)
        await websocket.close()
        serial_manager.disconnect()
        return
    # if websocket disconnect then close serial connection and websocket and stop loop




app.include_router(router)
