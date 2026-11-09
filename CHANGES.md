# Modifications to the ECP5 Mini

This file is the notice of modification required by the CERN-OHL-S v2 licence.

**Source:** [joshajohnson/ecp5-mini](https://github.com/joshajohnson/ecp5-mini), hardware r0.1, commit `711a78e` (2020-10-19), © Josh Johnson, CERN-OHL-S v2.
**Modified by:** Hauke Carstensen, with AI assistance (Claude Opus 5.5).
**Date of modification:** 2026-11-08.
**Status:** concept change. Not manufactured or tested on hardware.

## Board (hardware/rev1.1/ecp5-mini.kicad_pcb)
1. The file was converted to the KiCad 9 format.
2. **JTAG header J2 removed.** It is replaced by J2, a `Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical` footprint on the bottom side with the ARM Cortex 10-pin pinout:
   - 1 VTref = +3V3
   - 2 TMS, 4 TCK, 6 TDO, 8 TDI
   - 3, 5, 9 GND
   - 7 key, 10 nRESET: not connected

   The original FPGA-side JTAG routing is kept. Only the bottom-layer runs to the old header were replaced.
3. **Qwiic connector J6 added:** JST SH SM04B-SRSS-TB on the top side, at the top-left corner.
   - 1 GND, 2 +3V3, 3 SDA = /PORT_H1, 4 SCL = /PORT_H0.
   - 4k7 pull-ups R31 (SCL) and R32 (SDA), 0402, on the bottom side.
4. **RGB LEDs D9, D10, D11 removed.** D4–D8 moved down 0.20 mm (pitch unchanged).
5. Two existing traces were moved sideways under the shifted D4: /PORT_A0 by 0.16 mm and /PORT_A4 by 0.07 mm. The rest of their routing is unchanged.
6. All LED cathode and anode nets were rerouted, along with the new I²C, JTAG and power connections. That is 121 new track segments plus 26 new vias.
7. Fiducials moved: FID5 to (136.2, 92.4) mm and FID2 to (146.4, 89.0) mm.
8. Silkscreen:
   - Removed the old JTAG pin labels (3V3/GND/TCK/TDO/TDI/TMS).
   - Changed the LED label "7" to "4".
   - Moved the reference text of the new parts to the fab layer.
9. Net names updated to match the schematic: RN3 pads 2–4 and the unused TC2050 pins.

## Schematic
- **FPGA Config sheet:** J2 is now a `Conn_02x05_Odd_Even` symbol (TC2050, not in BOM), with an explanatory note.
- **Root sheet:** J6 Qwiic connector and R31/R32 added, with a note that they share PORT_H0/H1 with J4.
- **LEDs sheet:** D9–D11 marked DNP, not in BOM and not on board, with a note. LED_5 to LED_7 still connect to RN3.

## Verification
- **DRC:** 0 new violations and 0 unconnected items compared with the original board converted to KiCad 9.
- **Schematic parity:** 0 new mismatches compared with the original's own parity report.
- **ERC:** no new violation types beyond library-symbol mismatches of the kind the original already had.
- **SPICE:** I²C rise time and JTAG TCK signal quality. See README.md and scripts/spice.
