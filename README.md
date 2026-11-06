# maze-photos

Real photos and video frames of micromouse mazes at competitions, each matched to its maze in
[mazefiles](https://github.com/micromouseonline/mazefiles), with the four outer corners annotated. It documents which
maze was used where and what it looked like, and it is the test set of the photo → maze recogniser in
[maze-studio](https://github.com/Team-Micras/maze-studio).

## What is here

| Path | What |
|---|---|
| `index.json` | One entry per frame: competition, year, category, source (URL, timestamp, channel), licence, maze file and orientation, corners, lens fit, review |
| `incoming.json` | Frames collected since, not reviewed yet |
| `labels/` | One `maze-label/1` file per frame with a known maze (schema in `schema/`), and `labels/index.json` with the evaluation splits |
| `images/` | Only the images we may share (see below) |
| `reviews/` | The human review of the match and of the lens fit (verdicts and comments) |
| `coverage.csv` | Which mazefiles mazes have a frame and what was searched |
| `tools/` | The scripts used to scout, match, fit and check (working scripts; paths point at a local cache) |

Corners are listed NW, NE, SE, SW in the maze file's orientation, at the centre of the top of the corner posts, with
pixel centres at whole coordinates. Wall truth is the maze file itself.

## Licences

- Most frames come from public competition streams with no stated licence. For those the dataset carries only the
  reference (video URL and timestamp) and the annotation, never the image: fetch the frame from the source to use it.
- `images/` holds the frames from Creative Commons videos (credited in `ATTRIBUTION.md`) and Team Micras' own photos.
- Annotations, labels and reviews: [CC BY 4.0](LICENSE-DATA). Code in `tools/`: [MIT](LICENSE).

## Status

89 frames: 64 reviewed (52 with a confirmed maze, 12 of mazes not in mazefiles yet), 25 not reviewed yet. Mazes not
in mazefiles with a clean view are listed for transcription and will be offered back to mazefiles.
