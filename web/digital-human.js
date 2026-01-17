// digital-human.js - Vue3数字人组件
export default {
    name: 'DigitalHuman',
    template: `
        <div class="digital-human-container">
            <!-- 视频显示区域 -->
            <div class="video-section" :class="{ 'fullscreen': isFullscreen }">
                <video 
                    ref="videoElement"
                    :class="['digital-human-video', { 'hidden': !isConnected }]"
                    autoplay 
                    playsinline 
                    muted
                    @click="toggleFullscreen">
                </video>
                
                <!-- 状态遮罩 -->
                <div v-if="!isConnected" class="status-overlay">
                    <div class="status-content">
                        <div v-if="isConnecting" class="loading-animation">
                            <div class="pulse"></div>
                            <p>正在连接数字人...</p>
                        </div>
                        <div v-else class="waiting-state">
                            <div class="avatar-placeholder">
                                <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
                                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4z" fill="currentColor"/>
                                    <path d="M12 14c-4.42 0-8 1.79-8 4v2h16v-2c0-2.21-3.58-4-8-4z" fill="currentColor"/>
                                </svg>
                            </div>
                            <p>数字人助手待命中</p>
                        </div>
                    </div>
                </div>

                <!-- 控制按钮浮层 -->
                <div v-if="isConnected" class="video-controls">
                    <button @click="toggleFullscreen" class="control-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                            <path d="M7 14H5v5h5v-2H7v-3zM5 10h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" fill="currentColor"/>
                        </svg>
                    </button>
                    <button @click="toggleMute" class="control-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                            <path v-if="!isMuted" d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" fill="currentColor"/>
                            <path v-else d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" fill="currentColor"/>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- 主控制面板 -->
            <div class="control-panel">
                <!-- 连接控制 -->
                <div class="connection-controls">
                    <button 
                        @click="startConnection" 
                        :disabled="isConnecting || isConnected"
                        class="btn btn-primary btn-large">
                        {{ connectionButtonText }}
                    </button>
                    <button 
                        @click="stopConnection" 
                        :disabled="!isConnected"
                        class="btn btn-danger">
                        断开连接
                    </button>
                </div>

                <!-- 对话区域 -->
                <div class="chat-area">
                    <div class="input-group">
                        <textarea 
                            v-model="currentMessage"
                            @keydown.enter.ctrl="sendMessage"
                            placeholder="输入您想说的话... (Ctrl+Enter发送)"
                            class="message-input"
                            :disabled="!isConnected">
                        </textarea>
                        <button 
                            @click="sendMessage" 
                            :disabled="!canSendMessage"
                            class="btn btn-primary send-btn">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor"/>
                            </svg>
                            发送
                        </button>
                    </div>
                </div>

                <!-- 快捷消息 -->
                <div class="quick-messages">
                    <button 
                        v-for="msg in quickMessages" 
                        :key="msg"
                        @click="sendQuickMessage(msg)"
                        :disabled="!isConnected"
                        class="btn btn-outline quick-msg-btn">
                        {{ msg }}
                    </button>
                </div>

                <!-- 功能按钮 -->
                <div class="feature-buttons">
                    <button 
                        @click="toggleRecording"
                        :disabled="!isConnected"
                        :class="['btn', isRecording ? 'btn-danger' : 'btn-success']">
                        {{ recordButtonText }}
                    </button>
                    
                    <button 
                        @click="downloadRecording"
                        :disabled="!hasRecording"
                        class="btn btn-info">
                        下载录制
                    </button>
                </div>

                <!-- 高级设置 -->
                <details class="advanced-settings">
                    <summary>高级设置</summary>
                    <div class="settings-grid">
                        <label class="setting-item">
                            <input type="checkbox" v-model="useStunServer">
                            <span>使用STUN服务器</span>
                        </label>
                        <label class="setting-item">
                            <input type="checkbox" v-model="autoReconnect">
                            <span>自动重连</span>
                        </label>
                        <label class="setting-item">
                            <input type="checkbox" v-model="showDebugInfo">
                            <span>显示调试信息</span>
                        </label>
                    </div>
                </details>

                <!-- 调试信息 -->
                <div v-if="showDebugInfo" class="debug-info">
                    <h4>连接状态: {{ connectionState }}</h4>
                    <p>会话ID: {{ sessionId }}</p>
                    <p>消息计数: {{ messageCount }}</p>
                    <p>录制状态: {{ isRecording ? '录制中' : '未录制' }}</p>
                </div>
            </div>

            <!-- 隐藏的音频元素 -->
            <audio ref="audioElement" autoplay :muted="isMuted"></audio>
        </div>
    `,
    
    setup() {
        const { ref, computed, onMounted, onUnmounted, watch } = Vue;
        
        // 基本状态
        const isConnecting = ref(false);
        const isConnected = ref(false);
        const isRecording = ref(false);
        const isMuted = ref(false);
        const isFullscreen = ref(false);
        const hasRecording = ref(false);
        
        // 用户设置
        const useStunServer = ref(true);
        const autoReconnect = ref(true);
        const showDebugInfo = ref(false);
        
        // 消息相关
        const currentMessage = ref('');
        const messageCount = ref(0);
        const sessionId = ref(0);
        
        // DOM引用
        const videoElement = ref(null);
        const audioElement = ref(null);
        
        // WebRTC相关
        let pc = null;
        const connectionState = ref('new');
        
        // 快捷消息
        const quickMessages = ref([
            '你好！',
            '请介绍一下自己',
            '今天天气怎么样？',
            '谢谢你的帮助',
            '再见！'
        ]);

        // 计算属性
        const connectionButtonText = computed(() => {
            if (isConnecting.value) return '连接中...';
            if (isConnected.value) return '已连接';
            return '开始对话';
        });

        const recordButtonText = computed(() => {
            return isRecording.value ? '停止录制' : '开始录制';
        });

        const canSendMessage = computed(() => {
            return isConnected.value && currentMessage.value.trim().length > 0;
        });

        // WebRTC方法
        const createPeerConnection = () => {
            const config = { sdpSemantics: 'unified-plan' };
            
            if (useStunServer.value) {
                config.iceServers = [
                    { urls: ['stun:stun.l.google.com:19302'] },
                    { urls: ['stun:stun.miwifi.com:3478'] }
                ];
            }

            pc = new RTCPeerConnection(config);

            // 监听事件
            pc.addEventListener('track', handleTrack);
            pc.addEventListener('connectionstatechange', handleConnectionStateChange);
            pc.addEventListener('iceconnectionstatechange', handleIceConnectionStateChange);

            return pc;
        };

        const handleTrack = (evt) => {
            console.log('收到媒体轨道:', evt.track.kind);
            if (evt.track.kind === 'video' && videoElement.value) {
                videoElement.value.srcObject = evt.streams[0];
            } else if (evt.track.kind === 'audio' && audioElement.value) {
                audioElement.value.srcObject = evt.streams[0];
            }
        };

        const handleConnectionStateChange = () => {
            connectionState.value = pc.connectionState;
            console.log('连接状态变化:', pc.connectionState);
            
            if (pc.connectionState === 'connected') {
                isConnected.value = true;
                isConnecting.value = false;
                console.log('WebRTC连接成功建立');
            } else if (pc.connectionState === 'failed') {
                console.error('WebRTC连接失败');
                if (autoReconnect.value && isConnected.value) {
                    console.log('将在3秒后尝试自动重连...');
                    setTimeout(() => startConnection(), 3000);
                }
                isConnected.value = false;
                isConnecting.value = false;
            } else if (pc.connectionState === 'disconnected') {
                console.warn('WebRTC连接断开');
                if (autoReconnect.value && isConnected.value) {
                    console.log('将在3秒后尝试自动重连...');
                    setTimeout(() => startConnection(), 3000);
                }
                isConnected.value = false;
                isConnecting.value = false;
            }
        };

        const handleIceConnectionStateChange = () => {
            console.log('ICE连接状态:', pc.iceConnectionState);
        };

        const negotiate = async () => {
            if (!pc) return;

            try {
                // 添加轨道
                pc.addTransceiver('video', { direction: 'recvonly' });
                pc.addTransceiver('audio', { direction: 'recvonly' });

                // 创建和设置offer
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);

                // 等待ICE收集
                await waitForIceGathering();

                // 发送offer
                const response = await fetch('/offer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        sdp: pc.localDescription.sdp,
                        type: pc.localDescription.type,
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const answer = await response.json();
                sessionId.value = answer.sessionid;
                
                await pc.setRemoteDescription(answer);
                
            } catch (error) {
                console.error('协商失败:', error);
                throw error;
            }
        };

        const waitForIceGathering = () => {
            return new Promise((resolve) => {
                if (pc.iceGatheringState === 'complete') {
                    resolve();
                } else {
                    const checkState = () => {
                        if (pc.iceGatheringState === 'complete') {
                            pc.removeEventListener('icegatheringstatechange', checkState);
                            resolve();
                        }
                    };
                    pc.addEventListener('icegatheringstatechange', checkState);
                }
            });
        };

        // 公共方法
        const startConnection = async () => {
            if (isConnecting.value || isConnected.value) return;

            isConnecting.value = true;
            
            try {
                createPeerConnection();
                await negotiate();
                console.log('连接成功建立');
            } catch (error) {
                console.error('连接失败:', error);
                isConnecting.value = false;
                
                // 用户友好的错误消息
                let errorMessage = '连接失败';
                if (error.name === 'NetworkError') {
                    errorMessage = '网络错误，请检查网络连接';
                } else if (error.message.includes('404')) {
                    errorMessage = '服务未找到，请确认LiveTalking服务正在运行';
                } else if (error.message.includes('500')) {
                    errorMessage = '服务器内部错误，请检查模型加载状态';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = '无法连接到服务器，请检查服务地址和端口';
                }
                
                alert(errorMessage + '\n\n技术详情: ' + error.message);
            }
        };

        const stopConnection = () => {
            if (pc) {
                pc.close();
                pc = null;
            }
            
            // 清理媒体流
            if (videoElement.value) {
                videoElement.value.srcObject = null;
            }
            if (audioElement.value) {
                audioElement.value.srcObject = null;
            }
            
            isConnected.value = false;
            isConnecting.value = false;
            isRecording.value = false;
            connectionState.value = 'closed';
        };

        const sendMessage = async () => {
            if (!canSendMessage.value) return;

            const message = currentMessage.value.trim();
            
            try {
                // 先检查数字人是否正在说话
                let shouldInterrupt = false;
                try {
                    const speakingResponse = await fetch('/is_speaking', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sessionid: sessionId.value })
                    });
                    const speakingData = await speakingResponse.json();
                    shouldInterrupt = speakingData.data;
                } catch (e) {
                    console.warn('无法检测说话状态:', e.message);
                    shouldInterrupt = true; // 默认打断
                }

                const response = await fetch('/human', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: message,
                        type: 'echo',
                        interrupt: shouldInterrupt,
                        sessionid: sessionId.value,
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    if (result.code === 0) {
                        messageCount.value++;
                        currentMessage.value = '';
                        console.log('消息发送成功:', message);
                    } else {
                        throw new Error(result.msg || '服务器返回错误');
                    }
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            } catch (error) {
                console.error('发送消息错误:', error);
                alert('发送消息失败: ' + error.message);
            }
        };

        const sendQuickMessage = (message) => {
            currentMessage.value = message;
            sendMessage();
        };

        const toggleRecording = async () => {
            if (!isConnected.value) return;

            try {
                const action = isRecording.value ? 'end_record' : 'start_record';
                
                const response = await fetch('/record', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: action,
                        sessionid: sessionId.value,
                    })
                });

                if (response.ok) {
                    isRecording.value = !isRecording.value;
                    if (!isRecording.value) {
                        hasRecording.value = true;
                    }
                    console.log(isRecording.value ? '开始录制' : '停止录制');
                } else {
                    throw new Error(`录制操作失败: ${response.status}`);
                }
            } catch (error) {
                console.error('录制操作错误:', error);
                alert('录制操作失败: ' + error.message);
            }
        };

        const downloadRecording = async () => {
            try {
                const response = await fetch('/record_lasted.mp4');
                if (!response.ok) {
                    throw new Error('下载失败');
                }

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `recording_${new Date().toISOString().slice(0, 19)}.mp4`;
                a.click();
                URL.revokeObjectURL(url);
            } catch (error) {
                console.error('下载录制文件错误:', error);
                alert('下载失败: ' + error.message);
            }
        };

        const toggleFullscreen = () => {
            isFullscreen.value = !isFullscreen.value;
            if (isFullscreen.value && videoElement.value) {
                videoElement.value.requestFullscreen?.();
            }
        };

        const toggleMute = () => {
            isMuted.value = !isMuted.value;
            if (audioElement.value) {
                audioElement.value.muted = isMuted.value;
            }
        };

        // 生命周期
        onMounted(() => {
            console.log('数字人组件已挂载');
            window.addEventListener('beforeunload', stopConnection);
        });

        onUnmounted(() => {
            stopConnection();
            window.removeEventListener('beforeunload', stopConnection);
        });

        // 监听器
        watch(isMuted, (newVal) => {
            if (audioElement.value) {
                audioElement.value.muted = newVal;
            }
        });

        return {
            // refs
            videoElement,
            audioElement,
            
            // 状态
            isConnecting,
            isConnected,
            isRecording,
            isMuted,
            isFullscreen,
            hasRecording,
            
            // 设置
            useStunServer,
            autoReconnect,
            showDebugInfo,
            
            // 消息
            currentMessage,
            messageCount,
            sessionId,
            quickMessages,
            
            // 计算属性
            connectionButtonText,
            recordButtonText,
            canSendMessage,
            connectionState,
            
            // 方法
            startConnection,
            stopConnection,
            sendMessage,
            sendQuickMessage,
            toggleRecording,
            downloadRecording,
            toggleFullscreen,
            toggleMute,
        };
    }
};