# Five-minute demo

Use the dashboard linked in README after the completion branch is deployed. Start the backend before presenting if using a free instance. Keep a local copy of the app and exported JSON available.

1. Click **Start new shipment**, then **Fill synthetic example**, then **Process email**. Explain that synthetic inputs are going through the real processing pipeline. SI has 3 containers; BL has 4. Show MISMATCH.
2. Expand container evidence. Show the exact source lines, not just a red badge. Enter a reviewer name and record review of the finding. This acknowledges a version; it does not approve the BL.
3. Edit the BL text to 3 containers and process again. Show OK, the fixed container difference, and the earlier review marked OUTDATED. This demonstrates that a previous review does not silently carry forward.
4. Change the BL discharge port to another port and process. Show the new mismatch. Remove the gross-weight line and process again: NEEDS_REVIEW must preserve the known port defect while showing UNKNOWN for missing weight.
5. Explain the human correction panel: use it only after checking the original source when extraction was wrong. Reviewer, reason, old/new value, and time are retained. If the source itself is wrong, upload/paste the corrected document instead.
6. Optionally use **Process an organizer inbox ZIP**, select the participant bundle, filter NEEDS_REVIEW, inspect an item, and download submission JSON. Counts are predictions, not an accuracy claim. Inbox results are held in browser memory; download before refreshing.

## One-sentence pitch

DraftGuard checks shipping documents with traceable evidence and rechecks revised drafts so teams can see which errors were fixed, which appeared, and which earlier reviews are no longer current.

## Be precise about scope

This is a working hackathon prototype with deterministic routing/extraction, four supported document formats, human review, revision checks, and evaluator export. It does not connect to live mailboxes, perform OCR, provide authenticated approval, or maintain a shared server history. Do not claim validated time savings or accuracy before measuring them.
