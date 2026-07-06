# TODO

## Modernization (separate commit)

- Migrate packaging from `setup.py`/`requirements.txt` to `pyproject.toml`.
- Add `ruff` for linting/formatting.
- Add `mypy` and tighten type hints across `cmd.py`/`raster.py`/`printer.py`
  (most signatures already have hints, but return types are inconsistent).
- Pass over docstrings/comments.

## Known limitations

- `half_cut` (in `print_data`/`print_image`) defaults to `True`. It was only
  empirically verified on a PT-E560BT over Bluetooth, which isn't one of the
  officially listed printers (PT-P710BT/E550W/P750W) -- test with a spare
  tape on other models before relying on it.

  It defaults on because plain `half_cut=False` (`AUTO_CUT` + `NO_CHAINING`)
  feeds and fully cuts a wasted ~1 inch blank leading piece of tape before
  the real content on every job -- confirmed even with pristine, unmodified
  upstream code (not introduced by this fork), and it survives a power
  cycle and a factory reset. This turns out to be documented, expected
  Brother behavior, not a bug: there's a physical gap between the print
  head and cutter blade that tape must travel across, so Auto Cut mode
  always wastes a leading piece on the first label of a session ([Brother
  support FAQ](https://help.brother-usa.com/app/answers/detail/a_id/52292/~/why-does-one-inch-piece-of-lead-tape-feed-or-cut-off-prior-to-every-label-that)).
  Brother's own documented fix is to use Half Cut instead of Auto Cut
  ([QL-820NWB FAQ](https://support.brother.com/g/b/faqend.aspx?c=us&lang=en&prod=lpql820nwbeus&faqid=faqp00001293_015)),
  which is exactly what `half_cut=True` (`HALF_CUT | CUT_ON_LAST_LABEL`,
  `AUTO_CUT` off) does here.
- `print_information()`'s `length_mm` parameter is unused by `printer.py`.
  Passing a nonzero value made a PT-E560BT reject the job with "wrong media"
  on continuous tape -- it appears to only be valid for pre-cut/die-cut label
  stock, not continuous rolls. Needs more investigation before it's exposed
  anywhere.
- `find_rfcomm_channel()` (`bluetooth_transport.py`) shells out to `sdptool`
  and does simple text parsing -- best-effort, not guaranteed across
  printers/BlueZ versions.
