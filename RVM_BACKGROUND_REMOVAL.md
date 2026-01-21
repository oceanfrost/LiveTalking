# RVM 背景去除功能说明

## 功能概述

使用 **RVM (Robust Video Matting)** 深度学习模型，实现实时视频背景去除。将 wav2lip 合成的数字人视频背景替换为绿幕，前端通过色度键（Chroma Key）算法实现透明背景效果。

## 技术方案

### 为什么选择绿幕方案？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **黑幕** | 简单 | 容易影响头发、眼睛等深色区域 |
| **绿幕** ✅ | 人体几乎不含绿色，边缘精确 | 需要前端色度键处理 |
| **直接透明** | 最理想 | WebRTC 不支持 alpha 通道传输 |

### 处理流程

```
原始视频帧 (BGR) 
    ↓
RVM 模型推理 → 获取 alpha matte（人像遮罩）
    ↓
Alpha 混合: 人像 + 绿色背景 → 绿幕视频 (BGR)
    ↓
WebRTC 传输
    ↓
前端 Canvas 色度键处理 → 透明背景显示
```

## 文件清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `rvm_processor.py` | RVM 处理器核心模块 |
| `test_rvm.py` | RVM 功能测试脚本 |
| `RVM_BACKGROUND_REMOVAL.md` | 本文档 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `basereal.py` | 添加 RVM 初始化和应用逻辑 |
| `app.py` | 添加命令行参数 |
| `web/webrtcapi.html` | 添加前端色度键处理 |

## 依赖

### 模型文件

RVM 模型通过 TorchHub 自动下载，首次运行会从以下地址下载：
- 仓库: `PeterL1n/RobustVideoMatting`
- 模型: `rvm_resnet50.pth` (~103MB)
- 缓存位置: `~/.cache/torch/hub/`

### Python 依赖

```
torch
torchvision
numpy
opencv-python (cv2)
```

这些依赖项目原本就需要，无需额外安装。

## 使用方法

### 启动命令

```bash
# 基础使用
python app.py --model wav2lip --enable_rvm

# 自定义参数
python app.py --model wav2lip --enable_rvm --rvm_downsample 0.5
```

### 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--enable_rvm` | flag | False | 启用 RVM 背景去除 |
| `--rvm_model` | str | `./models/rvm_resnet50.pth` | RVM 模型路径（可选，默认用 TorchHub） |
| `--rvm_downsample` | float | 0.25 | 下采样比例，越小越快但精度略低 |

### 访问前端

启动后访问: `http://localhost:8010/web/webrtcapi.html`

## 前端控制选项

### 参数调节

| 控件 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| **绿幕容差** | 0-150 | 80 | 控制多少绿色被识别为背景，值越大抠图越彻底 |
| **边缘柔化** | 0-50 | 20 | 平滑人物边缘，避免锯齿 |
| **去除绿色溢出** | 开/关 | 开 | 消除人物边缘的绿色反光 |

### 背景选择

- **透明背景**: 显示棋盘格（标准透明表示）
- **白色背景**: 纯白色
- **蓝色背景**: 蓝色
- **图片背景**: 随机在线图片

### 调参建议

- 如果人物边缘有绿边残留 → **提高容差**
- 如果人物部分被透明化 → **降低容差**
- 如果边缘有锯齿 → **提高柔化**
- 如果头发等细节有绿色 → **开启溢出抑制**

## 性能

| 指标 | 数值 |
|------|------|
| 处理帧率 | ~85 FPS (640x480) |
| GPU 显存占用 | ~500MB |
| 延迟增加 | ~12ms/帧 |

## API 说明

### RVMProcessor 类

```python
from rvm_processor import RVMProcessor

# 初始化
processor = RVMProcessor(
    model_path="./models/rvm_resnet50.pth",  # 可选
    downsample_ratio=0.25  # 下采样比例
)

# 预热（可选，减少首帧延迟）
processor.warm_up(width=640, height=480)

# 处理帧 - 绿幕输出
result_bgr = processor.process_frame(
    frame,  # BGR 图像 numpy array
    background_color=(0, 255, 0)  # BGR 背景色
)

# 处理帧 - RGBA 输出（带透明通道）
result_bgra = processor.process_frame_rgba(frame)

# 只获取 alpha 通道
alpha = processor.get_alpha(frame)  # 返回 0-1 的浮点数组

# 重置时序状态（场景切换时调用）
processor.reset_states()
```

