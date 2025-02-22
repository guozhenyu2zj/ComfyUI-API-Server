import asyncio
import websockets
import json
from tasks import (
    test,
    process_face_swap, 
    process_face_desensitization, 
    process_face_desensitization_thumbnail, 
    process_face_swap_thumbnail, 
    process_image_upscale,
    process_multiple_face_desensitization_fast,
    process_multiple_face_swap_fast,
    process_multiple_face_desensitization,
    process_multiple_face_swap,
    process_multiple_face_desensitization_auto,
    process_face_swap_auto,
    process_multiple_face_desensitization_auto_xly,
)
from enum import Enum
from collections import deque
import time
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi import APIRouter
import uvicorn

app = FastAPI()
task_queue = None

task_cost = {"face_swap_auto": 40,
             "image_upscale": 40,
             "single_face_desensitization_auto": 80,
             "multi_face_desensitization_auto": 180}
task_expired_time = 3600
task_funcs = {}
tasks = {}
# Config for logging
log_dir = "log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "server.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file), 
        logging.StreamHandler()          
    ]
)

class TaskType:
    Test = "test"
    FaceSwap = "face_swap"
    FaceDesensitization = "face_desensitization"
    FaceDesensitizationThumbnail = "face_desensitization_thumbnail"
    FaceSwapThumbnail = "face_swap_thumbnail"
    ImageUpscale = "image_upscale"
    MultiFaceDesensitizationFast = "multi_face_desensitization_fast"
    MultiFaceSwapFast = "multi_face_swap_fast"
    MultiFaceDesensitization = "multi_face_desensitization"
    MultiFaceSwap = "multi_face_swap"
    SingleFaceDesensitizationAuto = "single_face_desensitization_auto"
    MultiFaceDesensitizationAuto = "multi_face_desensitization_auto"
    FaceSwapAuto = "face_swap_auto"
    FaceDesensitizationAuto = "face_desensitization_auto"
    Query = "task_query"

class TaskStatus:
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"


class PhotoTask:
    def __init__(self, task_id: str, task_type: TaskType, task_para: dict):
        self.task_id = task_id
        self.task_type = task_type
        self.task_para = task_para
        self.cost_time = task_cost[task_type]
        self.task_status = TaskStatus.WAITING
        self.waiting_time = -1
        self.finished_time = -1
        self.result = {}

