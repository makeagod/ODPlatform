# 为什么需要 frame_source:从官方源码的"接不住",到八面墙的"自己撞"

> **本文定位**:D8 inference 子系统的**前置铺垫**——把"为什么必须自己造一个 `frame_source`"彻底讲透。
>
> 这件事有**两个角度**,本文把它们合流:
> - **刨根(分析)**:扒开 ultralytics 的 `LoadStreams` 源码,看清官方的 `source=` 为什么**源码层面就没留配置接口**;再用官方 GitHub Issues 佐证——这不是我们用得不对,是已知且未被采纳的局限。结论:官方这条路堵死了,只能自己接管输入源。
> - **实撞(经验)**:自己接管输入源之后,从一行 `model.predict` 起步,沿 8 个演示脚本一路撞墙,每撞一面墙就长出一个新脚本。八面墙撞完,三个信号同时亮起,`frame_source` 的轮廓才算被逼出来。
>
> 两个角度指向同一个答案:**官方接不住(必要性)+ 自己写会撞一连串墙(复杂度)= 必须把"出帧"剥成一个独立模块**。
>
> **本文到"引出 frame_source"为止结束**。子模块的真正代码,另起炉灶写。
>
> **怎么读**:那 8 个脚本都是 `/tmp/` 下的演示稿,**演完就丢、不进 git 主线**。但强烈建议有摄像头的同学真的敲出来跑——尤其 `06`/`07`/`08` 那几面墙(后端 / 线程 / 解耦),在屏幕上是肉眼可见的卡顿,光读文字感受不到那个痛。

---

## 起点:ultralytics 一行就能跑

模型训练好了(D6)、验证过了(D7),现在的问题是:**推理怎么跑起来?**

听起来比训练还简单,ultralytics 一行就行:

```python
from ultralytics import YOLO
model = YOLO("best.pt")
model.predict(source="0", show=True)   # 摄像头实时推理,一行
```

这一行**真的能跑**:开摄像头、画框、弹窗口。绝大多数 yolo 教程到这里就结束了。

但 ODPlatform 是"端到端实验工程 + 未来要做 web 实时推理服务"的场景。这套朴素方案在这里会撞一连串墙——而且比 D6 训练撞得多,因为**推理的输入源复杂度本来就比训练高**:

- 训练的输入是 `data.yaml` 指向的**带标注的静态数据集**,ultralytics 已经把数据加载抽象得很完善了。
- 推理的输入是**动态的原始流**:一张图、一个目录、一段 mp4、一个 USB 摄像头、一路 RTSP。每一种的打开方式、参数协商、帧率特性、资源释放都不一样。

ultralytics 的 `model.predict(source=...)` 想用一个 `source` 参数吃下所有这些——结果是:**能跑,但是个黑盒**。

但在自己动手接管之前,得先回答一个问题:这个黑盒,**为什么不能直接配置一下就用**?把摄像头配成 720p@90fps 不就行了吗?答案藏在 ultralytics 的源码里——而且这不是我们用得不对,是它**源码层面就没留接口**。

---

# 刨根:官方的 `source=` 为什么接不住

## 我们的真实痛点

这套朴素方案放进真实的工地安全帽检测项目,立刻暴露一串硬伤:

| 痛点 | 具体表现 |
|---|---|
| **摄像头参数不可控** | 720p 90fps 高帧率摄像头无法配置,只能跑系统默认分辨率 |
| **4K 输入不支持** | 高分辨率摄像头被压在低分辨率上 |
| **后端无法选择** | 无法指定 MSMF / DShow / V4L2 后端 |
| **深度耦合** | 输入源处理与推理逻辑绑死,无法单独测试 |

这些痛点不是用法问题,根子在官方的输入源加载器。

## LoadStreams 源码:只 get,从不 set

翻 ultralytics 的 `ultralytics/data/loaders.py`(简化):

```python
class LoadStreams:
    def __init__(self, sources="file.streams", vid_stride=1, buffer=False, channels=3):
        # ...
        self.caps[i] = cv2.VideoCapture(s)   # 直接打开,无任何参数配置

        # 只读取属性,从不设置
        w   = int(self.caps[i].get(cv2.CAP_PROP_FRAME_WIDTH))
        h   = int(self.caps[i].get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps =     self.caps[i].get(cv2.CAP_PROP_FPS)
```

