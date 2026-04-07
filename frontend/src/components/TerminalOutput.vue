<template>
  <div class="terminal-output" ref="containerRef">
    <div v-if="history.length === 0" class="empty">
      <span class="prompt-dim">fsight@sec:~$</span>
      <span class="empty-msg"> awaiting query...</span>
    </div>

    <div
      v-for="(entry, i) in history"
      :key="i"
      class="entry"
    >
      <div class="separator">────────────────────────────────────────────────────</div>

      <div class="meta-line">
        <span class="prompt-dim">fsight@sec:~$</span>
        <span class="query-echo">&nbsp;query: "{{ entry.question }}"</span>
      </div>
      <div class="meta-line">
        <span class="prompt-dim">fsight@sec:~$</span>
        <span class="ticker-echo">&nbsp;ticker: {{ entry.ticker || 'ALL' }}</span>
      </div>

      <div v-if="entry.pending" class="pending-line">
        <span class="spinner">{{ spinnerChar }}</span>
        <span> running query...</span>
        <span class="cursor">█</span>
      </div>

      <div v-else-if="entry.error" class="error-line">
        error: {{ entry.error }}
      </div>

      <div v-else-if="entry.answer" class="result">
        <div class="result-text">{{ entry.answer }}</div>
        <div class="sources">
          <span class="sources-label">sources:</span>
          <span v-for="(s, j) in entry.sources" :key="j" class="source-tag">
            [{{ s.ticker }}·{{ s.date }}]
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  history: { type: Array, required: true },
})

const containerRef = ref(null)
const spinnerChar = ref('⠋')
const spinnerFrames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
let spinnerIdx = 0
let spinnerInterval = null

onMounted(() => {
  spinnerInterval = setInterval(() => {
    spinnerIdx = (spinnerIdx + 1) % spinnerFrames.length
    spinnerChar.value = spinnerFrames[spinnerIdx]
  }, 80)
})

onUnmounted(() => clearInterval(spinnerInterval))

watch(
  () => props.history.length,
  () => nextTick(() => {
    if (containerRef.value) containerRef.value.scrollTop = containerRef.value.scrollHeight
  })
)
</script>

<style scoped>
.terminal-output {
  flex: 1;
  padding: 20px;
  background: var(--bg-panel);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 15px;
  border-radius: 10px;
  border: 1px solid var(--border);
}

.empty {
  display: flex;
  gap: 6px;
  opacity: 0.4;
}

.empty-msg {
  color: var(--primary);
  font-style: italic;
}

.entry {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 20px;
}

.separator {
  color: var(--primary-dim);
  opacity: 0.6;
  letter-spacing: 0.02em;
  margin-bottom: 4px;
}

.meta-line {
  display: flex;
  align-items: center;
  gap: 0;
}

.prompt-dim {
  color: var(--primary);
  opacity: 0.4;
  white-space: nowrap;
}

.query-echo {
  color: var(--primary);
  opacity: 0.85;
}

.ticker-echo {
  color: var(--primary);
  opacity: 0.65;
}

.pending-line {
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  gap: 6px;
  padding-left: 4px;
  padding-top: 6px;
}

.cursor {
  animation: blink 1s step-end infinite;
  opacity: 0.6;
}

@keyframes blink {
  50% { opacity: 0; }
}

.spinner {
  display: inline-block;
}

.error-line {
  color: #e05c5c;
  padding-left: 4px;
  padding-top: 6px;
}

.result {
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-text {
  color: var(--primary);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.sources {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.sources-label {
  color: var(--primary);
  opacity: 0.55;
  font-size: 13px;
}

.source-tag {
  color: var(--primary);
  opacity: 0.6;
  font-size: 13px;
}
</style>
