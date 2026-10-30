# 重建工程
source scripts/rebuild.tcl
# 跑综合
launch_runs synth_1
wait_on_run synth_1
# 跑实现
launch_runs impl_1
wait_on_run impl_1
# 生成报告
open_run impl_1
report_timing_summary -file ./timing_report.rpt
report_utilization -file ./utilization_report.rpt
exit