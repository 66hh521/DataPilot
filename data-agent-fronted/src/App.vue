<template>
  <LoginView v-if="!currentUser" @login="handleLogin" />

  <div v-else class="app-shell">
    <header class="app-header">
      <button class="brand" aria-label="返回智能问数" @click="currentView = 'chat'">
        <span class="brand-mark">掌</span>
        <span class="brand-text"><strong>掌柜问数</strong><small>DATA AGENT</small></span>
      </button>

      <nav class="main-nav">
        <button :class="{ active: currentView === 'chat' }" @click="currentView = 'chat'">
          <svg viewBox="0 0 24 24"><path d="M4 5h16v12H8l-4 3V5Z" /><path d="M8 9h8M8 13h5" /></svg>
          智能问数
        </button>
        <button :class="{ active: currentView === 'guide' }" @click="currentView = 'guide'">
          <svg viewBox="0 0 24 24"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4Z" /><path d="M8 16h11M9 8h6M9 11h5" /></svg>
          使用文档
        </button>
      </nav>

      <div class="user-area">
        <div class="status-pill" :class="{ offline: !serviceOnline }"><i></i><span>{{ serviceOnline ? '服务已连接' : '服务未连接' }}</span></div>
        <div class="user-menu">
          <span class="user-avatar">{{ currentUser.charAt(0).toUpperCase() }}</span>
          <div><strong>{{ currentUser }}</strong><small>体验用户</small></div>
          <button title="退出登录" @click="logout">
            <svg viewBox="0 0 24 24"><path d="M10 5H5v14h5M14 8l4 4-4 4M18 12H9" /></svg>
          </button>
        </div>
      </div>
    </header>

    <GuideView v-if="currentView === 'guide'" @try-question="useGuideQuestion" />

    <main v-else class="chat-page">
      <div ref="messagesEl" class="messages" :class="{ empty: messages.length === 0 }">
        <section v-if="messages.length === 0" class="welcome-panel">
          <div class="welcome-icon">
            <span>掌</span><i></i>
          </div>
          <span class="welcome-kicker">AI-POWERED DATA ANALYSIS</span>
          <h1>今天想从数据中了解什么？</h1>
          <p>告诉我指标、分析维度和时间范围，我会完成数据检索、SQL 生成与安全执行。</p>

          <div class="starter-grid">
            <button v-for="item in starterQuestions" :key="item.question" @click="fillQuestion(item.question)">
              <span :class="item.color">{{ item.icon }}</span>
              <div><small>{{ item.category }}</small><strong>{{ item.question }}</strong></div>
              <b>↗</b>
            </button>
          </div>
          <button class="guide-shortcut" @click="currentView = 'guide'">
            第一次使用？查看功能介绍与操作说明 <span>→</span>
          </button>
        </section>

        <div v-for="(msg, index) in messages" :key="index" :class="['message-row', msg.role]">
          <div v-if="msg.role === 'assistant'" class="avatar assistant-avatar">掌</div>

          <div :class="['bubble', msg.type]">
            <div v-if="msg.type === 'text'">{{ msg.content }}</div>

            <div v-else-if="msg.type === 'steps'" class="steps-card">
              <div class="steps-header">
                <div><span class="pulse-dot" :class="{ done: msg.trace }"></span><strong>{{ msg.trace ? '分析完成' : 'Agent 正在分析' }}</strong></div>
                <small v-if="msg.requestId">ID {{ msg.requestId.slice(0, 8) }}</small>
              </div>
              <div class="steps">
                <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="step">
                  <span class="dot" :class="step.status"><i></i></span>
                  <span>{{ step.text }}</span>
                  <small>{{ statusLabel(step.status) }}</small>
                </div>
              </div>
              <div v-if="msg.trace" class="trace-summary">
                <span>总耗时 <b>{{ formatDuration(msg.trace.total_duration_ms) }}</b></span>
                <span>缓存命中 <b>{{ msg.trace.cache?.hits || 0 }}</b></span>
                <span>节点 <b>{{ Object.keys(msg.trace.node_durations_ms || {}).length }}</b></span>
              </div>
            </div>

            <div v-else-if="msg.type === 'table'" class="result-card">
              <div class="result-heading">
                <div><span>✓</span><div><strong>查询结果</strong><small>共 {{ msg.rowCount }} 条记录</small></div></div>
                <button v-if="msg.sql" @click="msg.showSql = !msg.showSql">{{ msg.showSql ? '收起 SQL' : '查看 SQL' }}</button>
              </div>
              <pre v-if="msg.showSql" class="sql-block"><code>{{ msg.sql }}</code></pre>
              <div class="table-wrap">
                <table class="result-table">
                  <thead><tr><th v-for="col in msg.columns" :key="col">{{ col }}</th></tr></thead>
                  <tbody><tr v-for="(row, rIdx) in msg.rows" :key="rIdx"><td v-for="col in msg.columns" :key="col">{{ row[col] }}</td></tr></tbody>
                </table>
              </div>
            </div>

            <div v-else-if="msg.type === 'error'" class="notice error-notice"><span>!</span><div><strong>查询未完成</strong><p>{{ msg.content }}</p></div></div>
            <div v-else-if="msg.type === 'empty'" class="notice empty-notice"><span>i</span><div><strong>暂无匹配数据</strong><p>{{ msg.content }}</p></div></div>
          </div>

          <div v-if="msg.role === 'user'" class="avatar user-avatar-message">{{ currentUser.charAt(0).toUpperCase() }}</div>
        </div>
        <div class="messages-bottom-spacer"></div>
      </div>

      <div class="input-wrapper">
        <div class="composer-shell">
          <div class="input-box">
            <textarea
              v-model="question"
              rows="1"
              :disabled="loading"
              placeholder="输入业务问题，例如：统计2025年各地区销售额..."
              @keydown.enter.exact.prevent="sendQuestion"
            ></textarea>
            <button class="send-button" :disabled="loading || !question.trim()" @click="sendQuestion">
              <svg v-if="!loading" viewBox="0 0 24 24"><path d="m5 12 14-7-4 14-3-6-7-1Z" /><path d="m12 13 7-8" /></svg>
              <span v-else class="spinner"></span>
            </button>
          </div>
          <div class="composer-meta"><span>Enter 发送 · Shift + Enter 换行</span><span><i></i> 只读安全查询</span></div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";
