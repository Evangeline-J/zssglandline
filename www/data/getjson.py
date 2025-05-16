#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_lines.py - 使用与app.js相同的方法处理线段坐标数据

功能:
1. 读取JSON文件中的线段坐标数据
2. 重采样为60个点
3. 计算最小包围圆
4. 基于圆半径进行缩放
5. 将坐标归一化到[-250, 250]范围内
6. 输出处理后的JSON文件
"""

import json
import math
import random
import numpy as np
import argparse
from pathlib import Path

# 常量定义
RESAMPLE_POINTS = 60  # 重采样后的点数（与app.js中保持一致）
TARGET_HALF = 250     # 目标边长一半（方形）

# 实现app.js中的makeCircle函数，用于计算最小包围圆
def make_circle(points):
    """
    计算包围所有点的最小圆
    这是app.js中makeCircle函数的Python实现
    """
    # 特殊情况处理
    if len(points) == 0:
        return {"x": 0, "y": 0, "r": 0}
    if len(points) == 1:
        return {"x": points[0]["x"], "y": points[0]["y"], "r": 0}
    
    # 随机打乱点的顺序，提高算法效率
    shuffled = points.copy()
    random.shuffle(shuffled)
    
    # 从前两个点开始
    c = make_circle_2(shuffled[0], shuffled[1])
    
    # 逐步添加其他点
    for i in range(2, len(shuffled)):
        if not is_point_in_circle(shuffled[i], c):
            c = make_circle_with_point(shuffled[:i], shuffled[i])
    
    return c

def make_circle_2(p1, p2):
    """计算包围两个点的最小圆"""
    cx = (p1["x"] + p2["x"]) / 2
    cy = (p1["y"] + p2["y"]) / 2
    r = math.sqrt((p1["x"] - cx)**2 + (p1["y"] - cy)**2)
    return {"x": cx, "y": cy, "r": r}

def make_circle_3(p1, p2, p3):
    """计算包围三个点的最小圆"""
    # 使用外接圆公式
    temp = p2["x"]**2 + p2["y"]**2
    bc = (p1["x"]**2 + p1["y"]**2 - temp) / 2
    cd = (temp - p3["x"]**2 - p3["y"]**2) / 2
    det = (p1["x"] - p2["x"]) * (p2["y"] - p3["y"]) - (p2["x"] - p3["x"]) * (p1["y"] - p2["y"])
    
    if abs(det) < 1e-10:
        # 三点共线，找出距离最远的两点
        d1 = math.sqrt((p2["x"] - p3["x"])**2 + (p2["y"] - p3["y"])**2)
        d2 = math.sqrt((p1["x"] - p3["x"])**2 + (p1["y"] - p3["y"])**2)
        d3 = math.sqrt((p1["x"] - p2["x"])**2 + (p1["y"] - p2["y"])**2)
        
        if d1 >= d2 and d1 >= d3:
            return make_circle_2(p2, p3)
        elif d2 >= d1 and d2 >= d3:
            return make_circle_2(p1, p3)
        else:
            return make_circle_2(p1, p2)
    
    cx = (bc * (p2["y"] - p3["y"]) - cd * (p1["y"] - p2["y"])) / det
    cy = (cd * (p1["x"] - p2["x"]) - bc * (p2["x"] - p3["x"])) / det
    r = math.sqrt((cx - p1["x"])**2 + (cy - p1["y"])**2)
    return {"x": cx, "y": cy, "r": r}

def make_circle_with_point(points, p):
    """计算包围已有点集和新点的最小圆"""
    c = {"x": p["x"], "y": p["y"], "r": 0}
    
    for i, q in enumerate(points):
        if not is_point_in_circle(q, c):
            if c["r"] == 0:
                c = make_circle_2(p, q)
            else:
                c = make_circle_3(p, q, points[0])
    
    return c

def is_point_in_circle(p, c):
    """判断点是否在圆内"""
    return math.sqrt((p["x"] - c["x"])**2 + (p["y"] - c["y"])**2) <= c["r"] * 1.000001  # 添加小误差容忍

def smooth_interpolate(points, n_points):
    """
    使用类似app.js中Smooth函数的方法进行插值
    """
    if len(points) < 2:
        return points
    
    # 提取x和y坐标
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    
    # 创建参数t，表示点的累积弦长（与app.js中的处理类似）
    t = np.zeros(len(points))
    for i in range(1, len(points)):
        dx = xs[i] - xs[i-1]
        dy = ys[i] - ys[i-1]
        t[i] = t[i-1] + math.sqrt(dx*dx + dy*dy)
    
    if t[-1] == 0:
        # 如果所有点重合，直接返回相同的点
        return points[:n_points] if len(points) >= n_points else points + [points[-1]] * (n_points - len(points))
    
    # 归一化t到[0, 1]
    t = t / t[-1]
    
    # 创建插值函数（使用三次样条插值，更接近app.js中的Smooth效果）
    try:
        from scipy import interpolate
        fx = interpolate.CubicSpline(t, xs)
        fy = interpolate.CubicSpline(t, ys)
    except ImportError:
        # 如果没有scipy，使用numpy的多项式拟合
        fx = np.poly1d(np.polyfit(t, xs, 3))
        fy = np.poly1d(np.polyfit(t, ys, 3))
    
    # 均匀采样n_points个点
    new_t = np.linspace(0, 1, n_points)
    new_xs = fx(new_t)
    new_ys = fy(new_t)
    
    # 返回重采样后的点
    return [{"x": float(x), "y": float(y)} for x, y in zip(new_xs, new_ys)]

def process_line(line_points):
    """
    处理单条线段，使用与app.js相同的方法
    
    参数:
    line_points - 线段坐标点列表，格式为[x1, y1, x2, y2, ...]或[{"x": x1, "y": y1}, ...]
    
    返回:
    处理后的数据对象
    """
    # 确保输入格式一致（转换为对象数组）
    points = []
    if isinstance(line_points, list):
        if isinstance(line_points[0], dict):
            # 已经是对象数组格式
            points = line_points
        else:
            # 是一维数组格式 [x1, y1, x2, y2, ...]
            for i in range(0, len(line_points), 2):
                if i+1 < len(line_points):
                    points.append({"x": line_points[i], "y": line_points[i+1]})
    
    # 重采样为60个点
    resampled_points = smooth_interpolate(points, RESAMPLE_POINTS)
    
    # 计算包围所有点的最小圆
    enclosing_circle = make_circle(resampled_points)
    
    # 基于最小包围圆的半径计算缩放因子
    scale_factor = TARGET_HALF / enclosing_circle["r"] if enclosing_circle["r"] > 0 else 1.0
    
    # 应用缩放，将坐标缩放到[-250, 250]范围内
    scaled_coords = []
    for p in resampled_points:
        # 将坐标系原点移到圆心，然后缩放
        scaled_x = (p["x"] - enclosing_circle["x"]) * scale_factor
        scaled_y = (p["y"] - enclosing_circle["y"]) * scale_factor
        scaled_coords.append(round(scaled_x))
        scaled_coords.append(round(scaled_y))
    
    # 创建结果对象
    result = {
        "coords": scaled_coords,
        "scaleFactor": scale_factor,
        "circle": {
            "x": enclosing_circle["x"],
            "y": enclosing_circle["y"],
            "r": enclosing_circle["r"]
        }
    }
    
    return result

def process_json_file(input_file, output_file):
    """
    处理JSON文件中的线段数据
    
    参数:
    input_file - 输入JSON文件路径
    output_file - 输出JSON文件路径
    """
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 处理结果
    results = []
    
    # 根据输入JSON的结构进行处理
    if isinstance(data, list):
        # 如果是数组，假设每个元素是一条线段
        for i, line in enumerate(data):
            if "points" in line:
                # 格式: [{"points": [x1, y1, x2, y2, ...]}, ...]
                result = process_line(line["points"])
            elif "coords" in line:
                # 格式: [{"coords": [x1, y1, x2, y2, ...]}, ...]
                result = process_line(line["coords"])
            else:
                # 格式: [[x1, y1, x2, y2, ...], ...]
                result = process_line(line)
            
            # 添加原始索引
            result["index"] = i
            results.append(result)
    elif "lines" in data:
        # 格式: {"lines": [[x1, y1, x2, y2, ...], ...]}
        for i, line in enumerate(data["lines"]):
            result = process_line(line)
            result["index"] = i
            results.append(result)
    elif "segments" in data:
        # 格式: {"segments": [[x1, y1, x2, y2, ...], ...]}
        for i, line in enumerate(data["segments"]):
            result = process_line(line)
            result["index"] = i
            results.append(result)
    else:
        # 尝试处理其他可能的格式
        print("警告: 未识别的JSON格式，尝试直接处理...")
        try:
            result = process_line(data)
            results.append(result)
        except Exception as e:
            print(f"错误: 无法处理输入数据: {e}")
            return
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 处理完成! 共处理 {len(results)} 条线段")
    print(f"✓ 结果已保存到: {output_file}")

def main():
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='使用与app.js相同的方法处理线段坐标数据')
    parser.add_argument('input', help='输入JSON文件路径')
    parser.add_argument('-o', '--output', help='输出JSON文件路径 (默认为input_processed.json)')
    args = parser.parse_args()
    
    input_file = args.input
    if args.output:
        output_file = args.output
    else:
        # 默认输出文件名
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_processed{input_path.suffix}")
    
    # 处理文件
    process_json_file(input_file, output_file)

if __name__ == "__main__":
    main()