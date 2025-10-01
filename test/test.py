# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# Control bit positions in uio_in
EN   = 0
LOAD = 1
UP   = 2
OE   = 3

def ctrl_val(en=0, load=0, up=1, oe=1):
    """Pack control bits into uio_in."""
    return (oe << OE) | (up << UP) | (load << LOAD) | (en << EN)


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset (active-low), and default lines
    dut.ena.value   = 1
    dut.ui_in.value = 0
    dut.uio_in.value = ctrl_val(en=0, load=0, up=1, oe=1)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # After reset, expect 0
    assert int(dut.uo_out.value) == 0, f"After reset expected 0, got {int(dut.uo_out.value):#x}"

    # ---- LOAD D=0x05 ----
    dut.ui_in.value  = 0x05                 # D bus
    dut.uio_in.value = ctrl_val(en=0, load=1, up=1, oe=1)
    await ClockCycles(dut.clk, 1)           # load occurs on rising edge
    dut.uio_in.value = ctrl_val(en=0, load=0, up=1, oe=1)
    await ClockCycles(dut.clk, 1)
    assert int(dut.uo_out.value) == 0x05, f"After load expected 0x05, got {int(dut.uo_out.value):#x}"

    # ---- COUNT UP 3 cycles: 0x05 -> 0x08 ----
    dut.uio_in.value = ctrl_val(en=1, load=0, up=1, oe=1)
    await ClockCycles(dut.clk, 3)
    assert int(dut.uo_out.value) == 0x08, f"After count up expected 0x08, got {int(dut.uo_out.value):#x}"

    # ---- COUNT DOWN 2 cycles: 0x08 -> 0x06 ----
    dut.uio_in.value = ctrl_val(en=1, load=0, up=0, oe=1)
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == 0x06, f"After count down expected 0x06, got {int(dut.uo_out.value):#x}"

    # ---- OE gate: when oe=0, outputs should be 0 (don’t drive Z on TT outputs) ----
    dut.uio_in.value = ctrl_val(en=0, load=0, up=1, oe=0)   # hold count, gate output
    await ClockCycles(dut.clk, 1)
    assert int(dut.uo_out.value) == 0x00, f"With OE=0 expected 0x00, got {int(dut.uo_out.value):#x}"

    # Re-enable OE, output should reflect stored count (still 0x06)
    dut.uio_in.value = ctrl_val(en=0, load=0, up=1, oe=1)
    await ClockCycles(dut.clk, 1)
    assert int(dut.uo_out.value) == 0x06, f"After OE re-enable expected 0x06, got {int(dut.uo_out.value):#x}"

    # ---- Wrap-around up: load 0xFE, count 3 -> 0x01 ----
    dut.ui_in.value  = 0xFE
    dut.uio_in.value = ctrl_val(en=0, load=1, up=1, oe=1)
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = ctrl_val(en=1, load=0, up=1, oe=1)
    await ClockCycles(dut.clk, 3)   # FE -> FF -> 00 -> 01
    assert int(dut.uo_out.value) == 0x01, f"Wrap-up expected 0x01, got {int(dut.uo_out.value):#x}"

    # ---- Wrap-around down: load 0x01, count down 2 -> 0xFF ----
    dut.ui_in.value  = 0x01
    dut.uio_in.value = ctrl_val(en=0, load=1, up=0, oe=1)
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = ctrl_val(en=1, load=0, up=0, oe=1)
    await ClockCycles(dut.clk, 2)   # 01 -> 00 -> FF
    assert int(dut.uo_out.value) == 0xFF, f"Wrap-down expected 0xFF, got {int(dut.uo_out.value):#x}"

    
    # Reset
#    dut._log.info("Reset")
#    dut.ena.value = 1
#    dut.ui_in.value = 0
#    dut.uio_in.value = 0
#    dut.rst_n.value = 0
#    await ClockCycles(dut.clk, 10)
#    dut.rst_n.value = 1

#    dut._log.info("Test project behavior")
#
    # Set the input values you want to test
#    dut.ui_in.value = 20
#    dut.uio_in.value = 30

    # Wait for one clock cycle to see the output values
#    await ClockCycles(dut.clk, 1)

    # The following assersion is just an example of how to check the output values.
    # Change it to match the actual expected output of your module:
#    assert dut.uo_out.value == 50

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.
    
    
