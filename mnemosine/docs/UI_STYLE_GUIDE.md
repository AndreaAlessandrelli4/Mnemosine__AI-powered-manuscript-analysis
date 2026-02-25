# Mnemosine UI Style Guide

Obiettivo: riprodurre **il “feel”** degli screenshot (pulito, moderno, accenti viola/lilla), **non** una copia pixel-perfect.

## Design principles
- Interfaccia “calma”: molto spazio bianco, card leggere, bordi arrotondati.
- Accenti viola/lilla per CTA e tab attivi.
- Contrasto leggibile, testi non troppo scuri su superfici chiare.
- Layout a griglia: sidebar + main panel nella pagina Metadata.

## Color palette (suggested)
Questi colori sono scelti per essere coerenti con la palette visiva degli screenshot (lavanda/viola + grigi chiari).

### Core
- Primary (violet): **#8878E8**
- Primary hover/darker: **#7666D8**
- Secondary (lavender): **#B0A8E8**
- Accent soft (light lavender): **#EDEBFF**

### Neutrals
- Background: **#F7F6FB**
- Surface/Card: **#FFFFFF**
- Border: **#E6E3F2**
- Text strong: **#1C1B1F**
- Text muted: **#6B6780**
- Icon muted: **#8A879C**

### Status
- Success: **#2EBD85**
- Warning: **#F5A524**
- Error: **#E5484D**
- Info: **#3B82F6**

## Typography
- Font family: `Inter` (fallback: system-ui, -apple-system, Segoe UI, Roboto)
- Headings:
  - H1: 40–48px, weight 700
  - H2: 28–32px, weight 700
  - H3: 20–22px, weight 600
- Body: 14–16px, weight 400–500
- Small/muted: 12–13px

## Spacing & layout
- Base spacing unit: 8px
- Card padding: 16–20px
- Page max width: 1200–1280px
- Sidebar width: 320–360px
- Border radius:
  - Buttons: 999px (pill)
  - Cards/panels: 16–20px
- Shadow:
  - Card: `0 8px 24px rgba(28, 27, 31, 0.06)`
  - Dropdown: `0 12px 30px rgba(28, 27, 31, 0.10)`

## Components (visual rules)
### Navbar
- Background: Surface/Card (#FFF)
- Border bottom: 1px solid Border (#E6E3F2)
- Active item: text Primary + soft pill background Accent soft (#EDEBFF)
- Logo “Mnemosine”: bold, Primary or Text strong

### Buttons
- Primary: bg Primary, text white, hover Primary hover
- Secondary: bg Accent soft, text Primary, border Border
- Ghost: no bg, text muted; hover bg Background

### Tabs
- Inactive: bg Surface, border Border, text muted
- Active: bg Accent soft, text Primary, border Secondary

### Cards/Panels
- Surface: white
- Border: Border
- Header: titolo strong + sottotitolo muted

### Inputs/Dropdown
- bg white, border Border, focus ring Primary (soft)
- Disabled option:
  - text muted (#8A879C)
  - tooltip “Available on GPU only”

## Suggested implementation (Tailwind option)
Add to Tailwind theme:
- colors.primary = #8878E8
- colors.primaryHover = #7666D8
- colors.secondary = #B0A8E8
- colors.accentSoft = #EDEBFF
- colors.bg = #F7F6FB
- colors.border = #E6E3F2
- colors.text = #1C1B1F
- colors.muted = #6B6780

Or use CSS variables:

```css
:root{
  --mn-primary:#8878E8;
  --mn-primary-hover:#7666D8;
  --mn-secondary:#B0A8E8;
  --mn-accent-soft:#EDEBFF;
  --mn-bg:#F7F6FB;
  --mn-surface:#FFFFFF;
  --mn-border:#E6E3F2;
  --mn-text:#1C1B1F;
  --mn-muted:#6B6780;
  --mn-shadow:0 8px 24px rgba(28,27,31,0.06);
}
```

## Page mapping

### Home
- **Hero** con gradient leggero *(Background → Accent Soft)*.
- **2 CTA** stile “pill”:
  - Primary
  - Secondary

### Metadata
- **Sidebar**:
  - “Saved works”
  - filtro
  - elenco
- **Main**:
  - “Nuova opera”
  - tabs
  - form
  - risultati

### XML Parser / Retrieve / RAG
- Placeholder coerente con il resto:
  - card
  - header
  - testo “muted”
  - eventuali input minimi (se utili)

## Iconography
- **Icon set**: `lucide-react` (outline, stroke 1.5–2).
- **Colore icone**:
  - default: `muted`
  - `primary` solo per stati attivi / selezionati