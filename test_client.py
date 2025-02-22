import asyncio
import websockets
import json

async def websocket_client():
    uri = "ws://39.107.101.110:38765"  # 连接到 FastAPI 服务器的 WebSocket 地址
    async with websockets.connect(uri) as websocket:
        while True:
            # 发送消息到服务器
            message = {"task_id": "123", "task_type": "test", "content":{}}
            print(f"Sending message to server: {message}")
            await websocket.send(json.dumps(message))

            # 等待并接收来自服务器的响应
            response = await websocket.recv()
            print(f"Received from server: {response}")
            await asyncio.sleep(1)

# 运行客户端
if __name__ == "__main__":
    asyncio.run(websocket_client())