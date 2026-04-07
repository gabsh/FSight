<template>
  <div class="terminal-input">
    <div class="section">
      <div class="prompt-line">
        <span class="prompt">fsight@sec:~$</span>
        <span class="label">--ticker</span>
      </div>
      <div class="companies">
        <button
          v-for="c in companies"
          :key="c"
          class="company-btn"
          :class="{ active: ticker === c }"
          @click="ticker = c"
        >{{ c }}</button>
      </div>
      <div v-if="dates[ticker]?.length" class="ticker-years">
        └ {{ dates[ticker].join(', ') }}
      </div>
    </div>

    <div class="section query-section">
      <div class="prompt-line">
        <span class="prompt">fsight@sec:~$</span>
        <span class="label">query</span>
      </div>
      <div class="input-row">
        <span class="chevron">&gt;</span>
        <textarea
          ref="textareaRef"
          v-model="question"
          class="query-input"
          rows="1"
          :placeholder="loading ? 'running query...' : 'type your question and press Enter'"
          :disabled="loading"
          @keydown.enter.exact.prevent="submit"
          @input="autoResize"
        />
      </div>
      <div v-if="!question && !loading" class="example-query">
        <span class="example-prefix">e.g. </span>{{ typingText }}<span class="cursor">█</span>
      </div>
    </div>

    <div class="hint">
      <span class="prompt-dim">fsight@sec:~$</span>
      <span class="hint-text"> press Enter to search · Shift+Enter for new line</span>
    </div>
    <div class="lang-badge">50+ languages supported</div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { COMPANIES } from '../constants.js'

const props = defineProps({ loading: Boolean, dates: { type: Object, default: () => ({}) } })
const emit = defineEmits(['search'])

const companies = COMPANIES
const ticker = ref('AAPL')
const question = ref('')
const textareaRef = ref(null)

function submit() {
  const q = question.value.trim()
  if (!q || props.loading) return
  emit('search', { question: q, ticker: ticker.value })
  question.value = ''
  nextTick(() => autoResize())
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

const EXAMPLES = [
  "What were Apple's total revenues in 2023?",
  "How many employees does Meta have?",
  "What risks does Amazon highlight in its 10-K?",
  "What is Microsoft's R&D spending?",
  "What are Google's main sources of revenue?",
]

const typingText = ref('')
let animTimeout = null
let phraseIdx = 0
let charIdx = 0
let erasing = false

function tick() {
  if (question.value || props.loading) {
    typingText.value = ''
    return
  }
  const phrase = EXAMPLES[phraseIdx]
  if (!erasing) {
    charIdx++
    typingText.value = phrase.slice(0, charIdx)
    if (charIdx >= phrase.length) {
      erasing = true
      animTimeout = setTimeout(tick, 1800)
    } else {
      animTimeout = setTimeout(tick, 50)
    }
  } else {
    charIdx--
    typingText.value = phrase.slice(0, charIdx)
    if (charIdx <= 0) {
      erasing = false
      phraseIdx = (phraseIdx + 1) % EXAMPLES.length
      animTimeout = setTimeout(tick, 400)
    } else {
      animTimeout = setTimeout(tick, 28)
    }
  }
}

function restartAnim() {
  clearTimeout(animTimeout)
  charIdx = 0
  erasing = false
  typingText.value = ''
  animTimeout = setTimeout(tick, 600)
}

watch(() => question.value, (val) => {
  if (!val && !props.loading) restartAnim()
  else { clearTimeout(animTimeout); typingText.value = '' }
})

watch(() => props.loading, (val) => {
  if (!val && !question.value) restartAnim()
})

onMounted(() => { animTimeout = setTimeout(tick, 900) })
onUnmounted(() => clearTimeout(animTimeout))
</script>

<style scoped>
.terminal-input {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: var(--bg-panel);
  overflow-y: auto;
  gap: 28px;
  border-radius: 10px;
  border: 1px solid var(--border);
}

.section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.query-section {
  flex: 1;
}

.prompt-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompt {
  color: var(--primary);
  opacity: 0.65;
  white-space: nowrap;
}

.prompt-dim {
  color: var(--primary);
  opacity: 0.4;
  white-space: nowrap;
}

.label {
  color: var(--primary);
  font-weight: bold;
}

.companies {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding-left: 2px;
}

.company-btn {
  background: none;
  border: 1px solid var(--primary-dim);
  color: var(--primary-dim);
  font-family: var(--font);
  font-size: 15px;
  padding: 3px 10px;
  cursor: pointer;
  transition: all 0.1s;
  letter-spacing: 0.05em;
}

.company-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.company-btn.active {
  border-color: var(--primary);
  color: #1c1c1c;
  background: var(--primary);
}

.input-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.chevron {
  color: var(--primary);
  padding-top: 1px;
  flex-shrink: 0;
}

.query-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--primary);
  font-family: var(--font);
  font-size: 15px;
  resize: none;
  line-height: 1.5;
  caret-color: var(--primary);
  overflow: hidden;
  min-height: 20px;
}

.query-input::placeholder {
  color: var(--primary-dim);
  opacity: 0.6;
}

.query-input:disabled {
  opacity: 0.4;
}

.example-query {
  padding-left: 16px;
  font-size: 12px;
  color: var(--primary-dim);
  opacity: 0.9;
  min-height: 18px;
  letter-spacing: 0.02em;
}

.example-prefix {
  opacity: 0.5;
}

.ticker-years {
  font-size: 11px;
  color: var(--primary-dim);
  opacity: 0.8;
  padding-left: 2px;
  letter-spacing: 0.03em;
}

.lang-badge {
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--primary-dim);
  opacity: 0.65;
  margin-top: 8px;
}

.cursor {
  animation: blink 1s step-end infinite;
  opacity: 0.6;
}

@keyframes blink {
  50% { opacity: 0; }
}

.hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
}

.hint-text {
  color: var(--primary);
  opacity: 0.4;
  font-size: 11px;
}
</style>
