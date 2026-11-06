# Images

- `profile-light-background.png`: Carlos's original portrait from
  `public/images/profil-pic.jpg`, with the background lightened using built-in ImageGen.
  The original person was restored over the edit using a local person matte. The presentation
  still uses the original JPEG. The prompt and restoration tool are in prototype round 37.
  Selected as 37.1, then used as the lighter endpoint for the halfway version.
- `profile-light-background-v2.png`: revised edge treatment for the badge. All RGB comes from
  the original photo. A finer ImageGen alpha matte limits lightening to the background, so
  the subject is not composited from two different images. Round 38 records the revision;
  37.1 was preferred over this version.
- `profile-background-halfway.png`: an exact 50/50 RGB blend of the original portrait and
  37.1, rounded to the nearest integer. The face remains unchanged; the badge uses this copy.
  Prototype round 39 records the blend.
- `640k.png` and `owl.webp`: the slide animation references recorded in prototype rounds 31
  and 32.
