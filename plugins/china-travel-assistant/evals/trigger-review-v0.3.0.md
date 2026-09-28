# Trigger Review v0.3.0

The fixed corpus has eight positive and eight negative examples per Skill. The first five examples in each class form the adjustment set; the final three form the holdout set. This is a routing-description evaluation, not proof of live provider behavior.

Three independent Agent trials reviewed only the eight frontmatter descriptions and 48 holdout decisions each. Results were `48/48`, `45/48`, and `48/48` (aggregate `141/144`). The three disagreements in the middle trial were:

- `search-china-flights` negative "比较整个飞铁方案": a complete-trip request can lead to a later flight fact query, but should first route to the parent Skill.
- `search-china-trains` negative "比较整个机铁联运方案": same parent-versus-domain distinction for rail facts.
- `explore-china-routes` positive "比较分段票和直达票的总收益": without stated existing provider facts, this might require a fact query before the explorer can compare.

No holdout examples were edited after reviewing these results. The ambiguity should be addressed by a future corpus revision with an explicit distinction between initial routing and downstream delegation; a revised corpus must receive a new holdout. The trials read descriptions while a minor wording normalization was in progress, so these are directional evaluation results rather than a frozen-build benchmark.
