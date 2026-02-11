# Wave Bridge Animation System

This package contains the complete animation system for the Wave Bridge theme, including XML animation resources and Kotlin utility classes.

## Animation XML Resources

Location: `app/src/main/res/anim/`

### Loading Animations

#### `wave_pulse.xml`
Pulsing animation for loading states. Creates a breathing effect with scale and alpha changes.

**Usage:**
```kotlin
val animation = AnimationUtils.loadAnimation(context, R.anim.wave_pulse)
view.startAnimation(animation)
```

**Or use programmatically:**
```kotlin
WaveAnimationUtils.applyWavePulse(view)
```

#### `wave_flow.xml`
Flowing wave animation for data transfer indication. Combines horizontal flow with vertical oscillation.

**Usage:**
```kotlin
val animation = AnimationUtils.loadAnimation(context, R.anim.wave_flow)
view.startAnimation(animation)
```

#### `connection_wave.xml`
Ripple expansion animation for connection establishment. Uses overshoot interpolator for dynamic effect.

**Usage:**
```kotlin
val animation = AnimationUtils.loadAnimation(context, R.anim.connection_wave)
view.startAnimation(animation)
```

**Or use programmatically:**
```kotlin
WaveAnimationUtils.applyConnectionWave(view) {
    // Callback when animation completes
}
```

### Transition Animations

#### `wave_enter.xml`
Screen entrance animation with wave motion. Slides in from right with vertical wave movement.

**Duration:** 300ms

**Usage with Activities:**
```kotlin
WaveTransitions.applyWaveEntrance(this, R.anim.wave_enter)
```

**Or programmatically:**
```kotlin
WaveAnimationUtils.applyWaveEnter(view) {
    // Callback when animation completes
}
```

#### `wave_exit.xml`
Screen exit animation with wave motion. Slides out to left with vertical wave movement.

**Duration:** 250ms

**Usage with Activities:**
```kotlin
WaveTransitions.applyWaveExit(this, R.anim.wave_exit)
```

**Or programmatically:**
```kotlin
WaveAnimationUtils.applyWaveExit(view) {
    // Callback when animation completes
}
```

#### `fade_through_wave.xml`
Crossfade transition with wave overlay. Fades out then in with subtle wave motion.

**Duration:** 300ms (150ms each phase)

**Usage:**
```kotlin
WaveAnimationUtils.applyFadeThroughWave(view,
    onHalfway = {
        // Update content at halfway point
    },
    onEnd = {
        // Callback when animation completes
    }
)
```

## Kotlin Utility Classes

### WaveAnimationUtils

Main utility object for applying wave animations programmatically.

**Available Methods:**

- `applyWavePulse(view, duration)` - Pulsing animation for loading
- `applyWaveEnter(view, onEnd)` - Entrance animation
- `applyWaveExit(view, onEnd)` - Exit animation
- `applyConnectionWave(view, onEnd)` - Connection established animation
- `applyButtonPress(view)` - Button press with bounce effect
- `applyWaveRipple(view, duration)` - Ripple effect from center
- `applyFadeThroughWave(view, onHalfway, onEnd)` - Fade transition
- `stopAnimations(view)` - Stop all animations on a view

**Example:**
```kotlin
import com.neuralbridge.companion.animation.WaveAnimationUtils

// Apply loading pulse
WaveAnimationUtils.applyWavePulse(loadingView)

// Apply button press feedback
button.setOnClickListener {
    WaveAnimationUtils.applyButtonPress(it)
    // Handle click
}

// Apply entrance animation
WaveAnimationUtils.applyWaveEnter(newView) {
    // Animation completed
}
```

### WaveRippleHelper

Helper for creating and applying wave-themed ripple effects.

**Methods:**

- `applyWaveRipple(view, rippleColorRes, bounded)` - Apply ripple to a view
- `createWaveRipple(context, rippleColorRes)` - Create a RippleDrawable

**Example:**
```kotlin
import com.neuralbridge.companion.animation.WaveRippleHelper

// Apply bounded ripple
WaveRippleHelper.applyWaveRipple(
    view,
    R.color.ripple_primary,
    bounded = true
)

// Create ripple drawable
val ripple = WaveRippleHelper.createWaveRipple(context, R.color.ripple_accent)
view.background = ripple
```

### WaveTransitions

