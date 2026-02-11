# Wave Bridge Design System - Developer Guide

**Target Audience:** Android developers working on NeuralBridge companion app
**Prerequisites:** Familiarity with Android XML layouts and Material Design 3

---

## Quick Start

### 1. Apply Theme to Your Activity

The Wave Bridge theme is automatically applied via `AndroidManifest.xml`. All activities inherit `Theme.NeuralBridge` unless explicitly overridden.

```xml
<!-- AndroidManifest.xml -->
<application
    android:theme="@style/Theme.NeuralBridge">

    <activity android:name=".MainActivity" />
    <!-- Inherits Theme.NeuralBridge automatically -->

</application>
```

To use dark theme explicitly:

```xml
<activity
    android:name=".SettingsActivity"
    android:theme="@style/Theme.NeuralBridge.Dark" />
```

### 2. Reference Theme Colors

**ALWAYS** use theme attributes, not direct color resources:

✅ **DO THIS:**
```xml
<View
    android:background="?attr/colorPrimary"
    android:textColor="?attr/colorOnPrimary" />
```

❌ **DON'T DO THIS:**
```xml
<View
    android:background="@color/wave_blue"
    android:textColor="@color/white" />
```

**Why?** Theme attributes automatically adapt to light/dark themes. Direct color references break dark mode.

---

## Using Colors

### Available Theme Attributes

#### Primary Colors
```xml
?attr/colorPrimary              <!-- Main brand color (#5E72E4) -->
?attr/colorOnPrimary            <!-- Text on primary (#FFFFFF) -->
?attr/colorPrimaryContainer     <!-- Subtle primary background -->
?attr/colorOnPrimaryContainer   <!-- Text on primary container -->
```

#### Secondary Colors
```xml
?attr/colorSecondary              <!-- Secondary brand color (#825EE4) -->
?attr/colorOnSecondary            <!-- Text on secondary -->
?attr/colorSecondaryContainer     <!-- Subtle secondary background -->
?attr/colorOnSecondaryContainer   <!-- Text on secondary container -->
```

#### Surface & Background
```xml
?attr/colorSurface              <!-- Card/dialog backgrounds -->
?attr/colorOnSurface            <!-- Text on surfaces -->
?attr/colorSurfaceVariant       <!-- Subtle surface variation -->
?attr/colorOnSurfaceVariant     <!-- Text on surface variant -->
?attr/colorBackground           <!-- Screen background -->
?attr/colorOnBackground         <!-- Text on background -->
```

#### Semantic Colors
```xml
?attr/colorError                <!-- Error states (#BA1A1A) -->
?attr/colorOnError              <!-- Text on error -->
?attr/colorErrorContainer       <!-- Error background -->
?attr/colorOnErrorContainer     <!-- Text on error background -->
```

### Direct Color Resources (Use Sparingly)

Only use direct color resources for brand-specific elements or illustrations:

```xml
@color/wave_blue                <!-- #5E72E4 -->
@color/wave_purple              <!-- #825EE4 -->
@color/wave_accent_light        <!-- #A3B3F5 -->
@color/wave_accent_dark         <!-- #3E4DBD -->

@color/wave_gradient_start      <!-- For programmatic gradients -->
@color/wave_gradient_middle
@color/wave_gradient_end

@color/success                  <!-- #00C853 -->
@color/warning                  <!-- #FF9800 -->
@color/info                     <!-- #2196F3 -->
```

### Example: Button Colors

```xml
<!-- Primary button (filled) -->
<Button
    style="@style/Widget.NeuralBridge.Button"
    android:backgroundTint="?attr/colorPrimary"
    android:textColor="?attr/colorOnPrimary"
    android:text="Save" />

<!-- Secondary button (tonal) -->
<Button
    style="@style/Widget.NeuralBridge.Button.Tonal"
    android:backgroundTint="?attr/colorSecondaryContainer"
    android:textColor="?attr/colorOnSecondaryContainer"
    android:text="Cancel" />

<!-- Error button -->
<Button
    style="@style/Widget.NeuralBridge.Button"
    android:backgroundTint="?attr/colorError"
    android:textColor="?attr/colorOnError"
    android:text="Delete" />
```

---

## Using Typography

### Text Appearance Attributes

Apply text styles using `android:textAppearance`:

