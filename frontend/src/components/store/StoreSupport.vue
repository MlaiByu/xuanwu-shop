<template>
  <div class="support">
    <Transition name="support-pop">
      <section v-if="open" class="panel" aria-label="智能客服">
        <header class="panel-head">
          <div class="who">
            <span class="avatar">玄</span>
            <div>
              <strong>客服小玄</strong>
              <span class="status">
                <i class="dot" />
                {{ userStore.isLoggedIn ? '在线 · 通常 1 分钟内回复' : '在线 · 登录后可查订单' }}
              </span>
            </div>
          </div>
          <button class="close" type="button" aria-label="收起" @click="open = false">
            <LineIcon name="close" :size="16" />
          </button>
        </header>

        <div ref="scrollRef" class="body">
          <div v-if="!userStore.isLoggedIn" class="login-tip">
            <span>登录后可以直接查订单和物流</span>
            <RouterLink to="/login" @click="open = false">去登录</RouterLink>
          </div>

          <div
            v-for="(item, index) in messages"
            :key="index"
            class="msg"
            :class="item.role"
          >
            <div class="bubble">
              <span v-if="item.intent" class="intent">{{ item.intent }}</span>
              <p>{{ item.text }}<span v-if="item.streaming" class="caret" /></p>
              <span v-if="item.ticketId" class="handoff">
                已转人工 · 工单 #{{ item.ticketId }}
              </span>
            </div>
          </div>

          <div v-if="!messages.length" class="quick">
            <p class="quick-title">可以这样问我</p>
            <button
              v-for="question in quickQuestions"
              :key="question"
              type="button"
              class="chip"
              @click="send(question)"
            >
              {{ question }}
            </button>
          </div>

          <p v-if="toolHint" class="tool-hint">{{ toolHint }}</p>
        </div>

        <form class="composer" @submit.prevent="submit">
          <textarea
            v-model="draft"
            rows="1"
            maxlength="500"
            placeholder="说说你想问的，例如「我的订单到哪了」"
            @keydown.enter.exact.prevent="submit"
          />
          <button class="send" type="submit" :disabled="sending || !draft.trim()">
            {{ sending ? '…' : '发送' }}
          </button>
        </form>
      </section>
    </Transition>

    <button
      v-if="!open"
      class="fab"
      type="button"
      :aria-label="unread ? `${unread} 条未读，打开客服` : '打开客服'"
      @click="open = true"
    >
      <LineIcon name="chat" :size="20" />
      <span class="fab-text">客服</span>
    </button>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { useUserStore } from '@/store/user'
import LineIcon from './LineIcon.vue'

const SESSION_KEY = 'xw_support_session'
const QUICK_QUESTIONS = ['我的订单到哪了', '怎么申请退货', '运费怎么算', '我要转人工']

const userStore = useUserStore()
const open = ref(false)
const draft = ref('')
const sending = ref(false)
const unread = ref(0)
const messages = ref([])
const quickQuestions = ref(QUICK_QUESTIONS)
const toolHint = ref('')
const scrollRef = ref(null)
const sessionId = ref('')
const historyLoaded = ref(false)

