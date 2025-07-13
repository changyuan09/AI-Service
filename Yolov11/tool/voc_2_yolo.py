import cv2
import numpy as np
from pathlib import Path

def binary_mask_to_yolo_label(input_png_path, output_label_path, min_area=100):
    """
    将二值PNG图像（0=背景，1=建筑物）转换为YOLO格式的label.txt
    
    参数:
        input_png_path (str): 输入PNG图像路径
        output_label_path (str): 输出的YOLO标签文件路径
        min_area (int): 最小多边形面积（过滤小噪点）
    """
    # 读取PNG图像
    img = cv2.imread(input_png_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"无法读取图像: {input_png_path}")
    
    # 二值化处理（确保只有0和255）
    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY)
    
    # 查找轮廓
    contours, _ = cv2.findContours(binary, cv2.THRESH_BINARY, cv2.CHAIN_APPROX_SIMPLE)
    
    # 获取图像尺寸（用于归一化）
    height, width = img.shape
    
    # 准备YOLO格式数据
    yolo_lines = []
    
    for contour in contours:
        # 过滤小面积区域
        if cv2.contourArea(contour) < min_area:
            continue
            
        # 简化多边形（减少点数）
        epsilon = 0.002 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 转换为归一化的YOLO格式
        polygon = []
        for point in approx:
            x, y = point[0]
            # 归一化到 [0,1]
            nx = x / width
            ny = y / height
            polygon.append(f"{nx:.6f}")
            polygon.append(f"{ny:.6f}")
        
        # YOLO格式: class_id x1 y1 x2 y2 ... xn yn
        yolo_line = f"0 {' '.join(polygon)}"  # 假设类别ID=0（建筑物）
        yolo_lines.append(yolo_line)
    
    # 写入标签文件
    with open(output_label_path, 'w') as f:
        f.write("\n".join(yolo_lines))
    
    print(f"成功生成YOLO标签: {output_label_path} (共{len(yolo_lines)}个建筑物)")

def process_directory(input_dir, output_dir=None, min_area=100):
    """
    遍历目录下的所有PNG图像并生成YOLO标签
    
    参数:
        input_dir (str): 包含PNG图像的输入目录
        output_dir (str): 输出目录（默认与输入目录相同）
        min_area (int): 最小多边形面积
    """
    input_dir = Path(input_dir)
    if output_dir is None:
        output_dir = input_dir
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 遍历所有PNG文件
    png_files = list(input_dir.glob("*.jpg"))
    print(f"找到 {len(png_files)} 个PNG文件")
    
    for png_path in png_files:
        # 生成对应的标签文件路径
        label_path = output_dir / f"{png_path.stem}.txt"
        
        try:
            binary_mask_to_yolo_label(str(png_path), str(label_path), min_area)
        except Exception as e:
            print(f"处理 {png_path.name} 时出错: {e}")
    
    print("所有PNG文件处理完成！")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="批量转换二值PNG为YOLO标签")
    parser.add_argument("input_dir", help="包含PNG图像的输入目录")
    parser.add_argument("--output_dir", help="输出目录（可选）")
    parser.add_argument("--min_area", type=int, default=1, help="最小多边形面积（默认100）")
    
    args = parser.parse_args()
    
    process_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        min_area=args.min_area
    )