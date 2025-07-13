#convert bmp 2 jpg
import os
from PIL import Image
def convert_bmp_to_jpg(bmp_path, jpg_path):
    # Open the BMP image
    with Image.open(bmp_path) as img:
        # Convert to RGB (JPEG does not support transparency)
        rgb_img = img.convert('RGB')
        # Save as JPEG
        rgb_img.save(jpg_path, 'JPEG')
        
def convert_tiff_to_jpg(tiff_path, jpg_path):
    # Open the TIFF image
    with Image.open(tiff_path) as img:
        # Convert to RGB (JPEG does not support transparency)
        rgb_img = img.convert('RGB')
        # Save as JPEG
        rgb_img.save(jpg_path, 'JPEG')
if __name__ == "__main__":

    # bmp_directory = '/work/dev/osw-ai-server/datasets_v1/images/train'
    # jpg_directory = '/work/dev/osw-ai-server/datasets_v1/images/train'
    # if not os.path.exists(jpg_directory):
    #     os.makedirs(jpg_directory)
    # for filename in os.listdir(bmp_directory):
    #     if filename.endswith('.bmp'):
    #         bmp_file = os.path.join(bmp_directory, filename)
    #         jpg_file = os.path.join(jpg_directory, filename.replace('.bmp', '.jpg'))
    #         convert_bmp_to_jpg(bmp_file, jpg_file)
    #         print(f"Converted {bmp_file} to {jpg_file}")

    tiff_directory = '/work/dev/osw-ai-server/datasets/whu/r_test/test_label'
    jpg_directory = '/work/dev/osw-ai-server/datasets/whu/r_test/test_label_new'
    if not os.path.exists(jpg_directory):
        os.makedirs(jpg_directory)
    for filename in os.listdir(tiff_directory):
        if filename.endswith('.tiff') or filename.endswith('.tif') or filename.endswith('.TIF'):
            tiff_file = os.path.join(tiff_directory, filename)
            jpg_file = os.path.join(jpg_directory, filename.replace('.tiff', '.jpg').replace('.tif', '.jpg').replace('.TIF', '.jpg'))
            convert_tiff_to_jpg(tiff_file, jpg_file)
            print(f"Converted {tiff_file} to {jpg_file}")


# file save as

# # 设置你的目录路径
# directory = "/work/dev/osw-ai-server/datasets/labels/val"  # 替换为你的实际目录路径

# # 遍历目录中的所有文件
# for filename in os.listdir(directory):
#     # 检查文件名是否以 '_label.txt' 结尾
#     if filename.endswith("_label.txt"):
#         # 构建新文件名（去掉 '_label'）
#         new_filename = filename.replace("_label.txt", ".txt")
        
#         # 完整的旧文件路径和新文件路径
#         old_file = os.path.join(directory, filename)
#         new_file = os.path.join(directory, new_filename)
        
#         # 重命名文件
#         os.rename(old_file, new_file)
#         print(f"Renamed: {filename} -> {new_filename}")

# print("文件重命名完成！")