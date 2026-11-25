# my learnings

Running dev log. Newest entry at the bottom.

## 2026-11-25: scaffolding, and thinking about secrets before writing any code

My shell did not have ANTHROPIC_API_KEY set, which I only found out because I checked before step 2. That made me decide how keys should work in this repo before there was any code that needed one. The harness reads the key from the environment and nowhere else. `.gitignore` covers `.env` and `.env.*` (with `.env.example` allowed) so a key can't be committed by accident. The point of doing it first is that a leaked key in git history is still leaked after you delete the file, so the ignore rule has to exist before the first commit that could contain one.

The same reasoning shaped CI. The tests will use a fake model client, so the GitHub Actions workflow never gets an API key at all. That is less to leak, and it also means tests are free and deterministic. Real API runs are a separate command I run by hand.

I decided to run each attack N times per configuration instead of once. Model output is random, so a single run only tells me that an attack can work once, not how often. A scoreboard cell like 3/5 means something; a lone pass or fail could just be luck. The cost is five times the API calls, which is why bulk runs will use Haiku and cache results on disk (`.cache/` is gitignored for that reason).

First CI run on GitHub passed (15s).
