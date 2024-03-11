import os
import asyncio
import uuid
from asyncio import sleep
from dataclasses import dataclass

import serial
from fastapi import FastAPI, APIRouter, Request, Response
from serial.serialutil import SerialException
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import json
import ast

from reader.app import SerialManager

from loguru import logger

app = FastAPI(
    title="SMART-Q API",
    description="API for SMART-Q",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

router = APIRouter(
    prefix="/api/v1",
    tags=["api"],
    responses={404: {"messages": [{"message": "Not found", "type": "error"}]}},
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


@dataclass
class ApiGateway:
    base_url: str = "https://ledokol-journal-api.kebzu.com/api/v1"
    # base_url: str = "http://127.0.0.1:8001/api/v1"
    headers: dict = None
    timeout: int = 30
    token: str = None
    refresh_token: str = None

    # guard_id: str = None

    async def get(self, url: str, **kwargs):
        url = f"{self.base_url}/{url}"
        headers = {}
        if self.token:
            headers = {"smart-q": f"{self.token}"}
        if self.refresh_token:
            headers.update({"smart_refresh_token": f"{self.refresh_token}"})
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, **kwargs) as response:
                if response.content_type == "application/json":
                    response_json = await response.json()
                    logger.info(f"Response: {response_json}")
                    return response_json
                else:
                    return await response.text()

    async def post(self, url: str, **kwargs):
        url = f"{self.base_url}/{url}"
        headers = {}
        if self.token:
            headers = {"smart-q": f"{self.token}"}
        if self.refresh_token:
            headers.update({"smart_refresh_token": f"{self.refresh_token}"})
        # set cookies
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, **kwargs) as response:
                if response.content_type == "application/json":
                    response_json = await response.json()
                    logger.info(f"Response: {response_json}")
                    return response_json
                else:
                    return await response.text()


    async def options(self, url: str, **kwargs):
        url = f"{self.base_url}/{url}"
        headers = {}
        if self.token:
            headers = {"smart-q": f"{self.token}"}
        if self.refresh_token:
            headers.update({"smart_refresh_token": f"{self.refresh_token}"})
        async with aiohttp.ClientSession() as session:
            async with session.options(url, headers=headers, **kwargs) as response:
                return await response.json()


async def get_user_data(qr_data: str, mocked: bool = False):
    logger.info(f"UUID: {qr_data}")
    backend_url = "https://ledokol-journal-api.kebzu.com"
    # backend_url = "http://127.0.0.1:8001"
    if mocked:
        return get_user_json(qr_data)
    async with aiohttp.ClientSession() as session:
        logger.info(f"{type(uuid)}")
        str_qr_data = qr_data.replace("'", '"')
        str_dict = str_qr_data.replace("UUID(", "").replace(")", "")
        data = ast.literal_eval(str_dict)
        logger.info(f"Data user: {data}")
        data = dict(data)
        async with session.post(f"{backend_url}/api/v1/admin/smart-q/", json=data
                                ) as resp:
            return await resp.json()


async def set_user_action(data, token, refresh_token):
    url = 'admin/smart-q/log'
    logger.info(f"Action data: {token}")
    api_gateway = ApiGateway(token=token, refresh_token=refresh_token)
    resp = await api_gateway.post(url, json=data)
    return resp


@router.get("/ping")
async def pong():
    return {"ping": "pong!"}


@router.get("/device_status")
async def device_status():
    serial_manager = SerialManager()
    logger.info(f"Device status: {serial_manager.is_connected()}")
    if serial_manager.is_connected():
        return {"status": "connected"}
    else:
        try:
            serial_manager.connect()
            return {"status": "connected"}
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}


@router.get("/{path:path}")
async def catch_all(
        request: Request,
        response: Response,
        path: str,
):
    token = request.cookies.get("access_token_cookie")
    refresh_token = request.cookies.get("refresh_token_cookie")
    api_gateway = ApiGateway(token=token, refresh_token=refresh_token)
    resp = await api_gateway.get(path)
    logger.info(f"Response: {resp}")
    return resp


@router.post("/{path:path}")
async def catch_all(
        request: Request,
        response: Response,
        path: str,
        body: dict = None
):
    token = request.cookies.get("access_token_cookie")
    refresh_token = request.cookies.get("refresh_token_cookie")
    api_gateway = ApiGateway(token=token, refresh_token=refresh_token)
    resp = await api_gateway.post(path, json=body)
    if resp.get("data") and resp["data"].get("token"):
        access_token = resp.get("data").get("token")
        if access_token:
            response.set_cookie("access_token_cookie", access_token)
        refresh_token = resp.get("data").get("refresh_token")
        if refresh_token:
            response.set_cookie("refresh_token_cookie", refresh_token)
        response.set_cookie("is_auth", "true")
    elif path.__contains__("sign-out"):
        response.delete_cookie("access_token_cookie")
        response.delete_cookie("refresh_token_cookie")
        response.delete_cookie("is_auth")
    logger.info(f"Response: {resp}")
    return resp


