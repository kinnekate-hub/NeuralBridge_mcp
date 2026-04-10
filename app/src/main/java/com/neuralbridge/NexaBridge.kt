package com.neuralbridge

import ai.nexa.core.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class NexaBridge {
    private var engine: NexaEngine? = null

    // FUNCTION 1: Load the AI Model into the Pixel 8 NPU
    suspend fun initializeAI(modelPath: String): Boolean = withContext(Dispatchers.IO) {
        try {
            engine = NexaEngine()
            engine?.loadModel(modelPath)
            return@withContext true
        } catch (e: Exception) {
            return@withContext false
        }
    }

    // FUNCTION 2: Send a Prompt and Get a Response
    suspend fun chatWithAI(userPrompt: String): String = withContext(Dispatchers.IO) {
        if (engine == null) return@withContext "SYSTEM: AI Engine is offline."
        
        return@withContext try {
            engine?.generate(userPrompt) ?: "SYSTEM: No response generated."
        } catch (e: Exception) {
            "SYSTEM: Generation failed."
        }
    }

    // FUNCTION 3: Unload the AI to protect phone battery and memory
    fun shutdownAI() {
        engine?.close()
        engine = null
    }
}
