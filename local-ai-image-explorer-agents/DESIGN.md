---
version: alpha
name: Cody Sandahl — Personal Brand
description: Editorial personal-brand site for a writer/technologist, pairing a monochrome gallery aesthetic with playful pastel accents for maker/craft content.
colors:
  primary: "#1A1A1A"
  secondary: "#666666"
  tertiary: "#8A8A8A"
  neutral: "#FFFFFF"
  surface: "#EEEEEE"
  border: "#B5B5B5"
  accent-lavender: "#A29FD6"
  accent-mint: "#ACE39F"
  accent-coral: "#D88F88"
typography:
  display:
    fontFamily: Playfair Display
    fontSize: 3.4rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.03em
  h1:
    fontFamily: Playfair Display
    fontSize: 2.3rem
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: -0.03em
  h2:
    fontFamily: Playfair Display
    fontSize: 1.7rem
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: -0.005em
  h3:
    fontFamily: Playfair Display
    fontSize: 1.35rem
    fontWeight: 700
    lineHeight: 1.22
    letterSpacing: -0.05em
  body-md:
    fontFamily: Fira Sans
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.65
  body-sm:
    fontFamily: Fira Sans
    fontSize: 0.9rem
    fontWeight: 400
    lineHeight: 1.6
  label-caps:
    fontFamily: Fira Sans
    fontSize: 0.875rem
    fontWeight: 600
    lineHeight: 1.89
    letterSpacing: 0.1em
    fontFeature: uppercase
  caption:
    fontFamily: Fira Sans
    fontSize: 0.8rem
    fontWeight: 400
    lineHeight: 1.8
    letterSpacing: 0.04em
    fontFeature: uppercase
  logo:
    fontFamily: Playfair Display
    fontSize: 1.15rem
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: 0.05em
    fontFeature: small-caps
rounded:
  none: 0px
  sm: 4px
  full: 9999px
spacing:
  3xs: 4px
  2xs: 8px
  xs: 12px
  sm: 16px
  md: 24px
  lg: 32px
  xl: 48px
  2xl: 64px
  3xl: 96px
  4xl: 128px
  5xl: 200px
components:
  nav:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    typography: "{typography.label-caps}"
    height: 72px
  button-ghost:
    backgroundColor: transparent
    textColor: "{colors.primary}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.none}"
    padding: "{spacing.xs} {spacing.md}"
  button-ghost-hover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
  card-post:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    rounded: "{rounded.none}"
  card-post-eyebrow:
    textColor: "{colors.tertiary}"
    typography: "{typography.caption}"
  badge-tag:
    textColor: "{colors.secondary}"
    typography: "{typography.caption}"
  promo-block:
    rounded: "{rounded.none}"
    padding: "{spacing.xl}"
  promo-photo:
    rounded: "{rounded.full}"
---

## Overview

Editorial Minimalism meets Maker's Studio. The core reading experience — nav, headlines, post grid — is a quiet monochrome gallery: ink-black serif headlines on white, gray body copy, hairline dividers, square corners. Against that restrained backdrop, promotional and product content breaks into flat pastel color blocks with circular, Instagram-grid-style product photography. The contrast is intentional: one voice is the thoughtful long-form writer (AI, tech, faith), the other is the playful maker selling personalized goods and games. Both share the same disciplined grid and typographic system; only the color and shape vocabulary shifts to signal "shop" versus "read."

## Colors

- **Primary** (`#1A1A1A`) — near-black ink. Headlines, nav links, primary body text, button outlines/text. Treat as the functional "black" of the system; true `#000000` appears in the source but should be normalized to this softer ink tone for consistency.
- **Secondary** (`#666666`) — muted gray. Body copy, tags, secondary UI text.
- **Tertiary** (`#8A8A8A`) — lighter gray for tertiary metadata (post dates, eyebrows) that should recede further than secondary text.
- **Neutral** (`#FFFFFF`) — page and card background.
- **Surface** (`#EEEEEE`) — subtle section backgrounds and hover fills, used sparingly.
- **Border** (`#B5B5B5`, applied at low opacity ~30%) — hairline dividers and input underlines. Always render as a thin 1px rule, never a heavy stroke.
- **Accent Lavender** (`#A29FD6`), **Accent Mint** (`#ACE39F`), **Accent Coral** (`#D88F88`) — the promo/product palette. Soft, chalky pastels, roughly equal in lightness and saturation so any two can sit side-by-side without one dominating. Reserved exclusively for commerce/promo surfaces (banners, shop callouts, badges) — never used in the editorial reading flow.

## Typography

Two families carry distinct jobs and should not be swapped:

