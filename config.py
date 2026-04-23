# -*- coding: utf-8 -*-
"""
培训效果追踪器 - 配置模块
Training Effectiveness Tracker
"""

# ==================== 主题配色方案 ====================
THEME = {
    "primary": "#2C5F8A",       # 深蓝（主色）
    "secondary": "#4A90D9",    # 亮蓝
    "success": "#27AE60",      # 绿色（进步/达标）
    "warning": "#F39C12",      # 橙色（警示）
    "danger": "#E74C3C",       # 红色（下降/未达标）
    "light": "#ECF0F1",        # 浅灰背景
    "dark": "#2C3E50",         # 深灰文字
    "white": "#FFFFFF",
    "bg": "#F4F7FA",            # 页面背景
    "card_bg": "#FFFFFF",
    "border": "#D0D9E2",
}

# ==================== 进步幅度阈值 ====================
PROGRESS_THRESHOLDS = {
    "excellent": 30,    # ≥30% 显著进步
    "good": 15,         # ≥15% 良好
    "average": 5,       # ≥5% 一般
    # <5% 无明显进步
}

# ==================== 评分标准 ====================
SCORE_LEVELS = [
    (90, "优秀", "#27AE60"),
    (75, "良好", "#4A90D9"),
    (60, "及格", "#F39C12"),
    (0, "不及格", "#E74C3C"),
]

# ==================== 培训主题预设 ====================
TRAINING_TOPICS = [
    "新员工入职培训",
    "岗位技能培训",
    "管理能力培训",
    "领导力发展",
    "数字化技能培训",
    "安全合规培训",
    "销售技巧培训",
    "客户服务培训",
    "产品知识培训",
    "团队协作培训",
]

# ==================== 里程碑预设 ====================
DEFAULT_MILESTONES = [
    {"name": "培训前测", "icon": "📝"},
    {"name": "课程完成", "icon": "✅"},
    {"name": "课后作业", "icon": "📋"},
    {"name": "培训后测", "icon": "🎯"},
    {"name": "30天跟进", "icon": "🔄"},
    {"name": "90天评估", "icon": "📊"},
]

# ==================== 文件路径 ====================
DATA_DIR = "data"
STUDENTS_FILE = f"{DATA_DIR}/students.json"
TRAININGS_FILE = f"{DATA_DIR}/trainings.json"
RECORDS_FILE = f"{DATA_DIR}/records.json"
REPORTS_DIR = "reports"

# ==================== 版本信息 ====================
VERSION = "1.0.0"
APP_NAME = "培训效果追踪器"
APP_NAME_EN = "Training Effectiveness Tracker"
