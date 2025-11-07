# nonsense

Repository of one-off experiments, utilities, and study notes. Each file is intentionally standalone; paths, parameters, and dependencies are hard-coded for the author’s environment. Below is a guided tour describing what every artifact does, notable quirks, and any obvious hazards.

## Automation & Data Utilities

- `Makefile` – Single `commit` recipe that stages everything, commits with a timestamped message, and pushes to `origin main`. Handy shortcut, but running it on the wrong branch or with unwanted files staged will push those changes immediately.
- `hash.py` / `decrypt.py` – Toy pair for demonstrating salted SHA-256 hashing plus a reversible “keyboard shift” used to obfuscate a symmetric key. Both scripts prompt on stdin and reuse the same row-wise key map. They call the output “encrypted,” but nothing is actually decrypted because SHA-256 is one-way; the scripts simply recompute the hash to verify user input, so treat them as demos only.
- `icbcbankstatement.py` – Regex parser for Chinese ICBC transaction narratives. It extracts per-day totals by currency (EUR/DKK/SEK/USD/CNY) from the embedded sample text, assembles a pandas DataFrame, and prints currency totals. Assumes the SMS/email wording and punctuation stay identical; the combined regex can miss or double-count amounts if the format shifts. `collections.Counter` is imported but unused.
- `hrv.py` – Headless Selenium scraper that walks every date from 2024‑11‑11 to “now,” loading Wunderground’s history pages (`lib-city-history-summary` widget) for KILEVANS56 in Evanston. It pulls summary spans (high/low temp, precipitation, etc.) and writes `evanston_weather_data.csv`. Any markup change or slow load triggers the fallback branch that skips days; there’s no retry or caching, so expect long runtimes and potential rate-limit issues.
- `onedrivepic.py` – Counts photos by inspecting a `year/month` directory hierarchy (filenames must start with `YYYYMMDD`). It aggregates daily, weekly, and monthly totals since `start_date_input`, smooths each series, and plots raw vs. smoothed curves. Useful for personal activity tracking, but it assumes every directory follows the naming convention and loads the entire index into memory.
- `wordsort.py` – Maintains a big vocabulary list inline, sorts the entries case-insensitively, reports duplicates, and prints how many words only appear once. Helpful for spotting repeated study terms (e.g., duplicated “Accession” entries or repeated Christopher Hitchens excerpts), but the vocabulary lives directly in the script, so editing requires modifying the code.

## Media & Visualization Tools

- `audio2text.py` – Forces OpenAI Whisper “medium” to run on CPU and transcribes `/Users/rx/Downloads/bart.m4a`. Segments are formatted as `[start_time] text` and saved to `/Users/rx/Downloads/transcript.txt`. There is no CLI, batching, or error handling; hard-coded paths must be changed in the script, and `torch` is imported but unused.
- `videoocr.py` – End-to-end OCR pipeline for chat screenshots: optional (commented) frame extraction, per-frame OCR in `chi_sim+eng`, live CPU/RAM monitoring via a daemon thread, and deduplication using SequenceMatcher plus TF‑IDF/DBSCAN clustering before writing the final transcript. Paths, language packs, and frame sampling are hard-coded; the monitor thread never stops, and clustering assumes scikit-learn is present. `fuzzywuzzy` is imported but not used.
- `gamma.py` – Uses NetworkX to sketch the signal flow of a gamma-ray coincidence setup. Nodes carry multi-line descriptions and are linked sequentially from source to counter. Saving fails because `plt.savefig` receives a directory path (`/Users/rx/Downloads`) instead of a filename; fix by appending a filename before calling `savefig`.
- `rainbow.py` / `rainbow_visibility_YYYY.MM.DD.HHMM.html` – Generates Folium maps that overlay the 42° rainbow cone relative to several fountains near 42.054756° N, −87.672833° W. `rainbow.py` fetches sun altitude/azimuth via Pysolar/Astral, draws sunlight and “visibility cone” polylines, opens the map in a browser, screenshots it with Selenium, and loops interactively between “current” and custom timestamps (validated down to Gregorian cutover rules). Heavy geo/GUI dependencies and numerous hard-coded paths (ChromeDriver, font assets) mean it only works in the original author’s setup; the cone geometry is approximate because it reuses fixed ∆lat/∆lon offsets regardless of azimuth. The HTML file is an example output.
- `cropwhite.py` – Batch crops every JPG/PNG in `/Users/rx/Desktop/Quiz 8` using a fixed bounding box and writes the result back into the same folder. Fast but destructive: outputs overwrite originals, and the crop tuple is specified in raw pixels without checking image dimensions or orientation.