```xml
<!-- Display (Hero text) -->
<TextView
    android:textAppearance="@style/TextAppearance.NeuralBridge.DisplayLarge"
    android:text="Welcome" />

<!-- Headline (Page titles) -->
<TextView
    android:textAppearance="@style/TextAppearance.NeuralBridge.HeadlineLarge"
    android:text="Setup Instructions" />

<!-- Title (Card titles) -->
<TextView
    android:textAppearance="@style/TextAppearance.NeuralBridge.TitleLarge"
    android:text="Permissions" />

<!-- Body (Content text) -->
<TextView
    android:textAppearance="@style/TextAppearance.NeuralBridge.BodyLarge"
    android:text="Grant accessibility permissions to enable automation." />

<!-- Label (Button text, chips) -->
<TextView
    android:textAppearance="@style/TextAppearance.NeuralBridge.LabelLarge"
    android:text="GRANT PERMISSION" />
```

### Complete Text Appearance List

| Style | Size | Weight | Usage |
|-------|------|--------|-------|
| `DisplayLarge` | 57sp | Medium | Hero sections |
| `DisplayMedium` | 45sp | Regular | Large headers |
| `HeadlineLarge` | 32sp | Regular | Page titles |
| `HeadlineMedium` | 28sp | Regular | Section headers |
| `HeadlineSmall` | 24sp | Regular | Sub-section headers |
| `TitleLarge` | 22sp | Medium | Toolbar titles |
| `TitleMedium` | 16sp | Medium | List item titles |
| `TitleSmall` | 14sp | Medium | Overlines |
| `BodyLarge` | 16sp | Regular | Primary body text |
| `BodyMedium` | 14sp | Regular | Secondary text |
| `BodySmall` | 12sp | Regular | Captions |
| `LabelLarge` | 14sp | Medium | Button text |
| `LabelMedium` | 12sp | Medium | Chip text |
| `LabelSmall` | 11sp | Medium | Timestamps |

### Text Color Emphasis

Use theme attributes for proper emphasis levels:

```xml
<!-- High emphasis (87% opacity in light, 100% in dark) -->
<TextView
    android:textColor="?attr/colorOnSurface"
    android:text="Primary content" />

<!-- Medium emphasis (use colorOnSurfaceVariant) -->
<TextView
    android:textColor="?attr/colorOnSurfaceVariant"
    android:text="Secondary content" />

<!-- Disabled (38% opacity) -->
<TextView
    android:textColor="@color/text_disabled"
    android:text="Disabled text" />
```

---

## Using Spacing & Dimensions

### Spacing Resources

Use the 8dp grid system for consistent spacing:

```xml
<!-- Padding -->
<View
    android:padding="@dimen/spacing_medium"           <!-- 16dp -->
    android:paddingStart="@dimen/spacing_large"       <!-- 24dp -->
    android:paddingEnd="@dimen/spacing_large" />

<!-- Margins -->
<View
    android:layout_margin="@dimen/spacing_medium"     <!-- 16dp -->
    android:layout_marginBottom="@dimen/spacing_xlarge" /> <!-- 32dp -->

<!-- Screen edge padding -->
<LinearLayout
    android:paddingHorizontal="@dimen/screen_padding_horizontal"  <!-- 16dp -->
    android:paddingVertical="@dimen/screen_padding_vertical" />   <!-- 16dp -->
```

### Available Spacing Dimensions

| Dimension | Value | Usage |
|-----------|-------|-------|
| `spacing_tiny` | 4dp | Icon padding, tight spacing |
| `spacing_small` | 8dp | Component internal padding |
| `spacing_medium` | 16dp | Standard padding, list spacing |
| `spacing_large` | 24dp | Section spacing, card padding |
| `spacing_xlarge` | 32dp | Screen margins |
| `spacing_xxlarge` | 48dp | Hero section spacing |
| `spacing_huge` | 64dp | Major section breaks |

### Corner Radii

Apply Wave Bridge corner radii to custom views:

```xml
<!-- Shape drawable with wave corner radius -->
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="?attr/colorSurface" />
    <corners android:radius="@dimen/corner_radius_large" /> <!-- 24dp -->
</shape>

<!-- CardView with wave corners -->
<com.google.android.material.card.MaterialCardView
    app:cardCornerRadius="@dimen/corner_radius_card" /> <!-- 24dp -->
```

### Available Corner Radii

| Dimension | Value | Component |
|-----------|-------|-----------|
| `corner_radius_small` | 8dp | Chips, checkboxes |
| `corner_radius_medium` | 16dp | Buttons, text fields |
| `corner_radius_large` | 24dp | Cards, dialogs |
| `corner_radius_xlarge` | 32dp | Bottom sheets |
| `corner_radius_wave` | 48dp | Hero sections |
| `corner_radius_button` | 16dp | Buttons |
| `corner_radius_card` | 24dp | Cards |
| `corner_radius_fab` | 28dp | FAB |

---

## Using Components

### Buttons

