import os
import time
import torch
import numpy as np
import requests
from PIL import Image
import io
import folder_paths
import random
import uuid
import urllib3
import json

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 辅助工具 ---

def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

# --- 核心：URL 生成器 ---
def get_image_url(pil_image, user_url):
    print(f"HDD🤣 DEBUG: 接收到的 AutoDL 地址 -> '{user_url}'")
    
    if not user_url or not isinstance(user_url, str) or len(user_url.strip()) < 10:
        raise ValueError("❌ 错误：[autodl_url] 未填写！请填入完整的公网地址 (例如 https://uXXXX.westb.seetacloud.com:8443)")

    clean_url = user_url.strip()
    
    if "http" not in clean_url:
         clean_url = "https://" + clean_url

    if clean_url.endswith("/"):
        clean_url = clean_url[:-1]

    filename = f"HDD_upload_{uuid.uuid4()}.png"
    temp_dir = folder_paths.get_temp_directory()
    image_path = os.path.join(temp_dir, filename)
    
    pil_image.save(image_path)
    print(f"HDD🤣: 图片已保存在本地: {filename}")
    
    final_url = f"{clean_url}/view?filename={filename}&type=temp"
    print(f"HDD🤣: 最终提交给 API 的链接: {final_url}")
    return final_url

# --- 通用生成逻辑 (V9: 参数格式大修) ---
def run_generation_task(api_key, model_id, content_list, batch_size, generate_audio, return_last_frame, seed):
    url = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model_id,
        "content": content_list
    }
    
    # 1.5 Pro 特性
    if generate_audio:
        payload["generate_audio"] = True
    
    if return_last_frame:
        payload["return_last_frame"] = True
        
    # 添加种子控制 (解决敏感内容误判)
    if seed and seed > 0:
        payload["seed"] = seed

    task_ids = []
    print(f"HDD🤣: 提交任务... (音效:{generate_audio}, 尾帧:{return_last_frame}, 种子:{seed})")
    
    for i in range(batch_size):
        try:
            # 这里的 verify=False 是为了适配 AutoDL 环境
            response = requests.post(url, headers=headers, json=payload, timeout=60, verify=False)
            response_json = response.json()
            
            if response.status_code == 200 and "id" in response_json:
                task_id = response_json["id"]
                print(f"HDD🤣: 任务 {i+1} 提交成功 -> ID: {task_id}")
                task_ids.append(task_id)
            else:
                print(f"HDD🤣: 任务 {i+1} 提交失败! API返回: {response_json}")
        except Exception as e:
            print(f"HDD🤣: 网络请求异常: {e}")
            
    return (",".join(task_ids),)

