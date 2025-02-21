from celery import Celery
from config import *
import time

app = Celery('tasks',
             broker=f'pyamqp://{broker_user}:{broker_pwd}@{broker_hostname}:{broker_port}/{broker_vhost}',
             backend=f'redis://{backend_hostname}:{backend_port}/{backend_db_num}'
            )

app.conf.update(
    task_routes = {
        'tasks.test': {'queue': 'test'},
        'tasks.process_face_swap': {'queue': 'face_swap'},
        'tasks.process_face_swap_thumbnail': {'queue': 'face_swap_thumbnail'},
        'tasks.process_image_upscale': {'queue': 'image_upscale'},
        'tasks.process_face_desensitization': {'queue': 'face_desensitization'},
        'tasks.process_face_desensitization_thumbnail': {'queue': 'face_desensitization_thumbnail'},
        'tasks.process_multiple_face_desensitization_fast': {'queue': 'multi_face_desensitization_fast'},
        'tasks.process_multiple_face_swap_fast': {'queue': 'multi_face_swap_fast'},
        'tasks.process_multiple_face_desensitization': {'queue': 'multi_face_desensitization'},
        'tasks.process_multiple_face_swap': {'queue': 'multi_face_swap'},
        'tasks.process_multiple_face_desensitization_auto': {'queue': 'multi_face_desensitization_auto'},
        'tasks.process_face_swap_auto': {'queue': 'face_swap_auto'},
        'tasks.process_multiple_face_desensitization_auto_xly': {'queue': 'multi_face_desensitization_auto_xly'},
    },
)

app.conf.timezone = 'Asia/Shanghai'
# @app.task
# def face_swap(origin_img_path, face_img_path):
#     client = ComfyUIClient()  
#     result = client.process_face_swap(origin_img_path, face_img_path)
#     status = result["status"]
#     if status != 0:
#         raise ValueError(result["message"])
#     return result

# @app.task
# def face_desensitization(origin_img_path):
#     client = ComfyUIClient()
#     result = client.process_face_desensitization(origin_img_path)
#     status = result["status"]
#     if status != 0:
#         raise ValueError(result["message"])
#     return result

# @app.task
# def face_desensitization_upscale(comfyui_task_id, work_id):
#     client = ComfyUIClient()
#     result = client.process_face_desensitization_upscale(comfyui_task_id, work_id)
#     status = result["status"]
#     if status != 0:
#         raise ValueError(result["message"])
#     return result

@app.task
def test():
    pass

@app.task
def process_face_desensitization_thumbnail(image_path, **kwargs):
    pass

@app.task
def process_face_desensitization(comfyui_task_id, work_id, **kwargs):
    pass

@app.task
def process_face_swap_thumbnail(image_path, face_image_path, **kwargs):
    pass

@app.task
def process_face_swap(comfyui_task_id, work_id, **kwargs):
    pass

@app.task
def process_image_upscale(comfyui_task_id, **kwargs):
    pass

# 任务6 多重人脸快速脱敏
@app.task
def process_multiple_face_desensitization_fast(image_path, **kwargs):
    pass

# 任务7 多人快速换脸
@app.task
def process_multiple_face_swap_fast(image_path, face_image_path, **kwargs):
    pass

# 任务8 多重人脸脱敏（细致）
@app.task
def process_multiple_face_desensitization(image_path, order, **kwargs):
    pass

# 任务9 多人换脸（细致）
@app.task
def process_multiple_face_swap(image_path, face_image_path, order, **kwargs):
    pass

@app.task
def process_multiple_face_desensitization_auto(image_path, **kwargs):
    # time.sleep(120)
    # msg = {'task_id': '86b22c5a-bddf-4b8b-a664-3145ef8757d9', 'task_type': 'multi_face_desensitization_auto', 'content': {'image_path': 'https://img.sw.gz.cn/photography-comfyui/user_1/20250113/094725_076b99615d8b48d9974beb25859b105f.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=KoIWIjPxYDm3YfmzJ2r6%2F20250113%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250113T014809Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=d06b4b56186f5ad98868484a97ccc0e38130e6ba85c0e97d56226dfd3e57e6bb'}}
    # return msg
    pass
    
@app.task
def process_face_swap_auto(image_path, face_image_path, **kwargs):
    pass

@app.task
def process_multiple_face_desensitization_auto_xly(image_path, **kwargs):
    # time.sleep(120)
    # msg = {'task_id': '86b22c5a-bddf-4b8b-a664-3145ef8757d9', 'task_type': 'multi_face_desensitization_auto', 'content': {'image_path': 'https://img.sw.gz.cn/photography-comfyui/user_1/20250113/094725_076b99615d8b48d9974beb25859b105f.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=KoIWIjPxYDm3YfmzJ2r6%2F20250113%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250113T014809Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=d06b4b56186f5ad98868484a97ccc0e38130e6ba85c0e97d56226dfd3e57e6bb'}}
    # return msg
    pass