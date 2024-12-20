import asyncio
import websockets
import json
from tasks import (
    process_face_swap, 
    process_face_desensitization, 
    process_face_desensitization_thumbnail, 
    process_face_swap_thumbnail, 
    process_image_upscale,
    process_multiple_face_desensitization_fast,
    process_multiple_face_swap_fast,
    process_multiple_face_desensitization,
    process_multiple_face_swap,
    process_multiple_face_desensitization_auto
)
from enum import Enum

class TaskType:
    FaceSwap = "face_swap"
    FaceDesensitization = "face_desensitization"
    FaceDesensitizationThumbnail = "face_desensitization_thumbnail"
    FaceSwapThumbnail = "face_swap_thumbnail"
    ImageUpscale = "image_upscale"
    MultiFaceDesensitizationFast = "multi_face_desensitization_fast"
    MultiFaceSwapFast = "multi_face_swap_fast"
    MultiFaceDesensitization = "multi_face_desensitization"
    MultiFaceSwap = "multi_face_swap"
    MultiFaceDesensitizationAuto = "multi_face_desensitization_auto"

tasks = {}
current_connection = None

def create_by_task_id(task_id, task_type, content):
    try:
        if task_type == TaskType.FaceSwap:
            print(content)
            task = process_face_swap.delay(**content)
            print("face swap")
        elif task_type == TaskType.FaceDesensitization:
            print(content)
            task = process_face_desensitization.delay(**content)
            print("face desensitization")
        elif task_type == TaskType.FaceDesensitizationThumbnail:
            print(content)
            task = process_face_desensitization_thumbnail.delay(**content)
            print("face desensitization thumbnail")
        elif task_type == TaskType.FaceSwapThumbnail:
            print(content)
            task = process_face_swap_thumbnail.delay(**content)
            print("face swap thumbnail")
        elif task_type == TaskType.ImageUpscale:
            print(content)
            task = process_image_upscale.delay(**content)
            print("image upscale")
        elif task_type == TaskType.MultiFaceDesensitizationFast:
            print(content)
            task = process_multiple_face_desensitization_fast.delay(**content)
            print("multi face desensitization fast")
        elif task_type == TaskType.MultiFaceSwapFast:
            print(content)
            task = process_multiple_face_swap_fast.delay(**content)
            print("multi face swap fast")
        elif task_type == TaskType.MultiFaceDesensitization:
            print(content)
            task = process_multiple_face_desensitization.delay(**content)
            print("multi face desensitization")
        elif task_type == TaskType.MultiFaceSwap:
            print(content)
            task = process_multiple_face_swap.delay(**content)
            print("multi face swap")
        elif task_type == TaskType.MultiFaceDesensitizationAuto:
            print(content)
            task = process_multiple_face_desensitization_auto.delay(**content)
            print("multi face desensitization")
        
        task_result = task.get()
        print(task_result)
        
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
    except Exception as e:
        error_message = json.dumps({'error': str(e)})
        await websocket.send(error_message)

# 定义 WebSocket 处理函数
async def handle_client(websocket):
    global current_connection

    # 允许当前连接
    current_connection = websocket
    print("Client connected.")

    try:
        while True:
            # 接收客户端发来的消息（假设是 JSON 格式的字符串）
            message = await websocket.recv()
            
            # 将接收到的 JSON 字符串转换为字典
            data = json.loads(message)
            print(data)
            
            task_id = data["task_id"]
            task_type = data["task_type"]
            content = data["content"]
            
            if task_type == TaskType.FaceSwap:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.FaceDesensitization:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.FaceDesensitizationThumbnail:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.FaceSwapThumbnail:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.ImageUpscale:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.MultiFaceDesensitizationFast:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.MultiFaceSwapFast:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.MultiFaceDesensitization:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.MultiFaceSwap:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == TaskType.MultiFaceDesensitizationAuto:
                asyncio.create_task(async_task_create(websocket, task_id, task_type, content))
            elif task_type == "query":
                asyncio.create_task(async_task_query(websocket, task_id, task_type, content))
            
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
