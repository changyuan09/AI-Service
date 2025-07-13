import os
import shutil
import schedule
import time


def delete_files_in_folder(folder_path):
    try:
        # 检查文件夹是否存在
        if not os.path.exists(folder_path):
            print(f"文件夹 {folder_path} 不存在")
            return

        # 遍历文件夹中的所有文件和子文件夹
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # 删除文件或符号链接
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # 删除子文件夹及其内容
                print(f"已删除: {file_path}")
            except Exception as e:
                print(f"删除 {file_path} 时出错: {e}")

        print(f"已完成清理文件夹: {folder_path}")
    except Exception as e:
        print(f"清理文件夹时发生错误: {e}")


def job(folder_path):
    print(f"开始执行定时清理任务... ({time.ctime()})")
    delete_files_in_folder(folder_path)
    print(f"定时清理任务完成... ({time.ctime()})")


def main(folder_path, interval_hours=1):
    print(f"启动定时清理服务，每隔 {interval_hours} 小时清理文件夹: {folder_path}")

    # 设置定时任务
    schedule.every(interval_hours).hours.do(job, folder_path=folder_path)

    # 立即执行一次
    job(folder_path)

    # 循环执行定时任务
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # 设置要清理的文件夹路径
    folder_to_clean = "/work/dev/osw-ai-server/output"  # 替换为你要清理的文件夹路径

    # 设置清理间隔（小时）
    clean_interval_hours = 1

    # 启动服务
    main(folder_to_clean, clean_interval_hours)
