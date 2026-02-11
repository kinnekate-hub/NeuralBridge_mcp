# Wave Bridge Design System

**Version:** 1.0
**Status:** ✅ Implementation Complete
**Platform:** Android (Material Design 3)

---

## Overview

The Wave Bridge design system brings a fluid, modern aesthetic to NeuralBridge inspired by wave motion and energy flow. Built on Material Design 3 foundations, it emphasizes smooth curves, blue-purple gradients, and flowing transitions that reflect the seamless connection between AI agents and Android devices.

### Design Principles

1. **Fluid Motion** - Generous rounded corners (24%+ radius) and wave-inspired curves
2. **Energy Flow** - Blue-purple gradient as signature visual element
3. **Clarity** - High contrast, accessible typography, clear visual hierarchy
4. **Consistency** - Systematic spacing (8dp grid), predictable component behavior
5. **Adaptability** - Comprehensive light/dark theme support

---

## Color Palette

### Brand Colors

The Wave Bridge signature palette uses ocean-inspired blues transitioning to energetic purples:

| Color | Hex | Usage |
|-------|-----|-------|
| **Wave Blue** | `#5E72E4` | Primary brand color, main CTA buttons, active states |
| **Wave Purple** | `#825EE4` | Secondary brand color, secondary actions, accents |
| **Wave Accent Light** | `#A3B3F5` | Highlights, hover states, light backgrounds |
| **Wave Accent Dark** | `#3E4DBD` | Pressed states, dark accents, shadows |

### Material Design 3 Color System

#### Light Theme

**Primary Colors:**
```xml
Primary:           #5E72E4  (Wave Blue)
On Primary:        #FFFFFF  (White text on primary)
Primary Container: #DFE1FF  (Subtle primary background)
On Primary Cont:   #00006E  (Text on primary container)
```

**Secondary Colors:**
```xml
Secondary:           #825EE4  (Wave Purple)
On Secondary:        #FFFFFF  (White text on secondary)
Secondary Container: #EBDDFF  (Subtle secondary background)
On Secondary Cont:   #28005D  (Text on secondary container)
```

**Surface & Background:**
```xml
Background:         #FEFBFF  (Off-white, reduces eye strain)
On Background:      #1B1B1F  (Near-black text)
Surface:            #FEFBFF  (Card/dialog backgrounds)
On Surface:         #1B1B1F  (Text on surfaces)
Surface Variant:    #E4E1EC  (Subtle variation)
On Surface Variant: #46464F  (Medium emphasis text)
```

**Semantic Colors:**
```xml
Error:           #BA1A1A  (Critical actions, destructive)
Success:         #00C853  (Success states, confirmations)
Warning:         #FF9800  (Caution, important notices)
Info:            #2196F3  (Informational messages)
```

#### Dark Theme

**Primary Colors:**
```xml
Primary:           #BBC3FF  (Light blue-white)
On Primary:        #2B3FA4  (Dark blue)
Primary Container: #4458CC  (Medium blue)
On Primary Cont:   #DFE1FF  (Light text)
```

**Secondary Colors:**
```xml
Secondary:           #D4BAFF  (Light purple-white)
On Secondary:        #4A2473  (Dark purple)
Secondary Container: #643B8B  (Medium purple)
On Secondary Cont:   #EBDDFF  (Light text)
```

**Surface & Background:**
```xml
Background:         #1B1B1F  (Dark gray-blue)
On Background:      #E4E1E6  (Light gray)
Surface:            #1B1B1F  (Card/dialog backgrounds)
On Surface:         #E4E1E6  (Text on surfaces)
Surface Variant:    #46464F  (Slightly lighter surface)
On Surface Variant: #C8C5D0  (Medium emphasis text)
```

### Color Usage Guidelines

**DO:**
- Use `colorPrimary` for primary action buttons (Save, Submit, Confirm)
- Use `colorSecondary` for secondary actions (Cancel, Skip, Optional)
- Use `colorSurface` for card backgrounds and elevated elements
- Use semantic colors (success, error, warning) for status indicators
- Maintain WCAG AA contrast ratios (4.5:1 for body text, 3:1 for large text)

**DON'T:**
- Don't use brand colors for text (use `colorOnSurface` variants instead)
- Don't hardcode color values in layouts (always use theme attributes)
- Don't mix light theme colors in dark theme and vice versa
- Don't use pure black (#000000) or pure white (#FFFFFF) for backgrounds

