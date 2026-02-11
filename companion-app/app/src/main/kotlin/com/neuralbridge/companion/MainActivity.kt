package com.neuralbridge.companion

import android.Manifest
import android.app.Activity
import android.app.NotificationManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.text.TextUtils
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

/**
 * Main Activity
 *
 * Permission management UI showing status of all required permissions
 * with direct shortcuts to system settings for each.
 */
class MainActivity : Activity() {

    companion object {
        private const val REQUEST_CODE_POST_NOTIFICATIONS = 1001
        private const val TAG = "MainActivity"
    }

    // Permission status views
    private val permissionViews = mutableMapOf<String, PermissionView>()

    private lateinit var progressText: TextView
    private lateinit var overallStatusText: TextView
    private lateinit var serviceStatusText: TextView
    private lateinit var connectionInfoText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(createView())

        // Request POST_NOTIFICATIONS permission at runtime (Android 13+)
        requestNotificationPermissionIfNeeded()

        updateAllStatus()
    }

    override fun onResume() {
        super.onResume()
        updateAllStatus()
    }

    /**
     * Create comprehensive permission management UI
     */
    private fun createView(): View {
        val scrollView = ScrollView(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            val padding = resources.getDimensionPixelSize(R.dimen.screen_padding_horizontal)
            setPadding(padding, padding, padding, padding)
            setBackgroundResource(R.drawable.bg_wave_pattern)
        }

        // App title
        layout.addView(createTextView("NeuralBridge", R.style.TextAppearance_NeuralBridge_HeadlineLarge, true).apply {
            val paddingBottom = resources.getDimensionPixelSize(R.dimen.spacing_medium)
            setPadding(0, 0, 0, paddingBottom)
            setTextColor(getColor(R.color.wave_blue))
        })

        // Progress indicator
        progressText = createTextView("Checking permissions...", R.style.TextAppearance_NeuralBridge_BodyMedium, false).apply {
            val paddingBottom = resources.getDimensionPixelSize(R.dimen.spacing_small)
            setPadding(0, 0, 0, paddingBottom)
        }
        layout.addView(progressText)

        // Overall status
        overallStatusText = createTextView("", R.style.TextAppearance_NeuralBridge_TitleLarge, true).apply {
            val paddingBottom = resources.getDimensionPixelSize(R.dimen.spacing_large)
            setPadding(0, 0, 0, paddingBottom)
        }
        layout.addView(overallStatusText)

        // Section: Required Permissions
        layout.addView(createTextView("REQUIRED PERMISSIONS", R.style.TextAppearance_NeuralBridge_TitleMedium, true).apply {
            val paddingBottom = resources.getDimensionPixelSize(R.dimen.spacing_medium)
            setPadding(0, 0, 0, paddingBottom)
            setTextColor(getColor(R.color.wave_purple))
        })

        // 1. AccessibilityService
        permissionViews["accessibility"] = createPermissionView(
            "AccessibilityService",
            "Core automation service for UI control and observation"
        ).also { layout.addView(it.container) }

        // 2. NotificationListenerService
        permissionViews["notification_listener"] = createPermissionView(
            "Notification Listener",
            "Access full notification content (title, text, actions)"
        ).also { layout.addView(it.container) }

        // 3. POST_NOTIFICATIONS (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissionViews["post_notifications"] = createPermissionView(
                "Notification Permission",
                "Show foreground service notification"
            ).also { layout.addView(it.container) }
        }

        // 4. Battery optimization exemption (recommended)
        permissionViews["battery"] = createPermissionView(
            "Battery Optimization Exempt",
            "Prevent Android from killing the service (recommended)"
        ).also { layout.addView(it.container) }

        // 5. Restricted Settings (Android 15+)
        if (Build.VERSION.SDK_INT >= 35) { // Android 15+
            permissionViews["restricted_settings"] = createPermissionView(
                "Restricted Settings",
                "Allow full AccessibilityService permissions (Android 15+)"
            ).also { layout.addView(it.container) }
        }

        // Section: Service Status
        layout.addView(createTextView("SERVICE STATUS", R.style.TextAppearance_NeuralBridge_TitleMedium, true).apply {
            val paddingTop = resources.getDimensionPixelSize(R.dimen.spacing_large)
            val paddingBottom = resources.getDimensionPixelSize(R.dimen.spacing_medium)
            setPadding(0, paddingTop, 0, paddingBottom)
            setTextColor(getColor(R.color.wave_purple))
        })

        serviceStatusText = createTextView("", R.style.TextAppearance_NeuralBridge_BodyMedium, false).apply {
            val paddingBottom = resources.getDimensionPixelSize(R.dimen.spacing_small)
            setPadding(0, 0, 0, paddingBottom)
        }
        layout.addView(serviceStatusText)

        connectionInfoText = createTextView("", R.style.TextAppearance_NeuralBridge_BodyMedium, false).apply {
            val paddingBottom = resources.getDimensionPixelSize(R.dimen.spacing_medium)
            setPadding(0, 0, 0, paddingBottom)
        }
        layout.addView(connectionInfoText)

        // ADB Setup Instructions
        layout.addView(createTextView("ADB SETUP", R.style.TextAppearance_NeuralBridge_TitleMedium, true).apply {
            val paddingTop = resources.getDimensionPixelSize(R.dimen.spacing_small)
            val paddingBottom = resources.getDimensionPixelSize(R.dimen.spacing_medium)
            setPadding(0, paddingTop, 0, paddingBottom)
            setTextColor(getColor(R.color.wave_purple))
        })

        layout.addView(createTextView(
            "$ adb forward tcp:38472 tcp:38472\n$ cargo run --release -- --auto-discover",
            R.style.TextAppearance_NeuralBridge_BodySmall,
            false
        ).apply {
            val padding = resources.getDimensionPixelSize(R.dimen.spacing_medium)
            val paddingVert = resources.getDimensionPixelSize(R.dimen.spacing_small)
            setPadding(padding, paddingVert, padding, paddingVert)
            setBackgroundColor(getColor(R.color.md_theme_dark_surface))
            setTextColor(getColor(R.color.success))
            typeface = android.graphics.Typeface.MONOSPACE
        })

        scrollView.addView(layout)
        return scrollView
    }

    /**
     * Create a permission view with status indicator and action button
     */
    private fun createPermissionView(title: String, description: String): PermissionView {
        val cardPadding = resources.getDimensionPixelSize(R.dimen.card_padding)
        val spacingSmall = resources.getDimensionPixelSize(R.dimen.spacing_small)
        val spacingMedium = resources.getDimensionPixelSize(R.dimen.spacing_medium)

        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(cardPadding, cardPadding, cardPadding, cardPadding)
            setBackgroundResource(R.drawable.bg_card_wave)
            elevation = resources.getDimension(R.dimen.elevation_card)
            val params = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            params.setMargins(0, 0, 0, spacingSmall)
            layoutParams = params
        }

        // Title row with status indicator
        val titleRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }

        val statusIndicator = TextView(this).apply {
            text = "⚠"
            setTextAppearance(R.style.TextAppearance_NeuralBridge_TitleMedium)
            setPadding(0, 0, spacingMedium, 0)
        }
        titleRow.addView(statusIndicator)

        val titleText = TextView(this).apply {
            text = title
            setTextAppearance(R.style.TextAppearance_NeuralBridge_TitleMedium)
        }
        titleRow.addView(titleText)

        container.addView(titleRow)

        // Description
        val descriptionText = TextView(this).apply {
            text = description
            setTextAppearance(R.style.TextAppearance_NeuralBridge_BodySmall)
            setPadding(30, 4, 0, spacingSmall)
            setTextColor(getColor(R.color.text_medium_emphasis))
        }
        container.addView(descriptionText)

        // Action button
        val actionButton = Button(this).apply {
            text = "GRANT"
            setTextAppearance(R.style.TextAppearance_NeuralBridge_LabelLarge)
            setBackgroundResource(R.drawable.btn_wave_primary)
            val buttonPadding = resources.getDimensionPixelSize(R.dimen.spacing_large)
            val buttonPaddingVert = resources.getDimensionPixelSize(R.dimen.spacing_small)
            setPadding(buttonPadding, buttonPaddingVert, buttonPadding, buttonPaddingVert)
            minimumHeight = resources.getDimensionPixelSize(R.dimen.button_height_default)
        }
        container.addView(actionButton)

        return PermissionView(container, statusIndicator, actionButton)
    }

    /**
     * Create a styled TextView with theme support
     */
    private fun createTextView(text: String, styleRes: Int, bold: Boolean): TextView {
        return TextView(this).apply {
            this.text = text
            setTextAppearance(styleRes)
            if (bold) setTypeface(null, android.graphics.Typeface.BOLD)
        }
    }

    /**
     * Request POST_NOTIFICATIONS permission at runtime (Android 13+)
     */
    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this,
                    Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                    REQUEST_CODE_POST_NOTIFICATIONS
                )
            }
        }
    }

    /**
     * Handle permission request result
     */
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_POST_NOTIFICATIONS) {
            updateAllStatus()
        }
    }

    /**
     * Update all permission statuses and UI
     */
    private fun updateAllStatus() {
        // Check each permission
        val accessibilityEnabled = isAccessibilityServiceEnabled()
        val notificationListenerEnabled = isNotificationListenerEnabled()
        val postNotificationsGranted = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            isPostNotificationsGranted()
        } else {
            true // Not required below Android 13
        }
        val batteryOptimizationExempt = isBatteryOptimizationExempt()
        val restrictedSettingsAllowed = true // Cannot programmatically check this

        // Update permission views
        updatePermissionView(
            "accessibility",
            accessibilityEnabled,
            "ENABLED",
            "ENABLE →"
        ) { openAccessibilitySettings() }

        updatePermissionView(
            "notification_listener",
            notificationListenerEnabled,
            "ENABLED",
            "ENABLE →"
        ) { openNotificationListenerSettings() }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            updatePermissionView(
                "post_notifications",
                postNotificationsGranted,
                "GRANTED",
                "GRANT →"
            ) { requestNotificationPermissionIfNeeded() }
        }

        updatePermissionView(
            "battery",
            batteryOptimizationExempt,
            "EXEMPT",
            "EXEMPT →"
        ) { openBatteryOptimizationSettings() }

        if (Build.VERSION.SDK_INT >= 35) { // Android 15+
            updatePermissionView(
                "restricted_settings",
                restrictedSettingsAllowed,
                "ALLOWED",
                "OPEN →"
            ) { openAppSettings() }
        }

        // Calculate progress
        var granted = 0
        var total = 0

        total++
        if (accessibilityEnabled) granted++

        total++
        if (notificationListenerEnabled) granted++

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            total++
            if (postNotificationsGranted) granted++
        }

        // Battery optimization is optional, don't count towards required

        progressText.text = "Setup Progress: $granted/$total required permissions"

        // Update overall status
        val allGranted = (granted == total)
        if (allGranted) {
            overallStatusText.text = "✓ ALL SYSTEMS READY"
            overallStatusText.setTextColor(getColor(R.color.success))
        } else {
            overallStatusText.text = "⚠ SETUP INCOMPLETE"
            overallStatusText.setTextColor(getColor(R.color.warning))
        }

        // Update service status
        val service = com.neuralbridge.companion.service.NeuralBridgeAccessibilityService.instance
        if (service != null) {
            serviceStatusText.text = "🟢 AccessibilityService running\n🟢 TCP Server on port 38472\n🟢 Foreground Service active"
            serviceStatusText.setTextColor(getColor(R.color.success))

            // TODO: Get actual connection count from TcpServer
            connectionInfoText.text = "📡 Ready for connections"
        } else {
            serviceStatusText.text = "🔴 AccessibilityService not running"
            serviceStatusText.setTextColor(getColor(R.color.status_error))
            connectionInfoText.text = ""
        }
    }

    /**
     * Update a permission view with status
     */
    private fun updatePermissionView(
        key: String,
        granted: Boolean,
        grantedText: String,
        notGrantedText: String,
        action: () -> Unit
    ) {
        val view = permissionViews[key] ?: return

        if (granted) {
            view.statusIndicator.text = "✓"
            view.statusIndicator.setTextColor(getColor(R.color.success))
            view.actionButton.text = grantedText
            view.actionButton.isEnabled = false
            view.actionButton.alpha = 0.5f
        } else {
            view.statusIndicator.text = "✗"
            view.statusIndicator.setTextColor(getColor(R.color.status_error))
            view.actionButton.text = notGrantedText
            view.actionButton.isEnabled = true
            view.actionButton.alpha = 1.0f
            view.actionButton.setOnClickListener { action() }
        }
    }

    // ========================================================================
    // Permission Checking Methods
    // ========================================================================

    /**
     * Check if AccessibilityService is enabled
     */
    private fun isAccessibilityServiceEnabled(): Boolean {
        val expectedComponentName = ComponentName(this,
            com.neuralbridge.companion.service.NeuralBridgeAccessibilityService::class.java)

        val enabledServicesSetting = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false

        val colonSplitter = TextUtils.SimpleStringSplitter(':')
        colonSplitter.setString(enabledServicesSetting)

        while (colonSplitter.hasNext()) {
            val componentNameString = colonSplitter.next()
            val enabledService = ComponentName.unflattenFromString(componentNameString)
            if (enabledService != null && enabledService == expectedComponentName) {
                return true
            }
        }
        return false
    }

    /**
     * Check if NotificationListenerService is enabled
     */
    private fun isNotificationListenerEnabled(): Boolean {
        val packageName = packageName
        val enabledListeners = Settings.Secure.getString(
            contentResolver,
            "enabled_notification_listeners"
        ) ?: return false

        return enabledListeners.contains(packageName)
    }

    /**
     * Check if POST_NOTIFICATIONS permission is granted (Android 13+)
     */
    private fun isPostNotificationsGranted(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    /**
     * Check if battery optimization is disabled for this app
     */
    private fun isBatteryOptimizationExempt(): Boolean {
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        // minSdk is 24, which is >= API 23 (M), so this is always available
        return powerManager.isIgnoringBatteryOptimizations(packageName)
    }

    // ========================================================================
    // Settings Intent Launchers
    // ========================================================================

    /**
     * Open accessibility settings
     */
    private fun openAccessibilitySettings() {
        val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
        startActivity(intent)
    }

    /**
     * Open notification listener settings
     */
    private fun openNotificationListenerSettings() {
        val intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
        startActivity(intent)
    }

    /**
     * Open battery optimization settings
     */
    private fun openBatteryOptimizationSettings() {
        // minSdk is 24, which is >= API 23 (M), so this is always available
        val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
            data = Uri.parse("package:$packageName")
        }
        startActivity(intent)
    }

    /**
     * Open app-specific settings
     */
    private fun openAppSettings() {
        val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
            data = Uri.parse("package:$packageName")
        }
        startActivity(intent)
    }
}

/**
 * Container for permission view components
 */
private data class PermissionView(
    val container: LinearLayout,
    val statusIndicator: TextView,
    val actionButton: Button
)