**关键问题**:`LoadStreams` 对摄像头**只 `get` 读默认属性,不提供任何 `set` 接口**。也就是说,你想要的分辨率/帧率/后端/编码,官方根本没给入口——黑盒不是"封装得好",是"压根没开口"。

## GitHub Issues 佐证:这是已知、且未被采纳的局限

不是个例。官方仓库里大量用户撞同一堵墙:

- **[yolov5 #1757](https://github.com/ultralytics/yolov5/issues/1757)** "How to change the resolution of a usb camera" —— 摄像头 2304×1536、FPS 只有 2,无法修改。
- **[yolov5 #9402](https://github.com/ultralytics/yolov5/issues/9402)** "LoadStreams() can't get correct webcam resolution" —— 用户只能手动改 `dataloaders.py` 源码才能设分辨率。
- **[ultralytics #1446](https://github.com/ultralytics/ultralytics/issues/1446)** "Adjust webcam resolution for prediction" —— 功能请求被标记 Stale 关闭,官方未采纳。

> 据上述社区 issues,摄像头参数配置至今未进官方接口。换句话说:等官方支持,是等不到的。

## 官方社区的 workaround:改源码

目前社区唯一的办法,是**手动改 YOLO 的源码**:

```python
# 用户不得不在 dataloaders.py 里手动塞这几行
cap.set(cv2.CAP_PROP_FPS, 90)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```

这条路的代价:**改第三方库源码** / **升级 YOLO 版本后修改丢失** / **不同项目配置不同、无法统一管理**。对一个要长期维护的工程平台,这是不可接受的。

> **金句**: **"`source=` 不是黑盒封装得太严,是它在源码层面只读不写、压根没留配置口。官方 issue 关了、workaround 是改库源码——这条路堵死了。剩下唯一的选择:把输入源从 ultralytics 手里接管过来,自己管。"**

## 那……直接自己写 cv2 循环不就好了?

既然要自己接管,最直接的念头是绕开 YOLO、自己 `cv2.VideoCapture`:

```python
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 90)
model = YOLO("best.pt")
while True:
    ret, frame = cap.read()
    if not ret: break
    results = model.predict(frame)
```

这解决了"能不能配置"(能了),但**带来一串新问题**:

| 问题 | 影响 |
|---|---|
| 代码重复 | 每个脚本都要把摄像头配置抄一遍 |
| 多输入源切换麻烦 | 摄像头 / 视频 / 图片各写一套逻辑 |
| 元数据缺失 | 帧号、时间戳、分辨率要自己维护 |
| 难以测试 | 输入源与业务逻辑耦合 |
| 资源管理混乱 | 忘了 `cap.release()` 就泄漏 |

这些问题里,**多源切换、元数据**我们会在下面 8 面墙里亲身撞到;**统一接口、可测试、资源管理**留到最后总账时收。更要命的是:就算只用 raw cv2,**光是把摄像头真正跑到 90fps**,本身就是一连串墙——下面 8 个脚本,就是把"自己接管输入源"这条路上的墙,亲手一面一面撞过去。

---

# 阶段一:拆黑盒、拿回控制权

## 示例 `01_原生推理.py` —— 朴素方案,黑盒的起点

```python
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :01_原生推理.py
# @Function  :朴素方案,绝大多数 yolo 教程的做法
from ultralytics import YOLO

model = YOLO("train3-20250704-165500-yolo11n-best.pt")
model.predict(source="0", show=True)
```

它**能跑**:弹一个窗口,摄像头画面上实时画着检测框。表面看,推理一行就解决了。

### 🧱 撞墙 ①:这是个黑盒,你伸不进任何控制点

试着在这一行方案上,做几件工程化推理**一定会做**的事:

```text
需求 1:每帧推理完,把检测到的目标数写进数据库
需求 2:画面右下角叠我自己的水印,不是 ultralytics 默认的框
需求 3:检测到 "person" 超过 5 个时触发报警回调
需求 4:我想知道摄像头实际跑了多少 fps(不是推理耗时)
```

`model.predict(source="0", show=True)` 这一行里,**这 4 件事一件都插不进去**。`source=` 把"打开输入源 → 逐帧读 → 推理 → 画框 → 显示"全包在 ultralytics 内部了,你只能在外面看着它跑,没有任何钩子让你在"帧与帧之间"插逻辑。

**第一面墙:黑盒不可控。** 解法的第一步很自然——**别让 ultralytics 管输入源,我自己用 OpenCV 把帧读出来,推理只喂单帧**。

---

## 示例 `02-opencv接管输入源.py` —— 把读帧从 ultralytics 手里拿回来

```python
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :02-opencv接管输入源.py
import cv2
from ultralytics import YOLO

model = YOLO("train3-20250704-165500-yolo11n-best.pt")
cap = cv2.VideoCapture(0)          # ← 自己开摄像头

while True:
    ret, frame = cap.read()        # ← 控制点①:现在能在这里插逻辑了
    if not ret:
        break
    results = model(frame, verbose=False)   # ← 控制点②:推单帧,results 自己处理
    annotated_frame = results[0].plot()      # ← 控制点③:也可以不用 plot,自己画

    cv2.imshow("YOLOv8 Inference", annotated_frame)
    # ★ 修复:原版 waitKey(1) 被调用两次,第一次即消费按键,第二次永远拿不到 ESC
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break

cap.release()
cv2.destroyAllWindows()
```

跑起来跟 `01` 看着一样,但**性质变了**:`cap.read()` 和 `model(frame)` 之间、`results` 拿到之后,现在全是**你的地盘**,刚才那 4 个需求现在都能插进去了。

这版**解开了撞墙 ①(黑盒)**,但立刻暴露新问题——你怎么知道它跑得好不好?

---

# 阶段二:三连墙——可观测 / 配置 / 实测

## 示例 `03_opencv_叠加信息显示.py` —— 让系统从黑盒变仪表盘

`02` 能跑,但你盯着画面答不出任何量化问题:现在多少帧率?单帧推理几毫秒?跑到第几帧?分辨率多少?全是黑的。

工程化系统第一要求是**可观测**。`03` 把这些信息叠到画面上:

```python
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :03_opencv_叠加信息显示.py
import cv2, time
from ultralytics import YOLO

model = YOLO("train3-20250704-165500-yolo11n-best.pt")
cap = cv2.VideoCapture(0)

frame_index = 0
fps = 0.0
last_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    t_start = time.time()
    results = model(frame, verbose=False)
    t_end = time.time()
    infer_ms = (t_end - t_start) * 1000          # 单帧推理耗时

    # ★ 修复:原版 dt 用 time.time() 但 last_time 存的是 t_end,时间基混用
    now = time.time()
    fps = 1.0 / (now - last_time)                 # 循环帧率
    last_time = now
    h, w = frame.shape[:2]                         # 当前帧尺寸

    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f"FPS: {fps:.2f}",          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Infer: {infer_ms:.2f} ms", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Frame: {frame_index}",     (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Resolution: {w}x{h}",      (10,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("YOLOv8 Inference", annotated_frame)
    # ★ 修复:pollKey 不驱动窗口事件循环,Windows/macOS 上窗口可能不刷新或假死
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break
    frame_index += 1

cap.release()
cv2.destroyAllWindows()
```

### 🧱 撞墙 ②:系统不可观测

现在画面上能看到 fps / 推理耗时 / 帧序号 / 分辨率——**系统从黑盒变成了仪表盘**。这是第二面墙的解法。

> **伏笔(`pollKey` vs `waitKey`)**:`waitKey(1)` 会阻塞至少 1ms 等键盘事件,`pollKey()` 不阻塞立即返回,但它**不驱动 GUI 事件循环**,窗口会假死/不刷新。这个差别现在看无所谓,到撞墙 ⑥(摄像头满速)时会变成帧率与卡顿的关键。先记住。

---

## 示例 `04_opencv_输入输出控制.py` —— 参数集中 + 输入/输出控制分离

`03` 能观测了,但分辨率、目标帧率、显示窗口大小全是 magic number,散落在代码各处。想把摄像头跑 1280×720@90、显示缩到 1280×720,得翻好几处改。这是配置散乱。

`04` 把**输入控制**和**输出控制**的参数拎到文件顶部:

```python
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :04_opencv_输入输出控制.py
import cv2, time
from ultralytics import YOLO

# ── 输入控制:请求摄像头按这个参数采集 ──
CAMERA_WIDTH  = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS    = 90
# ── 输出控制:显示窗口缩放,不影响推理 ──
DISPLAY_WIDTH  = 1280
DISPLAY_HEIGHT = 720

model = YOLO("train3-20250704-165500-yolo11n-best.pt")
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS,          CAMERA_FPS)

actual_width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
actual_fps    = cap.get(cv2.CAP_PROP_FPS)
# ★ 修复:摄像头没有总帧数(CAP_PROP_FRAME_COUNT 返回 -1 或 0),单独处理
total_frames  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
if total_frames > 0:
    print(f"摄像头参数: {actual_width}x{actual_height} @ {actual_fps}fps, 总帧数={total_frames}")
else:
    print(f"摄像头参数: {actual_width}x{actual_height} @ {actual_fps}fps (无总帧数)")

frame_index = 0
fps = 0.0
last_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    t_start = time.time()
    results = model(frame, verbose=False)
    t_end = time.time()
    infer_ms = (t_end - t_start) * 1000

    now = time.time()                  # ★ 修复:时间基统一
    fps = 1.0 / (now - last_time)
    last_time = now

    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f"FPS: {fps:.2f}",   (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Infer: {infer_ms:.2f} ms", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Frame: {frame_index}", (10,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Size: {actual_width}x{actual_height}", (10,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    # 输出控制:缩放显示,推理仍在原始分辨率上做
    if DISPLAY_WIDTH is not None and DISPLAY_HEIGHT is not None:
        display_frame = cv2.resize(annotated_frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT), interpolation=cv2.INTER_LINEAR)
    else:
        display_frame = annotated_frame
    cv2.imshow("YOLOv8 Inference", display_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    frame_index += 1

cap.release()
cv2.destroyAllWindows()
```

### 🧱 撞墙 ③:参数硬编码,改个分辨率要翻遍代码

`04` 的纪律:**输入控制**(请求摄像头按 1280×720@90 采集)和**输出控制**(显示窗口缩到多大)是两件事。关键——**推理永远在原始采集分辨率上做,`cv2.resize` 只缩放显示**。先 resize 再推理 = 降低推理输入分辨率,精度会掉。

> 这条"采集分辨率 ≠ 显示分辨率,推理跟采集走"的区分,后面会变成 `frame_source` 里 `FrameInfo.width/height`(采集尺寸)与下游显示缩放的职责分离。

这版**解开了撞墙 ③(配置散乱)**,但 `print` 出来的 `actual_fps` 真的可信吗?

---

## 示例 `05_opencv捕获_真实输入输出测试.py` —— "标称帧率"是假的,必须实测

`04` 用 `cap.get(CAP_PROP_FPS)` 读回 `90.0`,你以为摄像头真在跑 90fps。**错。**

`cap.get(CAP_PROP_FPS)` 返回的是摄像头**自己上报的标称值**——它说能跑 90,不代表真在跑 90。真实采集帧率受 USB 带宽、编码格式、后端、自动曝光等一堆因素影响,标称值经常虚高。

`05` 加了一个**实测帧率**:每隔 1 秒数一次实际读到多少帧,用"实际帧数 / 经过秒数"算真值,跟标称值并排对比(核心片段):

```python
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :05_opencv捕获_真实输入输出测试.py
# ... 配置 + set + get 同 04 ...

# ── 验证参数是否真生效(set 失败不报错,必须 get 读回来验)──
if actual_width != CAMERA_WIDTH or actual_height != CAMERA_HEIGHT:
    print(f"⚠️ 分辨率未生效:期望 {CAMERA_WIDTH}x{CAMERA_HEIGHT},实际 {actual_width}x{actual_height}")
if actual_fps < CAMERA_FPS:
    print(f"⚠️ 帧率未生效:期望 {CAMERA_FPS},实际标称 {actual_fps:.1f}")

# ── 实测摄像头真实采集帧率 ──
camera_frame_count = 0
camera_fps_timer   = time.time()
real_camera_fps    = 0.0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    camera_frame_count += 1
    elapsed = time.time() - camera_fps_timer
    if elapsed >= 1.0:                              # 每 1 秒刷新一次实测值
        real_camera_fps    = camera_frame_count / elapsed
        camera_frame_count = 0
        camera_fps_timer   = time.time()

    results = model(frame, verbose=False)
    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f"Loop FPS:   {loop_fps:.1f}",        (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Camera FPS: {real_camera_fps:.1f}", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)  # ← 实测值
    # ★ 修复:原版 imshow 被注释掉了,跑起来看不到窗口;且必须用 waitKey 而非 pollKey
    cv2.imshow("Detection", display_frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break
```

### 🧱 撞墙 ④:标称帧率不可信

跑起来你会看到**两个 fps 数字打架**:标称写着 90,实测可能只有 28。真相大白——**摄像头根本没在跑 90fps**,标称值是空头支票。

> **金句**:`cap.set()` 是**请求**不是命令,`cap.get()` 读回的是摄像头的"自我宣传"。工程化推理只信一个数:你自己掐表数出来的实测帧率。这条"**set 是请求 / get 要验证 / fps 要实测**"的三连纪律,后面会全部沉淀进 `frame_source` 的 `CameraSource.open()`。

**那 28 是硬件极限吗?还是有办法让它真的跑到 90?** —— 大概率有办法,而且不在"设 fps",在**编码格式和后端**:USB 摄像头默认常用 YUYV(未压缩),1280×720 的 YUYV 帧很大,USB 带宽喂不动 90fps;换成 **MJPG**(摄像头内部硬件 JPEG 压缩)同样带宽能塞下 90fps。但"换 MJPG"在 Windows 上还得选对**后端**、按特定顺序设参数——这正是 `06`/`07`/`08` 要撞的最后三面墙。

---

# 阶段三:摄像头满速跑不起来——后端 / 线程 / 解耦三连墙

## 示例 `06_摄像头后端自己选择.py` —— 显式选后端 + MJPG + 采集/显示双线程

`05` 实测只有 28fps。`06` 一次性把三件事做对:① 显式指定 **MSMF 后端** + **MJPG 编码** + 禁用硬件变换;② **采集线程与显示主线程分离**;③ 显示限速 30fps,不占采集带宽(核心结构):

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @FileName  :06_摄像头后端自己选择.py
import os, time, threading
from typing import Optional, List   # ★ 修复:向 Python 3.9 兼容
import cv2, numpy as np

# ★ MSMF 必须在创建 VideoCapture 之前设置,禁用硬件变换,否则插入色彩转换滤镜拖低帧率
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

CAMERA_ID, WIDTH, HEIGHT, TARGET_FPS, DURATION = 0, 1280, 720, 90, 30

latest_frame: Optional[np.ndarray] = None
frame_lock  = threading.Lock()       # 保护 latest_frame 读写
stop_event  = threading.Event()
ready_event = threading.Event()
count = dropped = 0

def capture_thread():
    global count, dropped, latest_frame
    cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_MSMF)     # ← 显式 MSMF 后端
    if not cap.isOpened():
        stop_event.set(); ready_event.set(); return

    # ★ 参数顺序:分辨率 → FOURCC → FPS
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))   # ← MJPG 压缩
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
    cap.read()                                          # ★ 触发格式协商,之后 get() 才准

    ready_event.set()
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            dropped += 1; continue
        count += 1
        with frame_lock:                                # ← 加锁写最新帧,防撕裂
            latest_frame = frame
    cap.release()

