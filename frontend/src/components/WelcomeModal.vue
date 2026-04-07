<template>
  <Teleport to="body">
    <div class="overlay" @keydown.enter="close" tabindex="-1" ref="overlayRef">
      <div class="modal">
        <div class="modal-titlebar">
          <span>fsight@sec:~$ ./welcome.sh</span>
          <button class="close-btn" @click="close">✕</button>
        </div>

        <div class="modal-body">
          <pre class="ascii"><span style="color:#fde68a">███████╗███████╗██╗ ██████╗ ██╗  ██╗████████╗</span>
<span style="color:#fbbf24">██╔════╝██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝</span>
<span style="color:#fb923c">█████╗  ███████╗██║██║  ███╗███████║   ██║</span>
<span style="color:#f97316">██╔══╝  ╚════██║██║██║   ██║██╔══██║   ██║</span>
<span style="color:#ea580c">██║     ███████║██║╚██████╔╝██║  ██║   ██║</span>
<span style="color:#c2410c">╚═╝     ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝</span></pre>

          <div class="section">
            <div class="section-title">// about</div>
            <p>FSight is a <span class="hl">RAG pipeline</span> (Retrieval-Augmented Generation) built on top of <span class="hl">SEC EDGAR 10-K annual filings</span>. Ask any question about the financials, risks, or strategy of the 5 covered companies and get an AI-synthesized answer grounded in official documents.</p>
          </div>

          <div class="section">
            <div class="section-title">// covered companies</div>
            <div class="tags">
              <span class="tag" v-for="c in companies" :key="c">{{ c }}</span>
            </div>
            <p>Each annual report includes historical comparisons (prior years' financials, multi-year trends), information from earlier periods may also be retrievable through these documents.</p>
          </div>

          <div class="section">
            <div class="section-title">// stack</div>
            <div class="stack-grid">
              <div class="stack-item"><span class="stack-key">embeddings</span><span class="stack-val">OpenAI text-embedding-3-small</span></div>
              <div class="stack-item"><span class="stack-key">reranker  </span><span class="stack-val">Voyage AI rerank-2.5</span></div>
              <div class="stack-item"><span class="stack-key">llm       </span><span class="stack-val">OpenAI gpt-4o-mini</span></div>
              <div class="stack-item"><span class="stack-key">vector db </span><span class="stack-val">Qdrant</span></div>
              <div class="stack-item"><span class="stack-key">backend   </span><span class="stack-val">FastAPI (Python)</span></div>
              <div class="stack-item"><span class="stack-key">frontend  </span><span class="stack-val">Vue 3 + Vite · nginx</span></div>
              <div class="stack-item"><span class="stack-key">source    </span><span class="stack-val">SEC EDGAR API</span></div>
              <div class="stack-item"><span class="stack-key">github    </span><span class="stack-val"><a class="gh-link" href="https://github.com/gabsh/FSight" target="_blank" rel="noopener">github.com/gabsh/FSight</a></span></div>
            </div>
          </div>

          <div class="section warning-section">
            <div class="section-title warning-title">// disclaimer</div>
            <p class="warning-text">This tool is <span class="hl-warn">experimental</span> and provided for informational purposes only. Answers are AI-generated from SEC filings and may be incomplete, outdated, or inaccurate. <span class="hl-warn">Do not rely on this tool for any financial, legal, or investment decisions.</span> Always refer to the original SEC filings.</p>
          </div>

          <div class="footer">
            <label class="no-show">
              <input type="checkbox" v-model="dontShowAgain" />
              <span>don't show again</span>
            </label>
            <button class="enter-btn" @click="close">
              [ Press Enter to continue ]
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { COMPANIES, WELCOME_SEEN_KEY } from '../constants.js'

const emit = defineEmits(['close'])
const overlayRef = ref(null)
const dontShowAgain = ref(false)

const companies = COMPANIES

onMounted(() => overlayRef.value?.focus())

function close() {
  if (dontShowAgain.value) localStorage.setItem(WELCOME_SEEN_KEY, '1')
  emit('close')
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  outline: none;
}

.modal {
  width: min(700px, 92vw);
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--primary-dim);
  background: var(--bg-panel);
  font-family: var(--font);
}

.modal-titlebar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background: #252525;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  color: var(--primary-dim);
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 12px;
  font-family: var(--font);
  padding: 0;
}

.close-btn:hover { color: var(--primary); }

.modal-body {
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ascii {
  font-size: 9px;
  line-height: 1.2;
  overflow-x: auto;
  white-space: pre;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  color: var(--primary);
  opacity: 0.65;
  font-size: 11px;
  letter-spacing: 0.08em;
}

p {
  color: var(--primary);
  opacity: 0.9;
  line-height: 1.7;
  font-size: 13px;
}

.hl { color: var(--primary); opacity: 1; font-weight: bold; }

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  border: 1px solid var(--primary-dim);
  color: var(--primary);
  padding: 2px 10px;
  font-size: 12px;
  letter-spacing: 0.05em;
}

.stack-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stack-item {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.stack-key {
  color: var(--primary);
  opacity: 0.6;
  white-space: pre;
  min-width: 80px;
}

.stack-val {
  color: var(--primary);
  opacity: 1;
}

.gh-link {
  color: var(--primary);
  opacity: 0.85;
  text-decoration: none;
  border-bottom: 1px solid var(--primary-dim);
}

.gh-link:hover {
  opacity: 1;
}

.warning-section {
  border: 1px solid #5a1a1a;
  padding: 14px;
  background: rgba(90, 26, 26, 0.15);
}

.warning-title { color: #e05c5c; opacity: 0.8; }

.warning-text { color: #e05c5c; opacity: 0.75; }

.hl-warn { color: #e05c5c; opacity: 1; font-weight: bold; }

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.no-show {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--primary);
  opacity: 0.55;
  font-size: 11px;
  cursor: pointer;
}

.no-show input { accent-color: var(--primary); cursor: pointer; }

.enter-btn {
  background: none;
  border: 1px solid var(--primary-dim);
  color: var(--primary);
  font-family: var(--font);
  font-size: 13px;
  padding: 6px 16px;
  cursor: pointer;
  transition: all 0.1s;
}

.enter-btn:hover {
  background: var(--primary);
  color: var(--bg);
}
</style>
