# README imagery

## VIDAA → CleanFrame comparison

`vidaa-to-cleanframe.gif` is a visual comparison, not a recording of the TV
switching screens or a measurement of launch speed.

- **Before:** the owner's photograph `IMG_4627.jpg`, supplied for the README on
  22 October 2026. The built-in image generation tool corrected daylight glare,
  straightened the display and cropped out the wall and bezel. It is an edited
  photo, not a direct screenshot. The original remains outside the repository.
- **After:** a Playwright capture of the actual CleanFrame interface using
  bundled public fonts, the Night wallpaper and five Home apps. The clock was
  fixed to match the photo. This is a browser preview, not a TV screenshot.
  `cleanframe-five-apps.jpg` provides a static alternative.
- **Animation:** FFmpeg assembled the frames with simple caption strips rendered
  in HTML. The 6.5-second loop holds VIDAA for two seconds, wipes for 0.75 seconds,
  holds CleanFrame for three seconds, then wipes back for 0.75 seconds. Output is
  960 × 584 at 12 fps, including the caption strip, with a shared GIF palette.

Promotional artwork and service marks in the before frame retain their owners'
rights. Wallpaper, font and icon sources for the after frame remain listed in
the project's asset registers and third-party notices.

### Photo-edit prompt

The built-in image generation tool received the owner-supplied photo and this
prompt (no CLI/API fallback was used):

```text
Use case: lighting-weather. Asset: the BEFORE frame of a truthful README comparison GIF. Input image 1 is the edit target: an actual photograph of a Hisense VIDAA television home screen taken in bright daylight. Correct the milky sunlight glare and exposure moderately to improve legibility, without changing any on-screen content. Straighten the slight perspective and crop to ONLY the illuminated television display, removing the wood bezel and surrounding wall. Output a clean landscape 16:9 rectangle, ideally 1920x1080, screen content edge-to-edge. Preserve the original exact UI layout, real Prime Video promotional image and woman, words LOVE OF YOUR LIFE, clock 14:48, Click OK to Watch focus, Recent and Trending on HBO Max headings, CleanFrame Home recent tile, all the app logos and lower sports banner. Preserve all original names, logos, positions and relative sizes. No redesign, new content, added elements, invented detail or new text. This must remain a faithful corrected photograph of the existing interface, not an illustrative recreation. Keep a natural display appearance; do not exaggerate contrast or make the original screen look worse for comparison.
```

## Earlier previews

`cleanframe-hisense.jpg` is the earlier three-app browser preview.
`cleanframe-dock.jpg` is retained from Nathan Clark's original CleanFrame project.
