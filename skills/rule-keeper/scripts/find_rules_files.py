#!/usr/bin/env python3
"""定位项目中的项目规则文件（只读，不修改任何文件）。

用法:
    python3 find_rules_files.py [项目根目录]

默认以当前目录为项目根。找到的候选文件按根目录名 → 相对路径顺序列出；
未找到时提示默认建议（在项目根创建 AGENTS.md）。退出码：0 = 正常。
"""

import glob
import os
import sys

# 项目根下的已知规则文件名（大小写不敏感）
ROOT_NAMES = {
    "AGENTS.MD",
    "CLAUDE.MD",
    "RULES.MD",
    "PROJECT-RULES.MD",
    "COPILOT-INSTRUCTIONS.MD",
    ".CURSORRULES",
}

# 常见相对路径模式（相对项目根）
RELATIVE_PATTERNS = [
    ".cursor/rules/*.md",
    ".github/copilot-instructions.md",
    "docs/RULES.md",
    "docs/rules.md",
    ".ai/rules.md",
    ".agent/rules.md",
    "agent/rules.md",
]


def main() -> int:
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    if not os.path.isdir(root):
        print(f"错误：目录不存在 {root}")
        return 2

    found: list[str] = []

    # 1) 项目根目录下的已知文件名（大小写不敏感）
    for name in sorted(os.listdir(root)):
        if name.upper() in ROOT_NAMES:
            found.append(os.path.join(root, name))

    # 2) 常见相对路径模式
    for pattern in RELATIVE_PATTERNS:
        for path in glob.glob(os.path.join(root, pattern), recursive=True):
            if os.path.isfile(path):
                found.append(path)

    # 去重并保序
    seen: set[str] = set()
    unique: list[str] = []
    for path in found:
        if path not in seen:
            seen.add(path)
            unique.append(path)

    if unique:
        print(f"找到 {len(unique)} 个候选规则文件：")
        for path in unique:
            print(f"  {path}")
        print("按项目实际约定选择要维护的一个（默认首选 AGENTS.md）。")
    else:
        print(f"在 {root} 下未找到既有规则文件。")
        print("默认建议：在项目根创建 AGENTS.md。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
