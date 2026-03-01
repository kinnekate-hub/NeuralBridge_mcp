package com.neuralbridge.companion.mcp

import android.content.Context
import android.util.Log
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.cio.*
import io.ktor.server.engine.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.*
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

class McpHttpServer(
    private val context: Context,
    private val toolHandler: McpToolHandler,
    private val authManager: McpAuthManager,
    private val port: Int = MCP_PORT
) {
    companion object {
        const val MCP_PORT = 7474
        private const val TAG = "McpHttpServer"
        private const val SERVER_NAME = "neuralbridge-android"
        private const val SERVER_VERSION = "0.4.0"
        private const val PROTOCOL_VERSION = "2024-11-05"
    }

    @Volatile
    private var server: EmbeddedServer<CIOApplicationEngine, CIOApplicationEngine.Configuration>? = null

    // Session tracking: sessionId → creation time. Capped to prevent unbounded growth.
    private val sessions = ConcurrentHashMap<String, Long>()
    private val MAX_SESSIONS = 100

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = false
        isLenient = true
    }

    suspend fun start() = withContext(Dispatchers.IO) {
        val wifiIp = McpNetworkUtils.getWifiIpAddress(context)
        Log.i(TAG, "Starting MCP HTTP server on 0.0.0.0:$port (WiFi: $wifiIp)")

        server = embeddedServer(CIO, port = port, host = "0.0.0.0") {
            routing {
                get("/") {
                    call.respondText("NeuralBridge MCP Server v$SERVER_VERSION — POST /mcp")
                }

                get("/health") {
                    call.respondText(
                        "{\"status\":\"ok\",\"version\":\"$SERVER_VERSION\"}",
                        ContentType.Application.Json
                    )
                }

                // CORS preflight for browser-based MCP clients
                options("/mcp") {
                    call.response.headers.append("Access-Control-Allow-Origin", "*")
                    call.response.headers.append("Access-Control-Allow-Methods", "POST, OPTIONS")
                    call.response.headers.append("Access-Control-Allow-Headers",
                        "${McpAuthManager.HEADER_NAME}, Content-Type")
                    call.respond(HttpStatusCode.NoContent)
                }

                post("/mcp") {
                    handleMcpPost(call)
                }
            }
        }.start(wait = false)

        Log.i(TAG, "MCP HTTP server started. URL: http://${wifiIp ?: "device-ip"}:$port/mcp")
    }

    private suspend fun handleMcpPost(call: ApplicationCall) {
        // Auth check
        val apiKey = call.request.headers[McpAuthManager.HEADER_NAME]
        if (!authManager.validate(apiKey)) {
            call.respondText(
                """{"error":"Invalid or missing API key. Set header: ${McpAuthManager.HEADER_NAME}"}""",
                ContentType.Application.Json,
                HttpStatusCode.Unauthorized
            )
            return
        }

        // CORS
        call.response.headers.append("Access-Control-Allow-Origin", "*")

        // Parse request body
        val body = call.receiveText()
        val request = try {
            json.decodeFromString<JsonRpcRequest>(body)
        } catch (e: Exception) {
            Log.w(TAG, "Failed to parse JSON-RPC request: ${e.message}")
            val errResp = errorResponse(null, JsonRpcErrorCodes.PARSE_ERROR, "Parse error: ${e.message}")
            call.respondText(
                json.encodeToString(JsonRpcResponse.serializer(), errResp),
                ContentType.Application.Json
            )
            return
        }

        Log.d(TAG, "MCP request: method=${request.method}, id=${request.id}")

        // Route by method
        val response: JsonRpcResponse? = when (request.method) {
            "initialize" -> handleInitialize(request)
            "notifications/initialized" -> null  // client ACK, no response
            "ping" -> successResponse(request.id, buildJsonObject {})
            "tools/list" -> handleToolsList(request)
            "tools/call" -> handleToolsCall(request)
            else -> {
                Log.w(TAG, "Unknown MCP method: ${request.method}")
                errorResponse(request.id, JsonRpcErrorCodes.METHOD_NOT_FOUND, "Method not found: ${request.method}")
            }
        }

        if (response != null) {
            call.respondText(
                json.encodeToString(JsonRpcResponse.serializer(), response),
                ContentType.Application.Json
            )
        } else {
            call.respond(HttpStatusCode.NoContent)
        }
    }

    private fun handleInitialize(request: JsonRpcRequest): JsonRpcResponse {
        val sessionId = UUID.randomUUID().toString()
        // Evict oldest entries if cap reached to prevent unbounded growth
        if (sessions.size >= MAX_SESSIONS) {
            sessions.entries.minByOrNull { it.value }?.let { sessions.remove(it.key) }
        }
        sessions[sessionId] = System.currentTimeMillis()
        Log.i(TAG, "MCP client initialized. Session: $sessionId")

        return successResponse(request.id, buildJsonObject {
            put("protocolVersion", PROTOCOL_VERSION)
            putJsonObject("capabilities") {
                putJsonObject("tools") {
                    put("listChanged", false)
                }
            }
            putJsonObject("serverInfo") {
                put("name", SERVER_NAME)
                put("version", SERVER_VERSION)
            }
        })
    }

    private fun handleToolsList(request: JsonRpcRequest): JsonRpcResponse {
        val tools = McpToolRegistry.getAllTools()
        Log.d(TAG, "tools/list: returning ${tools.size} tools")
        return successResponse(request.id, buildJsonObject {
            putJsonArray("tools") {
                tools.forEach { tool ->
                    addJsonObject {
                        put("name", tool.name)
                        put("description", tool.description)
                        put("inputSchema", tool.inputSchema)
                    }
                }
            }
        })
    }

    private suspend fun handleToolsCall(request: JsonRpcRequest): JsonRpcResponse {
        val params = request.params?.jsonObject
            ?: return errorResponse(request.id, JsonRpcErrorCodes.INVALID_PARAMS, "Missing params")
        val toolName = params["name"]?.jsonPrimitive?.contentOrNull
            ?: return errorResponse(request.id, JsonRpcErrorCodes.INVALID_PARAMS, "Missing tool name")
        val arguments = params["arguments"]?.jsonObject

        Log.d(TAG, "tools/call: $toolName")

        return try {
            val result = toolHandler.handleToolCall(toolName, arguments)
            successResponse(request.id, buildJsonObject {
                putJsonArray("content") {
                    result.content.forEach { block ->
                        addJsonObject {
                            put("type", block.type)
                            block.text?.let { put("text", it) }
                            block.data?.let { put("data", it) }
                            block.mimeType?.let { put("mimeType", it) }
                        }
                    }
                }
                if (result.isError) put("isError", true)
            })
        } catch (e: Exception) {
            Log.e(TAG, "Tool execution error: $toolName", e)
            errorResponse(request.id, JsonRpcErrorCodes.INTERNAL_ERROR, "Tool error: ${e.message ?: "unknown"}")
        }
    }

    suspend fun stop() = withContext(Dispatchers.IO) {
        server?.stop(gracePeriodMillis = 100, timeoutMillis = 1000)
        server = null
        sessions.clear()
        Log.i(TAG, "MCP HTTP server stopped")
    }

    fun getPort(): Int = port
    fun isRunning(): Boolean = server != null
    fun getActiveConnectionCount(): Int = sessions.size
}