if __name__ == "__main__":
    t = threading.Thread(target=capture_thread, daemon=True)
    t.start()
    ready_event.wait(timeout=10)

    # ── 显示主循环,限 30fps,不占采集带宽 ──
    display_interval, last_display = 1.0 / 30, 0.0
    while not stop_event.is_set():
        now = time.perf_counter()
        if now - last_display < display_interval:
            time.sleep(0.001); continue
        last_display = now
        with frame_lock:
            frame = None if latest_frame is None else latest_frame.copy()
        if frame is None:
            continue
        # ... OSD 叠加实时/峰值/低谷 fps + 进度条 ...
        cv2.imshow("MSMF MJPG Benchmark", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):           # ★ waitKey 驱动事件循环,必须调用
            stop_event.set()
    t.join(); cv2.destroyAllWindows()
```

### 🧱 撞墙 ⑤:设了 90 只跑 28 —— 后端/编码/顺序都得对

显式 `CAP_MSMF` + `MJPG` + 禁用硬件变换 + 按"分辨率→FOURCC→FPS"顺序设参数 + 先 `read()` 触发协商。这一套下来,实测帧率才有机会冲到 90。

### 🧱 撞墙 ⑥:`imshow` + `waitKey` 拖垮采集

`imshow + waitKey` 在 Windows 下每帧约 10~16ms。若放在采集循环里,会直接把采集压到 60fps 以下。`06` 的解法:**采集线程只管 `cap.read()`,显示丢给主线程**,两者用一把锁 + 一个 `latest_frame` 共享变量解耦。这就是撞墙 ③ 那个 `pollKey/waitKey` 伏笔的归宿。

---

## 示例 `07_opencv摄像头测试.py` —— 队列传帧 + 显示文本每秒只刷一次

`07` 是双线程的另一种实现:用 `queue.Queue(maxsize=1)` 传帧。并且解决一个**观感**问题——FPS 计算照旧用窗口算,但贴到画面上的字符串每秒才换一次,避免末位数字疯狂跳动晃眼(核心结构):

```python
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :07_opencv摄像头测试.py
import cv2, time, threading, queue

CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, CAMERA_FOURCC = 0, 1280, 720, 90, "MJPG"
DISPLAY_TEXT_REFRESH_SEC = 1.0      # ★ 显示文本刷新间隔,底层采样仍按窗口算

frame_queue: queue.Queue = queue.Queue(maxsize=1)
running = threading.Event(); running.set()

def camera_thread_func():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*CAMERA_FOURCC))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          CAMERA_FPS)
    backend_name = cap.getBackendName()                 # ← 后端自己上报名字

    for _ in range(30):                                 # ← 预热 30 帧
        cap.read()

    cam_fps_text, frame_count, fps_timer = "Cam FPS: --", 0, time.perf_counter()
    while running.is_set():
        ret, frame = cap.read()
        if not ret:
            continue
        frame_count += 1
        if time.perf_counter() - fps_timer >= 1.0:
            cam_fps_text = f"Cam FPS: {frame_count / (time.perf_counter() - fps_timer):.1f}"  # ★ 1 秒才更新文本
            frame_count, fps_timer = 0, time.perf_counter()
        # ... putText(帧号/时间戳/cam_fps_text) ...
        try: frame_queue.get_nowait()                   # ← 队列只留最新一帧
        except queue.Empty: pass
        frame_queue.put(frame)
    cap.release()

