# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

EN, LOAD, UP, OE = 0, 1, 2, 3

def ctrl(en=0, load=0, up=1, oe=1):
    return (oe << OE) | (up << UP) | (load << LOAD) | (en << EN)

@cocotb.test()
async def test_project(dut):
    dut._log.info("=== Smoke test: reset, load, count, OE gate ===")

    # 100 kHz clock (10 us)
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    # Reset
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = ctrl(0, 0, 1, 1)
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 2)

    got = int(dut.uo_out.value)
    dut._log.info(f"After reset: uo_out=0x{got:02X}")
    assert got == 0x00, f"After reset expected 0x00, got 0x{got:02X}"

    # LOAD D=0x05
    dut.ui_in.value  = 0x05
    dut.uio_in.value = ctrl(en=0, load=1, up=1, oe=1)
    await ClockCycles(dut.clk, 1)         # load on rising edge
    dut.uio_in.value = ctrl(en=0, load=0, up=1, oe=1)
    await ClockCycles(dut.clk, 2)         # give GL a bit of slack

    got = int(dut.uo_out.value)
    dut._log.info(f"After load 0x05: uo_out=0x{got:02X}")
    assert got == 0x05, f"After load expected 0x05, got 0x{got:02X}"

    # COUNT UP 3: 0x05 -> 0x08
    dut.uio_in.value = ctrl(en=1, load=0, up=1, oe=1)
    await ClockCycles(dut.clk, 3)
    await ClockCycles(dut.clk, 1)         # one extra cycle for GL settle
    got = int(dut.uo_out.value)
    dut._log.info(f"After +3: uo_out=0x{got:02X}")
    assert got == 0x08, f"Count up expected 0x08, got 0x{got:02X}"

    # COUNT DOWN 2: 0x08 -> 0x06
    dut.uio_in.value = ctrl(en=1, load=0, up=0, oe=1)
    await ClockCycles(dut.clk, 2)
    await ClockCycles(dut.clk, 1)
    got = int(dut.uo_out.value)
    dut._log.info(f"After -2: uo_out=0x{got:02X}")
    assert got == 0x06, f"Count down expected 0x06, got 0x{got:02X}"

    # OE gate to 0
    dut.uio_in.value = ctrl(en=1, load=0, up=1, oe=0)
    await ClockCycles(dut.clk, 1)
    got = int(dut.uo_out.value)
    dut._log.info(f"With OE=0: uo_out=0x{got:02X}")
    assert got == 0x00, f"With OE=0 expected 0x00, got 0x{got:02X}"

    # Re-enable OE, should reflect current count (incremented once while OE was 0)
    dut.uio_in.value = ctrl(en=1, load=0, up=1, oe=1)
    await ClockCycles(dut.clk, 1)
    got = int(dut.uo_out.value)
    dut._log.info(f"After OE=1: uo_out=0x{got:02X}")
    assert got == 0x07, f"After OE re-enable expected 0x07, got 0x{got:02X}"
