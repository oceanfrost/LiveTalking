"""
预设音频TTS - 加载预先生成的音频文件，让系统实时生成视频
只需要准备音频文件，不需要预先准备图像序列
"""

import os
import json
import soundfile as sf
import numpy as np
from ttsreal import BaseTTS
from logger import logger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from basereal import BaseReal


class PresetAudioTTS(BaseTTS):
    """
    预设音频TTS类
    使用预先生成的音频文件，系统会根据音频实时生成视频帧
    """
    
    def __init__(self, opt, parent: 'BaseReal'):
        super().__init__(opt, parent)
        
        # 加载预设音频配置
        self.preset_audios = {}
        self.load_preset_config()
        
    def load_preset_config(self):
        """加载预设音频配置文件"""
        config_path = "data/preset_audio_config.json"
        
        if not os.path.exists(config_path):
            logger.warning(f"预设音频配置文件不存在: {config_path}")
            logger.info("将创建示例配置文件...")
            self.create_sample_config(config_path)
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载所有预设音频到内存
            for preset in config:
                audio_id = preset['id']
                audio_path = preset['audio_path']
                text = preset.get('text', '')  # 可选的文本说明
                
                if os.path.exists(audio_path):
                    # 读取音频文件
                    audio_data, sample_rate = sf.read(audio_path, dtype='float32')
                    
                    # 转换为单声道
                    if audio_data.ndim > 1:
                        audio_data = audio_data[:, 0]
                    
                    # 重采样到16kHz（如果需要）
                    if sample_rate != self.sample_rate:
                        import resampy
                        audio_data = resampy.resample(
                            x=audio_data, 
                            sr_orig=sample_rate, 
                            sr_new=self.sample_rate
                        )
                    
                    self.preset_audios[audio_id] = {
                        'audio': audio_data,
                        'text': text,
                        'name': preset.get('name', f'预设{audio_id}')
                    }
                    logger.info(f"已加载预设音频 {audio_id}: {preset.get('name', '')}")
                else:
                    logger.warning(f"音频文件不存在: {audio_path}")
            
            logger.info(f"共加载 {len(self.preset_audios)} 个预设音频")
            
        except Exception as e:
            logger.error(f"加载预设音频配置失败: {e}")
    
    def create_sample_config(self, config_path):
        """创建示例配置文件"""
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        sample_config = [
            {
                "id": "welcome",
                "name": "欢迎语",
                "text": "您好！欢迎使用我们的服务",
                "audio_path": "data/preset_audio/welcome.wav"
            },
            {
                "id": "goodbye",
                "name": "再见",
                "text": "感谢您的使用，再见！",
                "audio_path": "data/preset_audio/goodbye.wav"
            }
        ]
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已创建示例配置文件: {config_path}")
        logger.info("请修改配置文件并添加您的预设音频")
    
    def txt_to_audio(self, msg: tuple[str, dict]):
        """
        处理文本消息，将预设ID转换为音频流
        msg格式: (preset_id, datainfo)
        其中preset_id可以是配置中的id字符串
        """
        text, datainfo = msg
        preset_id = text.strip()
        
        if preset_id not in self.preset_audios:
            logger.warning(f"未找到预设音频: {preset_id}")
            logger.info(f"可用的预设: {list(self.preset_audios.keys())}")
            return
        
        preset = self.preset_audios[preset_id]
        audio_data = preset['audio']
        
        logger.info(f"播放预设音频: {preset['name']} ({preset_id})")
        if preset['text']:
            logger.info(f"内容: {preset['text']}")
        
        # 将音频数据分块发送，系统会实时生成视频
        self.stream_audio_chunks(audio_data)
    
    def stream_audio_chunks(self, audio_data):
        """将音频数据分块流式发送"""
        total_samples = len(audio_data)
        idx = 0
        
        while idx < total_samples:
            # 每次发送一个chunk（20ms的音频）
            chunk_end = min(idx + self.chunk, total_samples)
            audio_chunk = audio_data[idx:chunk_end]
            
            # 如果最后一块不足chunk大小，用0填充
            if len(audio_chunk) < self.chunk:
                audio_chunk = np.pad(
                    audio_chunk, 
                    (0, self.chunk - len(audio_chunk)), 
                    'constant'
                )
            
            # 发送音频块到父类进行处理（会触发视频生成）
            self.parent.push_audio(audio_chunk)
            
            idx = chunk_end
        
        logger.info("预设音频播放完成")
    
    def list_presets(self):
        """列出所有可用的预设音频"""
        logger.info("=== 可用的预设音频 ===")
        for preset_id, preset in self.preset_audios.items():
            duration = len(preset['audio']) / self.sample_rate
            logger.info(f"  {preset_id:15s} - {preset['name']:20s} ({duration:.1f}秒)")
            if preset['text']:
                logger.info(f"      内容: {preset['text'][:50]}...")
