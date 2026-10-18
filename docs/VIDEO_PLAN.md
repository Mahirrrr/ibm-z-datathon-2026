# Demo video plan (target 2:55, hard cap 3:00)

The screen footage is already recorded, from the live deployment on the z17. The browser clips go through the SSH tunnel to the Podman container, and the terminal clip runs on the VM itself. The files are in `video/clips/` (gitignored, local only):

| Clip | Length | What it shows |
|---|---|---|
| `01_story.mp4` | 26s | Story page: 94,395 hero → denial-reason bar → adjusted-odds chart → top disasters. Recorded before the county map and the $385.0M aid tile were added; re-record to show them. |
| `02_disaster.mp4` | 38s | Hurricane Laura console: tiles → callback list → click a row → Granite note → script → expand cited FEMA passage |
| `03_method.mp4` | 41s | Method page: model metrics → "How Granite writes the callback" → LinuxONE runtime → engine chart → TF/NNPA twin → stack table |
| `04_public_demo.mp4` | 7s | The same console on GitHub Pages, with the snapshot banner |
| `05_terminal_linuxone.mp4` | 46s | On the VM: `s390x`, `machine = 9175`, `nnpa`, the running container, its read-only/caps-dropped config, the live API, the Granite GGUF, the NNPA 1.23x result |

The opener is finished: `~/Downloads/second-look-opener/second_look_opener.mp4` (13.8s, with sound; details in `docs/VIDEO_OPENER.md`).

The screen clips are silent. Record the on-camera parts and the voice-over separately, then cut the clips to fit the voice.

## Script (about 380 spoken words, roughly 150 words per minute)

**[0:00–0:14] Opener.** No voice. Calm village, blink, fire, "IBM Z Datathon 2026", "Second Look", blink, aftermath with the blowing paper.

**[0:14–0:30] On camera.** Cut yourself out over the aftermath clip, then cut to plain you.

> What happens when you lose your home, and then lose the proof it was ever yours? We grew up in Bangladesh, watching that happen every monsoon. Families with no deed and no lease were turned away from help.

**[0:30–0:52] `01_story`, hero number.** Count-up from 0 to 94,395. A red DENIED stamp lands on the beat of "said no", with half a second of silence after it.

> That paperwork wall isn't only a Bangladesh problem. FEMA, America's disaster relief agency, publishes every application for aid: 26 million records. So we looked. In 94,395 cases, an inspector confirmed the damage in person, and FEMA still said no. Second Look finds them and gets them a callback.

**[0:52–1:10] `01_story`, denial-reason bar.** A phone rings out unanswered under "couldn't reach".

> They weren't denied because the damage wasn't real. They were denied for a missing document, a phone number FEMA couldn't reach, or ownership nobody checked. That's 612 million dollars of verified loss, and 71,674 homes that weren't safe to live in. Approved neighbors with the same damage got paid; by that yardstick, about 385 million dollars never reached them.

**[1:10–1:25] `01_story`, odds chart.** Zoom on the red bars.

> It falls hardest on renters, at 1.88 times the odds, and on households reporting zero income, at 3.02 times, even after controlling for damage.

**[1:25–2:05] `02_disaster`, whole clip.** Speed the scroll to 1.3x if needed. Keyboard typing under the Granite note, a soft ding when it finishes. Zoom on the cited passage.

> So we built Second Look. A caseworker picks a disaster and gets a ranked callback list. Call the top 1,000 it flags, and 419 are in that group. Call 1,000 at random, and you'd reach about 11. For each household, IBM Granite, running on the mainframe, explains why the denial looks fixable and drafts the call, citing FEMA's own policy guide. It's IBM's loan-approval lab in reverse: instead of explaining why a bank said no, it finds the people the system wrongly turned away. Our code checks every note's citations and dollar amounts, and that nothing promises approval. All 50 passed.

**[2:05–2:35] `05_terminal_linuxone` (first 25s), then `03_method` from the runtime band (about 0:20 on).** Speed-ramp the scoring run with a whoosh, then slow down on "3.9 seconds" and on the `nnpa` and `1.23` lines.

> All of it runs on an IBM z17 in the LinuxONE Community Cloud. A Snap ML model, tested on 114 disasters it never saw, reaches a ROC AUC of 0.785 and scores all 8.9 million households in 3.9 seconds. A TensorFlow twin runs on the Telum AI accelerator, 1.23 times faster than the CPU.

**[2:35–2:45] `05_terminal_linuxone` at the `podman inspect` line.** Zoom in.

> Nothing leaves the machine. It's a rootless, read-only container with every capability dropped, behind a tunnel, and no outside AI service ever sees a household.

**[2:45–2:58] All four of you on camera (plain, no cutout; one shared shot, or a quick cut of each person with a name caption), then deck slide 13, then `04_public_demo` with the URL as a caption.** End on the phone from 0:52 being picked up: the ring cuts off with a handset click.

> We're Team Second Look. Next, we want to take it home to Bangladesh, where proving you own your home is even harder. 94,395 households. One callback each.

## Recording tips

- Mahir records the full voice-over. Each teammate only needs a few seconds on camera for the 2:45 team shot.
- Read the on-camera lines (0:14 and 2:45) to the lens, not the screen. Record each one 3 times and keep the best.
- Record the voice-over in a closet or under a blanket for a dead room. Leave a one-second pause between paragraphs so it's easy to cut.
- If a section runs long, trim the terminal shot first, then the method page.
- The access-needs finding (those households are *less* likely to be in the cohort, OR 0.70) is cut from the voice-over for time. Keep it in the deck so the honesty point still reaches judges.
- Background removal: CapCut, **Video → Remove background → Auto removal**. Use a plain wall, front light, a locked camera, and framing from the waist up.

## Editing (CapCut, iMovie or Descript)

- Burn in captions. Judges often watch muted. Highlight "denied" in Carbon red `#DA1E28` and "Second Look" in IBM Blue `#0F62FE`.
- Cut or zoom every 2–4 seconds.
- Play quiet instrumental music under the voice, ducked to about -20 dB. Let it drop out completely for the DENIED beat.
- Sound effects (stamp, phone ring, typing, ding, whoosh): Pixabay Sound Effects. Don't use meme sounds or copyrighted songs.
- Export 1080p, H.264, 2:50–2:58. Upload it to YouTube as unlisted.

## Rules for the cut

- Keep it to 3:00 or less.
- Show all four team members on screen with name captions. The voice-over says "we" as a team; the deck's team slide credits the build to Mahir. Don't caption roles nobody did.
- Caption the opener "AI-generated illustration". It illustrates the story; it isn't footage of real events.
- Don't run demo footage through any generative tool. The rubric wants a real recording of the demo running live on LinuxONE.
- Never show the `.pem` key path, the VM IP or any Jupyter token. The recorded clips already hide them.
- The NNPA claim is the TensorFlow twin only: 1.23x faster than the CPU. Never credit Snap ML's `zdnn_tensors` engine with acceleration.