class TaskQueue:
    def __init__(self, websocket: WebSocket):
        self.task_queue_type = ["face_swap_auto", "image_upscale", "face_desensitization_auto"]
        self.main_queue = asyncio.Queue()
        self.sub_queue_dict = {}
        for task_queue_type in self.task_queue_type:
            task_queue = asyncio.Queue()
            task_list = deque()
            task_start_time = -1
            self.sub_queue_dict[task_queue_type] = (task_queue, task_list, task_start_time)
        self.websocket = websocket
        self.task_dict = {}
        self.waiting_time = {}
        
    def run(self):
        asyncio.create_task(self.task_dispatcher())
        # asyncio.create_task(self.handle_face_swap_auto())
        # asyncio.create_task(self.handle_multi_face_desensitization_auto())
        # asyncio.create_task(self.handle_image_upscale())
        for task_queue_type in self.task_queue_type:
            asyncio.create_task(self.handle_task_queue(task_queue_type))
        # asyncio.create_task(self.handle_task_queue_xly("face_desensitization_auto"))
        asyncio.create_task(self.update_waiting_time())
        # asyncio.create_task(self.update_task_dict())
    
    def test_task(self):
        result = test.delay()
        msg = result.get(timeout=10)
        asyncio.run(self.websocket.send_text(msg))

    def process_task(self, task_id):
        print("3090")
        try:
            task = self.task_dict[task_id]
            if task.task_type == TaskType.FaceSwapAuto:
                result = process_face_swap_auto.delay(**task.task_para)
            elif task.task_type == TaskType.MultiFaceDesensitizationAuto:
                result = process_multiple_face_desensitization_auto.delay(**task.task_para)
            elif task.task_type == TaskType.SingleFaceDesensitizationAuto:
                result = process_multiple_face_desensitization_auto.delay(**task.task_para)
            elif task.task_type == TaskType.ImageUpscale:
                result = process_image_upscale.delay(**task.task_para)
            else:
                raise ValueError("Unknown task type")
            
            task_result = result.get()
            print(task_result)
            processed_result = {"url": task_result["url"],
                                "file_path": task_result["file_path"],
                                "comfyui_task_id": task_result["task_id"]}
            return TaskStatus.SUCCESSFUL, processed_result

        except Exception as e:
            return TaskStatus.FAILED, f'{e}'
        
    def process_task_xly(self, task_id):
        print("xly")
        try:
            task = self.task_dict[task_id]
            if task.task_type == TaskType.FaceSwapAuto:
                result = process_face_swap_auto.delay(**task.task_para)
            elif task.task_type == TaskType.MultiFaceDesensitizationAuto:
                result = process_multiple_face_desensitization_auto_xly.delay(**task.task_para)
            elif task.task_type == TaskType.SingleFaceDesensitizationAuto:
                result = process_multiple_face_desensitization_auto_xly.delay(**task.task_para)
            elif task.task_type == TaskType.ImageUpscale:
                result = process_image_upscale.delay(**task.task_para)
            else:
                raise ValueError("Unknown task type")
            
            task_result = result.get()
            print(task_result)
            processed_result = {"url": task_result["url"],
                                "file_path": task_result["file_path"],
                                "comfyui_task_id": task_result["task_id"]}
            return TaskStatus.SUCCESSFUL, processed_result

        except Exception as e:
            return TaskStatus.FAILED, f'{e}'
    
    async def update_waiting_time(self):
        while True:
            try:
                for task_queue_type in self.task_queue_type:
                    await self.update_waiting_time_by_type(task_queue_type)
                await asyncio.sleep(5)
            except Exception as e:
                print(f'{e}')
    
    async def update_waiting_time_by_type(self, task_queue_type):
        _, sub_list, start_time = self.sub_queue_dict[task_queue_type]
        waiting_time = 0 - (time.time() - start_time)
        for task_id in sub_list:
            task = self.task_dict[task_id]
            task_cost_time = task_cost[task.task_type]
            waiting_time += task_cost_time
            waiting_time = waiting_time if waiting_time > 0 else 0
            task.waiting_time = waiting_time
            print(f'task:{task.task_id} left {task.waiting_time} waiting time.')
    
    async def update_task_dict(self):
        task_dict = self.task_dict
        while True:
            try:
                for task_id in task_dict:
                    task = task_dict[task_id]
                    task_finished_time = task.finished_time
                    if task_finished_time > 0:
                        if time.time() - task_finished_time > task_expired_time:
                            task[task_id] = None
                await asyncio.sleep(5)
            except Exception as e:
                print(f'{e}')

    async def handle_task_queue(self, task_queue_type):
        task_queue, task_list, _ = self.sub_queue_dict[task_queue_type]
        while True:
            try:
                task_id = await task_queue.get()
                task_list.popleft()
                task = self.task_dict[task_id]
                task.waiting_time = 0
                if task:
                    task.task_status = TaskStatus.RUNNING
                    self.sub_queue_dict[task_queue_type] = (task_queue, task_list, time.time())
                    # task start
                    start_msg ={"task_id": task.task_id,
                                "result": {"processed": task.task_status,
                                            "left_waiting_time": task.waiting_time,
                                            "cost_time": task.cost_time,
                                            "task_type": task.task_type,
                                            "processed_result": task.result}}
                    await self.websocket.send_text(json.dumps(start_msg))
                    
                    status, result = await asyncio.to_thread(self.process_task, task_id)    
                    
                    if status == TaskStatus.SUCCESSFUL:
                        task.task_status = TaskStatus.SUCCESSFUL
                        task.result = result
                        task.waiting_time = 0
                        task.finished_time = time.time()
                    elif status == TaskStatus.FAILED:
                        task.task_status = TaskStatus.FAILED
                        task.result = f'{e}'
                        task.waiting_time = 0
                        task.finished_time = time.time()

                    msg = {"task_id": task.task_id,
                                "result": {"processed": task.task_status,
                                            "left_waiting_time": task.waiting_time,
                                            "cost_time": task.cost_time,
                                            "task_type": task.task_type,
                                            "processed_result": task.result}}
                    await self.websocket.send_text(json.dumps(msg))
            except Exception as e:
                print(f'{e}')
                
    async def handle_task_queue_xly(self, task_queue_type):
        task_queue, task_list, _ = self.sub_queue_dict[task_queue_type]
        while True:
            try:
                task_id = await task_queue.get()
                task_list.popleft()
                task = self.task_dict[task_id]
                task.waiting_time = 0
                if task:
                    task.task_status = TaskStatus.RUNNING
                    self.sub_queue_dict[task_queue_type] = (task_queue, task_list, time.time())
                    # task start
                    start_msg ={"task_id": task.task_id,
                                "result": {"processed": task.task_status,
                                            "left_waiting_time": task.waiting_time,
                                            "cost_time": task.cost_time,
                                            "task_type": task.task_type,
                                            "processed_result": task.result}}
                    await self.websocket.send_text(json.dumps(start_msg))
                    
                    status, result = await asyncio.to_thread(self.process_task_xly, task_id)
                    
                    if status == TaskStatus.SUCCESSFUL:
                        task.task_status = TaskStatus.SUCCESSFUL
                        task.result = result
                        task.waiting_time = 0
                        task.finished_time = time.time()
                    elif status == TaskStatus.FAILED:
                        task.task_status = TaskStatus.FAILED
                        task.result = f'{e}'
                        task.waiting_time = 0
                        task.finished_time = time.time()

                    msg = {"task_id": task.task_id,
                                "result": {"processed": task.task_status,
                                            "left_waiting_time": task.waiting_time,
                                            "cost_time": task.cost_time,
                                            "task_type": task.task_type,
                                            "processed_result": task.result}}
                    await self.websocket.send_text(json.dumps(msg))
            except Exception as e:
                print(f'{e}')

    async def task_dispatcher(self):
        while True:
            try:
                task_id = await self.main_queue.get()
                task = self.task_dict[task_id]
                if task:
                    if task.task_type == TaskType.FaceSwapAuto:
                        face_swap_auto_queue, face_swap_auto_list, _ = self.sub_queue_dict[TaskType.FaceSwapAuto]
                        await face_swap_auto_queue.put(task_id)
                        face_swap_auto_list.append(task_id)
                    elif task.task_type == TaskType.MultiFaceDesensitizationAuto:
                        print(TaskType.MultiFaceDesensitizationAuto)
                        multi_face_desensitization_auto_queue, multi_face_desensitization_auto_list, _ = self.sub_queue_dict["face_desensitization_auto"]
                        await multi_face_desensitization_auto_queue.put(task_id)
                        multi_face_desensitization_auto_list.append(task_id)
                    elif task.task_type == TaskType.SingleFaceDesensitizationAuto:
                        print(TaskType.SingleFaceDesensitizationAuto)
                        single_face_desensitization_auto_queue, single_face_desensitization_auto_list, _ = self.sub_queue_dict["face_desensitization_auto"]
                        await single_face_desensitization_auto_queue.put(task_id)
                        single_face_desensitization_auto_list.append(task_id)
                    elif task.task_type == TaskType.ImageUpscale:
                        image_upscale_queue, image_upscale_list, _ = self.sub_queue_dict[TaskType.ImageUpscale]
                        await image_upscale_queue.put(task_id)
                        image_upscale_list.append(task_id)
                    self.main_queue.task_done()
            except Exception as e:
                print(f'{e}')

    
    async def add_task(self, task: PhotoTask):
        await self.main_queue.put(task.task_id)
        self.task_dict[task.task_id] = task
        # task commit
        if (task.task_type == TaskType.SingleFaceDesensitizationAuto) or (task.task_type == TaskType.MultiFaceDesensitizationAuto):
            task_queue_type = TaskType.FaceDesensitizationAuto
        else:
            task_queue_type = task.task_type
        await self.update_waiting_time_by_type(task_queue_type)
        commit_msg = {"task_id": task.task_id,
                        "result": {"processed": task.task_status,
                                    "left_waiting_time": task.waiting_time,
                                    "cost_time": task.cost_time,
                                    "task_type": task.task_type,
                                    "processed_result": task.result}}
        await self.websocket.send_text(json.dumps(commit_msg))

    async def query_task(self, task_id):
        try:
            if task_id in self.task_dict:
                task = self.task_dict[task_id]
                msg = {"task_id": task.task_id,
                                "result": {"processed": task.task_status,
                                            "left_waiting_time": task.waiting_time,
                                            "cost_time": task.cost_time,
                                            "task_type": task.task_type,
                                            "processed_result": task.result}}
                print(msg)
                return msg
            else:
                msg = {"task_id": task_id, "error": "Invalid task id."}
                print(msg)
                return msg
        except Exception as e:
                print(f'{e}')

    async def cancel_task(self, task_id):
        try:
            pass
        except Exception as e:
                print(f'{e}')

    async def test(self):
        await asyncio.to_thread(self.test_task)


