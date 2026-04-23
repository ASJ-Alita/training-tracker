# -*- coding: utf-8 -*-
"""
培训效果追踪器 - HTML报告生成模块
生成个人进步报告和班级汇总报告
"""

import os
import datetime
from charts import (
    bar_chart, progress_comparison_chart, improvement_distribution_chart,
    pie_chart_for_scores, save_fig, get_color_for_improvement, get_level_label
)
import config


class ReportGenerator:
    """HTML报告生成器"""

    def __init__(self, data_manager, reports_dir="reports"):
        self.dm = data_manager
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def _get_css(self):
        """内嵌CSS样式"""
        return """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
                   background: #F4F7FA; color: #2C3E50; line-height: 1.6; }
            .container { max-width: 1100px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #2C5F8A, #4A90D9);
                      color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px;
                      text-align: center; }
            .header h1 { font-size: 26px; margin-bottom: 8px; }
            .header p { opacity: 0.85; font-size: 14px; }
            .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
            .kpi-card { background: white; border-radius: 10px; padding: 20px; text-align: center;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #4A90D9; }
            .kpi-card.success { border-top-color: #27AE60; }
            .kpi-card.warning { border-top-color: #F39C12; }
            .kpi-card.danger { border-top-color: #E74C3C; }
            .kpi-value { font-size: 28px; font-weight: bold; color: #2C5F8A; margin: 8px 0; }
            .kpi-label { font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
            .section { background: white; border-radius: 10px; padding: 25px; margin-bottom: 20px;
                       box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
            .section-title { font-size: 18px; font-weight: bold; color: #2C5F8A;
                             margin-bottom: 20px; padding-bottom: 10px;
                             border-bottom: 2px solid #ECF0F1; }
            .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .chart-grid.single { grid-template-columns: 1fr; }
            .chart-item { text-align: center; }
            .chart-item img { max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .chart-caption { font-size: 13px; color: #888; margin-top: 8px; }
            table { width: 100%; border-collapse: collapse; }
            th { background: #2C5F8A; color: white; padding: 12px 15px; text-align: left; font-size: 13px; }
            td { padding: 10px 15px; border-bottom: 1px solid #ECF0F1; font-size: 13px; }
            tr:hover { background: #F8F9FA; }
            .tag { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; }
            .tag-success { background: #D4EDDA; color: #155724; }
            .tag-warning { background: #FFF3CD; color: #856404; }
            .tag-danger { background: #F8D7DA; color: #721C24; }
            .tag-info { background: #D1ECF1; color: #0C5460; }
            .progress-bar-wrap { background: #ECF0F1; border-radius: 8px; height: 20px; overflow: hidden; }
            .progress-bar { height: 100%; border-radius: 8px; transition: width 0.5s ease; color: white;
                            text-align: center; font-size: 11px; line-height: 20px; font-weight: bold; }
            .suggestion-box { background: #F8F9FA; border-left: 4px solid #4A90D9; padding: 15px 20px;
                              border-radius: 0 8px 8px 0; margin: 10px 0; }
            .suggestion-box h4 { color: #2C5F8A; margin-bottom: 8px; }
            .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .footer { text-align: center; color: #999; font-size: 12px; padding: 20px 0; }
            @media print { body { background: white; } .section { box-shadow: none; border: 1px solid #ddd; } }
            @media (max-width: 768px) { .kpi-row { grid-template-columns: 1fr 1fr; } .chart-grid { grid-template-columns: 1fr; } .two-col { grid-template-columns: 1fr; } }
        </style>
        """

    def _level_tag(self, score, improvement):
        """生成等级标签"""
        if improvement >= 30 or score >= 90:
            cls, text = "success", "优秀 ⭐"
        elif improvement >= 15 or score >= 75:
            cls, text = "info", "良好 ✓"
        elif improvement >= 5 or score >= 60:
            cls, text = "warning", "及格 ⚡"
        else:
            cls, text = "danger", "待提升 ⚠"
        return f'<span class="tag tag-{cls}">{text}</span>'

    def _progress_bar(self, value, max_val=100, color=None):
        """生成进度条HTML"""
        pct = min(100, max(0, value / max_val * 100))
        if color is None:
            color = get_color_for_improvement(value)
        return f'''
        <div class="progress-bar-wrap">
            <div class="progress-bar" style="width:{pct:.1f}%; background:{color};">
                {value:.1f}%
            </div>
        </div>'''

    def generate_student_report(self, student_id):
        """生成个人进步报告"""
        student = self.dm.get_student(student_id)
        if not student:
            return None, "学员不存在"

        progress = self.dm.get_student_progress(student_id)
        stats = self.dm.get_dashboard_stats()

        # 生成图表
        chart_paths = {}
        if progress:
            # 前后测对比图
            names = [p["training"]["name"][:10] for p in progress]
            pre_scores = [p["pre"]["score"] for p in progress]
            post_scores = [p["post"]["score"] for p in progress]
            fig1 = progress_comparison_chart(pre_scores, post_scores, names,
                                             f"{student['name']} - 前后测成绩对比")
            chart_paths["comparison"] = save_fig(fig1, f"{self.reports_dir}/{student_id}_comparison.png")

            # 进步幅度分布
            improvements = [p["improvement_pct"] for p in progress]
            fig2 = improvement_distribution_chart(improvements, "各培训进步幅度")
            chart_paths["improvement"] = save_fig(fig2, f"{self.reports_dir}/{student_id}_improvement.png")

            # 成绩分布饼图
            all_scores = pre_scores + post_scores
            fig3 = pie_chart_for_scores(all_scores, title="历次成绩分布")
            chart_paths["pie"] = save_fig(fig3, f"{self.reports_dir}/{student_id}_pie.png")

        # 生成建议
        suggestions = []
        if progress:
            avg_improvement = sum(p["improvement_pct"] for p in progress) / len(progress)
            if avg_improvement >= 30:
                suggestions.append("🎉 该学员进步显著，建议作为培训标杆案例分享。")
            elif avg_improvement >= 15:
                suggestions.append("📈 学员整体进步良好，可适当增加进阶内容挑战。")
            elif avg_improvement >= 5:
                suggestions.append("⚠️ 进步幅度有限，建议增加实操练习和课后辅导。")
            else:
                suggestions.append("🔴 进步不明显，需要深入分析原因并调整培训策略。")

            weak_areas = [p for p in progress if p["improvement_pct"] < 15]
            if weak_areas:
                topics = [p["training"]["topic"] for p in weak_areas]
                suggestions.append(f"📌 薄弱环节：{', '.join(topics)}，建议针对性补训。")

        if not suggestions:
            suggestions.append("📋 暂无足够的测评数据，建议先完成至少一次完整培训前后测。")

        # 计算总进步
        total_improvement = 0
        if progress:
            total_improvement = sum(p["improvement_pct"] for p in progress) / len(progress)
        pre_avg = sum(p["pre"]["score"] for p in progress) / len(progress) if progress else 0
        post_avg = sum(p["post"]["score"] for p in progress) / len(progress) if progress else 0

        # 生成表格行
        rows_html = ""
        for p in progress:
            rows_html += f"""
            <tr>
                <td>{p['training']['name']}</td>
                <td>{p['training']['topic']}</td>
                <td>{p['pre']['score']:.0f}</td>
                <td>{p['post']['score']:.0f}</td>
                <td>{p['improvement']:+.1f}</td>
                <td>{self._progress_bar(p['improvement_pct'], 50)}</td>
                <td>{self._level_tag(p['post']['score'], p['improvement_pct'])}</td>
            </tr>"""

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{student['name']} - 培训效果追踪报告</title>
    {self._get_css()}
