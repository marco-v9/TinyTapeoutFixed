/*
 * Copyright (c) 2024 Marco
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_counter (
    `ifdef GL_TEST
    input  wire VPWR,   // added for gate-level sim
    input  wire VGND,   // added for gate-level sim
    `endif
    input  wire [7:0] ui_in,    // Dedicated inputs (we use as D[7:0])
    output wire [7:0] uo_out,   // Dedicated outputs (counter value when OE=1)
    input  wire [7:0] uio_in,   // Extra inputs: control pins
    output wire [7:0] uio_out,  // Not used
    output wire [7:0] uio_oe,   // 0 = all UIOs are inputs
    input  wire       ena,      // always 1 when powered (unused)
    input  wire       clk,      // clock
    input  wire       rst_n     // async reset, active-low
);
  // control mapping on UIOs:
  wire en_i   = uio_in[0];
  wire load_i = uio_in[1];
  wire up_i   = uio_in[2];
  wire oe_i   = uio_in[3];

  wire [7:0] count_bus;

  // counter instance
  counter_298A u_cnt (
      .clk     (clk),
      .reset_n (rst_n),
      .en      (en_i),
      .load    (load_i),
      .up      (up_i),
      .oe      (oe_i),
      .d       (ui_in),
      .y       (count_bus)
  );

  // TT dedicated outputs: never drive Z. Gate to 0 when OE=0.
  assign uo_out  = oe_i ? count_bus : 8'b0000_0000;

  // keep UIOs as inputs only
  assign uio_out = 8'b0000_0000;
  assign uio_oe  = 8'b0000_0000;

  // silence unused warnings (upper UIO bits + ena)
  wire _unused = &{ena, uio_in[7:4], 1'b0};
endmodule


//counter code
module counter_298A (
    input  wire        clk,
    input  wire        reset_n,   // async reset, active lo
    input  wire        en,        // count enable
    input  wire        load,      // sync load: 1 -> load d on next rising clk
    input  wire        up,        // 1 = count up, 0 = count down
    input  wire        oe,        // 1 = drive outputs, 0 = high-Z
    input  wire [7:0]  d,         // parallel load value
    output wire [7:0]  y          // tri-stated count bus
);
  reg [7:0] count_q;

  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      count_q <= 8'd0;
    end else if (load) begin
      count_q <= d;
    end else if (en) begin
      if (up)
        count_q <= count_q + 8'd1;
      else
        count_q <= count_q - 8'd1;
    end
  end

  // internal tri-state; top-level converts Z to 0 on uo_out.
  assign y = oe ? count_q : 8'bz;
endmodule