---

## Typography

### Type Scale (Material Design 3)

Wave Bridge uses the MD3 type scale with optimized line heights and letter spacing for readability:

#### Display Styles (Large, prominent headlines)

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| **Display Large** | 57sp | Medium | 64sp | Hero sections, splash screens |
| **Display Medium** | 45sp | Regular | 52sp | Large section headers |

#### Headline Styles

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| **Headline Large** | 32sp | Regular | 40sp | Page titles, dialog headers |
| **Headline Medium** | 28sp | Regular | 36sp | Section headers |
| **Headline Small** | 24sp | Regular | 32sp | Sub-section headers |

#### Title Styles

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| **Title Large** | 22sp | Medium | 28sp | Toolbar titles, card titles |
| **Title Medium** | 16sp | Medium | 24sp | List item titles, tab labels |
| **Title Small** | 14sp | Medium | 20sp | Overlines, small headers |

#### Body Styles

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| **Body Large** | 16sp | Regular | 24sp | Primary body text, descriptions |
| **Body Medium** | 14sp | Regular | 20sp | Secondary text, captions |
| **Body Small** | 12sp | Regular | 16sp | Small details, metadata |

#### Label Styles

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| **Label Large** | 14sp | Medium | 20sp | Button text, input labels |
| **Label Medium** | 12sp | Medium | 16sp | Chip labels, tags |
| **Label Small** | 11sp | Medium | 16sp | Timestamps, badges |

### Font Families

- **Sans-serif** (default): Android system font (Roboto on most devices)
- **Sans-serif-medium**: Medium weight for emphasis
- **Monospace**: Code snippets, technical data (if needed)

### Typography Guidelines

**DO:**
- Use Display styles for hero sections and splash screens
- Use Headline styles for page/section titles
- Use Body Large for main content (16sp ensures readability)
- Use Label styles for interactive elements (buttons, chips)
- Maintain consistent line heights for vertical rhythm

**DON'T:**
- Don't use more than 3 different text sizes on a single screen
- Don't use Display styles for body content (too large)
- Don't use Label styles for paragraphs (too small, low readability)
- Don't override text appearance without creating a named style

---

## Spacing & Layout

### 8dp Grid System

All spacing in Wave Bridge follows an 8dp base unit for visual consistency:

| Name | Value | Multiplier | Usage |
|------|-------|------------|-------|
| **Tiny** | 4dp | 0.5× | Icon padding, tight spacing |
| **Small** | 8dp | 1× | Component internal padding |
| **Medium** | 16dp | 2× | Standard padding, list item spacing |
| **Large** | 24dp | 3× | Section spacing, card padding |
| **XLarge** | 32dp | 4× | Screen margins, large spacing |
| **XXLarge** | 48dp | 6× | Hero section spacing |
| **Huge** | 64dp | 8× | Major section breaks |

### Corner Radii (Wave-Inspired)

Generous rounded corners create the signature wave aesthetic:

| Component | Radius | Usage |
|-----------|--------|-------|
| **Small** | 8dp | Chips, small buttons, checkboxes |
| **Medium** | 16dp | Buttons, text fields, small cards |
| **Large** | 24dp | Cards, dialogs, medium containers |
| **XLarge** | 32dp | Bottom sheets, large cards |
| **Wave** | 48dp | Hero sections, signature wave curves |

**Special Cases:**
- FAB: 28dp (balanced for circular shape)
- Dialog: 28dp (prominent but not extreme)
- Bottom Sheet: 32dp (top corners only)
- Switch Track: 16dp (fully rounded pill shape)

### Elevation

Material Design 3 elevation system using shadow and surface tint:

| Level | Elevation | Usage |
|-------|-----------|-------|
| **Level 0** | 0dp | Flush with surface (buttons, text fields) |
| **Level 1** | 1dp | Cards at rest |
| **Level 2** | 3dp | Cards raised, buttons pressed |
| **Level 3** | 6dp | FAB at rest, dropdowns |
| **Level 4** | 8dp | Bottom navigation, tabs |
| **Level 5** | 12dp | App bar (scrolled), FAB raised |

**Elevation Guidelines:**
- Use elevation sparingly - flat design is preferred
- Elevation should indicate interactivity or hierarchy
- Higher elevation = closer to user, more important
- Dialogs use 24dp elevation (highest in app)

---

## Components

