# -*- coding: utf-8 -*-
"""
培训效果追踪器 - 可视化图表模块
使用 matplotlib 生成各类分析图表
"""

import os
import matplotlib
matplotlib.use('Agg')  # 无头模式，不弹出窗口
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager
import numpy as np
import config

# ==================== 字体配置 ====================
def get_font():
    """获取中文字体"""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return font_manager.FontProperties(fname=path)
    return None

FONT = get_font()

# ==================== 配色方案 ====================
COLORS = {
    "primary": "#2C5F8A",
    "secondary": "#4A90D9",
    "success": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "purple": "#9B59B6",
    "teal": "#1ABC9C",
}

# ==================== 图表基础设置 ====================
plt.rcParams['font.size'] = 11
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['grid.linestyle'] = '--'


def get_color_for_improvement(pct):
    """根据进步幅度返回颜色"""
    if pct >= 30:
        return COLORS["success"]
    elif pct >= 15:
        return COLORS["secondary"]
    elif pct >= 5:
        return COLORS["warning"]
    else:
        return COLORS["danger"]


def get_level_label(score):
    """获取分数对应的等级标签"""
    for threshold, label, color in config.SCORE_LEVELS:
        if score >= threshold:
            return label
    return "不及格"


def bar_chart(data, labels, title, ylabel="分数", figsize=(10, 5)):
    """通用柱状图"""
    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(labels, data, color=COLORS["secondary"], edgecolor='white', linewidth=1.5)

    # 添加数值标签
    for bar, val in zip(bars, data):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val:.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, max(data) * 1.15 if data else 100)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig


def progress_comparison_chart(pre_scores, post_scores, names, title="前后测成绩对比"):
    """前后测对比柱状图"""
    fig, ax = plt.subplots(figsize=(max(8, len(names) * 1.5), 6))

    x = np.arange(len(names))
    width = 0.35

    bars1 = ax.bar(x - width/2, pre_scores, width, label='前测', color='#BDC3C7', edgecolor='white')
    bars2 = ax.bar(x + width/2, post_scores, width, label='后测', color=COLORS["secondary"], edgecolor='white')

    # 添加数值
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha='right')
    ax.set_ylabel('分数')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper left')
    ax.set_ylim(0, 110)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig


def improvement_line_chart(data_dict, title="进步趋势"):
    """多条进步趋势线图（不同培训）"""
    fig, ax = plt.subplots(figsize=(10, 5))

    colors_list = list(COLORS.values())
    for i, (name, scores) in enumerate(data_dict.items()):
        ax.plot(range(1, len(scores)+1), scores, marker='o', linewidth=2,
                label=name, color=colors_list[i % len(colors_list)])

    ax.set_xlabel('培训序号')
    ax.set_ylabel('成绩分数')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    ax.set_ylim(0, 105)
    ax.set_xticks(range(1, max(len(s) for s in data_dict.values()) + 1))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig


def improvement_distribution_chart(improvements, title="进步幅度分布"):
    """进步幅度分布直方图"""
    fig, ax = plt.subplots(figsize=(8, 5))

    colors = [get_color_for_improvement(p) for p in improvements]
    bars = ax.bar(range(len(improvements)), improvements, color=colors, edgecolor='white')

    ax.axhline(y=15, color=COLORS["secondary"], linestyle='--', linewidth=1.5, label='良好线(15%)')
    ax.axhline(y=30, color=COLORS["success"], linestyle='--', linewidth=1.5, label='优秀线(30%)')

    for bar, val in zip(bars, improvements):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('学员编号')
    ax.set_ylabel('进步幅度 (%)')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig


def radar_chart_for_training(stats_dict, title="培训效果雷达图"):
    """雷达图：展示多个培训的多维度指标"""
    categories = list(stats_dict[0].keys())
    N = len(categories)

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    colors = list(COLORS.values())
    for i, stats in enumerate(stats_dict):
        values = list(stats.values())
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=f"培训{i+1}", color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.15, color=colors[i % len(colors)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=11)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    plt.tight_layout()
    return fig


def heatmap_chart(data_matrix, row_labels, col_labels, title="培训效果热力图", cmap="Blues"):
    """热力图：培训效果按主题和时间"""
    fig, ax = plt.subplots(figsize=(10, max(4, len(row_labels) * 0.8)))

    im = ax.imshow(data_matrix, cmap=cmap, aspect='auto')

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)

    # 添加数值标签
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            val = data_matrix[i][j]
            color = "white" if val > data_matrix.max() * 0.6 else "black"
            ax.text(j, i, f'{val:.0f}', ha='center', va='center', color=color, fontsize=10)

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    plt.colorbar(im, ax=ax, label='平均进步幅度(%)')
    plt.tight_layout()
    return fig


def pie_chart_for_scores(scores, labels=None, title="成绩分布"):
    """饼图：成绩分布"""
    if labels is None:
        labels = [get_level_label(s) for s in scores]

    # 统计各等级数量
    level_counts = {"优秀": 0, "良好": 0, "及格": 0, "不及格": 0}
    level_colors = {"优秀": COLORS["success"], "良好": COLORS["secondary"],
                    "及格": COLORS["warning"], "不及格": COLORS["danger"]}

    for score in scores:
        level = get_level_label(score)
        level_counts[level] += 1

    fig, ax = plt.subplots(figsize=(7, 7))
    sizes = list(level_counts.values())
    pie_labels = list(level_counts.keys())
    pie_colors = [level_colors[l] for l in pie_labels if level_counts[l] > 0]
    pie_labels = [l for l in pie_labels if level_counts[l] > 0]

    if not pie_labels:
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=14)
        plt.tight_layout()
        return fig

    wedges, texts, autotexts = ax.pie(
        [level_counts[l] for l in pie_labels],
        labels=pie_labels,
        colors=pie_colors,
        autopct='%1.1f%%',
        startangle=90,
        explode=[0.02] * len(pie_labels),
        shadow=False
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    return fig


def save_fig(fig, filepath):
    """保存图表到文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return filepath


def generate_dashboard_image(stats):
    """生成仪表盘图片（KPI卡片风格）"""
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.5))
    fig.patch.set_facecolor('#F4F7FA')

    kpi_data = [
        {"label": "在册学员", "value": stats.get("active_students", 0), "icon": "👥", "color": COLORS["primary"]},
        {"label": "进行中培训", "value": stats.get("active_trainings", 0), "icon": "📚", "color": COLORS["secondary"]},
        {"label": "测评记录", "value": stats.get("total_records", 0), "icon": "📝", "color": COLORS["purple"]},
        {"label": "平均进步率", "value": f"{stats.get('avg_improvement', 0):.1f}%", "icon": "📈", "color": COLORS["success"]},
    ]

    for ax, kpi in zip(axes, kpi_data):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # 卡片背景
        rect = mpatches.FancyBboxPatch((0.02, 0.1), 0.96, 0.8,
                                        boxstyle="round,pad=0.05",
                                        facecolor='white', edgecolor=kpi["color"],
                                        linewidth=2, alpha=0.95)
        ax.add_patch(rect)

        # 图标
        ax.text(0.5, 0.75, kpi["icon"], ha='center', va='center', fontsize=24)

        # 数值
        ax.text(0.5, 0.45, str(kpi["value"]), ha='center', va='center',
                fontsize=20, fontweight='bold', color=kpi["color"])

        # 标签
        ax.text(0.5, 0.18, kpi["label"], ha='center', va='center',
                fontsize=11, color='#555')

    plt.tight_layout(pad=2)
    return fig
