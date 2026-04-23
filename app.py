# -*- coding: utf-8 -*-
"""
培训效果追踪器 - GUI主程序
Training Effectiveness Tracker
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import config
from data_manager import DataManager
from report import ReportGenerator
import webbrowser

# ==================== 配色 ====================
C = config.THEME


def hex_to_rgb(color):
    """#RRGGBB → (r,g,b)"""
    h = color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


class ToolTip:
    """气泡提示"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip = tk.Toplevel()
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="#2C3E50",
                         foreground="white", padding=(8, 4), font=("Arial", 9),
                         relief=tk.SOLID, borderwidth=0)
        label.pack()

    def hide(self, _=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class ScrollFrame(tk.Frame):
    """自动滚动框架"""
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0,
                                yscrollincrement=20)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                        command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=C["bg"])

        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)


class App:
    """主应用"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{config.APP_NAME} v{config.VERSION}")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.configure(bg=C["bg"])

        self.dm = DataManager()
        self.rg = ReportGenerator(self.dm, config.REPORTS_DIR)

        self.setup_styles()
        self.build_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        """配置ttk样式"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=C["bg"])
        style.configure("Card.TFrame", background=C["card_bg"],
                        relief=tk.FLAT, borderwidth=0)
        style.configure("Header.TLabel", background=C["primary"],
                        foreground="white", font=("Arial", 16, "bold"), padding=15)
        style.configure("Title.TLabel", background=C["bg"],
                        foreground=C["primary"], font=("Arial", 13, "bold"))
        style.configure("Subtitle.TLabel", background=C["bg"],
                        foreground=C["dark"], font=("Arial", 11))
        style.configure("TButton", font=("Arial", 10), padding=(10, 6))
        style.configure("Primary.TButton", font=("Arial", 10, "bold"),
                        background=C["primary"], foreground="white")
        style.configure("Success.TButton", font=("Arial", 10),
                        background=C["success"], foreground="white")
        style.configure("Danger.TButton", font=("Arial", 10),
                        background=C["danger"], foreground="white")
        style.configure("TLabel", background=C["bg"], font=("Arial", 10))
        style.configure("Field.TLabel", background=C["bg"], font=("Arial", 9),
                        foreground="#666")
        style.configure("TCheckbutton", background=C["bg"], font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10))
        style.configure("TCombobox", font=("Arial", 10))
        style.configure("Treeview", font=("Arial", 10), rowheight=28,
                        background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"),
                        background=C["primary"], foreground="white")

    def build_ui(self):
        """构建UI"""
        # 顶部标题栏
        header = tk.Frame(self.root, bg=C["primary"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=f"📊 {config.APP_NAME}",
                bg=C["primary"], fg="white",
                font=("Arial", 18, "bold")).pack(side=tk.LEFT, padx=20)

        tk.Label(header, text=f"Training Effectiveness Tracker | v{config.VERSION}",
                bg=C["primary"], fg="rgba(255,255,255,0.7)",
                font=("Arial", 9)).pack(side=tk.LEFT, padx=10)

        btn_frame = tk.Frame(header, bg=C["primary"])
        btn_frame.pack(side=tk.RIGHT, padx=15)

        ttk.Button(btn_frame, text="🎭 演示数据", style="TButton",
                   command=self.inject_demo).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="📤 导出CSV", style="TButton",
                   command=self.export_csv).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="🗑️ 清空数据", style="TButton",
                   command=self.clear_data).pack(side=tk.LEFT, padx=3)

        # 主内容区（Notebook）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_dashboard = ScrollFrame(self.notebook)
        self.tab_students = ScrollFrame(self.notebook)
        self.tab_trainings = ScrollFrame(self.tab_students.inner)
        self.tab_records = ScrollFrame(self.notebook)
        self.tab_reports = ScrollFrame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="📊 仪表盘")
        self.notebook.add(self.tab_students, text="👥 学员管理")
        self.notebook.add(self.tab_trainings, text="📚 培训管理")
        self.notebook.add(self.tab_records, text="📝 测评记录")
        self.notebook.add(self.tab_reports, text="📈 报告生成")

        # 构建各Tab内容
        self.build_dashboard()
        self.build_students_tab()
        self.build_trainings_tab()
        self.build_records_tab()
        self.build_reports_tab()

    # ==================== 仪表盘 Tab ====================

    def build_dashboard(self):
        """仪表盘内容"""
        f = self.tab_dashboard.inner
        f.configure(bg=C["bg"])

        # KPI区
        kpi_frame = tk.Frame(f, bg=C["bg"])
        kpi_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        self.kpi_labels = {}
        kpis = [
            ("👥 在册学员", "active_students", C["primary"]),
            ("📚 进行中培训", "active_trainings", C["secondary"]),
            ("📝 测评记录", "total_records", C["purple"]),
            ("📈 平均进步率", "avg_improvement", C["success"]),
        ]
        for title, key, color in kpis:
            card = tk.Frame(kpi_frame, bg="white", relief=tk.FLAT, bd=0,
                           highlightbackground=color, highlightthickness=3)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Label(card, text=title, bg="white", fg="#888",
                    font=("Arial", 10)).pack(pady=(12, 0))
            val_lbl = tk.Label(card, text="--", bg="white", fg=color,
                              font=("Arial", 26, "bold"))
            val_lbl.pack(pady=5)
            self.kpi_labels[key] = val_lbl
            tk.Label(card, text="", bg="white", height=1).pack()

        # 最近活动
        tk.Label(f, text="📌 最近测评记录", font=("Arial", 12, "bold"),
                bg=C["bg"], fg=C["primary"]).pack(anchor="w", padx=15, pady=(15, 5))

        self.dashboard_tree = ttk.Treeview(f, columns=("name", "training",
                    "type", "score", "date"), show="headings",
                    style="Treeview", height=8)
        for col, text, w in [("name", "学员", 100), ("training", "培训", 180),
                              ("type", "类型", 80), ("score", "分数", 80),
                              ("date", "日期", 110)]:
            self.dashboard_tree.heading(col, text=text)
            self.dashboard_tree.column(col, width=w, anchor="center")

        self.dashboard_tree.pack(fill=tk.X, padx=15, pady=5)

        # 刷新按钮
        tk.Frame(f, bg=C["bg"], height=10).pack()
        btn_row = tk.Frame(f, bg=C["bg"])
        btn_row.pack()
        ttk.Button(btn_row, text="🔄 刷新数据", command=self.refresh_dashboard).pack(side=tk.LEFT, padx=5)

        self.refresh_dashboard()

    def refresh_dashboard(self):
        """刷新仪表盘"""
        stats = self.dm.get_dashboard_stats()
        self.kpi_labels["active_students"].config(text=str(stats["active_students"]))
        self.kpi_labels["active_trainings"].config(text=str(stats["active_trainings"]))
        self.kpi_labels["total_records"].config(text=str(stats["total_records"]))
        self.kpi_labels["avg_improvement"].config(text=f"{stats['avg_improvement']:.1f}%")

        # 刷新最近记录
        for row in self.dashboard_tree.get_children():
            self.dashboard_tree.delete(row)

        for record in sorted(self.dm.records, key=lambda x: x["created_at"],
                            reverse=True)[:15]:
            student = self.dm.get_student(record["student_id"])
            training = self.dm.get_training(record["training_id"])
            type_map = {"pre": "前测", "post": "后测", "milestone": "里程碑"}
            self.dashboard_tree.insert("", tk.END, values=(
                student["name"] if student else record["student_id"],
                (training["name"] if training else record["training_id"])[:20],
                type_map.get(record["type"], record["type"]),
                f"{record['score']:.0f}",
                record["date"]
            ))

    # ==================== 学员管理 Tab ====================

    def build_students_tab(self):
        """学员管理内容"""
        f = self.tab_students.inner
        f.configure(bg=C["bg"])

        # 工具栏
        toolbar = tk.Frame(f, bg="white", relief=tk.FLAT)
        toolbar.pack(fill=tk.X, padx=10, pady=(5, 0))
        toolbar.configure(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(toolbar, text="👥 学员列表", bg="white", fg=C["primary"],
                font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10, pady=8)
        ttk.Button(toolbar, text="➕ 添加学员", style="TButton",
                  command=self.add_student_dialog).pack(side=tk.LEFT, padx=5)

        # 搜索
        search_frame = tk.Frame(toolbar, bg="white")
        search_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(search_frame, text="🔍 搜索:", bg="white").pack(side=tk.LEFT)
        self.student_search = ttk.Entry(search_frame, width=20)
        self.student_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.filter_students).pack(side=tk.LEFT)
        self.student_search.bind("<Return>", lambda e: self.filter_students())

        # 学员表格
        tree_frame = tk.Frame(f, bg="white")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree_frame.configure(highlightbackground=C["border"], highlightthickness=1)

        cols = ("id", "name", "dept", "position", "email", "created", "status")
        self.students_tree = ttk.Treeview(tree_frame, columns=cols,
                                          show="headings", height=12)
        col_defs = [("id", 60, "center"), ("name", 80, "center"),
                    ("dept", 100, "center"), ("position", 100, "center"),
                    ("email", 150, "center"), ("created", 100, "center"),
                    ("status", 80, "center")]
        col_widths = {"id": 60, "name": 80, "dept": 100, "position": 100,
                      "email": 150, "created": 100, "status": 80}
        for col, text, anchor in col_defs:
            self.students_tree.heading(col, text=text)
            self.students_tree.column(col, width=col_widths[col], anchor=anchor)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=vsb.set)
        self.students_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.students_tree.bind("<Double-Button-1>", lambda e: self.edit_student())

        # 操作按钮
        btn_bar = tk.Frame(f, bg="white")
        btn_bar.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_bar, text="✏️ 编辑", command=self.edit_student).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="🗑️ 删除", style="TButton",
                  command=self.delete_student).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="📄 个人报告", command=self.gen_student_report_from_list).pack(side=tk.LEFT, padx=5)

        self.students_all = []  # 保存过滤前的全部学员
        self.refresh_students()

        # 培训管理子Tab
        self.tab_trainings.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def refresh_students(self):
        """刷新学员列表"""
        for row in self.students_tree.get_children():
            self.students_tree.delete(row)
        self.students_all = self.dm.students[:]
        for s in self.students_all:
            status_map = {"active": "✅ 活跃", "inactive": "❌ 停用"}
            self.students_tree.insert("", tk.END, values=(
                s["id"], s["name"], s.get("dept", ""), s.get("position", ""),
                s.get("email", ""), s["created_at"],
                status_map.get(s.get("status"), "✅ 活跃")
            ))

    def filter_students(self):
        """搜索过滤"""
        keyword = self.student_search.get().strip().lower()
        for row in self.students_tree.get_children():
            self.students_tree.delete(row)
        if not keyword:
            data = self.students_all
        else:
            data = [s for s in self.students_all
                    if keyword in s["name"].lower()
                    or keyword in s.get("dept", "").lower()
                    or keyword in s.get("position", "").lower()]
        for s in data:
            self.students_tree.insert("", tk.END, values=(
                s["id"], s["name"], s.get("dept", ""), s.get("position", ""),
                s.get("email", ""), s["created_at"], "✅ 活跃"
            ))

    def add_student_dialog(self):
        """添加学员弹窗"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加学员")
        dialog.geometry("400x320")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=C["bg"])

        fields = [("姓名 *", "name"), ("部门", "dept"),
                  ("岗位", "position"), ("邮箱", "email")]
        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(dialog, text=label, bg=C["bg"], font=("Arial", 10)).grid(
                row=i, column=0, sticky="e", padx=10, pady=8)
            entries[key] = ttk.Entry(dialog, width=30)
            entries[key].grid(row=i, column=1, padx=10, pady=8)

        def do_add():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showwarning("提示", "姓名不能为空")
                return
            dept = entries["dept"].get().strip()
            position = entries["position"].get().strip()
            email = entries["email"].get().strip()
            self.dm.add_student(name, dept, position, email)
            self.refresh_students()
            self.refresh_dashboard()
            dialog.destroy()
            messagebox.showinfo("成功", f"学员「{name}」添加成功！")

        tk.Frame(dialog, height=20, bg=C["bg"]).grid(row=len(fields))
        tk.Button(dialog, text="✅ 确认添加", bg=C["success"], fg="white",
                 font=("Arial", 11, "bold"), relief=tk.FLAT, padx=20, pady=8,
                 command=do_add).grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
        tk.Button(dialog, text="取消", bg="#CCC", fg="#333",
                 font=("Arial", 10), relief=tk.FLAT, padx=15, pady=8,
                 command=dialog.destroy).grid(row=len(fields)+2, column=0, columnspan=2, pady=5)

    def edit_student(self):
        """编辑学员"""
        sel = self.students_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择要编辑的学员")
            return
        vals = self.students_tree.item(sel[0])["values"]
        student_id = vals[0]

        dialog = tk.Toplevel(self.root)
        dialog.title("编辑学员")
        dialog.geometry("400x320")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=C["bg"])

        student = self.dm.get_student(student_id)
        fields = [("姓名 *", "name", student["name"]),
                  ("部门", "dept", student.get("dept", "")),
                  ("岗位", "position", student.get("position", "")),
                  ("邮箱", "email", student.get("email", ""))]
        entries = {}
        for i, (label, key, default) in enumerate(fields):
            tk.Label(dialog, text=label, bg=C["bg"], font=("Arial", 10)).grid(
                row=i, column=0, sticky="e", padx=10, pady=8)
            entries[key] = ttk.Entry(dialog, width=30)
            entries[key].insert(0, default)
            entries[key].grid(row=i, column=1, padx=10, pady=8)

        def do_update():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showwarning("提示", "姓名不能为空")
                return
            self.dm.update_student(student_id, name=name,
                dept=entries["dept"].get().strip(),
                position=entries["position"].get().strip(),
                email=entries["email"].get().strip())
            self.refresh_students()
            dialog.destroy()
            messagebox.showinfo("成功", "学员信息已更新！")

        tk.Button(dialog, text="✅ 保存修改", bg=C["success"], fg="white",
                 font=("Arial", 11, "bold"), relief=tk.FLAT, padx=20, pady=8,
                 command=do_update).grid(row=len(fields), column=0, columnspan=2, pady=15)

    def delete_student(self):
        """删除学员"""
        sel = self.students_tree.selection()
        if not sel:
            return
        vals = self.students_tree.item(sel[0])["values"]
        if messagebox.askyesno("确认", f"删除学员「{vals[1]}」？相关测评记录也会被删除。"):
            self.dm.delete_student(vals[0])
            self.refresh_students()
            self.refresh_dashboard()
            messagebox.showinfo("成功", "删除成功！")

    def gen_student_report_from_list(self):
        """从列表生成个人报告"""
        sel = self.students_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择学员")
            return
        vals = self.students_tree.item(sel[0])["values"]
        filepath, name = self.rg.generate_student_report(vals[0])
        if filepath:
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
        else:
            messagebox.showwarning("提示", "该学员暂无完整测评数据（前测+后测）")

    # ==================== 培训管理 Tab ====================

    def build_trainings_tab(self):
        """培训管理内容"""
        f = self.tab_trainings
        f.configure(bg=C["bg"])

        toolbar = tk.Frame(f, bg="white", relief=tk.FLAT)
        toolbar.pack(fill=tk.X, padx=10, pady=(5, 0))
        toolbar.configure(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(toolbar, text="📚 培训计划列表", bg="white", fg=C["primary"],
                font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10, pady=8)
        ttk.Button(toolbar, text="➕ 添加培训", style="TButton",
                  command=self.add_training_dialog).pack(side=tk.LEFT, padx=5)

        tree_frame = tk.Frame(f, bg="white")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree_frame.configure(highlightbackground=C["border"], highlightthickness=1)

        cols = ("id", "name", "topic", "start", "end", "status")
        self.trainings_tree = ttk.Treeview(tree_frame, columns=cols,
                                            show="headings", height=10)
        col_defs = [("id", 60, "center"), ("name", 200, "center"),
                    ("topic", 120, "center"), ("start", 100, "center"),
                    ("end", 100, "center"), ("status", 80, "center")]
        for col, text, anchor in col_defs:
            self.trainings_tree.heading(col, text=text)
            self.trainings_tree.column(col, width={
                "id": 60, "name": 200, "topic": 120,
                "start": 100, "end": 100, "status": 80}[col], anchor=anchor)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                           command=self.trainings_tree.yview)
        self.trainings_tree.configure(yscrollcommand=vsb.set)
        self.trainings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.trainings_tree.bind("<Double-Button-1>", lambda e: self.edit_training())

        btn_bar = tk.Frame(f, bg="white")
        btn_bar.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_bar, text="✏️ 编辑", command=self.edit_training).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="🗑️ 删除", command=self.delete_training).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="📄 班级报告", command=self.gen_training_report_from_list).pack(side=tk.LEFT, padx=5)

        self.refresh_trainings()

    def refresh_trainings(self):
        """刷新培训列表"""
        for row in self.trainings_tree.get_children():
            self.trainings_tree.delete(row)
        for t in self.dm.trainings:
            self.trainings_tree.insert("", tk.END, values=(
                t["id"], t["name"], t["topic"], t["start_date"],
                t["end_date"], "✅ 进行中" if t.get("status") == "active" else "❌ 已结束"
            ))

    def add_training_dialog(self):
        """添加培训弹窗"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加培训计划")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=C["bg"])

        fields = [("培训名称 *", "name"), ("培训主题", "topic"),
                  ("开始日期(YYYY-MM-DD)", "start"), ("结束日期(YYYY-MM-DD)", "end")]
        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(dialog, text=label, bg=C["bg"], font=("Arial", 10)).grid(
                row=i, column=0, sticky="e", padx=10, pady=8)
            entries[key] = ttk.Entry(dialog, width=30)
            entries[key].grid(row=i, column=1, padx=10, pady=8)

        # 主题下拉
        tk.Label(dialog, text="选择预设主题:", bg=C["bg"], font=("Arial", 9)).grid(
            row=len(fields), column=0, sticky="e", padx=10, pady=5)
        topic_var = tk.StringVar()
        topic_cb = ttk.Combobox(dialog, textvariable=topic_var, width=28,
                                values=config.TRAINING_TOPICS, state="readonly")
        topic_cb.grid(row=len(fields), column=1, padx=10, pady=5)
        topic_cb.bind("<<ComboboxSelected>>",
                      lambda e: entries["topic"].delete(0, tk.END)
                      or entries["topic"].insert(0, topic_var.get()))

        def do_add():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showwarning("提示", "培训名称不能为空")
                return
            topic = entries["topic"].get().strip() or "综合培训"
            start = entries["start"].get().strip()
            end = entries["end"].get().strip()
            self.dm.add_training(name, topic, start, end)
            self.refresh_trainings()
            self.refresh_dashboard()
            dialog.destroy()
            messagebox.showinfo("成功", f"培训「{name}」添加成功！")

        tk.Button(dialog, text="✅ 确认添加", bg=C["success"], fg="white",
                 font=("Arial", 11, "bold"), relief=tk.FLAT, padx=20, pady=8,
                 command=do_add).grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
        tk.Button(dialog, text="取消", bg="#CCC", fg="#333",
                 font=("Arial", 10), relief=tk.FLAT, padx=15, pady=8,
                 command=dialog.destroy).grid(row=len(fields)+2, column=0, columnspan=2, pady=5)

    def edit_training(self):
        """编辑培训"""
        sel = self.trainings_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择要编辑的培训")
            return
        vals = self.trainings_tree.item(sel[0])["values"]
        tid = vals[0]
        t = self.dm.get_training(tid)
        if not t:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("编辑培训")
        dialog.geometry("450x280")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=C["bg"])

        fields = [("培训名称 *", "name", t["name"]),
                  ("培训主题", "topic", t["topic"]),
                  ("开始日期", "start", t["start_date"]),
                  ("结束日期", "end", t["end_date"])]
        entries = {}
        for i, (label, key, default) in enumerate(fields):
            tk.Label(dialog, text=label, bg=C["bg"], font=("Arial", 10)).grid(
                row=i, column=0, sticky="e", padx=10, pady=8)
            entries[key] = ttk.Entry(dialog, width=30)
            entries[key].insert(0, default)
            entries[key].grid(row=i, column=1, padx=10, pady=8)

        def do_update():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showwarning("提示", "培训名称不能为空")
                return
            self.dm.update_training(tid, name=name,
                topic=entries["topic"].get().strip(),
                start_date=entries["start"].get().strip(),
                end_date=entries["end"].get().strip())
            self.refresh_trainings()
            dialog.destroy()
            messagebox.showinfo("成功", "培训信息已更新！")

        tk.Button(dialog, text="✅ 保存修改", bg=C["success"], fg="white",
                 font=("Arial", 11, "bold"), relief=tk.FLAT, padx=20, pady=8,
                 command=do_update).grid(row=len(fields), column=0, columnspan=2, pady=15)

    def delete_training(self):
        """删除培训"""
        sel = self.trainings_tree.selection()
        if not sel:
            return
        vals = self.trainings_tree.item(sel[0])["values"]
        if messagebox.askyesno("确认", f"删除培训「{vals[1]}」？相关测评记录也会被删除。"):
            self.dm.delete_training(vals[0])
            self.refresh_trainings()
            self.refresh_dashboard()
            messagebox.showinfo("成功", "删除成功！")

    def gen_training_report_from_list(self):
        """从列表生成班级报告"""
        sel = self.trainings_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择培训")
            return
        vals = self.trainings_tree.item(sel[0])["values"]
        filepath, name = self.rg.generate_training_report(vals[0])
        if filepath:
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
        else:
            messagebox.showwarning("提示", name)

    # ==================== 测评记录 Tab ====================

    def build_records_tab(self):
        """测评记录内容"""
        f = self.tab_records.inner
        f.configure(bg=C["bg"])

        # 筛选区
        filter_frame = tk.Frame(f, bg="white")
        filter_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        filter_frame.configure(highlightbackground=C["border"], highlightthickness=1)

        tk.Label(filter_frame, text="📝 测评记录管理", bg="white", fg=C["primary"],
                font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=5)

        tk.Label(filter_frame, text="学员:", bg="white").grid(row=1, column=0, sticky="e", padx=5)
        self.record_student_var = tk.StringVar()
        self.record_student_cb = ttk.Combobox(filter_frame, textvariable=self.record_student_var,
                                               width=15, state="readonly")
        self.record_student_cb.grid(row=1, column=1, padx=5, pady=5)
        self.record_student_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_records())

        tk.Label(filter_frame, text="培训:", bg="white").grid(row=1, column=2, sticky="e", padx=5)
        self.record_training_var = tk.StringVar()
        self.record_training_cb = ttk.Combobox(filter_frame, textvariable=self.record_training_var,
                                                 width=20, state="readonly")
        self.record_training_cb.grid(row=1, column=3, padx=5, pady=5)
        self.record_training_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_records())

        tk.Label(filter_frame, text="类型:", bg="white").grid(row=1, column=4, sticky="e", padx=5)
        self.record_type_var = tk.StringVar()
        type_cb = ttk.Combobox(filter_frame, textvariable=self.record_type_var, width=10,
                                values=["全部", "前测", "后测", "里程碑"], state="readonly")
        type_cb.grid(row=1, column=5, padx=5, pady=5)
        type_cb.current(0)
        type_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_records())

        ttk.Button(filter_frame, text="🔄 刷新", command=self.refresh_comboboxes).grid(
            row=1, column=6, padx=10)

        # 记录表格
        tree_frame = tk.Frame(f, bg="white")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree_frame.configure(highlightbackground=C["border"], highlightthickness=1)

        cols = ("id", "student", "training", "type", "score", "notes", "date")
        self.records_tree = ttk.Treeview(tree_frame, columns=cols,
                                          show="headings", height=12)
        col_defs = [("id", 60, "center"), ("student", 80, "center"),
                    ("training", 150, "center"), ("type", 60, "center"),
                    ("score", 60, "center"), ("notes", 150, "center"),
                    ("date", 100, "center")]
        for col, text, anchor in col_defs:
            self.records_tree.heading(col, text=text)
            self.records_tree.column(col, width={
                "id": 60, "student": 80, "training": 150,
                "type": 60, "score": 60, "notes": 150, "date": 100}[col], anchor=anchor)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                           command=self.records_tree.yview)
        self.records_tree.configure(yscrollcommand=vsb.set)
        self.records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮行
        btn_bar = tk.Frame(f, bg="white")
        btn_bar.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_bar, text="➕ 添加测评记录", style="Success.TButton",
                  command=self.add_record_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="🗑️ 删除记录", command=self.delete_record).pack(side=tk.LEFT, padx=5)

        self.refresh_comboboxes()
        self.refresh_records()

    def refresh_comboboxes(self):
        """刷新下拉框"""
        students = ["全部"] + [s["name"] for s in self.dm.students]
        trainings = ["全部"] + [t["name"][:20] for t in self.dm.trainings]
        self.record_student_cb["values"] = students
        self.record_training_cb["values"] = trainings
        if students:
            self.record_student_cb.current(0)
        if trainings:
            self.record_training_cb.current(0)

    def refresh_records(self):
        """刷新记录列表"""
        for row in self.records_tree.get_children():
            self.records_tree.delete(row)

        filtered = self.dm.records[:]
        student_filter = self.record_student_var.get()
        training_filter = self.record_training_var.get()
        type_filter = self.record_type_var.get()

        if student_filter and student_filter != "全部":
            sid = next((s["id"] for s in self.dm.students if s["name"] == student_filter), None)
            if sid:
                filtered = [r for r in filtered if r["student_id"] == sid]

        if training_filter and training_filter != "全部":
            tid = next((t["id"] for t in self.dm.trainings
                       if t["name"].startswith(training_filter)), None)
            if tid:
                filtered = [r for r in filtered if r["training_id"] == tid]

        if type_filter and type_filter != "全部":
            type_map = {"前测": "pre", "后测": "post", "里程碑": "milestone"}
            t = type_map.get(type_filter, "")
            if t:
                filtered = [r for r in filtered if r["type"] == t]

        type_map_cn = {"pre": "前测", "post": "后测", "milestone": "里程碑"}
        for r in sorted(filtered, key=lambda x: x["created_at"], reverse=True):
            student = self.dm.get_student(r["student_id"])
            training = self.dm.get_training(r["training_id"])
            self.records_tree.insert("", tk.END, values=(
                r["id"],
                student["name"] if student else r["student_id"],
                (training["name"] if training else r["training_id"])[:20],
                type_map_cn.get(r["type"], r["type"]),
                f"{r['score']:.0f}",
                r.get("notes", "")[:20],
                r["date"]
            ))

    def filter_records(self):
        """过滤记录"""
        self.refresh_records()

    def add_record_dialog(self):
        """添加测评记录"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加测评记录")
        dialog.geometry("420x360")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=C["bg"])

        tk.Label(dialog, text="👤 学员 *", bg=C["bg"], font=("Arial", 10)).grid(
            row=0, column=0, sticky="e", padx=10, pady=8)
        student_var = tk.StringVar()
        student_cb = ttk.Combobox(dialog, textvariable=student_var, width=28,
                                   values=[s["name"] for s in self.dm.students], state="readonly")
        student_cb.grid(row=0, column=1, padx=10, pady=8)

        tk.Label(dialog, text="📚 培训 *", bg=C["bg"], font=("Arial", 10)).grid(
            row=1, column=0, sticky="e", padx=10, pady=8)
        training_var = tk.StringVar()
        training_cb = ttk.Combobox(dialog, textvariable=training_var, width=28,
                                    values=[t["name"][:25] for t in self.dm.trainings], state="readonly")
        training_cb.grid(row=1, column=1, padx=10, pady=8)

        tk.Label(dialog, text="📝 测评类型 *", bg=C["bg"], font=("Arial", 10)).grid(
            row=2, column=0, sticky="e", padx=10, pady=8)
        type_var = tk.StringVar()
        type_cb = ttk.Combobox(dialog, textvariable=type_var, width=28,
                                values=["前测(pre)", "后测(post)", "里程碑(milestone)"], state="readonly")
        type_cb.grid(row=2, column=1, padx=10, pady=8)

        tk.Label(dialog, text="⭐ 分数(0-100) *", bg=C["bg"], font=("Arial", 10)).grid(
            row=3, column=0, sticky="e", padx=10, pady=8)
        score_entry = ttk.Entry(dialog, width=30)
        score_entry.grid(row=3, column=1, padx=10, pady=8)

        tk.Label(dialog, text="📋 备注", bg=C["bg"], font=("Arial", 10)).grid(
            row=4, column=0, sticky="e", padx=10, pady=8)
        notes_entry = ttk.Entry(dialog, width=30)
        notes_entry.grid(row=4, column=1, padx=10, pady=8)

        def do_add():
            student_name = student_var.get().strip()
            training_name = training_var.get().strip()
            type_str = type_var.get().strip()
            score_str = score_entry.get().strip()
            notes = notes_entry.get().strip()

            if not all([student_name, training_name, type_str, score_str]):
                messagebox.showwarning("提示", "请填写所有必填项")
                return

            try:
                score = float(score_str)
                if not 0 <= score <= 100:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("提示", "分数必须在0-100之间")
                return

            type_map = {"前测": "pre", "后测": "post", "里程碑": "milestone"}
            type_code = type_map.get(type_str.split("(")[0].strip(), "pre")

            sid = next((s["id"] for s in self.dm.students if s["name"] == student_name), None)
            tid = next((t["id"] for t in self.dm.trainings
                       if t["name"].startswith(training_name)), None)

            if not sid or not tid:
                messagebox.showerror("错误", "学员或培训不存在")
                return

            self.dm.add_record(sid, tid, type_code, score, notes)
            self.refresh_records()
            self.refresh_dashboard()
            dialog.destroy()
            messagebox.showinfo("成功", "测评记录添加成功！")

        tk.Button(dialog, text="✅ 确认添加", bg=C["success"], fg="white",
                 font=("Arial", 11, "bold"), relief=tk.FLAT, padx=20, pady=8,
                 command=do_add).grid(row=5, column=0, columnspan=2, pady=15)

    def delete_record(self):
        """删除记录"""
        sel = self.records_tree.selection()
        if not sel:
            return
        vals = self.records_tree.item(sel[0])["values"]
        if messagebox.askyesno("确认", f"删除这条测评记录？"):
            self.dm.delete_record(vals[0])
            self.refresh_records()
            self.refresh_dashboard()
            messagebox.showinfo("成功", "删除成功！")

    # ==================== 报告生成 Tab ====================

    def build_reports_tab(self):
        """报告生成内容"""
        f = self.tab_reports.inner
        f.configure(bg=C["bg"])

        # 个人报告区
        card1 = tk.Frame(f, bg="white", relief=tk.FLAT)
        card1.pack(fill=tk.X, padx=15, pady=(10, 5))
        card1.configure(highlightbackground=C["primary"], highlightthickness=2)

        tk.Label(card1, text="📄 个人进步报告", bg="white", fg=C["primary"],
                font=("Arial", 13, "bold")).pack(anchor="w", padx=15, pady=(12, 5))
        tk.Label(card1, text="选择学员 → 生成包含前后测对比、进步图表、个人建议的HTML报告",
                bg="white", fg="#888", font=("Arial", 10)).pack(anchor="w", padx=15)

        row1 = tk.Frame(card1, bg="white")
        row1.pack(fill=tk.X, padx=15, pady=10)
        self.report_student_var = tk.StringVar()
        self.report_student_cb = ttk.Combobox(row1, textvariable=self.report_student_var,
                                               width=25, state="readonly")
        self.report_student_cb.pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="🖨️ 生成个人报告",
                  command=self.gen_personal_report).pack(side=tk.LEFT, padx=5)

        # 班级报告区
        card2 = tk.Frame(f, bg="white", relief=tk.FLAT)
        card2.pack(fill=tk.X, padx=15, pady=10)
        card2.configure(highlightbackground=C["secondary"], highlightthickness=2)

        tk.Label(card2, text="📚 班级汇总报告", bg="white", fg=C["secondary"],
                font=("Arial", 13, "bold")).pack(anchor="w", padx=15, pady=(12, 5))
        tk.Label(card2, text="选择培训 → 生成包含班级整体进步率、达标率、建议的HTML报告",
                bg="white", fg="#888", font=("Arial", 10)).pack(anchor="w", padx=15)

        row2 = tk.Frame(card2, bg="white")
        row2.pack(fill=tk.X, padx=15, pady=10)
        self.report_training_var = tk.StringVar()
        self.report_training_cb = ttk.Combobox(row2, textvariable=self.report_training_var,
                                               width=30, state="readonly")
        self.report_training_cb.pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="🖨️ 生成班级报告",
                  command=self.gen_class_report).pack(side=tk.LEFT, padx=5)

        # 统计卡片
        stats_frame = tk.Frame(f, bg=C["bg"])
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        tk.Label(stats_frame, text="📈 培训效果总览", bg=C["bg"], fg=C["primary"],
                font=("Arial", 13, "bold")).pack(anchor="w", pady=(10, 5))

        self.stats_tree = ttk.Treeview(stats_frame, columns=("name", "topic", "students",
                    "pre", "post", "improvement", "rate", "qualified"),
                    show="headings", height=10)
        col_defs = [("name", "培训名称", 180), ("topic", "主题", 100),
                    ("students", "人数", 60), ("pre", "前测均分", 80),
                    ("post", "后测均分", 80), ("improvement", "进步分", 80),
                    ("rate", "进步率", 80), ("qualified", "达标率", 80)]
        for col, text, w in col_defs:
            self.stats_tree.heading(col, text=text)
            self.stats_tree.column(col, width=w, anchor="center")
        self.stats_tree.pack(fill=tk.X)

        self.refresh_report_comboboxes()
        self.refresh_training_stats()

    def refresh_report_comboboxes(self):
        """刷新报告下拉框"""
        self.report_student_cb["values"] = [s["name"] for s in self.dm.students]
        self.report_training_cb["values"] = [t["name"][:30] for t in self.dm.trainings]
        self.record_student_cb["values"] = ["全部"] + [s["name"] for s in self.dm.students]
        self.record_training_cb["values"] = ["全部"] + [t["name"][:20] for t in self.dm.trainings]

    def refresh_training_stats(self):
        """刷新培训统计"""
        for row in self.stats_tree.get_children():
            self.stats_tree.delete(row)
        for t in self.dm.trainings:
            stats = self.dm.get_training_stats(t["id"])
            if stats:
                color = "#27AE60" if stats["improvement_pct"] >= 15 else "#E74C3C"
                self.stats_tree.insert("", tk.END, tags=(color,),
                    values=(t["name"][:25], t["topic"], stats["total_students"],
                            f"{stats['pre_avg']:.1f}", f"{stats['post_avg']:.1f}",
                            f"{stats['improvement']:+.1f}",
                            f"{stats['improvement_pct']:+.1f}%",
                            f"{stats['qualified_rate']:.1f}%"))
        self.stats_tree.tag_configure("#27AE60", foreground="#27AE60")
        self.stats_tree.tag_configure("#E74C3C", foreground="#E74C3C")

    def gen_personal_report(self):
        """生成个人报告"""
        name = self.report_student_var.get().strip()
        if not name:
            messagebox.showinfo("提示", "请选择学员")
            return
        sid = next((s["id"] for s in self.dm.students if s["name"] == name), None)
        if not sid:
            messagebox.showerror("错误", "学员不存在")
            return
        filepath, _ = self.rg.generate_student_report(sid)
        if filepath:
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
        else:
            messagebox.showwarning("提示", "该学员暂无完整测评数据")

    def gen_class_report(self):
        """生成班级报告"""
        name = self.report_training_var.get().strip()
        if not name:
            messagebox.showinfo("提示", "请选择培训")
            return
        tid = next((t["id"] for t in self.dm.trainings
                   if t["name"].startswith(name)), None)
        if not tid:
            messagebox.showerror("错误", "培训不存在")
            return
        filepath, _ = self.rg.generate_training_report(tid)
        if filepath:
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
        else:
            messagebox.showwarning("提示", "该培训暂无完整前后测数据")

    # ==================== 全局操作 ====================

    def inject_demo(self):
        """注入演示数据"""
        if messagebox.askyesno("确认", "这将清空现有数据并添加6名学员、3个培训、36条测评记录。是否继续？"):
            self.dm.clear_all_data()
            n, m = self.dm.inject_demo_data()
            self.refresh_all()
            messagebox.showinfo("成功", f"演示数据注入完成！\n{n} 名学员\n{m} 个培训\n{n * m * 2} 条测评记录")

    def export_csv(self):
        """导出CSV"""
        import datetime
        default_name = f"培训效果数据_{datetime.date.today().strftime('%Y%m%d')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV文件", "*.csv")],
            initialfile=default_name)
        if not filepath:
            return
        if self.dm.export_csv(filepath):
            messagebox.showinfo("成功", f"数据已导出至：\n{filepath}")
        else:
            messagebox.showerror("错误", "导出失败，请重试")

    def clear_data(self):
        """清空所有数据"""
        if messagebox.askyesno("⚠️ 危险操作", "确定要清空所有数据吗？此操作不可撤销！"):
            self.dm.clear_all_data()
            self.refresh_all()
            messagebox.showinfo("成功", "所有数据已清空")

    def refresh_all(self):
        """刷新所有Tab"""
        self.refresh_dashboard()
        self.refresh_students()
        self.refresh_trainings()
        self.refresh_comboboxes()
        self.refresh_records()
        self.refresh_report_comboboxes()
        self.refresh_training_stats()

    def on_close(self):
        """关闭窗口"""
        self.root.destroy()

    def run(self):
        """运行应用"""
        self.root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
