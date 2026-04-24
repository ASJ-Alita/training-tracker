# -*- coding: utf-8 -*-
"""
培训效果追踪器 - 单元测试
测试数据管理、统计计算、配置模块
"""
import os
import sys
import json
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def data_dir(tmp_path):
    """创建临时数据目录，测试结束后自动清理"""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return str(test_dir)


class MockConfig:
    """模拟 config 模块，使用临时目录"""
    DATA_DIR = ""
    STUDENTS_FILE = ""
    TRAININGS_FILE = ""
    RECORDS_FILE = ""
    REPORTS_DIR = ""
    VERSION = "1.0.0"
    APP_NAME = "培训效果追踪器"


@pytest.fixture
def dm(data_dir, monkeypatch):
    """创建使用临时目录的 DataManager 实例"""
    cfg = MockConfig()
    cfg.DATA_DIR = data_dir
    cfg.STUDENTS_FILE = os.path.join(data_dir, "students.json")
    cfg.TRAININGS_FILE = os.path.join(data_dir, "trainings.json")
    cfg.RECORDS_FILE = os.path.join(data_dir, "records.json")

    # 替换 data_manager 模块中的 config 引用
    import data_manager
    monkeypatch.setattr(data_manager, "config", cfg)

    dm = data_manager.DataManager()
    return dm


# ==================== DataManager: 学员管理 ====================

class TestStudentManagement:
    """学员 CRUD 测试"""

    def test_add_student(self, dm):
        """测试添加学员"""
        student = dm.add_student("张伟", dept="技术部", position="开发")
        assert student["name"] == "张伟"
        assert student["dept"] == "技术部"
        assert student["id"] is not None
        assert len(dm.students) == 1

    def test_add_multiple_students(self, dm):
        """测试添加多个学员"""
        dm.add_student("张伟")
        dm.add_student("李娜")
        dm.add_student("王强")
        assert len(dm.students) == 3

    def test_get_student(self, dm):
        """测试获取学员"""
        student = dm.add_student("张伟", dept="技术部")
        result = dm.get_student(student["id"])
        assert result["name"] == "张伟"
        assert result["dept"] == "技术部"

    def test_get_nonexistent_student(self, dm):
        """测试获取不存在的学员"""
        result = dm.get_student("nonexistent")
        assert result is None

    def test_update_student(self, dm):
        """测试更新学员信息"""
        student = dm.add_student("张伟", dept="技术部")
        updated = dm.update_student(student["id"], dept="市场部", position="经理")
        assert updated["dept"] == "市场部"
        assert updated["position"] == "经理"
        assert dm.get_student(student["id"])["dept"] == "市场部"

    def test_delete_student(self, dm):
        """测试删除学员"""
        student = dm.add_student("张伟")
        dm.delete_student(student["id"])
        assert len(dm.students) == 0
        assert dm.get_student(student["id"]) is None

    def test_delete_student_cascades_records(self, dm):
        """测试删除学员时级联删除相关记录"""
        student = dm.add_student("张伟")
        training = dm.add_training("测试培训", "测试主题", "2024-01-01", "2024-01-02")
        dm.add_record(student["id"], training["id"], "pre", 60)
        dm.add_record(student["id"], training["id"], "post", 80)

        dm.delete_student(student["id"])
        records = dm.get_records_by_student(student["id"])
        assert len(records) == 0


# ==================== DataManager: 培训管理 ====================

class TestTrainingManagement:
    """培训计划 CRUD 测试"""

    def test_add_training(self, dm):
        """测试添加培训计划"""
        training = dm.add_training(
            "新员工入职培训", "新员工入职培训",
            "2024-01-15", "2024-01-17"
        )
        assert training["name"] == "新员工入职培训"
        assert training["topic"] == "新员工入职培训"
        assert training["status"] == "active"

    def test_update_training(self, dm):
        """测试更新培训计划"""
        training = dm.add_training("培训A", "主题A", "2024-01-01", "2024-01-02")
        updated = dm.update_training(training["id"], name="培训B", max_score=150)
        assert updated["name"] == "培训B"
        assert updated["max_score"] == 150

    def test_delete_training(self, dm):
        """测试删除培训计划"""
        training = dm.add_training("培训A", "主题A", "2024-01-01", "2024-01-02")
        dm.delete_training(training["id"])
        assert len(dm.trainings) == 0


# ==================== DataManager: 测评记录 ====================

class TestRecordManagement:
    """测评记录管理测试"""

    def test_add_record(self, dm):
        """测试添加测评记录"""
        student = dm.add_student("张伟")
        training = dm.add_training("培训A", "主题A", "2024-01-01", "2024-01-02")
        record = dm.add_record(student["id"], training["id"], "pre", 65.5)
        assert record["type"] == "pre"
        assert record["score"] == 65.5
        assert record["student_id"] == student["id"]

    def test_get_records_by_student(self, dm):
        """测试按学员获取记录"""
        student = dm.add_student("张伟")
        training = dm.add_training("培训A", "主题A", "2024-01-01", "2024-01-02")
        dm.add_record(student["id"], training["id"], "pre", 60)
        dm.add_record(student["id"], training["id"], "post", 80)
        records = dm.get_records_by_student(student["id"])
        assert len(records) == 2

    def test_get_records_by_training(self, dm):
        """测试按培训获取记录"""
        s1 = dm.add_student("张伟")
        s2 = dm.add_student("李娜")
        training = dm.add_training("培训A", "主题A", "2024-01-01", "2024-01-02")
        dm.add_record(s1["id"], training["id"], "pre", 60)
        dm.add_record(s2["id"], training["id"], "pre", 70)
        records = dm.get_records_by_training(training["id"])
        assert len(records) == 2

    def test_get_student_training_record(self, dm):
        """测试获取学员在某培训的前后测记录"""
        student = dm.add_student("张伟")
        training = dm.add_training("培训A", "主题A", "2024-01-01", "2024-01-02")
        dm.add_record(student["id"], training["id"], "pre", 50)
        dm.add_record(student["id"], training["id"], "post", 80)
        dm.add_record(student["id"], training["id"], "milestone", 90)

        pre, post, milestones = dm.get_student_training_record(student["id"], training["id"])
        assert pre is not None
        assert pre["score"] == 50
        assert post is not None
        assert post["score"] == 80
        assert len(milestones) == 1

    def test_delete_record(self, dm):
        """测试删除记录"""
        student = dm.add_student("张伟")
        training = dm.add_training("培训A", "主题A", "2024-01-01", "2024-01-02")
        record = dm.add_record(student["id"], training["id"], "pre", 60)
        dm.delete_record(record["id"])
        assert len(dm.records) == 0