## Simulation, Math & Physics

- `Test.py` – Relativistic constant-acceleration burn estimator for an antimatter-powered spacecraft. It iteratively guesses a fuel load, integrates motion at 0.1 s resolution, and plots velocity, mass, power, and force histories before printing the required fuel mass (with a 1.5× safety multiplier). Caveats: `fuel_consumption_rate` is never updated yet still plotted, intermediate arrays are shared across repeated `compute_trajectory` calls (so stale data persists), and the `velocity[i+1:] = v_final` slice can throw when `i` is the final index.
- `modfma.py` – Integrates a one-second sprint to 0.999999 c under three contrived thrust laws (F=ma, √(ma), ∛(ma)), accumulating energy expenditure and proper time. `lorentz_gamma` is computed but not fed back into the acceleration or force models, so the simulation is purely Newtonian despite the relativistic veneer; power draws ignore mass loss or engine limits.
- `rindler.py` – Fully featured constant proper-acceleration planner (single leg and symmetric four-leg trips). Includes a bisection solver for the rapidity ratio, time/distance summaries in SI and astronomical units, and photon-rocket power/energy bookkeeping. Extremely useful reference, but `solve_eta_from_ratio` snaps low ratios to ~0 without warning, so sub-relativistic scenarios may quietly degrade.
- `bianchi.py` – Collection of Manim scenes illustrating Rindler horizons, horizon detectors, quantum surface facets, and two derivations of black-hole entropy. Each scene assembles TeX/math objects and axes, but the file uses `np.exp` for the Boltzmann factor without importing NumPy, so rendering currently raises `NameError: name 'np' is not defined`.
- `chaos.py` – Loads `~/Downloads/chaos01.csv`, renames its first three columns to `Time`, `Counts`, `isGate`, computes the gradient of `Counts` versus `Time`, and plots a Poincaré section sampled whenever `isGate == 1`. Requires at least two gate crossings and assumes the CSV column order never changes; no optional arguments or safeguards.
- `daylight.py` – Pure-Numpy daylight-duration map. Builds a latitude/day mesh, calculates solar declination, clips the hour-angle domain to [-1, 1], and plots both contour lines every two hours and a filled heat map. A nice self-contained visualization; does not model atmospheric refraction or leap years.
- `shannon.py` – Demonstrates compression ratios for different entropy sources by writing three 1 MB text files (uniform, random, blocky) and measuring gzip output sizes. Great for teaching, but every execution writes six large files without cleanup or configuration hooks.

## Security / Crypto Demos

- `hash.py` / `decrypt.py` (see above) – emphasize that they are illustrative only; SHA-256 outputs are not decrypted, merely verified. The keyboard-shift cipher is trivially reversible (and implemented twice), so don’t rely on it for real secrecy.

## Text Analytics & Documentation

- `grammar.py` – Contains a massive document-audit tool embedded inside a triple-quoted raw string assigned to `script`. Running this file writes `/mnt/data/doc_audit.py` and an accompanying requirements file, but the helper variable `reqs` is never defined before use, so execution fails unless you manually define `reqs` or copy the string contents out. If you want to use the actual auditor, extract `script` to its own file and fix the missing requirements definition.
- `conlaw.qmd` – Quarto notebook filled with constitutional-law lecture notes: interpretive hypotheticals, doctrinal tables, case briefs, IRAC templates, and policy discussions. No executable code; render with Quarto to get a formatted HTML study packet.
- `Test.py`, `modfma.py`, `rindler.py`, `bianchi.py`, `chaos.py`, `daylight.py`, `shannon.py`, and `rainbow.py` are good places to mine for math-heavy snippets/questions.

## Miscellaneous

