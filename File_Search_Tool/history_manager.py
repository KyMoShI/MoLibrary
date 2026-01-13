import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self, history_file="search_history.json", log_folder="search_logs"):
        self.history_file = history_file
        self.log_folder = log_folder
        self.history = self.load_history()
        # 从日志文件加载历史记录
        self.load_history_from_logs()
    
    def load_history(self):
        """加载历史搜索记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return []
    
    def save_history(self):
        """保存历史搜索记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def add_search_history(self, search_criteria):
        """添加搜索记录到历史"""
        # 为每条记录添加时间戳
        search_criteria['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 检查是否存在重复记录（基于主要搜索条件）
        for item in self.history:
            # 比较主要搜索条件
            if (item.get('folder') == search_criteria.get('folder') and
                item.get('date_from') == search_criteria.get('date_from') and
                item.get('date_to') == search_criteria.get('date_to') and
                item.get('file_type') == search_criteria.get('file_type') and
                item.get('size_min') == search_criteria.get('size_min') and
                item.get('size_max') == search_criteria.get('size_max')):
                # 如果存在重复，先删除旧记录
                self.history.remove(item)
                break
        
        # 将新记录添加到历史列表开头
        self.history.insert(0, search_criteria)
        
        # 限制历史记录数量，只保留最近20条
        if len(self.history) > 20:
            self.history = self.history[:20]
        
        # 保存到文件
        self.save_history()
    
    def get_history(self):
        """获取历史搜索记录"""
        return self.history
    
    def clear_history(self):
        """清空历史搜索记录"""
        self.history = []
        self.save_history()
    
    def delete_history(self, index):
        """删除特定的历史搜索记录"""
        if 0 <= index < len(self.history):
            del self.history[index]
            self.save_history()
    
    def load_history_from_logs(self):
        """从日志文件加载历史搜索记录"""
        try:
            # 检查日志文件夹是否存在
            if not os.path.exists(self.log_folder):
                return
            
            # 安全获取日志文件夹中的所有txt文件
            log_files = []
            try:
                log_files = [f for f in os.listdir(self.log_folder) if f.endswith('.txt')]
            except PermissionError:
                print(f"没有权限访问日志文件夹: {self.log_folder}")
                return
            except Exception as e:
                print(f"读取日志文件夹失败: {e}")
                return
            
            # 按修改时间排序，从最新到最旧
            try:
                log_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.log_folder, x)), reverse=True)
            except Exception as e:
                print(f"排序日志文件失败: {e}")
                # 无法排序时，使用默认顺序
                pass
            
            # 解析每个日志文件
            for log_file in log_files:
                log_path = os.path.join(self.log_folder, log_file)
                
                try:
                    # 读取日志文件内容
                    with open(log_path, 'r', encoding='utf-8') as f:
                        content = f.readlines()
                    
                    # 解析日志内容
                    search_criteria = {}
                    timestamp = None
                    
                    for line in content:
                        line = line.strip()
                        
                        # 提取搜索时间（支持中英文格式）
                        if line.startswith('Search Log - ') or line.startswith('搜索日志 - '):
                            timestamp = line[11:].strip() if line.startswith('Search Log - ') else line[6:].strip()
                        # 提取搜索文件夹（支持中英文格式）
                        elif line.startswith('Search Folder:') or line.startswith('搜索文件夹:'):
                            search_criteria['folder'] = line[14:].strip() if line.startswith('Search Folder:') else line[5:].strip()
                        # 提取日期范围（支持中英文格式）
                        elif line.startswith('Date Range:') or line.startswith('日期范围:'):
                            date_range = line[12:].strip() if line.startswith('Date Range:') else line[5:].strip()
                            # 支持中英文分隔符
                            if 'to' in date_range:
                                date_from, date_to = date_range.split('to', 1)
                                search_criteria['date_from'] = date_from.strip()
                                search_criteria['date_to'] = date_to.strip()
                            elif '至' in date_range:
                                date_from, date_to = date_range.split('至', 1)
                                search_criteria['date_from'] = date_from.strip()
                                search_criteria['date_to'] = date_to.strip()
                        # 提取文件类型（支持中英文格式）
                        elif line.startswith('File Type:') or line.startswith('文件类型:'):
                            search_criteria['file_type'] = line[10:].strip() if line.startswith('File Type:') else line[5:].strip()
                        # 提取大小范围（支持中英文格式）
                        elif line.startswith('Size Range:') or line.startswith('大小范围:'):
                            size_range = line[11:].strip() if line.startswith('Size Range:') else line[5:].strip()
                            # 支持中英文分隔符
                            if 'to' in size_range:
                                size_min_str, size_max_str = size_range.split('to', 1)
                                size_min = size_min_str.replace('KB', '').strip()
                                size_max = size_max_str.replace('KB', '').strip()
                            elif '至' in size_range:
                                size_min_str, size_max_str = size_range.split('至', 1)
                                size_min = size_min_str.replace('KB', '').strip()
                                size_max = size_max_str.replace('KB', '').strip()
                            else:
                                continue
                                
                            # 转换大小为数字
                            try:
                                search_criteria['size_min'] = float(size_min) if size_min != '0' else 0
                            except:
                                search_criteria['size_min'] = 0
                            
                            if size_max == 'Unlimited' or size_max == '不限制':
                                search_criteria['size_max'] = float('inf')
                            else:
                                try:
                                    search_criteria['size_max'] = float(size_max)
                                except:
                                    search_criteria['size_max'] = float('inf')
                    
                    # 如果提取到了必要的搜索条件
                    if search_criteria and timestamp:
                        # 添加时间戳
                        search_criteria['timestamp'] = timestamp
                        
                        # 确保所有必要字段都存在
                        if all(key in search_criteria for key in ['folder', 'date_from', 'date_to', 'file_type', 'size_min', 'size_max', 'timestamp']):
                            # 检查是否存在重复记录（基于主要搜索条件）
                            is_duplicate = False
                            for item in self.history:
                                if (item.get('folder') == search_criteria.get('folder') and
                                    item.get('date_from') == search_criteria.get('date_from') and
                                    item.get('date_to') == search_criteria.get('date_to') and
                                    item.get('file_type') == search_criteria.get('file_type') and
                                    item.get('size_min') == search_criteria.get('size_min') and
                                    item.get('size_max') == search_criteria.get('size_max')):
                                    is_duplicate = True
                                    break
                            
                            # 如果不是重复记录，则添加到历史列表
                            if not is_duplicate:
                                # 将新记录添加到历史列表开头
                                self.history.insert(0, search_criteria)
                                
                                # 限制历史记录数量，只保留最近20条
                                if len(self.history) > 20:
                                    self.history = self.history[:20]
                
                except PermissionError:
                    print(f"没有权限读取日志文件: {log_file}")
                    continue
                except Exception as e:
                    print(f"解析日志文件 {log_file} 失败: {e}")
                    continue
            
            # 保存更新后的历史记录
            self.save_history()
            
        except Exception as e:
            print(f"从日志加载历史记录失败: {e}")
