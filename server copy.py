import asyncio
import websockets
import json
from tasks import face_swap, face_desensitization, face_desensitization_upscale
import time
from enum import Enum


class TaskType:
    FaceSwap = "face_swap"
    FaceDesensitization = "face_desensitization"
    FaceDesensitizationUpscale = "face_desensitization_upscale"

tasks = {}
current_connection = None

def create_by_task_id(task_id, task_type, content):
    try:
        if task_type == TaskType.FaceSwap:
            print(content)
            task = face_swap.delay(**content)
            print("face swap")
        elif task_type == TaskType.FaceDesensitization:
            print(content)
            task = face_desensitization.delay(**content)
            print("face desensitization")
        elif task_type == TaskType.FaceDesensitizationUpscale:
            print(content)
            task = face_desensitization_upscale.delay(**content)
            print("face desensitization upscale")
        task_result = task.get()
        print(task_result)
        # result_status = task_result["status"]
        # if result_status == 0:
        #     msg = {"task_id": task_id,
        #                 "result": {"processed": "completed",
        #                             "task_type": task_type,
        #                             "processed_result": task_result["url"]}}
        # else:
        #     msg = {"task_id": task_id,
        #                 "result": {"processed": "failed",
        #                             "task_type": task_type,
        #                             "processed_result": task_result["message"]}}
        msg = {"task_id": task_id,
                "result": {"processed": "completed",
                "task_type": task_type,
                "processed_result": {"url": task_result["url"],
                                     "file_path": task_result["file_path"],
                                     "comfyui_task_id": task_result["task_id"]}}}
    except Exception as e:
        msg = {"task_id": task_id,
                "result": {"processed": "failed",
                "task_type": task_type,
                "processed_result": f'{e}'}}
    
    return msg

def query_by_task_id(task_id, task_type, content):
    if task_id in tasks:
        task = tasks[task_id]
        task_type = task["type"]
        task_result = task["result"]
        if task_result.ready():
            msg = {"task_id": task_id,
                   "result": {"processed": "completed",
                              "task_type": task_type,
                              "processed_result": {"url": task_result["url"],
                                                   "file_path": task_result["file_path"],
                                                   "comfyui_task_id": task_result["task_id"]}}}
        else:
            msg = {"task_id": task_id,
                   "result": {"processed": "processing",
                              "task_type": task_type,
                              "processed_result": ""}}
    else:
        msg = {"task_id": task_id,
                    "result": {"processed": "failed",
                                "task_type": task_type,
                                "processed_result": "Query failed."}}
    return msg
    

async def async_task_create(websocket, task_id, task_type, content):
    print("Starting async task")
    create_result = await asyncio.to_thread(create_by_task_id, 
                                            task_id=task_id, 
                                            task_type=task_type,
                                            content=content)
    print(create_result)
    await websocket.send(json.dumps(create_result))
    
async def async_task_query(websocket, task_id, task_type, content):
    print("Querying task")
    
    try:
        query_result = await asyncio.to_thread(query_by_task_id,
                                               task_id=task_id,
                                               task_type=task_type,
                                               content=content)
        await websocket.send(json.dumps(query_result))
    except:
        pass
# 定义处理 JSON 数据的函数
def process_data(data):
    pass

# 定义 WebSocket 处理函数
async def handle_client(websocket):
    global current_connection

    # if current_connection is not None:
    #     # 如果已经有一个客户端连接，拒绝新的连接
    #     await websocket.send("Server is already occupied with another client.")
    #     await websocket.close()
    #     return

    # 允许当前连接
    current_connection = websocket
    print("Client connected.")

    try:
        while True:
            # # 接收客户端发来的消息（假设是 JSON 格式的字符串）
            message = await websocket.recv()
            
            # 将接收到的 JSON 字符串转换为字典
            data = json.loads(message)
            print(data)
            
            task_id = data["task_id"]
            task_type = data["task_type"]
            content = data["content"]
            
            print(task_type==TaskType.FaceSwap)
            if task_type == TaskType.FaceSwap:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.FaceDesensitization:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.FaceDesensitizationUpscale:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == "query":
                asyncio.create_task(async_task_query(websocket, task_id, task_type, content))
            
            # # 调用处理函数处理数据
            # result = process_data(data)
            
            # # 将结果转换回 JSON 字符串
            # response = json.dumps(result)
            
            # # 将结果发送回客户端
            # await websocket.send(response)
            pass
        
    except Exception as e:
        # 处理异常并发送错误消息
        error_message = json.dumps({'error': str(e)})
        await websocket.send(error_message)
    finally:
        # 断开连接后清理当前连接
        current_connection = None

# 启动 WebSocket 服务器
async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 38765):
        print("WebSocket服务器已启动，等待客户端连接...")
        await asyncio.Future()  # 永远不会结束的任务，保持服务器运行

if __name__ == "__main__":
    asyncio.run(main())
