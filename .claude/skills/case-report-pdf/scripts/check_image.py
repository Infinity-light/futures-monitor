#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片透明边距检查与裁剪工具
用于处理 Logo 等图片，去除多余的透明区域
"""

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误: 需要安装 Pillow: pip install pillow")
    sys.exit(1)


def check_transparency(image_path: Path) -> tuple:
    """
    检查图片的透明边距

    Returns:
        (原尺寸, 实际内容区域, 建议裁剪后尺寸)
    """
    img = Image.open(image_path)
    original_size = img.size

    if img.mode not in ('RGBA', 'P'):
        print(f"图片模式: {img.mode} (无透明通道)")
        return original_size, None, original_size

    # 获取实际内容区域（非透明部分的边界框）
    bbox = img.getbbox()
    if bbox is None:
        print("警告: 图片完全透明")
        return original_size, None, original_size

    # 计算裁剪后尺寸
    cropped_width = bbox[2] - bbox[0]
    cropped_height = bbox[3] - bbox[1]
    cropped_size = (cropped_width, cropped_height)

    return original_size, bbox, cropped_size


def crop_image(input_path: Path, output_path: Path = None) -> Path:
    """
    裁剪图片，去除透明边距

    Args:
        input_path: 输入图片路径
        output_path: 输出路径（默认在原文件名后加 -cropped）

    Returns:
        裁剪后的图片路径
    """
    img = Image.open(input_path)

    if img.mode not in ('RGBA', 'P'):
        print(f"图片无透明通道，无需裁剪")
        return input_path

    bbox = img.getbbox()
    if bbox is None:
        raise ValueError("图片完全透明")

    # 裁剪到内容区域
    cropped = img.crop(bbox)

    # 确定输出路径
    if output_path is None:
        stem = input_path.stem
        suffix = input_path.suffix
        output_path = input_path.parent / f"{stem}-cropped{suffix}"

    # 保存（保留原格式）
    if cropped.mode == 'RGBA' and output_path.suffix.lower() in ('.jpg', '.jpeg'):
        # JPG 不支持透明，转为 RGB
        background = Image.new('RGB', cropped.size, (255, 255, 255))
        background.paste(cropped, mask=cropped.split()[3])
        background.save(output_path, quality=95)
    else:
        cropped.save(output_path)

    return output_path


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python check_image.py <图片文件> [--crop]")
        print("示例:")
        print("  python check_image.py logo.png       # 仅检查")
        print("  python check_image.py logo.png --crop # 检查并裁剪")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    should_crop = '--crop' in sys.argv

    if not image_path.exists():
        print(f"错误: 文件不存在: {image_path}")
        sys.exit(1)

    print(f"检查图片: {image_path}")
    print(f"格式: {image_path.suffix}")

    try:
        original, bbox, cropped = check_transparency(image_path)
        print(f"\n原尺寸: {original[0]} x {original[1]}")

        if bbox:
            print(f"内容区域: ({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]})")
            print(f"裁剪后尺寸: {cropped[0]} x {cropped[1]}")

            # 计算节省的空间
            original_pixels = original[0] * original[1]
            cropped_pixels = cropped[0] * cropped[1]
            saved = (1 - cropped_pixels / original_pixels) * 100
            print(f"去除透明边距: {saved:.1f}%")

            if should_crop:
                output = crop_image(image_path)
                print(f"\n已裁剪保存: {output}")
            elif saved > 10:
                print(f"\n建议裁剪: python check_image.py {image_path.name} --crop")
        else:
            print("无需裁剪（无透明通道或图片完全透明）")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