</head>
<body>
<div class="container">
    <!-- 标题区 -->
    <div class="header">
        <h1>👤 个人培训效果追踪报告</h1>
        <p>{student['name']} · {student.get('dept', '未填写部门')} · {student.get('position', '未填写岗位')} · 生成日期：{datetime.date.today()}</p>
    </div>

    <!-- KPI卡片 -->
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">参与培训</div>
            <div class="kpi-value">{len(progress)}</div>
            <div class="kpi-label">个</div>
        </div>
        <div class="kpi-card success">
            <div class="kpi-label">前测均分</div>
            <div class="kpi-value">{pre_avg:.1f}</div>
            <div class="kpi-label">分</div>
        </div>
        <div class="kpi-card success">
            <div class="kpi-label">后测均分</div>
            <div class="kpi-value">{post_avg:.1f}</div>
            <div class="kpi-label">分</div>
        </div>
        <div class="kpi-card {'success' if total_improvement >= 15 else 'warning'}">
            <div class="kpi-label">平均进步率</div>
            <div class="kpi-value">{total_improvement:.1f}%</div>
            <div class="kpi-label">{'↑ 显著' if total_improvement >= 30 else '↑ 良好' if total_improvement >= 15 else '需加强'}</div>
        </div>
    </div>

    <!-- 培训详情表格 -->
    <div class="section">
        <div class="section-title">📋 培训详情</div>
        <table>
            <thead>
                <tr>
                    <th>培训名称</th><th>主题</th><th>前测</th><th>后测</th>
                    <th>进步分</th><th>进步率</th><th>等级</th>
                </tr>
            </thead>
            <tbody>{rows_html or '<tr><td colspan="7" style="text-align:center;color:#999;">暂无数据</td></tr>'}</tbody>
        </table>
    </div>

    <!-- 图表区 -->
    <div class="section">
        <div class="section-title">📊 效果可视化</div>
        <div class="chart-grid{' single' if len(chart_paths) < 2 else ''}">
            {f'<div class="chart-item"><img src="{chart_paths["comparison"]}" alt="前后测对比"><div class="chart-caption">前后测成绩对比</div></div>' if 'comparison' in chart_paths else ''}
            {f'<div class="chart-item"><img src="{chart_paths["improvement"]}" alt="进步幅度"><div class="chart-caption">各培训进步幅度</div></div>' if 'improvement' in chart_paths else ''}
        </div>
        <div class="chart-grid" style="margin-top:15px;">
            {f'<div class="chart-item"><img src="{chart_paths["pie"]}" alt="成绩分布"><div class="chart-caption">历次成绩分布</div></div>' if 'pie' in chart_paths else ''}
        </div>
    </div>

    <!-- 改进建议 -->
    <div class="section">
        <div class="section-title">💡 改进建议</div>
        {"".join(f'<div class="suggestion-box"><h4>建议</h4><p>{s}</p></div>' for s in suggestions)}
    </div>

    <div class="footer">
        <p>{config.APP_NAME} v{config.VERSION} · {datetime.date.today()}</p>
    </div>
