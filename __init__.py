import sys
import subprocess
import importlib.util

# --- 自动环境部署区 ---
def is_installed(module_name):
    try:
        return importlib.util.find_spec(module_name) is not None
    except ImportError:
        return False

def install_package(package_name, module_name=None):
    # 如果没有指定导入名，默认和包名一致
    if module_name is None:
        module_name = package_name
        
    if not is_installed(module_name):
        print(f"HDD🤣 正在为你自动安装依赖: {package_name} ...")
        try:
            # 💡 关键修改：添加了 -i 清华源，解决 AutoDL 下载失败的问题
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                package_name, 
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ])
            print(f"HDD🤣 依赖 {package_name} 安装成功！")
        except subprocess.CalledProcessError as e:
            print(f"HDD🤣 依赖安装失败，请尝试手动并在终端运行: pip install {package_name}")
            raise e

# 1. 安装火山引擎 SDK (豆包)
# 包名: volcengine-python-sdk[ark]
# 导入名: volcenginesdkarkruntime
install_package("volcengine-python-sdk[ark]", "volcenginesdkarkruntime")

# 2. 安装其他工具
install_package("requests")
install_package("imageio")

# --- 节点加载区 ---
from .hdd_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]