<template>
  <div class="window">
    <WelcomeModal v-if="showWelcome" @close="showWelcome = false" />
    <div class="titlebar">
      <pre class="ascii-logo"><span style="color:#fde68a">███████╗███████╗██╗ ██████╗ ██╗  ██╗████████╗</span>
<span style="color:#fbbf24">██╔════╝██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝</span>
<span style="color:#fb923c">█████╗  ███████╗██║██║  ███╗███████║   ██║   </span>
<span style="color:#f97316">██╔══╝  ╚════██║██║██║   ██║██╔══██║   ██║   </span>
<span style="color:#ea580c">██║     ███████║██║╚██████╔╝██║  ██║   ██║   </span>
<span style="color:#c2410c">╚═╝     ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝  </span></pre>
      <span class="title-sub">RAG SEC 10-K Explorer</span>
    </div>
    <div class="panels">
      <TerminalInput
        :loading="loading"
        :dates="dates"
        @search="handleSearch"
      />
      <TerminalOutput :history="history" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TerminalInput from './components/TerminalInput.vue'
import TerminalOutput from './components/TerminalOutput.vue'
import WelcomeModal from './components/WelcomeModal.vue'
import { search, getDates } from './api.js'
const showWelcome = ref(true)
const loading = ref(false)
const history = ref([])
const dates = ref({})

onMounted(async () => { dates.value = await getDates() })
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
  --primary: #ffffff;
  --primary-dim: rgba(240,240,240,0.65);
  --bg: #161616;
  --bg-panel: #1c1c1c;
  --border: #2a2a2a;
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
  color: var(--primary);
  font-family: var(--font);
  font-size: 13px;
  font-weight: 500;
}

.titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 16px;
  background: #252525;
  border-bottom: 1px solid var(--border);
  user-select: none;
  flex-shrink: 0;
  gap: 20px;
}

.ascii-logo {
  font-family: var(--font);
  font-size: 5px;
  line-height: 1.2;
  white-space: pre;
}

.title-sub {
  font-size: 11px;
  color: var(--primary-dim);
  letter-spacing: 0.1em;
  white-space: nowrap;
  margin-left: auto;
}

.panels {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 14px 16px;
  gap: 14px;
}
</style>
