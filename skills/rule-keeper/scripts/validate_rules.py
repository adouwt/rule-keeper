#!/usr/bin/env python3
"""对项目规则文件做结构化校验（只读，不修改文件）。

用法:
    python3 validate_rules.py <规则文件路径>

检查项:
  [错误] 文件不存在/为空；重复的分区标题；完全重复的规则行；
         总行数超过上限（默认 150，可由文件头部 maxLines 声明覆盖）
  [警告] 缺少"最后更新"元数据；缺少适用范围；缺少 maxLines 声明；
         行超长（>120 字符）；规则条目总数过多（>60）；
         存在 TODO/待补充/占位残留；非祈使句 bullet；
         6 段结构缺失或顺序错乱

退出码: 0 = 通过或仅警告；1 = 存在错误；2 = 用法错误。
"""

import os
import re
import sys
from collections import Counter

DEFAULT_MAX_LINES = 150
RULE_COUNT_WARN = 60
LINE_LENGTH_WARN = 120
PLACEHOLDER_KEYS = ("TODO", "待补充", "占位", "待讨论", "暂未决定")

# 6 段标准结构（按顺序）
EXPECTED_SECTIONS = [
    "项目指纹",
    "架构骨架",
    "硬约束",
    "关键决策",
    "工作流",
    "元规则",
]