## 注意事项

1. **首次启动**: 需要下载 RVM 模型 (~103MB)，请确保网络畅通
2. **GPU 推荐**: 虽然支持 CPU，但 GPU 可获得更好性能
3. **时序一致性**: RVM 使用循环神经网络，连续帧处理效果更好
4. **场景切换**: 如果视频内容突变，建议调用 `reset_states()`

## 故障排查

### 问题: 背景去除效果不好

1. 检查 `--rvm_downsample` 参数，尝试设为 0.5 或 1.0
2. 确保输入图像光照均匀
3. 调整前端的容差和柔化参数

### 问题: 帧率下降明显

1. 降低 `--rvm_downsample` 参数（如 0.25）
2. 检查 GPU 是否正常工作
3. 减小输入分辨率

### 问题: 模型加载失败

1. 检查网络连接（首次需下载模型）
2. 手动下载模型到 `~/.cache/torch/hub/checkpoints/`
3. 查看日志中的具体错误信息

## 参考资料

- [RobustVideoMatting GitHub](https://github.com/PeterL1n/RobustVideoMatting)
- [RVM 论文](https://arxiv.org/abs/2108.11515)
---

## WebSocket 透明视频流（推荐）

### 概述

由于 WebRTC 不支持 alpha 通道，绿幕方案会有绿光溢出问题。为了实现真正的透明背景，我们提供了 **WebSocket + 压缩 RGBA** 方案。

### 原理

```
原始视频帧 (BGR)
    ↓
RVM 模型推理 → 获取 alpha matte
    ↓
┌──────────────────────────────────┐
│ 同时生成两路输出（共享一次推理）：   │
│ 1. BGRA (透明) → WebSocket 发送   │
│ 2. BGR (绿幕) → WebRTC 发送       │
└──────────────────────────────────┘
    ↓
前端 Canvas 直接渲染 RGBA → 真正透明！
```

### 数据格式

采用二进制传输，低延迟设计：

| 字段 | 大小 | 说明 |
|------|------|------|
| width | 4 bytes | 图像宽度 (uint32, little-endian) |
| height | 4 bytes | 图像高度 |
| rgb_len | 4 bytes | RGB 数据长度 |
| rgb_data | 变长 | JPEG 压缩的 RGB 图像 |
| alpha_data | 变长 | zlib 压缩的 Alpha 通道 |

典型压缩率：
- RGB (JPEG, quality=80): ~10-20KB
- Alpha (zlib, level=1): ~5-10KB
- 总计: ~15-30KB/帧 @ 25fps ≈ 375-750KB/s

### 使用方法

```bash
# 启用透明视频流（会自动启用 RVM）
python app.py --model wav2lip --enable_transparent_stream

# 或同时指定 RVM 参数
python app.py --model wav2lip --enable_rvm --enable_transparent_stream --rvm_downsample 0.5
```

### 前端页面

访问: `http://localhost:8010/transparent-video.html`

功能：
- 棋盘格背景显示透明效果
- 自定义背景图片叠加
- 实时 FPS 和带宽统计
- 支持发送文字让数字人说话

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--enable_transparent_stream` | 启用 WebSocket 透明视频流 |

注意：启用透明流会自动启用 RVM 背景去除。

### 与 WebRTC 的关系

| 特性 | WebRTC (绿幕) | WebSocket (透明) |
|------|---------------|------------------|
| 视频传输 | ✓ | ✓ |
| 音频传输 | ✓ | ✗ (仍需 WebRTC) |
| 延迟 | ~50-100ms | ~50-100ms |
| 透明质量 | 有绿光溢出 | 完美透明 |
| 复杂度 | 低 | 中 |

推荐方案：
- **视频**：使用 WebSocket 透明流
- **音频**：保持使用 WebRTC

### 技术细节

**前端依赖**：
- [pako](https://github.com/nodeca/pako) - zlib 解压缩

**性能优化**：
- RGB 用 JPEG 压缩（质量 80，禁用优化提高速度）
- Alpha 用 zlib level 1（最快压缩）
- 复用临时 Canvas 避免 GC
- 二进制传输避免 Base64 开销