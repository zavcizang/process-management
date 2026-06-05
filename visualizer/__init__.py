# visualizer/__init__.py
# StrideCOWScheduler 可视化引擎层
# 项目: StrideCOWScheduler — 进程管理内核模拟器
# 作者: zavci (zjh3432512933)
# 仓库: https://gitee.com/zjh3432512933/process-management
from .tree_view import visualize_tree, visualize_tree_with_status, get_process_summary
from .scheduler_view import visualize_gantt, visualize_queue_snapshot, visualize_cpu_utilization, visualize_context_switches
from .memory_view import visualize_frame_map, visualize_page_table, visualize_memory_stats
from .dashboard import show_dashboard, show_process_detail
from .charts import ChartGenerator
