# Contributing

A fresh, accurate funding list is only useful if it stays fresh. Two ways to help:

## 1. Suggest a raise (easiest)

[Open an "Add a startup" issue →](https://github.com/landedjobs/recently-funded-ai-startups-hiring/issues/new?template=add-startup.yml) with the company, amount/round, and a link to the announcement. New AI raises are especially welcome while they're recent.

## 2. Open a PR

The page is generated — **don't edit `README.md` directly** (it's overwritten on every build). Instead:

1. Add a startup object to `data/startups.json` (match the existing shape: `company`, `handle`, `amount`, `amount_usd`, `round`, `sector`, `description`, `lead_investors`, `other_investors`, `founders`, `location`, `funded_at`, `source_url`, `from_roundup`).
2. `sector` must be one of the fixed set (see the section headers / the issue template dropdown).
3. `amount_usd` is the round size as a plain integer, used for sorting.
4. Run `python3 build.py` to regenerate `README.md`, commit both files, open a PR.

## Ground rules

- **Real and sourced** — link the funding announcement. No unconfirmed rumors.
- **Recent** — this is a *recently* funded list; very old rounds get pruned.
- **No em dashes in descriptions** — this is published copy; use commas or periods.
- Descriptions are factual one-liners about the product, not marketing copy.

Thanks for keeping the radar current. 🙏