### Buttons

#### Filled Button (Primary Action)
- **Style:** `Widget.NeuralBridge.Button`
- **Corner Radius:** 16dp
- **Min Height:** 48dp
- **Horizontal Padding:** 24dp
- **Elevation:** 2dp
- **Usage:** Primary CTAs (Save, Submit, Confirm)

```xml
<Button
    style="@style/Widget.NeuralBridge.Button"
    android:text="Primary Action"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```

#### Tonal Button (Secondary Action)
- **Style:** `Widget.NeuralBridge.Button.Tonal`
- **Corner Radius:** 16dp
- **Background:** `colorSecondaryContainer`
- **Usage:** Secondary actions (Cancel, Skip)

```xml
<Button
    style="@style/Widget.NeuralBridge.Button.Tonal"
    android:text="Secondary Action"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```

#### Outlined Button (Tertiary Action)
- **Style:** `Widget.NeuralBridge.Button.Outlined`
- **Corner Radius:** 16dp
- **Stroke Width:** 1dp
- **Usage:** Tertiary actions, less prominent

```xml
<Button
    style="@style/Widget.NeuralBridge.Button.Outlined"
    android:text="Tertiary Action"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```

#### Text Button (Low Priority Action)
- **Style:** `Widget.NeuralBridge.Button.Text`
- **No background, no border**
- **Usage:** Low priority actions (Learn More, Dismiss)

### Cards

#### Elevated Card (Default)
- **Style:** `Widget.NeuralBridge.Card.Elevated`
- **Corner Radius:** 24dp
- **Elevation:** 2dp
- **Content Padding:** 16dp
- **Usage:** Default card style

```xml
<com.google.android.material.card.MaterialCardView
    style="@style/Widget.NeuralBridge.Card.Elevated"
    android:layout_width="match_parent"
    android:layout_height="wrap_content">

    <!-- Card content -->

</com.google.android.material.card.MaterialCardView>
```

#### Filled Card
- **Style:** `Widget.NeuralBridge.Card.Filled`
- **Corner Radius:** 24dp
- **Background:** `colorSurfaceVariant`
- **Elevation:** 0dp
- **Usage:** Less prominent cards, grouped content

#### Outlined Card
- **Style:** `Widget.NeuralBridge.Card.Outlined`
- **Corner Radius:** 24dp
- **Stroke Width:** 1dp
- **Stroke Color:** `colorOutline`
- **Usage:** Emphasized borders without elevation

### Text Fields

#### Filled Text Field (Default)
- **Style:** `Widget.NeuralBridge.TextField`
- **Corner Radius:** 12dp (top only)
- **Stroke Width:** 1dp (2dp when focused)
- **Usage:** Default input fields

```xml
<com.google.android.material.textfield.TextInputLayout
    style="@style/Widget.NeuralBridge.TextField"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:hint="Label">

    <com.google.android.material.textfield.TextInputEditText
        android:layout_width="match_parent"
        android:layout_height="wrap_content" />

</com.google.android.material.textfield.TextInputLayout>
```

#### Outlined Text Field
- **Style:** `Widget.NeuralBridge.TextField.Outlined`
- **Corner Radius:** 12dp (all corners)
- **Usage:** Forms, emphasized inputs

### Floating Action Button (FAB)

- **Style:** `Widget.NeuralBridge.FloatingActionButton`
- **Corner Radius:** 28dp
- **Size:** 56dp × 56dp
- **Elevation:** 6dp
- **Usage:** Primary screen action

```xml
<com.google.android.material.floatingactionbutton.FloatingActionButton
    style="@style/Widget.NeuralBridge.FloatingActionButton"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    app:srcCompat="@drawable/ic_add" />
```

### Chips

- **Assist Chip:** `Widget.NeuralBridge.Chip.Assist`
- **Filter Chip:** `Widget.NeuralBridge.Chip.Filter`
- **Input Chip:** `Widget.NeuralBridge.Chip.Input`
- **Corner Radius:** 8dp
- **Usage:** Tags, filters, selections

---

## Animations & Transitions

> **Note:** Animation specifications will be added when Task #6 (Wave Animations) is complete.

### Animation Principles (Draft)

1. **Smooth & Fluid** - No abrupt changes, ease-in-out timing
2. **Purpose-Driven** - Animations guide user attention
3. **Performance-First** - 60fps minimum, use hardware acceleration
4. **Consistent Timing** - Standard durations (150ms, 300ms, 500ms)