# 主线程:从 frame_queue 取帧显示,GUI FPS 也用 30 帧窗口均值 + 每秒刷一次文本
```

### 🧱 撞墙 ⑦:文字抖动 —— 队列该留哪一帧

`queue.Queue(maxsize=1)` + 取新帧前先 `get_nowait()` 清掉旧的 = **宁丢勿堆,永远只留最新一帧**。配合"FPS 计算照旧、显示文本每秒才刷"消掉末位数字抖动。

---

## 示例 `08_opencv摄像头测试_多线程.py` —— deque 自动丢帧,证明解耦有效

`08` 与 `07` 同源,改用 `deque(maxlen=1)` 传最新帧。重点是**用帧号 + 时间戳实证**:摄像头满速采集,窗口只渲染 30fps,中间多余的帧被 deque 自动丢弃,从而保证画面无延迟(核心结构):

```python
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :08_opencv摄像头测试_多线程.py
import cv2, time, threading
from collections import deque

CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS = 1280, 720, 60
DISPLAY_FPS_WINDOW, DISPLAY_TEXT_REFRESH_SEC = 10, 1.0

latest_frame = deque(maxlen=1)      # ← maxlen=1:新帧入队自动挤掉旧帧
frame_lock = threading.Lock()
running = True

def camera_thread_func():
    global running
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          CAMERA_FPS)
    for _ in range(30):                                 # 预热
        cap.read()
    while running:
        ret, frame = cap.read()
        if not ret:
            continue
        # putText(Capture Index 飞速跳动 ← 证明非重复帧 / 时间戳 / Real FPS)
        with frame_lock:
            latest_frame.append(frame)                  # ← 持续覆盖
    cap.release()