@router.options("/{path:path}")
async def catch_all(
        request: Request,
        response: Response,
        path: str,
):
    token = request.cookies.get("access_token_cookie")
    refresh_token = request.cookies.get("refresh_token_cookie")
    api_gateway = ApiGateway(token=token, refresh_token=refresh_token)
    return await api_gateway.options(path)


# =========

# Assuming 'logger' is properly configured

async def read_serial_data(websocket: WebSocket, serial_manager: SerialManager):
    # while serial_manager.is_connected():
    data = await serial_manager.read()
    if data:
        user_data = await get_user_data(data, mocked=False)
        await websocket.send_json(user_data)
        await asyncio.sleep(1)


async def handle_serial_error(websocket: WebSocket, message: str, message_type: str):
    await websocket.send_json({"messages": [{"message": message, "type": message_type}]})
    await websocket.close()


async def handle_websocket_messages(websocket: WebSocket, token: str, refresh_token: str):
    data = await websocket.receive_json()
    logger.info(f"Data: {data}")
    if data and data.get("action"):
        resp = await set_user_action(data=data, token=token,
                                     refresh_token=refresh_token)
        response = {
            "data": None,
            "messages": [{"message": "Успешно", "type": "SUCCESS"}],
            "action": "success"
        }
        await websocket.send_json(response)


async def handle_websocket_error(websocket: WebSocket, message: str, message_type: str):
    logger.error(message)
    await websocket.send_json({"messages": [{"message": message, "type": message_type}]})
    await websocket.close()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        serial_manager = SerialManager()
        try:
            serial_manager.connect()
            if serial_manager.is_connected():
                await websocket.send_json({"messages": [{"message": "Устройство подключено", "type": "info"}]})
        except Exception as e:
            await handle_serial_error(websocket, "Устройство не подключено", "error")
            return
        # task_serial = asyncio.create_task(read_serial_data(websocket, serial_manager))
        # task_websocket = asyncio.create_task(handle_websocket_messages(websocket))
        while True:
            token = websocket.cookies.get("access_token_cookie")
            refresh_token = websocket.cookies.get("refresh_token_cookie")
            logger.info(f"Token: {token}")
            await read_serial_data(websocket, serial_manager)
            await handle_websocket_messages(websocket, token, refresh_token)
            # await asyncio.gather(
            #     task_serial,
            #     task_websocket
            # )
    except SerialException as e:
        await handle_serial_error(websocket, "Устройство отключено", "error")
    except WebSocketDisconnect:
        await handle_websocket_error(websocket, "Соединение разорвано", "error")
    except Exception as e:
        logger.error(e)
        await handle_websocket_error(websocket, "Ошибка при обработке сообщений", "error")


# async def read_serial_data(websocket: WebSocket):
#     # Open the serial port
#     seraial_port = os.getenv("SERIAL_PORT", "/dev/cu.usbmodem185021")
#     with serial.Serial(port=seraial_port, baudrate=9600, timeout=1) as ser:
#         while True:
#             # Read data from the serial port
#             serial_data = ser.readline().decode('utf-8').strip()
#             logger.info(f"Serial Data: {serial_data}")
#
#             # Send the serial data to the WebSocket client
#             await websocket.send_text(f"Serial Data: {serial_data}")
#
#             # Receive data from the WebSocket client
#             client_data = await websocket.receive_text()
#             print(f"Received from WebSocket: {client_data}")

# You can process the client_data as needed

