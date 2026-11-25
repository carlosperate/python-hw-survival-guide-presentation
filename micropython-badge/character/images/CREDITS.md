# Images

- `profile-light-background.png`: Carlos's original portrait from
  `public/images/profil-pic.jpg`, with the background lightened using built-in ImageGen.
  The original person was restored over the edit using a local person matte (macOS Vision).
  The presentation still uses the original JPEG. It is the lighter endpoint of the halfway
  version.
- `profile-light-background-v2.png`: revised edge treatment for the badge. All RGB comes from
  the original photo. A finer ImageGen alpha matte limits lightening to the background, so
  the subject is not composited from two different images. `profile-light-background.png` was
  preferred over this version.
- `profile-background-halfway.png`: an exact 50/50 RGB blend of the original portrait and
  `profile-light-background.png`, rounded to the nearest integer. The face remains unchanged;
  the badge uses this copy.
- `640k.png` and `owl.webp`: the references for the slides' 640K and owl animations.