# 主线程:latest_frame[-1].copy() 取最新帧;Display FPS 用窗口均值 + 每秒刷文本
# 结论:Index 飞跳(非重复帧)、Real FPS ≈ 满速、Display FPS ≈ 30,差值帧被自动丢弃
```

### 🧱 撞墙 ⑧:怎么证明解耦真有效

画面左上角:红色 `Index` 飞速跳动(证明拿到的不是重复帧)、绿色 `Real FPS` 稳定在满速、黄色 `Display FPS` 稳定在 30。**采集和显示的帧率被肉眼可见地拉开了**,中间差值的帧被 deque 自动丢弃。八面墙,到这里全部撞完。

---

# 八面墙汇总,三个信号亮起

回头看这条 8 步演进链,每个脚本都是上一面墙逼出来的:

| 脚本 | 表面问题 | 真正问题 | 解法 |
|---|---|---|---|
| `01_原生推理` | 一行不够吗 | 黑盒,帧间无控制点 | 自己 cv2 读帧 |
| `02-opencv接管输入源` | 控制权拿回来了 | —(过渡) | `model(frame)` 喂单帧 |
| `03_opencv_叠加信息显示` | 跑得好不好看不出 | 不可观测 | 叠加 fps/耗时/帧号 |
| `04_opencv_输入输出控制` | 改分辨率要翻代码 | 配置散乱 | 参数集中 + 输入/输出分离 |
| `05_opencv捕获_真实输入输出测试` | get 的 fps 是 90 | 标称值不可信 | 实测帧率 |
| `06_摄像头后端自己选择` | 设了 90 只跑 28 | 后端/编码/顺序错 | MSMF + MJPG + 顺序协商 |
| `07_opencv摄像头测试` | 文字疯狂跳动 | 旧帧无价值 + 观感 | 队列 maxsize=1 + 文本节流 |
| `08_opencv摄像头测试_多线程` | 怎么证明解耦有效 | — | deque maxlen=1 + 帧号实证 |

把这 8 面墙叠在一起,**三个信号同时亮起**——它们都指向同一个结论:**"打开输入源并稳定出帧"这件事,复杂到必须从推理循环里剥出来,单独做成一层基础设施。**

**信号一:输入源种类太多,但推理循环不该关心它们的差异。**
图、目录、视频、摄像头、RTSP——打开方式、参数协商、帧率特性、资源释放各不相同。如果把这些差异全写进推理循环,循环里会塞满 `if source_type == ...` 的分支。推理循环真正想要的,只是"给我下一帧"。

**信号二:摄像头那套脏活(后端 / 编码 / 顺序 / 线程 / 丢帧)和推理毫无关系,却严重污染推理代码。**
`06`/`07`/`08` 撞出来的 MSMF、MJPG、参数顺序、双线程、deque——这些是"怎么把帧弄出来"的事,跟"拿到帧之后怎么推理"是两个完全正交的关注点。它们不该和 `model(frame)` 挤在同一个文件里。

**信号三:这套"出帧"能力,D8 推理要用,D9 web 实时推理也要用,甚至 D7 边验证边可视化也能用。**
它是**跨任务的基础设施**,不该绑死在推理子系统里;它甚至应该能脱离整个平台,**整包拷到任何 Python 项目就能跑**。

---

# 引出:`frame_source` 模块

三个信号合起来,就是我们接下来要发明的东西——一个叫 `frame_source` 的子模块。它要做且**只做**一件事:**把图 / 目录 / 视频 / 摄像头 / RTSP 这五类源,统一成一个"打开 → 逐帧出帧 → 关闭"的协议,让推理循环对所有源长一个样。**

它存在的全部意义,可以用一段调用方代码概括——无论 `src` 是哪类源,这一段都不变:

```python
def run(src):
    with src as s:
        for frame in s:
            model.predict(frame.image)    # ← 图/视频/目录/摄像头,这一行都一样,没有一个 if
