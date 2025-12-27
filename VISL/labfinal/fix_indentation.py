#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时脚本：修复缩进错误
"""

def fix_layout_drawer():
    """修复layout_drawer.py的缩进问题"""
    file_path = 'src/visualization/layout_drawer.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复第215-216行
    if len(lines) > 215:
        # 检查第215行和第216行
        line_215 = lines[214]  # 0-based indexing
        line_216 = lines[215]
        
        print(f"Original line 215: {repr(line_215)}")
        print(f"Original line 216: {repr(line_216)}")
        
        # 修复缩进
        if 'else:' in line_215:
            # 确保第216行有正确的缩进
            lines[215] = '                    title += f" - Iteration {request.iteration}"\n'
            print("Fixed line 216 indentation")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("layout_drawer.py修复完成")

def fix_greedy_pin_assignment():
    """修复greedy_pin_assignment.py的缩进问题"""
    file_path = 'src/algorithms/pin_assignment/greedy_pin_assignment.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复第67行
    if len(lines) > 67:
        line_67 = lines[66]  # 0-based indexing
        print(f"Original line 67: {repr(line_67)}")
        
        # 确保正确的缩进
        if 'self._assign_pins_greedy' in line_67:
            lines[66] = '            self._assign_pins_greedy(pins, design, int(chip_width), int(chip_height), pin_networks)\n'
            print("Fixed line 67 indentation")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("greedy_pin_assignment.py修复完成")

if __name__ == "__main__":
    print("开始修复缩进错误...")
    fix_layout_drawer()
    fix_greedy_pin_assignment()
    print("所有缩进错误修复完成！") 