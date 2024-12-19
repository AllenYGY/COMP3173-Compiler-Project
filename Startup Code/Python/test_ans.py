import json
import sys
sys.setrecursionlimit(1999999999)

import json

def compare_json_files(file1: str, file2: str) -> None:
    """
    比较两个 JSON 文件的内容，输出差异。

    Args:
        file1 (str): 第一个 JSON 文件的路径。
        file2 (str): 第二个 JSON 文件的路径。
    """
    try:
        # 加载 JSON 数据
        with open(file1, 'r', encoding='utf-8') as f1:
            data1 = json.load(f1)
        with open(file2, 'r', encoding='utf-8') as f2:
            data2 = json.load(f2)

        # 比较 JSON 数据
        differences = compare_json(data1, data2)

        if differences:
            print("发现差异:")
            for diff in differences:
                print(f" - {diff}")
        else:
            print("Correct!")

    except FileNotFoundError as e:
        print(f"文件未找到: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")


def compare_json(data1, data2, path="root"):
    """
    递归比较两个 JSON 对象并报告差异。

    Args:
        data1 (any): 第一个 JSON 数据。
        data2 (any): 第二个 JSON 数据。
        path (str): 当前比较的 JSON 路径（用于显示差异位置）。

    Returns:
        list: 包含所有差异的列表。
    """
    differences = []

    if isinstance(data1, dict) and isinstance(data2, dict):
        # 比较字典
        for key in data1.keys() | data2.keys():
            new_path = f"{path} -> {key}"
            if key not in data1:
                differences.append(f"{new_path}: 第一个 JSON 缺少键")
            elif key not in data2:
                differences.append(f"{new_path}: 第二个 JSON 缺少键")
            else:
                differences.extend(compare_json(data1[key], data2[key], new_path))

    elif isinstance(data1, list) and isinstance(data2, list):
        # 比较列表
        if len(data1) != len(data2):
            differences.append(f"{path}: 列表长度不匹配 ({len(data1)} vs {len(data2)})")
        else:
            for index, (item1, item2) in enumerate(zip(data1, data2)):
                differences.extend(compare_json(item1, item2, f"{path}[{index}]"))

    else:
        if data1 != data2:
            differences.append(f"{path}: 值不匹配 ({data1} vs {data2})")

    return differences

if __name__ == '__main__':
    # Paths to JSON files
    file_path='/Users/allenygy/Desktop/WorkSpace/VScode-Workspace/Compiler/Startup Code/Python/'
    lexer_ouput = file_path+'lexer_out.json'
    lexer_ans = file_path+'lexer_ans.json'
    parser_output = file_path+'parser_out.json'
    parser_ans = file_path+'parser_ans.json'
    typing_output = file_path+'typing_out.json'
    typing_ans = file_path+'typing_ans.json'
    evaluate_output = file_path+'evaluation_out.json'
    evaluate_ans = file_path+'evaluation_ans.json'
    # Run comparison
    compare_json_files(lexer_ouput, lexer_ans)
    compare_json_files(parser_output, parser_ans)
    compare_json_files(typing_output,typing_ans)
    compare_json_files(evaluate_output,evaluate_ans)

