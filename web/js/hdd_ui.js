import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "HDD.FrameLoader",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "HDD_FrameLoader") {
            // 当创建这个节点时触发
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // 找到 "交换顺序" 这个 widget
                const swapWidget = this.widgets.find(w => w.name === "交换顺序");
                
                if (swapWidget) {
                    // 修改它的回调，增加一些视觉反馈
                    const originalCallback = swapWidget.callback;
                    swapWidget.callback = (value) => {
                        if (originalCallback) originalCallback(value);
                        
                        // 简单的视觉提示
                        if (value) {
                            this.title = "HDD🤣 首尾帧加载器 (🔄 已交换)";
                            this.bgcolor = "#4A2A2A"; // 变红提示
                        } else {
                            this.title = "HDD🤣 首尾帧加载器 (正常)";
                            this.bgcolor = "#2A2A2A"; // 恢复默认
                        }
                    };
                }
                return r;
            };
        }
    },
});