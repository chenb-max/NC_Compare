#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# 2025/8/15 22:11
import os
for root, dirs, files in os.walk(r"F:\pycharm2023\NCcomparison\files\Number_01"):
    print(f"目录: {root}")
    print(f"子文件夹: {dirs}")
    print(f"文件: {files}\n")