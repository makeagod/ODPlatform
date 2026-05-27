# frame_source 教学示例（D8 铺垫）

按课程 **「八面墙」** 顺序阅读/运行。这些是演示稿，**不进平台主流程**；终态 API 见 `odp_platform.frame_source`。

| 脚本 | 撞墙 / 主题 |
|------|-------------|
| `01_原生推理.py` | ① ultralytics `source=` 黑盒 |
| `02_opencv接管输入源.py` | ② 自己 `cap.read` + `model(frame)` |
| `03_opencv_叠加信息显示.py` | ③ 叠加 FPS / 帧号 |
| `04_opencv_输入 输出控制.py` | ④ 输入/输出分辨率 |
| `05_opencv捕获真实输入输出测试.py` | ⑤ 实测帧率 vs `cap.get(FPS)` |
| `06_摄像头后端自己选择.py` | ⑥ MSMF / DShow / V4L2 |
| `07_opencv摄像头测试.py` | ⑦ 单线程采集瓶颈 |
| `08_opencv摄像头测试_多线程.py` | ⑧ 采集/消费解耦 + FPS 平滑 |
| `ex03_输入输出控制.py` | 扩展：输入输出控制变体 |
| `ex04_实时高帧率_丢帧证明.py` | 扩展：高帧率丢帧 |
| `09_frame_source_统一接口.py` | **终态**：`odp_platform.frame_source` |

## 运行前

```powershell
pip install -e ./apps/platform
# 需摄像头示例：连接 USB 摄像头；无摄像头可只跑 09（图片）或改 source 为视频路径
```

模型路径：示例里多为课程权重名，请改为本机路径，例如：

```text
models/checkpoints/<your-best>.pt
models/pretrained/yolov8n.pt
```

## 讲义

[docs/platform/D8-frame_source-铺垫.md](../../../docs/platform/D8-frame_source-铺垫.md)
