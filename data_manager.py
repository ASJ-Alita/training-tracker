# -*- coding: utf-8 -*-
"""
培训效果追踪器 - 数据管理模块
管理学员、培训计划、测评记录
"""

import os
import json
import uuid
from datetime import datetime
import config

class DataManager:
    """数据管理器"""

    def __init__(self):
        self.data_dir = config.DATA_DIR
        self.ensure_data_dir()
        self.students = self.load_data(config.STUDENTS_FILE, [])
        self.trainings = self.load_data(config.TRAININGS_FILE, [])
        self.records = self.load_data(config.RECORDS_FILE, [])

    def ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(self.data_dir, exist_ok=True)

    def load_data(self, filepath, default):
        """加载JSON数据"""
        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载数据失败 {filepath}: {e}")
        return default

    def save_data(self, filepath, data):
        """保存JSON数据"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存数据失败: {e}")
            return False

    # ==================== 学员管理 ====================

    def add_student(self, name, dept="", position="", email=""):
        """添加学员"""
        student = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "dept": dept,
            "position": position,
            "email": email,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "active"
        }
        self.students.append(student)
        self.save_data(config.STUDENTS_FILE, self.students)
        return student

    def update_student(self, student_id, **kwargs):
        """更新学员信息"""
        for s in self.students:
            if s["id"] == student_id:
                s.update(kwargs)
                self.save_data(config.STUDENTS_FILE, self.students)
                return s
        return None

    def delete_student(self, student_id):
        """删除学员"""
        self.students = [s for s in self.students if s["id"] != student_id]
        # 同时删除相关记录
        self.records = [r for r in self.records if r.get("student_id") != student_id]
        self.save_data(config.STUDENTS_FILE, self.students)
        self.save_data(config.RECORDS_FILE, self.records)
        return True

    def get_student(self, student_id):
        """获取学员"""
        for s in self.students:
            if s["id"] == student_id:
                return s
        return None

    # ==================== 培训计划管理 ====================

    def add_training(self, name, topic, start_date, end_date, max_score=100):
        """添加培训计划"""
        training = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "topic": topic,
            "start_date": start_date,
            "end_date": end_date,
            "max_score": max_score,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "active"
        }
        self.trainings.append(training)
        self.save_data(config.TRAININGS_FILE, self.trainings)
        return training

    def update_training(self, training_id, **kwargs):
        """更新培训计划"""
        for t in self.trainings:
            if t["id"] == training_id:
                t.update(kwargs)
                self.save_data(config.TRAININGS_FILE, self.trainings)
                return t
        return None

    def delete_training(self, training_id):
        """删除培训计划"""
        self.trainings = [t for t in self.trainings if t["id"] != training_id]
        self.records = [r for r in self.records if r.get("training_id") != training_id]
        self.save_data(config.TRAININGS_FILE, self.trainings)
        self.save_data(config.RECORDS_FILE, self.records)
        return True

    def get_training(self, training_id):
        """获取培训计划"""
        for t in self.trainings:
            if t["id"] == training_id:
                return t
        return None

    # ==================== 测评记录管理 ====================

    def add_record(self, student_id, training_id, record_type, score, notes=""):
        """
        添加测评记录
        record_type: pre(前测) / post(后测) / milestone(里程碑)
        """
        record = {
            "id": str(uuid.uuid4())[:8],
            "student_id": student_id,
            "training_id": training_id,
            "type": record_type,
            "score": float(score),
            "notes": notes,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.records.append(record)
        self.save_data(config.RECORDS_FILE, self.records)
        return record

    def get_records_by_student(self, student_id):
        """获取学员的所有记录"""
        return [r for r in self.records if r["student_id"] == student_id]

    def get_records_by_training(self, training_id):
        """获取培训的所有记录"""
        return [r for r in self.records if r["training_id"] == training_id]

    def get_student_training_record(self, student_id, training_id):
        """获取学员在某培训中的前测/后测记录"""
        records = [r for r in self.records
                   if r["student_id"] == student_id and r["training_id"] == training_id]
        pre = next((r for r in records if r["type"] == "pre"), None)
        post = next((r for r in records if r["type"] == "post"), None)
        milestones = [r for r in records if r["type"] == "milestone"]
        return pre, post, milestones

    def delete_record(self, record_id):
        """删除记录"""
        self.records = [r for r in self.records if r["id"] != record_id]
        self.save_data(config.RECORDS_FILE, self.records)
        return True

    # ==================== 统计分析 ====================

    def get_training_stats(self, training_id):
        """获取培训的整体统计"""
        records = self.get_records_by_training(training_id)
        pres = [r for r in records if r["type"] == "pre"]
        posts = [r for r in records if r["type"] == "post"]

        if not pres or not posts:
            return None

        pre_avg = sum(r["score"] for r in pres) / len(pres)
        post_avg = sum(r["score"] for r in posts) / len(posts)
        improvement = post_avg - pre_avg
        improvement_pct = (improvement / pre_avg * 100) if pre_avg > 0 else 0

        # 达标率（进步≥15%或后测≥75分）
        qualified = sum(1 for r in posts if r["score"] >= 75)
        qualified_rate = qualified / len(posts) * 100 if posts else 0

        return {
            "total_students": len(pres),
            "pre_avg": round(pre_avg, 1),
            "post_avg": round(post_avg, 1),
            "improvement": round(improvement, 1),
            "improvement_pct": round(improvement_pct, 1),
            "qualified_rate": round(qualified_rate, 1),
        }

    def get_student_progress(self, student_id):
        """获取学员所有培训的进步情况"""
        progress = []
        for t in self.trainings:
            pre, post, milestones = self.get_student_training_record(student_id, t["id"])
            if pre and post:
                improvement = post["score"] - pre["score"]
                improvement_pct = (improvement / pre["score"] * 100) if pre["score"] > 0 else 0
                progress.append({
                    "training": t,
                    "pre": pre,
                    "post": post,
                    "improvement": round(improvement, 1),
                    "improvement_pct": round(improvement_pct, 1),
                    "milestones": milestones
                })
        return progress

    def get_dashboard_stats(self):
        """获取仪表盘统计数据"""
        active_students = len([s for s in self.students if s.get("status") == "active"])
        active_trainings = len([t for t in self.trainings if t.get("status") == "active"])
        total_records = len(self.records)

        # 计算整体进步率
        all_improvements = []
        for t in self.trainings:
            stats = self.get_training_stats(t["id"])
            if stats and stats["improvement_pct"] != 0:
                all_improvements.append(stats["improvement_pct"])

        avg_improvement = sum(all_improvements) / len(all_improvements) if all_improvements else 0

        return {
            "active_students": active_students,
            "active_trainings": active_trainings,
            "total_records": total_records,
            "avg_improvement": round(avg_improvement, 1),
        }

    def get_all_data(self):
        """获取所有数据"""
        return {
            "students": self.students,
            "trainings": self.trainings,
            "records": self.records,
        }

    def export_csv(self, filepath):
        """导出所有数据为CSV"""
        import csv
        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["学员姓名", "部门", "岗位", "培训名称",
                               "培训主题", "前测成绩", "后测成绩", "进步幅度",
                               "进步率(%)", "记录日期"])

                for student in self.students:
                    progress = self.get_student_progress(student["id"])
                    if progress:
                        for p in progress:
                            writer.writerow([
                                student["name"],
                                student.get("dept", ""),
                                student.get("position", ""),
                                p["training"]["name"],
                                p["training"]["topic"],
                                p["pre"]["score"],
                                p["post"]["score"],
                                p["improvement"],
                                p["improvement_pct"],
                                p["post"]["date"]
                            ])
            return True
        except Exception as e:
            print(f"导出CSV失败: {e}")
            return False

    def inject_demo_data(self):
        """注入演示数据"""
        # 添加学员
        demo_students = [
            {"name": "张伟", "dept": "销售部", "position": "销售代表"},
            {"name": "李娜", "dept": "技术部", "position": "Java开发"},
            {"name": "王强", "dept": "市场部", "position": "市场专员"},
            {"name": "陈静", "dept": "人事部", "position": "HR主管"},
            {"name": "刘洋", "dept": "财务部", "position": "会计"},
            {"name": "赵敏", "dept": "销售部", "position": "销售经理"},
        ]

        student_ids = []
        for s in demo_students:
            st = self.add_student(**s)
            student_ids.append(st["id"])

        # 添加培训计划
        demo_trainings = [
            {"name": "2024年Q1新员工入职培训", "topic": "新员工入职培训",
             "start_date": "2024-01-15", "end_date": "2024-01-17"},
            {"name": "销售技能提升班", "topic": "销售技巧培训",
             "start_date": "2024-02-01", "end_date": "2024-02-03"},
            {"name": "数字化办公技能培训", "topic": "数字化技能培训",
             "start_date": "2024-03-10", "end_date": "2024-03-12"},
        ]

        training_ids = []
        for t in demo_trainings:
            tr = self.add_training(**t)
            training_ids.append(tr["id"])

        # 添加测评记录（模拟数据）
        import random
        records_data = []

        for sid in student_ids:
            for tid in training_ids:
                # 前测成绩（40-70随机）
                pre_score = random.randint(40, 70)
                # 后测成绩（进步10-35分）
                post_score = min(100, pre_score + random.randint(10, 35))
                records_data.append((sid, tid, "pre", pre_score))
                records_data.append((sid, tid, "post", post_score))

        for r in records_data:
            self.add_record(*r)

        return len(demo_students), len(demo_trainings)

    def clear_all_data(self):
        """清空所有数据"""
        self.students = []
        self.trainings = []
        self.records = []
        self.save_data(config.STUDENTS_FILE, self.students)
        self.save_data(config.TRAININGS_FILE, self.trainings)
        self.save_data(config.RECORDS_FILE, self.records)
        return True