import GuideView from "./components/GuideView.vue";
import LoginView from "./components/LoginView.vue";

const API_URL = "/api/query";
const SESSION_KEY = "data-agent-demo-user";
const rememberedUser = localStorage.getItem(SESSION_KEY) || sessionStorage.getItem(SESSION_KEY);

const currentUser = ref(rememberedUser || "");
const currentView = ref("chat");
const question = ref("");
const loading = ref(false);
const messages = ref([]);
const messagesEl = ref(null);
const serviceOnline = ref(false);

const starterQuestions = [
  { icon: "¥", category: "销售趋势", question: "统计2025年各大区GMV", color: "mint" },
  { icon: "%", category: "用户洞察", question: "查询不同会员等级的平均客单价", color: "blue" },
  { icon: "#", category: "商品表现", question: "统计各商品品类的销量，取前5名", color: "orange" },
];

function handleLogin({ username, remember }) {
  currentUser.value = username;
  const storage = remember ? localStorage : sessionStorage;
  storage.setItem(SESSION_KEY, username);
  (remember ? sessionStorage : localStorage).removeItem(SESSION_KEY);
  checkService();
}

async function checkService() {
  try {
    const response = await fetch("/api/metrics", { method: "GET" });
    serviceOnline.value = response.ok;
  } catch {
    serviceOnline.value = false;
  }
}

onMounted(checkService);

function logout() {
  localStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(SESSION_KEY);
  currentUser.value = "";
  currentView.value = "chat";
  messages.value = [];
}

function fillQuestion(value) {
  question.value = value;
}

function useGuideQuestion(value) {
  currentView.value = "chat";
  question.value = value;
  nextTick(() => document.querySelector(".input-box textarea")?.focus());
}

function statusLabel(status) {
  return { running: "处理中", success: "完成", error: "失败" }[status] || "";
}

function formatDuration(milliseconds) {
  if (milliseconds < 1000) return `${Math.round(milliseconds)} ms`;
  return `${(milliseconds / 1000).toFixed(2)} s`;
}

function scrollToBottom() {
  const el = messagesEl.value;
  if (el) el.scrollTop = el.scrollHeight;
}

