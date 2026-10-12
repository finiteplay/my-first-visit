# Research dossier schema

The research directory contains `corpus.csv`, `dossier.yaml` and eventually `REVIEW.md`.
The YAML file uses JSON syntax until the project adopts a general YAML parser.

## corpus.csv

Required columns:

```text
id,url,platform,source_role,published_at,trip_date,traveler_origin,trip_style,season,firsthand,topics,notes
```

- `id`: stable source/account ID. One independently attributable traveler account per row.
- `url`: direct HTTPS link.
- `platform`: source community or publisher, such as `reddit-visitingiceland`,
  `tripadvisor-iceland`, `rick-steves-forum`, `safe-travel`.
- `source_role`: `traveler`, `editorial`, `official`, `provider`, or `reviewer`.
- `published_at`: `YYYY-MM-DD`.
- `trip_date`: `YYYY-MM-DD`, `YYYY-MM`, `YYYY`, or `unknown`.
- `traveler_origin`, `trip_style`, `season`: known value or `unknown`; never infer identity.
- `firsthand`: `true` only when this row is the speaker's own experience.
- `topics`: semicolon-separated topic IDs.
- `notes`: concise paraphrase relevant to the topics. Do not paste source prose.

## dossier.yaml

```json
{
  "schemaVersion": 1,
  "country": "IS",
  "audience": "en-US:first-time",
  "asOf": "2026-10-10",
  "status": "draft",
  "researchWindowMonths": 24,
  "travelModes": [
    {
      "id": "compact-campervan",
      "status": "primary",
      "travelerFit": "Travelers who accept compact living in exchange for route flexibility",
      "advantages": ["Transport, bed and simple cooking stay together"],
      "frictions": ["Campsite dependence", "Wet-weather living space"],
      "seasonality": "Verify heating and open campsites outside summer",
      "sourceIds": ["r001", "o001"],
      "coverage": ["briefing:start-here", "playbook:campervan"]
    }
  ],
  "batches": [
    {
      "id": "b01",
      "scope": "Recent US self-drive trip reports",
      "sourceIds": ["r001", "r002"],
      "newHighImpactTopics": ["car-coverage"],
      "newDecisionFactors": ["wind-door exclusion"]
    }
  ],
  "topics": [
    {
      "id": "car-coverage",
      "title": "Decide rental coverage before the counter",
      "importance": "core",
      "risk": ["insurance"],
      "signal": "split",
      "sourceIds": ["r001", "r002", "p001"],
      "anecdotes": [
        {
          "sourceId": "r001",
          "stance": "damage-covered",
          "context": "Summer South Coast self-drive",
          "event": "A stone chipped the windshield on a paved road.",
          "action": "The traveler had selected glass coverage before arrival.",
          "outcome": "The reported repair was handled under that policy."
        }
      ],
      "synthesis": {
        "travelerPattern": "Travelers repeatedly raise gravel, glass and wind damage.",
        "counterPattern": "Others report uneventful trips or different exclusions.",
        "decisionHelp": "Compare exclusions, excess and reimbursement before departure.",
        "verify": "Obtain current written terms from the card issuer and rental provider.",
        "limits": "Forum recurrence does not establish an incident rate."
      }
    }
  ]
}
```

Allowed topic values:

- `importance`: `core`, `supporting`
- `signal`: `repeated`, `split`, `emerging`, `single-anecdote`
- sensitive `risk`: `safety`, `health`, `legal`, `emergency`, `insurance`

Allowed travel-mode `status` values are `primary`, `supporting` and `excluded`. Every mode needs
source IDs. Primary and supporting modes also need traveler fit, advantages, frictions,
seasonality and content coverage. An excluded mode needs a concrete reason. The list records a
completed discovery decision; it is not a universal mode checklist.

Move `status` to `review-ready` only when the strict audit and research stopping rule pass.
Publication approval is a different state.
