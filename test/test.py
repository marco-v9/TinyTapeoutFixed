# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

EN, LOAD, UP, OE = 0, 1, 2, 3

def ctrl(en=0, load=0, up=1, oe=1):
    return (oe << OE) | (up << UP) | (load << LOAD) | (en << EN)

async def set_ctrl_and_latch(dut, en, load, up, oe):
    """Apply control bits and wait one rising edge so the DUT samples them."""
    dut.uio_in.value = ctrl(en, load, up, oe)
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_project(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())  # 100 kHz

    # Enable design, clear inputs
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = ctrl(0,0,1,1)

    # Reset (active-low)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == 0x00, f"After reset expected 0x00, got 0x{int(dut.uo_out.value):02X}"

    # LOAD D=0x05
    dut.ui_in.value = 0x05
    await set_ctrl_and_latch(dut, en=0, load=1, up=1, oe=1)  # pulse LOAD high for one edge
    await set_ctrl_and_latch(dut, en=0, load=0, up=1, oe=1)
    assert int(dut.uo_out.value) == 0x05, f"After load expected 0x05, got 0x{int(dut.uo_out.value):02X}"

    # COUNT UP 3: 0x05 -> 0x08
    await set_ctrl_and_latch(dut, en=1, load=0, up=1, oe=1)  # latch controls
    await ClockCycles(dut.clk, 3)
    assert int(dut.uo_out.value) == 0x08, f"After +3 expected 0x08, got 0x{int(dut.uo_out.value):02X}"

    # COUNT DOWN 2: 0x08 -> 0x06
    await set_ctrl_and_latch(dut, en=1, load=0, up=0, oe=1)  # change direction, let it latch
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == 0x06, f"After -2 expected 0x06, got 0x{int(dut.uo_out.value):02X}"

    # Gate outputs: OE=0 -> uo_out should be 0 (internal count still runs)
    await set_ctrl_and_latch(dut, en=1, load=0, up=1, oe=0)  # count one while gated
    assert int(dut.uo_out.value) == 0x00, f"With OE=0 expected 0x00, got 0x{int(dut.uo_out.value):02X}"

    # Re-enable OE: should now show 0x07 (0x06 + 1 while gated)
    await set_ctrl_and_latch(dut, en=1, load=0, up=1, oe=1)
    assert int(dut.uo_out.value) == 0x07, f"After OE re-enable expected 0x07, got 0x{int(dut.uo_out.value):02X}"
