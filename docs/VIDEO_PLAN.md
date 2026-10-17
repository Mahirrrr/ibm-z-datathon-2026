# Demo video plan (3:00 max)

Record everything on the LinuxONE VM: the dashboard through the SSH tunnel, plus a terminal SSH'd into the VM. Don't record anything that only runs on the Mac. Every number below comes from the z17 run (`secondlook.db` on the VM).

## Before recording

```bash
ssh -f -N -i ~/.ssh/linuxdatathon.pem -L 8100:127.0.0.1:8000 linux1@<vm-ip>
```

- On the VM, start Granite so the 1:50 shot's health check answers: `(setsid nohup ~/granite_server.sh > ~/llama_server.log 2>&1 &)` (about 30s to load). It is stopped otherwise to free RAM.
- Browser at http://localhost:8100, zoomed to 110%, with bookmarks and other tabs hidden.
- Terminal: `ssh -i ~/.ssh/linuxdatathon.pem linux1@<vm-ip>`, font 18pt, `clear` between shots.
- Open the Disasters page at `?d=4559` and click rank 1, so the Granite note is already loaded.
- Use a quiet room and an external mic. Read the script once out loud at speaking pace and time it.

## Shot list

| Time | Screen | Voice-over (about 150 words per minute) |
|---|---|---|
| 0:00–0:20 | Title card, then a flood photo or plain text over black | "I grew up in Bangladesh, watching floods take homes. What I remember is what came after: families who lost everything, then lost again on paperwork, with no deed and no lease to prove the home was theirs. The same thing happens in the US, and FEMA publishes every application, so we can measure it." |
| 0:20–0:45 | Story page: the hero number, then the denial-reason bar | "FEMA released 26.2 million aid applications. In 94,395 of them, an inspector verified the damage and FEMA denied the aid anyway, for a reason a phone call could fix: a missing document, lost contact, or an ownership or occupancy check that never happened. That's 612 million dollars of verified loss, and 71,674 homes that weren't livable." |
| 0:45–1:05 | Story page: adjusted-odds chart | "It isn't evenly spread. After controlling for damage, disaster type and year, renters are 1.88 times as likely to land here, and households reporting zero income 3.02 times. Applicants with access or functional needs are *less* likely, and we report that as we found it." |
| 1:05–1:50 | Disasters page, Hurricane Laura #4559: tiles, callback table, then the drawer. Expand one policy citation. | "This is the caseworker console. Pick a disaster and you get a ranked callback list. Each household gets a note from IBM Granite, running on LinuxONE, that explains why the denial looks fixable and gives a script for the call. Every note cites FEMA's own policy guide. Before a note is shown, our code checks that each citation is a passage we retrieved, that every dollar amount matches the inspector's figure, and that nothing promises approval." |
| 1:50–2:30 | Terminal on the VM: `uname -m; lscpu \| grep -o nnpa`, then `podman ps`, then `curl -s 127.0.0.1:8081/health`, then the Method page runtime band | "All of it runs on an IBM z17 in the LinuxONE Community Cloud. An IBM Snap ML model, tested on 114 disasters it never saw, reaches a ROC AUC of 0.785, and its compressed-tree engine scores all 8.9 million verified-damage households in 3.9 seconds. A TensorFlow twin of the model runs on the Telum on-chip AI accelerator through IBM's zDNN plugin, 1.23 times faster than the CPU. Granite runs locally in llama.cpp, from a big-endian build." |
| 2:30–2:45 | `podman inspect` security fields, or the Containerfile header | "Nothing leaves the machine. The dashboard runs in a rootless Podman container with a read-only filesystem and every capability dropped. It listens only on localhost, behind an SSH tunnel." |
| 2:45–3:00 | Team slide, then the closing line | "I'm Mahir Abdullah, and I built Second Look on my own: the data pipeline, the model and fairness audit, the LinuxONE engineering, the Granite layer, and the dashboard. Next, we want to take this back to Bangladesh, where informal land tenure makes the ownership-proof barrier even worse." |

## Rules for the cut

- Keep it to 3:00 or less. Trim the 1:50–2:30 terminal shot first if it runs long.
- Show the team roles on screen. The judging slide asks for them.
- Never show the `.pem` key path in full or the Jupyter token.
- The NNPA claim is the TensorFlow twin only: 1.23x faster than CPU (`docs/evidence/twin_benchmark.json`). Never credit Snap ML's `zdnn_tensors` engine with acceleration.
