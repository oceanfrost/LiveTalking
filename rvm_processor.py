###############################################################################
#  RVM (Robust Video Matting) Background Removal Processor
#  用于将视频帧的背景转为透明，只保留人像
#  基于官方RVM实现: https://github.com/PeterL1n/RobustVideoMatting
###############################################################################

import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional
from logger import logger

device = "cuda" if torch.cuda.is_available() else ("mps" if (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()) else "cpu")


class RVMProcessor:
    """
    RVM处理器类，用于视频帧的背景去除
    
    使用方法:
        processor = RVMProcessor(model_path="./models/rvm_resnet50.pth")
        rgba_frame = processor.process_frame(bgr_frame)  # 返回BGRA格式的帧
    """
    
    def __init__(self, model_path: str = "./models/rvm_resnet50.pth", downsample_ratio: float = 0.25):
        """
        初始化RVM处理器
        
        Args:
            model_path: RVM模型路径
            downsample_ratio: 下采样比例，用于加速处理。0.25表示缩小4倍处理后再放大
        """
        self.model_path = model_path
        self.downsample_ratio = downsample_ratio
        self.model = None
        self.device = device
        
        # 循环状态（用于时序一致性）
        self.rec = [None] * 4  # r1, r2, r3, r4
        
        self._load_model()
        
    def _load_model(self):
        """加载RVM模型"""
        logger.info(f"Loading RVM model from TorchHub (using local weights if available)")
        
        try:
            # 使用官方TorchHub加载模型架构和权重
            self.model = torch.hub.load(
                'PeterL1n/RobustVideoMatting', 
                'resnet50',
                trust_repo=True
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            logger.info("RVM model loaded successfully from TorchHub")
        except Exception as e:
            logger.error(f"Failed to load RVM model: {e}")
            raise RuntimeError(f"Cannot load RVM model: {e}")
    
    def reset_states(self):
        """重置循环状态（在场景切换时调用）"""
        self.rec = [None] * 4
        
    @torch.no_grad()
    def process_frame(self, frame: np.ndarray, background_color: tuple = (0, 255, 0)) -> np.ndarray:
        """
        处理单帧图像，去除背景，返回带指定背景色的BGR图像
        
        Args:
            frame: BGR格式的图像 (H, W, 3)，值范围0-255
            background_color: 背景颜色 BGR格式，默认绿色 (0, 255, 0)
            
        Returns:
            BGR格式图像 (H, W, 3)，背景替换为指定颜色
        """
        if frame is None:
            return None
            
        # 确保是uint8类型
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
            
        H, W = frame.shape[:2]
        
        # BGR -> RGB -> Tensor
        rgb = frame[:, :, ::-1].copy()  # BGR to RGB
        src = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        src = src.to(self.device)
        
        # 运行模型
        fgr, pha, *self.rec = self.model(src, *self.rec, self.downsample_ratio)
        
        # 获取alpha
        pha = pha[0, 0].cpu().numpy()  # (H, W)
        
        # 创建背景
        background = np.zeros((H, W, 3), dtype=np.uint8)
        background[:, :] = background_color  # BGR格式
        
        # Alpha混合: result = foreground * alpha + background * (1 - alpha)
        alpha_3ch = np.stack([pha] * 3, axis=-1)
        result = (frame * alpha_3ch + background * (1 - alpha_3ch)).astype(np.uint8)
        
        return result
    
    @torch.no_grad()
    def process_frame_rgba(self, frame: np.ndarray) -> np.ndarray:
        """
        处理单帧图像，返回BGRA格式（带透明通道）
        
        Args:
            frame: BGR格式的图像 (H, W, 3)，值范围0-255
            
        Returns:
            BGRA格式图像 (H, W, 4)，值范围0-255
            注意：返回非预乘alpha格式，RGB保持原始颜色
        """
        if frame is None:
            return None
            
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
            
        H, W = frame.shape[:2]
        
        rgb = frame[:, :, ::-1].copy()
        src = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        src = src.to(self.device)
        
        fgr, pha, *self.rec = self.model(src, *self.rec, self.downsample_ratio)
        pha = pha[0, 0].cpu().numpy()
        
        # 创建BGRA图像（非预乘alpha，保持原始RGB颜色）
        bgra = np.zeros((H, W, 4), dtype=np.uint8)
        bgra[:, :, :3] = frame  # 保持原始BGR颜色
        bgra[:, :, 3] = (pha * 255).astype(np.uint8)  # Alpha通道
        
        return bgra
    
    @torch.no_grad()
    def process_frame_both(self, frame: np.ndarray, background_color: tuple = (0, 255, 0)) -> tuple:
        """
        处理单帧图像，同时返回BGRA和带背景的BGR（共享一次推理）
        
        Args:
            frame: BGR格式的图像 (H, W, 3)，值范围0-255
            background_color: 背景颜色 BGR格式，默认绿色 (0, 255, 0)
            
        Returns:
            tuple: (bgra, bgr_with_bg)
                - bgra: BGRA格式图像 (H, W, 4)
                - bgr_with_bg: BGR格式图像 (H, W, 3)，背景替换为指定颜色
        """
        if frame is None:
            return None, None
            
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
            
        H, W = frame.shape[:2]
        
        # 转换为tensor并推理
        rgb = frame[:, :, ::-1].copy()
        src = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        src = src.to(self.device)
        
        fgr, pha, *self.rec = self.model(src, *self.rec, self.downsample_ratio)
        pha = pha[0, 0].cpu().numpy()
        
        # 创建BGRA图像（非预乘alpha）
        bgra = np.zeros((H, W, 4), dtype=np.uint8)
        bgra[:, :, :3] = frame
        bgra[:, :, 3] = (pha * 255).astype(np.uint8)
        
        # 创建带背景的BGR图像
        background = np.zeros((H, W, 3), dtype=np.uint8)
        background[:, :] = background_color
        alpha_3ch = np.stack([pha] * 3, axis=-1)
        bgr_with_bg = (frame * alpha_3ch + background * (1 - alpha_3ch)).astype(np.uint8)
        
        return bgra, bgr_with_bg
    
    @torch.no_grad()
    def get_alpha(self, frame: np.ndarray) -> np.ndarray:
        """
        只获取alpha通道
        
        Args:
            frame: BGR格式的图像 (H, W, 3)
            
        Returns:
            alpha通道 (H, W)，值范围0-1
        """
        if frame is None:
            return None
            
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
            
        H, W = frame.shape[:2]
        
        rgb = frame[:, :, ::-1].copy()
        src = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        src = src.to(self.device)
        
        fgr, pha, *self.rec = self.model(src, *self.rec, self.downsample_ratio)
        
        return pha[0, 0].cpu().numpy()
    
    def warm_up(self, width: int = 512, height: int = 512):
        """预热模型"""
        logger.info("Warming up RVM model...")
        dummy_frame = np.zeros((height, width, 3), dtype=np.uint8)
        self.process_frame(dummy_frame)
        self.reset_states()  # 重置状态
        logger.info("RVM model warmed up")


# 全局单例（可选）
_rvm_processor = None

def get_rvm_processor(model_path: str = "./models/rvm_resnet50.pth", downsample_ratio: float = 0.25) -> RVMProcessor:
    """获取RVM处理器单例"""
    global _rvm_processor
    if _rvm_processor is None:
        _rvm_processor = RVMProcessor(model_path, downsample_ratio)
    return _rvm_processor
