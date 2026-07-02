#!/usr/bin/env python3
"""Render README.md from data/startups.json — recently-funded AI startups, grouped by sector.

data/startups.json: {"updatedAt": "YYYY-MM-DD", "startups": [ {company, handle, amount, amount_usd,
round, sector, description, lead_investors, other_investors, founders, location, funded_at, source_url,
from_roundup}, ... ]}
Run: python3 build.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
SITE = "https://landed.jobs"
ORG = "https://github.com/landedjobs"
BRAND = "Landed"

# Sector → (emoji, anchor). Order sets section order in the README.
SECTORS = [
	("AI Infrastructure", "🏗️"),
	("Agents & Automation", "🤖"),
	("Developer Tools", "🛠️"),
	("Data & Analytics", "📊"),
	("Healthcare & Bio", "🧬"),
	("Robotics & Hardware", "🦾"),
	("Fintech", "💳"),
	("Security", "🔐"),
	("Legal & Compliance", "⚖️"),
	("Sales & GTM", "📈"),
	("Enterprise SaaS", "🏢"),
	("Consumer", "🛍️"),
	("Defense & Aerospace", "🛰️"),
	("Climate & Energy", "🌱"),
	("Other", "🧩"),
]
SECTOR_EMOJI = dict(SECTORS)


def anchor(sector: str) -> str:
	import re
	return re.sub(r"[^a-z0-9]+", "-", sector.lower()).strip("-")


def load():
	d = json.loads((HERE / "data" / "startups.json").read_text(encoding="utf-8"))
	return d.get("updatedAt"), d["startups"]


def esc(s) -> str:
	return (s or "").replace("|", "&#124;").replace("<", "&lt;").replace(">", "&gt;").strip()


def money(n) -> str:
	if not n:
		return ""
	if n >= 1_000_000_000:
		return f"${n / 1_000_000_000:.1f}".rstrip("0").rstrip(".") + "B"
	if n >= 1_000_000:
		return f"${round(n / 1_000_000)}M"
	if n >= 1_000:
		return f"${round(n / 1_000)}K"
	return f"${n}"


def age(iso: str, now: datetime) -> str:
	if not iso:
		return ""
	try:
		d = (now - datetime.fromisoformat(iso)).days
	except ValueError:
		return ""
	if d <= 0:
		return "this week"
	if d < 7:
		return f"{d}d ago"
	if d < 60:
		return f"{d // 7}w ago"
	return f"{d // 30}mo ago"


def avatar(handle, company) -> str:
	initial = (company or "?").strip()[:1].upper() or "?"
	fb = f"https://ui-avatars.com/api/?name={quote(initial)}&size=64&background=00A86B&color=fff&bold=true&format=png"
	if handle:
		return f"https://unavatar.io/x/{handle}?fallback={quote(fb, safe='')}"
	return fb


def btn(url, asset, alt) -> str:
	return f'<a href="{url}"><img src="assets/{asset}" width="168" alt="{alt}"></a>'


def row(s, now) -> str:
	company, handle = s.get("company", "—"), s.get("handle")
	name_link = f'https://x.com/{handle}' if handle else s.get("source_url", "#")
	who = (
		f'<a href="{name_link}"><img src="{avatar(handle, company)}" width="46" height="46" alt="{esc(company)}"></a><br>'
		f'<b><a href="{name_link}">{esc(company)}</a></b>'
	)
	if s.get("location"):
		who += f'<br><sub>📍 {esc(s["location"])}</sub>'

	amt = s.get("amount") or money(s.get("amount_usd"))
	raised = f'<b>{esc(amt)}</b>' if amt else "—"
	if s.get("round"):
		raised += f'<br><sub>{esc(s["round"])}</sub>'
	if a := age(s.get("funded_at"), now):
		raised += f'<br><sub>🗓️ {a}</sub>'

	what = esc(s.get("description", ""))
	if s.get("founders"):
		what += f'<br><sub>🧑‍💼 {esc(", ".join(s["founders"]))}</sub>'
	backers = s.get("lead_investors") or []
	others = s.get("other_investors") or []
	if backers or others:
		lead = ", ".join(f"<b>{esc(b)}</b>" for b in backers)
		rest = ", ".join(esc(o) for o in others[:4])
		line = " · ".join(x for x in [lead, rest] if x)
		what += f'<br><sub>💰 {line}</sub>'

	go = btn(f'https://www.google.com/search?q={quote(company + " careers jobs")}', "btn-careers-v2.svg", "Careers")
	if s.get("source_url"):
		go += "<br>" + btn(s["source_url"], "btn-raise-v2.svg", "The raise")
	return (
		f'<tr><td align="center" width="130">{who}</td><td align="center" width="90">{raised}</td>'
		f'<td>{what}</td><td align="center" width="180">{go}</td></tr>'
	)


def table(rows, now) -> str:
	# Raw HTML table: markdown tables can't set td width, and without a fixed Go column
	# GitHub's forced img{max-width:100%} lets the text column crush the buttons to nothing.
	head = '<tr><th align="center">Company</th><th align="center">Raised</th><th align="left">What they do &amp; who backed them</th><th align="center">Go</th></tr>'
	return "<table>\n" + "\n".join([head] + [row(s, now) for s in rows]) + "\n</table>"


def section(sector, emoji, items, now) -> str:
	if not items:
		return ""
	items = sorted(items, key=lambda s: s.get("amount_usd") or 0, reverse=True)
	return (
		f'<a name="{anchor(sector)}"></a>\n## {emoji} {sector} · {len(items)}\n\n'
		f"{table(items, now)}\n\n[⬆ back to top](#top)\n"
	)


def main():
	updated, startups = load()
	now = datetime.now(timezone.utc).replace(tzinfo=None)
	today = updated or now.strftime("%Y-%m-%d")
	total_cap = sum(s.get("amount_usd") or 0 for s in startups)

	by_sector = {name: [s for s in startups if s.get("sector") == name] for name, _ in SECTORS}
	# fold any unknown sector into Other
	known = set(by_sector)
	for s in startups:
		if s.get("sector") not in known:
			by_sector["Other"].append(s)

	top = sorted([s for s in startups if s.get("amount_usd")], key=lambda s: s["amount_usd"], reverse=True)[:12]

	nav = " · ".join(
		[f"[💸 Biggest raises](#biggest-raises)"]
		+ [f"[{emoji} {name}](#{anchor(name)})" for name, emoji in SECTORS if by_sector[name]]
	)
	toc = "\n".join(
		[f"- [💸 Biggest raises this month](#biggest-raises) · **{len(top)}**"]
		+ [f"- [{emoji} {name}](#{anchor(name)}) · **{len(by_sector[name])}**" for name, emoji in SECTORS if by_sector[name]]
	)
	sections = "\n---\n\n".join(section(name, emoji, by_sector[name], now) for name, emoji in SECTORS if by_sector[name])

	readme = f"""<a name="top"></a>

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="Recently Funded AI Startups Hiring" width="100%">
</picture>

