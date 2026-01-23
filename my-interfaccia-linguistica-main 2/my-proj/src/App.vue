<script setup>
// Import ref and onMounted from Vue
import { ref, onMounted } from 'vue'

// Base URL for the FastAPI backend
// In Codespaces, use the forwarded port URL, otherwise use localhost
const getApiBase = () => {
  // Check if we're in Codespaces by looking at the hostname
  if (window.location.hostname.includes('github.dev') || window.location.hostname.includes('app.github.dev')) {
    // In Codespaces, construct the backend URL based on the frontend URL
    const protocol = window.location.protocol
    const hostname = window.location.hostname
    // Replace the port number in the hostname (e.g., literate-trout-pw555p47r7gfjqr-5173 -> literate-trout-pw555p47r7gfjqr-8000)
    const backendHostname = hostname.replace(/-\d+\./, '-8000.')
    return `${protocol}//${backendHostname}`
  }
  // Local development
  return 'http://localhost:8000'
}

const API_BASE = getApiBase()

// ========== Reactive State Variables ==========

// Model loading state
const isLoadingModel = ref(false)
const modelLoaded = ref(false)
const modelMessage = ref('')

// Joke generation state
const jokeTopic = ref('')           // Topic for the joke
const generatedJoke = ref('')       // The generated joke
const isGenerating = ref(false)     // Loading state during generation
const jokeHistory = ref([])         // History of generated jokes

// ========== Functions (API calls to backend) ==========

/**
 * Load the model
 * Makes POST request to /load-model endpoint
 */
const loadModel = async () => {
  isLoadingModel.value = true
  modelMessage.value = 'Loading model... This should take about 30 seconds.'

  try {
    const response = await fetch(`${API_BASE}/load-model`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to load model')
    }

    const data = await response.json()
    
    modelLoaded.value = true
    modelMessage.value = `✓ ${data.message}`
  } catch (error) {
    modelLoaded.value = false
    modelMessage.value = `✗ Error: ${error.message}`
  } finally {
    isLoadingModel.value = false
  }
}

/**
 * Generate a joke using the loaded model
 * Makes POST request to /generate-joke endpoint
 */
