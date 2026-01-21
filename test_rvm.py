"""
RVM背景去除功能测试脚本
用于验证RVM集成是否正常工作
"""

import numpy as np
import cv2
import os
import time

def test_rvm_processor():
    """测试RVM处理器"""
    print("=" * 50)
    print("测试 RVM 处理器")
    print("=" * 50)
    
    from rvm_processor import RVMProcessor
    
    # 创建处理器
    processor = RVMProcessor(
        model_path="./models/rvm_resnet50.pth",
        downsample_ratio=0.25
    )
    
    # 预热
    processor.warm_up(640, 480)
    
    # 测试处理
    test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # 计时测试
    times = []
    for i in range(10):
        start = time.time()
        result = processor.process_frame(test_img)
        times.append(time.time() - start)
    
    avg_time = np.mean(times[1:])  # 排除第一次
    fps = 1.0 / avg_time
    
    print(f"输入尺寸: {test_img.shape}")
    print(f"输出尺寸: {result.shape}")
    print(f"输出格式: BGRA (4通道)")
    print(f"平均处理时间: {avg_time*1000:.2f} ms")
    print(f"处理帧率: {fps:.2f} FPS")
    print()
    
    return True


def test_rvm_with_real_image():
    """使用真实图像测试RVM"""
    print("=" * 50)
    print("测试 RVM 背景去除效果")
    print("=" * 50)
    
    from rvm_processor import RVMProcessor
    
    # 查找测试图像
    test_paths = [
        "./data/avatars/wav2lip256_avatar1/full_imgs/0.png",
        "./data/avatars/wav2lip256_avatar1/full_imgs/0.jpg",
    ]
    
    test_img = None
    for path in test_paths:
        if os.path.exists(path):
            test_img = cv2.imread(path)
            print(f"使用测试图像: {path}")
            break
    
    if test_img is None:
        print("未找到测试图像，跳过此测试")
        return True
    
    processor = RVMProcessor()
    result = processor.process_frame(test_img)
    
    # 保存结果
    output_path = "./debug_output/rvm_test_output.png"
    os.makedirs("./debug_output", exist_ok=True)
    cv2.imwrite(output_path, result)
    print(f"结果已保存到: {output_path}")
    
    # 也保存一个带绿色背景的版本用于对比
    green_bg = np.zeros_like(test_img)
    green_bg[:, :] = [0, 255, 0]  # 绿色背景
    
    alpha = result[:, :, 3:4] / 255.0
    foreground = result[:, :, :3]
    composite = (foreground + green_bg * (1 - alpha)).astype(np.uint8)
    
    composite_path = "./debug_output/rvm_test_composite.png"
    cv2.imwrite(composite_path, composite)
    print(f"合成结果(绿色背景)已保存到: {composite_path}")
    
    return True


def main():
    print("\n" + "=" * 60)
    print("   RVM 背景去除功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_rvm_processor()
        test_rvm_with_real_image()
        
        print("\n" + "=" * 60)
        print("   所有测试通过!")
        print("=" * 60)
        print("\n使用方法:")
        print("  启动时添加 --enable_rvm 参数即可启用背景去除")
        print("  例如: python app.py --model wav2lip --enable_rvm")
        print()
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