![Startups](https://img.shields.io/badge/{len(startups)}%20funded%20startups-ff5b29?style=flat-square) ![Capital](https://img.shields.io/badge/{money(total_cap).replace('$', '%24')}%2B%20raised%20tracked-00A86B?style=flat-square) ![Updated](https://img.shields.io/badge/updated-{today.replace('-', '.')}-6C2BD9?style=flat-square) [![Stars](https://img.shields.io/github/stars/landedjobs/recently-funded-ai-startups-hiring?style=social)]({ORG}/recently-funded-ai-startups-hiring)

**AI startups that just raised — sorted by sector, newest capital first.**
Fresh funding means fresh headcount. These teams are staffing up *right now*, often before a single role hits the job boards.

*Curated weekly by [{BRAND}]({SITE}).*

{nav}

</div>

---

> **Why a funding list is a job list** — a round closes, the team's #1 job becomes hiring, and for a few weeks the fastest way in is to reach the founder directly (the people in these posts) before the careers page even updates. This list tracks who just raised, what they do, and who backed them — so you can apply while the door is widest. ⭐ **Star it** — refreshed weekly.

## Jump to

{toc}

> ➕ **Spotted a raise we're missing?** [Add it →]({ORG}/recently-funded-ai-startups-hiring/issues/new?template=add-startup.yml) · see [CONTRIBUTING](CONTRIBUTING.md)

---

<a name="biggest-raises"></a>
## 💸 Biggest raises this month · {len(top)}

_The largest rounds in the window — the teams with the most new runway to spend on people._

{table(top, now)}

[⬆ back to top](#top)

---

{sections}

---

## How this list is built

We track fresh AI funding announcements (bootstrapped from [@fundable_ai](https://x.com/fundable_ai), expanding to more sources), pull out what each company does, the round, and the backers, and sort them by sector. Roundup posts are expanded so every company gets its own row. It's a weekly snapshot — always confirm a company is hiring your role before you reach out.

**Know a raise we missed?** [Add it]({ORG}/recently-funded-ai-startups-hiring/issues/new?template=add-startup.yml) or open a PR editing `data/startups.json`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## How to actually get hired at a fresh-funded startup

Right after a raise, the founder is the hiring manager and cold, specific outreach works. Reference the round, show one relevant thing you've built, and be clear about the role you'd own. Fewer, sharper applications beat the spray — [{BRAND}]({SITE}) brings you matched roles daily, drafts your answers to each application's questions, and preps you with courses and voice mock interviews.

**[Get started free → {SITE}]({SITE})**

## Related

- 🧭 [awesome-ai-native-jobs]({ORG}/awesome-ai-native-jobs) — the umbrella for the whole family
- 🔥 [whos-hiring-in-ai]({ORG}/whos-hiring-in-ai) — real hiring posts from founders on X
- 🚀 [ai-engineer-jobs]({ORG}/ai-engineer-jobs) — 300 live AI engineer roles, auto-updated

<div align="center">
<sub>{len(startups)} startups · {money(total_cap)}+ tracked · updated {today} · maintained by <a href="{SITE}">{BRAND}</a>. Funding data from public announcements; verify before acting. Not affiliated with the listed companies or investors.</sub>
</div>
"""
	(HERE / "README.md").write_text(readme, encoding="utf-8")
	dist = ", ".join(f"{name}:{len(by_sector[name])}" for name, _ in SECTORS if by_sector[name])
	print(f"README.md: {len(startups)} startups, {money(total_cap)} tracked · {dist}")


if __name__ == "__main__":
	main()