# ==================== DataManager: 统计分析 ====================

class TestStatistics:
    """统计分析测试"""

    def _setup_complete_training(self, dm):
        """辅助：创建一个完整的培训场景（3个学员，前后测）"""
        students = []
        for name in ["张伟", "李娜", "王强"]:
            students.append(dm.add_student(name))

        training = dm.add_training("销售培训", "销售技巧", "2024-02-01", "2024-02-03")

        # 前测（低分）+ 后测（高分）
        pre_scores = [45, 55, 60]
        post_scores = [75, 85, 90]
        for s, pre, post in zip(students, pre_scores, post_scores):
            dm.add_record(s["id"], training["id"], "pre", pre)
            dm.add_record(s["id"], training["id"], "post", post)

        return students, training

    def test_training_stats(self, dm):
        """测试培训统计数据"""
        students, training = self._setup_complete_training(dm)
        stats = dm.get_training_stats(training["id"])

        assert stats is not None
        assert stats["total_students"] == 3
        assert stats["pre_avg"] == 53.3  # (45+55+60)/3
        assert stats["post_avg"] == 83.3  # (75+85+90)/3
        assert stats["improvement"] > 0
        assert stats["improvement_pct"] > 0

    def test_training_stats_no_records(self, dm):
        """测试无记录时返回 None"""
        training = dm.add_training("空培训", "空主题", "2024-01-01", "2024-01-02")
        stats = dm.get_training_stats(training["id"])
        assert stats is None

    def test_student_progress(self, dm):
        """测试学员进步数据"""
        students, training = self._setup_complete_training(dm)
        progress = dm.get_student_progress(students[0]["id"])

        assert len(progress) == 1
        assert progress[0]["improvement"] == 30.0  # 75 - 45
        assert progress[0]["improvement_pct"] > 50  # (30/45)*100

    def test_dashboard_stats(self, dm):
        """测试仪表盘统计"""
        self._setup_complete_training(dm)
        stats = dm.get_dashboard_stats()

        assert stats["active_students"] == 3
        assert stats["active_trainings"] == 1
        assert stats["total_records"] == 6  # 3 前测 + 3 后测
        assert stats["avg_improvement"] > 0

    def test_qualified_rate(self, dm):
        """测试达标率计算（后测 >= 75 分为达标）"""
        self._setup_complete_training(dm)
        training_id = dm.trainings[0]["id"]
        stats = dm.get_training_stats(training_id)
        assert stats["qualified_rate"] == 100.0  # 后测都 >= 75


# ==================== DataManager: 数据操作 ====================

class TestDataOperations:
    """数据导入导出测试"""

    def test_inject_demo_data(self, dm):
        """测试注入演示数据"""
        count_students, count_trainings = dm.inject_demo_data()
        assert count_students == 6
        assert count_trainings == 3
        assert len(dm.records) >= 30  # 6学员 * 3培训 * 2(前后测) = 36

    def test_clear_all_data(self, dm):
        """测试清空所有数据"""
        dm.inject_demo_data()
        dm.clear_all_data()
        assert len(dm.students) == 0
        assert len(dm.trainings) == 0
        assert len(dm.records) == 0

    def test_export_csv(self, dm, tmp_path):
        """测试 CSV 导出"""
        dm.inject_demo_data()
        csv_path = tmp_path / "export.csv"
        result = dm.export_csv(str(csv_path))
        assert result is True
        assert os.path.exists(csv_path)

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            assert "学员姓名" in content  # CSV 表头
            assert "张伟" in content  # 演示数据

    def test_get_all_data(self, dm):
        """测试获取所有数据"""
        dm.inject_demo_data()
        all_data = dm.get_all_data()
        assert "students" in all_data
        assert "trainings" in all_data
        assert "records" in all_data


# ==================== config 测试 ====================

class TestConfig:
    """配置模块测试"""

    def test_theme_colors(self):
        """测试主题配色"""
        import config
        assert config.THEME["primary"] == "#2C5F8A"
        assert config.THEME["success"] == "#27AE60"

    def test_progress_thresholds(self):
        """测试进步阈值"""
        import config
        assert config.PROGRESS_THRESHOLDS["excellent"] >= config.PROGRESS_THRESHOLDS["good"]

    def test_score_levels(self):
        """测试评分标准"""
        import config
        assert len(config.SCORE_LEVELS) == 4
        assert config.SCORE_LEVELS[0][0] == 90  # 优秀 >= 90

    def test_training_topics(self):
        """测试预设培训主题"""
        import config
        assert len(config.TRAINING_TOPICS) >= 10
        assert "新员工入职培训" in config.TRAINING_TOPICS

    def test_version(self):
        """测试版本号"""
        import config
        assert config.VERSION == "1.0.0"
        assert config.APP_NAME == "培训效果追踪器"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
