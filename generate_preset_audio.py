"""
预设音频批量生成工具
用于批量生成预设文本的音频文件，以便在LiveTalking中使用预设音频功能
"""

import asyncio
import edge_tts
import os
import json
from pathlib import Path


class PresetAudioGenerator:
    def __init__(self, voice="zh-CN-YunxiaNeural"):
        """
        初始化预设音频生成器
        
        Args:
            voice: EdgeTTS语音模型ID，默认为 zh-CN-YunxiaNeural
                  其他选项：
                  - zh-CN-XiaoxiaoNeural (女声，自然)
                  - zh-CN-YunyangNeural (男声，专业)
                  - zh-CN-XiaoyiNeural (女声，温柔)
        """
        self.voice = voice
        self.output_dir = Path("data/custom_audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_audio(self, text, name, audiotype):
        """
        生成单个预设音频
        
        Args:
            text: 要转换的文本内容
            name: 预设音频的名称（用于文件夹命名）
            audiotype: 预设音频的类型ID
        """
        # 创建目录
        preset_dir = self.output_dir / name
        preset_dir.mkdir(exist_ok=True)
        image_dir = preset_dir / "image"
        image_dir.mkdir(exist_ok=True)
        
        # 生成音频文件
        audio_path = preset_dir / "audio.wav"
        print(f"正在生成 {name} ({audiotype}): {text[:30]}...")
        
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(str(audio_path))
            print(f"✓ 已生成: {audio_path}")
            
            return {
                "audiotype": audiotype,
                "imgpath": f"data/custom_audio/{name}/image",
                "audiopath": f"data/custom_audio/{name}/audio.wav",
                "text": text,
                "name": name
            }
        except Exception as e:
            print(f"✗ 生成失败: {e}")
            return None
    
    async def generate_batch(self, presets):
        """
        批量生成预设音频
        
        Args:
            presets: 预设列表，格式为 [{"name": "...", "audiotype": N, "text": "..."}, ...]
        """
        tasks = []
        for preset in presets:
            task = self.generate_audio(
                preset["text"],
                preset["name"],
                preset["audiotype"]
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
    
    def generate_config(self, results, output_path="data/custom_config.json"):
        """
        生成 custom_config.json 配置文件
        
        Args:
            results: generate_batch 返回的结果列表
            output_path: 配置文件输出路径
        """
        config = []
        for result in results:
            config.append({
                "audiotype": result["audiotype"],
                "imgpath": result["imgpath"],
                "audiopath": result["audiopath"]
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=3)
        
        print(f"\n✓ 配置文件已生成: {output_path}")
        print(f"共 {len(config)} 个预设音频")
    
    def generate_mapping(self, results, output_path="data/preset_mapping.json"):
        """
        生成预设文本到audiotype的映射文件（用于前端快速查询）
        
        Args:
            results: generate_batch 返回的结果列表
            output_path: 映射文件输出路径
        """
        mapping = {}
        for result in results:
            # 添加名称映射
            mapping[result["name"]] = result["audiotype"]
            # 添加文本前缀映射（前10个字符）
            text_prefix = result["text"][:10]
            mapping[text_prefix] = result["audiotype"]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 映射文件已生成: {output_path}")


# ==================== 使用示例 ====================

async def main():
    """主函数：定义预设音频并生成"""
    
    # 创建生成器
    generator = PresetAudioGenerator(voice="zh-CN-YunxiaNeural")
    
    # 定义预设音频列表
    presets = [
        {
            "name": "idle",
            "audiotype": 1,
            "text": "..."  # 静默状态可以用很短的无声音频
        },
        {
            "name": "welcome",
            "audiotype": 2,
            "text": "您好！欢迎使用我们的服务，我是您的智能助手小云，很高兴为您服务。请问有什么可以帮您的吗？"
        },
        {
            "name": "greeting_morning",
            "audiotype": 3,
            "text": "早上好！新的一天开始了，希望您今天心情愉快，工作顺利！"
        },
        {
            "name": "greeting_afternoon",
            "audiotype": 4,
            "text": "下午好！辛苦了，要不要休息一下，喝杯茶放松一下呢？"
        },
        {
            "name": "greeting_evening",
            "audiotype": 5,
            "text": "晚上好！一天的工作辛苦了，祝您有个愉快的夜晚！"
        },
        {
            "name": "faq_hours",
            "audiotype": 11,
            "text": "我们的营业时间是每天上午9点到晚上6点，周末和节假日正常营业。如有特殊情况会提前通知，感谢您的关注！"
        },
        {
            "name": "faq_location",
            "audiotype": 12,
            "text": "我们的地址在北京市海淀区中关村大街123号科技大厦8层，地铁4号线中关村站A口出来步行5分钟即可到达。"
        },
        {
            "name": "faq_contact",
            "audiotype": 13,
            "text": "您可以通过以下方式联系我们：客服电话400-123-4567，工作时间随时为您服务；或者添加我们的官方微信号：service123，我们会尽快回复您。"
        },
        {
            "name": "faq_price",
            "audiotype": 14,
            "text": "关于价格，我们提供多种套餐选择：基础版每月299元，专业版每月599元，企业版每月999元。首次购买可享受8折优惠哦！"
        },
        {
            "name": "faq_features",
            "audiotype": 15,
            "text": "我们的主要功能包括智能对话、语音识别、数字人驱动、多语言支持等。可以应用于客服、教育、直播等多个场景，满足您的不同需求。"
        },
        {
            "name": "goodbye",
            "audiotype": 20,
            "text": "感谢您的咨询！如果还有其他问题，随时欢迎回来找我。祝您生活愉快，再见！"
        },
        {
            "name": "transfer_human",
            "audiotype": 21,
            "text": "好的，我这就为您转接人工客服，请稍等片刻，马上就有专业客服人员为您服务。"
        },
        {
            "name": "not_understand",
            "audiotype": 22,
            "text": "抱歉，我没有完全理解您的问题。您可以换个方式说明，或者我为您转接人工客服，会有专人为您详细解答。"
        },
    ]
    
    # 批量生成音频
    print("=" * 60)
    print("开始批量生成预设音频...")
    print("=" * 60)
    results = await generator.generate_batch(presets)
    
    # 生成配置文件
    print("\n" + "=" * 60)
    print("生成配置文件...")
    print("=" * 60)
    generator.generate_config(results)
    generator.generate_mapping(results)
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print("\n后续步骤：")
    print("1. 使用LiveTalking生成对应的图像序列（或使用现有的图像序列）")
    print("2. 将图像序列放置到对应的 data/custom_audio/{name}/image/ 目录")
    print("3. 重启LiveTalking服务以加载新配置")
    print("4. 通过 /set_audiotype API 调用播放预设音频")
    print("\n预设音频列表：")
    for result in results:
        print(f"  - {result['name']:20s} (audiotype={result['audiotype']:2d}): {result['text'][:40]}...")


# ==================== 自定义预设 ====================

async def custom_presets():
    """
    自定义预设音频生成示例
    您可以根据自己的需求修改这个函数
    """
    generator = PresetAudioGenerator(voice="zh-CN-YunxiaNeural")
    
    # 您的自定义预设
    my_presets = [
        {
            "name": "my_custom_1",
            "audiotype": 100,
            "text": "这是我的自定义预设音频1"
        },
        {
            "name": "my_custom_2",
            "audiotype": 101,
            "text": "这是我的自定义预设音频2"
        },
    ]
    
    results = await generator.generate_batch(my_presets)
    generator.generate_config(results, "data/my_custom_config.json")
    generator.generate_mapping(results, "data/my_preset_mapping.json")


# ==================== 可用语音列表 ====================

AVAILABLE_VOICES = {
    # 中文女声
    "zh-CN-XiaoxiaoNeural": "晓晓 - 女声，温暖亲切",
    "zh-CN-XiaoyiNeural": "晓伊 - 女声，甜美可爱", 
    "zh-CN-YunxiaNeural": "云夏 - 女声，清新自然",
    "zh-CN-YunxiNeural": "云希 - 女声，知性优雅",
    
    # 中文男声
    "zh-CN-YunyangNeural": "云扬 - 男声，专业稳重",
    "zh-CN-YunjianNeural": "云健 - 男声，年轻活力",
    "zh-CN-YunxiaNeural-Male": "云夏男声 - 男声，温和亲切",
    
    # 多语言
    "zh-CN-XiaoxiaoMultilingualNeural": "晓晓多语言 - 支持多语言",
}


def list_voices():
    """列出可用的语音选项"""
    print("可用的EdgeTTS语音选项：")
    print("=" * 60)
    for voice_id, description in AVAILABLE_VOICES.items():
        print(f"{voice_id:40s} {description}")
    print("=" * 60)
    print("\n使用方法：")
    print('generator = PresetAudioGenerator(voice="zh-CN-YunxiaNeural")')


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list-voices":
            list_voices()
        elif sys.argv[1] == "custom":
            asyncio.run(custom_presets())
        else:
            print("用法:")
            print("  python generate_preset_audio.py          # 生成默认预设音频")
            print("  python generate_preset_audio.py custom   # 生成自定义预设音频")
            print("  python generate_preset_audio.py list-voices  # 列出可用语音")
    else:
        asyncio.run(main())
