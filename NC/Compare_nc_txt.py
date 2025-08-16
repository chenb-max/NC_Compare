import difflib
import os
import logging
import time
from datetime import datetime


class BatchFileComparator:
    def __init__(self, parent_dir, file_exts=[".nc", ".txt"]):
        self.parent_dir = parent_dir
        self.file_exts = [ext.lower() for ext in file_exts]
        self.logger = None
        self.log_filename = None
        self.different_files = []
        self._setup_logger()

    def _setup_logger(self):
        """配置日志系统"""
        files_dir = os.path.dirname(self.parent_dir)
        log_dir = os.path.join(files_dir, "file_diff_logs")
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join(log_dir, f"batch_diff_{timestamp}.log")

        self.logger = logging.getLogger("BatchFileDiff")
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(self.log_filename, encoding='utf-8')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        self.logger.info("=" * 100)
        self.logger.info(f"文件批量比较工具启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"父目录: {os.path.abspath(self.parent_dir)}")
        self.logger.info(f"比较文件扩展名: {', '.join(self.file_exts)}")
        self.logger.info("=" * 100)

    def _find_files(self):
        """查找所有指定扩展名的文件"""
        file_groups = {}

        for folder in os.listdir(self.parent_dir):
            folder_path = os.path.join(self.parent_dir, folder)

            if not os.path.isdir(folder_path):
                continue

            # 按扩展名分类文件
            ext_files = {ext: [] for ext in self.file_exts}
            for file in os.listdir(folder_path):
                file_lower = file.lower()
                for ext in self.file_exts:
                    if file_lower.endswith(ext):
                        ext_files[ext].append(os.path.join(folder_path, file))
                        break

            # 对每种扩展名的文件列表进行排序
            for ext in self.file_exts:
                ext_files[ext].sort()

            file_groups[folder] = {
                'folder_path': folder_path,
                'files_by_ext': ext_files
            }

        return file_groups

    def _compare_files(self, file1, file2):
        """比较两个文件"""
        try:
            with open(file1, 'r', encoding='utf-8') as f1, \
                    open(file2, 'r', encoding='utf-8') as f2:
                lines1 = f1.readlines()
                lines2 = f2.readlines()
        except UnicodeDecodeError:
            with open(file1, 'rb') as f1, \
                    open(file2, 'rb') as f2:
                lines1 = [line.decode('latin1') for line in f1]
                lines2 = [line.decode('latin1') for line in f2]

        differ = difflib.Differ()
        return list(differ.compare(lines1, lines2)), len(lines1), len(lines2)

    def _analyze_differences(self, diff):
        """分析差异"""
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

    def _compare_in_folder(self, folder, folder_info):
        """比较单个文件夹中的文件"""
        folder_path = folder_info['folder_path']
        files_by_ext = folder_info['files_by_ext']

        self.logger.info(f"\n{'=' * 100}")
        self.logger.info(f"📁 正在处理文件夹: {folder}")
        self.logger.info(f"📂 路径: {folder_path}")

        comparison_results = []

        # 对每种扩展名分别比较
        for ext in self.file_exts:
            files = files_by_ext[ext]
            if len(files) < 2:
                if len(files) == 1:
                    self.logger.info(f"⚠️ 只有1个{ext}文件: {os.path.basename(files[0])}")
                continue

            file1, file2 = files[0], files[1]
            file1_name = os.path.basename(file1)
            file2_name = os.path.basename(file2)

            self.logger.info(f"\n🔍 同{ext}扩展名比较:")
            self.logger.info(f"  文件1: {file1_name}")
            self.logger.info(f"  文件2: {file2_name}")

            try:
                diff_result, file1_lines, file2_lines = self._compare_files(file1, file2)
                self.logger.info(f"📝 文件行数: {file1_name}: {file1_lines}, {file2_name}: {file2_lines}")

                differences = self._analyze_differences(diff_result)

                if not differences:
                    self.logger.info("✅ 文件内容完全相同")
                    result = {
                        'status': 'identical',
                        'file1': file1_name,
                        'file2': file2_name,
                        'ext': ext,
                        'differences': 0
                    }
                else:
                    self.logger.info(f"❌ 发现 {len(differences)} 处差异")
                    self.different_files.append({
                        'folder': folder,
                        'file1': file1_name,
                        'file2': file2_name,
                        'ext': ext,
                        'differences': len(differences)
                    })

                    for i, diff in enumerate(differences, 1):
                        if diff['type'] == '变化后内容':
                            self.logger.info(f"    | 改为: {diff['content']}")
                        else:
                            self.logger.info(f"差异 #{i}: {diff['type']} [行号: {diff['line']}]")
                            self.logger.info(f"    | 内容: {diff['content']}")
                        self.logger.info("-" * 50)

                    result = {
                        'status': 'different',
                        'file1': file1_name,
                        'file2': file2_name,
                        'ext': ext,
                        'differences': len(differences)
                    }

                comparison_results.append(result)

            except Exception as e:
                self.logger.error(f"处理错误: {str(e)}")
                comparison_results.append({
                    'status': 'error',
                    'error': str(e),
                    'ext': ext
                })

        return {
            'comparisons': comparison_results,
            'folder': folder
        }

    def run(self):
        """执行批量比较"""
        start_time = time.time()
        file_groups = self._find_files()

        if not file_groups:
            self.logger.error(f"在目录 {self.parent_dir} 中未找到任何子文件夹")
            return None

        self.logger.info(f"🔎 找到 {len(file_groups)} 个子文件夹:")
        for folder, info in file_groups.items():
            file_counts = {ext: len(files) for ext, files in info['files_by_ext'].items()}
            status = ", ".join([f"{ext}:{count}" for ext, count in file_counts.items()])
            self.logger.info(f"  - {folder}: {status}")

        results = {
            'total_folders': len(file_groups),
            'compared_pairs': 0,
            'identical_pairs': 0,
            'different_pairs': 0,
            'error_pairs': 0,
            'total_differences': 0,
            'different_files': [],
            'details': []
        }

        for folder, folder_info in file_groups.items():
            result = self._compare_in_folder(folder, folder_info)
            results['details'].append(result)

            for comp in result['comparisons']:
                results['compared_pairs'] += 1
                if comp['status'] == 'identical':
                    results['identical_pairs'] += 1
                elif comp['status'] == 'different':
                    results['different_pairs'] += 1
                    results['total_differences'] += comp['differences']
                    results['different_files'].append({
                        'folder': folder,
                        'file1': comp['file1'],
                        'file2': comp['file2'],
                        'ext': comp['ext'],
                        'differences': comp['differences']
                    })
                elif comp['status'] == 'error':
                    results['error_pairs'] += 1

        # 生成报告
        elapsed_time = time.time() - start_time
        self.logger.info("\n" + "=" * 100)
        self.logger.info("🏁 批量比较完成")
        self.logger.info("=" * 100)
        self.logger.info(f"📊 统计摘要:")
        self.logger.info(f"  总文件夹数: {results['total_folders']}")
        self.logger.info(f"  比较文件对数: {results['compared_pairs']}")
        self.logger.info(f"    ├─ 文件相同: {results['identical_pairs']}")
        self.logger.info(f"    └─ 文件不同: {results['different_pairs']}")
        self.logger.info(f"  比较错误: {results['error_pairs']}")
        self.logger.info(f"  总差异数: {results['total_differences']}")

        if results['different_files']:
            self.logger.info("\n📌 不同的文件对列表:")
            for item in results['different_files']:
                self.logger.info(f"  - 文件夹: {item['folder']}")
                self.logger.info(f"    ├─ 比较类型: 同{item['ext']}扩展名比较")
                self.logger.info(f"    ├─ 文件1: {item['file1']}")
                self.logger.info(f"    └─ 文件2: {item['file2']}")
                self.logger.info(f"    差异数: {item['differences']}")
                self.logger.info("-" * 50)

        self.logger.info(f"\n⏱️ 耗时: {elapsed_time:.2f}秒")
        self.logger.info(f"📄 日志文件: {os.path.abspath(self.log_filename)}")
        self.logger.info("=" * 100)

        return results


if __name__ == "__main__":
    # 使用示例
    comparator = BatchFileComparator(
        r"f:/VSCode/NCcomparison\files\Number_01",
        file_exts=[".nc", ".txt"]
    )

    result = comparator.run()

    if result:
        print("\n比较结果摘要:")
        print(f"处理文件夹数: {result['total_folders']}")
        print(f"比较文件对数: {result['compared_pairs']}")
        print(f"  - 相同: {result['identical_pairs']}")
        print(f"  - 不同: {result['different_pairs']} (共 {result['total_differences']}处差异)")
        print(f"错误: {result['error_pairs']}")

        if result['different_files']:
            print("\n不同的文件对:")
            for idx, item in enumerate(result['different_files'], 1):
                print(f"{idx}. 文件夹: {item['folder']}")
                print(f"   比较类型: 同{item['ext']}扩展名比较")
                print(f"   - {item['file1']}")
                print(f"   - {item['file2']}")
                print(f"   差异数: {item['differences']}")
                print("-" * 40)