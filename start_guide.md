# LiveTalking 启动指南

## 启动后端服务

```bash
# 激活环境
conda activate nerfstream

# 启动服务 (WebRTC模式)
python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1

# 启动参数说明:
# --transport webrtc : 使用WebRTC传输协议
# --model wav2lip : 使用wav2lip模型
# --avatar_id wav2lip256_avatar1 : 指定头像ID
```

## 前端访问方式

服务启动后，后端会在端口8010上运行，需要开放：
- TCP端口: 8010
- UDP端口: 1-65536

前端访问地址：
- 基础版本: http://serverip:8010/webrtcapi.html
- ASR版本: http://serverip:8010/webrtcapi-asr.html  
- 自定义版本: http://serverip:8010/webrtcapi-custom.html

## WebRTC拉流原理

1. 前端创建RTCPeerConnection
2. 添加只接收的音视频轨道(recvonly)
3. 创建Offer并发送到后端/offer接口
4. 后端返回Answer，建立WebRTC连接
5. 通过WebRTC协议接收实时音视频流