---
layout: default
title: Davi Liu's AI Blogs
---

<style>
  .ai-steps { counter-reset: step; padding-left: 0; }
  .ai-steps li { counter-increment: step; list-style: none; margin-bottom: 1em; padding-left: 2.5em; position: relative; }
  .ai-steps li::before { content: counter(step); position: absolute; left: 0; top: 0; width: 1.8em; height: 1.8em; background: #0969da; color: #fff; border-radius: 50%; text-align: center; line-height: 1.8em; font-weight: 600; font-size: 0.85em; }
  hr { border: 0; border-top: 1px solid #d0d7de; margin: 2em 0; }

  /* 文章卡片列表 */
  .post-list {
    display: flex;
    flex-direction: column;
    gap: 0.75em;
    margin: 1.2em 0;
  }
  .post-card {
    background: #fff;
    border: 1px solid #e8eaed;
    border-radius: 10px;
    padding: 1em 1.3em;
    transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
    display: flex;
    align-items: center;
    gap: 1em;
  }
  .post-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(9,105,218,0.08), 0 1px 3px rgba(0,0,0,0.03);
    border-color: #b6c8e5;
  }
  .post-card-body {
    flex: 1;
    min-width: 0;
  }
  .post-card-title {
    font-weight: 650;
    font-size: 1em;
    line-height: 1.45;
    margin-bottom: 0.15em;
  }
  .post-card-title a {
    color: #1a1a2e;
    text-decoration: none;
  }
  .post-card-title a:hover {
    color: #0969da;
  }
  .post-card-desc {
    font-size: 0.87em;
    color: #656d76;
    line-height: 1.55;
  }
  .post-card-meta {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.25em;
    font-size: 0.78em;
    color: #8b949e;
  }
  .post-card-tag {
    display: inline-block;
    background: #eef3fb;
    color: #0550ae;
    border-radius: 20px;
    padding: 0.12em 0.65em;
    font-size: 0.85em;
    font-weight: 500;
    white-space: nowrap;
  }

  /* 图片灯箱 */
  .img-lightbox { display: none; position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.82); align-items: center; justify-content: center; }
  .img-lightbox:target { display: flex; }
  .img-lightbox img { max-width: 92vw; max-height: 90vh; border-radius: 10px; box-shadow: 0 8px 40px rgba(0,0,0,0.4); }
  .img-lightbox-close { position: absolute; top: 18px; right: 24px; font-size: 2em; color: #ccc; text-decoration: none; line-height: 1; transition: color 0.15s; }
  .img-lightbox-close:hover { color: #fff; }
  .img-lightbox-bg { position: absolute; inset: 0; cursor: default; }
</style>

# Davi Liu's AI Blogs

---

## 文章目录

<div class="post-list">

  <a href="blogs/math-primer-for-ml" style="text-decoration:none; color:inherit;">
  <div class="post-card">
    <div class="post-card-body">
      <div class="post-card-title">机器学习快速入门——数学部分</div>
      <div class="post-card-desc">线性代数、概率论、微积分与优化理论的 ML 核心数学速览，从向量矩阵推进到反向传播与梯度下降。</div>
    </div>
    <div class="post-card-meta">
      <span class="post-card-tag">约 1.6 万字</span>
      <span>基础入门</span>
    </div>
  </div>
  </a>

  <a href="blogs/diffusion-math" style="text-decoration:none; color:inherit;">
  <div class="post-card">
    <div class="post-card-body">
      <div class="post-card-title">Diffusion 模型的数学主线</div>
      <div class="post-card-desc">从 DDPM 马尔可夫链到 Score-based SDE，再到概率流 ODE——完整推导扩散模型的数学骨架。</div>
    </div>
    <div class="post-card-meta">
      <span class="post-card-tag">约 1.9 万字</span>
      <span>生成模型</span>
    </div>
  </div>
  </a>

  <a href="blogs/YOLO-Complete-Learning-Guide" style="text-decoration:none; color:inherit;">
  <div class="post-card">    <div class="post-card-body">
      <div class="post-card-title">YOLO 目标检测：十年演进 2015–2026</div>
      <div class="post-card-desc">从 YOLOv1 网格划分到 YOLO26 端到端革新，架构迭代、标签分配、损失函数与训练技巧的系统梳理。</div>
    </div>
    <div class="post-card-meta">
      <span class="post-card-tag">约 3.2 万字</span>
      <span>目标检测</span>
    </div>
  </div>
  </a>

  <a href="blogs/mla_modes_deep_dive" style="text-decoration:none; color:inherit;">
  <div class="post-card">    <div class="post-card-body">
      <div class="post-card-title">MLA 双模式深度专题</div>
      <div class="post-card-desc">MHA 模式 vs MQA 模式，深入 KV cache 压缩原理与推理加速的关键设计决策。</div>
    </div>
    <div class="post-card-meta">
      <span class="post-card-tag">约 0.3 万字</span>
      <span>注意力机制</span>
    </div>
  </div>
  </a>

  <a href="blogs/dsv4_att" style="text-decoration:none; color:inherit;">
  <div class="post-card">    <div class="post-card-body">
      <div class="post-card-title">DeepSeek-V4 注意力机制深度解析</div>
      <div class="post-card-desc">拆解稀疏注意力、NSA 算子与 MLA 融合，理解长上下文低开销背后的工程取舍。</div>
    </div>
    <div class="post-card-meta">
      <span class="post-card-tag">约 0.9 万字</span>
      <span>LLM 架构</span>
    </div>
  </div>
  </a>

  <a href="blogs/world-models-survey" style="text-decoration:none; color:inherit;">
  <div class="post-card">    <div class="post-card-body">
      <div class="post-card-title">世界模型综述：从像素之梦到表征理解</div>
      <div class="post-card-desc">Dreamer 系列到 Transformer-based 世界模型，latent dynamics、tokenized state 与 3D-aware 三大范式全景梳理。</div>
    </div>
    <div class="post-card-meta">
      <span class="post-card-tag">约 3.6 万字</span>
      <span>综述</span>
    </div>
  </div>
  </a>

  <a href="blogs/cot-survey" style="text-decoration:none; color:inherit;">
  <div class="post-card">    <div class="post-card-body">
      <div class="post-card-title">思维链：从提示工程到推理时训练</div>
      <div class="post-card-desc">从 Few-shot CoT 到 DeepSeek-R1 推理时强化学习，LLM 推理能力从 Prompt 技巧到训练范式的跃迁。</div>
    </div>
    <div class="post-card-meta">
      <span class="post-card-tag">约 1.8 万字</span>
      <span>LLM 推理</span>
    </div>
  </div>
  </a>

</div>

---

## 建议使用 AI Agent 阅读

这个仓库最适合的打开方式是：**用 VS Code + Claude Code 把文章下载到本地，逐段精读。** 你不需要安装 git、不需要懂命令行——全程在 VS Code 里用自然语言对话就能完成。

### 三步开始

<ol class="ai-steps">
  <li>
    <strong>安装 VS Code 并配置 Claude Code</strong><br>
    <strong>①</strong> 下载安装 <a href="https://code.visualstudio.com/">VS Code</a>。<br>
    <strong>②</strong> 在 VS Code 扩展商店（<code>Ctrl+Shift+X</code>）搜索并安装 <a href="https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code">Claude Code</a>（发布者 Anthropic，标识符 <code>anthropic.claude-code</code>）和 <code>Markdown Preview Enhanced</code>（用于漂亮的文章渲染预览）。重启 VS Code。<br><br>

    <details style="background:#f6f8fa; border-left:4px solid #0969da; padding:1em 1.2em; margin:1.5em 0; border-radius:4px;">
    <summary style="font-weight:600; cursor:pointer; color:#0969da;">⚙️ 可选：配置 DeepSeek 作为后端模型（中国大陆地区用户必读）</summary><br>
    Claude Code 默认通过 Anthropic 官方 API（<code>api.anthropic.com</code>）调用 Claude 模型。由于网络限制，中国大陆地区无法直接访问该端点。推荐使用 <strong>DeepSeek</strong> 作为替代后端——DeepSeek API 国内可直接访问，模型能力强、性价比极高，且与 Claude Code 兼容。如果你不在大陆且已拥有 Anthropic API 额度，可以跳过本节。<br><br>
    <strong>① 获取 DeepSeek API Key</strong><br>
    访问 <a href="https://platform.deepseek.com/">DeepSeek 开放平台</a> 注册账号，进入「API Keys」页面创建 API Key。新用户通常有免费额度，后续按量计费，价格远低于海外模型。<strong>创建后立刻复制 Key 保存好</strong>，关掉页面就看不到了。<br><br>
    <strong>② 关闭登录提示</strong><br>
    打开 VS Code 设置（<code>Cmd+,</code> 或 <code>Ctrl+,</code>），搜索 <code>claude code login</code>，勾选 <strong>Disable Login Prompt</strong>。<br><br>
    <strong>③ 创建配置文件并写入配置</strong><br>
    注意：配置要写在 Claude Code 自己的配置文件里（<code>~/.claude/settings.json</code>），<strong>不是</strong> VS Code 的 <code>settings.json</code>。后者经常会失效。<br><br>
    <em>Mac：</em>打开终端，运行：<br>
    <code>mkdir -p ~/.claude && touch ~/.claude/settings.json && open ~/.claude/settings.json</code><br>
    <em>Windows：</em>按 <code>Win+R</code>，输入 <code>cmd</code> 回车，运行：<br>
    <code>md %USERPROFILE%\\.claude 2>nul & echo {} > %USERPROFILE%\\.claude\\settings.json & start %USERPROFILE%\\.claude\\settings.json</code><br><br>
    在打开的文件中填入以下内容（把 <code>sk-xxx</code> 换成你的 API Key）：<br>
    <pre style="background:#fff; padding:0.6em 1em; border-radius:4px; border:1px solid #d0d7de; overflow-x:auto;"><code>{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-你的DeepSeek-API-Key填这里",
    "ANTHROPIC_MODEL": "DeepSeek-V4-Pro[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "DeepSeek-V4-Pro[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "DeepSeek-V4-Pro[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "DeepSeek-V4-Pro[1m]"
  }
}</code></pre>
    保存后<strong>完全退出 VS Code 再重新打开</strong>，配置即可生效。如果 DeepSeek 后续推出新模型，把上面 <code>ANTHROPIC_MODEL</code> 和 <code>ANTHROPIC_DEFAULT_*_MODEL</code> 里的模型名换成新的即可。
    </details>
    
  </li>

<li>
    <strong>用 Claude Code 一键下载文章</strong><br>
    随便用 VS Code 打开一个空白文件夹，按 <code>Cmd+Shift+P</code>（Mac）或 <code>Ctrl+Shift+P</code>（Windows）打开命令面板，输入 <code>Claude Code: Open</code> 启动对话。在对话框中输入：<br>
    <code>请 clone 仓库 https://github.com/liuwwei3/liuwwei3.github.io.git 到当前文件夹下的 liuwwei3.github.io 子目录</code><br>
    Claude Code 执行完毕后，用 VS Code 打开 <code>liuwwei3.github.io</code> 文件夹。所有文章都在 <code>blogs/</code> 目录下。选中 <code>.md</code> 文件，用 <code>Ctrl+K V</code>（Mac: <code>Cmd+K V</code>）开启 Markdown 预览，边看边向 Claude Code 提问。
    配置完成之后，工作界面如下：<br>
    <a href="#img-vscode-setup"><img src="vscode-read-config.jpeg" alt="VS Code 工作界面" style="max-width:100%; border-radius:8px; margin-top:0.4em; border:1px solid #d0d7de; cursor:zoom-in;"></a>
  </li>
  <li>
    <strong>使用文中注释实现精细问答</strong><br>
    本项目的每篇文章都天然适合 AI 辅助阅读——你可以在阅读时用自然语言向 AI 提问。但需要注意：文章包含大量数学公式，如果直接在聊天窗口里复制包含公式的段落提问，公式经常会因格式转换而变形，导致 AI 理解错误，阅读体验很差。<br><br>
	    更好的做法是：你<span style="background:#fff3cd;padding:0 4px;">直接在原文中插入 HTML 注释 <code>&lt;!--你的问题--&gt;</code></span>，然后让 Claude Code 读取原文并逐条解答。这样公式直接从文件中读取，不会变形。<br>
    例如在不容易理解的部分后面加一行：<code>&lt;!--这里为什么用 log 而不是线性惩罚？--&gt;</code>，然后对 Claude Code 说「找出文中所有注释并解答」。
  </li>

</ol>

<!-- 图片灯箱浮层 -->
<div class="img-lightbox" id="img-vscode-setup">
  <a class="img-lightbox-bg" href="#_" title="关闭"></a>
  <a class="img-lightbox-close" href="#_" title="关闭 (Esc)">&times;</a>
  <img src="vscode-read-config.jpeg" alt="VS Code 工作界面">
