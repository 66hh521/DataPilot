<template>
  <div class="guide-page">
    <section class="guide-hero">
      <div>
        <span class="section-kicker">PRODUCT GUIDE · 产品文档</span>
        <h1>从业务问题到数据答案，<br />一份文档快速上手。</h1>
        <p>了解掌柜问数的核心能力、推荐提问方式和完整执行流程。</p>
      </div>
      <div class="hero-card">
        <span>快速开始</span>
        <strong>一句话描述你想分析的指标、维度与时间范围</strong>
        <button @click="$emit('try-question', '查询2025年1月各省份销售额，并按销售额从高到低排序')">
          使用示例问题 <b>→</b>
        </button>
      </div>
    </section>

    <nav class="doc-nav" aria-label="文档目录">
      <a href="#capabilities">功能介绍</a>
      <a href="#steps">操作步骤</a>
      <a href="#examples">问题示例</a>
      <a href="#tips">使用建议</a>
    </nav>

    <section id="capabilities" class="doc-section">
      <div class="section-title"><span>01</span><div><h2>核心功能</h2><p>面向经营分析的自然语言数据 Agent</p></div></div>
      <div class="capability-grid">
        <article v-for="item in capabilities" :key="item.title" class="capability-card">
          <div class="card-top"><span>{{ item.index }}</span><i :class="item.color"></i></div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
          <div class="tag-row"><span v-for="tag in item.tags" :key="tag">{{ tag }}</span></div>
        </article>
      </div>
    </section>

    <section id="steps" class="doc-section">
      <div class="section-title"><span>02</span><div><h2>操作步骤</h2><p>四步完成一次智能问数</p></div></div>
      <div class="steps-panel">
        <div v-for="(step, index) in steps" :key="step.title" class="guide-step">
          <div class="step-index">{{ String(index + 1).padStart(2, '0') }}</div>
          <div class="step-line"><i></i></div>
          <div class="step-copy"><h3>{{ step.title }}</h3><p>{{ step.description }}</p><code v-if="step.example">{{ step.example }}</code></div>
        </div>
      </div>
    </section>

    <section id="examples" class="doc-section">
      <div class="section-title"><span>03</span><div><h2>推荐问题</h2><p>点击即可带入智能问数输入框</p></div></div>
      <div class="example-grid">
        <button v-for="example in examples" :key="example.question" @click="$emit('try-question', example.question)">
          <span>{{ example.category }}</span>
          <strong>{{ example.question }}</strong>
          <i>立即提问 →</i>
        </button>
      </div>
    </section>

    <section id="tips" class="doc-section tips-section">
      <div class="section-title"><span>04</span><div><h2>使用建议与边界</h2><p>这样提问，结果更稳定</p></div></div>
      <div class="tips-layout">
        <div class="do-card">
          <h3><span>✓</span> 推荐这样提问</h3>
          <ul>
            <li>明确指标：销售额、客单价、订单数或商品销量</li>
            <li>明确维度：省份、大区、品类、品牌或会员等级</li>
            <li>明确时间：具体年月、季度或“去年”等相对时间</li>
            <li>需要排序或 Top N 时，在问题中直接说明</li>
          </ul>
        </div>
        <div class="boundary-card">
          <h3><span>!</span> 当前系统边界</h3>
          <ul>
            <li>仅执行只读查询，不支持新增、修改和删除数据</li>
            <li>结果基于当前数据仓库已有表、字段与指标口径</li>
            <li>复杂口径建议先在语义层登记，再进行自然语言查询</li>
            <li>登录页为作品演示，生产鉴权需要接入后端账号体系</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="architecture-strip">
      <div><span>自然语言</span><b>01</b></div><i>→</i><div><span>混合检索</span><b>02</b></div><i>→</i><div><span>语义层 / Schema Graph</span><b>03</b></div><i>→</i><div><span>安全 SQL</span><b>04</b></div><i>→</i><div><span>数据结果</span><b>05</b></div>
    </section>
  </div>
</template>

<script setup>
defineEmits(["try-question"]);

