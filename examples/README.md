# Bluetooth examples

These scripts exercise `brother_pt`'s Bluetooth transport (`BrotherPt.bluetooth(...)`,
`brother_pt/bluetooth_transport.py`) against real hardware over a classic
Bluetooth RFCOMM/SPP connection. They require:

* Linux (uses `socket.AF_BLUETOOTH`/`BTPROTO_RFCOMM`, no extra Python packages)
* The printer already paired and bonded, e.g.:
  ```
  bluetoothctl
  > pair <bdaddr>
  > trust <bdaddr>
  ```

Because they need a real printer connected over Bluetooth, they can't be run
in CI -- they're for manual/hardware-in-the-loop testing.

## Finding the RFCOMM channel

Both scripts try to auto-detect the channel via `sdptool browse <bdaddr>`. If
that fails (e.g. `sdptool` isn't installed, or parsing doesn't match your
printer's SDP records), find it yourself:

```
sdptool browse <bdaddr>
```

Look for the `"Serial Port"` service and its `Channel:` number, then pass it
explicitly with `-c/--channel`.

## Scripts

* `bluetooth_status.py <bdaddr>` -- connects and prints media width/type/tape
  color/text color.
* `bluetooth_print.py <bdaddr> --text "..."` -- prints a text label. By
  default this uses a leading peel-tab score cut in addition to the trailing
  separating cut; pass `--no-half-cut` for plain auto-cut instead. Verified
  on a PT-E560BT only -- other printer models are untested and may behave
  differently, including cutting mid-label or double-cutting; test with a
  spare tape first. Half-cut is the default here because plain auto-cut
  wastes a blank leading piece of tape before the real content -- this is
  documented Brother behavior (physical gap between print head and cutter),
  not a bug, and Brother's own recommended fix is exactly this: use Half
  Cut instead of Auto Cut. See `TODO.md` for sources.