- `audio2text.py`, `videoocr.py`, `gamma.py`, `cropwhite.py`, and `onedrivepic.py` rely heavily on hard-coded absolute paths (`/Users/rx/...`). Update those before running on another machine.
- `wechat.py` – Placeholder file with no content.
- `README.md` – This guide. Update it whenever you add another one-off so future you doesn’t have to rediscover what each script does.

 Test.py:1 – Relativistic constant-acceleration burn simulator that iteratively guesses the antimatter fuel load, populates velocity/
    mass/power histories, and plots four diagnostic panes (Test.py:115). fuel_consumption_rate is never updated (Test.py:27), so that
    subplot is flat; the arrays are shared across successive compute_trajectory calls causing stale data, and clamping via velocity[i+1:] =
    v_final can index past the array when i is the last timestep (Test.py:48).
  - modfma.py:1 – Integrates a one-second sprint under three hypothetical thrust laws (F=ma, sqrt, cbrt) and accumulates energy and
    proper time (modfma.py:31). lorentz_gamma is computed but not fed back into the acceleration or force models (modfma.py:57), so the
    “relativistic” label is cosmetic and the comparison ignores mass change or power limits.
  - rindler.py:1 – Fully worked constant proper-acceleration planner: utilities for single legs (rindler.py:65), symmetric 4-leg trips
    solved via a bisection helper for η (rindler.py:34), and photon-rocket power/energy bookkeeping (rindler.py:127). Solid numerics, but
    solve_eta_from_ratio silently snaps low ratios to ~0 (rindler.py:39), so sub‑relativistic trips may be misreported instead of warning
    the caller.
  - daylight.py:4 – Pure-Numpy daylight-duration field: builds a latitude/day mesh, computes solar declination, clips the hour-
    angle domain, and overlays contour/heat maps (daylight.py:23). Simple and self-contained; limitations are physical (no atmospheric
    refraction, leap years).
  - chaos.py:5 – Reads a CSV of rotor revolutions, takes the gradient of “Counts” w.r.t. “Time,” filters revolutions via an isGate flag,
    and renders a Poincaré scatter (chaos.py:28). Assumes the input file lives at ~/Downloads, that columns appear in fixed order, and that
    the gradient denominator stays monotonic; any missing isGate rows raise immediately (chaos.py:18).
  - shannon.py:6 – Generates three 1 MB text corpora (random, uniform, blocky) and compares gzip ratios to illustrate entropy
    (shannon.py:41). Useful teaching snippet but every run writes six large files without cleanup; consider guarding the workload or
    parameterizing n_chars.

  Media & Visualization

  - audio2text.py:5 – Forces Whisper “medium” to run on CPU, transcribes a hard-coded .m4a, formats each segment as [start] text, and saves
    to a fixed Downloads path (audio2text.py:30). Great for a one-off but there’s no CLI, error handling, or batching, and the torch import
    is unused.
  - videoocr.py:1 – End-to-end OCR helper: optional (commented) frame extraction, per-frame OCR in chi_sim+eng, live CPU/RAM monitoring via
    a daemon thread (videoocr.py:39), deduplication with SequenceMatcher + TF‑IDF + DBSCAN, and final transcript output (videoocr.py:99).
    Hard-coded folders (videoocr.py:115), unused fuzzywuzzy import, and a monitor thread that never stops once process_frames_to_text
    returns all merit cleanup; clustering assumes scikit‑learn is available and can explode on empty transcripts.
  - gamma.py:1 – NetworkX diagram of a gamma-ray coincidence apparatus with descriptive node labels (gamma.py:8). Saving fails because
    plt.savefig is given a directory (gamma.py:48) instead of a file; flowchart_path is reused for both directory and return value, so even
    after fixing the path you’d still only print /Users/rx/Downloads.
  - cropwhite.py:4 – Batch crops every JPG/PNG in /Users/rx/Desktop/Quiz 8 with a fixed bounding box and writes back into the same folder
    (cropwhite.py:5). Simple but destructive: outputs overwrite originals, the crop rectangle is hard-coded in pixels (cropwhite.py:13),
    and there’s no guard for orientation/size mismatches.
  - rainbow.py:1 – Ambitious rainbow-visibility mapper: Folium map creation, sun altitude/azimuth via Pysolar/Astral, optional boundary
    visualization for multiple fountains (rainbow.py:26), Selenium screenshot capture (rainbow.py:164), and an interactive loop for
    “current” versus custom timestamps with validation down to Gregorian calendar cutover (rainbow.py:171). Heavy dependencies and side
    effects (opens browsers, requires ChromeDriver path at rainbow.py:209), plus the geometry approximations reuse constant ∆lat/∆lon
    regardless of azimuth, so the cones are only qualitative.
  - rainbow_visibility_2024.12.21.1200.html:1 – Static Folium output produced by the script above: includes OpenStreetMap tiles, the sun
    vector line, and pink/blue polylines marking the 42° cone for that timestamp—useful as a reference that the pipeline runs end-to-end.

  Data & Automation

  - hrv.py:11 – Headless Chrome scraper that walks day by day from 2024‑11‑11 to “now,” waits for Wunderground’s history component, scrapes
    the summary spans, and exports a CSV (hrv.py:82). Reliant on custom web components like lib-city-history-summary (hrv.py:45); any
    markup tweak or slower load causes skipped days, and there’s no retry/backoff other than a 1 s sleep (hrv.py:77).
  - icbcbankstatement.py:5 – Regex-based parser for Chinese-language ICBC SMS/email statements: extract_currency_data hunts for
    dates and currency-specific suffixes (icbcbankstatement.py:7), summarize_transactions aggregates totals per day/currency
    (icbcbankstatement.py:31), and the remainder builds a DataFrame plus totals (icbcbankstatement.py:58). Works for the embedded sample
    text but the nested regex ({"|".join(...)} at icbcbankstatement.py:20) can break on overlapping captures, and Counter is imported but
    unused.
  - onedrivepic.py:7 – Tallies daily/weekly/monthly counts of photos stored in a year/month folder hierarchy where filenames start with
    YYYYMMDD, then plots raw versus smoothed counts for each cadence (onedrivepic.py:48). Assumes strict naming conventions and loads
    everything into memory; there’s no progress/logging, so traversing a big Camera Roll may feel opaque.
  - hash.py:7 – CLI that salts and hashes a user-provided string, generates a random 16-char key, obfuscates it with a keyboard “shift
    right,” and verifies the reversible mapping (hash.py:82). Good toy example, but presenting the SHA-256 digest as an “encrypted message”
    and echoing the plaintext back (hash.py:102) could mislead someone into thinking it’s secure messaging.
  - decrypt.py:3 – Companion script that asks for the hash, salt, and shifted key, decodes the key with the same keyboard map
    (decrypt.py:42), and recomputes the salted SHA-256 to verify the original input (decrypt.py:46). Input validation is minimal—
    bytes.fromhex will throw if you mistype the salt—and the “encrypted message” is never actually decrypted because hashing is one-way.
  - wordsort.py:1 – Maintains a large vocabulary list inline, strips the bullet markers, sorts case-insensitively, and reports duplicates
    plus the count of words that only appear once (wordsort.py:238). Duplicated entries like “Accession” and repeated Hitchens excerpts are
    surfaced via the repeated_words list (wordsort.py:234); if you need case folding or deduped definitions you’ll have to extend it.

  Docs & Meta

  - bianchi.py:1 – Set of four Manim scenes illustrating Rindler horizons, detector transition rates, quantum surface facets, and entropy
    derivations; heavy use of LaTeX-based MathTex objects and axes plotting (bianchi.py:50). The file references np.exp for the Boltzmann
    curve (bianchi.py:60) but never imports NumPy, so rendering raises a NameError.
  - grammar.py:1 – Massive one-file document auditor defined entirely inside a raw triple-quoted string (grammar.py:1) and written out
    to /mnt/data/doc_audit.py when this file runs (grammar.py:689). The intended helper reqs is never defined before writing /mnt/data/
    doc_audit_requirements.txt (grammar.py:692), so executing grammar.py fails immediately; to use the auditor you’d need to extract the
    string contents manually.
  - conlaw.qmd:1 – Quarto notebook of constitutional-law notes with tables, case summaries, doctrinal outlines, and IRAC guidance; no
    executable code, just carefully structured Markdown (e.g., “Week 1.2” table at conlaw.qmd:12). Rendering this gives you a richly
    formatted HTML study guide.
  - Makefile:1 – Single commit target that stages everything, commits with a timestamped message, and pushes to origin main (Makefile:4).
    Handy shortcut but dangerous if you’re on another branch or have untracked files you don’t want committed.
  - README.md:1 – Minimal placeholder containing only the repo title “nonsense”; there’s no catalog of the scripts, which is why this tour
    is useful.
  - wechat.py – Empty placeholder (0 bytes). Likely earmarked for a future automation script; currently importing it would do nothing.
