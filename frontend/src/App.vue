<template>
  <div class="window">
    <WelcomeModal v-if="showWelcome" @close="showWelcome = false" />
    <div class="titlebar">
      <pre class="ascii-logo">
███████╗███████╗██╗ ██████╗ ██╗  ██╗████████╗
██╔════╝██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝
█████╗  ███████╗██║██║  ███╗███████║   ██║
██╔══╝  ╚════██║██║██║   ██║██╔══██║   ██║
██║     ███████║██║╚██████╔╝██║  ██║   ██║
╚═╝     ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝</pre>
      <span class="title-sub">RAG SEC 10-K Explorer</span>
    </div>
    <div class="panels">
      <TerminalInput
        :loading="loading"
        @search="handleSearch"
      />
      <div class="divider" />
      <TerminalOutput :history="history" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import TerminalInput from './components/TerminalInput.vue'
import TerminalOutput from './components/TerminalOutput.vue'
import WelcomeModal from './components/WelcomeModal.vue'
import { search } from './api.js'
import { WELCOME_SEEN_KEY } from './constants.js'

const showWelcome = ref(localStorage.getItem(WELCOME_SEEN_KEY) !== '1')
const loading = ref(false)
const history = ref([])

async function handleSearch({ question, ticker }) {
  loading.value = true
  history.value.push({ question, ticker, pending: true })
  const idx = history.value.length - 1
  try {
    const data = await search(question, ticker)
    history.value[idx] = { question, ticker, answer: data.answer, sources: data.sources, pending: false }
  } catch (e) {
    history.value[idx] = { question, ticker, error: e.message, pending: false }
  } finally {
    loading.value = false
  }
}
</script>

<style>
:root {
  --green: #00ff88;
  --green-dim: #006644;
  --bg: #0a0a0a;
  --bg-panel: #0d0d0d;
  --border: #1a1a1a;
  --font: 'Courier New', Courier, monospace;
  font-size: 15px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

.window {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  color: var(--green);
  font-family: var(--font);
  font-size: 13px;
}

.titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 16px;
  background: #111;
  border-bottom: 1px solid var(--border);
  user-select: none;
  flex-shrink: 0;
  gap: 20px;
}

.ascii-logo {
  font-family: var(--font);
  font-size: 5px;
  line-height: 1.2;
  color: var(--green);
  white-space: pre;
  opacity: 0.85;
}

.title-sub {
  font-size: 11px;
  color: var(--green-dim);
  letter-spacing: 0.1em;
  white-space: nowrap;
  margin-left: auto;
}

.controls {
  display: flex;
  gap: 10px;
}

.ctrl {
  font-size: 12px;
  color: #333;
  cursor: default;
}

.panels {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.divider {
  width: 1px;
  background: var(--border);
  flex-shrink: 0;
}
</style>
