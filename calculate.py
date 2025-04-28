import os
import shutil
from collections import defaultdict
import re
from static import *
def select_files(folder_path, target=500):
    """贪心算法选择最接近目标的文件组合"""
    # 1. 文件分类与验证
    file_dict = defaultdict(lambda: {'invoice': [], 'itinerary': []})

    for filename in os.listdir(folder_path):
        # 提取金额和类型
        match = re.match(r"(\d+\.\d{2})_.*?(发票|单)", filename)
        if match:
            amount = float(match.group(1))
            file_type = match.group(2)
            if file_type =="发票":
                file_dict[amount]['invoice'].append(filename)
            else:
                file_dict[amount]['itinerary'].append(filename)

    # 2. 生成有效组合
    valid_pairs = {}
    for amount, files in file_dict.items():
        pair_count = min(len(files['invoice']), len(files['itinerary']))
        if pair_count > 0:
            valid_pairs[amount] = {
                'invoices': files['invoice'][:pair_count],
                'itineraries': files['itinerary'][:pair_count]
            }

    # 3. 贪心算法选择
    selected = []
    current_sum = 0
    tolerance = 5  # 允许超出阈值

    # 按金额降序排列
    sorted_amounts = sorted(valid_pairs.keys(), reverse=True)

    for amount in sorted_amounts:
        while len(valid_pairs[amount]['invoices']) > 0:
            if current_sum + amount * 2 <= target + tolerance:
                # 选取文件对
                inv = valid_pairs[amount]['invoices'].pop()
                iti = valid_pairs[amount]['itineraries'].pop()

                selected.extend([inv, iti])
                current_sum += amount

                if current_sum >= target:
                    return selected, current_sum
            else:
                break

    return selected, current_sum


def move_files(src_folder, dest_folder, file_list):
    """移动选中文件到新目录"""
    os.makedirs(dest_folder, exist_ok=True)

    for filename in file_list:
        src = os.path.join(src_folder, filename)
        dest = os.path.join(dest_folder, filename)

        # 处理文件名冲突
        if os.path.exists(dest):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest):
                new_name = f"{base}_{counter}{ext}"
                dest = os.path.join(dest_folder, new_name)
                counter += 1

        shutil.move(src, dest)


# 使用示例
if __name__ == "__main__":
    with open("path.txt", "r") as f:
        source_folder= f.readline()
    month=input("请输入月份：")
    target_folder = rf"C:\Users\22205\Desktop\postgraduate\money\{month}"
    targe=int(input("请输入目标金额："))
    selected_files, total = select_files(source_folder,targe)
    print(f"选中文件：{len(selected_files) // 2}对，总金额：{total:.2f}")

    move_files(source_folder, target_folder, selected_files)
    process_folder(target_folder,"no_path",month)