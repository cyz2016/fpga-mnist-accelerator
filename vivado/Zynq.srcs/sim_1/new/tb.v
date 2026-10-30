`timescale 1ns / 1ps

module tb;

  reg FIXED_IO_ps_clk = 0;
  always #10 FIXED_IO_ps_clk = ~FIXED_IO_ps_clk;

  reg FIXED_IO_ps_porb = 0;
  reg FIXED_IO_ps_srstb = 0;

  wire [14:0] DDR_addr;
  wire [2:0]  DDR_ba;
  wire        DDR_cas_n;
  wire        DDR_ck_n;
  wire        DDR_ck_p;
  wire        DDR_cke;
  wire        DDR_cs_n;
  wire [3:0]  DDR_dm;
  wire [31:0] DDR_dq;
  wire [3:0]  DDR_dqs_n;
  wire [3:0]  DDR_dqs_p;
  wire        DDR_odt;
  wire        DDR_ras_n;
  wire        DDR_reset_n;
  wire        DDR_we_n;
  wire        FIXED_IO_ddr_vrn;
  wire        FIXED_IO_ddr_vrp;
  wire [53:0] FIXED_IO_mio;

  initial begin
    FIXED_IO_ps_porb  = 0;
    FIXED_IO_ps_srstb = 0;
    #200;
    FIXED_IO_ps_porb  = 1;
    FIXED_IO_ps_srstb = 1;
  end

  initial begin
    #200000;
    $display("Simulation finished");
    $finish;
  end

  design_1_wrapper dut (
    .DDR_addr(DDR_addr),
    .DDR_ba(DDR_ba),
    .DDR_cas_n(DDR_cas_n),
    .DDR_ck_n(DDR_ck_n),
    .DDR_ck_p(DDR_ck_p),
    .DDR_cke(DDR_cke),
    .DDR_cs_n(DDR_cs_n),
    .DDR_dm(DDR_dm),
    .DDR_dq(DDR_dq),
    .DDR_dqs_n(DDR_dqs_n),
    .DDR_dqs_p(DDR_dqs_p),
    .DDR_odt(DDR_odt),
    .DDR_ras_n(DDR_ras_n),
    .DDR_reset_n(DDR_reset_n),
    .DDR_we_n(DDR_we_n),
    .FIXED_IO_ddr_vrn(FIXED_IO_ddr_vrn),
    .FIXED_IO_ddr_vrp(FIXED_IO_ddr_vrp),
    .FIXED_IO_mio(FIXED_IO_mio),
    .FIXED_IO_ps_clk(FIXED_IO_ps_clk),
    .FIXED_IO_ps_porb(FIXED_IO_ps_porb),
    .FIXED_IO_ps_srstb(FIXED_IO_ps_srstb)
  );

endmodule
