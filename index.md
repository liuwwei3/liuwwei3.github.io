---
layout: default
title: 大伟的AI学习日志
---

<style>
  .blog-list { list-style: none; padding: 0; }
  .blog-list li { margin-bottom: 0.8em; padding: 0.6em 0.9em; border-left: 3px solid #0969da; background: #f6f8fa; border-radius: 0 6px 6px 0; }
  .blog-list li .title { font-weight: 600; font-size: 1.05em; }
  .blog-list li .meta { font-size: 0.85em; color: #656d76; margin-left: 0.6em; }
  .blog-list li .desc { font-size: 0.9em; color: #57606a; margin-top: 0.2em; }
  .ai-steps { counter-reset: step; padding-left: 0; }
  .ai-steps li { counter-increment: step; list-style: none; margin-bottom: 1em; padding-left: 2.5em; position: relative; }
  .ai-steps li::before { content: counter(step); position: absolute; left: 0; top: 0; width: 1.8em; height: 1.8em; background: #0969da; color: #fff; border-radius: 50%; text-align: center; line-height: 1.8em; font-weight: 600; font-size: 0.85em; }
  .tip-box { border: 1px solid #d0d7de; border-radius: 8px; padding: 1em 1.2em; background: #f6f8fa; margin: 1em 0; }
  .tip-box summary { font-weight: 600; cursor: pointer; color: #0969da; }
  hr { border: 0; border-top: 1px solid #d0d7de; margin: 2em 0; }
</style>

# 大伟的AI学习日志

---

## 建议使用 AI Agent 阅读

这个仓库最适合的打开方式是：**用 VS Code 把文章下载到本地，配合 AI Agent 逐段精读。** 你不需要一开始就全部看懂——选中不懂的段落，直接向 AI 提问。

### 三步开始

<ol class="ai-steps">
  <li>
    <strong>Clone 仓库并用 VS Code 打开</strong><br>
    <code>git clone https://github.com/liuwwei3/liuwwei3.github.io.git</code><br>
    <code>cd liuwwei3.github.io</code>，然后用 VS Code 打开该文件夹。
  </li>
  <li>
    <strong>安装 AI 插件</strong><br>
    推荐以下任一方式（任选一个即可）：<br>
    <strong>Claude Code</strong> — 在 VS Code 终端中运行 <code>claude</code>，Claude 会自动加载仓库中的 <code>CLAUDE.md</code> 获得上下文，然后你直接选中 <code>blogs/</code> 下的文章开始对话。<br>
    <strong>GitHub Copilot Chat</strong> — VS Code 原生集成，打开 <code>.md</code> 文件，选中不懂的段落，<code>Ctrl+I</code>（Mac: <code>Cmd+I</code>）直接提问。<br>
    <strong>Cursor</strong> — 用 Cursor 打开仓库，侧栏对话中 <code>@file</code> 引用文章。
  </li>
  <li>
    <strong>使用文中注释实现精细问答</strong><br>
    本项目的每篇文章都天然适合 AI 辅助阅读——你可以在阅读时用自然语言向 AI 提问。更进一步，你<span style="background:#fff3cd;padding:0 4px;">可以在任意段落后插入 HTML 注释 <code>&lt;!--你的问题--&gt;</code></span>，然后让 AI Agent 逐条解答。<br>
    例如在不容易理解的部分后面加一行：<code>&lt;!--这里为什么用 log 而不是线性惩罚？--&gt;</code>，然后对 Agent 说「找出文中所有注释并解答」。
  </li>
</ol>

---

## 文章目录

<ul class="blog-list">
  <li>
    <span class="title"><a href="blogs/math-primer-for-ml">机器学习快速入门——数学部分</a></span><span class="meta">约 1.6 万字</span>
    <div class="desc">线性代数 + 概率论 + 微积分三合一。读完就能看懂 Transformer、扩散模型、世界模型等博客里的数学符号。</div>
  </li>
  <li>
    <span class="title"><a href="blogs/diffusion-math">Diffusion 模型的数学主线：从马尔可夫链到概率流</a></span><span class="meta">约 1.9 万字</span>
    <div class="desc">34 篇核心论文的数学骨架，从 DDPM 到 Flow Matching 到 SD3，一条线串起扩散模型的完整理论。</div>
  </li>
  <li>
    <span class="title"><a href="blogs/YOLO-Complete-Learning-Guide">YOLO 目标检测算法：一文读懂十年演进 (2015–2026)</a></span><span class="meta">约 3.2 万字</span>
    <div class="desc">从 YOLOv1 到 YOLO26 的完整技术谱系，含损失函数推导、PyTorch 实现和 Tensor 形状追踪。</div>
  </li>
  <li>
    <span class="title"><a href="blogs/dsv4_att">DeepSeek-V4 注意力机制深度解析</a></span><span class="meta">约 0.9 万字</span>
    <div class="desc">从 Q/K/V 直觉出发，逐层拆解 MHA → MQA → GQA → MLA → DSA → CSA 的进化逻辑和矩阵代数。</div>
  </li>
  <li>
    <span class="title"><a href="blogs/mla_modes_deep_dive">MLA 双模式深度专题：MHA 模式 vs MQA 模式</a></span><span class="meta">约 0.3 万字</span>
    <div class="desc">MLA 的 MHA/MQA 双模式代数等价性证明、BF16 精度分析和逐行代码走读。</div>
  </li>
  <li>
    <span class="title"><a href="blogs/world-models-survey">世界模型综述：从像素之梦到表征理解（2018–2026）</a></span><span class="meta">约 3.6 万字</span>
    <div class="desc">24 篇论文覆盖 7 个子领域：JEPA、DreamerV3、Sora、Genie、自动驾驶世界模型和机器人 DayDreamer。</div>
  </li>
  <li>
    <span class="title"><a href="blogs/cot-survey">思维链：从提示工程到推理时训练</a></span><span class="meta">约 1.8 万字</span>
    <div class="desc">14 篇核心论文 + 7 个开源项目，从 few-shot CoT 到 o1/DeepSeek-R1 的完整推理演进图谱。</div>
  </li>
</ul>

