# Country pack review — `<country>`

Status: **draft / review-ready / approved / blocked**  
Audience lens: `<origin, first-time/repeat, trip modes>`  
Research as of: `YYYY-MM-DD`  
Pack/content version: `<version or commit>`  
Reviewer roles: `<evidence, editorial, traveler, native/resident, specialist>`

Never delete a failed round. Append the revision and rerun so the report shows why the content
changed and which checks were actually repeated.

## Automated gates

| Check | Command | Date | Result | Evidence or failure |
|---|---|---|---|---|
| Research structure | `python tools/content/audit_research.py content/<cc>/research --strict` | | | |
| Country source shape | `<country-specific command>` | | | |
| Media and rights | `<inventory command or review>` | | | |

An automated pass proves only the stated structure. It is not editorial, traveler, native,
safety or rights approval.

## Topic review

Copy one row per core briefing or playbook. Score with
`.agents/skills/verify-country-pack/references/quality-rubric.md`.

| Topic | Critical zeros? | Experience score / 12 | Evidence gaps | Required revision | Rerun result |
|---|---:|---:|---|---|---|
| | | | | | |

## Travel-mode coverage

| Mode | Status | Evidence of use/fit | Distinct advantages and frictions | Reader coverage | Traveler task/result |
|---|---|---|---|---|---|
| | | | | | |

## Material and sensitive claims

| Claim ID | Reader claim | Evidence role and source | Freshness | Limitation/live handoff | Reviewer/result |
|---|---|---|---|---|---|
| | | | | | |

## Traveler-task tests

Repeat this block for each realistic decision. Give the reviewer only the content a traveler
would see; do not coach them toward the intended answer.

### Task `<id>` — `<decision>`

- Traveler profile:
- Content provided:
- Time to usable answer:
- Options identified:
- Trade-offs identified:
- Preparation steps identified:
- Uncertainty or live check identified:
- Next action identified:
- Confusion or unsupported inference:
- Result: **PASS / FAIL**
- Revision:
- Rerun date, reviewer and result:

Pass only when the reviewer finds options, trade-offs, preparation, uncertainty and a next
action within 90 seconds without inventing a material fact.

## Native, destination and specialist review

| Scope | Named reviewer and role | Exact files/version | Date | Result | Required changes |
|---|---|---|---|---|---|
| Language and pronunciation | | | | | |
| Destination context | | | | | |
| Safety/health/legal/insurance as applicable | | | | | |

## Revision log

| Round | Failed criterion or new evidence | Change made | Checks rerun | Result | Remaining limitation |
|---|---|---|---|---|---|
| 1 | | | | | |

## Release decision

- Deterministic strict audit: **PASS / FAIL**
- Every core topic: **at least 10/12 and no zero / FAIL**
- Planned traveler tasks: **PASS / FAIL**
- Required named reviews: **PASS / FAIL**
- Media rights and hashes: **PASS / FAIL**
- Fast-changing claims have live handoffs: **PASS / FAIL**
- Known limitations still visible to readers/reviewers:
- Decision and approver: **APPROVE / REVISE / BLOCK**, `<name/role/date>`
