import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import glob

# 日志缩写映射
LOG_MAPPINGS = {
    # 状态码映射
    "status": {
        "S": "成功",
        "F": "失败"
    },
    # 文件类型映射
    "file_type": {
        "all_files": "所有文件",
        "all_images": "所有图片",
        "jpeg": "JPEG格式",
        "png": "PNG格式",
        "tiff": "TIFF格式",
        "raw": "RAW格式",
        "psd": "PSD格式",
        "dng": "DNG格式",
        "video": "视频文件",
        "archive": "压缩文件"
    }
}

class LogInterpreter:
    def __init__(self, root):
        self.root = root
        self.root.title("日志解释器")
        self.root.geometry("1000x600")
        self.root.option_add("*Font", "SimHei 10")
        
        # 设置全局变量
        self.current_logs = []
        self.log_folder = "search_logs"
        
        # 创建主界面
        self.create_widgets()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部按钮框架
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        # 选择日志文件按钮
        ttk.Button(top_frame, text="选择单个日志文件", command=self.select_single_log).pack(side=tk.LEFT, padx=5)
        
        # 导入日志文件夹按钮
        ttk.Button(top_frame, text="导入日志文件夹", command=self.import_log_folder).pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        ttk.Button(top_frame, text="刷新日志列表", command=self.refresh_log_list).pack(side=tk.LEFT, padx=5)
        
        # 清除按钮
        ttk.Button(top_frame, text="清除当前列表", command=self.clear_log_list).pack(side=tk.LEFT, padx=5)
        
        # 日志文件列表
        list_frame = ttk.LabelFrame(main_frame, text="日志文件列表")
        list_frame.pack(fill=tk.X, pady=5)
        
        # 创建列表框
        self.log_listbox = tk.Listbox(list_frame, height=5, selectmode=tk.SINGLE)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.log_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.log_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        # 绑定列表框双击事件
        self.log_listbox.bind("<Double-1>", self.on_log_select)
        
        # 日志详情框架
        detail_frame = ttk.LabelFrame(main_frame, text="日志详情")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建文本框用于显示日志详情
        self.detail_text = tk.Text(detail_frame, wrap=tk.WORD)
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)
        
        # 初始加载日志文件夹中的日志文件
        self.refresh_log_list()
    
    def refresh_log_list(self):
        """刷新日志文件列表"""
        # 清空列表
        self.log_listbox.delete(0, tk.END)
        
        # 检查日志文件夹是否存在
        if not os.path.exists(self.log_folder):
            return
        
        # 获取所有日志文件
        log_files = glob.glob(os.path.join(self.log_folder, "*.txt"))
        
        # 按修改时间排序，最新的在最上面
        log_files.sort(key=os.path.getmtime, reverse=True)
        
        # 添加到列表
        for log_file in log_files:
            # 只显示文件名，不显示完整路径
            self.log_listbox.insert(tk.END, os.path.basename(log_file))
    
    def select_single_log(self):
        """选择单个日志文件"""
        # 打开文件选择对话框
        log_file = filedialog.askopenfilename(
            title="选择日志文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if log_file:
            self.interpret_log(log_file)
    
    def import_log_folder(self):
        """导入日志文件夹"""
        # 打开文件夹选择对话框
        folder = filedialog.askdirectory(title="选择日志文件夹")
        
        if folder:
            self.log_folder = folder
            self.refresh_log_list()
    
    def on_log_select(self, event):
        """选择日志文件时触发"""
        # 获取选中的日志文件名
        selected_index = self.log_listbox.curselection()
        if selected_index:
            log_filename = self.log_listbox.get(selected_index)
            log_path = os.path.join(self.log_folder, log_filename)
            self.interpret_log(log_path)
    
    def interpret_log(self, log_path):
        """解释日志文件"""
        try:
            # 读取日志文件
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read().strip()
            
            # 解析日志内容
            log_parts = log_content.split(',')
            
            if len(log_parts) < 9:
                messagebox.showerror("错误", "日志格式不正确")
                return
            
            # 提取日志字段
            timestamp = log_parts[0]
            status = log_parts[1]
            folder = log_parts[2]
            date_from = log_parts[3]
            date_to = log_parts[4]
            file_type = log_parts[5]
            size_min = log_parts[6]
            size_max = log_parts[7]
            result = ','.join(log_parts[8:])
            
            # 转换缩写
            status_text = LOG_MAPPINGS["status"].get(status, status)
            file_type_text = LOG_MAPPINGS["file_type"].get(file_type, file_type)
            
            # 格式化结果显示
            formatted_result = self.format_result(status, result)
            
            # 格式化大小范围显示
            if size_min == '0' and size_max == '':
                size_range = "无限制"
            else:
                size_range = f"{size_min} KB 至 {size_max} KB"
            
            # 构建详细信息
            detail_info = [
                f"日志文件: {os.path.basename(log_path)}",
                f"日志路径: {log_path}",
                "=" * 50,
                f"搜索时间: {self.format_timestamp(timestamp)}",
                f"搜索状态: {status} ({status_text})",
                f"搜索文件夹: {folder if folder else '未指定'}",
                f"日期范围: {date_from} 至 {date_to}",
                f"文件类型: {file_type} ({file_type_text})",
                f"大小范围: {size_range}",
                f"搜索结果: {formatted_result}",
                "=" * 50
            ]
            
            # 显示到文本框
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(tk.END, '\n'.join(detail_info))
            
        except Exception as e:
            messagebox.showerror("错误", f"解析日志文件失败: {e}")
    
    def format_timestamp(self, timestamp):
        """格式化时间戳"""
        if len(timestamp) == 15:  # YYYYMMDD_HHMMSS
            try:
                # 转换为标准日期格式
                year = timestamp[:4]
                month = timestamp[4:6]
                day = timestamp[6:8]
                time_part = timestamp[9:]
                return f"{year}-{month}-{day} {time_part[:2]}:{time_part[2:4]}:{time_part[4:]}"
            except:
                return timestamp
        return timestamp
    
    def format_result(self, status, result):
        """格式化结果"""
        if status == "S":
            # 成功结果格式: 文件数,耗时
            if ',' in result:
                file_count, search_time = result.split(',', 1)
                return f"成功找到 {file_count} 个文件，耗时 {search_time} 秒"
            else:
                return result
        else:
            # 失败结果直接返回错误信息
            return f"失败 - {result}"
    
    def clear_log_list(self):
        """清除当前日志列表"""
        self.log_listbox.delete(0, tk.END)
        self.detail_text.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = LogInterpreter(root)
    root.mainloop()