# async def handle_message(message, task_queue):
#     try:
#         # 假设消息是 JSON 格式
#         data = json.loads(message)
#         print(data)
#         task_id = data.get("task_id")
#         task_type = data.get("task_type")
#         content = data.get("content")
        
#         if task_type == TaskType.Query:
#             await task_queue.query_task(task_id=task_id)
#         else:  
#             task = PhotoTask(task_id=task_id, task_type=task_type, task_para=content)
#             await task_queue.add_task(task)
#         # 在此处可以处理任务并返回相应消息
#         # response = {
#         #     "status": "success",
#         #     "message": "Task processed successfully"
#         # }
#         # await websocket.send(json.dumps(response))
    
#     except json.JSONDecodeError as e:
#         logging.error(f"JSON Decode Error: {e}")
#         error_response = {"error": "Invalid JSON format"}
#         # await websocket.send(json.dumps(error_response))
    
#     except KeyError as e:
#         logging.error(f"Missing expected key: {e}")
#         error_response = {"error": f"Missing key: {e}"}
#         # await websocket.send(json.dumps(error_response))
    
#     except Exception as e:
#         logging.error(f"Unexpected error: {e}")
#         error_response = {"error": "Unexpected error occurred"}
#         # await websocket.send(json.dumps(error_response))

