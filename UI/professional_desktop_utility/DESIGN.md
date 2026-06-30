---
name: Professional Desktop Utility
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#404752'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f1f1f1'
  outline: '#717783'
  outline-variant: '#c0c7d4'
  surface-tint: '#0060ab'
  primary: '#005faa'
  on-primary: '#ffffff'
  primary-container: '#0078d4'
  on-primary-container: '#ffffff'
  inverse-primary: '#a3c9ff'
  secondary: '#006e25'
  on-secondary: '#ffffff'
  secondary-container: '#80f98b'
  on-secondary-container: '#007327'
  tertiary: '#7b5800'
  on-tertiary: '#ffffff'
  tertiary-container: '#9a6f00'
  on-tertiary-container: '#ffffff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d3e3ff'
  primary-fixed-dim: '#a3c9ff'
  on-primary-fixed: '#001c39'
  on-primary-fixed-variant: '#004883'
  secondary-fixed: '#83fc8e'
  secondary-fixed-dim: '#66df75'
  on-secondary-fixed: '#002106'
  on-secondary-fixed-variant: '#00531a'
  tertiary-fixed: '#ffdea7'
  tertiary-fixed-dim: '#ffbb18'
  on-tertiary-fixed: '#271900'
  on-tertiary-fixed-variant: '#5e4200'
  background: '#f9f9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e2e2e2'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
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
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin: 24px
---

## Brand & Style
The design system is engineered for productivity-focused Windows desktop applications. It balances the utility of classic enterprise software with the refined aesthetics of modern Windows 11 design. The target audience is office professionals who require a dependable, low-fatigue environment for data management and workflow execution.

The style is **Corporate Modern** with a focus on high-density information display. It utilizes a structured grid, subtle elevation to distinguish functional areas, and a clear visual hierarchy. The emotional response is one of efficiency, reliability, and precision. Interaction patterns prioritize speed and clarity, ensuring that complex tasks feel manageable through organized layouts and familiar Windows-native behaviors.

## Colors
The palette is rooted in the professional Windows ecosystem.
- **Primary Blue (#0078D4):** Used for primary actions, selection states, and focus indicators.
- **Success Green (#28A745):** Reserved for "Execute," "Complete," or "Submit" actions.
- **Warning Orange (#FFB900):** Specific to "Undo," "Revert," or "Pending" states.
- **Neutral Gray (#F3F3F3):** Applied to secondary actions, background containers, and zebra-striping in tables.
- **Backgrounds:** The main application window uses a very light gray (#F9F9F9) to reduce glare, while functional cards and containers use pure white (#FFFFFF).

## Typography
The system uses **Inter** (as a highly legible web-optimized alternative to Segoe UI) to ensure crisp rendering of Vietnamese diacritics on high-DPI displays.
- **Hierarchies:** Use `headline-md` for page titles and `body-md` for standard data entry.
- **Data Display:** For tabular data and list items, `body-md` is the standard.
- **Labels:** Use `label-md` in all caps or bold for table headers and input field labels to provide clear structural markers.
- **Readability:** Maintain a high contrast ratio between text and background, using Dark Gray (#201F1E) for primary text and Medium Gray (#605E5C) for metadata or captions.

## Layout & Spacing
The layout follows a **Fluid Grid** model optimized for desktop window resizing. 
- **Structure:** Content is organized into functional "panes" (e.g., Sidebar, Main Content Area, Inspector).
- **Margins:** A standard page margin of 24px (lg) is applied to all main window edges.
- **Rhythm:** An 8px/4px base unit system governs all spacing. Use 16px (md) for spacing between related components and 8px (xs) for internal padding within components.
- **Tables:** Rows should have a minimum height of 36px to ensure clickability and readability, with 12px horizontal padding for cell content.

## Elevation & Depth
This design system utilizes **Tonal Layers** and **Low-Contrast Outlines** rather than heavy shadows to maintain a clean, professional look.
- **Planes:** The main background is the lowest level. Content containers (cards, table areas) are raised using a 1px border (#E1E1E1).
- **Interactive Elements:** Buttons and Input fields use a subtle 1px inset or bottom-border to simulate depth without clutter.
- **Overlays:** Modals and context menus use a soft, diffused ambient shadow (10% opacity, 8px blur) to separate them from the underlying UI.
- **Hover States:** Elements slightly shift in background color (e.g., from #FFFFFF to #F3F3F3) rather than increasing shadow depth.

## Shapes
The shape language is **Soft**, reflecting the modern Windows 11 aesthetic.
- **Standard Radius:** 4px (rounded-sm) for buttons, input fields, and checkboxes.
- **Container Radius:** 8px (rounded-lg) for main content cards and panels.
- **Badges:** Use a pill-shape (fully rounded) for status indicators to distinguish them from interactive buttons.

## Components
- **Buttons:** 
  - *Primary Blue:* For "Next" or "Submit."
  - *Success Green:* For "Run," "Apply," or "Start."
  - *Warning Orange:* Specifically for "Undo" or "Rollback."
  - *Neutral Gray:* For "Cancel," "Back," or "Secondary" actions.
- **Data Tables (Treeview):** Must implement zebra-striping using #F3F3F3 on alternate rows. Headers are sticky with a 2px bottom border. Include a checkbox column for bulk actions and handle cursors for drag-and-drop rows.
- **Status Badges:** Use bold, high-contrast colors with icons:
  - Success: ✅ (Green background, white text)
  - Warning: ⚠️ (Yellow background, dark text)
  - Info/Active: 🔵 (Blue background, white text)
  - Error/Stop: ❌ (Red background, white text)
- **Input Fields:** 1px solid border (#C8C6C4). Focus state changes border to Primary Blue (#0078D4) with a 2px thickness.
- **Progress Bar:** Flat design. The container is #EDEBE9 and the fill is Primary Blue. For "Success" states, the fill may transition to Success Green.
- **Checkboxes/Radios:** Square-ish with 2px rounding. Uses Primary Blue for the checked state.