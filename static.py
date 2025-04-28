import os
import re
import pdfplumber


def extract_amount(file_path):
    """从PDF文件中提取金额"""
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""

    # 尝试匹配精确的金额模式（带金额关键词）
    patterns = [
               # 高优先级：包含金额关键词的完整表述（支持中文单位）
        r'(?:合计|总计|金额|总金额)[\s:：]*[￥\$]?(\d+[\,\.]\d{1,2})[元]?\b',
        # 中优先级：金额行特征（如用户文档中的"共X笔行程，合计..."）
        r'共\d+笔行程[^,]*?合计(\d+\.\d{2})',
        # 低优先级：纯浮点数
        r'\b(\d+[\.\,]\d{2})\b'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            # 取最后一个匹配项（通常为最终金额）
            amount = matches[-1].replace(',', '')
            return f"{float(amount):.2f}"

    return None


def process_folder(folder_path,mode="path",month="未报销"):
    total_invoice = 0.0
    sum=0

    # 遍历所有PDF文件
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # 跳过非PDF文件
        if not filename.lower().endswith('.pdf') or not os.path.isfile(file_path):
            continue

        # 判断文件类型
        is_invoice = '发票' in filename
        is_itinerary = '单' in filename

        # 跳过无法分类的文件
        if not is_invoice and not is_itinerary:
            continue

        # 检查是否已包含金额
        if re.match(r'\d+\.\d{2}', filename):
            print(f'[跳过] 已处理文件: {filename}')

            # 如果是发票则累加已有金额
            if is_invoice:
                try:
                    sum += 1
                    amount = float(re.findall(r'\d+\.\d{2}', filename)[0])
                    total_invoice += amount
                except:
                    pass
            continue

        # 提取金额
        amount_str = extract_amount(file_path)
        if not amount_str:
            print(f'[错误] 无法提取金额: {filename}')
            continue

        # 格式校验
        try:
            amount = float(amount_str)
        except ValueError:
            print(f'[错误] 无效金额格式: {amount_str}')
            continue

        # 累加发票金额
        if is_invoice:
            sum+=1
            total_invoice += amount

        # 构建新文件名
        new_filename = f"{amount_str}_{filename}"
        new_path = os.path.join(folder_path, new_filename)

        # 重命名文件
        os.rename(file_path, new_path)
        print(f'[成功] 重命名: {filename} -> {new_filename}')

    # 重命名文件夹
    parent_dir = os.path.dirname(folder_path)
    new_folder_name = f"{month}发票总金额_{total_invoice:.2f}"
    new_folder_path = os.path.join(parent_dir, new_folder_name)
    print(f"共{sum}张发票")
    if mode=="path":
        with open("path.txt","w",encoding="utf-8")as f:
            f.write(new_folder_path)

    # 避免名称冲突
    if os.path.exists(new_folder_path):
        print(f"[警告] 文件夹名称已存在: {new_folder_name}")
    else:
        os.rename(folder_path, new_folder_path)
        print(f"[完成] 文件夹已重命名为: {new_folder_name}")

    # 验证金额配对
    missing_list = validate_pairing(new_folder_path)
    if missing_list:
        print("\n[警告] 以下金额存在未配对情况：")
        for item in missing_list:
            print(f"金额 {item['金额']} 元：缺少 {item['缺失数量']} 份{item['缺失类型']}")
    else:
        print("\n[验证通过] 所有发票与行程单金额已正确配对")

def validate_pairing(folder_path):
    """验证发票与行程单金额配对情况"""
    amount_records = {}

    # 遍历所有PDF文件收集金额信息
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if not filename.lower().endswith('.pdf'):
            continue

        # 从文件名中提取金额和类型
        match = re.match(r'^(\d+\.\d{2})_.*?(发票|单)', filename)
        if not match:
            continue

        amount = match.group(1)
        file_type = match.group(2)

        # 初始化金额记录结构
        if amount not in amount_records:
            amount_records[amount] = {'发票': 0, '单': 0}

        # 计数增加
        amount_records[amount][file_type] += 1

    # 检查配对情况
    missing_records = []
    for amount, counts in amount_records.items():
        if counts['发票'] != counts['单']:
            diff = counts['发票'] - counts['单']
            if diff > 0:
                missing_type = '单'
                missing_count = abs(diff)
            else:
                missing_type = '发票'
                missing_count = abs(diff)

            missing_records.append({
                '金额': amount,
                '缺失类型': missing_type,
                '缺失数量': missing_count
            })

    return missing_records

if __name__ == "__main__":
    with open("path.txt", "r",encoding="utf-8") as f:
        path=f.readline()
    if os.path.isdir(path):
        process_folder(path)
    else:
        print("错误：路径无效或不是文件夹")