# async def read_serial_data(websocket: WebSocket):
#     serial_manager = SerialManager()
#     try:
#         serial_manager.connect()
#         if serial_manager.is_connected():
#             await websocket.send_json({"messages": [{"message": "Устройство подключено", "type": "info"}]})
#     except Exception as e:
#         await websocket.send_json({"messages": [{"message": "Устройство не подключено", "type": "error"}]})
#         await websocket.close()
#         return
#     try:
#         while True:
#             if not serial_manager.is_connected():
#                 await websocket.send_json({"messages": [{"message": "Устройство отключено", "type": "error"}]}),
#                 break
#             data = await serial_manager.read()
#             if data:
#                 user_data = await get_user_data(data, mocked=False)
#                 await websocket.send_json(user_data)
#                 await asyncio.sleep(1)
#     except WebSocketDisconnect as e:
#         logger.error(e)
#         await websocket.send_json({"messages": [{"message": "Соединение разорвано", "type": "error"}]})
#         # await websocket.close()
#         # serial_manager.disconnect()
#         return
#     except SerialException as e:
#         logger.error(e)
#         await websocket.send_json({"messages": [{"message": "Устройство отключено", "type": "error"}]})
#         # await websocket.close()
#         serial_manager.disconnect()
#         return
#     except Exception as e:
#         logger.error(e)
#         await websocket.send_json({"messages": [{"message": "Произошла ошибка при чтеении данных", "type": "error"}]})
#         # await websocket.close()
#         serial_manager.disconnect()
#         return
#
#
# async def handle_websocket_messages(websocket: WebSocket):
#     while True:
#         try:
#             data = await websocket.receive_json()
#             logger.info(f"Data: {data}")
#             if data and data.get("action"):
#                 # resp = await ApiGateway().post(data.get("action"), json=data)
#                 response = {
#                     "data": None,
#                     "messages": [
#                         {
#                             "message": "Успешно",
#                             "type": "SUCCESS"
#                         }
#                     ],
#                     "action": "success"
#                 }
#                 await websocket.send_json(response)
#         except WebSocketDisconnect:
#             logger.info("Websocket disconnected")
#             break
#
# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     try:
#         await websocket.accept()
#         task_serial = asyncio.create_task(read_serial_data(websocket))
#         task_websocket = asyncio.create_task(handle_websocket_messages(websocket))
#         await asyncio.gather(
#             task_serial,
#             task_websocket
#         )
#     except WebSocketDisconnect as e:
#         logger.error(e)
#     await websocket.send_json({"messages": [{"message": "Соединение разорвано", "type": "error"}]})
#     await websocket.close()
#     serial_manager.disconnect()
#     return


# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket, q: str = None):
#     await websocket.accept()
#     serial_manager = SerialManager()
#     logger.info(f"Client state: {websocket.client_state} client: {websocket.client}")
#     # if websocket disconnect then close serial connection and websocket and stop loop
#     if websocket.client_state != WebSocketState.CONNECTED:
#         logger.info(f"Client state: {websocket.client_state}")
#         serial_manager.disconnect()
#         await websocket.close()
#         return
#     try:
#         serial_manager.connect()
#         if serial_manager.is_connected():
#             await websocket.send_json({"messages": [{"message": "Устройство подключено", "type": "info"}]})
#     except Exception as e:
#         await websocket.send_text(str(e))
#         await websocket.close()
#         return
#     try:
#         while True:
#             # if websocket disconnect then close serial connection and websocket and stop loop
#             logger.info(f"Client state: {websocket.client_state}")
#
#             if websocket.client_state != WebSocketState.CONNECTED:
#                 logger.info(f"Client state: {websocket.client_state}")
#                 # serial_manager.disconnect()
#                 await websocket.close()
#                 break
#             if not serial_manager.is_connected():
#                 await websocket.send_json({"messages": [{"message": "Устройство отключено", "type": "error"}]}),
#                 break
#             data = await serial_manager.read()
#             # data = ("{'user_id': 'UUID(04a5820d-a949-4b84-a609-92905a33d57b)', 'meeting_id': 'UUID("
#             #         "293d0ec1-4dd8-4982-b6a1-3e8c014aa552)'}")
#             # await asyncio.sleep(1)
#             logger.info(f"Data: {data}")
#             if data:
#                 user_data = await get_user_data(data, mocked=False)
#                 await websocket.send_json(user_data)
#                 await asyncio.sleep(1)
#             websocket_data = await websocket.receive_json()
#             if websocket_data:
#                 if websocket_data.get("action"):
#                     resp = await ApiGateway().post(websocket_data.get("action"), json=websocket_data)
#                     response = {
#                         "data": None,
#                         "messages": [
#                             {
#                                 "message": "Успешно",
#                                 "type": "SUCCESS"
#                             }
#                         ],
#                         "action": "success"
#                     }
#                     await websocket.send_json(response)
#
#     except WebSocketDisconnect as e:
#         logger.error(e)
#         await websocket.send_json({"messages": [{"message": "Соединение разорвано", "type": "error"}]})
#         # await websocket.close()
#         # serial_manager.disconnect()
#         return
#     except Exception as e:
#         logger.error(e)
#         await websocket.send_json({"messages": [{"message": "Произошла ошибка", "type": "error"}]})
#         # await websocket.close()
#         serial_manager.disconnect()
#         return
#     # if websocket disconnect then close serial connection and websocket and stop loop


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