const capabilities = [
  { index: "A", title: "自然语言问数", description: "把经营分析问题直接转换为可执行 SQL，降低业务人员的数据使用门槛。", tags: ["NL2SQL", "流式反馈"], color: "green" },
  { index: "B", title: "混合 RAG 召回", description: "融合向量检索与 BM25，通过 RRF 排序召回相关字段、指标和值。", tags: ["Qdrant", "Elasticsearch"], color: "blue" },
  { index: "C", title: "统一语义层", description: "沉淀 GMV、客单价等指标公式，减少同一指标在不同查询中的口径漂移。", tags: ["Metric", "Schema Graph"], color: "orange" },
  { index: "D", title: "SQL 安全防护", description: "基于 AST 校验表和字段白名单，只允许单条只读查询并限制最大返回行数。", tags: ["SQLGlot", "Read Only"], color: "red" },
  { index: "E", title: "自动纠错", description: "SQL 验证或执行失败后，携带结构化错误进入有限次数的修正闭环。", tags: ["Retry", "Error Classify"], color: "purple" },
  { index: "F", title: "链路可观测", description: "按 request_id 记录节点耗时、模型分层、缓存命中与整体成功率。", tags: ["P95", "Trace"], color: "cyan" },
];

const steps = [
  { title: "登录工作台", description: "使用体验账号进入系统。登录状态仅保存在当前浏览器，不会提交密码到后端。" },
  { title: "描述分析问题", description: "尽量同时给出指标、分析维度、时间范围和排序方式。", example: "查询2025年1月各省份销售额，并按销售额从高到低排序" },
  { title: "观察 Agent 执行链", description: "页面会流式展示关键词抽取、字段与指标召回、Schema 扩展、SQL 生成和验证状态。" },
  { title: "查看并核对结果", description: "结果以表格呈现，可展开查看最终执行 SQL；未查到数据时会给出明确提示。" },
];

const examples = [
  { category: "销售分析", question: "统计2025年各大区GMV，并按金额降序排列" },
  { category: "用户分析", question: "查询不同会员等级的平均客单价" },
  { category: "商品分析", question: "统计各商品品类的销量，取前5名" },
  { category: "订单分析", question: "查询各品牌的订单数量" },
];
</script>