#### Filled Button (Primary Action)

```xml
<Button
    style="@style/Widget.NeuralBridge.Button"
    android:text="Primary Action"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```

#### Tonal Button (Secondary Action)

```xml
<Button
    style="@style/Widget.NeuralBridge.Button.Tonal"
    android:text="Secondary Action"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```

#### Outlined Button (Tertiary Action)

```xml
<Button
    style="@style/Widget.NeuralBridge.Button.Outlined"
    android:text="Tertiary Action"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```

#### Text Button (Low Priority)

```xml
<Button
    style="@style/Widget.NeuralBridge.Button.Text"
    android:text="Learn More"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```

#### Icon Button

```xml
<com.google.android.material.button.MaterialButton
    style="@style/Widget.NeuralBridge.Button.Icon"
    app:icon="@drawable/ic_settings"
    android:contentDescription="Settings"
    android:layout_width="48dp"
    android:layout_height="48dp" />
```

### Cards

#### Elevated Card (Default)

```xml
<com.google.android.material.card.MaterialCardView
    style="@style/Widget.NeuralBridge.Card.Elevated"
    android:layout_width="match_parent"
    android:layout_height="wrap_content">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="@dimen/card_padding"> <!-- 16dp -->

        <TextView
            android:textAppearance="@style/TextAppearance.NeuralBridge.TitleLarge"
            android:text="Card Title" />

        <TextView
            android:textAppearance="@style/TextAppearance.NeuralBridge.BodyMedium"
            android:text="Card content goes here." />

    </LinearLayout>

</com.google.android.material.card.MaterialCardView>
```

#### Filled Card

```xml
<com.google.android.material.card.MaterialCardView
    style="@style/Widget.NeuralBridge.Card.Filled"
    android:layout_width="match_parent"
    android:layout_height="wrap_content">

    <!-- Card content -->

</com.google.android.material.card.MaterialCardView>
```

#### Outlined Card

```xml
<com.google.android.material.card.MaterialCardView
    style="@style/Widget.NeuralBridge.Card.Outlined"
    android:layout_width="match_parent"
    android:layout_height="wrap_content">

    <!-- Card content -->

</com.google.android.material.card.MaterialCardView>
```

#### Clickable Card

```xml
<com.google.android.material.card.MaterialCardView
    style="@style/Widget.NeuralBridge.Card.Elevated"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:clickable="true"
    android:focusable="true"
    app:cardElevation="@dimen/elevation_card"
    app:cardElevationPressed="@dimen/elevation_level3"> <!-- 6dp when pressed -->

    <!-- Card content -->

</com.google.android.material.card.MaterialCardView>
```

### Text Fields

#### Filled Text Field (Default)

```xml
<com.google.android.material.textfield.TextInputLayout
    style="@style/Widget.NeuralBridge.TextField"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:hint="Username">

    <com.google.android.material.textfield.TextInputEditText
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:inputType="text" />

</com.google.android.material.textfield.TextInputLayout>
```

#### Outlined Text Field

```xml
<com.google.android.material.textfield.TextInputLayout
    style="@style/Widget.NeuralBridge.TextField.Outlined"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:hint="Email"
    app:startIconDrawable="@drawable/ic_email"
    app:endIconMode="clear_text">

    <com.google.android.material.textfield.TextInputEditText
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:inputType="textEmailAddress" />

</com.google.android.material.textfield.TextInputLayout>
```

#### Password Field with Error

```xml
<com.google.android.material.textfield.TextInputLayout
    style="@style/Widget.NeuralBridge.TextField"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:hint="Password"
    app:endIconMode="password_toggle"
    app:errorEnabled="true"
    app:error="Password must be at least 8 characters">

    <com.google.android.material.textfield.TextInputEditText
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:inputType="textPassword" />

</com.google.android.material.textfield.TextInputLayout>
```

### Floating Action Button (FAB)

```xml
<com.google.android.material.floatingactionbutton.FloatingActionButton
    style="@style/Widget.NeuralBridge.FloatingActionButton"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:layout_gravity="bottom|end"
    android:layout_margin="@dimen/spacing_medium"
    app:srcCompat="@drawable/ic_add"
    android:contentDescription="Add item" />
```

### Chips

#### Assist Chip

```xml
<com.google.android.material.chip.Chip
    style="@style/Widget.NeuralBridge.Chip.Assist"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="Assist" />
```

#### Filter Chip

```xml
<com.google.android.material.chip.Chip
    style="@style/Widget.NeuralBridge.Chip.Filter"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="Filter"
    android:checkable="true" />
```

#### Chip Group

