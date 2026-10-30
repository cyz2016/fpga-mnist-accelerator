# Makefile for Vitis HLS MNIST inference
PROJECT_NAME = mnist_fpga
TOP_FUNCTION = mnist_infer
SOLUTION = solution1


VITIS_HLS = vitis_hls

run: csim csynth cosim

csim:
	$(VITIS_HLS) -f scripts/run_hls.tcl -c "open_project $(PROJECT_NAME); set_top $(TOP_FUNCTION); csim_design; exit"

csynth:
	$(VITIS_HLS) -f scripts/run_hls.tcl -c "open_project $(PROJECT_NAME); set_top $(TOP_FUNCTION); csynth_design; exit"

cosim:
	$(VITIS_HLS) -f scripts/run_hls.tcl -c "open_project $(PROJECT_NAME); set_top $(TOP_FUNCTION); cosim_design; exit"

clean:
	rm -rf $(PROJECT_NAME)/$(SOLUTION)/sim/
	rm -rf $(PROJECT_NAME)/$(SOLUTION)/syn/