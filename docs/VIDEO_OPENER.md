# Video opener: "Second Look" (about 14 seconds, then you on camera)

Total video limit is 3:00, so the opener should finish by about 0:14 and your intro by about 0:45.

## How to build it in Higgsfield

1. Make **one still image** of the village first (prompt S0). Every clip uses that image as its **start frame**, so the place looks the same before and after each blink.
2. Generate the clips below with image-to-video. Make them 5s each; you'll trim them in the editor.
3. Do the **blinks and titles in your editor** (CapCut, Premiere, DaVinci), not in Higgsfield. AI video garbles text, and an editor blink lands exactly on the beat.

## Prompts

**S0: start image (image model, 16:9)**
> Cinematic wide shot of a small rural village at golden hour, tin-roof houses and wooden homes close together, laundry on lines, a dirt path through the middle, a child's bicycle leaning on a fence, warm soft sunlight, light haze, peaceful and lived-in, eye-level documentary photography, 35mm lens, natural colors, no people in focus, no text

**C1: calm (image-to-video from S0, 5s)**
> Same village, gentle breeze moves the laundry and tree leaves, slow push-in at eye level, birds cross the sky, warm late-afternoon light, calm and quiet, handheld documentary feel, no text

**C2: on fire (image-to-video from S0, 5s)**
> The exact same village and camera angle, now engulfed in a wildfire: flames climbing the tin-roof houses, thick orange smoke rolling across the path, embers drifting toward the camera, sky turned dark amber, laundry burning on the lines, the bicycle silhouetted against the fire, slow push-in, realistic, no people, no text

**C3: second look (image-to-video from S0, 5s)**
> The exact same village and camera angle after the fire: houses charred and roofless, smoke still rising, ash falling like snow, grey dawn light, the burned bicycle by the fence, a single sheet of paper blowing across the ash in the foreground, slow push-in, quiet and heavy, realistic, no people, no text

If the fire clip looks too clean, add: `photorealistic, news-footage grade, heat shimmer, dynamic smoke simulation`.

C3 is optional. You asked for fire on the second blink too. The aftermath version fits the story better, because Second Look is about what happens to people *after* the disaster. Use C2 again if you prefer the fire.

## Edit timeline

| Time | Picture | Sound |
|---|---|---|
| 0:00–0:03 | C1 calm village | Birds, wind, distant wind chime; a soft single piano note fades in |
| 0:03–0:035 | **Blink**: two black bars close from top and bottom over 6 frames, hold black 4 frames, open | Sharp breath in; all ambience cuts to silence |
| 0:035–0:06 | C2 village on fire | Fire roar and crackle hits at full volume; low sub-bass boom on the first frame |
| 0:06–0:08 | Hard cut to black. White text **IBM Z Datathon 2026** in IBM Plex Sans | **Click** (mechanical keyboard or camera shutter) as the text appears; fire drops to a muffled rumble |
| 0:08–0:10 | Black. **Second Look** fades in, IBM Plex Serif, larger | Low drone; a heartbeat thump |
| 0:10–0:105 | **Blink** again (same effect) | Breath; silence |
| 0:105–0:13 | C3 aftermath (or C2 fire) | Wind, falling ash, the paper rustling; drone continues |
| 0:13–0:14 | Fade or match cut to you on camera | Drone fades under your voice |

**Blink effect in CapCut:** add two black rectangles (top and bottom halves) and keyframe them closing to the middle and back open. Or search CapCut effects for "Blink" / "Eye close". Add a light blur ramp on the frames around it.

**Free sound sources:** Pixabay Sound Effects, Freesound.org, YouTube Audio Library. Search: "fire crackle roar", "village ambience birds", "keyboard click single", "sub boom cinematic", "heartbeat single", "sharp inhale", "paper rustle wind". For music, use an ambient piano or drone track in Pixabay Music (search "documentary tension ambient").

If you generate with a Higgsfield model that makes audio (such as a Veo-based model), turn its audio off and use your own sound. Generated audio rarely lands on the blink.

## Your intro (about 30 seconds, after the opener)

> I grew up in Bangladesh. Every monsoon, I watched floods take homes, and I watched families who lost everything get turned away from help because they couldn't prove they owned the land they lived on.
>
> That paperwork barrier isn't only a Bangladesh problem. FEMA publishes every application for disaster aid in the US: 26 million records. So I looked.
>
> 94,395 households had damage a FEMA inspector confirmed in person, and they were still denied. They weren't denied because the damage wasn't real. They were denied for a missing document, a phone number FEMA couldn't reach, or ownership nobody checked. That's 612 million dollars of verified loss. Renters were almost twice as likely to end up here.
>
> Every one of those is a phone call away from help. So I built Second Look: it finds them, ranks who to call first, and on IBM LinuxONE it writes the callback, citing FEMA's own policy.

Keep the Bangladesh part to what you saw yourself; no statistics about Bangladesh unless you have a source. The US numbers come from the z17 run: 94,395 households, $612M, renters 1.88x adjusted odds ("almost twice").

**Optional match cut:** end the opener on the paper blowing across the ash (C3), then cut to you holding a sheet of paper or tapping a printed denial letter. The paper is the visual thread from the fire to FEMA's paperwork.
