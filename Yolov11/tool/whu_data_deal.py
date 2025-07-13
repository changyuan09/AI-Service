import os
from PIL import Image
from tqdm import tqdm
import argparse

def resize_for_yolo(src_dir, dst_dir, target_size=640, padding=True, keep_original_format=True):
    """
    批量调整图像尺寸，保持原始像素精度
    
    参数:
        src_dir: 源目录
        dst_dir: 输出目录
        target_size: 目标尺寸
        padding: 是否使用填充保持比例
        keep_original_format: 是否保持原始文件格式
    """
    os.makedirs(dst_dir, exist_ok=True)
    
    img_files = [f for f in os.listdir(src_dir) 
               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff','.TIF'))]
    
    for filename in tqdm(img_files, desc="处理图像"):
        try:
            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(dst_dir, filename)
            
            with Image.open(src_path) as img:
                # 验证尺寸
                if img.size != (1024, 1024):
                    print(f"\n警告: {filename} 尺寸为 {img.size} 非1024x1024，已跳过")
                    continue
                
                # 处理透明通道
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (114, 114, 114))
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整尺寸
                if padding:
                    img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
                    new_img = Image.new("RGB", (target_size, target_size), (114, 114, 114))
                    offset = (
                        (target_size - img.size[0]) // 2,
                        (target_size - img.size[1]) // 2
                    )
                    new_img.paste(img, offset)
                else:
                    new_img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                
                # 保持原始格式或使用无损格式
                if keep_original_format:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ('.png', '.tif', '.tiff','.TIF'):
                        # 无损保存
                        new_img.save(dst_path, format=ext[1:].upper(), compress_level=0)
                    else:
                        # 高质量JPG
                        new_img.save(dst_path, quality=100, subsampling=0)
                else:
                    # 强制保存为PNG（完全无损）
                    new_dst_path = os.path.splitext(dst_path)[0] + '.png'
                    new_img.save(new_dst_path, format='PNG', compress_level=0)
                    
        except Exception as e:
            print(f"\n处理 {filename} 失败: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', type=str, required=True, help='源图像目录')
    parser.add_argument('--dst', type=str, required=True, help='输出目录')
    parser.add_argument('--no-padding', type=bool, help='禁用填充，直接拉伸图像')
    args = parser.parse_args()
    
    print(f"从 {args.src} 批量处理图像到 {args.dst}")
    print(f"模式: {'直接拉伸' if args.no_padding else '保持比例+填充'}")
    
    resize_for_yolo(
        src_dir=args.src,
        dst_dir=args.dst,
        padding=not args.no_padding
    )
    
    print("\n处理完成！")