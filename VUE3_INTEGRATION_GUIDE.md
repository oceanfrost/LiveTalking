# Vue3 数字人前端集成指南

## 快速开始

### 1. 启动后端服务
```bash
conda activate nerfstream
python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1
```

### 2. 访问前端界面
- **Vue3完整版**: http://localhost:8010/vue3-digital-human.html
- **Vue3组件版**: http://localhost:8010/vue3-app.html
- **原版对比**: http://localhost:8010/webrtcapi.html

## 文件结构
```
web/
├── vue3-digital-human.html    # Vue3单文件完整版本
├── vue3-app.html             # Vue3组件化版本
├── digital-human.js          # Vue3数字人组件
├── digital-human.css         # 组件样式文件
├── webrtcapi.html           # 原版HTML(对比用)
└── client.js                # 原版JavaScript
```

## 前端拉流原理

### WebRTC连接流程
1. 创建RTCPeerConnection
2. 添加接收轨道(recvonly模式)
3. 创建Offer并发送到/offer接口
4. 接收服务器返回的Answer
5. 建立P2P连接，开始接收音视频流

### 核心代码示例
```javascript
// 创建连接
const pc = new RTCPeerConnection(config);

// 添加轨道
pc.addTransceiver('video', { direction: 'recvonly' });
pc.addTransceiver('audio', { direction: 'recvonly' });

// 监听媒体轨道
pc.addEventListener('track', (evt) => {
    if (evt.track.kind === 'video') {
        videoElement.srcObject = evt.streams[0];
    }
});

// 发送消息到数字人
fetch('/human', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: message,
        type: 'echo',
        interrupt: true,
        sessionid: sessionId
    })
});
```

## Vue3版本优势

### 1. 无破绽UI设计
- ✅ 隐藏所有技术细节和调试信息
- ✅ 现代化渐变背景和卡片设计
- ✅ 流畅的动画和过渡效果
- ✅ 响应式布局，支持移动端
- ✅ 专业的状态指示器

### 2. 用户体验提升
- ✅ 智能连接状态管理
- ✅ 优雅的加载动画
- ✅ 快捷消息按钮
- ✅ 全屏播放支持
- ✅ 音频静音控制
- ✅ 自动重连功能

### 3. 开发体验
- ✅ Vue3 Composition API
- ✅ 响应式数据绑定
- ✅ 组件化架构
- ✅ TypeScript友好
- ✅ 完整的错误处理

### 4. 高级功能
- ✅ 录制功能
- ✅ 下载录制文件
- ✅ 调试信息开关
- ✅ STUN服务器配置
- ✅ 暗色主题支持

## 自定义配置

### 修改服务器地址
```javascript
// 如果后端不在localhost:8010
const API_BASE = 'http://your-server:8010';

fetch(`${API_BASE}/offer`, {
    // ...
});
```

### 添加自定义快捷消息
```javascript
const quickMessages = ref([
    '你好！',
    '请介绍一下你自己',
    '今天天气怎么样？',
    '能为我唱首歌吗？',
    '谢谢你的帮助'
]);
```

### 自定义主题色
```css
:root {
    --primary-color: #4f46e5;
    --secondary-color: #7c3aed;
    --success-color: #10b981;
    --danger-color: #ef4444;
    --info-color: #06b6d4;
}
```

## 部署说明

### 服务器要求
- 开放TCP端口: 8010
- 开放UDP端口: 1-65535 (WebRTC需要)
- HTTPS部署时需要有效SSL证书

### NGINX代理配置
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket代理(如果需要)
    location /ws {
        proxy_pass http://localhost:8010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Docker部署
```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY web/ ./web/
EXPOSE 8010
CMD ["python", "app.py", "--transport", "webrtc"]
```

## 常见问题

### 1. 视频无法显示
- 检查网络连接
- 确认服务器端口开放
- 查看浏览器控制台错误

### 2. 音频没有声音
- 检查浏览器音频权限
- 确认扬声器/耳机连接
- 尝试取消静音

### 3. 连接频繁断开
- 启用STUN服务器选项
- 检查网络稳定性
- 考虑部署TURN服务器

### 4. 移动端兼容性
- 使用HTTPS协议
- 确认浏览器支持WebRTC
- 检查移动网络限制

## 性能优化

### 1. 减少资源加载
```html
<!-- 使用本地CDN或自托管 -->
<script src="/static/vue.min.js"></script>
```

### 2. 启用Gzip压缩
```nginx
gzip on;
gzip_types text/css application/javascript text/javascript;
```

### 3. 缓存静态资源
```nginx
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 开发扩展

### 添加新功能组件
```javascript
// 在digital-human.js中添加
const newFeature = ref(false);

const toggleNewFeature = () => {
    newFeature.value = !newFeature.value;
    // 实现功能逻辑
};

return {
    // 现有返回值
    newFeature,
    toggleNewFeature
};
```

### 集成第三方服务
```javascript
// 添加语音识别
const speechRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

speechRecognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    currentMessage.value = text;
};
```

这套Vue3前端解决方案提供了专业、美观、功能完整的数字人交互界面，完全隐藏了技术细节，为用户提供流畅的体验。