# --- 节点 1: 文生视频 ---
class HDD_Txt2Vid:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": "", "multiline": False}),
                "model_version": (["doubao-seedance-1-5-pro-251215", "doubao-seedance-1-0-pro-250528"], {"default": "doubao-seedance-1-5-pro-251215"}),
                "prompt": ("STRING", {"default": "写实风格，晴朗的蓝天...", "multiline": True}),
                # 改用 --rt
                "ratio": (["adaptive", "16:9", "4:3", "1:1", "9:16", "21:9"], {"default": "16:9"}),
                # 改为 4-12，增加 -1 智能时长
                "duration": ("INT", {"default": 5, "min": -1, "max": 12}),
                # 改用 --rs
                "resolution": (["720p", "480p"], {"default": "720p"}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "audio": ("BOOLEAN", {"default": True, "label_on": "🔊 开启音效", "label_off": "🔇 关闭音效"}),
                "return_last_frame": ("BOOLEAN", {"default": False, "label_on": "🖼️ 生成尾帧(用于续写)", "label_off": "❌ 不生成"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("视频任务ID列表",)
    FUNCTION = "generate"
    CATEGORY = "HDD🤣/Seedance"

    def generate(self, api_key, model_version, prompt, ratio, duration, resolution, batch_size, seed, audio, return_last_frame):
        if "1-0" in model_version:
            audio = False
            return_last_frame = False 
            
        # V9 修正：使用 --rs 和 --rt，并处理 duration=-1
        dur_str = ""
        if duration != -1:
            dur_str = f"--dur {duration}"
            
        final_prompt = f"{prompt} --rt {ratio} {dur_str} --rs {resolution} --fps 24"
        content = [{"type": "text", "text": final_prompt}]
        return run_generation_task(api_key, model_version, content, batch_size, audio, return_last_frame, seed)

# --- 节点 2: 图生视频 ---
class HDD_Img2Vid:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "autodl_url": ("STRING", {"default": "", "placeholder": "必填: AutoDL公网链接"}),
                "image": ("IMAGE",),
                "prompt": ("STRING", {"default": "画面描述...", "multiline": True}),
                "model_version": (["doubao-seedance-1-5-pro-251215", "doubao-seedance-1-0-pro-250528"], {"default": "doubao-seedance-1-5-pro-251215"}),
                "ratio": (["adaptive", "16:9", "1:1", "9:16", "21:9"], {"default": "adaptive"}),
                "duration": ("INT", {"default": 5, "min": -1, "max": 12}),
                "resolution": (["720p", "480p"], {"default": "720p"}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "audio": ("BOOLEAN", {"default": True, "label_on": "🔊 开启音效", "label_off": "🔇 关闭音效"}),
                "return_last_frame": ("BOOLEAN", {"default": False, "label_on": "🖼️ 生成尾帧(用于续写)", "label_off": "❌ 不生成"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("视频任务ID列表",)
    FUNCTION = "generate"
    CATEGORY = "HDD🤣/Seedance"

    def generate(self, api_key, autodl_url, image, prompt, model_version, ratio, duration, resolution, batch_size, seed, audio, return_last_frame):
        if "1-0" in model_version:
            audio = False
            return_last_frame = False

        pil_img = tensor2pil(image)
        img_url = get_image_url(pil_img, autodl_url)
        
        # V9 修正：使用 --rs 和 --rt
        dur_str = ""
        if duration != -1:
            dur_str = f"--dur {duration}"

        final_prompt = f"{prompt} --rt {ratio} {dur_str} --rs {resolution} --fps 24"
        content = [
            {"type": "text", "text": final_prompt},
            {"type": "image_url", "image_url": {"url": img_url}}
        ]
        
        return run_generation_task(api_key, model_version, content, batch_size, audio, return_last_frame, seed)

# --- 节点 3: 首尾帧生视频 ---
class HDD_FirstLastVid:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "autodl_url": ("STRING", {"default": ""}),
                "first_image": ("IMAGE",),
                "last_image": ("IMAGE",),
                "prompt": ("STRING", {"default": "平滑过渡...", "multiline": True}),
                "model_version": (["doubao-seedance-1-5-pro-251215"], {"default": "doubao-seedance-1-5-pro-251215"}),
                "resolution": (["720p", "480p"], {"default": "720p"}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "audio": ("BOOLEAN", {"default": True, "label_on": "🔊 开启音效", "label_off": "🔇 关闭音效"}),
                "return_last_frame": ("BOOLEAN", {"default": False, "label_on": "🖼️ 生成尾帧", "label_off": "❌ 不生成"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("视频任务ID列表",)
    FUNCTION = "generate"
    CATEGORY = "HDD🤣/Seedance"

    def generate(self, api_key, autodl_url, first_image, last_image, prompt, model_version, resolution, batch_size, seed, audio, return_last_frame):
        print("HDD🤣: 处理首尾帧...")
        first_url = get_image_url(tensor2pil(first_image), autodl_url)
        last_url = get_image_url(tensor2pil(last_image), autodl_url)

        # 追加分辨率
        prompt = f"{prompt} --rs {resolution} --fps 24"

        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": first_url}, "role": "first_frame"},
            {"type": "image_url", "image_url": {"url": last_url}, "role": "last_frame"}
        ]
        
        return run_generation_task(api_key, model_version, content, batch_size, audio, return_last_frame, seed)

# --- 节点 4: 视频保存 (调试增强版) ---
class HDD_VideoSave:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "task_ids": ("STRING", {"forceInput": True}),
                "filename_prefix": ("STRING", {"default": "HDD_Seedance"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("尾帧图像(可连图生视频)",)
    OUTPUT_NODE = True
    FUNCTION = "save_video"
    CATEGORY = "HDD🤣/Seedance"

    def save_video(self, api_key, task_ids, filename_prefix):
        url_base = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
        headers = {"Authorization": f"Bearer {api_key}"}

        if not task_ids:
            empty_img = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
            return {"ui": {"videos": []}}, empty_img

        ids_list = task_ids.split(",")
        preview_videos = []
        last_frame_tensor = None 
        
        print(f"HDD🤣: 开始下载流程，共 {len(ids_list)} 个任务...")
        
        for task_id in ids_list:
            if not task_id: continue
            
            print(f"HDD🤣: 正在轮询任务 {task_id}...")
            video_url = ""
            last_frame_url = ""
            
            while True:
                try:
                    resp = requests.get(f"{url_base}/{task_id}", headers=headers, timeout=30, verify=False)
                    result = resp.json()
                    
                    status = result.get("status")
                    if status == "succeeded":
                        content = result.get("content", {})
                        video_url = content.get("video_url")
                        
                        # 尝试获取尾帧，这里涵盖了常见的字段名
                        # API 文档可能会有变动，所以多做几个检查
                        if "image_url" in content:
                             last_frame_url = content["image_url"]
                        elif "last_frame_url" in content:
                             last_frame_url = content["last_frame_url"]
                        
                        # DEBUG: 打印成功后的 content，方便看字段
                        print(f"HDD🤣: 任务成功! Content数据: {content}")
                        break
                    elif status == "failed":
                        # 任务失败时，无法获取视频和尾帧
                        err_msg = result.get('error', '未知错误')
                        print(f"HDD🤣: 任务 {task_id} 失败: {err_msg}")
                        video_url = None
                        break
                    else:
                        time.sleep(3) 
                except Exception as e:
                    print(f"HDD🤣: 轮询网络错误: {e}")
                    time.sleep(3)
            
            # 1. 下载视频
            if video_url:
                try:
                    response = requests.get(video_url, verify=False)
                    filename = f"{filename_prefix}_{task_id[:8]}_{int(time.time())}.mp4"
                    filepath = os.path.join(self.output_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"HDD🤣: 视频已保存至: {filepath}")
                    preview_videos.append({"filename": filename, "subfolder": "", "type": self.type})
                except Exception as e:
                    print(f"下载视频出错: {e}")

            # 2. 下载尾帧 (只有任务成功且API返回了URL才行)
            if last_frame_url:
                print(f"HDD🤣: 正在下载尾帧: {last_frame_url}")
                try:
                    img_resp = requests.get(last_frame_url, verify=False)
                    img = Image.open(io.BytesIO(img_resp.content))
                    last_frame_tensor = pil2tensor(img)
                except Exception as e:
                     print(f"HDD🤣: 尾帧下载失败: {e}")

        # 如果没有下载到尾帧（通常因为任务失败），返回黑图并打印提示
        if last_frame_tensor is None:
             print("HDD🤣: 未获取到有效尾帧 (可能是任务失败)，输出黑图占位。")
             last_frame_tensor = torch.zeros((1, 512, 512, 3), dtype=torch.float32)

        return {"ui": {"videos": preview_videos}, "result": (last_frame_tensor,)}

# --- 节点 5: 首尾帧加载器 (UI) ---
class HDD_FrameLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "first_img": ("IMAGE",),
                "last_img": ("IMAGE",),
                "swap": ("BOOLEAN", {"default": False, "label_on": "已交换", "label_off": "正常"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("首帧", "尾帧")
    FUNCTION = "process"
    CATEGORY = "HDD🤣/工具"

    def process(self, first_img, last_img, swap):
        if swap:
            return (last_img, first_img)
        else:
            return (first_img, last_img)

NODE_CLASS_MAPPINGS = {
    "HDD_Txt2Vid": HDD_Txt2Vid,
    "HDD_Img2Vid": HDD_Img2Vid,
    "HDD_FirstLastVid": HDD_FirstLastVid,
    "HDD_VideoSave": HDD_VideoSave,
    "HDD_FrameLoader": HDD_FrameLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HDD_Txt2Vid": "HDD🤣 文生视频 (1.5 Pro)",
    "HDD_Img2Vid": "HDD🤣 图生视频 (1.5 Pro)",
    "HDD_FirstLastVid": "HDD🤣 首尾帧生视频 (1.5 Pro)",
    "HDD_VideoSave": "HDD🤣 视频保存&尾帧输出",
    "HDD_FrameLoader": "HDD🤣 首尾帧加载器 (UI)"
}