</div>
</body>
</html>"""

        filepath = f"{self.reports_dir}/{student_id}_report.html"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return filepath, student["name"]

    def generate_training_report(self, training_id):
        """生成班级/培训汇总报告"""
        training = self.dm.get_training(training_id)
        if not training:
            return None, "培训不存在"

        records = self.dm.get_records_by_training(training_id)
        pres = [r for r in records if r["type"] == "pre"]
        posts = [r for r in records if r["type"] == "post"]
        stats = self.dm.get_training_stats(training_id)

        if not pres or not posts:
            return None, "该培训暂无完整的前后测数据"

        chart_paths = {}

        # 前后测对比图
        student_names = list(set(r["student_id"] for r in pres))
        pre_scores = []
        post_scores = []
        names = []
        for sid in student_names:
            p = next((r for r in pres if r["student_id"] == sid), None)
            po = next((r for r in posts if r["student_id"] == sid), None)
            st = self.dm.get_student(sid)
            if p and po and st:
                pre_scores.append(p["score"])
                post_scores.append(po["score"])
                names.append(st["name"][:4])

        if pre_scores:
            fig1 = progress_comparison_chart(pre_scores, post_scores, names,
                                             f"{training['name']} - 学员前后测对比")
            chart_paths["comparison"] = save_fig(fig1, f"{self.reports_dir}/{training_id}_class_comparison.png")

            # 进步幅度分布
            improvements = [po - pr for pr, po in zip(pre_scores, post_scores)]
            improvement_pcts = [(po - pr) / pr * 100 if pr > 0 else 0 for pr, po in zip(pre_scores, post_scores)]
            fig2 = improvement_distribution_chart(improvement_pcts, "班级进步幅度分布")
            chart_paths["improvement"] = save_fig(fig2, f"{self.reports_dir}/{training_id}_improvement.png")

            # 成绩分布饼图
            fig3 = pie_chart_for_scores(posts, title="后测成绩分布")
            chart_paths["pie"] = save_fig(fig3, f"{self.reports_dir}/{training_id}_pie.png")

        # 生成建议
        suggestions = []
        if stats:
            if stats["improvement_pct"] >= 30:
                suggestions.append(f"🎉 班级整体进步率达 {stats['improvement_pct']}%，培训效果非常显著！")
            elif stats["improvement_pct"] >= 15:
                suggestions.append(f"📈 班级整体进步率 {stats['improvement_pct']}%，培训效果良好。")
            else:
                suggestions.append(f"⚠️ 班级整体进步率 {stats['improvement_pct']}%，需分析原因并优化后续培训。")

            if stats["qualified_rate"] >= 80:
                suggestions.append(f"✅ 达标率 {stats['qualified_rate']}%，大多数学员达到良好水平。")
            elif stats["qualified_rate"] >= 50:
                suggestions.append(f"📊 达标率 {stats['qualified_rate']}%，建议对未达标学员进行补训。")
            else:
                suggestions.append(f"🔴 达标率仅 {stats['qualified_rate']}%，需要全面复盘培训内容和方法。")

        # 表格
        student_ids_true = list(set(r["student_id"] for r in pres))
        rows_html = ""
        for sid, pre, post in zip(student_ids_true, pre_scores, post_scores):
            st = self.dm.get_student(sid)
            if st:
                imp = post - pre
                imp_pct = (imp / pre * 100) if pre > 0 else 0
                rows_html += f"""
                <tr>
                    <td>{st['name']}</td>
                    <td>{st.get('dept', '-')}</td>
                    <td>{pre:.0f}</td>
                    <td>{post:.0f}</td>
                    <td>{imp:+.1f}</td>
                    <td>{self._progress_bar(imp_pct, 50)}</td>
                    <td>{self._level_tag(post, imp_pct)}</td>
                </tr>"""

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{training['name']} - 培训效果汇总报告</title>
    {self._get_css()}
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📚 培训效果汇总报告</h1>
        <p>{training['name']} · {training['topic']} · {training['start_date']} ~ {training['end_date']}<br>生成日期：{datetime.date.today()}</p>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">参训人数</div>
            <div class="kpi-value">{len(pres)}</div>
            <div class="kpi-label">人</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">前测均分</div>
            <div class="kpi-value">{stats['pre_avg'] if stats else '-'}</div>
            <div class="kpi-label">分</div>
        </div>
        <div class="kpi-card success">
            <div class="kpi-label">后测均分</div>
            <div class="kpi-value">{stats['post_avg'] if stats else '-'}</div>
            <div class="kpi-label">分</div>
        </div>
        <div class="kpi-card {'success' if (stats['improvement_pct'] if stats else 0) >= 15 else 'warning'}">
            <div class="kpi-label">平均进步率</div>
            <div class="kpi-value">{stats['improvement_pct'] if stats else '-'}%</div>
            <div class="kpi-label">达标率 {stats['qualified_rate'] if stats else '-'}%</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">👥 学员明细</div>
        <table>
            <thead>
                <tr><th>姓名</th><th>部门</th><th>前测</th><th>后测</th><th>进步分</th><th>进步率</th><th>等级</th></tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">📊 可视化分析</div>
        <div class="chart-grid">
            {f'<div class="chart-item"><img src="{chart_paths["comparison"]}" alt="对比"><div class="chart-caption">学员前后测对比</div></div>' if 'comparison' in chart_paths else ''}
            {f'<div class="chart-item"><img src="{chart_paths["improvement"]}" alt="进步"><div class="chart-caption">进步幅度分布</div></div>' if 'improvement' in chart_paths else ''}
        </div>
        <div class="chart-grid" style="margin-top:15px;">
            {f'<div class="chart-item"><img src="{chart_paths["pie"]}" alt="分布"><div class="chart-caption">后测成绩分布</div></div>' if 'pie' in chart_paths else ''}
        </div>
    </div>

    <div class="section">
        <div class="section-title">💡 培训优化建议</div>
        {"".join(f'<div class="suggestion-box"><p>{s}</p></div>' for s in suggestions)}
    </div>

    <div class="footer">
        <p>{config.APP_NAME} v{config.VERSION} · {datetime.date.today()}</p>
    </div>
</div>
</body>
</html>"""

        filepath = f"{self.reports_dir}/{training_id}_report.html"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return filepath, training["name"]