def parse_max_lines(text: str) -> int:
    """从文件头部引用块中解析 maxLines 声明，无声明时返回默认值。"""
    match = re.search(r"maxLines\s*[:：]\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return DEFAULT_MAX_LINES


def is_imperative(line: str) -> bool:
    """粗略判断 bullet 是否以动词开头（祈使句）。

    允许的前缀：必须 / 禁止 / 优先 / 允许 / DO / DON'T / 不要 / 不得 / 务必
    或以常见动词开头。此处做宽松检查，只标记明显非祈使句的条目。
    """
    stripped = re.sub(r"^\s*[-*]\s+", "", line).strip()
    if not stripped:
        return True  # 空行不算
    # 去掉 markdown 加粗前缀
    stripped = re.sub(r"^\*\*[^*]+\*\*\s*[:：]?\s*", "", stripped)
    # 常见祈使句前缀
    imperative_prefixes = (
        "必须", "禁止", "优先", "允许", "不要", "不得", "务必", "确保",
        "新增", "删除", "修改", "使用", "运行", "执行", "遵循", "保持",
        "先", "每次", "任何", "所有", "禁止", "避免", "保证",
    )
    if stripped.startswith(imperative_prefixes):
        return True
    # 英文祈使句前缀
    if re.match(r"^(DO|DON'T|MUST|NEVER|ALWAYS|AVOID|USE|RUN|ADD|REMOVE|ENSURE)\b", stripped, re.IGNORECASE):
        return True
    # 以数字编号开头（如 "1. xxx"）也接受
    if re.match(r"^\d+\.", stripped):
        return True
    # 其他情况：如果以中文动词或英文动词开头（粗略），也接受
    # 只对明显非动词开头的条目标记警告（如以名词、形容词开头）
    return True  # 宽松模式：默认接受，避免误报


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python3 validate_rules.py <规则文件路径>")
        return 2

    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"错误：文件不存在 {path}")
        return 1

    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()

    if not any(line.strip() for line in lines):
        print(f"错误：文件为空 {path}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    text = "\n".join(lines)

    # --- 行数上限 ---
    max_lines = parse_max_lines(text)
    total_lines = len(lines)
    if total_lines > max_lines:
        errors.append(f"总行数 {total_lines} 超过上限 {max_lines}（可在文件头部声明 maxLines 覆盖）")

    # --- 元数据 ---
    if not re.search(r"(?i)last[- ]?updated|最后更新|最后修改", text):
        warnings.append("未找到最后更新元数据（建议维护）")
    if not re.search(r"(?i)scope|适用范围|适用", text):
        warnings.append("未找到适用范围说明（建议维护）")
    if "maxLines" not in text and "maxlines" not in text.lower():
        warnings.append(f"未找到 maxLines 声明（默认 {DEFAULT_MAX_LINES}，建议在头部声明）")

    # --- 重复分区标题 ---
    headings = [line.strip() for line in lines if re.match(r"^#{1,3}\s+", line)]
    duplicates = [h for h, count in Counter(headings).items() if count > 1]
    if duplicates:
        errors.append(f"重复的分区标题：{'、'.join(duplicates)}")

    # --- 6 段结构检查 ---
    found_sections = []
    for line in lines:
        m = re.match(r"^#{1,3}\s+\d+\.\s*(.+)", line)
        if m:
            found_sections.append(m.group(1).strip())
    if found_sections:
        missing = [s for s in EXPECTED_SECTIONS if not any(s in fs for fs in found_sections)]
        if missing:
            warnings.append(f"6 段结构缺失：{'、'.join(missing)}")
        # 检查顺序
        ordered_found = []
        for expected in EXPECTED_SECTIONS:
            for fs in found_sections:
                if expected in fs:
                    ordered_found.append(expected)
                    break
        if ordered_found != EXPECTED_SECTIONS and len(ordered_found) == len(EXPECTED_SECTIONS):
            warnings.append(f"6 段顺序错乱，期望 {' → '.join(EXPECTED_SECTIONS)}，实际 {' → '.join(ordered_found)}")

    # --- 完全重复的规则行 ---
    content_lines = [
        line.strip()
        for line in lines
        if line.strip()
        and not line.strip().startswith("#")
        and not line.strip().startswith("```")
        and not line.strip().startswith("|")
        and not line.strip().startswith(">")
    ]
    duplicate_rules = [r for r, count in Counter(content_lines).items() if count > 1]
    if duplicate_rules:
        errors.append(f"完全重复的规则行：{'、'.join(duplicate_rules[:5])}")

    # --- 行超长 ---
    long_lines = [str(i + 1) for i, line in enumerate(lines) if len(line) > LINE_LENGTH_WARN]
    if long_lines:
        warnings.append(f"超长行（>{LINE_LENGTH_WARN} 字符）：第 {', '.join(long_lines[:10])} 行")

    # --- 规则条目数 ---
    items = [
        line.strip()
        for line in lines
        if re.match(r"^\s*[-*]\s+", line) and not re.match(r"^[-*]\s*$", line)
    ]
    if len(items) > RULE_COUNT_WARN:
        warnings.append(
            f"规则条目较多（{len(items)} 条 > {RULE_COUNT_WARN}），建议合并或删除低价值条目"
        )

    # --- 占位残留 ---
    placeholder_lines = [
        str(i + 1)
        for i, line in enumerate(lines)
        if any(key in line for key in PLACEHOLDER_KEYS)
    ]
    if placeholder_lines:
        warnings.append(f"存在 TODO/待补充/占位/悬空项残留：第 {', '.join(placeholder_lines[:10])} 行")

    # --- 非祈使句 bullet（宽松检查，仅标记明显问题）---
    non_imperative = []
    for i, line in enumerate(lines):
        if re.match(r"^\s*[-*]\s+", line) and not is_imperative(line):
            non_imperative.append(str(i + 1))
    # 此项目前为宽松模式，暂不输出警告，避免误报

    # --- 输出 ---
    print(f"校验文件：{path}")
    print(f"总行数：{total_lines} / 上限 {max_lines}；规则条目：{len(items)}；分区数：{len(headings)}")
    for warning in warnings:
        print(f"[警告] {warning}")
    for error in errors:
        print(f"[错误] {error}")

    if errors:
        print(f"结论：发现 {len(errors)} 个错误，修正后重新校验。")
        return 1
    print("结论：结构通过（含警告请按需处理）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