**Animation Types:**
- Wave ripple effects on interactive elements
- Flowing transitions between screens
- Smooth property animations (alpha, scale, translation)
- Spring-based physics for natural motion

---

## Dark Theme

Wave Bridge provides comprehensive dark theme support with proper contrast and reduced eye strain:

### Key Differences

| Element | Light Theme | Dark Theme |
|---------|-------------|------------|
| **Primary** | #5E72E4 (Wave Blue) | #BBC3FF (Light Blue) |
| **Background** | #FEFBFF (Off-White) | #1B1B1F (Dark Gray) |
| **Surface** | #FEFBFF | #1B1B1F |
| **Text (High)** | 87% Black | 100% White |
| **Text (Medium)** | 60% Black | 70% White |

### Dark Theme Guidelines

**DO:**
- Use elevated surfaces (with surface tint) for hierarchy
- Reduce image brightness/saturation slightly
- Use #1B1B1F (not pure black) for backgrounds
- Test contrast ratios (WCAG AA minimum)

**DON'T:**
- Don't invert colors mechanically (use MD3 palette)
- Don't use pure black backgrounds (causes smearing on OLED)
- Don't forget to adjust illustration colors for dark mode

---

## Accessibility

### Color Contrast

All Wave Bridge color combinations meet **WCAG AA** standards:
- Body text: 4.5:1 contrast ratio minimum
- Large text (18sp+): 3:1 contrast ratio minimum
- Interactive elements: 3:1 contrast ratio minimum

### Text Emphasis Levels

**Light Theme:**
- High Emphasis: 87% Black (#DE000000)
- Medium Emphasis: 60% Black (#99000000)
- Disabled: 38% Black (#61000000)

**Dark Theme:**
- High Emphasis: 100% White (#FFFFFFFF)
- Medium Emphasis: 70% White (#B3FFFFFF)
- Disabled: 38% White (#61FFFFFF)

### Touch Targets

All interactive elements meet **Material Design 3** touch target guidelines:
- Minimum touch target: 48dp × 48dp
- Small touch target (dense UIs): 32dp × 32dp
- Spacing between targets: 8dp minimum

### Focus Indicators

All focusable elements provide clear visual indicators:
- Keyboard navigation support
- Focus rings with high contrast
- Logical tab order

---

## Implementation Files

### Resource Files

| File | Purpose |
|------|---------|
| `values/colors.xml` | Complete color palette (light + dark themes) |
| `values/themes.xml` | Theme definitions (Theme.NeuralBridge + Dark variant) |
| `values/styles.xml` | Component styles and text appearances |
| `values/dimens.xml` | Spacing system, corner radii, elevations |

### Icon Resources

| Location | Content |
|----------|---------|
| `mipmap-*/ic_launcher.png` | App icon (5 densities) |
| `mipmap-*/ic_launcher_round.png` | Round app icon |
| `mipmap-anydpi-v26/ic_launcher.xml` | Adaptive icon (API 26+) |
| `drawable/ic_launcher_foreground.xml` | Adaptive icon foreground |
| `drawable/ic_launcher_background.xml` | Adaptive icon background |

### Drawables

| File | Purpose |
|------|---------|
| `drawable/bg_splash.xml` | Splash screen with Wave Bridge gradient |
| `drawable/bg_wave_*.xml` | Wave pattern backgrounds (multiple variants) |

---

## Version History

### Version 1.0 (Current)
- ✅ Complete Material Design 3 color system
- ✅ Light and dark theme support
- ✅ Comprehensive typography scale
- ✅ 8dp grid spacing system
- ✅ Wave-inspired corner radii (24dp+)
- ✅ Component styles (buttons, cards, inputs, chips)
- ✅ Icon resources (all densities)
- ✅ Wave pattern drawables
- ⏳ Wave animations (Task #6 in progress)

---

## Related Documentation

- [Developer Guide](./DEVELOPER_GUIDE.md) - How to use the design system in code
- [Icon Resources](./ICON_RESOURCES.md) - Icon generation and usage
- [Icon Showcase](./icon-showcase.html) - Visual preview of icons and design

---

## Credits

**Design System:** design-architect
**Icon Design:** icon-specialist
**Drawable Assets:** drawable-designer
**Platform:** Android (Material Design 3)
**Project:** NeuralBridge - AI-native Android automation