<style scoped>
.guide-page { width: min(1180px, calc(100% - 48px)); margin: 0 auto; padding: 48px 0 80px; color: #183047; }
.guide-hero { display: grid; grid-template-columns: 1.3fr .7fr; gap: 42px; align-items: end; padding: 46px 50px; border-radius: 24px; color: white; background: radial-gradient(circle at 90% 5%, rgba(65, 224, 192, .2), transparent 30%), #0a2238; overflow: hidden; }
.section-kicker { color: #63d8c0; font: 700 11px/1 ui-monospace, monospace; letter-spacing: .16em; }
.guide-hero h1 { margin: 18px 0 13px; font-size: clamp(34px, 4vw, 50px); line-height: 1.25; letter-spacing: -.035em; }
.guide-hero p { margin: 0; color: #9fb4c4; font-size: 14px; }
.hero-card { padding: 23px; border: 1px solid rgba(255,255,255,.1); border-radius: 16px; background: rgba(255,255,255,.06); backdrop-filter: blur(8px); }
.hero-card span, .hero-card strong { display: block; }.hero-card span { color: #64d9c1; font-size: 11px; font-weight: 750; }.hero-card strong { margin: 9px 0 18px; font-size: 14px; line-height: 1.7; }
.hero-card button { padding: 0; border: 0; color: #fff; background: none; font-size: 12px; }.hero-card b { margin-left: 5px; color: #5be0c4; }
.doc-nav { position: sticky; top: 72px; z-index: 5; display: flex; gap: 8px; margin: 22px 0 56px; padding: 8px; border: 1px solid #e5ebf0; border-radius: 13px; background: rgba(255,255,255,.92); box-shadow: 0 8px 30px rgba(21,48,70,.06); backdrop-filter: blur(12px); }
.doc-nav a { padding: 9px 16px; border-radius: 8px; color: #617486; font-size: 12px; font-weight: 650; }.doc-nav a:hover { color: #117d6b; background: #eef8f6; }
.doc-section { scroll-margin-top: 140px; margin-bottom: 70px; }
.section-title { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }.section-title > span { color: #18a087; font: 700 11px/1 ui-monospace, monospace; }.section-title h2 { margin: 0; font-size: 24px; }.section-title p { margin: 4px 0 0; color: #8a9aa8; font-size: 12px; }
.capability-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }.capability-card { min-height: 185px; padding: 22px; border: 1px solid #e4eaf0; border-radius: 16px; background: white; transition: .2s ease; }.capability-card:hover { transform: translateY(-3px); border-color: #c8dbd7; box-shadow: 0 14px 35px rgba(22,52,72,.08); }
.card-top { display: flex; justify-content: space-between; color: #9aabba; font: 700 10px/1 ui-monospace, monospace; }.card-top i { width: 8px; height: 8px; border-radius: 50%; }.green{background:#21b194}.blue{background:#388bd6}.orange{background:#e69c43}.red{background:#dc6868}.purple{background:#876fd1}.cyan{background:#36aeb9}
.capability-card h3 { margin: 24px 0 9px; font-size: 16px; }.capability-card p { min-height: 58px; margin: 0; color: #687b8c; font-size: 12px; line-height: 1.7; }.tag-row { display: flex; gap: 6px; margin-top: 16px; }.tag-row span { padding: 4px 8px; border-radius: 5px; color: #668090; background: #f1f5f7; font: 600 9px/1 ui-monospace, monospace; }
.steps-panel { padding: 12px 30px; border: 1px solid #e4eaf0; border-radius: 18px; background: white; }.guide-step { display: grid; grid-template-columns: 46px 28px 1fr; min-height: 112px; }.step-index { padding-top: 27px; color: #1a9d85; font: 750 12px/1 ui-monospace, monospace; }.step-line { display: flex; flex-direction: column; align-items: center; }.step-line::before { content:""; width: 1px; flex: 1; background: #dfe8e7; }.step-line::after { content:""; width: 1px; flex: 1; background: #dfe8e7; }.step-line i { width: 9px; height: 9px; flex: 0 0 auto; border: 3px solid #d9f4ee; border-radius: 50%; background: #18a087; }.guide-step:first-child .step-line::before,.guide-step:last-child .step-line::after{background:transparent}.step-copy { padding: 22px 0 20px 18px; border-bottom: 1px solid #edf1f4; }.guide-step:last-child .step-copy{border-bottom:0}.step-copy h3 { margin: 0 0 7px; font-size: 14px; }.step-copy p { margin: 0; color: #718392; font-size: 12px; line-height: 1.7; }.step-copy code { display: inline-block; margin-top: 9px; padding: 6px 10px; border-radius: 6px; color: #167b6b; background: #ecf8f5; font-size: 11px; }
.example-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 12px; }.example-grid button { display: grid; gap: 10px; padding: 20px; border: 1px solid #e2e9ef; border-radius: 14px; text-align: left; background: white; transition:.2s }.example-grid button:hover { border-color:#81c9bb; transform:translateY(-2px); box-shadow:0 10px 25px rgba(22,52,72,.07) }.example-grid span { color:#15937d;font-size:10px;font-weight:750;letter-spacing:.08em }.example-grid strong { color:#263e52;font-size:13px }.example-grid i { color:#8a9aa7;font-size:10px;font-style:normal }
.tips-layout { display:grid;grid-template-columns:1fr 1fr;gap:14px }.do-card,.boundary-card{padding:24px;border-radius:16px}.do-card{border:1px solid #d7ebe6;background:#f2faf8}.boundary-card{border:1px solid #ece5d9;background:#fcf8f1}.tips-layout h3{margin:0 0 16px;font-size:14px}.tips-layout h3 span{display:inline-grid;place-items:center;width:22px;height:22px;margin-right:7px;border-radius:7px;background:white}.tips-layout ul{display:grid;gap:10px;margin:0;padding-left:20px;color:#607586;font-size:12px;line-height:1.65}
.architecture-strip { display:flex;align-items:center;justify-content:space-between;gap:12px;padding:22px 26px;border-radius:15px;color:white;background:#102b42 }.architecture-strip div{display:flex;flex-direction:column;gap:5px}.architecture-strip span{font-size:11px}.architecture-strip b{color:#5ccfba;font:700 9px/1 ui-monospace,monospace}.architecture-strip>i{color:#557185;font-style:normal}
@media(max-width:850px){.guide-hero{grid-template-columns:1fr}.capability-grid{grid-template-columns:repeat(2,1fr)}.doc-nav{overflow-x:auto}.doc-nav a{white-space:nowrap}.architecture-strip{overflow-x:auto}.architecture-strip div{min-width:100px}}
@media(max-width:600px){.guide-page{width:min(100% - 28px,1180px);padding-top:22px}.guide-hero{padding:30px 24px;border-radius:18px}.guide-hero h1{font-size:30px}.capability-grid,.example-grid,.tips-layout{grid-template-columns:1fr}.doc-nav{top:64px;margin-bottom:40px}.doc-section{margin-bottom:50px}.steps-panel{padding:8px 16px}.guide-step{grid-template-columns:38px 20px 1fr}.step-copy{padding-left:12px}}
</style>
