# Demo video plan (target 2:50, hard cap 3:00)

The screen footage is already recorded, from the live deployment on the z17. The browser clips go through the SSH tunnel to the Podman container, and the terminal clip runs on the VM itself. The files are in `video/clips/` (gitignored, local only):

| Clip | Length | What it shows |
|---|---|---|
| `01_story.mp4` | 26s | Story page: 94,395 hero → denial-reason bar → adjusted-odds chart → top disasters |
| `02_disaster.mp4` | 38s | Hurricane Laura console: tiles → callback list → click a row → Granite note → script → expand cited FEMA passage |
| `03_method.mp4` | 41s | Method page: model metrics → "How Granite writes the callback" → LinuxONE runtime → engine chart → TF/NNPA twin → stack table |
| `04_public_demo.mp4` | 7s | The same console on GitHub Pages, with the snapshot banner |
| `05_terminal_linuxone.mp4` | 46s | On the VM: `s390x`, `machine = 9175`, `nnpa`, the running container, its read-only/caps-dropped config, the live API, the Granite GGUF, the NNPA 1.23x result |

The clips are silent. Record your voice-over separately, then cut the clips to fit it. To re-record any clip, run `node record.mjs` (browser) or `vhs terminal.tape` (terminal) in the session scratchpad's `rec/` folder.

## Timeline and script (about 400 words, roughly 150 words per minute)

| Time | Picture | Voice-over |
|---|---|---|
| 0:00–0:15 | Higgsfield B-roll (below), then a title card: **Second Look** · Team Second Look · IBM Z Datathon 2026 · SSF2026 | "I grew up in Bangladesh, watching floods take homes. The second loss came later, on paper: families with no deed, no lease, nothing to prove the home was theirs." |
| 0:15–0:40 | `01_story` 0:00–0:12 (hero → denial bar) | "FEMA publishes every aid application, 26.2 million of them. In 94,395, an inspector verified the damage and FEMA said no anyway, for reasons a phone call could fix: a missing document, lost contact, or ownership nobody checked. That's 612 million dollars of verified loss, and 71,674 homes that weren't livable." |
| 0:40–0:58 | `01_story` 0:12–0:24 (odds chart) | "It falls hardest on renters, at 1.88 times the odds, and on households reporting zero income, at 3.02 times, even after controlling for damage. People with access needs are actually *less* likely, and I report that as found." |
| 0:58–1:45 | `02_disaster` (whole clip; speed the scroll to 1.3x if needed) | "This is the caseworker console. Pick a disaster and you get a ranked callback list. For each household, IBM Granite, running on the mainframe, writes why the denial looks fixable and a script for the call, citing FEMA's own policy guide. It's IBM's loan-approval lab in reverse: instead of explaining why a bank said no, it finds families the system wrongly turned away. Before anything is shown, my code checks every citation, every dollar amount, and that nothing promises approval. All 50 notes passed." |
| 1:45–2:25 | `05_terminal_linuxone` (first 25s), then `03_method` from the runtime band (about 0:20 onward) | "Everything runs on an IBM z17 in the LinuxONE Community Cloud. A Snap ML model, tested on 114 disasters it never saw, reaches a ROC AUC of 0.785 and scores all 8.9 million households in 3.9 seconds. A TensorFlow twin runs on the Telum AI accelerator, 1.23 times faster than the CPU. Granite runs locally in llama.cpp, from a big-endian build." |
| 2:25–2:40 | `05_terminal_linuxone` at the `podman inspect` line (zoom in) | "Nothing leaves the machine. It's a rootless, read-only container with every capability dropped, behind a tunnel, and no third-party AI API ever sees a household." |
| 2:40–2:55 | Deck slide 12, then `04_public_demo` with the URL as a caption | "I'm Mahir Abdullah, and I built Second Look solo. Next, I want to take it home to Bangladesh, where proving you own your home is even harder. 94,395 households. One callback each." |

## Higgsfield: opener only

Use Higgsfield only for the first 10–15 seconds. **Don't run the demo footage through it.** Generative video can redraw the UI and the numbers, and the rubric wants a real recording of the demo running live on LinuxONE.

Make 2–3 clips of about 5 seconds each, in one style:

1. "Cinematic slow dolly shot over a flooded rural village in a river delta at dawn, tin-roof homes half submerged, monsoon clouds, soft golden light breaking through, muted teal and amber palette, documentary realism, no text, no faces in close-up"
2. "Close-up of a waterlogged paper document floating in muddy floodwater, ink running, shallow depth of field, slow push-in, somber documentary tone, muted colors, no readable text"
3. "Slow transition from floodwater ripples to a clean dark screen with soft blue light, minimal, cinematic, 16:9" (the bridge into the title card)

Caption these clips "AI-generated illustration". They illustrate your story; they are not footage of real events.

## Editing (CapCut, iMovie or Descript)

- Cut, zoom and caption in a normal editor. Descript can remove filler words and auto-caption.
- Zoom (Ken Burns, 120–140%) on the Granite note, the cited passage, and the `nnpa` and `1.23` lines in the terminal.
- Burn in captions. Judges often watch muted.
- Play quiet instrumental music under the voice, ducked to about -20 dB.
- Export 1080p, H.264, 2:45–2:55. Upload it to YouTube as unlisted.

## Rules for the cut

- Keep it to 3:00 or less. If it runs long, trim the terminal shot first.
- Show the team (Mahir Abdullah, solo) on screen.
- Never show the `.pem` key path, the VM IP or any Jupyter token. The recorded clips already hide them.
- The NNPA claim is the TensorFlow twin only: 1.23x faster than CPU. Never credit Snap ML's `zdnn_tensors` engine with acceleration.
