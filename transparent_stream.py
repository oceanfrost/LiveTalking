"""
WebSocket 透明视频流服务
用于发送带 Alpha 通道的 RGBA 视频帧

低延迟设计：
- 使用二进制传输减少编解码开销
- RGB 用 JPEG 压缩（快速，质量好）
- Alpha 用 zlib 压缩（单通道压缩率高）
- 帧格式：[4字节width][4字节height][4字节rgb_len][rgb_data][alpha_data]
"""

import asyncio
import struct
import zlib
import cv2
import numpy as np
from aiohttp import web
import aiohttp
from logger import logger
import time

class TransparentVideoStream:
    """
    透明视频流处理器
    将 RGBA 帧通过 WebSocket 发送给前端
    
    数据格式（二进制）：
    - bytes 0-3: width (uint32, little-endian)
    - bytes 4-7: height (uint32, little-endian)
    - bytes 8-11: rgb_length (uint32, little-endian)
    - bytes 12 to 12+rgb_length: JPEG compressed RGB
    - remaining bytes: zlib compressed Alpha
    """
    
    def __init__(self, quality: int = 80):
        """
        Args:
            quality: JPEG 压缩质量 (1-100)，80是速度和质量的平衡点
        """
        self.quality = quality
        self.websockets = set()
        self._frame_count = 0
        self._last_log_time = time.time()
        
    async def register(self, ws):
        """注册 WebSocket 连接"""
        self.websockets.add(ws)
        logger.info(f"Transparent video client connected, total: {len(self.websockets)}")
        
    async def unregister(self, ws):
        """注销 WebSocket 连接"""
        self.websockets.discard(ws)
        logger.info(f"Transparent video client disconnected, total: {len(self.websockets)}")
    
    def encode_frame_binary(self, bgra_frame: np.ndarray) -> bytes:
        """
        编码 BGRA 帧为二进制格式（低延迟优化）
        
        Args:
            bgra_frame: BGRA 格式图像 (H, W, 4)
            
        Returns:
            bytes: 二进制数据包
        """
        if bgra_frame is None or len(bgra_frame.shape) != 3 or bgra_frame.shape[2] != 4:
            return None
            
        h, w = bgra_frame.shape[:2]
        
        # 分离 RGB 和 Alpha
        bgr = bgra_frame[:, :, :3]
        alpha = bgra_frame[:, :, 3]
        
        # RGB 用 JPEG 压缩（快速）
        _, rgb_encoded = cv2.imencode('.jpg', bgr, [
            cv2.IMWRITE_JPEG_QUALITY, self.quality,
            cv2.IMWRITE_JPEG_OPTIMIZE, 0  # 禁用优化以提高速度
        ])
        rgb_bytes = rgb_encoded.tobytes()
        
        # Alpha 用 zlib 快速压缩（level 1 最快）
        alpha_compressed = zlib.compress(alpha.tobytes(), level=1)
        
        # 打包：width(4) + height(4) + rgb_len(4) + rgb_data + alpha_data
        header = struct.pack('<III', w, h, len(rgb_bytes))
        
        return header + rgb_bytes + alpha_compressed
    
    async def broadcast_frame(self, bgra_frame: np.ndarray):
        """
        广播帧到所有连接的客户端
        
        Args:
            bgra_frame: BGRA 格式图像
        """
        if not self.websockets:
            return
            
        data = self.encode_frame_binary(bgra_frame)
        if data is None:
            return
        
        # 统计
        self._frame_count += 1
        now = time.time()
        if now - self._last_log_time >= 5.0:
            fps = self._frame_count / (now - self._last_log_time)
            logger.info(f"Transparent stream: {fps:.1f} FPS, {len(data)/1024:.1f}KB/frame, {len(self.websockets)} clients")
            self._frame_count = 0
            self._last_log_time = now
        
        # 广播二进制数据给所有客户端
        dead_sockets = set()
        for ws in self.websockets:
            try:
                await ws.send_bytes(data)
            except (ConnectionResetError, ConnectionAbortedError):
                # Windows 上客户端断开时的常见错误
                dead_sockets.add(ws)
            except Exception as e:
                logger.debug(f"Failed to send frame: {e}")
                dead_sockets.add(ws)
        
        # 清理断开的连接
        for ws in dead_sockets:
            try:
                await self.unregister(ws)
            except Exception:
                self.websockets.discard(ws)
    
    def broadcast_frame_sync(self, bgra_frame: np.ndarray, loop: asyncio.AbstractEventLoop):
        """
        同步版本的广播（用于从非异步线程调用）
        
        Args:
            bgra_frame: BGRA 格式图像
            loop: asyncio 事件循环
        """
        if not self.websockets:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast_frame(bgra_frame), loop)


# 全局实例
_transparent_stream = None

def get_transparent_stream() -> TransparentVideoStream:
    """获取透明视频流单例"""
    global _transparent_stream
    if _transparent_stream is None:
        _transparent_stream = TransparentVideoStream()
    return _transparent_stream


async def transparent_video_handler(request):
    """WebSocket 处理器"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    stream = get_transparent_stream()
    await stream.register(ws)
    
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                # 处理客户端消息（如果需要）
                pass
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f'WebSocket error: {ws.exception()}')
    except ConnectionResetError:
        # Windows 上客户端断开时的常见错误，可以安全忽略
        logger.debug("WebSocket client disconnected (ConnectionReset)")
    except Exception as e:
        logger.debug(f"WebSocket handler exception: {e}")
    finally:
        try:
            await stream.unregister(ws)
        except Exception:
            pass
    
    return ws
