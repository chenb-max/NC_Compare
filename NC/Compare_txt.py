#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# 2025/8/15 22:44
import difflib
import os
import logging
import time
from datetime import datetime


class BatchFileComparator:
    def __init__(self, parent_dir, file1_name="file1.txt", file2_name="file2.txt"):
        self.parent_dir = parent_dir
        self.file1_name = file1_name
        self.file2_name = file2_name
        self.logger = None
        self.log_filename = None
        self._setup_logger()

    def _setup_logger(self):
        """配置日志系统，将日志放在上级files目录"""
        # 获取上级files目录路径
        files_dir = os.path.dirname(self.parent_dir)

        # 创建日志目录（在files目录下）
        log_dir = os.path.join(files_dir, "txt_file_diff_logs")
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"{log_dir}/batch_file_diff_{timestamp}.log"

        self.logger = logging.getLogger("BatchFileDiff")
        self.logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        file_handler = logging.FileHandler(self.log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        self.logger.info("=" * 100)
        self.logger.info(f"多文件夹文件批量比较工具启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"父目录: {os.path.abspath(self.parent_dir)}")
        self.logger.info("=" * 100)

    def _find_file_pairs(self):
        """Find all file pairs in subdirectories"""
        file_pairs = []

        for folder in os.listdir(self.parent_dir):
            folder_path = os.path.join(self.parent_dir, folder)

            if not os.path.isdir(folder_path):
                continue

            file1_path = os.path.join(folder_path, self.file1_name)
            file2_path = os.path.join(folder_path, self.file2_name)

            if os.path.exists(file1_path) and os.path.exists(file2_path):
                file_pairs.append({
                    'folder': folder,
                    'folder_path': folder_path,
                    'file1': file1_path,
                    'file2': file2_path
                })

        return file_pairs

    def _compare_files(self, file1, file2):
        """Compare two files"""
        try:
            with open(file1, 'r', encoding='utf-8') as f1, \
                    open(file2, 'r', encoding='utf-8') as f2:
                lines1 = f1.readlines()
                lines2 = f2.readlines()
        except UnicodeDecodeError:
            with open(file1, 'rb') as f1, \
                    open(file2, 'rb') as f2:
                lines1 = f1.readlines()
                lines2 = f2.readlines()

        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))

        return diff, len(lines1), len(lines2)

    def _analyze_differences(self, diff):
        """Analyze and categorize differences"""
        differences = []
        line_num = 0

        for line in diff:
            if line.startswith('  '):
                line_num += 1
                continue

            prefix = line[0]
            content = line[2:]

            if prefix == '-':
                differences.append({
                    'type': '删除',
                    'line': line_num + 1,
                    'content': content.rstrip('\n')
                })
            elif prefix == '+':
                differences.append({
                    'type': '添加',
                    'line': line_num + 1,
                    'content': content.rstrip('\n')
                })
                line_num += 1
            elif prefix == '?':
                if differences and differences[-1]['type'] == '删除':
                    differences[-1]['type'] = '变化'
                    differences.append({
                        'type': '变化后内容',
                        'line': '',
                        'content': content.rstrip('\n')
                    })

        return differences

    def _compare_file_pair(self, pair):
        """Compare a single file pair"""
        folder = pair['folder']
        file1 = pair['file1']
        file2 = pair['file2']

        self.logger.info(f"\n{'=' * 100}")
        self.logger.info(f"📁 正在处理文件夹: {folder}")
        self.logger.info(f"🔍 文件1: {os.path.basename(file1)}")
        self.logger.info(f"🔍 文件2: {os.path.basename(file2)}")
        self.logger.info(f"📂 路径: {os.path.dirname(file1)}")
        self.logger.info("-" * 100)

        try:
            diff_result, file1_lines, file2_lines = self._compare_files(file1, file2)
            self.logger.info(f"📝 文件1行数: {file1_lines}")
            self.logger.info(f"📝 文件2行数: {file2_lines}")

            differences = self._analyze_differences(diff_result)

            if not differences:
                self.logger.info("✅ 比较结果: 两个文件内容完全相同")
                return True, 0
            else:
                self.logger.info(f"❌ 比较结果: 发现 {len(differences)} 处差异")
                self.logger.info("-" * 100)

                for i, diff in enumerate(differences, 1):
                    if diff['type'] == '变化后内容':
                        self.logger.info(f"    | 改为: {diff['content']}")
                        self.logger.info("-" * 100)
                    else:
                        self.logger.info(f"差异 #{i}: {diff['type']} [行号: {diff['line']}]")
                        self.logger.info(f"    | 内容: {diff['content']}")
                        self.logger.info("-" * 100)

                return False, len(differences)

        except Exception as e:
            self.logger.error(f"处理文件夹 '{folder}' 时发生错误: {str(e)}")
            return False, -1

    def run(self):
        """执行批量比较"""
        start_time = time.time()
        file_pairs = self._find_file_pairs()

        if not file_pairs:
            self.logger.error(f"在目录 {self.parent_dir} 中未找到有效的文件对")
            return None

        self.logger.info(f"🔎 找到 {len(file_pairs)} 个包含文件对的子文件夹:")
        for pair in file_pairs:
            self.logger.info(f"  - {pair['folder']}")
        self.logger.info("=" * 100)

        # 统计结果
        results = {
            'total_folders': len(file_pairs),
            'identical_count': 0,
            'different_count': 0,
            'error_count': 0,
            'total_differences': 0,
            'different_folders': [],  # 新增：记录有差异的文件夹名称
            'details': []
        }

        for pair in file_pairs:
            is_identical, diff_count = self._compare_file_pair(pair)
            result = {
                'folder': pair['folder'],
                'is_identical': is_identical,
                'differences': diff_count,
                'file1': pair['file1'],
                'file2': pair['file2']
            }
            results['details'].append(result)

            if is_identical:
                results['identical_count'] += 1
            elif diff_count > 0:
                results['different_count'] += 1
                results['total_differences'] += diff_count
                results['different_folders'].append(pair['folder'])  # 记录有差异的文件夹
            else:
                results['error_count'] += 1

        # 生成总结报告
        end_time = time.time()
        elapsed_time = end_time - start_time

        self.logger.info("\n" + "=" * 100)
        self.logger.info("🏁 批量比较完成")
        self.logger.info("=" * 100)
        self.logger.info(f"📊 统计摘要:")
        self.logger.info(f"  总文件夹数: {results['total_folders']}")
        self.logger.info(f"  文件完全相同的文件夹: {results['identical_count']}")
        self.logger.info(f"  文件存在差异的文件夹: {results['different_count']}")

        # 新增：输出有差异的文件夹名称
        if results['different_folders']:
            self.logger.info("存在差异的文件夹列表:")
            for folder in results['different_folders']:
                self.logger.info(f"  - {folder}")

        self.logger.info(f"  出错文件夹数: {results['error_count']}")
        self.logger.info(f"  总差异数: {results['total_differences']}")
        self.logger.info(f"⏱️ 总耗时: {elapsed_time:.2f} 秒")
        self.logger.info(f"📄 详细日志已保存至: {os.path.abspath(self.log_filename)}")
        self.logger.info("=" * 100)

        return results