const generateJoke = async () => {
  if (!modelLoaded.value) {
    alert('Please load the model first')
    return
  }

  isGenerating.value = true
  generatedJoke.value = ''

  try {
    const response = await fetch(`${API_BASE}/generate-joke`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: jokeTopic.value,
        max_length: 50,
        temperature: 0.8
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Server error: ${response.status}`)
    }

    const data = await response.json()
    generatedJoke.value = data.joke
    
    // Add to history
    jokeHistory.value.unshift({
      joke: data.joke,
      topic: data.topic,
      timestamp: new Date().toLocaleTimeString()
    })
    
    // Keep only last 5 jokes
    if (jokeHistory.value.length > 5) {
      jokeHistory.value = jokeHistory.value.slice(0, 5)
    }
  } catch (error) {
    console.error('Generation error:', error)
    generatedJoke.value = `Error: ${error.message}`
  } finally {
    isGenerating.value = false
  }
}

/**
 * Check if model is already loaded on startup
 */
const checkModelStatus = async () => {
  console.log('🔍 Attempting to connect to backend at:', API_BASE)
  try {
    const response = await fetch(`${API_BASE}/`)
    console.log('✅ Backend response status:', response.status)
    if (!response.ok) {
      throw new Error('Backend not responding')
    }
    const data = await response.json()
    console.log('✅ Backend data:', data)
    modelLoaded.value = data.model_loaded || false
    if (modelLoaded.value) {
      modelMessage.value = `✓ Model ready: ${data.model_name}`
    }
  } catch (error) {
    console.error('❌ Failed to check model status:', error)
    console.error('❌ Tried URL:', API_BASE)
    modelLoaded.value = false
    modelMessage.value = `Backend not connected at ${API_BASE}. Error: ${error.message}`
  }
}

// Check model status when component mounts
onMounted(() => {
  checkModelStatus()
})
</script>

<template>
  <div class="app-container">
    <!-- Page header with title and description -->
    <header>
      <h1>🎭 AI Joke Generator</h1>
      <p>Generate jokes with an llm</p>
    </header>

    <main>
      <!-- ========== SECTION 1: Load Model ========== -->
      <section class="card">
        <h2>1. Load Model</h2>
        <p class="hint">First, load the model</p>
        
        <!-- Load button - disabled while loading or if already loaded -->
        <button
          @click="loadModel"
          :disabled="isLoadingModel || modelLoaded"
          class="btn btn-primary"
        >
          {{ isLoadingModel ? '⏳ Loading Model...' : modelLoaded ? '✓ Model Loaded' : '🚀 Load Model' }}
        </button>

        <!-- Success/error message after loading -->
        <p v-if="modelMessage" class="message" :class="{ success: modelLoaded }">
          {{ modelMessage }}
        </p>
      </section>

      <!-- ========== SECTION 2: Generate Jokes ========== -->
      <!-- Only shown if model is loaded -->
      <section class="card" v-if="modelLoaded">
        <h2>2. Generate a Joke</h2>
        
        <!-- Input for joke topic -->
        <div class="form-group">
          <label for="joke-topic">Joke Topic (optional):</label>
          <input
            id="joke-topic"
            v-model="jokeTopic"
            type="text"
            placeholder="e.g., programming, cats, pizza..."
          />
        </div>

        <!-- Generate button -->
        <button
          @click="generateJoke"
          :disabled="isGenerating"
          class="btn btn-secondary"
        >
          {{ isGenerating ? '😄 Generating...' : '🎪 Generate Joke' }}
        </button>

        <!-- Display generated joke if available -->
        <div v-if="generatedJoke" class="joke-display">
          <h3>😂 Your Joke:</h3>
          <p class="joke-text">{{ generatedJoke }}</p>
        </div>
      </section>

      <!-- ========== SECTION 3: Joke History ========== -->
      <!-- Only shown if there are jokes in history -->
      <section class="card" v-if="jokeHistory.length > 0">
        <h2>3. Recent Jokes</h2>
        <div class="history">
          <div v-for="(item, index) in jokeHistory" :key="index" class="history-item">
            <div class="history-header">
              <span class="history-topic">{{ item.topic }}</span>
              <span class="history-time">{{ item.timestamp }}</span>
            </div>
            <p class="history-joke">{{ item.joke }}</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* Main container with max width and centered */
.app-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

/* Header styling */
header {
  text-align: center;
  margin-bottom: 3rem;
  color: white;
}

header h1 {
  color: white;
  margin-bottom: 0.5rem;
  font-size: 3rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

header p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.2rem;
}

/* Card container for each section */
.card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.card h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
}

/* Form group spacing */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2c3e50;
}

/* Input styling */
input[type="text"] {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

/* Focus state for inputs */
input:focus {
  outline: none;
  border-color: #667eea;
}

/* Base button styling */
.btn {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

/* Disabled button state */
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Primary button (Load model) */
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Secondary button (Generate joke) */
.btn-secondary {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
}

/* Message styling (error/success) */
.message {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  background: #fee;
  color: #c33;
}

.message.success {
  background: #efe;
  color: #363;
}

/* Joke display container */
.joke-display {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.joke-display h3 {
  margin-bottom: 0.75rem;
  color: #2c3e50;
  font-size: 1.3rem;
}

.joke-text {
  line-height: 1.8;
  color: #2c3e50;
  font-size: 1.1rem;
  font-style: italic;
}

/* History section */
.history {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-item {
  background: #f9f9f9;
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.history-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.history-topic {
  font-weight: 600;
  color: #667eea;
  text-transform: capitalize;
}

.history-time {
  color: #999;
}

.history-joke {
  color: #2c3e50;
  line-height: 1.6;
  font-style: italic;
}

/* Hint text styling */
.hint {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}
</style>