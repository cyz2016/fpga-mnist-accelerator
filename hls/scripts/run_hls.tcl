# run_hls.tcl
open_project mnist_fpga
add_files inference.cpp
add_files -tb testbench.cpp
add_files -tb test_data.h
add_files weights.h
set_top mnist_infer
csim_design
csynth_design
cosim_design
exit