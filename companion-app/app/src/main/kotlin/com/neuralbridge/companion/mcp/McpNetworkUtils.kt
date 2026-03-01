package com.neuralbridge.companion.mcp

import android.content.Context
import android.net.ConnectivityManager
import java.net.Inet4Address

object McpNetworkUtils {
    fun getWifiIpAddress(context: Context): String? {
        return try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val activeNetwork = cm.activeNetwork ?: return null
            val linkProps = cm.getLinkProperties(activeNetwork) ?: return null
            linkProps.linkAddresses
                .filter { !it.address.isLoopbackAddress && it.address is Inet4Address }
                .firstOrNull()?.address?.hostAddress
        } catch (e: Exception) {
            null
        }
    }
}