Helper for applying wave-themed activity transitions.

**Methods:**

- `applyWaveTransitions(activity, enterResId, exitResId)` - Apply both transitions
- `applyWaveEntrance(activity, waveEnterResId)` - Apply entrance only
- `applyWaveExit(activity, waveExitResId)` - Apply exit only
- `createWaveTransitionOptions(activity)` - Create ActivityOptions

**Example:**
```kotlin
import com.neuralbridge.companion.animation.WaveTransitions

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WaveTransitions.applyWaveEntrance(this, R.anim.wave_enter)
    }

    override fun finish() {
        super.finish()
        WaveTransitions.applyWaveExit(this, R.anim.wave_exit)
    }
}
```

### WaveEdgeEffectFactory & WaveEdgeEffect

Custom edge effects for RecyclerView with wave theme colors.

**Usage:**
```kotlin
import com.neuralbridge.companion.animation.applyWaveEdgeEffect

// Apply to RecyclerView
recyclerView.applyWaveEdgeEffect(R.color.primary)

// Or manually
recyclerView.edgeEffectFactory = WaveEdgeEffectFactory(context, R.color.primary)
```

## Best Practices

### Performance

1. **Use XML animations** for simple, repeating animations (lower overhead)
2. **Use programmatic animations** for complex, conditional animations
3. **Stop animations** when views are recycled or destroyed:
   ```kotlin
   override fun onDestroyView() {
       WaveAnimationUtils.stopAnimations(view)
       super.onDestroyView()
   }
   ```

### Accessibility

All animations respect the system's animation settings. To manually check:
```kotlin
val animationsEnabled = Settings.Global.getFloat(
    contentResolver,
    Settings.Global.ANIMATOR_DURATION_SCALE,
    1f
) != 0f

if (animationsEnabled) {
    WaveAnimationUtils.applyWaveEnter(view)
} else {
    view.visibility = View.VISIBLE
}
```

### Duration Guidelines

- **Micro-interactions:** 100-200ms (button press, ripples)
- **Transitions:** 250-300ms (screen enter/exit)
- **Loading states:** 1000-1500ms (pulse, flow)
- **Connection feedback:** 600-800ms (ripple expand)

### Interpolators

- **Enter animations:** DecelerateInterpolator (slow down at end)
- **Exit animations:** AccelerateInterpolator (speed up at end)
- **Loading/pulse:** AccelerateDecelerateInterpolator (smooth both ends)
- **Connection:** OvershootInterpolator (bounce effect)

## Integration Examples

### Loading Screen
```kotlin
class LoadingFragment : Fragment() {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        WaveAnimationUtils.applyWavePulse(loadingIndicator)
    }
}
```

### Activity Transitions
```kotlin
class DetailActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_detail)
        WaveTransitions.applyWaveEntrance(this, R.anim.wave_enter)
    }
}
```

### List Items with Ripple
```kotlin
class MyViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
    init {
        WaveRippleHelper.applyWaveRipple(
            itemView,
            R.color.ripple_primary,
            bounded = true
        )
    }
}
```

### Connection Status Indicator
```kotlin
fun onConnectionEstablished() {
    statusIcon.visibility = View.VISIBLE
    WaveAnimationUtils.applyConnectionWave(statusIcon) {
        // Start data flow animation
        WaveAnimationUtils.applyWaveRipple(dataFlowIndicator)
    }
}
```

## Design Principles

The Wave Bridge animation system follows these principles:

1. **Subtle but noticeable** - Animations enhance UX without being distracting
2. **Natural motion** - Wave patterns follow natural physics (easing, overshoot)
3. **Consistent timing** - Similar actions have similar durations
4. **Purposeful** - Every animation communicates state or guides attention
5. **Performant** - Animations run at 60fps on target devices

## Troubleshooting

### Animations not playing

1. Check system animation settings (Developer Options)
2. Verify view is visible and attached to window
3. Ensure animation resources are compiled (clean/rebuild)

### Choppy animations

1. Use hardware acceleration: `view.setLayerType(View.LAYER_TYPE_HARDWARE, null)`
2. Reduce simultaneous animations
3. Profile with GPU rendering tools

### Memory leaks

Always cancel animations in lifecycle callbacks:
```kotlin
override fun onPause() {
    super.onPause()
    WaveAnimationUtils.stopAnimations(view)
}
```