```xml
<com.google.android.material.chip.ChipGroup
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    app:singleSelection="true"
    app:chipSpacing="@dimen/spacing_small">

    <com.google.android.material.chip.Chip
        style="@style/Widget.NeuralBridge.Chip.Filter"
        android:text="All" />

    <com.google.android.material.chip.Chip
        style="@style/Widget.NeuralBridge.Chip.Filter"
        android:text="Active" />

    <com.google.android.material.chip.Chip
        style="@style/Widget.NeuralBridge.Chip.Filter"
        android:text="Completed" />

</com.google.android.material.chip.ChipGroup>
```

---

## Creating Wave-Themed Custom Components

### Custom Shape with Wave Corners

```xml
<!-- res/drawable/bg_wave_surface.xml -->
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="?attr/colorSurface" />
    <corners android:radius="@dimen/corner_radius_large" />
    <stroke
        android:width="@dimen/stroke_width_default"
        android:color="?attr/colorOutline" />
</shape>
```

### Gradient Background (Wave Bridge Gradient)

```xml
<!-- res/drawable/bg_wave_gradient.xml -->
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <gradient
        android:angle="135"
        android:startColor="@color/wave_gradient_start"
        android:centerColor="@color/wave_gradient_middle"
        android:endColor="@color/wave_gradient_end"
        android:type="linear" />
    <corners android:radius="@dimen/corner_radius_large" />
</shape>
```

### Ripple Effect with Wave Colors

```xml
<!-- res/drawable/ripple_primary.xml -->
<ripple xmlns:android="http://schemas.android.com/apk/res/android"
    android:color="?attr/colorPrimary">
    <item android:id="@android:id/mask">
        <shape android:shape="rectangle">
            <solid android:color="#FFFFFF" />
            <corners android:radius="@dimen/corner_radius_medium" />
        </shape>
    </item>
</ripple>
```

### Custom Button Style

```xml
<!-- res/values/styles.xml -->
<style name="Widget.App.Button.Wave" parent="Widget.NeuralBridge.Button">
    <item name="cornerRadius">@dimen/corner_radius_wave</item>
    <item name="android:minWidth">200dp</item>
    <item name="android:paddingStart">@dimen/spacing_xlarge</item>
    <item name="android:paddingEnd">@dimen/spacing_xlarge</item>
</style>
```

---

## Common Patterns

### List Item with Card

```xml
<com.google.android.material.card.MaterialCardView
    style="@style/Widget.NeuralBridge.Card.Filled"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginHorizontal="@dimen/spacing_medium"
    android:layout_marginVertical="@dimen/spacing_small">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:padding="@dimen/spacing_medium"
        android:gravity="center_vertical">

        <ImageView
            android:layout_width="@dimen/icon_size_large"
            android:layout_height="@dimen/icon_size_large"
            android:layout_marginEnd="@dimen/spacing_medium"
            android:src="@drawable/ic_placeholder"
            android:contentDescription="Icon" />

        <LinearLayout
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:orientation="vertical">

            <TextView
                android:textAppearance="@style/TextAppearance.NeuralBridge.TitleMedium"
                android:text="Item Title" />

            <TextView
                android:textAppearance="@style/TextAppearance.NeuralBridge.BodyMedium"
                android:textColor="?attr/colorOnSurfaceVariant"
                android:text="Item description" />

        </LinearLayout>

        <Button
            style="@style/Widget.NeuralBridge.Button.Icon"
            android:layout_width="@dimen/min_touch_target"
            android:layout_height="@dimen/min_touch_target"
            app:icon="@drawable/ic_more_vert"
            android:contentDescription="More options" />

    </LinearLayout>

</com.google.android.material.card.MaterialCardView>
```

### Section Header

```xml
<TextView
    android:textAppearance="@style/TextAppearance.NeuralBridge.TitleSmall"
    android:textColor="?attr/colorPrimary"
    android:text="SECTION HEADER"
    android:layout_marginTop="@dimen/spacing_large"
    android:layout_marginBottom="@dimen/spacing_small"
    android:paddingHorizontal="@dimen/spacing_medium" />
```

### Dialog Layout

```xml
<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:padding="@dimen/dialog_padding">

    <TextView
        android:textAppearance="@style/TextAppearance.NeuralBridge.HeadlineSmall"
        android:text="Dialog Title"
        android:layout_marginBottom="@dimen/spacing_medium" />

    <TextView
        android:textAppearance="@style/TextAppearance.NeuralBridge.BodyMedium"
        android:text="Dialog message content goes here."
        android:layout_marginBottom="@dimen/spacing_large" />

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:gravity="end">

        <Button
            style="@style/Widget.NeuralBridge.Button.Text"
            android:text="Cancel"
            android:layout_marginEnd="@dimen/spacing_small" />

        <Button
            style="@style/Widget.NeuralBridge.Button"
            android:text="Confirm" />

    </LinearLayout>

</LinearLayout>
```

