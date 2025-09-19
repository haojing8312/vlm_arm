#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试private_vlm_api方法的测试脚本
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils_vlm import private_vlm_api

def create_test_image():
    """
    创建一个测试图像，包含红色方块和钢笔
    """
    # 创建一个白色背景的图像
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # 绘制红色方块
    cv2.rectangle(img, (100, 200), (200, 300), (0, 0, 255), -1)  # 红色方块
    
    # 绘制钢笔（用矩形和线条模拟）
    cv2.rectangle(img, (500, 150), (600, 200), (0, 0, 0), -1)  # 钢笔主体
    cv2.rectangle(img, (600, 160), (650, 190), (0, 0, 0), -1)  # 钢笔笔尖
    
    # 添加中文标签
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)
    
    # 尝试加载中文字体，如果失败则使用默认字体
    try:
        font = ImageFont.truetype('asset/SimHei.ttf', 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((100, 180), "红色方块", font=font, fill=(255, 0, 0))
    draw.text((500, 120), "钢笔", font=font, fill=(0, 0, 0))
    
    img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    
    # 确保temp目录存在
    os.makedirs('temp', exist_ok=True)
    
    # 保存测试图像
    cv2.imwrite('temp/test_image.jpg', img_bgr)
    print("测试图像已创建：temp/test_image.jpg")
    
    return 'temp/test_image.jpg'

def test_private_vlm_api():
    """
    测试private_vlm_api方法
    """
    print("开始测试 private_vlm_api 方法...")
    
    try:
        # 创建测试图像
        test_img_path = create_test_image()
        
        # 测试定位任务 (vlm_option=0)
        print("\n=== 测试定位任务 ===")
        prompt = "帮我把红色方块放在钢笔上"
        print(f"测试提示词: {prompt}")
        print(f"测试图像路径: {test_img_path}")
        
        result = private_vlm_api(
            PROMPT=prompt,
            img_path=test_img_path,
            vlm_option=0
        )
        
        print("定位任务结果:")
        print(f"起始物体: {result.get('start', 'N/A')}")
        print(f"起始坐标: {result.get('start_xyxy', 'N/A')}")
        print(f"终止物体: {result.get('end', 'N/A')}")
        print(f"终止坐标: {result.get('end_xyxy', 'N/A')}")
        
        # 测试视觉问答任务 (vlm_option=1)
        print("\n=== 测试视觉问答任务 ===")
        vqa_prompt = "请描述图片中的物体"
        print(f"测试提示词: {vqa_prompt}")
        
        vqa_result = private_vlm_api(
            PROMPT=vqa_prompt,
            img_path=test_img_path,
            vlm_option=1
        )
        
        print("视觉问答结果:")
        print(vqa_result)
        
        print("\n✅ private_vlm_api 方法测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_connection():
    """
    测试API连接是否正常
    """
    print("测试API连接...")
    
    try:
        from API_KEY import PRIVATE_API_KEY, PRIVATE_BASE_URL, PRIVATE_VLM_MODEL
        
        print(f"API Key: {PRIVATE_API_KEY[:20]}...")
        print(f"Base URL: {PRIVATE_BASE_URL}")
        print(f"Model: {PRIVATE_VLM_MODEL}")
        
        # 检查必要的配置是否存在
        if not PRIVATE_API_KEY or PRIVATE_API_KEY == "your_api_key_here":
            print("❌ PRIVATE_API_KEY 未正确配置")
            return False
            
        if not PRIVATE_BASE_URL or PRIVATE_BASE_URL == "your_base_url_here":
            print("❌ PRIVATE_BASE_URL 未正确配置")
            return False
            
        if not PRIVATE_VLM_MODEL or PRIVATE_VLM_MODEL == "your_model_name_here":
            print("❌ PRIVATE_VLM_MODEL 未正确配置")
            return False
            
        print("✅ API配置检查通过")
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入API配置: {e}")
        return False
    except Exception as e:
        print(f"❌ API配置检查失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("private_vlm_api 测试脚本")
    print("=" * 50)
    
    # 首先检查API配置
    if not test_api_connection():
        print("请先配置正确的API参数")
        sys.exit(1)
    
    # 运行主要测试
    success = test_private_vlm_api()
    
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 测试失败，请检查错误信息")
        sys.exit(1)
