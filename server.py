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
    process_multiple_face_desensitization_auto,
    process_face_swap_auto
)
from enum import Enum
from collections import deque
import time

task_cost = {"face_swap_auto": 40, "image_upscale": 40, "multi_face_desensitization_auto": 120}
task_funcs = {}
tasks = {}
current_connection = None
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
    FaceSwapAuto = "face_swap_auto"

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
        self.result = {}

class TaskQueue:
    def __init__(self, websocket):
        self.main_queue = asyncio.Queue()
        self.sub_queue_list = []
        self.face_swap_auto_queue = asyncio.Queue()
        self.face_swap_auto_list = deque()
        self.face_swap_auto_start_time = -1
        self.sub_queue_list.append(self.face_swap_auto_list)
        self.multi_face_desensitization_auto_queue = asyncio.Queue()
        self.multi_face_desensitization_auto_list = deque()
        self.multi_face_desensitization_auto_start_time = -1
        self.sub_queue_list.append(self.multi_face_desensitization_auto_list)
        self.image_upscale_queue = asyncio.Queue()
        self.image_upscale_list = deque()
        self.image_upscale_start_time = -1
        self.sub_queue_list.append(self.image_upscale_list)
        self.cost_time = [35, 45, 45]
        self.start_time = [time.time(), time.time(), time.time()]
        self.websocket = websocket
        self.task_dict = {}
        
    def run(self):
        asyncio.create_task(self.task_dispatcher())
        asyncio.create_task(self.handle_face_swap_auto())
        asyncio.create_task(self.handle_multi_face_desensitization_auto())
        asyncio.create_task(self.handle_image_upscale())
        asyncio.create_task(self.update_waiting_time())

    async def process_task(self, task):
        try:
            if task.task_type == TaskType.FaceSwapAuto:
                task.status = TaskStatus.RUNNING
                result = process_face_swap_auto.delay(**task.task_para)
                self.face_swap_auto_start_time = time.time()
                self.start_time[0] = self.face_swap_auto_start_time
            elif task.task_type == TaskType.MultiFaceDesensitizationAuto:
                task.status = TaskStatus.RUNNING
                result = process_multiple_face_desensitization_auto.delay(**task.task_para)
                self.multi_face_desensitization_auto_start_time = time.time()
                self.start_time[1] = self.multi_face_desensitization_auto_start_time
            elif task.task_type == TaskType.ImageUpscale:
                task.status = TaskStatus.RUNNING
                result = process_image_upscale.delay(**task.task_para)
                self.image_upscale_start_time = time.time()
                self.start_time[2] = self.image_upscale_start_time
            else:
                raise ValueError("Unknown task type")
            
            task_result = result.get()
            print(task_result)
            processed_result = {"url": task_result["url"],
                                "file_path": task_result["file_path"],
                                "comfyui_task_id": task_result["task_id"]}
            
            task.task_status = TaskStatus.SUCCESSFUL
            task.result = processed_result
            
            msg = {"task_id": task.task_id,
                "result": {"processed": task.task_status,
                            "task_type": task.task_type,
                            "processed_result": task.result}}

        except Exception as e:
            task.task_status = TaskStatus.FAILED
            task.result = f'{e}'

            msg = {"task_id": task.task_id,
               "result": {"processed": task.task_status,
                          "task_type": task.task_type,
                          "processed_result": task.result}}
        return msg
    
    async def update_waiting_time(self):
        length = len(self.sub_queue_list)
        while True:
            for i in range(length):
                sub_queue = self.sub_queue_list[i]
                cost = self.cost_time[i]
                rest_time = cost - (time.time() - self.start_time[i])
                waiting_time = rest_time if rest_time > 0 else 0
                for task in sub_queue:
                    task.waiting_time = waiting_time
                    waiting_time += cost
            await asyncio.sleep(5)

    async def handle_face_swap_auto(self):
        while True:
            task = await self.face_swap_auto_queue.get()
            self.face_swap_auto_list.popleft()
            task.waiting_time = 0
            if task:
                result = await self.process_task(task)
                print(result)
                self.face_swap_auto_queue.task_done()
                await self.websocket.send(json.dumps(result))
    
    async def handle_multi_face_desensitization_auto(self):
        while True:
            task = await self.multi_face_desensitization_auto_queue.get()
            self.multi_face_desensitization_auto_list.popleft()
            task.waiting_time = 0
            if task:
                result = await self.process_task(task)
                print(result)
                self.multi_face_desensitization_auto_queue.task_done()
                await self.websocket.send(json.dumps(result))
    
    async def handle_image_upscale(self):
        while True:
            task = await self.image_upscale_queue.get()
            self.image_upscale_list.popleft()
            task.waiting_time = 0
            if task:
                result = await self.process_task(task)
                print(result)
                self.image_upscale_queue.task_done()
                await self.websocket.send(json.dumps(result))

    async def task_dispatcher(self):
        while True:
            task = await self.main_queue.get()
            if task:
                if task.task_type == TaskType.FaceSwapAuto:
                    await self.face_swap_auto_queue.put(task)
                    self.face_swap_auto_list.append(task)
                elif task.task_type == TaskType.MultiFaceDesensitizationAuto:
                    print(TaskType.MultiFaceDesensitizationAuto)
                    await self.multi_face_desensitization_auto_queue.put(task)
                    self.multi_face_desensitization_auto_list.append(task)
                elif task.task_type == TaskType.ImageUpscale:
                    await self.image_upscale_queue.put(task)
                    self.image_upscale_list.append(task)
                self.main_queue.task_done()

    
    async def add_task(self, task: PhotoTask):
        await self.main_queue.put(task)
        self.task_dict[task.task_id] = task

    async def query_task(self, task_id):
        task_dict = self.task_dict
        if task_id in task_dict:
            task = task_dict[task_id]
            task_type = task.task_type
            task_status = task.task_status
            task_waiting_time = task.waiting_time
            task_result = task.result
            msg = {"task_id": task_id,
                   "result":{"task_type": task_type,
                             "task_status": task_status,
                             "task_waiting_time": task_waiting_time,
                             "task_result": task_result}}
            await self.websocket.send(json.dumps(msg))

# 定义 WebSocket 处理函数
async def handle_client(websocket):
    global current_connection

    # 允许当前连接
    current_connection = websocket
    print("Client connected.")
    
    task_queue = TaskQueue(websocket=websocket)
    task_queue.run()
    print("ok")
    # try:
    while True:
        # 接收客户端发来的消息（假设是 JSON 格式的字符串）
        message = await websocket.recv()
        
        # 将接收到的 JSON 字符串转换为字典
        data = json.loads(message)
        print(data)
        
        task_id = data["task_id"]
        task_type = data["task_type"]
        content = data["content"]
        
        task = PhotoTask(task_id=task_id, task_type=task_type, task_para=content)
        await task_queue.add_task(task)
            
    # except Exception as e:
    #     # 处理异常并发送错误消息
    #     error_message = json.dumps({'error': str(e)})
    #     await websocket.send(error_message)
    # finally:
    #     # 断开连接后清理当前连接
    #     current_connection = None

# 启动 WebSocket 服务器
async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 38765):
        print("WebSocket服务器已启动，等待客户端连接...")
        await asyncio.Future()  # 永远不会结束的任务，保持服务器运行

if __name__ == "__main__":
    asyncio.run(main())
