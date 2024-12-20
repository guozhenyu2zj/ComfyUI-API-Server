# from tasks import add
# result = add.delay(4, 4)
# print(result.get(timeout=15))

import asyncio
import websockets
import time
import json

# 异步函数：向 WebSocket 服务器发送消息
async def send_message():
    uri = "ws://localhost:38765"  # 替换成你的 WebSocket 服务器地址
    async with websockets.connect(uri) as websocket:
        print("WebSocket连接已打开")
        image_path = 'https://ts1.cn.mm.bing.net/th/id/R-C.eed97557f689df2382b6a9fc85ed172e?rik=d%2fBN9fsXJ2nz2w&riu=http%3a%2f%2fup.bizhizu.com%2fpic%2fd1%2fb7%2fc1%2fd1b7c1c9d4362b4ed5a433e69a19b383.jpg&ehk=OafBZEPbO07cQidzqmNBh0FzR5lM78gdhBOg7%2bjNdis%3d&risl=&pid=ImgRaw&r=0'
    
        face_image_path = 'https://k.sinaimg.cn/www/dy/slidenews/24_img/2016_19/74485_1363976_499220.jpg/w640slw.jpg'


        while True:
            message = {"task_id": 1,
                       "task_type": "face_swap",
                       "content": {"origin_img_path": image_path,
                                   "face_img_path": face_image_path}}
            await websocket.send(json.dumps(message))
            result = await websocket.recv()
            print(result)
            # message = {"task_id": 1,
            #            "task_type": "face_desensitization",
            #            "content": {"origin_img_path": image_path}}
            # await websocket.send(json.dumps(message))
            result = await websocket.recv()
            print(result)

            # 等待1秒再发送下一条消息
            await asyncio.sleep(1)
            break

# 运行 WebSocket 客户端
async def main():
    await send_message()

# 运行异步事件循环
if __name__ == "__main__":
    asyncio.run(main())
