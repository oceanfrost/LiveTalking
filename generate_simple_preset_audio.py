"""
简化版预设音频批量生成工具
只生成音频文件，视频由系统实时生成
"""

import asyncio
import edge_tts
import json
import os
from pathlib import Path

# 定义要生成的预设音频
PRESETS = [
    {
        "id": "welcome",
        "name": "欢迎语",
        "text": "您好！欢迎使用我们的服务，我是您的智能助手，有什么可以帮您的吗？"
    },
    {
        "id": "morning",
        "name": "早安问候",
        "text": "早上好！新的一天开始了，希望您今天心情愉快，工作顺利！"
    },
    {
        "id": "afternoon",
        "name": "下午问候",
        "text": "下午好！辛苦了，要不要休息一下，喝杯茶放松一下呢？"
    },
    {
        "id": "evening",
        "name": "晚上问候",
        "text": "晚上好！一天的工作辛苦了，祝您有个愉快的夜晚！"
    },
    {
        "id": "hours",
        "name": "营业时间",
        "text": "我们的营业时间是每天上午9点到晚上6点，周末和节假日正常营业。如有特殊情况会提前通知，感谢您的关注！"
    },
    {
        "id": "location",
        "name": "地址位置",
        "text": "我们的地址在北京市海淀区中关村大街123号科技大厦8层，地铁4号线中关村站A口出来步行5分钟即可到达。"
    },
    {
        "id": "contact",
        "name": "联系方式",
        "text": "您可以通过以下方式联系我们：客服电话400-123-4567，工作时间随时为您服务；或者添加我们的官方微信号service123。"
    },
    {
        "id": "price",
        "name": "价格套餐",
        "text": "关于价格，我们提供多种套餐选择：基础版每月299元，专业版每月599元，企业版每月999元。首次购买可享受8折优惠哦！"
    },
    {
        "id": "features",
        "name": "功能介绍",
        "text": "我们的主要功能包括智能对话、语音识别、数字人驱动、多语言支持等，可以应用于客服、教育、直播等多个场景。"
    },
    {
        "id": "goodbye",
        "name": "再见",
        "text": "感谢您的咨询！如果还有其他问题，随时欢迎回来找我。祝您生活愉快，再见！"
    },
    {
        "id": "transfer",
        "name": "转人工",
        "text": "好的，我这就为您转接人工客服，请稍等片刻，马上就有专业客服人员为您服务。"
    },
    {
        "id": "retry",
        "name": "重复说明",
        "text": "抱歉，我没有完全理解您的问题。您可以换个方式说明，或者我为您转接人工客服详细解答。"
    },
]

# EdgeTTS语音选项
VOICE = "zh-CN-YunxiaNeural"  # 默认语音

# 可用语音列表
AVAILABLE_VOICES = {
    "zh-CN-XiaoxiaoNeural": "晓晓 - 女声，温暖亲切",
    "zh-CN-XiaoyiNeural": "晓伊 - 女声，甜美可爱",
    "zh-CN-YunxiaNeural": "云夏 - 女声，清新自然",
    "zh-CN-YunyangNeural": "云扬 - 男声，专业稳重",
    "zh-CN-YunjianNeural": "云健 - 男声，年轻活力",
}

OUTPUT_DIR = "data/preset_audio"

async def generate_one(preset, voice=VOICE):
    """生成单个音频文件"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    audio_path = os.path.join(OUTPUT_DIR, f"{preset['id']}.wav")
    print(f"正在生成: {preset['name']:15s} ({preset['id']:12s})  {preset['text'][:30]}...")
    
    try:
        communicate = edge_tts.Communicate(preset['text'], voice)
        await communicate.save(audio_path)
        print(f"  ✓ 已保存: {audio_path}")
        
        # 返回配置项
        return {
            "id": preset['id'],
            "name": preset['name'],
            "text": preset['text'],
            "audio_path": audio_path
        }
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        return None

async def main(voice=VOICE, custom_presets=None):
    """主函数"""
    print("=" * 70)
    print("预设音频批量生成工具（简化版 - 只生成音频，视频实时生成）")
    print("=" * 70)
    print(f"使用语音: {voice}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 70)
    
    presets_to_generate = custom_presets if custom_presets else PRESETS
    
    # 并发生成所有音频
    print(f"\n开始生成 {len(presets_to_generate)} 个预设音频...\n")
    tasks = [generate_one(preset, voice) for preset in presets_to_generate]
    results = await asyncio.gather(*tasks)
    
    # 过滤掉失败的
    config = [r for r in results if r is not None]
    
    # 生成配置文件
    config_path = "data/preset_audio_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print(f"✅ 完成！")
    print("=" * 70)
    print(f"  成功: {len(config)}/{len(presets_to_generate)} 个音频文件")
    print(f"  配置: {config_path}")
    print(f"  音频: {OUTPUT_DIR}/")
    print("=" * 70)
    
    print("\n📋 生成的预设列表：")
    for item in config:
        duration_estimate = len(item['text']) * 0.15  # 粗略估算时长
        print(f"  {item['id']:12s} - {item['name']:15s} (~{duration_estimate:.1f}秒)")
    
    print("\n🚀 下一步：")
    print("  1. 启动服务（需要修改代码支持preset TTS）:")
    print("     python app.py --tts preset --model wav2lip --avatar_id wav2lip256_avatar1")
    print("")
    print("  2. 测试预设音频:")
    print("     浏览器访问: http://localhost:8010/preset-simple-test.html")
    print("")
    print("  3. API调用示例:")
    print("     POST /human")
    print("     {\"sessionid\": 0, \"type\": \"echo\", \"text\": \"welcome\"}")
    print("")
    print("💡 提示：")
    print("  - 只需要音频文件，视频会实时生成")
    print("  - 修改 PRESETS 列表可自定义预设")
    print("  - 修改 VOICE 变量可更换语音")
    print("=" * 70)

def list_voices():
    """列出可用语音"""
    print("=" * 70)
    print("可用的EdgeTTS语音选项")
    print("=" * 70)
    for voice_id, description in AVAILABLE_VOICES.items():
        print(f"  {voice_id:35s} {description}")
    print("=" * 70)
    print("\n使用方法:")
    print("  python generate_simple_preset_audio.py --voice zh-CN-YunyangNeural")

if __name__ == "__main__":
    import sys
    
    voice = VOICE
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list-voices":
            list_voices()
            sys.exit(0)
        elif sys.argv[1] == "--voice" and len(sys.argv) > 2:
            voice = sys.argv[2]
            if voice not in AVAILABLE_VOICES:
                print(f"警告: {voice} 不在推荐列表中")
                print("运行 'python generate_simple_preset_audio.py --list-voices' 查看可用语音")
    
    asyncio.run(main(voice=voice))
