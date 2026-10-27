# JD Analytics acceptance record

Updated: 2026-10-27. This is a local handoff record based on outputs and browser results reported during this task. “Passed” means an observed result was reported; it does not imply every case was repeated from a clean checkout. No additional Groq request was made for this handoff.

## Automated checks

| Check | Observed result | Status |
| --- | --- | --- |
| Full backend suite (`pytest -q`) | User reported 20 passed in 1.29 s. One Starlette/httpx TestClient deprecation warning. | Passed (reported) |
| Backend suite rerun during handoff preparation | This environment reached the first API TestClient test after 13 earlier tests passed, then stopped making progress. The isolated API TestClient test also did not finish; both runs were interrupted. | Pending here; not a test failure, but current rerun could not be verified |
| Frontend production build | User reported Vite build succeeded; 17 modules transformed. | Passed (reported) |
| Frontend build rerun during handoff preparation | `npm.cmd run build` completed successfully; 17 modules transformed. | Passed (verified) |
| GitHub push | Local commit `d6aea04739876ae5c555bbf9ad1f2faac2fa2782` was pushed to `origin/master`; `git ls-remote` returned the same commit SHA. | Passed (verified) |
| TEAM-V1 expected JSON syntax | `samples/jd_reviewed.json` parses as JSON. | Passed (verified) |
| Fresh-checkout reproducibility | Not run from a clean clone. | Pending |

## Functional acceptance

| Scenario | Observed result | Status |
| --- | --- | --- |
| JD A normal extraction and reviewed export | User reported the synthetic JD A was reviewed and downloaded; `samples/jd_reviewed.json` is the fictional hand-labelled expected fixture. | Passed (reported; fixture is not a live result) |
| JD B and JD C normal extraction | User reported completing the normal-JD review flow; JD C showed four skills and two groups (Python AND SQL mandatory; AWS OR GCP preferred). | Passed (reported) |
| JD A-C source fixture formats | JD B and JD C TXT, DOCX, and selectable-text PDF fixtures were added. The reader returns text matching each corresponding TXT fixture. | Passed (verified for file reading; not a live extraction claim) |
| Empty, corrupt, and wrong-type files | Reported responses: empty/corrupt inputs returned 422; wrong `.txt` upload returned 415. | Passed (reported) |
| Consent off / missing key / provider timeout | Offline path returned manual `needs_review`; missing key and mocked timeout returned service-unavailable errors. | Passed (reported/mock-tested) |
| Narrow viewport and keyboard access | After the text-size adjustment, the page was rechecked at a 390 px responsive viewport. Document/body widths were 390 px, helper text measured 16 px, and Tab navigation showed visible focus on controls. | Passed (verified during this handoff) |
| Unfamiliar skills and embedded instruction | An earlier live synthetic run identified Polars/Apache Arrow and AWS/GCP and ignored the embedded instruction, but marked skills high/claimed rather than uncertain. This did not meet the uncertainty expectation. | Failed (earlier live run) |
| Follow-up after uncertainty-prompt change | One authorized Groq request returned an application error: “A requirement group referenced an unknown skill.” The backend now instructs Groq to reuse exact proposed skill names and reports mismatched names safely; a mocked regression test covers the failure. No further live request was made. | Mock fix verified; live provider behavior remains pending |

## Handoff items and limitations

- The reviewed TEAM-V1 fixture and fictional JD A-C text/PDF/DOCX source fixtures are in `samples/`.
- The new PDFs were visually inspected. Their matching DOCX paragraph content and TEAM reader text were verified; the prescribed DOCX image renderer could not run because bundled LibreOffice is unavailable in this environment, so DOCX visual rendering remains unverified.
- The personal-named PDF `samples/jd_a-Lakshita.pdf` is intentionally ignored by Git and must stay local.
- Browser screenshots were shared in chat but were not saved into the workspace. Save non-sensitive screenshots of a successful review/export and a recoverable error state into a handoff evidence folder if the team requires image files.
- The live unfamiliar-skill scenario is not accepted yet; the latest attempt failed while mapping requirement group skill names to IDs. Do not describe this behavior as verified.
- The README and pinned Python requirements are now present. Clean-copy verification and screenshot files remain pending.
- The frontend production build succeeded during handoff preparation. The 390 px viewport and keyboard pass was completed after the text-size change.
- The app has in-memory storage and does not implement OCR or broader RADIX integration. The GitHub repository exists and the current branch is pushed, but collaborator access and a clean-clone verification remain pending.