function scrollToEnd() {
  nextTick(() => {
    const el = scrollRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function ensureSession() {
  // 注意：sessionId 有值不代表历史已拉取，刷新后必须先补一次历史再发消息
  if (sessionId.value) {
    if (!historyLoaded.value) {
      historyLoaded.value = true
      await loadHistory()
    }
    return sessionId.value
  }
  const cached = localStorage.getItem(SESSION_KEY)
  if (cached) {
    sessionId.value = cached
    historyLoaded.value = true
    await loadHistory()
    return cached
  }
  try {
    const res = await fetch('/api/v1/support/sessions', { method: 'POST' })
    const payload = await res.json()
    sessionId.value = payload?.data?.session_id || ''
  } catch (e) {
    sessionId.value = ''
  }
  if (sessionId.value) localStorage.setItem(SESSION_KEY, sessionId.value)
  historyLoaded.value = true
  return sessionId.value
}

async function loadHistory() {
  if (!sessionId.value) return
  try {
    const res = await fetch(`/api/v1/support/sessions/${sessionId.value}/messages`)
    const payload = await res.json()
    const list = payload?.data?.messages || []
    if (list.length) {
      messages.value = list.map((item) => ({ role: item.role, text: item.content }))
      scrollToEnd()
    }
  } catch (e) {
    /* 历史加载失败不阻断新对话 */
  }
}

async function loadMeta() {
  try {
    const res = await fetch('/api/v1/support/meta')
    const payload = await res.json()
    if (payload?.data?.quick_questions?.length) {
      quickQuestions.value = payload.data.quick_questions
    }
  } catch (e) {
    /* 用默认快捷问题 */
  }
}

function submit() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  send(text)
}

async function send(text) {
  if (sending.value) return
  const id = await ensureSession()
  if (!id) {
    messages.value.push({ role: 'assistant', text: '会话建立失败，请刷新页面再试。' })
    return
  }

  draft.value = ''
  sending.value = true
  toolHint.value = ''
  messages.value.push({ role: 'user', text })
  const reply = { role: 'assistant', text: '', streaming: true }
  messages.value.push(reply)
  scrollToEnd()

  try {
    const res = await fetch('/api/v1/support/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: id, message: text })
    })
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const chunks = buffer.split('\n\n')
      buffer = chunks.pop() || ''
      for (const chunk of chunks) {
        const line = chunk.trim()
        if (!line.startsWith('data:')) continue
        handleEvent(JSON.parse(line.slice(5).trim()), reply)
      }
    }
  } catch (e) {
    reply.text = reply.text || '网络不太稳定，稍后再试一次？'
  } finally {
    reply.streaming = false
    sending.value = false
    toolHint.value = ''
    scrollToEnd()
    if (!open.value) unread.value += 1
  }
}

function handleEvent(payload, reply) {
  const { event, data } = payload || {}
  if (event === 'intent' && data?.label) {
    reply.intent = data.label
  } else if (event === 'tool') {
    if (data?.summary) toolHint.value = data.summary
  } else if (event === 'token' && data?.text) {
    reply.text += data.text
    toolHint.value = ''
    scrollToEnd()
  } else if (event === 'handoff') {
    reply.ticketId = data?.ticket_id
  } else if (event === 'done') {
    reply.text = data?.reply || reply.text
    reply.streaming = false
  } else if (event === 'error') {
    reply.text = '服务暂时不可用，稍后再试。'
    reply.streaming = false
  }
}

onMounted(() => {
  loadMeta()
  sessionId.value = localStorage.getItem(SESSION_KEY) || ''
})

watch(open, (value) => {
  if (value) {
    unread.value = 0
    ensureSession()
    scrollToEnd()
  }
})
</script>

<style scoped>
.support {
  position: relative;
  z-index: 70;
  font-family: var(--xw-font-sans);
}

/* ---------- 悬浮球 ---------- */
.fab {
  position: fixed;
  right: 22px;
  bottom: 22px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 46px;
  padding: 0 18px 0 14px;
  border: 1px solid var(--xw-ink);
  border-radius: 999px;
  background: var(--xw-ink);
  color: #f7f2e8;
  font-size: 12.5px;
  letter-spacing: 0.04em;
  cursor: pointer;
  box-shadow: 0 18px 30px -18px rgba(26, 22, 17, 0.75);
  transition: transform 0.18s var(--xw-ease), background 0.18s;
}

.fab:hover {
  transform: translateY(-2px);
  background: #2a231a;
}

.fab-text {
  padding-left: 2px;
}

/* ---------- 面板 ---------- */
.panel {
  position: fixed;
  right: 22px;
  bottom: 22px;
  width: 366px;
  height: 560px;
  display: flex;
  flex-direction: column;
  background: var(--xw-surface);
  border: 1px solid var(--xw-line);
  border-radius: 4px;
  box-shadow: 0 40px 70px -40px rgba(26, 22, 17, 0.55);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--xw-line);
  background: var(--xw-paper);
}

