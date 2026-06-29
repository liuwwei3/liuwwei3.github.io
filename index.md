---
layout: default
title: 大伟的AI学习日志
---

<style>
  .ai-steps { counter-reset: step; padding-left: 0; }
  .ai-steps li { counter-increment: step; list-style: none; margin-bottom: 1em; padding-left: 2.5em; position: relative; }
  .ai-steps li::before { content: counter(step); position: absolute; left: 0; top: 0; width: 1.8em; height: 1.8em; background: #0969da; color: #fff; border-radius: 50%; text-align: center; line-height: 1.8em; font-weight: 600; font-size: 0.85em; }
  hr { border: 0; border-top: 1px solid #d0d7de; margin: 2em 0; }
</style>

# 大伟的AI学习日志

---

## 文章目录

- [机器学习快速入门——数学部分](blogs/math-primer-for-ml)（约 1.6 万字）
- [Diffusion 模型的数学主线：从马尔可夫链到概率流](blogs/diffusion-math)（约 1.9 万字）
- [YOLO 目标检测算法：一文读懂十年演进 (2015–2026)](blogs/YOLO-Complete-Learning-Guide)（约 3.2 万字）
- [MLA 双模式深度专题：MHA 模式 vs MQA 模式](blogs/mla_modes_deep_dive)（约 0.3 万字）
- [DeepSeek-V4 注意力机制深度解析](blogs/dsv4_att)（约 0.9 万字）
- [世界模型综述：从像素之梦到表征理解（2018–2026）](blogs/world-models-survey)（约 3.6 万字）
- [思维链：从提示工程到推理时训练](blogs/cot-survey)（约 1.8 万字）

---

## 建议使用 AI Agent 阅读

这个仓库最适合的打开方式是：**用 VS Code + Claude Code 把文章下载到本地，逐段精读。** 你不需要安装 git、不需要懂命令行——全程在 VS Code 里用自然语言对话就能完成。

### 两步开始

<ol class="ai-steps">
  <li>
    <strong>安装 VS Code 并配置 Claude Code</strong><br>
    <strong>①</strong> 下载安装 <a href="https://code.visualstudio.com/">VS Code</a>。<br>
    <strong>②</strong> 在 VS Code 扩展商店（<code>Ctrl+Shift+X</code>）搜索并安装 <a href="https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code">Claude Code</a>（发布者 Anthropic，标识符 <code>anthropic.claude-code</code>）和 <code>Markdown Preview Enhanced</code>（用于漂亮的文章渲染预览）。重启 VS Code。<br>
    
  </li>
  <li>
    <strong>用 Claude Code 一键下载文章</strong><br>
    随便用 VS Code 打开一个空白文件夹，按 <code>Cmd+Shift+P</code>（Mac）或 <code>Ctrl+Shift+P</code>（Windows）打开命令面板，输入 <code>Claude Code: Open</code> 启动对话。在对话框中输入：<br>
    <code>请 clone 仓库 https://github.com/liuwwei3/liuwwei3.github.io.git 到当前文件夹下的 liuwwei3.github.io 子目录</code><br>
    Claude Code 执行完毕后，用 VS Code 打开 <code>liuwwei3.github.io</code> 文件夹。所有文章都在 <code>blogs/</code> 目录下。选中 <code>.md</code> 文件，用 <code>Ctrl+K V</code>（Mac: <code>Cmd+K V</code>）开启 Markdown 预览，边看边向 Claude Code 提问。
    配置完成之后，工作界面如下：<br>
    <img src="vscode-read-config.jpeg" alt="VS Code 工作界面" style="max-width:100%; border-radius:8px; margin-top:0.4em; border:1px solid #d0d7de;">
  </li>
  <li>
    <strong>使用文中注释实现精细问答</strong><br>
    本项目的每篇文章都天然适合 AI 辅助阅读——你可以在阅读时用自然语言向 AI 提问。更进一步，你<span style="background:#fff3cd;padding:0 4px;">可以在任意段落后插入 HTML 注释 <code>&lt;!--你的问题--&gt;</code></span>，然后让 Claude Code 逐条解答。<br>
    例如在不容易理解的部分后面加一行：<code>&lt;!--这里为什么用 log 而不是线性惩罚？--&gt;</code>，然后对 Claude Code 说「找出文中所有注释并解答」。
  </li>
</ol>