async function sendQuestion() {
  if (!question.value.trim() || loading.value) return;
  const q = question.value.trim();
  question.value = "";
  loading.value = true;
  messages.value.push({ role: "user", type: "text", content: q });
  const stepIndex = messages.value.push({ role: "assistant", type: "steps", steps: [], trace: null, requestId: "" }) - 1;
  await nextTick();
  scrollToBottom();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q }),
    });
    if (!response.ok) throw new Error(`请求失败（${response.status}）`);
    if (!response.body) throw new Error("服务器未返回数据流");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const evt of events) {
        const line = evt.trim();
        if (!line.startsWith("data:")) continue;
        let data;
        try { data = JSON.parse(line.replace(/^data:\s*/, "")); } catch { continue; }

        const stepMessage = messages.value[stepIndex];
        if (data.type === "request") {
          stepMessage.requestId = data.request_id || "";
        } else if (data.type === "progress") {
          let step = stepMessage.steps.find((item) => item.text === data.step);
          if (!step) stepMessage.steps.push({ text: data.step, status: data.status });
          else step.status = data.status;
        } else if (data.type === "result" && Array.isArray(data.data)) {
          messages.value.push(data.data.length === 0
            ? { role: "assistant", type: "empty", content: data.message || "未查询到符合条件的数据" }
            : { role: "assistant", type: "table", columns: Object.keys(data.data[0]), rows: data.data, rowCount: data.row_count ?? data.data.length, sql: data.sql, showSql: false });
        } else if (data.type === "error") {
          messages.value.push({ role: "assistant", type: "error", content: data.message || "发生错误" });
        } else if (data.type === "trace") {
          stepMessage.trace = data;
        }
        await nextTick();
        scrollToBottom();
      }
    }
  } catch (error) {
    messages.value.push({ role: "assistant", type: "error", content: error?.message || "请求失败" });
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
}
</script>