```

八面墙撞出来的所有复杂度(后端协商 / 线程 / 丢帧 / 实测帧率),全都被关进各个源自己的类里;调用方的 `run()` 干净得像伪代码。

它的几条硬边界(决定了它长什么样),先立在这里:

- **职责单一**:只解决"出帧"。不碰推理、不碰配置、不碰日志、不碰落盘——那些是 `InferService` 和 D5/D2 的事。
- **独立成模块**:做成一个**顶层平级独立包**(`frame_source/`,跟 `common/`、`inference/` 平级),既不藏在 `inference/` 下(否则 D9 web 用它就反向依赖了推理),也不塞进 `common/`(那是本平台内部共享层,物种不同)。谁都不拥有它,谁都平等地用。
- **零宿主依赖**:包内**一行都不能** `from odp_platform...`。需要的常量(如图片/视频扩展名)它**自己重定义一份**。这条是它的灵魂——只有依赖断到 0,它才能整包 `cp -r` 拷到别的项目照样跑。
- **三层结构**:抽象基类(统一协议)+ 具体源(各自实现脏活)+ 装饰器(线程 / async 这类正交能力)。每一层都是上面某面墙逼出来的,不是过度设计。

## 三方对决:官方 / 手写 cv2 / frame_source

把"官方 `source=`""手写 cv2 循环""frame_source"摆在一起,一眼看清各自补上了什么、漏掉了什么:

| 特性 | YOLO 官方 | 手写 cv2 | frame_source |
|---|---|---|---|
| 摄像头分辨率配置 | ❌ | ✅ | ✅ |
| 摄像头帧率配置 | ❌ | ✅ | ✅ |
| 后端选择(MSMF/DShow/V4L2) | ❌ | ✅ | ✅ |
| 高帧率支持(90fps) | ❌ | ✅ | ✅ |
| 4K 摄像头支持 | ❌ | ✅ | ✅ |
| 统一接口(一套吃所有源) | ✅ | ❌ | ✅ |
| 多输入源零改切换 | ✅ | ❌ | ✅ |
| 上下文管理(`with`) | ❌ | ❌ | ✅ |
| 迭代器协议(`for`) | ✅ | ❌ | ✅ |
| 元数据(帧号/时间戳/尺寸) | 部分 | ❌ | ✅ |
| seek 跳帧 | ❌ | 手动实现 | ✅ |
| 日志可配置 | ❌ | ❌ | ✅ |
| 类型安全 | ❌ | ❌ | ✅ |
| 独立于 YOLO 版本 | ❌ | ✅ | ✅ |

官方占了"统一/迭代"但全盘丢了"可配置";手写 cv2 反过来,拿到了"可配置"却丢了"统一/可维护"。**frame_source 是唯一一列从上到下全是 ✅ 的**——它把两条路的优点合并,把两条路的坑都填上。

## 它能撑起的真实场景

把上面那些 ✅ 落到工地安全帽检测,就是这几类活(以下用模块的公开 API 写):

**场景 1 · 高帧率检测** —— 传送带上快速移动的目标,需要高帧率不丢关键帧:

```python
config = CameraConfig(width=1280, height=720, fps=90, backend="msmf", codec="MJPG")
with create_frame_source("0", camera_config=config) as src:
    for frame in src:
        detect(frame.image)        # 90fps 输入,实测帧率/丢帧策略都在模块内
