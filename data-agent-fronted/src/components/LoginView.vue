<template>
  <main class="login-page">
    <section class="brand-panel">
      <div class="brand-lockup">
        <div class="brand-mark">掌</div>
        <div>
          <strong>掌柜问数</strong>
          <span>DATA AGENT</span>
        </div>
      </div>

      <div class="brand-copy">
        <div class="eyebrow"><span></span> 企业级智能数据分析助手</div>
        <h1>让每一个业务问题，<br />都有清晰的数据答案。</h1>
        <p>
          用自然语言连接业务指标与数据仓库，从问题理解、Schema
          召回到安全 SQL 执行，一条链路完成分析。
        </p>

        <div class="feature-list">
          <div class="feature-item">
            <div class="feature-icon">01</div>
            <div><strong>自然语言问数</strong><span>无需编写 SQL，直接描述分析诉求</span></div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">02</div>
            <div><strong>可信指标口径</strong><span>语义层统一 GMV、客单价等业务定义</span></div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">03</div>
            <div><strong>安全可观测</strong><span>SQL 防护、执行链路与节点耗时全程可追踪</span></div>
          </div>
        </div>
      </div>

      <div class="tech-row">
        <span>Hybrid RAG</span><i></i><span>Semantic Layer</span><i></i><span>Text-to-SQL</span>
      </div>
      <div class="brand-orb orb-one"></div>
      <div class="brand-orb orb-two"></div>
    </section>

    <section class="form-panel">
      <form class="login-card" @submit.prevent="submit">
        <div class="mobile-brand">
          <div class="brand-mark">掌</div>
          <strong>掌柜问数</strong>
        </div>
        <div class="form-heading">
          <span>WELCOME BACK</span>
          <h2>登录工作台</h2>
          <p>登录后开始你的智能数据分析</p>
        </div>

        <label class="field-label" for="username">账号</label>
        <div class="field" :class="{ invalid: error }">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20 21a8 8 0 0 0-16 0m8-10a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />
          </svg>
          <input id="username" v-model.trim="username" autocomplete="username" placeholder="请输入账号" />
        </div>

        <label class="field-label" for="password">密码</label>
        <div class="field" :class="{ invalid: error }">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <rect x="4" y="10" width="16" height="11" rx="2" />
            <path d="M8 10V7a4 4 0 0 1 8 0v3" />
          </svg>
          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="请输入密码"
          />
          <button class="visibility" type="button" @click="showPassword = !showPassword">
            {{ showPassword ? "隐藏" : "显示" }}
          </button>
        </div>

        <div class="form-options">
          <label><input v-model="remember" type="checkbox" /> <span>记住登录状态</span></label>
          <span class="demo-label">演示环境</span>
        </div>

        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="login-button" type="submit">
          进入智能问数平台
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
        </button>

        <div class="demo-account">
          <span>体验账号</span>
          <code>admin</code>
          <b>/</b>
          <code>123456</code>
        </div>
        <p class="security-note">当前为作品演示登录，生产环境应接入后端 JWT / OAuth2 鉴权。</p>
      </form>
      <p class="copyright">© 2026 掌柜问数 · Data Agent Learning Project</p>
    </section>
  </main>
</template>

<script setup>
import { ref } from "vue";

const emit = defineEmits(["login"]);
const username = ref("admin");
const password = ref("123456");
const remember = ref(true);
const showPassword = ref(false);
const error = ref("");

