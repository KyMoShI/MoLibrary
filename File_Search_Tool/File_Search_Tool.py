import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
import stat
import sys

# 直接使用本地tkcalendar库
from tkcalendar import DateEntry

# 导入历史记录管理模块
from history_manager import HistoryManager

# 获取程序所在目录的绝对路径
APP_DIR = os.path.dirname(os.path.abspath(__file__))

class FileSearchTool:
    def __init__(self, root):
        self.root = root
        self.root.title("文件搜索工具")
        self.root.geometry("800x600")
        
        # 设置全局字体
        self.root.option_add("*Font", "SimHei 10")
        
        self.folder_path = ""
        # 定义中文到英文的筛选条件映射
        self.criteria_mapping = {
            "所有文件": "all_files",
            "所有图片": "all_images",
            "JPEG格式": "jpeg",
            "PNG格式": "png",
            "TIFF格式": "tiff",
            "RAW格式": "raw",
            "PSD格式": "psd",
            "DNG格式": "dng",
            "视频文件": "video",
            "压缩文件": "archive"
        }
        
        # 定义摄影常用文件类型映射
        self.file_types = {
            "所有文件": "*.*",
            "所有图片": "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.tiff;*.tif",
            "JPEG格式": "*.jpg;*.jpeg",
            "PNG格式": "*.png",
            "TIFF格式": "*.tiff;*.tif",
            "RAW格式": "*.cr2;*.cr3;*.nef;*.arw;*.dng;*.rw2;*.orf;*.pef;*.srw;*.raf;*.mos",
            "PSD格式": "*.psd",
            "DNG格式": "*.dng",
            "视频文件": "*.mp4;*.avi;*.mkv;*.mov;*.wmv;*.m4v",
            "压缩文件": "*.zip;*.rar;*.7z;*.tar;*.gz"
        }
        
        # 文件大小单位映射（KB为基准单位）
        self.size_units = {
            "KB": 1,
            "MB": 1024,
            "GB": 1024 * 1024,
            "TB": 1024 * 1024 * 1024
        }
        self.selected_unit = tk.StringVar()
        self.selected_unit.set("KB")  # 默认单位为KB
        
        # 日志相关设置
        # 使用程序所在目录作为基础路径，确保有写入权限
        self.log_folder = os.path.join(APP_DIR, "search_logs")
        # 确保日志文件夹存在
        self.ensure_log_folder_exists()
        
        # 历史记录文件路径，使用程序所在目录
        history_file = os.path.join(APP_DIR, "search_history.json")
        # 初始化历史记录管理器，传递日志文件夹路径和历史记录文件路径
        self.history_manager = HistoryManager(history_file=history_file, log_folder=self.log_folder)
        
        self.create_widgets()
        
    def ensure_log_folder_exists(self):
        """确保日志文件夹存在，不存在则创建"""
        try:
            if not os.path.exists(self.log_folder):
                os.makedirs(self.log_folder)
        except Exception as e:
            print(f"创建日志文件夹失败: {e}")
    
    def write_search_log(self, search_criteria, file_count=0, search_time=0.0, error_message=None):
        """写入搜索日志到文件，支持记录错误信息，优化空间使用"""
        try:
            # 生成日志文件名，使用当前时间戳确保唯一性
            log_filename = f"search_log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}.txt"
            log_path = os.path.join(self.log_folder, log_filename)
            
            # 获取文件类型，转换为英文变量
            file_type = search_criteria.get('file_type', '')
            # 使用映射将中文文件类型转换为英文变量，没有映射则使用原中文
            file_type_en = self.criteria_mapping.get(file_type, file_type)
            
            # 优化1: 使用更紧凑的时间格式
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 优化2: 更紧凑的字段名和值
            folder = search_criteria.get('folder', '')
            date_from = search_criteria.get('date_from', '')
            date_to = search_criteria.get('date_to', '')
            size_min = search_criteria.get('size_min', 0)
            # 不限制文件大小时记录为空字符，而不是空格
            size_max = search_criteria.get('size_max', '') if search_criteria.get('size_max', '') != float("inf") else ''
            
            # 优化3: 简化状态表示
            if error_message:
                status = "F"
                result = error_message
            else:
                status = "S"
                result = f"{file_count},{search_time:.2f}"
            
            # 优化4: 单行CSV格式，减少换行符和分隔符空间
            # 格式: 时间戳,状态,文件夹,日期范围,文件类型,最小大小,最大大小,结果
            log_line = f"{timestamp},{status},{folder},{date_from},{date_to},{file_type_en},{size_min},{size_max},{result}"
            
            # 写入日志文件
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_line)
                
        except Exception as e:
            print(f"Failed to write log: {e}")
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def search_files(self):
        # 记录搜索开始时间
        start_time = datetime.now()
        
        # 清除之前的结果
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取基本搜索条件
        folder = self.folder_entry.get()
        date_from_val = self.date_from_entry.get()
        date_to_val = self.date_to_entry.get()
        selected_type_desc = self.file_type_entry.get()
        size_min_str = self.size_min_entry.get()
        size_max_str = self.size_max_entry.get()
        
        # 构建基本搜索条件字典（用于日志）
        base_criteria = {
            'folder': folder,
            'date_from': date_from_val,
            'date_to': date_to_val,
            'file_type': selected_type_desc,
            'size_min': size_min_str if size_min_str else 0,
            'size_max': size_max_str if size_max_str else "不限制"
        }
        
        # 检查文件夹是否有效
        if not folder or not os.path.exists(folder):
            error_msg = "请选择有效的文件夹"
            messagebox.showerror("错误", error_msg)
            # 写入错误日志
            self.write_search_log(base_criteria, error_message=error_msg)
            return
        
        # 获取日期对象
        try:
            date_from = self.date_from_entry.get_date()
            date_to = self.date_to_entry.get_date()
        except Exception as e:
            error_msg = "日期格式不正确"
            messagebox.showerror("错误", error_msg)
            # 写入错误日志
            self.write_search_log(base_criteria, error_message=error_msg)
            return
        
        # 获取文件类型映射
        file_type = self.file_types[selected_type_desc]
        
        # 解析日期范围
        try:
            # 将date_from转换为datetime对象，时间设为00:00:00
            date_from = datetime.combine(date_from, datetime.min.time())
            # 将date_to转换为datetime对象，时间设为23:59:59
            date_to = datetime.combine(date_to, datetime.max.time())
            
            # 检查时间顺序是否正确
            if date_from > date_to:
                error_msg = "时间顺序错误：开始日期不能晚于结束日期"
                messagebox.showerror("错误", error_msg)
                # 写入错误日志
                self.write_search_log(base_criteria, error_message=error_msg)
                return
        except Exception as e:
            error_msg = "日期格式不正确"
            messagebox.showerror("错误", error_msg)
            # 写入错误日志
            self.write_search_log(base_criteria, error_message=error_msg)
            return
        
        # 解析文件大小范围
        try:
            # 获取当前选择的单位
            current_unit = self.selected_unit.get()
            # 获取单位转换系数
            unit_factor = self.size_units.get(current_unit, 1)
            
            # 将用户输入的大小转换为KB（程序内部使用的基准单位）
            size_min = float(size_min_str) * unit_factor if size_min_str else 0
            size_max = float(size_max_str) * unit_factor if size_max_str else float("inf")
        except ValueError:
            error_msg = "文件大小必须是数字"
            messagebox.showerror("错误", error_msg)
            # 写入错误日志
            self.write_search_log(base_criteria, error_message=error_msg)
            return
        
        # 开始搜索
        file_count = 0
        for root, dirs, files in os.walk(folder):
            for file in files:
                # 检查文件类型
                if not self.match_file_type(file, file_type):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    # 获取文件属性
                    stat_info = os.stat(file_path)
                    
                    # 获取文件大小（KB）
                    size_kb = stat_info.st_size / 1024
                    
                    # 检查文件大小
                    if not (size_min <= size_kb <= size_max):
                        continue
                    
                    # 获取创建时间
                    created_time = datetime.fromtimestamp(stat_info.st_ctime)
                    
                    # 检查创建时间
                    if date_from and created_time < date_from:
                        continue
                    if date_to and created_time > date_to:
                        continue
                    
                    # 获取修改时间
                    modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                    
                    # 获取当前选择的单位
                    current_unit = self.selected_unit.get()
                    # 获取单位转换系数
                    unit_factor = self.size_units.get(current_unit, 1)
                    
                    # 将文件大小转换为当前选择的单位
                    converted_size = size_kb / unit_factor
                    
                    # 添加到结果列表
                    self.tree.insert("", tk.END, values=(
                        file,
                        file_path,
                        f"{converted_size:.2f}",
                        created_time.strftime("%Y-%m-%d %H:%M:%S"),
                        modified_time.strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    
                    file_count += 1
                except Exception as e:
                    continue
        
        # 计算搜索耗时
        search_time = (datetime.now() - start_time).total_seconds()
        
        # 获取当前选择的单位
        current_unit = self.selected_unit.get()
        # 获取单位转换系数
        unit_factor = self.size_units.get(current_unit, 1)
        
        # 构建完整搜索条件（用于历史记录）
        history_criteria = {
            'folder': folder,
            'date_from': date_from.strftime("%Y-%m-%d"),
            'date_to': date_to.strftime("%Y-%m-%d"),
            'file_type': selected_type_desc,
            'size_min': size_min,
            'size_max': size_max  # 历史记录中保留原始的float('inf')
        }
        
        # 保存搜索条件到历史记录（仅当搜索成功时）
        self.history_manager.add_search_history(history_criteria)
        
        # 构建日志专用的搜索条件
        log_criteria = {
            'folder': folder,
            'date_from': date_from.strftime("%Y-%m-%d"),
            'date_to': date_to.strftime("%Y-%m-%d"),
            'file_type': selected_type_desc,
            'size_min': size_min,
            'size_max': size_max if size_max != float("inf") else ''  # 日志中用空字符表示不限制
        }
        
        # 写入搜索日志（成功情况）
        self.write_search_log(log_criteria, file_count, search_time)
        
        messagebox.showinfo("搜索完成", f"共找到 {file_count} 个文件")
        
        # 更新结果列标题中的单位
        self.tree.heading("size", text=f"大小({current_unit})")
    
    def match_file_type(self, filename, file_type):
        """检查文件名是否匹配文件类型，支持分号分隔的多个文件类型"""
        if file_type == "*.*" or file_type == "":
            return True
        
        # 处理分号分隔的多个文件类型
        file_type_list = file_type.split(";")
        import fnmatch
        for ft in file_type_list:
            if fnmatch.fnmatch(filename, ft):
                return True
        return False
    
    def open_file(self, event):
        """双击事件处理：双击path列打开文件资源管理器，双击其他列打开文件"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        # 获取双击位置的列
        region = self.tree.identify_region(event.x, event.y)
        
        if region == "cell":
            column = self.tree.identify_column(event.x)
            file_path = self.tree.item(item, "values")[1]
            
            if column == "#2":  # path列
                # 打开文件资源管理器
                try:
                    # Windows: 打开文件所在目录
                    if sys.platform == "win32":
                        os.startfile(os.path.dirname(file_path))
                    # Linux: 打开目录
                    elif sys.platform == "linux":
                        import subprocess
                        subprocess.run(["xdg-open", os.path.dirname(file_path)])
                    # macOS: 显示文件在Finder中
                    elif sys.platform == "darwin":
                        import subprocess
                        subprocess.run(["open", "-R", file_path])
                except Exception as e:
                    print(f"打开文件资源管理器失败: {e}")
            else:
                # 打开文件
                try:
                    if sys.platform == "win32":
                        os.startfile(file_path)
                    elif sys.platform == "linux":
                        import subprocess
                        subprocess.run(["xdg-open", file_path])
                    elif sys.platform == "darwin":
                        import subprocess
                        subprocess.run(["open", file_path])
                except Exception as e:
                    print(f"打开文件失败: {e}")
    
    def sort_result(self, col):
        """根据列名对搜索结果进行排序，自动切换升降序"""
        # 获取当前选择的单位，用于大小列的标题显示
        current_unit = getattr(self, 'selected_unit', tk.StringVar(value='KB')).get()
        
        # 判断是否是当前排序列
        if self.sort_column == col:
            # 切换排序顺序
            self.sort_order = not self.sort_order
        else:
            # 新的排序列，默认升序
            self.sort_column = col
            self.sort_order = False
        
        # 获取所有结果项
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        # 根据列类型进行排序
        try:
            if col in ['name', 'path']:
                # 字符串列，直接比较
                items.sort(key=lambda x: x[0].lower(), reverse=self.sort_order)
            elif col == 'size':
                # 大小列，转换为数字
                items.sort(key=lambda x: float(x[0]), reverse=self.sort_order)
            elif col in ['created', 'modified']:
                # 日期列，转换为datetime对象
                items.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S"), reverse=self.sort_order)
        except Exception as e:
            # 处理排序错误
            print(f"排序失败: {e}")
            return
        
        # 重新排列项目
        for index, (val, k) in enumerate(items):
            self.tree.move(k, '', index)
        
        # 更新所有列标题，只在当前排序列显示指示器
        # 重置所有列标题
        headers = {
            'name': '文件名',
            'path': '路径',
            'size': f'大小({current_unit})',
            'created': '创建时间',
            'modified': '修改时间'
        }
        
        # 为当前排序列添加指示器
        for column in headers:
            if column == self.sort_column:
                # 添加排序指示器
                indicator = ' ↓' if self.sort_order else ' ↑'
                header_text = headers[column] + indicator
            else:
                header_text = headers[column]
            
            # 更新列标题
            self.tree.heading(column, text=header_text, command=lambda c=column: self.sort_result(c))
    
    def open_history_window(self):
        """打开历史搜索记录窗口"""
        # 创建历史记录窗口
        history_window = tk.Toplevel(self.root)
        history_window.title("历史搜索记录")
        history_window.geometry("800x500")
        history_window.option_add("*Font", "SimHei 10")
        
        # 创建主框架
        main_frame = ttk.Frame(history_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建历史记录表格
        history_frame = ttk.LabelFrame(main_frame, text="历史搜索条件", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 历史记录表格列
        columns = ("timestamp", "folder", "date_range", "file_type", "size_range")
        history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        # 设置列标题和宽度
        history_tree.heading("timestamp", text="搜索时间")
        history_tree.heading("folder", text="搜索文件夹")
        history_tree.heading("date_range", text="日期范围")
        history_tree.heading("file_type", text="文件类型")
        history_tree.heading("size_range", text="大小范围(KB)")
        
        history_tree.column("timestamp", width=150, anchor=tk.CENTER)
        history_tree.column("folder", width=200)
        history_tree.column("date_range", width=150, anchor=tk.CENTER)
        history_tree.column("file_type", width=120, anchor=tk.CENTER)
        history_tree.column("size_range", width=120, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(yscroll=scrollbar.set)
        
        # 布局表格和滚动条
        history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载历史记录到表格
        def load_history_to_tree():
            # 清空表格
            for item in history_tree.get_children():
                history_tree.delete(item)
            
            # 加载历史记录
            history = self.history_manager.get_history()
            for i, record in enumerate(history):
                # 格式化日期范围
                date_range = f"{record['date_from']} 至 {record['date_to']}"
                # 格式化大小范围
                if record['size_min'] == 0 and record['size_max'] == float('inf'):
                    size_range = "不限制"
                elif record['size_min'] == 0:
                    size_range = f"≤ {record['size_max']}"
                elif record['size_max'] == float('inf'):
                    size_range = f"≥ {record['size_min']}"
                else:
                    size_range = f"{record['size_min']} 至 {record['size_max']}"
                
                # 添加到表格
                history_tree.insert("", tk.END, iid=i, values=(
                    record['timestamp'],
                    record['folder'],
                    date_range,
                    record['file_type'],
                    size_range
                ))
        
        # 初始加载历史记录
        load_history_to_tree()
        
        # 绑定双击事件到应用函数
        history_tree.bind("<Double-1>", lambda event: apply_history())
        
        # 应用选中的历史记录
        def apply_history():
            selected_item = history_tree.selection()
            if not selected_item:
                messagebox.showwarning("提示", "请选择一条历史记录")
                return
            
            # 获取选中的历史记录索引
            index = int(selected_item[0])
            history = self.history_manager.get_history()
            record = history[index]
            
            # 将历史记录应用到搜索界面
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, record['folder'])
            
            # 设置日期范围
            from datetime import datetime
            date_from = datetime.strptime(record['date_from'], "%Y-%m-%d")
            date_to = datetime.strptime(record['date_to'], "%Y-%m-%d")
            self.date_from_entry.set_date(date_from)
            self.date_to_entry.set_date(date_to)
            
            # 设置文件类型
            self.file_type_entry.set(record['file_type'])
            
            # 设置大小范围
            self.size_min_entry.delete(0, tk.END)
            self.size_max_entry.delete(0, tk.END)
            if record['size_min'] != 0:
                self.size_min_entry.insert(0, record['size_min'])
            if record['size_max'] != float('inf'):
                self.size_max_entry.insert(0, record['size_max'])
            
            messagebox.showinfo("提示", "历史搜索条件已应用")
            # 移除关闭窗口的代码，双击后窗口不关闭
            # history_window.destroy()
        
        # 删除选中的历史记录
        def delete_history():
            selected_item = history_tree.selection()
            if not selected_item:
                messagebox.showwarning("提示", "请选择一条历史记录")
                return
            
            if messagebox.askyesno("确认", "确定要删除这条历史记录吗？"):
                index = int(selected_item[0])
                self.history_manager.delete_history(index)
                load_history_to_tree()
        
        # 清空所有历史记录
        def clear_all_history():
            if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
                self.history_manager.clear_history()
                load_history_to_tree()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.pack(fill=tk.X, pady=5)
        
        # 应用按钮
        apply_btn = ttk.Button(button_frame, text="应用选中的历史记录", command=apply_history)
        apply_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除按钮
        delete_btn = ttk.Button(button_frame, text="删除选中记录", command=delete_history)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空按钮
        clear_btn = ttk.Button(button_frame, text="清空所有记录", command=clear_all_history)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_btn = ttk.Button(button_frame, text="刷新记录", command=load_history_to_tree)
        refresh_btn.pack(side=tk.LEFT, padx=5)
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件夹选择区
        folder_frame = ttk.LabelFrame(main_frame, text="文件夹选择", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(folder_frame, text="选择文件夹:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.folder_entry = ttk.Entry(folder_frame, width=50)
        self.folder_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(folder_frame, text="浏览", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5)
        
        # 历史记录按钮
        ttk.Button(folder_frame, text="历史记录", command=self.open_history_window).grid(row=0, column=3, padx=5, pady=5)
        
        # 搜索条件区
        criteria_frame = ttk.LabelFrame(main_frame, text="搜索条件", padding="10")
        criteria_frame.pack(fill=tk.X, pady=5)
        
        # 创建时间范围
        ttk.Label(criteria_frame, text="创建时间范围:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(criteria_frame, text="从:").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.date_from_entry = DateEntry(criteria_frame, width=15, date_pattern='yyyy-MM-dd', showweeknumbers=False, showothermonthdays=False)
        self.date_from_entry.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(criteria_frame, text="到:").grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.date_to_entry = DateEntry(criteria_frame, width=15, date_pattern='yyyy-MM-dd', showweeknumbers=False, showothermonthdays=False)
        self.date_to_entry.grid(row=0, column=4, padx=5, pady=5)
        
        # 文件类型
        ttk.Label(criteria_frame, text="文件类型:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_type_var = tk.StringVar()
        self.file_type_entry = ttk.Combobox(criteria_frame, textvariable=self.file_type_var, width=15)
        self.file_type_entry['values'] = list(self.file_types.keys())
        self.file_type_entry['state'] = 'readonly'  # 设置为只读，只能通过下拉选择
        self.file_type_entry.current(0)  # 默认选择第一个选项
        self.file_type_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 文件大小范围
        ttk.Label(criteria_frame, text="文件大小:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 最小大小输入框
        ttk.Label(criteria_frame, text="最小:").grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        self.size_min_entry = ttk.Entry(criteria_frame, width=10)
        self.size_min_entry.grid(row=1, column=4, padx=5, pady=5)
        
        # 最大大小输入框
        ttk.Label(criteria_frame, text="最大:").grid(row=1, column=5, sticky=tk.W, padx=5, pady=5)
        self.size_max_entry = ttk.Entry(criteria_frame, width=10)
        self.size_max_entry.grid(row=1, column=6, padx=5, pady=5)
        
        # 文件大小单位选择
        ttk.Label(criteria_frame, text="单位:").grid(row=1, column=7, sticky=tk.W, padx=5, pady=5)
        self.unit_combobox = ttk.Combobox(criteria_frame, textvariable=self.selected_unit, width=8)
        self.unit_combobox['values'] = list(self.size_units.keys())
        self.unit_combobox['state'] = 'readonly'  # 设置为只读，只能通过下拉选择
        self.unit_combobox.current(0)  # 默认选择第一个选项（KB）
        self.unit_combobox.grid(row=1, column=8, padx=5, pady=5)
        
        # 搜索按钮，增加columnspan以覆盖所有列
        ttk.Button(criteria_frame, text="开始搜索", command=self.search_files).grid(row=2, column=0, columnspan=9, pady=10)
        
        # 结果显示区
        result_frame = ttk.LabelFrame(main_frame, text="搜索结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建树状视图
        columns = ("name", "path", "size", "created", "modified")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings")
        
        # 初始化排序状态
        self.sort_column = ""
        self.sort_order = False
        
        # 设置列标题和排序功能
        self.tree.heading("name", text="文件名", command=lambda: self.sort_result("name"))
        self.tree.heading("path", text="路径", command=lambda: self.sort_result("path"))
        self.tree.heading("size", text="大小(KB)", command=lambda: self.sort_result("size"))
        self.tree.heading("created", text="创建时间", command=lambda: self.sort_result("created"))
        self.tree.heading("modified", text="修改时间", command=lambda: self.sort_result("modified"))
        
        # 设置列宽
        self.tree.column("name", width=150)
        self.tree.column("path", width=300)
        self.tree.column("size", width=100, anchor=tk.CENTER)
        self.tree.column("created", width=150)
        self.tree.column("modified", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # 布局树状视图和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.open_file)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearchTool(root)
    root.mainloop()