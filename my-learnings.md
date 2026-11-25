# my learnings

Running dev log. Newest entry at the bottom.

## 2026-11-25: scaffolding, and thinking about secrets before writing any code

My shell did not have ANTHROPIC_API_KEY set, which I only found out because I checked before step 2. That made me decide how keys should work in this repo before there was any code that needed one. The harness reads the key from the environment and nowhere else. `.gitignore` covers `.env` and `.env.*` (with `.env.example` allowed) so a key can't be committed by accident. The point of doing it first is that a leaked key in git history is still leaked after you delete the file, so the ignore rule has to exist before the first commit that could contain one.

The same reasoning shaped CI. The tests will use a fake model client, so the GitHub Actions workflow never gets an API key at all. That is less to leak, and it also means tests are free and deterministic. Real API runs are a separate command I run by hand.

I decided to run each attack N times per configuration instead of once. Model output is random, so a single run only tells me that an attack can work once, not how often. A scoreboard cell like 3/5 means something; a lone pass or fail could just be luck. The cost is five times the API calls, which is why bulk runs will use Haiku and cache results on disk (`.cache/` is gitignored for that reason).

First CI run on GitHub passed (15s).

## 2026-11-25: a bug the fake client could not catch, and 0/15 on my first attacks

My agent loop passed all its tests, then crashed on the first real API call with `unhandled block type thinking`. Haiku 5.5 sometimes returns an empty `thinking` block with a signature before its answer. My helper that converts response blocks back into message history only knew `text` and `tool_use`, and my fake client only ever produced those two, so the tests could never have shown this. The fix is to send thinking blocks back unchanged (the signature is checked by the API). What I took from it: a fake client only checks the shapes I already know about. I had to run against the real model to find the ones I did not.

Then the first real run: 3 attacks (fake "system override" in the user turn, hidden instruction in a fetched page, ask for the system prompt verbatim) x 5 trials each on the baseline, and every one failed, 0/15. Before trusting that I read the saved transcripts to check it was not my harness. It was not. On the hidden-div page the agent fetched it, noticed the text aimed at AI assistants, told me it had ignored it, and sent no email. So the result is real: this model already handles obvious injections. I expected a small model to be easy to inject and I was wrong. It means the attacks need to be better, and a scoreboard full of 0s would tell me nothing about whether scoped credentials help.