function submit() {
  if (username.value !== "admin" || password.value !== "123456") {
    error.value = "账号或密码不正确，请使用下方体验账号";
    return;
  }
  error.value = "";
  emit("login", { username: username.value, remember: remember.value });
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: grid; grid-template-columns: minmax(520px, 1.15fr) minmax(440px, .85fr); background: #f7f9fc; }
.brand-panel { position: relative; overflow: hidden; display: flex; flex-direction: column; padding: 46px clamp(48px, 6vw, 96px); color: white; background: radial-gradient(circle at 88% 15%, rgba(60, 211, 190, .2), transparent 26%), linear-gradient(145deg, #07172c 0%, #0b2944 55%, #0b3a50 100%); }
.brand-lockup, .mobile-brand { display: flex; align-items: center; gap: 12px; position: relative; z-index: 2; }
.brand-mark { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 13px; color: #082236; background: #59e1c2; font: 800 22px/1 "Microsoft YaHei", sans-serif; box-shadow: 0 10px 30px rgba(55, 221, 190, .24); }
.brand-lockup strong { display: block; font-size: 19px; letter-spacing: .08em; }
.brand-lockup span { display: block; margin-top: 2px; color: #8ea8bd; font-size: 9px; letter-spacing: .28em; }
.brand-copy { position: relative; z-index: 2; margin: auto 0; max-width: 670px; }
.eyebrow { display: flex; align-items: center; gap: 10px; color: #82d9ca; font-size: 13px; letter-spacing: .14em; }
.eyebrow span { width: 28px; height: 1px; background: #59e1c2; }
h1 { margin: 22px 0 20px; font-size: clamp(38px, 4vw, 60px); line-height: 1.25; letter-spacing: -.035em; font-weight: 700; }
.brand-copy > p { max-width: 570px; margin: 0; color: #a9bdcc; font-size: 16px; line-height: 1.9; }
.feature-list { display: grid; gap: 18px; margin-top: 42px; }
.feature-item { display: flex; align-items: center; gap: 15px; }
.feature-icon { width: 39px; height: 39px; flex: 0 0 auto; display: grid; place-items: center; border: 1px solid rgba(89, 225, 194, .34); border-radius: 11px; color: #62ddc2; background: rgba(89, 225, 194, .08); font: 700 11px/1 ui-monospace, monospace; }
.feature-item strong, .feature-item span { display: block; }
.feature-item strong { font-size: 14px; }
.feature-item span { margin-top: 4px; color: #8fa9bc; font-size: 12px; }
.tech-row { position: relative; z-index: 2; display: flex; align-items: center; gap: 14px; color: #718da2; font: 600 10px/1 ui-monospace, monospace; letter-spacing: .12em; }
.tech-row i { width: 3px; height: 3px; border-radius: 50%; background: #3f647b; }
.brand-orb { position: absolute; border: 1px solid rgba(89, 225, 194, .1); border-radius: 50%; }
.orb-one { width: 420px; height: 420px; right: -190px; bottom: -170px; }
.orb-two { width: 270px; height: 270px; right: -115px; bottom: -95px; }
.form-panel { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px clamp(32px, 5vw, 88px) 24px; }
.login-card { width: min(100%, 410px); }
.mobile-brand { display: none; color: #10263c; margin-bottom: 38px; }
.form-heading span { color: #15967f; font-size: 11px; font-weight: 800; letter-spacing: .18em; }
.form-heading h2 { margin: 10px 0 8px; color: #10263c; font-size: 32px; letter-spacing: -.025em; }
.form-heading p { margin: 0 0 34px; color: #7a8b9c; font-size: 14px; }
.field-label { display: block; margin: 18px 0 8px; color: #30465a; font-size: 13px; font-weight: 650; }
.field { height: 50px; display: flex; align-items: center; gap: 11px; padding: 0 15px; border: 1px solid #dce4eb; border-radius: 12px; background: #fff; transition: .2s ease; }
.field:focus-within { border-color: #22aa91; box-shadow: 0 0 0 4px rgba(34, 170, 145, .09); }
.field.invalid { border-color: #e99797; }
.field svg { width: 18px; fill: none; stroke: #8da0b0; stroke-width: 1.7; }
.field input { min-width: 0; flex: 1; border: 0; outline: 0; color: #182f43; background: transparent; font-size: 14px; }
.field input::placeholder { color: #aab7c2; }
.visibility { padding: 5px; border: 0; color: #7d8f9e; background: transparent; font-size: 11px; }
.form-options { display: flex; align-items: center; justify-content: space-between; margin: 17px 0 0; color: #6f8190; font-size: 12px; }
.form-options label { display: flex; align-items: center; gap: 7px; cursor: pointer; }
.form-options input { accent-color: #169b83; }
.demo-label { padding: 4px 9px; border-radius: 999px; color: #147f6e; background: #e8f7f3; font-weight: 700; }
.form-error { margin: 12px 0 -4px; color: #d55252; font-size: 12px; }
.login-button { width: 100%; height: 51px; display: flex; align-items: center; justify-content: center; gap: 9px; margin-top: 24px; border: 0; border-radius: 12px; color: white; background: #0e826f; box-shadow: 0 12px 25px rgba(14, 130, 111, .2); font-size: 14px; font-weight: 700; transition: .2s ease; }
.login-button:hover { transform: translateY(-1px); background: #0a725f; box-shadow: 0 15px 30px rgba(14, 130, 111, .26); }
.login-button svg { width: 17px; fill: none; stroke: currentColor; stroke-width: 2; }
.demo-account { display: flex; align-items: center; justify-content: center; gap: 9px; margin-top: 22px; color: #91a0ac; font-size: 11px; }
.demo-account code { padding: 3px 7px; border-radius: 5px; color: #526777; background: #edf1f5; }
.demo-account b { font-weight: 400; }
.security-note { margin: 16px auto 0; max-width: 340px; color: #a0adb8; font-size: 10px; line-height: 1.6; text-align: center; }
.copyright { margin: auto 0 0; padding-top: 42px; color: #a5b1bb; font-size: 10px; letter-spacing: .04em; }
@media (max-width: 900px) { .login-page { grid-template-columns: 1fr; } .brand-panel { display: none; } .form-panel { min-height: 100vh; } .mobile-brand { display: flex; } }
@media (max-width: 520px) { .form-panel { padding: 28px 24px 18px; } .login-card { width: 100%; } .form-heading h2 { font-size: 28px; } }
</style>