```

**场景 2 · 4K 监控** —— 大范围工地,要看清远处人员:

```python
config = CameraConfig(width=3840, height=2160, fps=30)
with create_frame_source("0", camera_config=config) as src:
    for frame in src:
        detect(frame.image)
```

**场景 3 · 视频审查** —— 事后快速跳到关键时间点(注意参数名是 `time_sec`,避免遮蔽 `time` 模块):

```python
with create_frame_source("site_recording.mp4") as src:
    src.seek(time_sec=2*3600 + 30*60)   # 跳到 2 小时 30 分
    for frame in src:
        analyze(frame.image)
```

**场景 4 · 数据集验证** —— 配合数据校验,批量过标注,且知道进度与文件名:

```python
with create_frame_source("./dataset/images/train") as src:
    for frame in src:
        info = frame.info               # 元数据统一挂在 frame.info 上
        print(f"验证 [{info.frame_index}/{info.total_frames}] {info.filename}")
```

## 结论:frame_source 的必要性

1. **填补官方空白**:ultralytics 至今不支持摄像头参数配置,相关 issue 被关,根子在 `LoadStreams` 只读不写。
2. **满足真实需求**:720p@90fps、4K 这类高性能摄像头,官方接口下根本发挥不出来。
3. **解耦设计**:输入源处理独立于推理引擎,可单独测试、单独维护。
4. **统一抽象**:一套接口覆盖图/视频/目录/摄像头/RTSP,下游零改切换。
5. **长期可维护**:不依赖 YOLO 版本,升级无影响;零依赖宿主,整包可移植。

> **核心价值**: **让硬件能力被充分发挥,而不是被框架限制——官方接不住的(必要性)、自己写会撞墙的(复杂度),frame_source 一次性收口。**

---

> **交接点到此为止。**
>
> 官方为什么接不住(刨根)讲清、八面墙撞完(实撞)、三个信号亮起、`frame_source` 的职责和边界立清——前置铺垫的任务完成了。
>
> **下一步:从零开始写 `frame_source` 模块的真正代码。**

---

## 附录:相关链接

- Ultralytics LoadStreams 源码参考:`https://docs.ultralytics.com/reference/data/loaders/`
- Issue #1757(分辨率问题):`https://github.com/ultralytics/yolov5/issues/1757`
- Issue #9402(分辨率问题):`https://github.com/ultralytics/yolov5/issues/9402`
- Issue #1446(分辨率功能请求,已 Stale 关闭):`https://github.com/ultralytics/ultralytics/issues/1446`
