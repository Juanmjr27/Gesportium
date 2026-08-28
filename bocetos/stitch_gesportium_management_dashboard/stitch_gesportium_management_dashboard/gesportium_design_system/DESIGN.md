---
name: Gesportium Design System
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#434656'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#737688'
  outline-variant: '#c3c5d9'
  surface-tint: '#004ced'
  primary: '#003ec7'
  on-primary: '#ffffff'
  primary-container: '#0052ff'
  on-primary-container: '#dfe3ff'
  inverse-primary: '#b7c4ff'
  secondary: '#4648d4'
  on-secondary: '#ffffff'
  secondary-container: '#6063ee'
  on-secondary-container: '#fffbff'
  tertiary: '#952200'
  on-tertiary: '#ffffff'
  tertiary-container: '#bf3003'
  on-tertiary-container: '#ffddd5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001452'
  on-primary-fixed-variant: '#0038b6'
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#ffdbd2'
  tertiary-fixed-dim: '#ffb4a1'
  on-tertiary-fixed: '#3c0800'
  on-tertiary-fixed-variant: '#891e00'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  button:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 1440px
  gutter: 20px
  sidebar-width: 260px
---

## Brand & Style
The design system for this B2B SaaS platform is built on the pillars of **Corporate Modernism** and **Functional Clarity**. It is designed to feel like a high-performance tool: reliable, precise, and unobtrusive. The target audience—gym owners and facility managers—requires a UI that minimizes cognitive load while managing complex data like memberships, billing, and scheduling.

The aesthetic leans into **Minimalism** with a focus on structured information density. We utilize a "Data-First" approach where whitespace is used strategically to group related information, ensuring the interface remains professional and trustworthy even when displaying dense tables or complex financial KPIs.

## Colors
The palette is rooted in a professional "Gesportium Blue" that signals stability and technology. 

- **Primary**: Used for core actions, active states, and brand moments.
- **Neutral Scale**: Extensively used to create hierarchy. `#F8FAFC` provides a cool, clean canvas for backgrounds, while `#1E293B` ensures high legibility for body text.
- **Semantic Colors**: Strictly reserved for status indicators. Green for active memberships and successful payments; Red for overdue accounts and system errors; Amber for pending registrations.
- **Surface Colors**: We use subtle gray borders (`#E2E8F0`) and white surfaces (`#FFFFFF`) to separate data containers from the background.

## Typography
This design system uses **Inter** for all primary UI elements to ensure maximum legibility and a neutral, professional tone. A systematic scale ensures that data-heavy screens remain scannable.

- **Headlines**: Use tighter letter spacing and bold weights to ground the page layout.
- **Labels**: We introduce **JetBrains Mono** for small labels, ID numbers, and currency values. This monospaced touch adds a technical, precise feel appropriate for a management SaaS.
- **Body**: Standardized at 14px for density, with 16px reserved for long-form content or simple dashboard widgets.

## Layout & Spacing
The layout follows a **Fluid Grid** philosophy with a fixed-width sidebar. 

- **Sidebar Navigation**: Fixed at 260px on desktop. On tablet, it collapses to an icon-only rail (72px).
- **Grid**: A 12-column system for the main content area. Dashboard cards typically span 3, 4, or 6 columns.
- **Rhythm**: All spacing is a multiple of 4px. Use 16px (md) for internal padding of cards and 24px (lg) for gaps between major layout sections.
- **Mobile**: Margins reduce to 16px. Cards stack vertically, and the sidebar transitions to a bottom navigation bar or a hidden hamburger menu.

## Elevation & Depth
Depth is conveyed through **Tonal Layers** rather than heavy shadows to maintain a clean B2B look.

- **Level 0 (Background)**: `#F8FAFC`.
- **Level 1 (Cards/Surface)**: `#FFFFFF` with a 1px solid border (`#E2E8F0`). No shadow.
- **Level 2 (Interactive/Hover)**: Same as Level 1 but with a very soft, diffused shadow: `0 4px 6px -1px rgb(0 0 0 / 0.05)`.
- **Level 3 (Modals/Popovers)**: White surface with a more pronounced shadow to indicate focus and separation from the primary data layer.

## Shapes
The design system adopts a **Soft** shape language. This provides a modern touch without appearing overly "bubbly" or consumer-oriented. 

- **Small Components (Buttons, Inputs)**: 0.25rem (4px) corner radius.
- **Medium Components (Cards, Modals)**: 0.5rem (8px) corner radius.
- **Status Pills**: 9999px (full pill) to distinguish them from interactive buttons.

## Components
- **Buttons**: Primary buttons are solid `#0052FF` with white text. Secondary buttons use a subtle gray stroke. Content should be centered with 14px semi-bold text.
- **Data Tables**: The heart of the platform. Use a flat design with 1px horizontal dividers only. Header cells should use `label-sm` typography in all-caps. High-density rows (40px height) should be the default.
- **Cards**: Dashboards should use cards to wrap KPIs. Use a "Header + Content" structure where the header is separated by a subtle 1px divider.
- **Input Fields**: Focus states must use a 2px outer glow of the primary color to ensure accessibility and clarity during data entry.
- **Chips/Status**: Use a "Subtle Tint" pattern. For example, a "Paid" status uses a light green background with dark green text.
- **Sidebar**: High-contrast dark sidebar (`#1E293B`) to visually separate navigation from the workspace. Active items should be highlighted with a left-edge primary color border.