.who {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--xw-ink);
  color: #f7f2e8;
  font-size: 13px;
  letter-spacing: 0.1em;
}

.who strong {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 3px;
  font-size: 10.5px;
  color: var(--xw-muted);
}

.dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--xw-olive);
}

.close {
  border: 0;
  background: none;
  padding: 6px;
  color: var(--xw-muted);
  cursor: pointer;
}

.close:hover {
  color: var(--xw-ink);
}

/* ---------- 消息区 ---------- */
.body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--xw-paper);
}

.login-tip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border: 1px dashed var(--xw-line-ink);
  font-size: 11px;
  color: var(--xw-muted);
}

.login-tip a {
  color: var(--xw-ink);
  border-bottom: 1px solid var(--xw-line-ink);
  white-space: nowrap;
}

.msg {
  display: flex;
}

.msg.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 82%;
  padding: 9px 12px;
  border: 1px solid var(--xw-line);
  background: var(--xw-surface);
  font-size: 12.5px;
  line-height: 1.75;
  color: var(--xw-ink-soft);
  white-space: pre-wrap;
  word-break: break-word;
}

.msg.user .bubble {
  background: var(--xw-ink);
  border-color: var(--xw-ink);
  color: #f7f2e8;
}

.intent {
  display: inline-block;
  margin-bottom: 4px;
  padding: 1px 6px;
  border: 1px solid var(--xw-line);
  font-size: 9.5px;
  letter-spacing: 0.06em;
  color: var(--xw-muted);
}

.caret {
  display: inline-block;
  width: 6px;
  height: 12px;
  margin-left: 2px;
  vertical-align: -2px;
  background: var(--xw-accent);
  animation: caret-blink 0.9s steps(2) infinite;
}

@keyframes caret-blink {
  50% {
    opacity: 0;
  }
}

.handoff {
  display: block;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed var(--xw-line);
  font-size: 10.5px;
  color: var(--xw-accent);
}

/* ---------- 快捷问题 ---------- */
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.quick-title {
  width: 100%;
  font-size: 10.5px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--xw-muted);
}

.chip {
  padding: 6px 11px;
  border: 1px solid var(--xw-line-ink);
  background: transparent;
  font-size: 11.5px;
  color: var(--xw-ink-soft);
  cursor: pointer;
  transition: all 0.15s;
}

.chip:hover {
  background: var(--xw-ink);
  border-color: var(--xw-ink);
  color: #f7f2e8;
}

.tool-hint {
  font-size: 10.5px;
  color: var(--xw-muted);
  padding-left: 2px;
}

/* ---------- 输入 ---------- */
.composer {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px;
  border-top: 1px solid var(--xw-line);
  background: var(--xw-surface);
}

.composer textarea {
  flex: 1;
  max-height: 92px;
  min-height: 38px;
  padding: 9px 11px;
  border: 1px solid var(--xw-line);
  border-radius: 2px;
  background: var(--xw-paper);
  font-family: inherit;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--xw-ink);
  resize: none;
  outline: none;
}

.composer textarea:focus {
  border-color: var(--xw-line-ink);
}

.send {
  height: 38px;
  padding: 0 16px;
  border: 1px solid var(--xw-ink);
  background: var(--xw-ink);
  color: #f7f2e8;
  font-size: 12px;
  letter-spacing: 0.04em;
  cursor: pointer;
}

.send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.support-pop-enter-active,
.support-pop-leave-active {
  transition: opacity 0.18s var(--xw-ease), transform 0.18s var(--xw-ease);
}

.support-pop-enter-from,
.support-pop-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 760px) {
  /* 上移避开详情/购物车的吸底操作栏 */
  .fab {
    right: 14px;
    bottom: 84px;
  }
  .panel {
    right: 0;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 78vh;
    border-radius: 12px 12px 0 0;
    border-left: 0;
    border-right: 0;
    border-bottom: 0;
  }
  .body {
    padding: 14px;
  }
}
</style>