def compare_files_in_directory(parent_dir, file1_name="file1.txt", file2_name="file2.txt"):
    """
    比较指定目录下所有子文件夹中的文件对

    参数:
        parent_dir: 包含多个子文件夹的父目录路径
        file1_name: 第一个文件名 (默认为 'file1.txt')
        file2_name: 第二个文件名 (默认为 'file2.txt')

    返回:
        包含比较结果的字典，或None如果出错
    """
    if not os.path.exists(parent_dir) or not os.path.isdir(parent_dir):
        print(f"错误: 目录 '{parent_dir}' 不存在或不是目录")
        return None

    comparator = BatchFileComparator(parent_dir, file1_name, file2_name)
    return comparator.run()


# 使用示例
if __name__ == "__main__":
    # 比较Number_01下的所有子文件夹
    result = compare_files_in_directory(r"F:\pycharm2023\NCcomparison\files\Number_01")
    if result:
        print("\n比较结果摘要:")
        print(f"处理了 {result['total_folders']} 个文件夹")
        print(f"{result['identical_count']} 个文件夹文件完全相同")
        print(f"{result['different_count']} 个文件夹存在差异:")

        # 打印有差异的文件夹名称
        for folder in result['different_folders']:
            print(f"  - {folder}")

        print(f"共发现 {result['total_differences']} 处差异")