<style scoped>
.app-shell { min-height: 100vh; color: #173047; background: #f6f8fa; }
.app-header { position: sticky; top: 0; z-index: 20; height: 70px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 0 28px; border-bottom: 1px solid #e4e9ee; background: rgba(255,255,255,.94); backdrop-filter: blur(14px); }
.brand { display:flex;align-items:center;gap:11px;width:max-content;padding:0;border:0;background:none;text-align:left }.brand-mark{width:36px;height:36px;display:grid;place-items:center;border-radius:11px;color:#092439;background:#4ed6b8;font-weight:850;box-shadow:0 7px 18px rgba(42,184,155,.18)}.brand-text strong,.brand-text small{display:block}.brand-text strong{color:#142e44;font-size:15px;letter-spacing:.05em}.brand-text small{margin-top:1px;color:#91a1ad;font:650 7px/1 ui-monospace,monospace;letter-spacing:.2em}
.main-nav{align-self:stretch;display:flex;gap:5px}.main-nav button{position:relative;display:flex;align-items:center;gap:7px;padding:0 15px;border:0;color:#728391;background:none;font-size:12px}.main-nav button::after{content:"";position:absolute;left:15px;right:15px;bottom:0;height:2px;border-radius:2px;background:transparent}.main-nav button.active{color:#0c806d;font-weight:700}.main-nav button.active::after{background:#22ad94}.main-nav svg{width:16px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.user-area{justify-self:end;display:flex;align-items:center;gap:16px}.status-pill{display:flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;color:#648177;background:#edf8f4;font-size:9px;font-weight:650}.status-pill i{width:6px;height:6px;border-radius:50%;background:#26b894;box-shadow:0 0 0 3px rgba(38,184,148,.12)}.user-menu{display:flex;align-items:center;gap:9px}.user-menu>.user-avatar{width:30px;height:30px;display:grid;place-items:center;border-radius:9px;color:white;background:#183d55;font-size:11px;font-weight:750}.user-menu div strong,.user-menu div small{display:block}.user-menu div strong{color:#314a5d;font-size:11px}.user-menu div small{color:#9ba8b2;font-size:8px}.user-menu button{display:grid;place-items:center;width:28px;height:28px;padding:0;border:0;border-radius:8px;color:#91a0ab;background:none}.user-menu button:hover{color:#d15858;background:#fff0f0}.user-menu svg{width:15px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.status-pill.offline{color:#9a6c61;background:#fbf0ed}.status-pill.offline i{background:#db7864;box-shadow:0 0 0 3px rgba(219,120,100,.12)}
.chat-page{height:calc(100vh - 70px);overflow:hidden;background:radial-gradient(circle at 50% 25%,rgba(63,207,179,.045),transparent 28%),#f7f9fb}.messages{height:100%;overflow-y:auto;padding:30px max(24px,calc((100% - 980px)/2)) 190px}.messages.empty{display:flex;align-items:center;justify-content:center;padding-top:20px}.welcome-panel{width:min(780px,100%);margin:auto;text-align:center}.welcome-icon{position:relative;width:58px;height:58px;display:grid;place-items:center;margin:0 auto 19px;border:1px solid #dce9e6;border-radius:18px;background:white;box-shadow:0 12px 35px rgba(20,62,76,.09)}.welcome-icon span{display:grid;place-items:center;width:38px;height:38px;border-radius:12px;color:#0d4b41;background:#dff7f1;font-size:18px;font-weight:800}.welcome-icon i{position:absolute;right:8px;bottom:8px;width:7px;height:7px;border:2px solid white;border-radius:50%;background:#22b596}.welcome-kicker{color:#17967f;font:750 9px/1 ui-monospace,monospace;letter-spacing:.17em}.welcome-panel h1{margin:14px 0 9px;color:#19354b;font-size:30px;letter-spacing:-.025em}.welcome-panel>p{margin:0 auto;color:#7d8e9c;font-size:13px;line-height:1.7}.starter-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:11px;margin-top:32px}.starter-grid button{position:relative;display:flex;align-items:center;gap:11px;padding:16px;border:1px solid #e2e9ee;border-radius:14px;text-align:left;background:white;box-shadow:0 4px 18px rgba(24,57,76,.035);transition:.2s}.starter-grid button:hover{transform:translateY(-2px);border-color:#a8d7cd;box-shadow:0 10px 26px rgba(24,57,76,.08)}.starter-grid button>span{width:34px;height:34px;flex:0 0 auto;display:grid;place-items:center;border-radius:10px;font:750 13px/1 ui-monospace,monospace}.starter-grid .mint{color:#168873;background:#e7f7f3}.starter-grid .blue{color:#3977ab;background:#eaf3fa}.starter-grid .orange{color:#b87526;background:#fbf1e4}.starter-grid div{min-width:0}.starter-grid small,.starter-grid strong{display:block}.starter-grid small{margin-bottom:4px;color:#99a6b0;font-size:9px}.starter-grid strong{overflow:hidden;color:#41586a;font-size:11px;white-space:nowrap;text-overflow:ellipsis}.starter-grid b{margin-left:auto;color:#a8b4bc;font-size:12px}.guide-shortcut{margin-top:22px;padding:8px 12px;border:0;color:#788b99;background:none;font-size:10px}.guide-shortcut:hover{color:#12826f}.guide-shortcut span{margin-left:4px;color:#20a68e}
.message-row{display:flex;align-items:flex-start;margin-bottom:18px}.message-row.assistant{justify-content:flex-start}.message-row.user{justify-content:flex-end}.avatar{width:32px;height:32px;flex:0 0 auto;display:grid;place-items:center;margin:0 9px;border-radius:10px;font-size:11px;font-weight:800}.assistant-avatar{color:#0b5649;background:#dff6f0}.user-avatar-message{color:white;background:#193d54}.bubble{max-width:min(820px,78%);font-size:13px;line-height:1.65}.bubble.text{padding:10px 15px;border-radius:14px 4px 14px 14px;color:#264458;background:#e3f3f8}.steps-card,.result-card{overflow:hidden;border:1px solid #e2e8ed;border-radius:15px;background:white;box-shadow:0 8px 25px rgba(23,52,70,.055)}.steps-card{min-width:285px}.steps-header{display:flex;align-items:center;justify-content:space-between;padding:12px 15px;border-bottom:1px solid #edf1f4}.steps-header>div{display:flex;align-items:center;gap:8px}.steps-header strong{font-size:11px}.steps-header small{color:#a0adb7;font:600 8px/1 ui-monospace,monospace}.pulse-dot{width:7px;height:7px;border-radius:50%;background:#e7ae36;box-shadow:0 0 0 4px rgba(231,174,54,.12);animation:pulse 1.5s infinite}.pulse-dot.done{background:#20b18f;box-shadow:0 0 0 4px rgba(32,177,143,.1);animation:none}@keyframes pulse{50%{opacity:.45}}.steps{display:flex;flex-direction:column;gap:0;padding:7px 15px}.step{display:grid;grid-template-columns:14px 1fr auto;align-items:center;gap:8px;min-height:27px;color:#536a7b;font-size:10px}.step small{color:#a1adb6;font-size:8px}.dot{width:8px;height:8px;display:grid;place-items:center;border-radius:50%;background:#d8e0e5}.dot.running{background:#edb33c}.dot.success{background:#23b794}.dot.error{background:#de6262}.trace-summary{display:flex;gap:16px;padding:10px 15px;border-top:1px solid #edf1f4;color:#8b9aa6;background:#fafcfc;font-size:8px}.trace-summary b{color:#4d6677;font-weight:750}
.result-card{min-width:min(650px,100%)}.result-heading{display:flex;align-items:center;justify-content:space-between;padding:13px 15px}.result-heading>div{display:flex;align-items:center;gap:9px}.result-heading>div>span{width:26px;height:26px;display:grid;place-items:center;border-radius:8px;color:#10836f;background:#e5f7f2;font-size:11px;font-weight:800}.result-heading strong,.result-heading small{display:block}.result-heading strong{font-size:11px}.result-heading small{margin-top:2px;color:#94a2ad;font-size:8px}.result-heading button{padding:5px 9px;border:1px solid #dfe7ec;border-radius:7px;color:#648091;background:#fff;font-size:8px}.result-heading button:hover{border-color:#93cfc3;color:#137b69}.sql-block{overflow:auto;max-height:180px;margin:0;padding:13px 15px;border-top:1px solid #e7edf1;color:#b7d9d1;background:#102c3e;font:10px/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap}.table-wrap{max-width:100%;overflow:auto;border-top:1px solid #e8edf1}.result-table{width:100%;min-width:max-content;border-collapse:collapse}.result-table th,.result-table td{padding:9px 15px;border-bottom:1px solid #edf1f4;text-align:left;white-space:nowrap;font-size:10px}.result-table th{position:sticky;top:0;color:#6e8190;background:#f7f9fa;font-weight:700}.result-table td{color:#334d60}.result-table tbody tr:hover{background:#f7fbfa}.notice{display:flex;gap:11px;padding:14px 16px;border-radius:13px}.notice>span{width:25px;height:25px;flex:0 0 auto;display:grid;place-items:center;border-radius:8px;font-weight:800}.notice strong{font-size:11px}.notice p{margin:3px 0 0;font-size:10px}.error-notice{color:#8a3d3d;border:1px solid #f0d3d3;background:#fff5f5}.error-notice>span{color:#bc4f4f;background:#fbe1e1}.empty-notice{color:#667784;border:1px solid #e3e8eb;background:#fafbfc}.empty-notice>span{color:#647d8d;background:#eaf0f3}
.input-wrapper{position:fixed;z-index:10;left:0;right:0;bottom:0;display:flex;justify-content:center;padding:30px 20px 18px;background:linear-gradient(transparent,#f7f9fb 38%);pointer-events:none}.composer-shell{width:min(760px,100%);pointer-events:auto}.input-box{display:flex;align-items:flex-end;gap:10px;padding:11px 11px 11px 17px;border:1px solid #dce4e9;border-radius:17px;background:rgba(255,255,255,.97);box-shadow:0 13px 38px rgba(20,53,71,.13);transition:.2s}.input-box:focus-within{border-color:#7cc9ba;box-shadow:0 13px 38px rgba(20,53,71,.13),0 0 0 4px rgba(29,164,139,.07)}.input-box textarea{min-height:24px;max-height:100px;flex:1;resize:none;border:0;outline:0;color:#263f52;background:transparent;font:12px/1.7 inherit}.input-box textarea::placeholder{color:#a3afb8}.send-button{width:36px;height:36px;flex:0 0 auto;display:grid;place-items:center;padding:0;border:0;border-radius:11px;color:white;background:#11836f;box-shadow:0 7px 16px rgba(17,131,111,.2)}.send-button:disabled{opacity:.4;box-shadow:none}.send-button svg{width:16px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.spinner{width:13px;height:13px;border:2px solid rgba(255,255,255,.35);border-top-color:white;border-radius:50%;animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.composer-meta{display:flex;justify-content:space-between;padding:7px 7px 0;color:#a1adb6;font-size:8px}.composer-meta span:last-child{display:flex;align-items:center;gap:5px}.composer-meta i{width:5px;height:5px;border-radius:50%;background:#26b693}.messages-bottom-spacer{height:120px}
@media(max-width:760px){.app-header{height:64px;grid-template-columns:auto 1fr auto;gap:6px;padding:0 12px}.brand-text{display:none}.main-nav{position:static;justify-self:center;align-self:stretch;gap:3px}.main-nav button{padding:0 8px;font-size:10px}.main-nav button::after{display:none}.main-nav button.active{align-self:center;height:38px;border-radius:10px;background:#ebf8f5}.status-pill,.user-menu div{display:none}.chat-page{height:calc(100vh - 64px)}.messages{padding:22px 12px 150px}.messages.empty{align-items:flex-start;padding-top:42px}.starter-grid{grid-template-columns:1fr}.welcome-panel h1{font-size:25px}.bubble{max-width:88%}.result-card{min-width:0}.input-wrapper{bottom:0;padding-left:12px;padding-right:12px}.composer-meta{display:none}.user-area{gap:4px}}
</style>