---

## Common Pitfalls & Solutions

### ❌ Pitfall: Hardcoded Colors

```xml
<!-- DON'T -->
<View android:background="#5E72E4" />
```

✅ **Solution:** Use theme attributes

```xml
<!-- DO -->
<View android:background="?attr/colorPrimary" />
```

### ❌ Pitfall: Inconsistent Spacing

```xml
<!-- DON'T -->
<View android:padding="17dp" />
```

✅ **Solution:** Use 8dp grid

```xml
<!-- DO -->
<View android:padding="@dimen/spacing_medium" /> <!-- 16dp -->
```

### ❌ Pitfall: Arbitrary Corner Radii

```xml
<!-- DON'T -->
<shape>
    <corners android:radius="13dp" />
</shape>
```

✅ **Solution:** Use design system radii

```xml
<!-- DO -->
<shape>
    <corners android:radius="@dimen/corner_radius_medium" /> <!-- 16dp -->
</shape>
```

### ❌ Pitfall: Setting Text Size Without TextAppearance

```xml
<!-- DON'T -->
<TextView
    android:textSize="16sp"
    android:textColor="#000000" />
```

✅ **Solution:** Use text appearance

```xml
<!-- DO -->
<TextView
    android:textAppearance="@style/TextAppearance.NeuralBridge.BodyLarge" />
```

### ❌ Pitfall: Touch Targets Too Small

```xml
<!-- DON'T (icon button only 24dp) -->
<ImageButton
    android:layout_width="24dp"
    android:layout_height="24dp" />
```

✅ **Solution:** Minimum 48dp touch target

```xml
<!-- DO -->
<ImageButton
    android:layout_width="@dimen/min_touch_target"  <!-- 48dp -->
    android:layout_height="@dimen/min_touch_target"
    android:padding="@dimen/spacing_medium" />  <!-- Icon is 24dp, padding adds to 48dp -->
```

---

## Testing Your Implementation

### Checklist

- [ ] All colors use theme attributes (no hardcoded hex values)
- [ ] All spacing uses 8dp grid dimensions
- [ ] All corner radii use design system values
- [ ] All text uses `textAppearance` styles
- [ ] Touch targets meet 48dp minimum
- [ ] UI looks correct in both light and dark themes
- [ ] High contrast mode tested (accessibility)
- [ ] Large font size tested (accessibility)

### Testing Dark Theme

Enable dark theme in developer options or system settings:

```kotlin
// Programmatically test dark theme
AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
```

### Testing Accessibility

```kotlin
// Test with large font scale
val config = resources.configuration
config.fontScale = 1.5f  // 150% font size
resources.updateConfiguration(config, resources.displayMetrics)
```

---

## Migration Guide (For Existing Code)

### Step 1: Update Theme Reference

```xml
<!-- Old -->
<application android:theme="@android:style/Theme.Material.Light" />

<!-- New -->
<application android:theme="@style/Theme.NeuralBridge" />
```

### Step 2: Replace Hardcoded Colors

```xml
<!-- Old -->
<Button android:backgroundTint="#5E72E4" />

<!-- New -->
<Button android:backgroundTint="?attr/colorPrimary" />
```

### Step 3: Apply Component Styles

```xml
<!-- Old -->
<Button
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:background="@drawable/custom_button" />

<!-- New -->
<Button
    style="@style/Widget.NeuralBridge.Button"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```

### Step 4: Use Text Appearances

```xml
<!-- Old -->
<TextView
    android:textSize="16sp"
    android:textColor="#000000"
    android:fontFamily="sans-serif" />

<!-- New -->
<TextView
    android:textAppearance="@style/TextAppearance.NeuralBridge.BodyLarge" />
```

---

## Resources

- [Design System Overview](./DESIGN_SYSTEM.md) - Complete design system specification
- [Icon Resources](./ICON_RESOURCES.md) - Icon usage and generation
- [Material Design 3 Guidelines](https://m3.material.io/) - Official MD3 documentation

---

## Support

For questions or issues with the Wave Bridge design system:
- Check this guide and `DESIGN_SYSTEM.md` first
- Review implementation files in `app/src/main/res/values/`
- Ask **design-architect** for design system questions
- Ask **icon-specialist** for icon-related questions

---

## Version

**Version:** 1.0
**Last Updated:** 2026-02-10
**Author:** design-architect