- **Playfair Display** (serif) — all headlines (`display`, `h1`–`h3`) and the wordmark (`logo`, rendered in small caps). Tight/negative letter-spacing at large sizes gives it an editorial, confident weight. This is the "voice" of the brand and should dominate any page's focal point.
- **Fira Sans**, falling back to Arial — everything functional: nav, buttons, captions, body copy, tags. `label-caps` and `caption` styles are uppercase with slightly opened letter-spacing, giving small UI text a deliberate, printed-label quality rather than looking like an afterthought.

Scale is deliberately small: one display size, three heading steps, two body steps, and two all-caps utility styles. Avoid introducing a heading size outside `display`/`h1`/`h2`/`h3` — the site keeps a tight, three-and-a-half-step hierarchy.

## Layout

Spacing follows an 11-step scale from `3xs` (4px) to `5xl` (200px), roughly doubling past `sm` (16px). Use the small end (`3xs`–`sm`) for text and inline component spacing, the middle (`md`–`xl`) for card and section padding, and the large end (`2xl`–`5xl`) sparingly, for major section breaks like the hero promo band.

The page is grid-based throughout:
- **Promo hero**: a fixed 3-column band, each column one flat accent color with a circular product photo and a ghost "Shop Now" button.
- **Post feed**: an editorial image-led grid (2–3 columns desktop, single column mobile), each cell pairing a thumbnail with an eyebrow date, serif title, pipe-separated category tags, and a short excerpt.
- **Nav**: single-row, logo left, all-caps text links + dropdowns + search right, on a plain white bar.

Responsive collapse happens early and often (breakpoints cluster around 680px, 768px, 900px, 1024px) — design mobile layouts as a clean single-column stack rather than a shrunk desktop grid.

## Elevation & Depth

The site is almost entirely flat — no elevation is used in the primary reading experience. The only shadows observed are soft, low-opacity, and reserved for transient/floating UI (dropdown menus, a floating "back to top" button):

- `0 0 0 1px rgba(0,0,0,0.1), 0 3px 12px rgba(0,0,0,0.12)` — floating menus/popovers
- `0 1px 8px rgba(0,0,0,0.12)` — small floating controls

Do not add shadows to cards, buttons, or images in the main content flow — depth is communicated through color blocking and whitespace, not elevation.

## Shapes

Corners are sharp by default (`rounded.none`, 0px) across nav, cards, buttons, and promo blocks — this is core to the gallery/editorial feel. The only exceptions:
- **Full circles** (`rounded.full`) for avatar-style product photography and icon buttons (menu, search).
- A single **small radius** (`rounded.sm`, 4px) appears on one floating utility control (back-to-top). Treat this as an exception for small floating controls, not a pattern to extend to cards or primary buttons.

## Components

- **Nav bar**: white background, serif small-caps logo at left, `label-caps` links and dropdowns at right, search icon, thin or no bottom border. 72px tall.
- **Ghost button** (`button-ghost`): transparent background, `primary`-colored 1px border and `label-caps` text, square corners. On hover/active, invert to filled `primary` background with `neutral` text — a simple, confident state change rather than a color shift.
- **Post card** (`card-post`): image on top, `caption`-styled eyebrow (date + tags in `tertiary`/`secondary` gray), `h3` serif title, `body-sm` excerpt. No border or shadow — separation comes from grid gutters (`spacing.md`–`lg`) alone.
- **Promo block**: full-bleed flat accent-color panel, circular product photo, centered `display`/`h1` serif headline in `primary` ink, ghost button beneath. Padding at `spacing.xl` or larger.
- **Tag/badge**: `caption` typography in `secondary` gray, pipe-separated, no background or border — a label, not a pill.

## Do's and Don'ts

- **Do** keep all headline and wordmark text in Playfair Display; keep all UI/functional text in Fira Sans. Never mix the two within the same text role.
- **Do** reserve the lavender/mint/coral accent palette for commerce and promo surfaces only — the editorial reading experience (nav, post feed, article body) stays monochrome.
- **Do** keep corners sharp everywhere except circular photography/icons and the one small-radius floating control.
- **Do** normalize stray `#000000` text to `primary` (`#1A1A1A`) for a single consistent "ink" value instead of two near-black blacks.
- **Don't** add drop shadows or elevation to cards, images, or buttons in the main content — flatness is the point.
- **Don't** introduce new heading sizes outside the `display`/`h1`/`h2`/`h3` scale, or new spacing values outside the 11-step scale — both are intentionally tight.
- **Don't** let accent pastels bleed into body text or link colors; they are surface/background colors only, never text colors.
