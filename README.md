# ComfyUI-HDD-Seedance-Nodes 🤣

这是一个专为 **Seedance 1.5 Pro** 视频生成模型设计的 ComfyUI 节点组。
支持 **AutoDL** 环境，解决了内网穿透和 SSL 验证问题，真正做到即插即用！

## ✨ 功能特点

* **1.5 Pro 原生支持**：完美支持最新版 Seedance 1.5 Pro API。
* **音效控制**：支持生成带音效的视频。
* **AutoDL 专用优化**：
    * 内建图床转发功能，解决 AutoDL 无法被 API 访问的问题。
    * 支持 `autodl_url` 直连，速度飞快。
* **无限续杯**：支持生成尾帧，并可直接作为下一段视频的输入，实现无限长视频制作。
* **画质可选**：支持 720p / 480p 切换。
* **智能时长**：支持 4-12秒 自定义或智能时长。

## 📦 安装方法

### 方法 1：通过 ComfyUI Manager (推荐)
1.  安装 [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)。
2.  点击 "Install via Git URL"。
3.  输入本仓库地址。

### 方法 2：手动安装
```bash
cd ComfyUI/custom_nodes
git clone [这里填你未来的Github仓库地址]
pip install -r requirements.txt