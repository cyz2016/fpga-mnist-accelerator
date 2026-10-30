

set script_dir [file dirname [file normalize [info script]]]
set root_dir   [file normalize $script_dir/../..]

set proj_file  $root_dir/vivado/Zynq.xpr
set report_dir $root_dir/docs/reports

file mkdir $report_dir


open_project $proj_file


open_run impl_1
report_timing_summary -file $report_dir/vivado_timing_routed.rpt \
                      -max_paths 10
report_utilization -file $report_dir/vivado_utilization_routed.rpt

close_project
puts "==> 报告已输出到: $report_dir"