# Lessons For Future Explainers

This file records reusable lessons from real review sessions. Treat these as operational rules when building or modifying an interactive paper explainer, especially during feedback-driven edits.

## 1. Respect The User's Current Mental Context

- The page the user is looking at is the source of truth. Preserve the current tab, anchor, and learning flow when applying feedback.
- If a user comments from `braingood`, do not refresh them into `braindead` or make them hunt for the changed block.
- Keep `data-cf-change` anchors stable. Browser history and feedback history depend on them.
- When changing a specific block, verify that exact block in the browser, not merely that the file changed.

## 2. Feedback Means Rebuild The Mental Model

- Frustrated feedback such as "I do not understand", "be more clear", "show me visually", "what does this mean", or "this is a mess" means the weak block needs a teaching-board upgrade, not another paragraph.
- Take the user's wording literally. If they ask what "250 samples" means, show time ticks. If they ask what "17 channels" means, show the named channels and scalp regions.
- Remove vague filler. Phrases like "pixels/features", "selected channels", "embedding", "score", and "samples" must be unpacked into visible objects.
- Prefer one clean explanation surface over many disconnected cards.

## 3. Put Concrete Evidence First

- Show the actual paper object or dataset example before explaining the abstraction: a paper figure crop, stimulus image, matrix, channel map, waveform, timeline, score gauge, or candidate set.
- Paper crops and dataset images are evidence, not decoration. They must be large enough to inspect.
- Do not use fixed-height `object-fit: cover` thumbnails for evidence images. Use `object-fit: contain`, stable dimensions, clear captions, and deliberate crops only when the crop itself is explained.
- If an image asset is low resolution, avoid making it carry fine detail. Pair it with a larger schematic that explains what to inspect.

## 4. Design Teaching Boards, Not Poster Walls

- A good board shows visible object -> hidden representation -> comparison/score -> next action.
- For pipelines and loops, every stage needs a surface layer and a data layer.
- Do not use equal-height card rows when one card has much more content. Dense transformations should span the row or become their own row.
- Avoid tall blank columns, cropped labels, tiny thumbnails, and cramped side-by-side cards.
- If a comparison has two routes, such as CLIP vs PSD, show them as parallel routes with matching structure.

## 5. Explain Hidden Data Shapes Visually

- Matrices need rows, columns, labels, and one example cell.
- Time samples need a ruler/timeline, not just "250 samples".
- Channels need exact names and grouping when the paper gives them.
- Embeddings need a "coordinates for search" visual: nearby candidates, distance, or vector bars.
- Scores need a visible meter or distance comparison and a clear explanation of how higher score changes the next batch.

## 6. Verify At The Actual Browser Width

- The in-app browser can be narrower than desktop screenshots. Measure the actual viewport and inspect that rendered layout.
- After every significant visual change, reload the local server page, scroll to the exact anchor, take a screenshot, and inspect DOM dimensions for the changed elements.
- Check that feedback/publish launchers do not cover important content.
- Breakpoints should be based on actual readability, not generic desktop/mobile assumptions.

## 7. Publish Belongs To The Current Local Explainer

- The local review copy is where learning and feedback happen. GitHub Pages is a static mirror.
- The publish button must live in the local explainer UI, stay visible, and clearly apply to the current explainer.
- Grey/disabled means this current explainer has no unpublished static changes. Enabled means the current local explainer can be published.
- Do not auto-publish after edits unless the user explicitly clicks/asks. Let the user decide when the page is good to go.

## 8. Keep Feedback Processing Trustworthy

- Process only unhandled comments, and record handled comment ids in `feedback/history.json`.
- Preserve user edits and unrelated changes.
- Make scoped edits that answer the feedback, then verify visually.
- If the output still requires the user to manually search for the fix, the feedback loop failed.

## 9. Default Visual QA Checklist

Before calling a visual change done:

- Can the reader understand the mechanism from the visual itself?
- Is every evidence image uncropped and inspectable?
- Are the exact paper facts visible where needed?
- Are there no blank towers, cramped cards, or overflowing labels?
- Are the changed anchors still present?
- Did the browser screenshot at the actual viewport look sane?
