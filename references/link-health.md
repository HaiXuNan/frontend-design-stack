# Link health and risk notes

Audit date: 2026-10-28. Scope: all 195 catalog destinations, plus the npm packages named in `recipes.md`.

## Site scan

- 178/195 returned HTTP 200.
- 0 cross-domain redirects among reachable sites.
- 0 matches for crypto-miner scripts, packed JavaScript, meta-refresh redirects, wallet addresses or prompt-injection phrases in the first 800 KB of each page.
- All URLs use HTTPS except `http://useplanes.com/`, which also serves `https://useplanes.com/`; prefer the HTTPS form.

## Not verified from this network (17)

These did not return a usable response from the audit machine. Most are connection timeouts, not confirmed dead links. Do not let an agent auto-visit or auto-install from them without re-checking.

| Resource | URL | Result |
|---|---|---|
| Wakamai Fondue | https://wakamaifondue.com/ | connection timeout |
| OKLCH | https://oklch.com/ | connection timeout |
| Amicro | https://amicro.vercel.app/ | connection timeout |
| Painterly | https://painterly.design-tools.workers.dev/ | connection timeout |
| React Three Fiber | https://r3f.docs.pmnd.rs/ | TLS handshake timeout |
| Material Symbols | https://fonts.google.com/icons | connection timeout |
| MX Icons | https://mx-icons.vercel.app/ | connection timeout |
| Devicon | https://devicon.dev/ | connection timeout |
| css.gg | https://css.gg/ | TLS handshake timeout |
| startercn | https://startercn.vercel.app/ | connection timeout |
| Gradient Spin | https://gradient-spin.vercel.app/ | connection timeout |
| Amacro | https://amacro.vercel.app/ | connection timeout |
| Animated shadcn/ui | https://shadcn-animated.vercel.app/ | connection timeout |
| Bezel | https://bezel-ui.vercel.app | connection timeout |
| emailcn | https://emailcn.run/ | HTTP 503 |
| Pin UI | https://www.pinui.xyz/ | HTTP 429 |
| Lottie | https://lottiefiles.com/ | HTTP 403 (bot block) |

DNS resolution looked abnormal for several hosts: some `*.vercel.app` names resolved to IP ranges associated with unrelated services (Twitter, Facebook, Dropbox), not Vercel. That points to local DNS interference rather than compromised sites, but it also means results from this machine are not authoritative. Re-check from a trusted network before removing an entry.

## Ephemeral hosting

Nine entries live on shared free hosting and can disappear or be reused by another project: seven `*.vercel.app`, one `*.workers.dev`, one `*.github.io`. Treat them as prototypes, not long-term dependencies.

## Domain expiry

RDAP checks found no imminent lapse except:

- `oklch.com` expires **2026-11-28** (one month after this audit). Re-check before relying on it.

Others sampled (`fontshare.com`, `getlayers.ai`, `pinui.xyz`, `emailcn.run`, `lottiefiles.com`, `devicon.dev`, `wakamaifondue.com`) expire in 2027–2029.

## npm packages

Sixteen packages named in `recipes.md` were checked against the registry:

- All point at their official repositories, none is deprecated except the old Base UI name, and none declares `preinstall`, `install` or `postinstall` scripts.
- Weekly downloads range from ~0.4M to ~90M, so none is an obscure typosquat.
- `@base-ui-components/react` is **deprecated** and renamed to `@base-ui/react`; the recipe has been corrected.
- `gsap` is not MIT: it uses GSAP's own no-charge licence. Check it for commercial use.
- `npx shadcn@latest` executes a remote CLI. Pin the version in automation and review generated files.

## Aggregator terms

`https://designeer.xyz/robots.txt` allows all crawlers, explicitly including assistants, and permits quoting the catalogue. Vendor URLs in the data are clean: no affiliate or tracking parameters were found.
