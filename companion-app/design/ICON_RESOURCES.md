# NeuralBridge Icon Resources

## Overview
Wave Bridge icon design (icon #6 from showcase) implemented as Android app launcher icon with full adaptive icon support for Android 8.0+.

## Generated Resources

### PNG Icons (10 files)
Located in `app/src/main/res/mipmap-*/`

| Density | Size | Regular | Round |
|---------|------|---------|-------|
| mdpi | 48×48 | ✅ 1.6K | ✅ 1.6K |
| hdpi | 72×72 | ✅ 2.4K | ✅ 2.4K |
| xhdpi | 96×96 | ✅ 3.2K | ✅ 3.2K |
| xxhdpi | 144×144 | ✅ 5.0K | ✅ 5.0K |
| xxxhdpi | 192×192 | ✅ 6.7K | ✅ 6.7K |

### Adaptive Icon Resources (Android 8.0+)

#### Foreground Layer
**File:** `drawable/ic_launcher_foreground.xml`
- Vector drawable with 108dp canvas
- Wave bridge design with white paths and circles
- Scaled from 512×512 original with 0.128 scale factor
- Translated (21, 21) to center in 66dp safe zone
- All elements properly within safe zone for circular masking

#### Background Layer
**File:** `drawable/ic_launcher_background.xml`
- Vector drawable with 108dp canvas
- Linear gradient: #5E72E4 (blue) → #825EE4 (purple)
- Diagonal gradient (0,0) to (108,108)
- Uses `aapt:attr` for gradient definition

#### Adaptive Icon Descriptors
**Files:**
- `mipmap-anydpi-v26/ic_launcher.xml`
- `mipmap-anydpi-v26/ic_launcher_round.xml`

Both reference foreground and background drawables. System applies appropriate mask (circle, squircle, rounded square) based on device OEM.

#### Fallback Color
**File:** `values/ic_launcher_background.xml`
- Color resource: `#5E72E4` (primary blue)
- Used on devices that don't support gradient backgrounds

## Design Specifications

### Color Palette
- Primary Blue: `#5E72E4`
- Secondary Purple: `#825EE4`
- Foreground: `#FFFFFF` (white)

### Canvas & Safe Zone
- Total canvas: 108dp × 108dp
- Safe zone (visible): 66dp diameter circle centered
- Foreground elements: All within 66dp safe zone
- Background: Full 108dp (extends beyond mask)

### Wave Bridge Design Elements
1. **Main wave path** - Top sine wave (stroke width 24, full opacity)
2. **Secondary wave** - Bottom sine wave (stroke width 16, 60% opacity)
3. **Connection nodes** - Three white circles at wave peaks
4. **Support pillars** - Two vertical lines at wave ends
5. **Base platforms** - Two rectangles at pillar bases

## Regeneration

To regenerate PNG icons from SVG source:

```bash
cd companion-app/design
./generate-icons.sh
```

**Requirements:**
- ImageMagick (`convert` command)
- Source file: `design/wave-bridge.svg`

**Output:**
- Generates all 10 PNG files at correct densities
- Preserves transparency (16-bit gray+alpha)
- Overwrites existing files

## Validation Checklist

✅ All PNG files have correct dimensions
✅ All PNG files have alpha channel (transparency)
✅ File sizes scale appropriately with density
✅ Adaptive icon foreground fits in 66dp safe zone
✅ Adaptive icon background fills 108dp canvas
✅ XML resources have proper Android namespace
✅ Gradient uses correct color codes
✅ Both regular and round variants provided
✅ Fallback color resource defined

## Integration Status

- [x] Icon resources generated
- [ ] AndroidManifest.xml updated (Task #4 - blocked by Task #2)
- [ ] Build tested
- [ ] Visual verification on device

## Notes

- The Wave Bridge design was selected from 10 concept designs
- Design emphasizes neural connection metaphor with flowing data
- Blue-purple gradient aligns with brand identity
- White foreground ensures visibility on all backgrounds
- Icon works well at all sizes from 48dp to 192dp