@app.get("/query")
async def read_root(task_id):
    global task_queue
    msg = await task_queue.query_task(task_id)
    return JSONResponse(content=msg)

@app.get("/cancel")
async def read_root(task_id):
    global task_queue
    msg = await task_queue.cancel_task(task_id)
    return JSONResponse(content=msg)

# 处理每个客户端连接
@app.websocket("/")
async def handle_client(websocket: WebSocket):
    await websocket.accept()
    global task_queue
    task_queue = TaskQueue(websocket=websocket)
    task_queue.run()
    
    while True:
        try:
            message = await websocket.receive_text()
            data = json.loads(message)
            print(data)
            task_id = data.get("task_id")
            task_type = data.get("task_type")
            content = data.get("content")
            
            if task_type == TaskType.Query:
                await task_queue.query_task(task_id=task_id)
            elif task_type == TaskType.Test:
                await task_queue.test()
            else:  
                task = PhotoTask(task_id=task_id, task_type=task_type, task_para=content)
                await task_queue.add_task(task)

        except websockets.ConnectionClosedError as e:
            logging.error(f"Connection closed with error: {e}")
            break  # 连接异常关闭，跳出重连逻辑
        
        except websockets.ConnectionClosedOK:
            logging.info("Connection closed cleanly by client.")
            break  # 客户端正常关闭连接

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=38765)
