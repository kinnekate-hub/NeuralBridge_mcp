package com.neuralbridge

import android.content.Context
import ai.nexa.core.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class NexaBridge(private val context: Context) {
    private var vlm: VlmWrapper? = null

    suspend fun initializeAI(modelPath: String): Boolean = withContext(Dispatchers.IO) {
        try {
            NexaSdk.getInstance().init(context)

            VlmWrapper.builder()
                .vlmCreateInput(VlmCreateInput(
                    model_name = "omni-neural",
                    model_path = modelPath,
                    plugin_id = "cpu", 
                    config = ModelConfig()
                ))
                .build()
                .onSuccess { wrapper ->
                    vlm = wrapper
                }
            
            return@withContext vlm != null
        } catch (e: Exception) {
            return@withContext false
        }
    }

    suspend fun chatWithAI(userPrompt: String) {
        if (vlm == null) return
        withContext(Dispatchers.IO) {
            vlm?.generateStreamFlow(userPrompt, GenerationConfig())?.collect { chunk ->
                println(chunk) 
            }
        }
    }
}
