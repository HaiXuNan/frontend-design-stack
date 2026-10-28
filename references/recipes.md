# Integration recipes

Short, opinionated wiring for the default picks. Adapt imports and file conventions to the project; the project always wins. Package names and versions were checked against the npm registry on 2026-10-28.

## 1. shadcn/ui — the default React foundation

Use when the team owns the component code and the app is React + Tailwind.

```bash
npx shadcn@latest init
npx shadcn@latest add button dialog input
```

Guardrails:

- Treat generated files as your code: edit freely, but keep one registry.
- Do not add a second headless library (Radix + Base UI) for the same widget.
- Keep semantic tokens (`--background`, `--foreground`, `--primary`) rather than raw hex in components.
- For Tailwind 4, tokens live in CSS variables and `@theme inline`; do not paste Tailwind 3 config snippets.

## 2. Base UI or Radix — behaviour without styling

```bash
npm i @base-ui/react   # v1.x stable, MUI lineage (the old @base-ui-components/react is deprecated)
# or
npm i radix-ui         # unified package, v1.x
```

```tsx
// Base UI: one subpath per primitive
import { Dialog } from "@base-ui/react/dialog";

// Radix: named exports from the unified package
import { Dialog } from "radix-ui";
```

Guardrails:

- These ship no visual design. Build two or three shared wrappers (`<Modal>`, `<Menu>`) instead of styling primitives ad hoc.
- `@base-ui-components/react` is renamed to `@base-ui/react`; do not install the deprecated name.
- Pin the major version and read the changelog before upgrading.
- Check that the primitive exists before writing the import: Base UI exposes lowercase subpaths (`/dialog`, `/select`, `/combobox`).

## 3. Motion — UI animation

Use for enter/exit, layout transitions, gestures, and shared-element effects. CSS first for hover/colour/simple transforms.

```bash
npm i motion
```

```tsx
import { motion, AnimatePresence } from "motion/react";

<AnimatePresence>
  {open && (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
    />
  )}
</AnimatePresence>
```

Guardrails:

- Animate `transform` and `opacity`; avoid animating `width`, `height`, `top`, `left`.
- One orchestrated page-load sequence beats a fade-up on every section.
- Wrap non-essential motion in `useReducedMotion()` or a `prefers-reduced-motion` media query.
- `motion/react` is the React entry point; do not import the vanilla package in React code.

## 4. GSAP — timelines and scroll orchestration

Use when motion needs a timeline, scrubbing, or precise sequencing across many elements. Not for a single button hover.

```bash
npm i gsap
```

```ts
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const tl = gsap.timeline({
  scrollTrigger: { trigger: ".section", start: "top 80%", once: true },
});
tl.from(".section h2", { y: 24, opacity: 0, duration: 0.6 })
  .from(".section li", { y: 16, opacity: 0, stagger: 0.06 }, "-=0.3");
```

Guardrails:

- Register plugins once, in a client-only module.
- Kill or `matchMedia`-gate triggers on resize; clean up in the framework's unmount hook.
- Do not mix GSAP and Motion on the same elements.
- Respect reduced motion with `gsap.matchMedia()`.

## 5. Icons

```bash
npm i lucide-react                    # default general set
npm i @phosphor-icons/react           # weights: thin/light/regular/bold/fill
npm i @iconify/react                  # breadth across many sets
```

```tsx
import { Search, ChevronDown } from "lucide-react";

<Search size={18} strokeWidth={1.75} aria-hidden />
```

Guardrails:

- Pick one family and one stroke width for the whole app; expose it through a local `<Icon>` wrapper.
- Decorative icons get `aria-hidden`; icon-only buttons get an accessible name.
- Import individual icons, not a barrel that defeats tree-shaking.
- Brand marks belong in Simple Icons, not your UI set.

## 6. Fonts and fluid type

```bash
npm i @fontsource-variable/inter
```

```ts
import "@fontsource-variable/inter";
```

Fluid scale (Utopia-style), no library needed:

```css
:root {
  --step-0: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --step-1: clamp(1.25rem, 1.15rem + 0.5vw, 1.5rem);
  --step-2: clamp(1.56rem, 1.4rem + 0.8vw, 2rem);
}
```

Guardrails:

- Self-host; avoid a third-party font CDN for privacy and CLS.
- Load 2–3 weights maximum, `font-display: swap`, and preload the body face only.
- Verify the licence for commercial use — Fontshare is free for commercial use, Klim is paid, Velvetyne is free but experimental.
- Keep body line length under ~80 characters and line-height ≥ 1.5.

## 7. Colour: OKLCH tokens and contrast

Author in OKLCH, ship sRGB fallbacks only if you must support old browsers.

```css
:root {
  --brand-500: oklch(0.62 0.17 255);
  --brand-600: oklch(0.55 0.17 255);
  --surface: oklch(0.98 0.005 255);
  --text: oklch(0.22 0.02 255);
}
```

Guardrails:

- Keep lightness steps even (roughly 0.04–0.06 apart) rather than eyeballing hex.
- Check body text against its actual background with Color.review or APCA; 4.5:1 minimum.
- Do not encode state with colour alone; pair with icon, text, or shape.
- Define semantic tokens (`--text-muted`, `--danger`) on top of the ramp; components should not reference ramp steps directly.

## 8. NumberFlow — animated numbers

```bash
npm i @number-flow/react
```

```tsx
import NumberFlow from "@number-flow/react";

<NumberFlow value={revenue} format={{ style: "currency", currency: "USD" }} />
```

Guardrails: reserve width to avoid layout shift, and disable animation for users who prefer reduced motion where the number is critical data.

## 9. 3D with React Three Fiber

```bash
npm i three @react-three/fiber @react-three/drei
```

```tsx
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

<Canvas dpr={[1, 2]} camera={{ position: [0, 0, 4] }}>
  <ambientLight intensity={0.6} />
  <mesh>
    <icosahedronGeometry args={[1, 1]} />
    <meshStandardMaterial color="oklch(0.62 0.17 255)" />
  </mesh>
  <OrbitControls enablePan={false} />
</Canvas>
```

Guardrails:

- Lazy-load the canvas; render a static poster until it mounts.
- Cap `dpr` at 2, pause rendering off-screen, and dispose geometries/materials on unmount.
- 3D is a design decision, not decoration: if a static image communicates the same thing, use the image.

## 10. Charts

- **Evil Charts** / **shadcn charts** when charts must match a shadcn design system (copy-in, Recharts-based).
- **Tremor** when you want a batteries-included dashboard kit and can accept its look.
- Never mix two chart libraries in one dashboard; axis, tooltip and legend behaviour will diverge.

## 11. Rive and Lottie

- **Rive** for interactive, state-driven vector motion with a small runtime (`@rive-app/react-canvas`). Best when a designer authors states.
- **Lottie** for After Effects exports; use DotLottie and lazy-load. Avoid Lottie for navigation-critical feedback or large hero files.
- Both should degrade to a static frame under reduced motion.

## Licence notes

| Source | Typical licence | What to check |
|---|---|---|
| Fontshare | Free, commercial use | Confirm the specific family's EULA |
| Fontsource | Open-source per family | OFL/Apache per font; keep the licence file |
| Klim | Paid licence | Web/desktop tiers, traffic limits |
| Velvetyne | Free, experimental | Some families are OFL, some custom |
| shadcn/ui and registries | MIT-style, code in your repo | Check per-registry licence; "free" blocks may have Pro tiers |
| Aceternity / Magic UI / React Bits | Free + Pro tiers | Do not ship Pro components without a licence |
| Iconify sets | Mixed per set | Check each set's licence, especially brand logos |
