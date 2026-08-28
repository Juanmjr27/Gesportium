---
name: Gesportium
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c4c9ac'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8e9379'
  outline-variant: '#444933'
  surface-tint: '#abd600'
  primary: '#ffffff'
  on-primary: '#283500'
  primary-container: '#c3f400'
  on-primary-container: '#556d00'
  inverse-primary: '#506600'
  secondary: '#c8c6c5'
  on-secondary: '#313030'
  secondary-container: '#474746'
  on-secondary-container: '#b7b5b4'
  tertiary: '#ffffff'
  on-tertiary: '#303030'
  tertiary-container: '#e4e2e1'
  on-tertiary-container: '#656464'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c3f400'
  primary-fixed-dim: '#abd600'
  on-primary-fixed: '#161e00'
  on-primary-fixed-variant: '#3c4d00'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c8c6c5'
  on-secondary-fixed: '#1c1b1b'
  on-secondary-fixed-variant: '#474746'
  tertiary-fixed: '#e4e2e1'
  tertiary-fixed-dim: '#c8c6c6'
  on-tertiary-fixed: '#1b1c1c'
  on-tertiary-fixed-variant: '#474747'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Montserrat
    fontSize: 48px
    fontWeight: '900'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Montserrat
    fontSize: 36px
    fontWeight: '900'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-bold:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
  container-max: 1280px
---

## Brand & Style

The design system is engineered for high-performance sports and fitness environments. It centers on an **Energetic Modernism** style—fusing the precision of corporate SaaS with the raw intensity of professional athletics.

The brand personality is authoritative yet motivating, characterized by extreme contrast and a sense of forward motion. The UI evokes an "after-dark training" atmosphere, utilizing deep backgrounds to make action-oriented data and interactive elements vibrate with energy. Visual interest is maintained through dynamic angles and a sense of depth created by layered glassmorphism, ensuring the interface feels like a premium, high-tech piece of gym equipment.

## Colors

This design system utilizes a high-contrast dark mode foundation to emphasize focus and energy.

- **Primary (Lime Green):** Used exclusively for "action" elements—CTAs, progress indicators, active states, and critical performance data. It represents energy and movement.
- **Neutral Foundation:** The palette relies on `#0F0F0F` (True Dark) for the primary canvas to ensure maximum contrast with the primary green. 
- **Surface Tiers:** `#1A1A1A` and `#2D2D2D` are used for containers and cards to create depth without sacrificing the dark aesthetic.
- **Typography:** Pure white (`#FFFFFF`) is reserved for headlines to ensure punchy readability, while a muted grey (`#A1A1A1`) is used for secondary body text to manage visual hierarchy.

## Typography

The typography strategy relies on the tension between the aggressive, geometric weight of **Montserrat** and the clinical clarity of **Inter**.

- **Headlines:** Use Montserrat with heavy weights (700-900). For primary displays, use a slight negative letter-spacing to create a "dense" and powerful look. Headlines should frequently use `text-transform: uppercase` to mimic athletic branding.
- **Body:** Use Inter for all functional text. It provides a neutral, systematic balance to the loud headlines, ensuring that workout stats and technical data remain highly legible.
- **Data Points:** When displaying metrics (e.g., heart rate, reps), use the Montserrat Bold style to give the numbers a physical, impactful presence.

## Layout & Spacing

This design system uses a **Fluid Grid** model with a base-4 spacing rhythm to maintain mathematical precision.

- **Grid:** A 12-column grid is used for desktop, scaling down to 4 columns for mobile. Gutters are kept wide (24px) to allow the high-contrast elements "room to breathe."
- **Dynamic Angles:** To evoke speed, use subtle 2-degree skew transforms on decorative backgrounds or image masks. 
- **Sectioning:** Content should be grouped in distinct modules with generous vertical padding (80px - 120px on desktop) to create a premium, editorial feel.
- **Mobile Adaptivity:** On mobile, margins tighten to 16px, and all glassmorphic cards transition to full-width to maximize touch targets for athletes on the go.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** and **Glassmorphism**, rather than traditional heavy shadows.

- **Surface Strategy:** The lowest layer is the pure dark background. Above this, cards use a semi-transparent background (e.g., `rgba(45, 45, 45, 0.6)`) with a `backdrop-filter: blur(12px)`.
- **Borders:** Instead of shadows, use "Inner Glow" borders—1px solid strokes with low opacity (e.g., `white/10%`) on the top and left edges of cards to simulate a physical light source hitting a glass surface.
- **Interactive Depth:** When an element is hovered, the primary lime green color should be applied as a subtle outer glow (`box-shadow: 0 0 20px rgba(204, 255, 0, 0.3)`) rather than a traditional drop shadow, making the element appear "energized."

## Shapes

The shape language is **Soft (0.25rem)**, opting for a precise, technical look over overly bubbly or sharp aesthetics.

- **Components:** Standard buttons and input fields use a 4px (0.25rem) radius. This small roundness maintains a professional, "machined" feel.
- **Large Containers:** Cards and modals may use `rounded-lg` (0.5rem) to provide a slightly softer framing for dense data.
- **Instructional Elements:** Use sharp corners or 45-degree angled "dog-ear" clips for decorative accents to reinforce the athletic, aggressive nature of the brand.

## Components

- **Buttons:** Primary buttons are solid Lime Green with Black Montserrat Bold text. Use `text-transform: uppercase`. Hover states should include a slight scale-up (1.02x) to feel responsive.
- **Cards:** Utilize the glassmorphic style—dark translucent fill, 12px blur, and a 1px faint border. Padding inside cards should be a consistent 24px.
- **Chips:** Small, pill-shaped tags used for categories (e.g., "Strength," "Cardio"). These should use a ghost style: transparent background with a 1px Primary Green border and Green text.
- **Inputs:** Dark backgrounds (`#1A1A1A`) with a bottom-only border that turns Lime Green on focus. This creates a streamlined, modern look.
- **Progress Bars:** Thin, high-contrast tracks. The filled portion should be Primary Green, utilizing a slight gradient or "pulse" animation to show active tracking.
- **Lists:** Clean rows separated by low-opacity (`rgba(255,255,255,0.05)`) dividers. Use Montserrat for the primary list item and Inter for the subtext.