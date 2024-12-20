import asyncio
import websockets
import json
from tasks import add


tasks = {}

def create_by_task_id(task_id, task_type, content):
    try:
        task = {}
        task["type"] = task_id
        # task["result"] = add.delay(1, 1)
        msg = {"task_id": task_id,
               "info": "Create task successfully."}
    except:
        msg = {"task_id": task_id,
               "error": "Create task failed."}
    
    return msg

def query_by_task_id(task_id, task_type, content):
    if task_id in tasks:
        task = tasks[task_id]
        task_type = task["type"]
        task_result = task["result"]
        if task_result.ready():
            msg = {"task_id": task_id,
                   "result": {"processed": True,
                              "task_type": task_type,
                              "processed_result": task_result}}
        else:
            msg = {"task_id": task_id,
                   "result":{}}
    else:
        msg = {"task_id": task_id,
               "error": "Invalid task id."}
    return msg
    

async def async_task_create(websocket, task_id, task_type, content):
    print("Starting async task")
    try:
        create_result = await asyncio.to_thread(create_by_task_id, 
                                                task_id=task_id, 
                                                task_type=task_type,
                                                content=content)
        await websocket.send(json.dumps(create_result))
    except:
        pass
    
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
    try:
        while True:
            # # 接收客户端发来的消息（假设是 JSON 格式的字符串）
            message = await websocket.recv()
            print(message)
            
            # 将接收到的 JSON 字符串转换为字典
            data = json.loads(message)
            
            task_id = data["task_id"]
            task_type = data["task_type"]
            content = data["content"]
            
            if task_type == "create_1":
                asyncio.create_task(async_task_create(websocket, task_type, task_id, content))
            elif task_type == "query":
                asyncio.create_task(async_task_query(websocket, task_type, task_id, content))
            
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

# 启动 WebSocket 服务器
async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        print("WebSocket服务器已启动，等待客户端连接...")
        await asyncio.Future()  # 永远不会结束的任务，保持服务器运行

if __name__ == "__main__":
    asyncio.run(main())
