---
layout: default
title: 大语言模型技术梳理：架构、训练、对齐与部署
---

# 大语言模型技术梳理：架构、训练、对齐与部署
[← 回到首页](..)

> **A Technical Survey of Large Language Models: Architecture, Training, Alignment, and Deployment**
>
> 覆盖 2017–2026，四个维度：架构演进 · 预训练 · 对齐 · 推理优化
>
> 撰写于 2026 年 7 月

---

## 符号表

### 基础符号

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $\mathbf{X} \in \mathbb{R}^{n \times d}$ | 输入序列，$n$ 个 token，维度 $d$ | §0.1 |
| $\mathbf{x}_i \in \mathbb{R}^{d}$ | 第 $i$ 个 token 的嵌入向量 | §0.1 |
| $d_{\text{model}}$ | 模型隐藏维度 | §1.2 |
| $h$ | 注意力头数 | §1.3 |
| $d_k = d_{\text{model}} / h$ | 每个注意力头的维度 | §1.3 |
| $V$ | 词表大小 | §0.2 |
| $L$ | Transformer 层数 | §1.4 |

### 架构相关

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $\mathbf{W}^Q, \mathbf{W}^K, \mathbf{W}^V$ | 注意力投影矩阵 | §1.2 |
| $\mathbf{W}^O$ | 多头注意力输出投影矩阵 | §1.3 |
| $\mathbf{q}, \mathbf{k}, \mathbf{v}$ | 单个 token 的 query / key / value 向量 | §1.2 |
| $n_{\text{ctx}}$ | 上下文窗口长度 | §4.1 |
| $m$ / $n$ | token 的位置索引（RoPE 中常用） | §4.4 |

### 训练相关

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $N$ | 模型参数量 | §8.1 |
| $D$ | 训练数据量（token 数） | §8.1 |
| $C$ | 总计算量（FLOPs） | §8.1 |
| $\mathcal{L}$ | 损失函数（通常是交叉熵） | §7.1 |
| $\pi_\theta$ | 策略（当前模型），RLHF 语境中常用 | §12.4 |
| $\pi_{\text{ref}}$ | 参考策略（冻结的旧模型） | §13.1 |

### 推理相关

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $\mathbf{K}_{cache}, \mathbf{V}_{cache}$ | 缓存的 Key / Value 矩阵 | §16.1 |
| $b$ | batch size | §16.2 |
| $s$ | 当前序列长度 | §16.2 |
| $\mathcal{M}$ | GPU 显存总量 | §16.2 |

---

## 主线总览

```
"一个语言模型如何从零开始构建、训练、对齐、并高效部署？"

第一幕：架构 (2017–2025)
│  Attention 机制 → Transformer 诞生 → GPT/LLaMA 规模化 → MoE/MLA 降本增效
│  核心问题：如何设计一个能处理长序列、参数效率高、训练稳定的模型架构？
│
├── 第二幕：预训练 (2018–2025)
│    数据清洗 → 分布式训练 → Scaling Laws → 涌现能力
│    核心问题：多少数据配多少参数？如何高效训练千亿参数模型？
│
├── 第三幕：对齐 (2022–2025)
│    SFT → RLHF → DPO → GRPO → 推理模型
│    核心问题：如何让模型说的话既正确、又有用、又无害？
│
└── 第四幕：推理优化 (2022–2025)
     KV Cache → Flash Attention → 量化 → vLLM → 投机解码
     核心问题：千亿参数模型如何在消费级硬件上跑起来？
```

> **与已有文章的衔接**
>
> 本文梳理 LLM 的四个核心维度。其中，**推理能力（CoT）** 和 **强化学习训练** 在另外两篇文章中做了深度展开：
> - [思维链：从提示工程到推理时训练](../cot-survey) — 覆盖 Chain-of-Thought、ReAct/ToT/GoT、STaR/Quiet-STaR、o1/R1/s1
> - [RL 完全教程](../RL-Tutorial) — 覆盖强化学习从 Q-learning 到 PPO/GRPO 的完整推导
> - [DeepSeek V4 注意力：MLA、NSA、mHC](../dsv4_att) — 覆盖 DeepSeek 系列注意力机制的细节
>
> 本文在这些交叉点上做简洁总结 + 引用，不做完整展开。

---

<!-- TOC generated: 4 parts, 21 chapters, ~120K words -->

## 第零章：语言模型基础

> 本章为后续所有章节提供最低限度的数学语言。如果你熟悉自回归语言模型、tokenization 和 perplexity，可以跳到 §1。

### 0.1 什么是语言模型

一个**语言模型**（Language Model, LM）是一个在 token 序列上定义的概率分布。给定一个由 $n$ 个 token 组成的序列 $\mathbf{w} = (w_1, w_2, ..., w_n)$，语言模型赋予它一个概率 $p(w_1, w_2, ..., w_n)$。

实用中，我们更关心**自回归分解**：利用链式法则将联合概率拆分为条件概率的乘积：

$$p(w_1, w_2, ..., w_n) = \prod_{i=1}^{n} p(w_i \mid w_1, w_2, ..., w_{i-1})$$

这就是**自回归语言模型**的核心——每一个 token 的生成都依赖于之前所有 token。这也就是 GPT 中 "G"（Generative）和 "P"（Pre-trained）的数学基础。

**训练目标**是最大化训练数据中所有序列的对数似然：

$$\mathcal{L}(\theta) = \frac{1}{|\mathcal{D}|} \sum_{\mathbf{w} \in \mathcal{D}} \sum_{i=1}^{|\mathbf{w}|} \log p_\theta(w_i \mid w_{<i})$$

等价于最小化交叉熵损失。用一条具体数据来说：如果模型预测下一个 token 是 "cat" 的概率为 0.8，那这条数据对这一位置的损失贡献就是 $-\log(0.8) \approx 0.223$。如果模型只会猜平均分布（比如词表 50K 个 token，每个概率 0.00002），损失就是 $-\log(1/50000) \approx 10.8$。

### 0.2 Tokenization：把文本变成数字

语言模型处理的不是文字，而是 **token**（词元）。Tokenizer 的工作是将任意文本映射到一个整数序列，同时支持反向映射（detokenization）。

**BPE（Byte Pair Encoding）** 是目前最广泛使用的子词分词算法。GPT-2/3/4、LLaMA 都在使用。其核心思想是迭代地合并最高频的相邻 token 对：

```
算法：Byte Pair Encoding
输入：训练语料，目标词表大小 V
输出：merge rules（合并规则表）

1. 将语料预处理为字节序列（或字符序列）
2. 初始词表 = 所有出现的单字节 + 特殊 token（<eos>, <unk> 等）
3. 循环直到词表大小 = V：
   a. 统计所有相邻 token 对的共现频率
   b. 选择频率最高的一对 (A, B)
   c. 将 "A B" 合并为新 token "AB"，加入词表
   d. 在语料中将所有 "A B" 替换为 "AB"
4. 输出词表和所有 merge rules
```

**编码时**：从字节序列开始，按 merge rules 的顺序反复应用合并，直到无法继续。
**解码时**：每个 token ID 映射回其组成字节，直接拼接即可。

具体实现（Python 伪代码）：

```python
import re, collections

def get_stats(vocab):
    """统计所有相邻 token 对的频率"""
    pairs = collections.defaultdict(int)
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols) - 1):
            pairs[symbols[i], symbols[i+1]] += freq
    return pairs

def merge_vocab(pair, v_in):
    """将 pair 合并为新 token"""
    v_out = {}
    bigram = re.escape(' '.join(pair))
    p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
    for word in v_in:
        w_out = p.sub(''.join(pair), word)
        v_out[w_out] = v_in[word]
    return v_out

# 示例：目标词表大小 10
vocab = {'l o w _': 4, 'l o w e r': 1, 'n e w _': 3, 'w i d e r _': 2}
num_merges = 10
for i in range(num_merges):
    pairs = get_stats(vocab)
    if not pairs:
        break
    best = max(pairs, key=pairs.get)
    vocab = merge_vocab(best, vocab)
    print(f"Merge {i+1}: {best} -> {best[0]}{best[1]}")
```

**Tokenization 对模型行为的影响比你想象的大得多：**

- **数学推理**：数字 "123" 可能被拆成 "12" + "3" 或者 "1" + "23"，甚至 "1" + "2" + "3"。这意味着模型不能通过"看一个数字"来理解其数值大小，而必须学习不同拆分下的算术模式。这就是为什么 LLM 做算术天然比人类困难——人类把数字当作一个整体来感知。

- **多语言公平性**：不同语言在相同 tokenizer 下的"压缩率"差距巨大。英文约 1.3 tokens/word，中文约 2.5 tokens/character（因为中文字符在 BPE 训练语料中出现频率低）。这意味着同样的信息量，中文需要约 2 倍的 token 数，推理成本翻倍。

- **代码**：缩进（空格/tab）、换行符的处理直接影响代码补全质量。如果 tokenizer 把 4 个空格拆成 4 个独立 token，模型理解缩进层级就需要学会"计数"。

常见模型的 tokenizer 对比：

| 模型 | Tokenizer | 词表大小 | 显著特点 |
|------|-----------|---------|---------|
| GPT-2 | BPE | 50,257 | 字节级 BPE 的早期实践 |
| GPT-3/4 | cl100k_base | ~100K | 多语言优化 |
| LLaMA 1/2 | SentencePiece BPE | 32,000 | 仅英文，小词表 |
| LLaMA 3 | tiktoken BPE | 128,000 | 覆盖 30+ 语言 |
| Qwen 2.5 | BPE | 152,064 | 中文做了大量优化 |
| DeepSeek V2/V3 | BBPE | 129,280 | 中英平衡 |
| Gemma | SentencePiece | 256,000 | 超大词表，追求高压缩率 |

### 0.3 嵌入层：从整数到稠密向量

Token ID 是一个整数（如 45231），它本身没有任何语义信息。**嵌入层（Embedding Layer）** 将每个 token ID 映射为一个稠密向量：

$$\mathbf{x}_i = \mathbf{E}[\text{token\_id}_i], \quad \mathbf{E} \in \mathbb{R}^{V \times d_{\text{model}}}$$

本质上就是从一个大矩阵中"查表"：取第 token_id 行。这个矩阵是**可学习的参数**，在训练中和模型其他部分一起优化。

嵌入矩阵的参数量有时是一个意想不到的大头。对于典型的大模型配置：

$$V = 128\text{K}, \quad d_{\text{model}} = 4096 \implies V \times d_{\text{model}} \approx 524\text{M params}$$

这已接近 GPT-2 Large（774M）的 68%。常见优化手段是 **Weight Tying**——共享输入嵌入和输出投影的权重矩阵，将参数量减半。

### 0.4 自回归解码：从概率到文本

训练好的语言模型生成文本的过程是**逐个 token 地采样**。每一步，模型输入当前序列，输出词表大小的概率分布，按一定策略选取下一个 token，拼接到序列后，重复。

**Greedy Decoding（贪心解码）**：
$$w_t = \arg\max_w p_\theta(w \mid w_{<t})$$

每步选概率最大的。问题是生成内容高度重复——一旦进入一个循环，贪心解码永远出不来。

**Temperature Sampling（温度采样）**：在 softmax 前对 logits 除以温度参数 $\tau$：

$$p(w_i) = \frac{\exp(z_i / \tau)}{\sum_j \exp(z_j / \tau)}$$

- $\tau \to 0$：趋近于 argmax（确定论输出）
- $\tau = 1$：保留原始概率分布
- $\tau > 1$：分布变平滑，罕见 token 概率增大
- $\tau \to \infty$：趋近于均匀分布（完全随机）

典型的 $\tau$ 设置：代码生成 0.2-0.4（需要确定论），一般对话 0.7-0.8，创意写作 0.9-1.1。

**Top-k Sampling**：只在概率最高的 $k$ 个 token 中重新归一化并采样。截断概率分布的长尾。

**Top-p（Nucleus）Sampling**：选取累积概率刚好超过 $p$ 的最小 token 集合。相比 Top-k，它能动态适应分布的尖锐程度——分布尖锐时选少数几个 token，平坦时选更多 token。

实践中组合使用，如 $\tau = 0.8, p = 0.95, k = 50$。

### 0.5 Perplexity：语言模型的成绩单

**Perplexity（困惑度，PPL）** 是评估语言模型的核心指标，定义为：

$$\text{PPL} = \exp\left(-\frac{1}{N} \sum_{i=1}^{N} \log p_\theta(w_i \mid w_{<i})\right) = \exp(\text{交叉熵损失})$$

一个非常有用的直觉：**PPL 可以理解为模型在预测下一个 token 时的"平均分支数"**。如果每个位置模型都面对 $K$ 个等可能的 token（每种概率 $1/K$），则：

$$-\sum_i \frac{1}{K} \log \frac{1}{K} = \log K \implies \text{PPL} = \exp(\log K) = K$$

因此：
- PPL = 1 → 完美预测（只有 1 个 token 概率为 1，其余为 0）
- PPL = 10 → 模型平均在 10 个候选 token 中犹豫
- PPL = 100 → 模型非常不确定

实际数字：LLaMA 7B 在 WikiText-2 上 PPL 约 5-6，GPT-3 约 20（zero-shot），未经训练的模型 PPL 约等于词表大小（50K+）。

**但要注意**：PPL 衡量的是"语言建模能力"，不等于"有用性"。一个背下整个 WikiText 测试集的模型 PPL 极低但毫无泛化能力。

---

### 本文的阅读约定

- **数学公式**：行内公式用 `$...$`，独立公式用 `$$...$$`。每个首次出现的符号都有定义。
- **代码块**：优先使用 Python 伪代码，强调可理解性而非可运行性。
- **信息框**：`>` 前缀的块引用用于强调关键洞察和常见误解。
- **引用**：指向本仓库其他文章的链接表示"此处有更详细的展开，本文仅做总结"。
- **章末标记**：每个章节末尾有 `---` 分隔线，方便定位。

---

## 第一幕：架构演进 — 从 Attention 到 GPT-4

---

## 第一章：Transformer — 一切开始的地方

> **核心论文**：Vaswani et al., *Attention Is All You Need* (NeurIPS 2017)
>
> 本章的目标不是面面俱到地复述论文，而是从"为什么这样设计"的角度，带你一步步理解 Transformer 的每一个设计选择。

### 1.1 为什么需要 Attention？

在 Transformer 之前，序列建模的主导范式是 RNN/LSTM。以一个典型的 seq2seq 机器翻译模型为例：

$$\mathbf{h}_t = \text{LSTM}(\mathbf{x}_t, \mathbf{h}_{t-1})$$

**RNN 的三大痛点**：

1. **顺序依赖**：$\mathbf{h}_t$ 必须等 $\mathbf{h}_{t-1}$ 算完。这意味着一个 100 词的句子需要 100 个串行计算步，无法并行。
2. **长距离遗忘**：第 1 个词的信息要经过 99 次非线性变换才能到达第 100 个位置。梯度要么消失要么爆炸。
3. **固定大小的瓶颈**：源语言的全部信息被压缩进最后一个隐藏状态，然后解码器必须从这个固定向量中恢复所有细节。

Attention 的洞见简单而深刻：**与其把信息压缩并传递，不如让解码器的每一步都能直接"看见"编码器的所有位置**。

### 1.2 Scaled Dot-Product Attention

Attention 的核心是一个**可微的键值查找**操作。把 Attention 类比为数据库查询：

| 数据库 | Attention |
|--------|-----------|
| Query（查询） | $\mathbf{q}$：当前 token "想要什么信息" |
| Key（键） | $\mathbf{k}$：每个 token "拥有什么信息" |
| Value（值） | $\mathbf{v}$：每个 token "传递什么信息" |

计算流程：

$$\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{d_k}}\right) \mathbf{V}$$

逐步骤拆解（假设单个 query $\mathbf{q} \in \mathbb{R}^{d_k}$）：

1. **打分**：用 query 和每个 key 做内积，得到相似度分数
   $$s_i = \mathbf{q} \cdot \mathbf{k}_i, \quad i = 1, ..., n$$

2. **缩放**：除以 $\sqrt{d_k}$。为什么是 $\sqrt{d_k}$？假设 $\mathbf{q}$ 和 $\mathbf{k}$ 的各分量独立，均值为 0，方差为 1，那么内积 $\mathbf{q} \cdot \mathbf{k}$ 的方差是 $d_k$。不缩放的话，$d_k$ 较大时 softmax 会极度尖锐（梯度接近 0）：
   $$\text{Var}(\mathbf{q} \cdot \mathbf{k}) = \sum_{j=1}^{d_k} \text{Var}(q_j \cdot k_j) = \sum_{j=1}^{d_k} 1 = d_k$$

3. **归一化**：softmax 将分数转换为概率分布（注意力权重）
   $$\alpha_i = \frac{\exp(s_i / \sqrt{d_k})}{\sum_j \exp(s_j / \sqrt{d_k})}$$

4. **聚合**：用注意力权重对 values 加权求和
   $$\mathbf{o} = \sum_{i=1}^{n} \alpha_i \mathbf{v}_i$$

写成矩阵形式（同时处理 $n$ 个 query）：

$$\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{d_k}}\right) \mathbf{V}$$

其中 $\mathbf{Q} \in \mathbb{R}^{n \times d_k}$，$\mathbf{K} \in \mathbb{R}^{n \times d_k}$，$\mathbf{V} \in \mathbb{R}^{n \times d_v}$。

**复杂度分析**：
- $\mathbf{Q}\mathbf{K}^T$：$n \times d_k \times n = O(n^2 d_k)$ —— 序列长度的平方
- Softmax + 加权：$O(n^2 d_v)$
- **总体复杂度**：$O(n^2 d_k)$，其中 $n^2$ 是瓶颈——这也是后续所有优化的核心目标

注意力权重矩阵 $\mathbf{A} = \text{softmax}(\mathbf{Q}\mathbf{K}^T / \sqrt{d_k})$ 的大小是 $n \times n$。对于 2K 长度的序列，这个矩阵是 2000 × 2000 = 4M 个元素；对于 128K 长度，是 16B 个元素（= 约 32GB，float16）。

### 1.3 多头注意力（Multi-Head Attention）

单头 Attention 的问题：一个 query 只能表达一种"关注模式"。但是，一个词可能需要同时关注"主语是谁"、"时态是什么"、"修饰语是什么"等多种信息。

**多头注意力的解决方案**：并行运行 $h$ 个独立的注意力，每个"头"有自己的 $\mathbf{W}^Q, \mathbf{W}^K, \mathbf{W}^V$ 投影：

$$\text{head}_i = \text{Attention}(\mathbf{X}\mathbf{W}_i^Q, \mathbf{X}\mathbf{W}_i^K, \mathbf{X}\mathbf{W}_i^V)$$

$$\text{MultiHead}(\mathbf{X}) = \text{Concat}(\text{head}_1, ..., \text{head}_h) \mathbf{W}^O$$

其中：
- $\mathbf{W}_i^Q \in \mathbb{R}^{d_{\text{model}} \times d_k}$，$\mathbf{W}_i^K \in \mathbb{R}^{d_{\text{model}} \times d_k}$，$\mathbf{W}_i^V \in \mathbb{R}^{d_{\text{model}} \times d_v}$
- $\mathbf{W}^O \in \mathbb{R}^{h d_v \times d_{\text{model}}}$
- 标准设置：$d_k = d_v = d_{\text{model}} / h$

**为什么多头有效？** 不同的头自然地学会关注不同的模式。可视化学者（如 Clark et al. 2019, BERTology）发现，有些头关注相邻位置（局部语法），有些头关注远距离依赖（指代消解），还有些头关注特定位置（如 [SEP] token）。

Vaswani 原论文设置：$h = 8, d_{\text{model}} = 512, d_k = d_v = 64$。

现代大模型的典型配置：$h = 32, d_{\text{model}} = 4096, d_k = d_v = 128$（LLaMA-7B）。

### 1.4 Transformer Block：不只是 Attention

单个 Transformer 层由两个子层组成：

```
输入 X ∈ R^{n × d_model}
    │
    ├→ Multi-Head Attention(Q=X, K=X, V=X)   # Self-Attention
    │   └→ + X                                # 残差连接 (Residual)
    │   └→ LayerNorm                          # 层归一化
    │   =: H                                  # 隐藏状态
    │
    ├→ FFN(H) = ReLU(H·W1 + b1)·W2 + b2     # 前馈网络
    │   └→ + H                                # 残差连接
    │   └→ LayerNorm                          # 层归一化
    │
    └→ 输出：下一层的输入
```

三个关键设计选择：

**（1）残差连接（Residual Connection）**：将子层的输入加到输出上。

$$\mathbf{H}_{\text{out}} = \text{LayerNorm}(\mathbf{X} + \text{Sublayer}(\mathbf{X}))$$

不只是为了梯度流动——这是训练深层网络的必要技巧（参见 ResNet, He 2016）——残差连接对 Transformer 还有一个更本质的作用：**它使网络可以"选择不关注"**。如果 Attention 层输出的权重全为 0，残差连接保证了原始信息至少完整通过。

**（2）Layer Normalization**：在特征维度上归一化。

$$\text{LayerNorm}(\mathbf{x}) = \gamma \odot \frac{\mathbf{x} - \mu}{\sqrt{\sigma^2 + \epsilon}} + \beta$$

其中 $\mu$ 和 $\sigma^2$ 在 $d_{\text{model}}$ 维度上计算。与 BatchNorm（在 batch 维度归一化）不同，LayerNorm 对 batch size 不敏感，且推理时不需要重新计算统计量。

Vaswani 原论文使用 **Post-LayerNorm**（残差之后做 Norm），后来的实践（GPT-2+）普遍采用 **Pre-LayerNorm**（残差之前做 Norm），因为 Pre-LN 训练更稳定，不需要特殊的学习率 warmup。

**（3）Position-wise Feed-Forward Network (FFN)**：

$$\text{FFN}(\mathbf{x}) = \max(0, \mathbf{x}\mathbf{W}_1 + \mathbf{b}_1)\mathbf{W}_2 + \mathbf{b}_2$$

其中 $\mathbf{W}_1 \in \mathbb{R}^{d_{\text{model}} \times d_{ff}}$，$\mathbf{W}_2 \in \mathbb{R}^{d_{ff} \times d_{\text{model}}}$。原论文 $d_{ff} = 2048$（4× $d_{\text{model}}$）。

这个设计很朴素但容量巨大：FFN 层的参数量 = $2 \times d_{\text{model}} \times d_{ff} \approx 8 \times d_{\text{model}}^2$，占据了 Transformer 约 2/3 的参数。它本质上是模型"存储知识"的地方——注意力负责在 token 之间传递信息，FFN 负责处理和转换信息。

现代变体 **SwiGLU**（LLaMA 使用）将 FFN 替换为：

$$\text{SwiGLU}(\mathbf{x}) = (\text{SiLU}(\mathbf{x}\mathbf{W}_1) \odot \mathbf{x}\mathbf{W}_2) \mathbf{W}_3$$

其中 $\text{SiLU}(x) = x \cdot \sigma(x)$（也叫 Swish）。门控机制使 FFN 可以选择性地激活，实验表明在相同参数量下性能优于标准 FFN。

### 1.5 位置编码：序的难题

Self-Attention 有一个根本缺陷：它是**置换等变的**（permutation equivariant）。如果你打乱输入 token 的顺序，在 softmax 求和后每个位置的输出只是跟随输入被重新排列——模型完全不知道顺序信息。

**Sinusoidal Position Encoding**（Vaswani 原论文方案）：

$$PE_{(pos, 2i)} = \sin(pos / 10000^{2i/d_{\text{model}}})$$
$$PE_{(pos, 2i+1)} = \cos(pos / 10000^{2i/d_{\text{model}}})$$

其中 $pos$ 是位置索引，$i$ 是维度索引。不同频率的正弦波形成了位置的"指纹"——每个维度对应一种不同的波长（从 $2\pi$ 到 $10000 \cdot 2\pi$）。

这个设计有一个优雅的性质：位置 $pos + k$ 的编码可以通过位置 $pos$ 的编码线性变换得到（因为正弦函数的加法公式）。但这并不意味着模型实际上学会了利用这个性质。

> 位置编码是 Transformer 设计中争议最多的部分之一，我们将在第四章做全面对比（sinusoidal → learned → RoPE → ALiBi → 长上下文扩展）。目前只需要记住：**Self-Attention 天生不知道顺序，需要额外注入位置信息**。

### 1.6 完整架构的参数统计

以 Vaswani 原论文的 Transformer-base 为例：$d_{\text{model}}=512, h=8, d_k=d_v=64, d_{ff}=2048, L=6$（编码器）+ 6（解码器）。

| 组件 | 参数量 | 占比 |
|------|--------|------|
| Embedding（共享） | $V \times 512$ | ~19M（$V \approx 37K$） |
| 每层 Self-Attention | $4 \times 512 \times 512$ | 1.05M |
| 每层 FFN | $2 \times 512 \times 2048$ | 2.10M |
| 每层 Output Proj（decoder cross-attn） | 额外 ~1M |
| **总计（6 enc + 6 dec）** | — | **~65M** |

现代 LLM 的 Transformer 几乎都是 **decoder-only**（GPT 路线）：丢掉编码器，用因果自注意力（causal self-attention）——每个 token 只能看到它之前的 token，通过一个下三角 mask 实现。

### 1.7 因果自注意力

Decoder-only Transformer 的核心修改：在 softmax 之前对 $\mathbf{Q}\mathbf{K}^T$ 矩阵施加一个**下三角 mask**（将所有 $i < j$ 的位置设为 $-\infty$），使得 softmax 后这些位置的权重变为 0：

$$(\text{CausalMask})_{ij} = \begin{cases} 0 & i \geq j \\ -\infty & i < j \end{cases}$$

$$\text{CausalAttention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{d_k}} + \text{CausalMask}\right) \mathbf{V}$$

这个简单的修改将 Encoder 的双向 Attention 变成了自回归（从左到右）的生成式 Attention。这也意味着：

- 位置 $i$ 的计算结果只依赖于位置 $1, ..., i$
- 生成时每步只需要计算新 token 的 query 与所有历史 key 的注意力——这就是 KV Cache 的数学基础
- 训练时可以并行处理整个序列（teacher forcing）

### 1.8 小结

Transformer 的成功源于三个设计原则的恰到好处组合：

1. **自注意力**：O(1) 的路径长度（任意两个 token 之间只需 1 步）
2. **多头机制**：多个并行的关注模式
3. **残差连接 + LayerNorm**：使深层堆叠稳定可行

再加上**高度并行**（训练效率远超 RNN），Transformer 成为 LLM 时代的标准配方就是必然。

> 下一章我们看 GPT 系列如何将 Transformer 从翻译任务中解放出来，并逐步证明"规模本身就是一种算法"。

---

## 第二章：GPT 系列 — 规模化之路

> **核心论文**：Radford et al., *Improving Language Understanding by Generative Pre-Training* (2018); Radford et al., *Language Models are Unsupervised Multitask Learners* (2019); Brown et al., *Language Models are Few-Shot Learners* (2020); OpenAI, *GPT-4 Technical Report* (2023)

### 2.1 GPT-1 (2018)：生成式预训练 + 判别式微调

GPT-1 的根本贡献不是架构创新（它用的就是 12 层 decoder-only Transformer），而是提出了一个**范式**：

```
阶段 1：无监督预训练（大规模无标注文本）
    ↓  学到一个"通才"语言模型
阶段 2：有监督微调（特定任务标注数据）
    ↓  调整模型适应该任务
```

预训练目标（标准的语言模型损失）：

$$\mathcal{L}_{\text{pretrain}} = -\sum_i \log p_\theta(w_i \mid w_{i-k}, ..., w_{i-1})$$

微调时，在最后一个 token 的隐藏状态上接一个线性分类器：

$$\mathcal{L}_{\text{finetune}} = -\log p(y \mid \mathbf{h}_{\text{last}})$$

关键发现：预训练已经学到了大量知识，微调只需要少量数据即可达到很好的效果。这个洞察在今天看来理所当然，但在 2018 年之前，NLP 的主流是做特定任务专用架构（LSTM + Attention 用于翻译，CNN 用于分类，等等）。

**GPT-1 的局限**：微调需要标注数据（虽然不多），且模型只学到了语言知识而非通用能力。

### 2.2 GPT-2 (2019)：Zero-shot 转移

GPT-2 做了一个大胆的主张：**语言模型本身就是多任务学习器**。核心论点——
任何 NLP 任务都可以被框架化为"给定上下文，预测下一个 token"：
- 翻译 → "English: Hello, French: _____"
- 摘要 → "Article: ... TL;DR: _____"
- 问答 → "Q: ... A: _____"

因此，一个足够大的语言模型，在足够多的文本上训练，**不需要任何微调**就能执行各种任务——这就是 **zero-shot transfer**。

GPT-2 的架构改动很小但很重要：
- LayerNorm 移到 Attention 和 FFN **之前**（Pre-LN）
- 最终输出前加一层额外的 LayerNorm
- 残差权重按 $1/\sqrt{L}$ 缩放

最大版本 GPT-2 XL：$L=48, d_{\text{model}}=1600, h=25, d_{ff}=6400$，总参数量 1.5B。

GPT-2 开启了两个趋势：(1) 模型的 zero-shot 能力强于预期，(2) 数据质量比数据量更关键。它使用的 WebText 数据集经过精心筛选（Reddit 上至少获得 3 karma 的外部链接），仅 40GB 却比 Common Crawl 效果好得多。

### 2.3 GPT-3 (2020)：涌现的临界点

GPT-3 将参数量从 1.5B 提升到 175B（约 100×），并且有一个明确的核心假设：**规模本身就是一种算法**。不需要改架构、不需要加模块，只需要把参数量和训练数据做大。

175B GPT-3 的架构配置：

| 超参数 | 值 |
|--------|-----|
| $d_{\text{model}}$ | 12288 |
| $h$（头数） | 96 |
| $d_k = d_v$ | 128 |
| $d_{ff}$ | 49152（4×） |
| $L$（层数） | 96 |
| 上下文长度 | 2048 |
| 总参数量（不含嵌入） | 175B |

GPT-3 引入了 **In-Context Learning（上下文学习）** 的概念——模型通过 prompt 中的几个示例就能"学会"任务，而**不需要任何梯度更新**。这催生了 Few-shot / One-shot / Zero-shot 三种范式。

关键实验发现：
- 随着模型变大，**所有任务上的性能稳定提升**（包括翻译、QA、常识推理等）
- 某些能力如算术推理、代码生成在 13B 之前几乎不存在，在 175B 时突然涌现
- Few-shot 性能与模型大小的关系近似幂律

**GPT-3 的开销**：训练约需要 3.14 × 10^23 FLOPs，在 V100 GPU 上训练估计需要 355 GPU-years。推理成本同样惊人——一次 175B 的前向传播约需 350 GB 显存（float16 下仅参数就 350GB）。

### 2.4 GPT-4 (2023)：多模态与 Mixture of Experts

GPT-4 的技术报告以"不透明"著称——没有架构细节，没有训练数据，没有参数量。但从各种来源（包括泄露和逆向工程）可以拼凑出一些合理推断：

- **MoE 架构**：推测使用 8-16 个专家，总参数量可能在 ~1.7T，每次前向传播激活约 ~280B
- **多模态**：支持图像输入（视觉编码器 + 投影）
- **长上下文**：初始 8K，后扩展到 32K 和 128K
- **训练数据**：包含大量 code 数据（可能 > 20%），这被认为是其推理能力的关键

GPT-4 的最大哲学意义是：将"做研究"和"做产品"彻底分离。OpenAI 选择了对架构保密，而竞争对手（LLaMA、DeepSeek）选择了开源和透明。这两种路线的碰撞塑造了整个 2023-2026 年的 LLM 生态。

### 2.5 架构的工程化演进

从 GPT-1 到 GPT-4，架构层面的改进虽然不像 Transformer 的发明那样革命性，但累积效果很大：

| 改进 | 引入时间 | 效果 |
|------|---------|------|
| Pre-LayerNorm | GPT-2 | 训练稳定性大幅提升 |
| 残差权重缩放 | GPT-2 | 深层网络梯度流动更好 |
| 可学习位置编码 | GPT-3 | 比 sinusoidal 灵活 |
| RoPE | LLaMA / GPT-NeoX | 相对位置 + 长度外推 |
| SwiGLU FFN | LLaMA / PaLM | 等参数量下性能提升 |
| GQA / MQA | LLaMA 2 / PaLM | KV Cache 大幅缩减 |
| MoE | GPT-4 / Mixtral | 参数量 ↑ 但推理成本可控 |

**Pre-Norm vs Post-Norm** 的差异非常重要。考虑一个 Transformer 层的输出：

Post-Norm（原始论文）：$\mathbf{h}_{l+1} = \text{LN}(\mathbf{h}_l + \text{Sublayer}(\mathbf{h}_l))$
Pre-Norm（现代实践）：$\mathbf{h}_{l+1} = \mathbf{h}_l + \text{Sublayer}(\text{LN}(\mathbf{h}_l))$

Pre-Norm 中 LayerNorm 在残差分支**内部**——梯度可以通过残差连接"干净"地流回去，不受 LayerNorm 的梯度缩放影响。这使得 Pre-Norm 可以用简单的线性学习率 warmup（而不需要原始论文中精心设计的 warmup 策略）。

### 2.6 从 GPT 到 ChatGPT

ChatGPT 的技术架构与 GPT-3.5 几乎相同，区别在于**训练后的对齐过程**。这个过程的细节我们将在第三幕展开，但这里先给出一个高层视角：

1. **SFT**（Supervised Fine-Tuning）：用人工编写的理想对话来微调模型。让模型学会"对话格式"。
2. **RM**（Reward Model）：让人工标注员比较两个模型回复哪个更好，训练一个"偏好预测器"。
3. **PPO**（Proximal Policy Optimization）：用 RM 作为奖励信号，用强化学习进一步优化模型。

ChatGPT 的成功揭示了一个重要事实：**基础模型的能力是一切的前提，但对齐决定了用户是否愿意使用它**。一个强但不听话的模型和一个听话但弱的模型，用户都会弃用。

---

## 第三章：注意力机制进化 — 为推理效率而战

> 从 MHA 到 MQA、GQA、MLA 再到 NSA——注意力机制的每一次进化，本质上都是在回答同一个问题：**如何在保持注意力质量的前提下减少 KV Cache？**

### 3.1 问题的根源：KV Cache 的显存代价

回忆因果自注意力的计算方式。在推理时（自回归生成），每生成一个新 token，都需要将它作为 query 去和**所有历史** key/value 做注意力。如果不做缓存，每个解码步都要重新计算所有历史的 K 和 V，使得推理复杂度达到 $O(n^3 d)$。

**KV Cache 的核心思想**：将每个位置的 K 和 V 计算一次后存起来，后续步骤直接读取。

这引出了一个巨大的显存问题。KV Cache 的存储量：

$$\text{KV Cache Size} = 2 \times L \times h \times d_k \times n_{\text{tokens}} \times \text{bytes\_per\_elem}$$

对于 LLaMA-7B（$L=32, h=32, d_k=128$），生成 2048 个 token：
$$2 \times 32 \times 32 \times 128 \times 2048 \times 2 \text{ bytes} \approx 1 \text{ GB}$$

对于 GPT-3-175B（$L=96, h=96, d_k=128$），生成 2048 个 token：
$$2 \times 96 \times 96 \times 128 \times 2048 \times 2\text{ bytes} \approx 9.2 \text{ GB}$$

而且注意：随着序列变长，KV Cache **线性增长**。对于 1M 上下文，同样 175B 的模型需要 ~4.5 TB 的 KV Cache——完全不可承受。

### 3.2 Multi-Query Attention (MQA, 2019)：最激进的压缩

> Shazeer, *Fast Transformer Decoding: One Write-Head Is All You Need* (2019)

MQA 的核心思想简单粗暴：**所有注意力头共享同一对 K 和 V**。

- 原始 MHA：$h$ 个独立的 $(\mathbf{K}_i, \mathbf{V}_i)$，$i = 1, ..., h$
- MQA：所有 $h$ 个 query 头共享 1 对 $(\mathbf{K}, \mathbf{V})$

$$\text{head}_i = \text{Attention}(\mathbf{Q}_i, \mathbf{K}_{\text{shared}}, \mathbf{V}_{\text{shared}})$$

效果：KV Cache 减少到原来的 $1/h$（例如 $h=32$ 时减少 97%）。代价是注意力质量的下降——不同头无法关注不同模式，因为它们共享相同的 key/value 表示。

### 3.3 Grouped-Query Attention (GQA, 2023)：实用主义的折中

> Ainslie et al., *GQA: Training Generalized Multi-Query Transformers from Multi-Head Checkpoints* (2023)

GQA 是 MHA 和 MQA 之间的平衡：将 $h$ 个 query 头分成 $g$ 组，每组共享一对 $(\mathbf{K}, \mathbf{V})$。

$$\text{head}_i = \text{Attention}(\mathbf{Q}_i, \mathbf{K}_{\text{group}(i)}, \mathbf{V}_{\text{group}(i)})$$

- $g = h$ → 标准 MHA
- $g = 1$ → MQA
- $g = 4$ → LLaMA 70B 的实际选择（KV Cache 减少到 1/4）

GQA 的另一个重要贡献是 **uptraining** 技术：从一个已训练好的 MHA 模型出发，将多个 K/V 头平均化为 GQA 的组，然后继续训练 ~5% 的原始训练量。这避免了从零训练 MQA/GQA 模型的巨大成本。

LLaMA 2 的实践：

| 模型大小 | GQA 组数 | KV Cache 减少 |
|---------|---------|--------------|
| 7B / 13B | $g = h$（标准 MHA）| 1× |
| 34B | $g = 8$ | 4× |
| 70B | $g = 8$ | 8× |

### 3.4 Multi-Head Latent Attention (MLA, 2024)：低秩压缩的艺术

> DeepSeek, *DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model* (2024)

MLA 的视角和 MQA/GQA 完全不同。MQA/GQA 的思路是"让所有头共享 KV"，MLA 的思路是"**把 KV 压缩到低维空间，推理时解压缩**"。

这是一个借鉴了信号处理思想的设计：自然信号（包括语言）的内在维度远低于其表示维度，因此高维 KV 表示中存在大量冗余，可以通过降维来压缩。

**核心机制——KV 联合压缩**：

$$\mathbf{c}_t^{KV} = \mathbf{W}^{DKV} \mathbf{h}_t \in \mathbb{R}^{d_c}$$

其中：
- $\mathbf{h}_t \in \mathbb{R}^{d_{\text{model}}}$ 是第 $t$ 个 token 的隐藏状态
- $\mathbf{W}^{DKV} \in \mathbb{R}^{d_c \times d_{\text{model}}}$ 是一个下投影矩阵（$d_c \ll d_{\text{model}} \cdot h$）
- $\mathbf{c}_t^{KV}$ 是压缩后的潜在表示，存储在 KV Cache 中

**推理时解压缩**：

$$\mathbf{k}_t^C = \mathbf{W}^{UK} \mathbf{c}_t^{KV}, \quad \mathbf{v}_t^C = \mathbf{W}^{UV} \mathbf{c}_t^{KV}$$

其中 $\mathbf{W}^{UK}, \mathbf{W}^{UV} \in \mathbb{R}^{d_{\text{model}} \times d_c}$ 是上投影矩阵，将压缩表示恢复到完整的 key/value。

**为什么叫"Latent Attention"？** 因为 KV 不再以显式形式存储，而是以"潜在码"的形式存储。注意力计算时，先将码解压，再做标准注意力。

以 DeepSeek-V3 的真实数字来说明压缩效果：

$$\text{标准 MHA KV Cache} = 2 \times L \times h \times d_k = 2 \times 60 \times 128 \times 128 = 1,966,080 \text{ dims/token}$$

$$\text{MLA KV Cache} = 2 \times L \times d_c = 2 \times 60 \times 512 = 61,440 \text{ dims/token}$$

$$\text{压缩比} = 1,966,080 / 61,440 = 32\times$$

这是质变：1M 上下文下，MLA 的 KV Cache 从 ~220GB 降到 ~7GB。

> MLA 的更详细分析（包括 RoPE 解耦、MHA/MQA 双模式切换、矩阵吸收等工程细节）详见 [DeepSeek V4 注意力机制深度解析](../dsv4_att)。这里只给出核心思想——理解低秩压缩的直觉就足够了。

### 3.5 NSA (Native Sparse Attention, 2025)：动态稀疏

> DeepSeek, *Native Sparse Attention: Hardware-Aligned and Natively Trainable* (2025)

NSA 解决的是 MLA 没有触及的另一个问题：Attention 的 $O(n^2)$ 计算复杂度。MLA 压缩了 KV Cache 的**存储**，但没有改变注意力计算的**次数**。

NSA 的核心思路：不是每个 token 都需要关注所有历史 token。大部分注意力权重集中在少数关键 token 上。因此，与其对每个 query 计算 $n$ 次注意力，不如先**动态选择**最相关的 $k$ 个 token（$k \ll n$），然后只在选中的 token 上计算注意力。

**Lightning Indexer** 是 NSA 的选择机制：

$$I_{t,s} = \sum_j w_{t,j}^I \cdot \text{ReLU}(\mathbf{q}_{t,j}^I \cdot \mathbf{k}_s^I)$$

- 对每个 query 位置 $t$，计算它与所有 key 的初级得分
- 使用 ReLU 而非 Softmax 来产生稀疏的选择（Softmax 总是稠密的）
- 用 FLOPs 极少（约标准注意力计算的 2%）

选择 Top-$k$ 后，只在选中 token 上做完整注意力。效果：128K 上下文下，DSA 的速度是标准注意力的 2-3 倍。

NSA 是 DSA（DeepSeek Sparse Attention）的改进版，使稀疏注意力能够原生支持训练。DSA 需要用两阶段训练（dense warmup → sparse finetune），而 NSA 从零开始就能训练稀疏注意力。

### 3.6 注意力进化路线图

```
MHA (2017):   每个头独立 KV，O(n²d) 计算 + O(L·h·d_k·n) 缓存
    │
    ├→ MQA (2019): 所有头共享 KV → 缓存 = 1/h
    │
    ├→ GQA (2023): 分组共享 KV → 缓存 = g/h，质量与效率的平衡点
    │
    ├→ MLA (2024): 低秩压缩 KV → 缓存 ~ 1/30，且保持多头表达能力
    │   └→ 解决了存储问题，但没解决 O(n²) 计算问题
    │
    └→ NSA/DSA (2025): 动态稀疏 + 硬件感知 → 连计算都省了
        └→ 与 MLA 互补：MLA 省存储，NSA 省计算
```

> 位置编码的详细演化（sinusoidal → learned → RoPE → ALiBi → 长上下文扩展）和 MoE 架构将在第四和第五章展开。

---

## 第四章：位置编码的演化

> 位置编码是 Transformer 中最"不起眼"但也最"折腾"的组件。不起眼是因为它只有几行代码；折腾是因为从 sinusoidal 到 RoPE 到 ALiBi 再到长上下文扩展，社区用了整整 8 年才把它搞明白。

### 4.1 问题的本质

Self-Attention 是完全**置换等变的**（permutation equivariant）：如果你把输入序列 $(x_1, x_2, x_3)$ 重排为 $(x_3, x_1, x_2)$，每个位置的输出也会跟随重排，但输出的**内容**完全一样。这意味着一句话 "狗咬了人" 和 "人咬了狗" 在 Self-Attention 眼中没有任何区别。

位置编码的任务就是把**顺序信息**以一种模型可以理解的方式注入到 Self-Attention 中。

$$p(w_1, ..., w_n) = \prod_i p(w_i \mid w_{<i})$$

在自回归模型中，causal mask 已经保证了位置 $i$ 只能看到位置 $<i$，但这只是"能看到哪些位置"的约束，并不是"每个位置是什么意思"的语义。位置编码负责后者。

### 4.2 Sinusoidal（Vaswani 2017）：绝对位置的指纹

原始 Transformer 使用固定的正弦函数作为位置编码：

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$
$$PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

其中 $pos$ 是位置，$i$ 是维度索引（$i = 0, 1, ..., d_{\text{model}}/2 - 1$）。

这个设计的关键性质：

- **每个位置有唯一指纹**：不同位置产生不同的向量，因为正弦函数的周期性在不同维度上以不同的频率展开
- **不同维度捕捉不同尺度的位置信息**：$i$ 越小（波长越短），该维度对局部位置变化越敏感；$i$ 越大（波长越长），该维度对远距离位置变化越敏感
- **相对位置的可线性表示性**：对于任意固定偏移 $k$，$PE(pos+k)$ 可以通过 $PE(pos)$ 的线性变换得到。这是因为 $\sin(pos+k) = \sin(pos)\cos(k) + \cos(pos)\sin(k)$

然而，这个性质在实践中几乎没有被模型利用。大多数模型学会的是直接使用绝对位置信息，而非相对位置。这也是后来 RoPE 出现的原因——与其希望模型学会相对位置，不如直接把相对位置编码进注意力计算。

### 4.3 可学习位置编码（GPT-3 路线）

另一种方案是直接把位置编码当作可学习参数：

```python
self.position_embedding = nn.Embedding(max_seq_len, d_model)
```

优缺点鲜明：
- **优点**：简单，模型可以自由学习任意位置表示
- **致命缺点**：无法外推。模型在训练时只见过位置 0-2047，推理时位置 2048 的嵌入是随机初始化的（或未定义的）

GPT-3 使用了可学习位置编码，这直接限制了它的最大序列长度。后来出现了各种插值方法（如 PI、NTK-aware），通过将新位置映射到已训练位置的"附近"来扩展上下文，但这些都是在 RoPE 上发展的。

### 4.4 RoPE（Su 2023）：相对位置的优雅方案

> Su et al., *RoFormer: Enhanced Transformer with Rotary Position Embedding* (2021, 最终版 2023)

RoPE 的核心思想可以这样理解：**通过对 Q 和 K 向量施加旋转来编码位置，使得旋转角度依赖于绝对位置，而 Q 和 K 的内积只依赖于相对位置**。

**数学推导**：

我们的目标是找到一个函数 $f$，使得：
$$\langle f(\mathbf{x}_m, m), f(\mathbf{x}_n, n) \rangle = g(\mathbf{x}_m, \mathbf{x}_n, m-n)$$

其中 $\mathbf{x}_m$ 是位置 $m$ 的 token 嵌入，$f$ 是带位置的变换。这个等式说的是：Q 和 K 的内积只依赖于它们内容的相似度（$g$ 的一部分）和它们的**相对位置** $m-n$，而不是绝对位置 $m$ 或 $n$。

在 2D 情况下，一个自然的解是用复数乘法——乘以一个单位旋转因子：

$$f(\mathbf{x}_m, m) = \mathbf{x}_m \cdot e^{i m \theta}$$

代入内积：
$$\langle f(\mathbf{x}_m, m), f(\mathbf{x}_n, n) \rangle = (\mathbf{x}_m e^{i m \theta}) \cdot (\overline{\mathbf{x}_n e^{i n \theta}}) = \mathbf{x}_m \overline{\mathbf{x}_n} e^{i(m-n)\theta}$$

这个内积只依赖于 $m-n$！扩展到 $d$ 维空间——将向量拆分为 $d/2$ 个 2D 对，每个对使用不同的旋转频率 $\theta_i$：

$$\Theta = \{\theta_i = 10000^{-2(i-1)/d} \mid i = 1, 2, ..., d/2\}$$

**RoPE 的矩阵形式**：

$$\mathbf{R}_{\Theta, m} = \begin{bmatrix}
\cos m\theta_1 & -\sin m\theta_1 & 0 & 0 & \cdots \\
\sin m\theta_1 & \cos m\theta_1 & 0 & 0 & \cdots \\
0 & 0 & \cos m\theta_2 & -\sin m\theta_2 & \cdots \\
0 & 0 & \sin m\theta_2 & \cos m\theta_2 & \cdots \\
\vdots & \vdots & \vdots & \vdots & \ddots
\end{bmatrix}$$

这是一个块对角旋转矩阵。RoPE 将 Q 和 K 分别旋转后，它们的注意力分数为：

$$\mathbf{q}_m^T \mathbf{k}_n = (\mathbf{R}_{\Theta, m} \mathbf{W}^Q \mathbf{x}_m)^T (\mathbf{R}_{\Theta, n} \mathbf{W}^K \mathbf{x}_n) = \mathbf{x}_m^T {\mathbf{W}^Q}^T \mathbf{R}_{\Theta, n-m} \mathbf{W}^K \mathbf{x}_n$$

**实际计算的高效实现**：不需要完整的矩阵乘法。RoPE 可以逐元素计算：

```python
def rope(x, position, theta=10000.0):
    """
    x: (..., d) — query or key vector
    Returns rotated x
    """
    d = x.shape[-1]
    # 频率：几何级数
    freq = 1.0 / (theta ** (np.arange(0, d, 2) / d))
    # 角度：位置 × 频率
    angle = position * freq
    # 旋转：(x_0, x_1) → (x_0*cos - x_1*sin, x_0*sin + x_1*cos)
    cos, sin = np.cos(angle), np.sin(angle)
    x_rot = x.copy()
    x_rot[..., 0::2] = x[..., 0::2] * cos - x[..., 1::2] * sin
    x_rot[..., 1::2] = x[..., 0::2] * sin + x[..., 1::2] * cos
    return x_rot
```

**RoPE 的三个关键性质**：

1. **相对位置编码**：$\mathbf{q}_m^T \mathbf{k}_n = g(m-n)$，注意力分数只取决于相对距离
2. **长距离衰减**：对于随机的 $\mathbf{x}_m, \mathbf{x}_n$，RoPE 的内积的期望随 $|m-n|$ 增大而衰减。这不是硬约束，而是一个自然的统计性质
3. **可外推性**：由于使用连续的三角函数定义，理论上可以对任意位置求值。虽然 naive 的外推性能会下降（因为训练数据中没见过大幅度的旋转角），但可以通过 NTK-aware 等方法修复

### 4.5 ALiBi（Press 2022）：最简单的东西有时最有效

> Press et al., *Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation* (2022)

ALiBi（Attention with Linear Biases）的方法极其简单：在 softmax 之前，给注意力分数加上一个随相对距离线性衰减的偏置：

$$\text{Attention}_{\text{ALiBi}}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{d_k}} + \mathbf{B}\right) \mathbf{V}$$

其中 $\mathbf{B}_{ij} = -m \cdot |i - j|$，$m$ 是头特定的斜率：

$$m = 2^{-\frac{8h}{H}} \quad \text{（对第 h 个头）}$$

例如，对于 $H=8$，斜率是 $2^{-1}, 2^{-2}, ..., 2^{-8}$，即 $0.5, 0.25, ..., 0.0039$。不同头有不同的衰减速度——有些头关注很近的位置（大斜率），有些头关注很远的依赖（小斜率）。

**为什么 ALiBi 能外推？** 因为偏置是纯几何的（只依赖于距离），不引入任何可学习参数或位置特定的函数。训练时见过距离 1-2048，推理时距离 4096 的偏置是训练时距离模式的直接延伸。

ALiBi 在 Bloom 和 MPT 系列模型中使用，效果极好：训练长度 1024，可以直接外推到 8000+ 且 perplexity 几乎不降。

### 4.6 长上下文扩展技术

随着 LLM 的上下文长度从 2K → 8K → 32K → 128K → 1M，如何让在短序列上训练的模型适应长序列成为一个核心工程问题。

**问题本质**：RoPE 在推理时遇到比训练时更大的旋转角，attention score 的分布改变，导致模型困惑。

**方法一：Position Interpolation（PI, Chen 2023）**
- 思路：将新位置"缩"回训练范围内
- 实现：将 RoPE 中的位置索引替换为 $pos \cdot \frac{L_{\text{train}}}{L_{\text{target}}}$
- 效果：只需少量微调（~1000 steps）就能扩展到 4-8 倍长度
- 缺点：高频信息被过度压缩，局部注意力退化（相邻位置的区分度下降）

**方法二：NTK-aware Interpolation（bloc97 2023）**
- 思路：低频维度需要更多插值（它们对远距离敏感），高频维度几乎不插值（它们对局部位置敏感，不插值可以保持分辨能力）
- 实现：用 $\theta_i' = \theta_i \cdot s^{\frac{d/2 - i}{d/2 - 1}}$ 缩放 RoPE 的基频（$s$ 是扩展倍数，高频维度 $i$ 小 → 缩放少，低频维度 $i$ 大 → 缩放多，类似 NTK 理论中的直觉）
- 效果：几乎不需要微调

**方法三：YaRN（Peng 2023）**
- 在 NTK-aware 基础上进一步优化了温度 scaling
- 实现：$\text{Attention} = \text{softmax}(\mathbf{Q}\mathbf{K}^T / \sqrt{d_k} / t)$，其中 $t$ 是温度系数
- 效果：只需 ~400 steps 微调即可扩展到 128K

**方法四：Recurrent / Streaming 架构**
- StreamingLLM、Ring Attention、Self-Extend 等
- 思路：不尝试让所有 token 互相关注，而是用滑窗 + 注意力汇（attention sink）

**方法五：分层混合（DeepSeek V4 方案）**
- 不同层使用不同的注意力策略：浅层用 HCA（粗粒度、大视野），深层用 CSA（细粒度、小视野）
- 详见 [DeepSeek V4 注意力机制深度解析](../dsv4_att)

### 4.7 位置编码全景对比

| 方法 | 年份 | 编码方式 | 外推能力 | 计算开销 | 使用者 |
|------|------|---------|---------|---------|--------|
| Sinusoidal | 2017 | 绝对 | 理论可，实践差 | 极低 | 原始 Transformer |
| Learned | 2018 | 绝对 | 无 | 极低 | GPT-1/2/3 |
| RoPE | 2021 | 相对 | 需技巧 | 低 | LLaMA, Qwen, DeepSeek |
| ALiBi | 2022 | 相对偏置 | 优秀 | 几乎为零 | Bloom, MPT |
| NoPE | 2024 | 无 | 优秀 | 零 | 某些小模型实验 |

> 当前（2026）的主流选择是 **RoPE**，几乎所有主流 LLM（LLaMA, Qwen, DeepSeek, Gemma, Mistral）都使用 RoPE。ALiBi 简洁且外推强，但在长上下文质量上略逊于经过 NTK/YaRN 优调的 RoPE。位置编码的研究仍在快速发展——"最好的位置编码"这个问题还没有最终答案。

---

## 第五章：混合专家模型 (MoE)

> MoE 是 LLM 从"大力出奇迹"走向"聪明地用力"的关键转折。它让千亿参数模型的计算成本不再随参数量线性增长。

### 5.1 MoE 的基本思想

一个稠密 Transformer 中，每个 token 都要通过**所有** FFN 参数。对于 175B 参数的模型，每个 token 的前向传播要经过全部 175B 参数——计算量是固定的。

**MoE 的核心洞见**：不是所有知识对所有任务都有用。对于某个具体 token，可能只有部分"专家"（expert FFN）是相关的。因此，用一个路由器（router）动态选择少数几个专家来激活。

稀疏激活的 MoE 层定义为：

$$\mathbf{y} = \sum_{i \in \mathcal{T}} G(\mathbf{x})_i \cdot E_i(\mathbf{x})$$

其中：
- $E_i(\cdot)$ 是第 $i$ 个专家（一个 FFN）
- $G(\mathbf{x}) = \text{Softmax}(\text{TopK}(\mathbf{x} \mathbf{W}_g))$ 是门控函数
- $\mathcal{T}$ 是 Top-K 最大的 logit 对应的专家索引集合
- 通常 $K=2$（每个 token 激活 2 个专家）

**关键术语**：

| 名词 | 含义 | 例子 |
|------|------|------|
| 总参数量（Total params） | 所有专家的参数之和 + 共享参数 | Mixtral 8×7B = 47B |
| 激活参数量（Active params） | 每个 token 实际使用的参数 | Mixtral 8×7B = 13B（2 个 7B 专家 + 共享 attention） |
| 专家数（N） | MoE 层有多少个专家 | Mixtral: 8, DeepSeek-V3: 256 |
| Top-K | 每个 token 激活几个专家 | 通常是 2 |
| 负载均衡 | 确保所有专家都被均匀使用 | 通过 auxiliary loss 实现 |

### 5.2 关键设计问题

**问题一：路由策略**

最简单的路由是对 $\mathbf{x} \mathbf{W}_g$ 取 top-k。但 k 选多少？

- **Top-1 路由**（Switch Transformer, Fedus 2021）：每个 token 只激活一个专家。最极端的稀疏性，但容易出现"专家坍塌"（所有 token 都选同一个专家）。
- **Top-2 路由**（GShard, Mixtral, DeepSeek）：每个 token 激活两个专家。在效率和质量之间的最佳平衡点。大多数 MoE LLM 标配。
- **Top-K 自适应**（DeepSeek-V4 的 mHC）：不同层、不同 token 可以激活不同数量的专家，总计控制在某个预算内。

**问题二：负载均衡**

如果所有 token 都选择同一个专家，MoE 就退化为一个（过载的）单模型。需要强制均衡：

- **Auxiliary Loss（辅助损失）**：Switch Transformer 引入的经典方案：

  $$\mathcal{L}_{\text{aux}} = \alpha \cdot N \cdot \sum_{i=1}^{N} f_i \cdot P_i$$

  其中 $f_i$ 是实际路由到专家 $i$ 的 token 比例，$P_i$ 是路由器分配给专家 $i$ 的平均概率。理想情况下 $f_i = P_i = 1/N$，辅助损失为最小值 $\alpha$。

  系数 $\alpha$ 通常设为 0.01——足够驱动均衡，但不过度干扰主任务损失。

- **Auxiliary-Loss-Free Balancing**（DeepSeek-V3）：不通过损失函数干预，而是动态调整每个专家的偏置项（bias），倾向路由 token 少的专家。

**问题三：专家容量**

实际训练中，无法保证每个专家恰好处理 $B/N$ 个 token（$B$ 是每个 batch 的 token 总数）。如果某个专家收到的 token 超过 GPU 显存能处理的量怎么办？

**Capacity Factor** 定义了每个专家能处理的最大 token 数：

$$\text{Expert Capacity} = \frac{\text{tokens\_per\_batch}}{\text{num\_experts}} \times \text{capacity\_factor}$$

溢出的 token 直接跳过 MoE 层（通过残差连接传递），不产生专家计算。通常 capacity_factor 设为 1.25-2.0。

**问题四：共享专家 vs 路由专家**

DeepSeekMoE 引入了一个重要创新：除了路由专家外，还设有一个**共享专家**（所有 token 都经过它）。这使得：

- 共享专家捕获通用知识（语法、常识）
- 路由专家捕获特殊知识（领域知识、专业术语）

这种设计下，即使路由分配完全失败（所有 token 都去了共享专家），模型也不会完全瘫痪。

### 5.3 MoE 的代表性模型

| 模型 | 年份 | 总参数 | 激活参数 | 专家数 | Top-K | 关键创新 |
|------|------|--------|---------|--------|-------|---------|
| GShard | 2020 | 600B | ~4B | 2048 | 2 | 首次大规模 MoE（翻译） |
| Switch Transformer | 2021 | 1.6T | ~5B | 2048 | 1 | 简化路由, 万亿参数 |
| Mixtral 8×7B | 2023 | 47B | 13B | 8 | 2 | 开源 MoE, 性能超 LLaMA 70B |
| DeepSeek-V2 | 2024 | 236B | 21B | 160 | 6 | 细粒度专家 + 共享专家 + MLA |
| DeepSeek-V3 | 2024 | 671B | 37B | 256 | 8 | FP8 训练, 无辅助损失路由 |
| DeepSeek-V4 | 2025 | 1020B+ | ~50B | — | 动态 | mHC 统一注意力和路由 |

### 5.4 MoE 的工程代价

MoE 不是免费的午餐，它带来了独特的工程挑战：

**通信开销**：在分布式训练中，每个专家的参数可能分布在不同的 GPU 上。每个 token 需要被发送到它选择的专家的所在 GPU（all-to-all communication），计算后再发回去。对于 256 个专家分布在 32 个节点上，通信开销可能占总时间的 20-30%。

**推理内存**：虽然激活参数少，但全部参数都必须加载在内存中（因为不知道下一个 token 会选择哪个专家）。一个 671B 的 MoE 模型，激活只有 37B，但需要约 1.3TB 显存来存放所有参数。

**微调的困难**：MoE 模型的微调比稠密模型更敏感。如果微调数据分布与预训练差异大，路由器可能做出错误分配，导致灾难性遗忘。

> MoE 在 2024-2025 年成了大模型竞赛的核心赛道。DeepSeek 用 MoE 在性能上对标 GPT-4（用 1/10 的激活参数），而 Mixtral 证明了开源 MoE 的可行性。可以预见，未来几乎所有千亿以上参数的模型都会采用某种形式的 MoE。

---

## 第六章：LLaMA 系列与开放模型生态

> LLaMA 的发布标志着 LLM 的"开源时刻"。2023 年 2 月至今，开放模型从追赶者成长为领先者。

### 6.1 LLaMA 1 (2023)：小而美的哲学

> Touvron et al., *LLaMA: Open and Efficient Foundation Language Models* (2023)

LLaMA 的核心主张是：**用更多更好的数据训练更小的模型**。在 Chinchilla 定律出现后，Meta AI 第一个将"数据质量 > 数据量"这一哲学推向极致。

架构设计的三个关键选择：

1. **Pre-Normalization**：使用 RMSNorm 在 Attention 和 FFN 的**输入**处归一化（而不是原始 Transformer 的输出处）。RMSNorm 去掉均值的计算，比 LayerNorm 更快：
   $$\text{RMSNorm}(\mathbf{x}) = \frac{\mathbf{x}}{\sqrt{\frac{1}{d}\sum_i x_i^2 + \epsilon}} \odot \gamma$$

2. **SwiGLU 激活**：用门控机制替换 ReLU，在等参数量下性能更好：
   $$\text{SwiGLU}(\mathbf{x}) = (\text{SiLU}(\mathbf{x}\mathbf{W}_1) \odot \mathbf{x}\mathbf{W}_2) \mathbf{W}_3$$
   其中 $\text{SiLU}(x) = x \cdot \sigma(x)$。FFN 的中间维度设为 $\frac{8}{3}d_{\text{model}}$ 而非 $4d_{\text{model}}$，以与标准 FFN 保持等参数量。

3. **RoPE**：用旋转位置编码替代可学习或 Sinusoidal。

LLaMA 系列的模型配置：

| 模型 | 参数 | $d_{\text{model}}$ | 头数 | 层数 | 训练 Token | 关键结果 |
|------|------|-------------------|------|------|-----------|---------|
| LLaMA-7B | 6.7B | 4096 | 32 | 32 | 1.0T | — |
| LLaMA-13B | 13.0B | 5120 | 40 | 40 | 1.0T | 超 GPT-3 175B |
| LLaMA-33B | 32.5B | 6656 | 52 | 60 | 1.4T | — |
| LLaMA-65B | 65.2B | 8192 | 64 | 80 | 1.4T | 接近 PaLM 540B |

**LLaMA 的数据配比**是其成功的关键之一：

| 数据源 | 比例 | 作用 |
|--------|------|------|
| CommonCrawl | 67.0% | 通用知识 |
| C4 | 15.0% | 清洗后的网页 |
| GitHub | 4.5% | 代码能力 |
| Wikipedia | 4.5% | 结构化知识 |
| Books | 4.5% | 长文本理解 |
| ArXiv | 2.5% | 科学推理 |
| StackExchange | 2.0% | 问答格式 |

所有数据均公开可用——这给了开源社区一个明确的信号："不需要专有数据也能做出顶级模型"。

### 6.2 LLaMA 2 (2023)：开源+商用

> Touvron et al., *Llama 2: Open Foundation and Fine-Tuned Chat Models* (2023)

LLaMA 2 的最大突破不在架构（基本沿用 LLaMA 1），而在**对齐**和**开源协议**：

- **GQA**：70B 模型使用 8 组 Grouped-Query Attention，KV Cache 减少到 1/8
- **更长上下文**：从 2K 扩展到 4K
- **更多数据**：2T tokens
- **RLHF 对齐**：发布了 Llama 2-Chat，经过 SFT + RLHF
- **开放商用**：允许商业使用的开源协议

LLaMA 2 的对齐流水线值得花一点篇幅。它使用了 RLHF，但做了一些工程改进：

1. **两阶段 RLHF**：先对有用性（helpfulness）做 PPO，再对安全性（safety）做 PPO
2. **边际奖励**：奖励模型输出的是两个回复之间的相对分数差，而非绝对分数——这减少了标注者偏差的影响
3. **Ghost Attention**：在每轮对话中注入系统指令作为额外的训练信号

### 6.3 LLaMA 3 (2024)：大规模合成数据

LLaMA 3 是 Meta 的"全力以赴"版本。核心数字：

- 8B 模型：15T tokens 训练
- 70B 模型：15T tokens 训练
- 405B 模型：15T tokens 训练（是的，同样 15T，因为已经快接近数据天花板了）
- 128K 词表（覆盖 30+ 语言）
- 8K 上下文（初始版本）

关键创新是**合成数据的大规模应用**：

1. 用 LLaMA 3-405B 生成大量的代码、数学、推理训练数据
2. 用这些合成数据训练 LLaMA 3-8B 和 70B
3. 结果：小模型通过从大模型"学习"（蒸馏）获得了超预期的能力

LLaMA 3 的 Scaling Law 发现：即使在 Chinchilla 最优值之后，继续增加数据仍然能提升性能（只是提升速度变慢）。15T 对于 8B 参数来说已经是 1875× 的过度训练。这个发现直接推动了"超长训练小模型"的趋势。

### 6.4 DeepSeek 系列：从追赶到领先

DeepSeek 的模型演进路径展示了中国 AI 公司的技术实力：

| 模型 | 年份 | 关键创新 | 意义 |
|------|------|---------|------|
| DeepSeek-V2 | 2024.05 | MLA + DeepSeekMoE | KV Cache 大幅压缩，MoE + 共享专家 |
| DeepSeek-V3 | 2024.12 | FP8 训练 + MTP | 万亿 MoE 有效训练，多 token 预测 |
| DeepSeek-R1 | 2025.01 | GRPO 纯 RL 推理 | 不开源的推理能力终于被开源追上 |
| DeepSeek-V4 | 2025.06 | mHC + CSA/HCA | 统一注意力和路由，分层混合注意力 |

DeepSeek 的技术哲学是"**在每一个瓶颈上都做创新**"：
- 显存不够？MLA 压缩 KV Cache
- 计算量太大？MoE 稀疏激活
- 负载不均衡？Auxiliary-loss-free 路由
- 长上下文崩溃？分层混合稀疏注意力
- 推理能力不足？GRPO 纯 RL 训练

结果：DeepSeek-V3 以约 1/10 的激活参数和约 1/50 的训练成本，在大量基准上接近 GPT-4 的水平。

> DeepSeek 的技术栈——MLA（注意力压缩）、MoE（稀疏激活）、GRPO（推理训练）——在本仓库的多篇文章中有详细分析。本文侧重全景视角，具体技术细节请参考：
> - [DeepSeek V4 注意力：MLA、NSA、mHC](../dsv4_att)
> - [思维链综述：GRPO 与 R1 训练管线](../cot-survey)

### 6.5 开放模型的版图（2026）

| 系列 | 开发商 | 最大版本 | 特点 |
|------|--------|---------|------|
| LLaMA | Meta | 405B | 综合能力最强开源 |
| Qwen | 阿里 | 72B / MoE | 中文最佳，多版本覆盖 |
| DeepSeek | 深度求索 | MoE 671B+ | MoE 效率巅峰 |
| Mistral | Mistral AI | MoE 8×22B | 欧洲最佳 |
| Gemma | Google | 27B | 轻量高性能 |
| Yi | 零一万物 | 34B | 中文社区贡献 |
| Command R | Cohere | 104B | RAG 优化 |

---

## 第一幕小结

我们覆盖了 LLM 架构从 2017 到 2026 年的演进：

- **Attention 机制**（§1）：从 $O(n^2)$ 的标准注意力到 MLA（压缩存储）到 NSA（稀疏选择）
- **GPT 系列**（§2）：规模化 + ICL + Chat，架构改进藏在细节中
- **注意力进化**（§3）：MHA → MQA → GQA → MLA → NSA——每一步都是对 KV Cache 的优化
- **位置编码**（§4）：从绝对到相对，从固定到可学习再到旋转——RoPE 是当前共识
- **MoE**（§5）：稀疏激活的 FFN，万亿参数的计算可行解
- **开放生态**（§6）：LLaMA、Qwen、DeepSeek 三足鼎立

下一幕我们转向**预训练**——这些海量参数如何被训练出来，分布式训练如何工作，以及 Scaling Laws 如何指导"该用多少参数、多少数据"。

---

## 第二幕：预训练 — 从数据到基础模型

---

## 第七章：预训练目标与数据工程

> 如果说架构是 LLM 的"身体"，那预训练就是"成长过程"。一个架构设计完美的模型，用垃圾数据训练，就是垃圾模型（garbage in, garbage out）。数据工程是 LLM 项目中最耗时、最不被理解、也最关键的部分。

### 7.1 预训练目标

自回归 LLM 的训练目标出奇地简单——**Next-Token Prediction**（下一 token 预测）：

$$\mathcal{L}(\theta) = -\frac{1}{|\mathcal{D}|} \sum_{\mathbf{x} \in \mathcal{D}} \sum_{t=1}^{|\mathbf{x}|} \log p_\theta(x_t \mid x_{<t})$$

给定一个 token 序列，模型在每个位置都尝试预测下一个 token，计算交叉熵损失，反向传播更新所有参数。

**为什么这么简单的东西能 work？** 因为"预测下一个 token"这个任务隐式地要求模型学习关于世界的各种知识：

- 预测"巴黎是___的首都" → 需要学会地理知识
- 预测 "if x = 5: print(___)" → 需要学会代码执行
- 预测 "翻译成英文：你好 → ___" → 需要学会翻译
- 预测 "Q: 什么是光合作用？A: ___" → 需要学会解释概念

语言建模的"压缩"视角在这里很有启发性：好的语言模型 = 好的压缩器。如果模型能把文本压缩得更好（更低的 PPL），说明它更理解文本结构。

### 7.2 训练数据流水线

预训练数据经过多个阶段才能喂给模型。一个典型的数据流水线：

```
原始数据源（CommonCrawl, Books, Code, Wiki...）
    │
    ▼
[1] 数据提取：从原始格式（HTML, PDF, JSON）提取纯文本
    │
    ▼
[2] 语言检测与过滤：扔掉非目标语言的文本
    │
    ▼
[3] 质量过滤：去掉低质量/有害内容
    ├── 基于规则：长度过滤、重复句子、特殊字符比例
    ├── 基于模型：用轻量分类器打分（perplexity-based, classifier-based）
    └── 基于启发式：URL 黑名单、成人内容过滤
    │
    ▼
[4] 去重（Deduplication）
    ├── 精确去重：完全相同文档
    ├── 近似去重：MinHash + LSH（Locality Sensitive Hashing）
    └── URL 级去重：同一来源的重复抓取
    │
    ▼
[5] 数据混合：按比例混合不同来源的数据
    │
    ▼
[6] Tokenization：将文本切分为 token 序列
    │
    ▼
[7] 打包（Packing）：将多个文档拼接为一个训练序列
    │
    ▼
最终训练数据
```

**为什么去重如此重要？** 互联网上有大量重复内容（镜像站点、转发、引用）。如果不做去重：

1. 模型会浪费训练预算在重复样本上
2. 模型可能"背诵"（memorize）重复出现的文本，导致训练集 PPL 虚低
3. 最坏情况：推理时逐字输出训练数据 → 隐私和版权问题

LLaMA 使用了 MinHash + 5-gram 重叠来近似去重。MinHash 的基本思路：用多个哈希函数对文档的 n-gram 集合做签名，签名相似的文档就是近似重复的。

### 7.3 数据混合的策略

不同数据源对模型不同能力的影响是不同的。一个经验性的观察：

| 数据类型 | 主要贡献 | 过量使用的风险 |
|---------|---------|--------------|
| 网页文本（CommonCrawl） | 常识、世界知识、对话风格 | 表面化、低信息密度 |
| 书籍 | 长文本连贯性、深层叙述 | 过时知识（经典文学） |
| 代码（GitHub） | 推理能力、逻辑思维 | 模型"说代码"（非人类语言） |
| 学术论文 | 科学推理、形式化思维 | 术语密集、不自然 |
| Wikipedia | 结构化事实知识 | 覆盖范围有限 |
| 论坛/社交媒体 | 对话能力、接地气 | 低质量、有毒内容 |

**数据退火（Data Annealing）** 是近年兴起的高级策略：在训练的早期阶段用大量"粗糙"数据（如完整 CommonCrawl），在训练末期切换到少量高质量数据（如精选的教科书级内容）。这类似于冶金中的退火过程——先粗加工再精加工。

LLaMA 3 的技术报告透露了一个有趣的发现：大量合成数据（由强模型生成）是提升小模型性能的关键。这正在成为行业标准做法。

### 7.4 数据清洗的规模挑战

预训练数据以 TB 计。LLaMA 3 的训练集约为 15T tokens，按英文约 0.75 个单词/token 换算，大约相当于 110 亿单词——比一个人一生能阅读的量多约 100 万倍。

这个规模下的清洗必须高度自动化且计算可控：
- 不能对每个文档跑大型 NLP 模型（成本不匹配）
- FastText 语言检测：简单但有效
- KenLM perplexity 打分：用 n-gram 模型淘汰"不像自然语言"的文本
- 规则 + 阈值是主力，深度学习模型只在必要时上场

一条经验法则：**从原始 CommonCrawl 到可用的高质量训练数据，数据的保留率通常只有 5-15%**。也就是说，为了获得 15T 的训练 token，可能需要处理 100-300T 的原始文本。

### 7.5 数据打包与序列构建

Tokenization 后的 token 序列需要被"打包"成固定长度的训练序列。两种常见策略：

1. **填充分组（Padding + Batching）**：将长度相近的文档放入同一个 batch，用 pad token 补齐。缺点是浪费 pad token 上的计算。
2. **无填充拼接（Concatenation + Chunking）**：将所有文档 token 直接拼接成一条超级长序列，然后切分成固定长度的 chunk。文档之间用 EOS token 分隔。LLaMA 和 GPT-3 都使用这种方案。

实践中的一个重要细节：文档边界处理。不同文档拼接在一起时，需要在文档之间插入分隔 token（如 `<|endoftext|>`），并确保 attention mask 不会跨文档泄露信息（虽然实际上 causal mask 天然防止了这一点，但特殊处理可以提高数据利用效率）。

---

## 第八章：Scaling Laws — 多少数据配多少参数？

> Scaling Laws 是整个 LLM 产业最核心的"经济学"。在动手训练之前，你必须回答：给定计算预算，最优的模型大小和数据量是多少？

### 8.1 Kaplan (2020)：第一代 Scaling Laws

> Kaplan et al., *Scaling Laws for Neural Language Models* (2020)

OpenAI 的 Kaplan 团队首次系统性地研究了语言模型性能与 $N$（参数量）、$D$（数据量）、$C$（计算量）之间的关系。核心发现：

**损失函数随 $N, D, C$ 都呈幂律关系**：

$$L(N) \propto N^{-0.076}$$
$$L(D) \propto D^{-0.095}$$
$$L(C) \propto C^{-0.057}$$

这意味着：如果想让损失减半，需要将参数量增加约 $2^{1/0.076} \approx 9000$ 倍——回报递减很快。

**Kaplan 的核心推论**：要最大化固定计算预算下的性能，应该**优先增大模型而非增加数据**。具体来说：
$$N_{\text{opt}} \propto C^{0.73}, \quad D_{\text{opt}} \propto C^{0.27}$$

即模型大小的增长应该比数据量快得多。这个推论直接指导了 GPT-3 的设计——175B 参数，训练 300B tokens。

### 8.2 Chinchilla (2022)：纠正与革命

> Hoffmann et al., *Training Compute-Optimal Large Language Models* (2022)

DeepMind 的 Chinchilla 团队发现 Kaplan 的推论有误。问题出在 Kaplan 的分析方法上——他们用了固定的学习率 schedule（与模型大小无关），导致小模型被"过度训练"而大模型被"欠训练"。

Chinchilla 用一个更全面的方法——同时变化模型大小和训练 token 数——重新估计了 Scaling Laws：

$$L(N, D) = E + \frac{A}{N^\alpha} + \frac{B}{D^\beta}$$

拟合得到的参数：$\alpha \approx 0.34, \beta \approx 0.28$（这与 Kaplan 的幂指数不同，反映了更准确的估计）。

**Chinchilla 的核心结论**：模型大小和数据量应该**等比例增长**：

$$N_{\text{opt}} \propto C^{0.50}, \quad D_{\text{opt}} \propto C^{0.50}$$

这意味着对每个参数，应该训练约 20 个 token。具体来说：

| 参数量 | 最优训练 Token 数 | 当前实践 |
|--------|-------------------|---------|
| 1B | ~20B | 200B+（严重过度训练） |
| 10B | ~200B | 2T+ |
| 100B | ~2T | 15T+ |
| 1T | ~20T | 尚未达到 |

**Chinchilla 的实战验证**：他们训练了一个 70B 的 Chinchilla 模型（1.4T tokens），在相同计算预算下超过了 280B 的 Gopher。这个结果震惊了整个社区——**原来大家一直在浪费算力训练过大的模型**。

**重要澄清**：Chinchilla 估算的是给定计算预算下的"最优"配置，但如果你有充足的数据（15T+ tokens），或者推理成本是主要考虑（较小模型推理更快），那么"过度训练"一个小模型可能是更好的选择。LLaMA 3-8B 训练在 15T tokens 上就是出于这个逻辑。

### 8.3 超越 Chinchilla

Chinchilla 之后，几个重要的延伸：

**数据质量的影响**：Chinchilla 假设数据是独立同分布的，但实际上数据质量参差不齐。数据去重和过滤可以提高"有效 token 数"。这解释了为什么 LLaMA 能用 1.4T 的高质量 tokens 达到超过 Chinchilla 预测的性能。

**数据重复的收益**：Chinchilla 假设数据不重复。但在实践中，可能需要 4-5 个 epoch（重复 4-5 次）的高质量数据才能获得最佳性能。高质量数据（如书籍、代码）的重复是有价值的，低质量数据（如 CommonCrawl）的重复是浪费。

**合成数据的 Scaling**：LLaMA 3 发现合成数据具有独特的 scaling 行为——10% 的合成数据能带来远超过 10% 的性能提升。这可能在根本上改变数据 scaling 的逻辑：与其收集更多自然文本，不如让强模型生成高质量合成数据。

### 8.4 涌现能力

> Wei et al., *Emergent Abilities of Large Language Models* (2022)

"涌现"是 LLM 领域最引人注目的现象之一：某些能力在模型达到一定规模后**突然出现**——在小模型上几乎为零的性能，在大模型上跃升到高水平。

典型涌现能力：
- 3 位数加减：在 13B 以下几乎为 0，在 175B 时突然达到 80%+
- 多语言翻译：在 6B 时 ≈10%，在 175B 时 ≈50%
- TruthfulQA：随模型增大性能反而有跳跃式提升

**争议**：2024 年，Schaeffer 等人提出，这些"涌现"可能只是评估指标的非线性造成的伪影。如果使用连续的指标（如 token-level probability），性能变化是平滑的。如果使用不连续的指标（如 exact match accuracy），平滑变化的概率会在某个阈值处突然跨越正确/错误的边界。

无论涌现是真实现象还是度量伪影，它的实用意义是：**小规模实验无法预测大规模行为**。你不能用 1B 模型的表现来推测 100B 模型的表现——这也是 Scaling Laws 研究的核心价值。

---

## 第九章：分布式训练

> 一个 175B 参数的模型用 float16 存储需要 350GB 显存——远超任何单张 GPU 的容量（H100 为 80GB，B200 为 192GB）。分布式训练不是可选项，是必需品。

### 9.1 混合精度训练

现代 LLM 训练使用混合精度来平衡速度和精度：

- **FP32（float32）**：权重的主副本（master weights），用于精确的参数更新
- **FP16/BF16（float16/bfloat16）**：前向和反向传播中的激活值和梯度——速度快 2×，显存省一半
- **FP8**（DeepSeek-V3 首创大规模使用）：更进一步，训练速度提升 ~2×

**为什么 BF16 优于 FP16？** FP16 的指数只有 5 位，能表示的数值范围约为 $[-65504, 65504]$，超出的值会溢出。BF16 保留了和 FP32 一样的 8 位指数，范围约 $[-3.4\times 10^{38}, 3.4\times 10^{38}]$，避免了训练中的梯度溢出。

**损失缩放（Loss Scaling）** 是 FP16 训练的必须技巧：在反向传播时，将损失乘以一个大常数（如 1024），使小梯度落入 FP16 的可表示范围，然后在更新前除回去。

### 9.2 数据并行（Data Parallelism）

最基础的分布式策略：每个 GPU 持有一份完整的模型副本，batch 被均匀拆分到不同 GPU 上训练。反向传播后，所有 GPU 对梯度做 all-reduce（求平均），然后各自更新参数。

```python
# PyTorch 分布式数据并行 (DDP) 的简化伪代码
model = MyModel()
model = DDP(model, device_ids=[local_rank])

for batch in dataloader:
    loss = model(batch)           # 每个 GPU 计算其子 batch 的损失
    loss.backward()               # 每个 GPU 计算其子 batch 的梯度
    # all-reduce 自动在 backward 中完成
    optimizer.step()              # 所有 GPU 做相同的参数更新
```

**局限**：每个 GPU 必须存下整个模型。对于 175B 模型，数据并行需要每个 GPU 至少有 350GB 显存——这需要至少 5 张 80GB 的 A100。而且随着 GPU 数量增加，all-reduce 通信开销线性增长。

### 9.3 模型并行

当模型大到单 GPU 放不下时，需要**模型并行**——将模型切片到多个 GPU 上。

**张量并行（Tensor Parallelism, TP）**：在层内部进行切分。例如，将 Transformer 的 Attention 矩阵的列均匀分布在多个 GPU 上，每个 GPU 计算其持有的列的部分结果，然后通过通信合并。

以多头注意力为例（Megatron-LM 方案）：
- 将 $\mathbf{W}^Q, \mathbf{W}^K, \mathbf{W}^V$ 按列切分到 $t$ 个 GPU 上
- 每个 GPU 计算其持有的注意力头
- 将 $\mathbf{W}^O$ 按行切分，各 GPU 计算部分输出
- 通过 all-reduce 合并

优点：通信在 Transformer 层的内部（前向/反向传播中），可以与计算重叠。缺点：跨 GPU 通信量大，对 GPU 间带宽要求极高（通常需要 NVLink）。

**流水线并行（Pipeline Parallelism, PP）**：将模型按层切分，GPU 0 负责层 1-10，GPU 1 负责层 11-20，以此类推。每个 GPU 处理完一个 micro-batch 后传给下一个 GPU。

流水线并行的难点是**气泡（bubble）**——在流水线填充和排空阶段，大量 GPU 处于空闲状态：

```
时间 →
GPU0: [1][2][3]___[4][5][6]___
GPU1: ___[1][2][3]___[4][5][6]
GPU2: _______[1][2][3]___[4][5]
         ↑ bubble（40% 空闲）
```

**减少气泡**：使用更多更小的 micro-batch，或使用 GPipe 的交错调度（interleaved schedule）。

### 9.4 ZeRO（零冗余优化器）

> Rajbhandari et al., *ZeRO: Memory Optimizations Toward Training Trillion Parameter Models* (2020)

DeepSpeed 的 ZeRO 系列策略通过**分片优化器状态**来大幅减少显存浪费。

回顾显存占用：
1. **模型参数**（必须）
2. **梯度**（必须）
3. **优化器状态**：Adam 需要存储一阶矩 $\mathbf{m}$ 和二阶矩 $\mathbf{v}$，各为参数量大小

对于混合精度训练（fp16 参数 + fp32 优化器状态），显存的分布大致是：
- fp16 参数 + 梯度：$4N$ 字节
- fp32 优化器状态（m + v + master params）：$12N$ 字节
- **总计**：$16N$ 字节，其中优化器状态占了 75%！

ZeRO 的三个阶段：

| 阶段 | 分片内容 | 显存节省 | 通信开销 |
|------|---------|---------|---------|
| ZeRO-1 | 优化器状态 | 4× | 低（all-reduce 梯度） |
| ZeRO-2 | 优化器状态 + 梯度 | 8× | 低 |
| ZeRO-3 | 优化器状态 + 梯度 + 参数 | 与 GPU 数成正比 | 中（需要 all-gather 参数） |

ZeRO-3 如何工作：参数被分片存储在 $P$ 个 GPU 上，每个 GPU 只持有 $1/P$ 的参数。前向传播时，需要的参数片段通过 all-gather 临时恢复，计算完成后立即释放。反向传播同理。

### 9.5 3D 并行：实操方案

实际训练一个大模型时，通常组合使用三种并行策略：

```
3D Parallelism = Data Parallelism × Tensor Parallelism × Pipeline Parallelism
```

以 GPT-3 175B 的训练为例（据推测）：

```
总 GPU 数 = 10000 个 V100（~350 个节点，每个节点 8 GPU）
- 数据并行度 = 64 → 每个 DP 组有 10000/64 ≈ 156 GPUs
- 流水线并行度 = 4 → 每个 PP 组有 156/4 = 39 GPUs  
- 张量并行度 = 8 → 每个 TP 组内 8 张 GPU（同一节点内 NVLink 连接）

总并行度 = DP × PP × TP = 64 × 4 × 8 = 2048（大约实际使用数）
```

### 9.6 训练基础设施

大模型训练不只是软件问题，硬件和网络是关键：

- **GPU 互联**：节点内用 NVLink/NVSwitch（900 GB/s，A100），节点间用 InfiniBand/RoCE（200-400 Gbps）
- **通信原语**：NCCL（NVIDIA Collective Communications Library）提供 all-reduce、all-gather、reduce-scatter 等
- **故障恢复**：1000+ GPU 训练数周，GPU 故障几乎必然发生。需要定期 checkpoint 保存（每 N 步），以及从最近 checkpoint 自动恢复的机制

---

## 第十章：训练稳定与优化

### 10.1 损失尖峰

在训练过程中，loss 有时会突然飙高（loss spike），然后可能：
- **恢复**：loss 回到正常轨迹，训练继续 → 问题不大
- **崩溃**：loss 变为 NaN，训练停止 → 需要回滚到 spike 前的 checkpoint

原因：梯度在某些 batch 上的异常大值（特别是数据包含非常长或非常特殊的序列）。MoE 模型中路由器的突然改变也可能引发。

应对：
- 梯度裁剪（gradient clipping）：将梯度的范数限制在阈值内（如 clip_grad_norm = 1.0）
- 跳过异常 batch：检测 loss spike → 跳过该 batch 的更新
- 降低学习率从 checkpoint 恢复

### 10.2 学习率调度

现代 LLM 训练几乎清一色使用 **warmup + cosine decay**：

```python
def lr_schedule(step, warmup_steps, total_steps, max_lr, min_lr):
    if step < warmup_steps:
        # 线性 warmup：从 0 线性增长到 max_lr
        return max_lr * step / warmup_steps
    else:
        # Cosine decay：cos 曲线从 max_lr 衰减到 min_lr
        progress = (step - warmup_steps) / (total_steps - warmup_steps)
        return min_lr + 0.5 * (max_lr - min_lr) * (1 + cos(pi * progress))
```

**为什么需要 warmup？** 在训练初期，模型权重是随机的，梯度方向变化剧烈。直接使用大学习率会导致参数被推向随机方向。warmup 给模型时间建立稳定的梯度模式。

Warmup 步数通常是总步数的 1-5%（如 2000 / 100000 步）。

**为什么用 cosine decay？** 相比于阶梯式衰减，cosine 在训练末期更平滑地降低学习率，有助于在损失曲面的最优点附近做精细搜索。

### 10.3 AdamW 优化器

LLM 训练的标配优化器：

$$\mathbf{g}_t = \nabla_\theta \mathcal{L}(\theta_{t-1})$$
$$\mathbf{m}_t = \beta_1 \mathbf{m}_{t-1} + (1-\beta_1) \mathbf{g}_t$$
$$\mathbf{v}_t = \beta_2 \mathbf{v}_{t-1} + (1-\beta_2) \mathbf{g}_t^2$$
$$\hat{\mathbf{m}}_t = \frac{\mathbf{m}_t}{1-\beta_1^t}, \quad \hat{\mathbf{v}}_t = \frac{\mathbf{v}_t}{1-\beta_2^t}$$
$$\theta_t = \theta_{t-1} - \eta \frac{\hat{\mathbf{m}}_t}{\sqrt{\hat{\mathbf{v}}_t} + \epsilon} - \eta \lambda \theta_{t-1}$$

注意最后一项是 **解耦权重衰减**（decoupled weight decay）——AdamW 相比 Adam 的关键改进：权重衰减直接在参数更新中应用，而不是混入自适应学习率中。这使得正则化强度与学习率解耦。

标准超参数：
- $\beta_1 = 0.9, \beta_2 = 0.95$（LLaMA 的配置）
- $\lambda = 0.1$（权重衰减系数）
- $\epsilon = 10^{-8}$

### 10.4 梯度检查点

训练大模型时，激活值（前向传播的中间结果）的显存占用经常超过参数本身。对于 $L$ 层、序列长度 $n$、hidden size $d$ 的 Transformer：

- 每层激活值约为 $O(n \cdot d)$ 个元素（每个 token 在每层的隐藏状态）
- Attention 层的激活值还包括 $n \times n$ 的注意力矩阵（虽然 Flash Attention 通过不存储它解决了这个问题）

**Gradient Checkpointing**（又称 activation recomputation）的核心 trade-off：不在前向传播时存储所有中间激活值，而是在反向传播时按需重新计算它们。

- 内存节省：约 $\sqrt{L}$（如果每 $\sqrt{L}$ 层存一个 checkpoint）
- 计算代价：约 33% 额外的前向计算（需要重新计算被丢弃的激活值）
- **净收益**：用 33% 的计算时间换取 50-75% 的显存节省——几乎总是值得的

LLaMA 使用的技巧：手动编写反向函数（而非依赖 PyTorch 的 autograd），以便在前向传播时重叠激活值计算和 GPU 间通信。

### 10.5 训练超参数速查

| 超参数 | 典型值 | 说明 |
|--------|--------|------|
| 学习率最大值 | 1.5e-4 — 3e-4 | 大模型用低值 |
| 学习率最小值 | 最大值的 10% | cosine decay 终点 |
| Batch size | 1M — 4M tokens | 全局 batch（所有 GPU 合计） |
| Warmup 步数 | 1000 — 2000 | 线性 warmup |
| 权重衰减 | 0.1 | AdamW 的解耦衰减 |
| 梯度裁剪 | 1.0 | 裁剪梯度的 L2 范数 |
| Adam $\beta_1$ | 0.9 | 一阶矩的动量 |
| Adam $\beta_2$ | 0.95 | 二阶矩的动量 |
| Dropout | 0.0 | 现代 LLM 通常不用 dropout |
| 序列长度 | 2048 — 8192 | 越长显存需求越大 |

> 注意：现代 LLM（LLaMA, GPT-3+）基本**不使用 dropout**。原因：数据量大到模型不会过拟合，且 dropout 会降低训练速度。

---

## 第二幕小结

预训练=数据+规模+工程：
- **数据工程**（§7）：从原始 CommonCrawl 提取 10% 的可用数据，经过清洗、去重、混合、打包，最终喂给模型
- **Scaling Laws**（§8）：${N_{\text{opt}} \propto C^{0.5}, D_{\text{opt}} \propto C^{0.5}}$——Chinchilla 告诉我们模型和数据应等比例增长
- **分布式训练**（§9）：3D 并行（DP+TP+PP）+ ZeRO 分片 = 万亿参数训练的基础设施
- **训练稳定**（§10）：warmup+cosine、梯度裁剪、AdamW、checkpointing——让训练在 10000 GPU 上稳定运行几个月的工程魔法

第三幕我们将看到，训练好的基础模型如何通过**对齐**变成真正可用的产品。

---

## 第三幕：对齐 — 让模型说人话

---

## 第十一章：监督微调 (SFT)

> 预训练的语言模型只会"续写文本"。它不知道什么时候该回答、什么时候该反问、什么时候该拒绝回答。SFT 是让它学会"与人对话"的第一道工序。

### 11.1 从续写到对话

预训练模型在 prompt "解释一下量子力学" 后面会续写什么？它可能续写一段关于量子力学的解释，也可能续写 "这是一道常见的物理考试题..."，还可能续写完全无关的内容。

SFT 的目标是将模型从"续写模式"切换到"指令执行模式"。方法是：收集一批 (指令, 理想回答) 的数据对，在基础模型上继续训练（通常 1-3 个 epoch）。

$$\mathcal{L}_{\text{SFT}} = -\sum_{(x,y) \in \mathcal{D}_{\text{SFT}}} \log p_\theta(y \mid x)$$

注意：只计算 $y$（回答）部分的损失，$x$（指令）部分的损失被 mask 掉。

### 11.2 SFT 数据的构建

SFT 的质量上限取决于数据。构建 SFT 数据的常见方法：

1. **人工标注**：雇人到平台上写理想的对话。最贵但最靠谱。OpenAI 使用了约 13K 条人工 SFT 数据来训练 InstructGPT。

2. **Self-Instruct**（Wang 2022）：用强模型生成指令，再用同一模型生成回答，然后用规则/模型过滤低质量样本。极大降低了数据成本。

3. **蒸馏（Distillation）**：用商业大模型（GPT-4, Claude）生成 SFT 数据，然后用来训练开源小模型。这在技术上是有效但存在法律灰色地带（多数商业模型的服务条款禁止用输出来训练竞争模型）。

数据格式通常如下：

```json
{
  "messages": [
    {"role": "system", "content": "你是一个有帮助的助手。"},
    {"role": "user", "content": "解释一下光合作用"},
    {"role": "assistant", "content": "光合作用是植物利用光能将..."}
  ]
}
```

多轮对话数据会包含交替的 user/assistant 消息，模型被训练为只预测 assistant 的回复。

### 11.3 LIMA：少即是多

> Zhou et al., *LIMA: Less Is More for Alignment* (2023)

LIMA（Less Is More for Alignment）提出了一个令人惊讶的发现：**仅用 1000 条高质量 SFT 数据，就能在很大程度上对齐一个预训练模型**。

关键论点：
- 预训练阶段模型已经学到了大量的知识和语言能力
- 对齐主要是教会模型**格式**（用户→助手）和**风格**（有帮助、无害）
- 因此，多样性和质量远比数量重要

LIMA 实验：从社区论坛（Stack Exchange, wikiHow）精心挑选了 1000 条高质量的问答对，对 LLaMA 65B 做 SFT。结果在 43% 的对比测试中，LIMA 的回复被人类偏好等同于或优于 GPT-4。

**实用启示**：与其收集 100K 条平庸的 SFT 数据，不如精心制作 1K 条优质数据。SFT 阶段的过多样本会导致过拟合（模型记住特定回复而非学习通用行为）。

### 11.4 SFT 的局限

SFT 虽然有效，但有根本局限：

1. **分布偏移**：SFT 教会模型模仿数据中的回复，但无法处理模型在推理时自己产生的错误分布
2. **无法区分好坏**：SFT 对所有训练样本一视同仁——"好的回复"和"不太好的回复"在损失函数中没有区别
3. **幻觉问题**：SFT 不能教会模型"不知道时应该说不"——事实上，SFT 数据中的回复几乎总是提供答案的，这可能强化了模型"无论如何都要回答"的倾向

这些局限正是 RLHF 和 DPO 要解决的问题。

---

## 第十二章：RLHF — 从人类偏好学习

> RLHF（Reinforcement Learning from Human Feedback）是 ChatGPT 成功的核心秘诀。它让模型不仅能回答问题，而且能回答得更"好"——更有用、更安全、更符合人类期望。

### 12.1 RLHF 三段式

```
基础模型 → [1] SFT → [2] Reward Model → [3] PPO 优化 → 对齐模型
```

**阶段 1：SFT**
用高质量的人工对话数据做监督微调，教会模型基本的对话格式和风格。

**阶段 2：奖励模型（Reward Model, RM）**
- 用 SFT 模型对每个 prompt 生成多个不同回复
- 人工标注员比较两个回复（A vs B），选出更好的
- 用这些"偏好对"训练一个奖励模型——输入是 (prompt, response)，输出是一个标量奖励分数

$$\mathcal{L}_{\text{RM}} = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} [\log \sigma(r_\theta(x, y_w) - r_\theta(x, y_l))]$$

其中 $y_w$ 是更好的回复，$y_l$ 是更差的回复。这个损失函数来自 **Bradley-Terry 偏好模型**：

$$p(y_w \succ y_l \mid x) = \frac{\exp(r(x, y_w))}{\exp(r(x, y_w)) + \exp(r(x, y_l))} = \sigma(r(x, y_w) - r(x, y_l))$$

奖励模型本质上是一个"偏好预测器"——预测人类更喜欢哪个回复。

**阶段 3：PPO 微调**
用奖励模型作为奖励信号，用 Proximal Policy Optimization (PPO) 优化 SFT 模型：

$$\mathcal{J}_{\text{PPO}} = \mathbb{E}_{(x,y)\sim \pi_\theta} [r(x, y) - \beta \cdot \text{KL}(\pi_\theta(y|x) \| \pi_{\text{SFT}}(y|x))]$$

- 第一项 $r(x,y)$：奖励模型给的分数，鼓励生成高质量回复
- 第二项 $\beta \cdot \text{KL}$：KL 散度惩罚，防止模型偏离 SFT 模型太远（防止"奖励黑客"——模型找到奖励模型的高分漏洞而非真正的好回复）

**PPO-ptx 变体**（InstructGPT 使用）额外加入预训练损失，防止模型在 NLP 公共基准上性能退化（对齐税）：

$$\mathcal{J}_{\text{PPO-ptx}} = \mathcal{J}_{\text{PPO}} + \gamma \cdot \mathbb{E}_{x \sim \mathcal{D}_{\text{pretrain}}} [\log \pi_\theta(x)]$$

### 12.2 奖励模型的工程细节

**为什么用比较（pairwise）而非评分（pointwise）？**
- 标注员之间对"这个回复打几分"差异巨大（有人偏严有人偏松）
- 但"回复 A 比回复 B 更好"更容易达成共识（标注员间一致性 ~73%）

**奖励模型的大小**：InstructGPT 发现 6B 的 RM 比 175B 的 RM 更稳定。更大的 RM 在训练中容易不稳定（可能因为偏好数据量不足以支撑大模型的参数空间）。

**奖励模型的泛化**：标注数据来自少数标注员（~40人），但训练出来的 RM 在 held-out 标注员的数据上表现仍然不错（69.6% vs 72.4% 准确率）——说明 RM 学到的是"人类通用的偏好"而非"特定标注员的个人偏好"。

### 12.3 PPO 在 RLHF 中的角色

> PPO 和 GRPO 的完整数学推导在 [RL 完全教程](../RL-Tutorial) 中有详细展开。这里只给出 RLHF 语境下的关键要点。

PPO 的 clipped 目标函数：

$$\mathcal{L}^{\text{CLIP}} = \min(r_t(\theta) \hat{A}_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) \hat{A}_t)$$

其中 $r_t(\theta) = \pi_\theta(a_t|s_t) / \pi_{\text{old}}(a_t|s_t)$ 是概率比，$\hat{A}_t$ 是优势估计，$\epsilon$ 通常为 0.2。

在 RLHF 中，PPO 需要额外维护一个 **Critic 网络**（价值函数）来估计基线，用于计算优势。这增加了约 1.5× 的显存开销。

### 12.4 InstructGPT 的核心发现

1. **对齐 vs 规模的分离**：1.3B 的 InstructGPT 在人类偏好上被判断优于 175B 的 GPT-3。对齐可以极大地弥补规模的不足。

2. **对齐税（Alignment Tax）**：PPO 在提升对齐度的同时，在某些学术基准（如 NLP 任务）上性能略微下降。PPO-ptx（混合预训练目标）可以缓解这个问题。

3. **泛化能力**：尽管 96% 的训练数据是英文，对齐后的模型在非英文语言和代码任务上也表现出改善。人类偏好信号跨越了语言边界。

4. **真实性提升**：InstructGPT 在 TruthfulQA 上的幻觉率约为 GPT-3 的一半。

---

## 第十三章：DPO — 绕过奖励模型的捷径

> RLHF 的三段式流水线（SFT → RM → PPO）工程复杂度极高。训练一个奖励模型，再用 RL 优化——能不能直接把人类偏好信号注入到 SFT 中？DPO 说：可以。

### 13.1 DPO 的数学推导

> Rafailov et al., *Direct Preference Optimization* (NeurIPS 2023)

DPO 的起点是一个数学洞察。回顾 RLHF 中 PPO 阶段的目标：

$$\max_\pi \mathbb{E}_{y \sim \pi}[r(x, y)] - \beta \cdot D_{KL}(\pi \| \pi_{\text{ref}})$$

这个 KL 约束优化问题有**闭式解**（这是 DPO 的核心）：

$$\pi^*(y|x) = \frac{1}{Z(x)} \pi_{\text{ref}}(y|x) \exp\left(\frac{1}{\beta} r(x, y)\right)$$

其中 $Z(x) = \sum_y \pi_{\text{ref}}(y|x) \exp(r(x,y)/\beta)$ 是归一化因子。

反过来，我们可以把奖励函数表示为策略的函数：

$$r(x, y) = \beta \log\frac{\pi^*(y|x)}{\pi_{\text{ref}}(y|x)} + \beta \log Z(x)$$

**这就是 DPO 的关键变换**：语言模型本身就是（隐式的）奖励模型！

代入 Bradley-Terry 偏好模型，$Z(x)$ 奇迹般地约掉了：

$$p(y_w \succ y_l | x) = \sigma\left(\beta \log\frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log\frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)$$

最终得到 DPO 损失——一个简单的交叉熵损失：

$$\mathcal{L}_{\text{DPO}} = -\mathbb{E}_{(x, y_w, y_l)} \left[\log \sigma\left(\beta \log\frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log\frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)\right]$$

**不需要 RM，不需要 PPO，不需要 Critic 网络**。就是一个带有参考模型的二元交叉熵。

**DPO 的梯度揭示了它的工作机制**：

$$\nabla_\theta \mathcal{L}_{\text{DPO}} = -\beta \cdot \mathbb{E}\left[\sigma(\hat{r}_\theta(y_l) - \hat{r}_\theta(y_w)) \cdot (\nabla_\theta \log \pi_\theta(y_w|x) - \nabla_\theta \log \pi_\theta(y_l|x))\right]$$

其中 $\hat{r}_\theta(y) = \beta \log \frac{\pi_\theta(y|x)}{\pi_{\text{ref}}(y|x)}$ 是隐式奖励。

梯度做了三件事：
1. 权重由模型犯错程度决定——当模型给 $y_l$ 打更高分时，权重更大（$\sigma$ 接近 1）
2. 增大更好的回复 $y_w$ 的概率
3. 减小更差的回复 $y_l$ 的概率

### 13.2 DPO vs RLHF

| 维度 | RLHF (PPO) | DPO |
|------|-----------|-----|
| 训练阶段 | 3（SFT + RM + PPO） | 1（有偏好数据即可） |
| 需要奖励模型 | 是 | 否 |
| 需要在线采样 | 是（PPO 需要用当前策略生成） | 否（纯离线数据） |
| 实现复杂度 | 高（4个模型同时运行） | 低（2个模型：当前 + 参考） |
| 训练稳定性 | 需要调 $\beta$ 和 clip 范围 | 相对稳定 |
| 绝对性能 | 理论上限更高（在线探索） | 接近 RLHF |
| 数据需求 | 偏好数据 + online generation | 仅偏好数据 |

DPO 的最大优势是实现简单——它就是一个带约束的 SFT。这使得 DPO 在开源社区迅速普及。2024 年，大多数开源 chat 模型（Zephyr, Qwen-Chat, Mistral-Instruct 等）都使用了某种形式的 DPO。

### 13.3 DPO 的改进与变体

DPO 有几个已知弱点，后续工作提出了改进：

- **IPO**（Azar 2023）：DPO 的最优 $\beta$ 依赖于数据噪声水平。IPO 提供了无超参数的版本。
- **KTO**（Ethayarajh 2024）：不需要偏好对，只需要单条回复的好/坏标签。更适合实际标注场景（标注员更愿意打 1-5 分而非做两两比较）。
- **SimPO**（Meng 2024）：去掉参考模型的需求，直接以序列平均对数概率作为隐式奖励。
- **ORPO**（Hong 2024）：将 SFT 和偏好优化合并为一个阶段，同时优化指令跟随和偏好对齐。

### 13.4 何时用 DPO，何时用 RLHF？

一个启发式决策树：

- 数据是偏好对（pairwise）且不需要在线交互 → **DPO**
- 有机制可以进行在线采样（模型生成回复 → 奖励打分 → 更新） → **RLHF 可能更好**
- 只需要"风格对齐"（礼貌、无害） → **DPO 足够**
- 需要"能力对齐"（复杂推理、多步工具使用） → **RLHF/GRPO**（在线探索帮助模型发现更好的推理路径）
- 对"最优回复"有明确的规则定义 → **GRPO**（用规则奖励，不需要奖励模型）

---

## 第十四章：推理模型的崛起

> 2024-2025 年是 LLM 对齐的转折点——从让模型"说好话"到让模型"想清楚"。o1 和 DeepSeek-R1 证明了：用强化学习训练模型进行长程推理，可以获得远超 prompt engineering 的推理能力。

### 14.1 范式转变：推理即训练

此前，提升推理能力的主流方法是**提示工程**（CoT, Self-Consistency, ToT 等）。这些方法让模型在推理时"多想想"，但推理策略本身是模型已有的能力，只是被激活而已。

2024-2025 年的新范式是：**通过强化学习把推理能力"写入"模型权重**。模型在 RL 训练中自发学会生成长推理链、自我验证、回溯修正——不是因为被提示这么做，而是因为这么做能获得更高的奖励。

OpenAI o1（2024）和 DeepSeek-R1（2025）是这一范式的两大里程碑。

### 14.2 DeepSeek-R1：纯 RL 训练的推理

> DeepSeek, *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning* (2025)

DeepSeek-R1 的最大胆实验是 **R1-Zero**：**不做任何 SFT，直接在 DeepSeek-V3-Base 上用 RL 训练推理能力**。

奖励设计非常简单（rule-based，不需要奖励模型）：
- **正确性奖励**：对于数学题，检查最终答案是否正确
- **格式奖励**：要求推理过程放在 `think` 和 `answer` 标签中

$$\text{reward} = \text{correctness\_reward} + \text{format\_reward}$$

训练算法用 **GRPO**（Group Relative Policy Optimization），不要 Critic 网络，用组内相对标准化估计优势：

$$\hat{A}_{i,t} = \frac{r_i - \text{mean}(\{r_1, ..., r_G\})}{\text{std}(\{r_1, ..., r_G\})}$$

其中每个 prompt 采样 $G$ 个输出（$G=64$），$r_i$ 是第 $i$ 个输出的奖励。

**R1-Zero 的 "Aha Moment"**：在训练约 8000 步时，模型出现了一个令人震惊的自发行为——在生成推理链的中途插入了"等等，让我重新检查一下"这样的自我验证语句，然后修正了之前的错误。这种行为没有被编程或提示——是纯 RL 训练中涌现的。

但 R1-Zero 也有问题：推理链可读性差、中英混杂、格式不稳定。

**R1 的四阶段完整训练**：

```
阶段 1：冷启动 SFT
  └→ 用几千条高质量的（带推理链的）人工数据做 SFT
  └→ 让模型学会"用清晰的格式推理"

阶段 2：推理 RL（GRPO）
  └→ 在数学/代码/科学推理任务上做 GRPO
  └→ 大幅提升推理能力

阶段 3：拒绝采样 + SFT
  └→ 用阶段 2 的模型生成大量数据
  └→ 过滤出正确的推理链
  └→ 加上写作/问答/翻译等通用数据
  └→ 做 SFT → 兼得推理能力和通用能力

阶段 4：全场景 RL
  └→ 在所有类型任务上做 RL
  └→ 提升有用性 + 无害性
```

关键结果：R1 在 AIME（美国数学邀请赛）上的得分从 ~15% 提升到 ~78%。

### 14.3 s1：极简测试时规模化

> Muennighoff et al., *s1: Simple Test-Time Scaling* (2025)

s1 的核心发现：仅用 **1000 条精心挑选的推理数据** + **强制延长思考时间**（Budget Forcing），就能获得与完整 RL 训练相当的测试时推理能力。

Budget Forcing 是 s1 的关键技巧：在推理时，强制模型继续生成（插入 "Wait" token 或抑制 EOS），直到达到预设的思考长度。效果：模型被迫进行更多推理步骤，最终答案的准确率提升。

这揭示了一个深刻的事实：基础模型内部已经存在推理能力，只是通常不会充分使用。s1 的 1000 条数据的作用是"教会模型开关"——何时、如何调用这个能力。

### 14.4 推理模型的开放问题

- **过度思考（Overthinking）**：对于简单问题，模型也会生成数百字的推理链。浪费计算且显得"啰嗦"。
- **语言混杂**：RL 训练中缺乏语言一致性约束，导致推理链可能中英混杂。
- **推理忠实性**：模型的推理链可能只是"看起来合理"，与模型实际决策的原因不一致。
- **安全性**：推理能力可能被用于恶意目的（如生成攻击代码的设计思路）。o1 的系统卡专门讨论了这一点。

> 推理模型的更完整分析——包括 GRPO 算法推导、OpenAI o1 系统卡、以及开源推理生态（Open-Reasoner-Zero, TinyZero, Open R1 等）——请参考 [思维链综述：从提示工程到推理时训练](../cot-survey)。

---

## 第十五章：对齐全景图

### 15.1 对齐技术的决策树

```
你的需求是什么？
│
├─ 只需要格式对齐 → SFT（几千条数据就够了）
│
├─ 需要偏好对齐，有偏好数据 → DPO（简单有效）
│
├─ 需要偏好对齐，有点数数据 → KTO
│
├─ 需要能力提升（推理/数学）→ GRPO + Rule-based Reward
│
└─ 需要全面对齐（有用+无害+真实）→ RLHF 完整流水线
```

### 15.2 对齐的安全性维度

安全对齐（Safety Alignment）是无害性的核心组成：

- **红队测试（Red Teaming）**：雇佣专家尝试攻破模型的安全防线，发现问题后修复
- **Constitutional AI**（Anthropic）：模型根据一套原则（constitution）自我批评和自我改进，减少对人类标注的依赖
- **Deliberative Alignment**（OpenAI o1）：让模型在生成回复前，先对照安全规范"思考"

### 15.3 评估与基准

对齐的效果如何衡量？没有单一的"对齐分数"，而是一张多维度的报告卡：

| 维度 | 常用基准 | 方法 |
|------|---------|------|
| 有用性 | Chatbot Arena, MT-Bench | 人类判断 / LLM-as-judge |
| 真实性 | TruthfulQA, HaluEval | 准确率 |
| 无害性 | ToxicChat, RealToxicityPrompts | 毒性检测 |
| 指令跟随 | IFEval, AlpacaEval | 自动评估 |
| 推理能力 | GSM8K, MATH, HumanEval | 准确率 / Pass@k |

**Chatbot Arena**（LMSYS）是最有影响力的众包评估平台。用户与两个匿名模型同时对话，投票选出更好的回复。用 Elo 评分排名。截至 2026 年，Arena 已收集超过 200 万次人工判断，Elo 排名被认为是最接近"真实用户偏好"的指标。

**LLM-as-Judge**：用 GPT-4 等强模型评判其他模型的回复质量。研究显示与人类判断的相关系数达 0.8+，但在某些细微维度（如创造力、幽默感）上仍有差距。

---

## 第三幕小结

对齐是预训练模型从"能用"到"好用"的最后一道工序：
- **SFT**（§11）：教会模型对话格式和基本风格，千条高质量数据可能就够
- **RLHF**（§12）：三段式（SFT→RM→PPO），让模型学习人类偏好
- **DPO**（§13）：绕过奖励模型和 RL，直接优化偏好——简单且有效
- **推理模型**（§14）：o1/R1/s1 开辟了"用 RL 训练推理"的新范式
- **全景**（§15）：选择哪种对齐方法取决于具体目标和资源

第四幕我们将看到，对齐后的模型如何通过**推理优化**变得能够真正部署到生产环境。

---

## 第四幕：推理优化 — 让模型跑得飞快

---

## 第十六章：KV Cache — 推理加速的基础

> KV Cache 是自回归推理的第一个也是最重要的优化。不理解 KV Cache，就无法理解后续所有推理优化为什么那样设计。

### 16.1 为什么需要 KV Cache？

回顾因果自注意力的计算。在生成第 $t$ 个 token 时：

$$\mathbf{o}_t = \sum_{j=1}^{t} \text{softmax}\left(\frac{\mathbf{q}_t \cdot \mathbf{k}_j}{\sqrt{d_k}}\right)_j \mathbf{v}_j$$

如果不做缓存，每个解码步都需要为所有 $t$ 个历史位置重新计算 $\mathbf{k}_j$ 和 $\mathbf{v}_j$。由于每步只新增 1 个 token，这意味着第 $t$ 步大约有 $t$ 次重复计算（对历史位置的 K 和 V）。总计算量达到 $O(n^3 d)$，其中 $n$ 是总生成长度。

**KV Cache 的洞见**：$\mathbf{k}_j$ 和 $\mathbf{v}_j$ 只依赖于第 $j$ 个 token，一旦算出就不变了。把它存起来！

```
生成第 1 个 token：计算 K1, V1 → 缓存
生成第 2 个 token：读取 K1, V1，计算 K2, V2 → 追加缓存
生成第 3 个 token：读取 K1, V1, K2, V2，计算 K3, V3 → 追加缓存
...
```

每次只需为新 token 计算一次 K 和 V，复杂度降为 $O(n^2 d)$。

### 16.2 KV Cache 的显存分析

KV Cache 的大小公式：

$$\text{KV Cache Size} = 2 \times L \times h \times d_k \times n_{\text{tokens}} \times \text{bytes\_per\_elem}$$

其中：
- 2：K 和 V 各一份
- $L$：层数
- $h$：每层的注意力头数
- $d_k$：每个头的 key/value 维度
- $n_{\text{tokens}}$：已缓存的 token 数
- bytes_per_elem：float16 = 2 bytes

代入具体数字（LLaMA-7B）：

| 参数 | 值 |
|------|-----|
| $L$ | 32 |
| $h$ | 32 |
| $d_k$ | 128 |
| 每 token KV Cache | $2 \times 32 \times 32 \times 128 \times 2 = 524,288 \text{ bytes} \approx 0.5$ MB |

生成 2048 个 token：$0.5 \times 2048 \approx 1$ GB

这看起来还行。但看 GPT-3-175B（$L=96, h=96, d_k=128$）：
每 token KV Cache：$2 \times 96 \times 96 \times 128 \times 2 = 4.7$ MB
2048 token：$4.7 \times 2048 \approx 9.6$ GB

如果上下文是 128K：$4.7 \times 128000 \approx 600$ GB——光是 KV Cache 就超过了单张 H100（80GB）的 7.5 倍。

**KV Cache 是自回归推理的显存瓶颈**。这就是为什么 GQA/MQA/MLA 如此重要——它们直接按倍数压缩这个开销。

### 16.3 批处理对 KV Cache 的放大

实际部署中，通常同时处理多个请求（batch $b > 1$）。每个请求有独立的 KV Cache：

$$\text{Total KV Cache} = 2 \times L \times h \times d_k \times (b \times n_{\text{avg}}) \times 2 \text{ bytes}$$

对于 $L=32, b=64$ 的并发请求，平均长度 512 token：约 32 GB 的 KV Cache 只为注意力服务。

这就是为什么 vLLM 的 PagedAttention 被设计出来——传统系统将 KV Cache 预分配为连续的固定大小块（如每个请求预先分配 2048 个位置的缓存），即使实际只用了几百个位置，造成 60-80% 的显存浪费。

### 16.4 KV Cache 量化

KV Cache 可以量化到更低的精度以进一步节省内存：

- **KV8（INT8）**：将 K 和 V 量化到 8 位整数，内存减半。精度损失很小。
- **KV4（INT4）**：量化到 4 位，损失略大但多数任务可接受。

量化策略：
- **逐 token（per-token）量化**：对每个 token 的 key/value 独立计算 scale
- **逐通道（per-channel）量化**：在 $d_k$ 维度上分组量化
- 实践上，KV8 几乎没有性能下降，KV4 在大多数任务上下降 < 1%

### 16.5 KV Cache 淘汰策略

当上下文超出显存上限时，需要淘汰一部分旧的 KV Cache：

- **滑窗（Sliding Window）**：只保留最近的 $w$ 个 token 的 KV Cache。Mistral 7B 使用了滑窗注意力（$w=4096$），较远的 token 的信息会丢失。
- **StreamingLLM**（Xiao 2023）：保留开头的几个 token（Attention Sinks——模型倾向于大量关注起始 token）+ 滑窗内的最近 token。效果出奇地好。
- **H2O（Heavy Hitter Oracle）**（Zhang 2023）：根据历史注意力权重的累积分数，保留"重击手"（累积注意力最高的 token），淘汰权重几乎为零的 token。
- **SnapKV**（Li 2024）：在生成过程中，观察哪些 token 的注意力权重在多个注意力头之间一致地高，选择保留这些 token。

这些方法本质上都在做同一件事：**不是所有 token 都同等重要，识别并保留重要的那些**。

---

## 第十七章：Flash Attention — IO 感知的精确注意力

> 标准 Attention 的 $O(n^2)$ 显存问题是自回归 Transformer 最核心的瓶颈。Flash Attention 用一个精妙的算法解决了它——不改变 Attention 的数学结果，只改变**计算顺序**。

### 17.1 问题：Memory Wall

GPU 的内存层次：

```
SRAM（片上缓存）: ~20 TB/s, ~100 KB（每个 SM）
    ↑ ~10× 带宽差距
HBM（显存）: ~2 TB/s, 80 GB（A100）
    ↑ ~100× 带宽差距
CPU RAM（内存）: ~50 GB/s, TB 级别
```

标准 Attention 的瓶颈不在计算（$O(n^2 d)$ FLOPs），而在**显存访问**。

计算 $\mathbf{S} = \mathbf{Q}\mathbf{K}^T$：
- 矩阵乘法：$\mathbf{Q}$ 和 $\mathbf{K}$ 从 HBM 读取，$\mathbf{S}$ 写出到 HBM
- Softmax：$\mathbf{S}$ 读回，逐行求 softmax，$\mathbf{P}$ 写出
- 加权聚合：$\mathbf{P}$ 读回，$\mathbf{V}$ 读入，$\mathbf{O}$ 写出

整个过程需要多次读写 $n \times n$ 的注意力矩阵。对于 $n = 2048$，这只是 4M 个元素（16MB）；但对于 $n = 128K$，这是 16B 个元素（32GB）——已经超出了 A100 的显存总量。

**关键洞察**：FLOPs 不慢，显存访问慢。如果能把大矩阵的读写去掉，就可以大幅加速。

### 17.2 Flash Attention (Dao 2022)

Flash Attention 的核心技巧是 **Tiling** + **Recomputation**：

**Tiling（分块计算）**：将 $\mathbf{Q}, \mathbf{K}, \mathbf{V}$ 分割为适合 SRAM 的小块，逐块计算部分结果，累积最终输出。但有个问题——softmax 不是"可交换的"（不能简单地先算一部分再加另一部分）。

**在线 Softmax** 是解决这个问题的关键。回顾 Softmax 的定义：
$$p_i = \frac{\exp(x_i)}{\sum_j \exp(x_j)}$$

如果我们分两批处理（先 $x_1, x_2$，再 $x_3, x_4$），可以先计算第一批的最大值和指数和，然后在处理第二批时更新：

$$m_{\text{new}} = \max(m_{\text{old}}, m_{\text{new}})$$
$$l_{\text{new}} = \exp(m_{\text{old}} - m_{\text{new}}) \cdot l_{\text{old}} + \exp(m_{\text{new}}' - m_{\text{new}}) \cdot l_{\text{new}}'$$

其中 $m = \max(x)$，$l = \sum \exp(x - m)$。最终的 softmax 结果 $= \exp(x_i - m) / l$。

代码伪逻辑：

```python
# 初始状态
O = torch.zeros(N, d)   # 输出
l = torch.zeros(N)      # 指数和 (softmax 分母)
m = torch.full(N, -inf) # 当前最大值

# 逐块处理 K, V
for j in range(num_kv_blocks):
    K_j = load_K_block(j)
    V_j = load_V_block(j)
    
    for i in range(num_q_blocks):
        Q_i = load_Q_block(i)
        
        # 计算部分注意力分数
        S_ij = Q_i @ K_j.T / sqrt(d_k)
        m_new = max(m_i, row_max(S_ij))
        
        # 更新指数和
        P_ij = exp(S_ij - m_new)
        l_new = exp(m_i - m_new) * l_i + row_sum(P_ij)
        
        # 更新输出
        O_i = diag(exp(m_i - m_new)) * O_i + P_ij @ V_j
        
        # 保存状态
        m_i = m_new
        l_i = l_new
```

**Recomputation（重计算）**：反向传播时需要 $\mathbf{S}$ 和 $\mathbf{P}$，但前向传播时没有把它们存入 HBM。解决方法：在反向时从保存的 $\mathbf{Q}, \mathbf{K}, \mathbf{V}$ 和 softmax 统计量 $(m, l)$ 中**重新计算** $\mathbf{S}$ 和 $\mathbf{P}$。这比存储然后读取更快（因为 S 非常大而 Q、K、V 相对小）。

**IO 复杂度**：
- 标准 Attention：$\Theta(Nd + N^2)$ HBM 访问
- Flash Attention：$\Theta(N^2 d^2 / M)$ HBM 访问，其中 $M$ 是 SRAM 大小
- 对于 $d=64-128$ 且 $M$ ~ 100KB，Flash Attention 的 HBM 访问量可以减少 5-10×

**关键结果**：
- 训练速度：GPT-2 3× 快于 HuggingFace 实现
- 显存：从 $O(N^2)$ 降到 $O(N)$
- 首次让 Transformer 在 Path-X（16K 序列长度）上超过随机水平（61.4%）

### 17.3 Flash Attention 2 (Dao 2023)

FA2 在 FA1 上做了三个关键改进，将 GPU 利用率从 30-50% 提升到 ~73%：

1. **减少非矩阵乘法的 FLOPs**：在线 softmax 中有大量除法、指数运算。FA2 优化了统计量维护，减少每次迭代的非乘加运算。这在 A100 上特别重要——矩阵乘法（312 TFLOPS）比非乘加运算（19.5 TFLOPS）快 16 倍。

2. **在序列长度维度上并行**：FA1 只在 batch 和 head 维度上并行。对于长序列小 batch 的情况，并行度不够。FA2 额外在序列长度（Q 的行）维度上并行。

3. **更好的 work partitioning**：FA1 在 warp 之间用"split-K"（分割 K），需要 warp 间通信。FA2 改用"split-Q"（分割 Q），消除了 warp 间通信。

### 17.4 实践：如何使用 Flash Attention

在现代 PyTorch 中，Flash Attention 已经深度集成：

```python
# PyTorch 2.0+ 自动使用 Flash Attention
# scaled_dot_product_attention 会根据输入自动选择最优后端
from torch.nn.functional import scaled_dot_product_attention

output = scaled_dot_product_attention(query, key, value, is_causal=True)
```

支持的框架：
- **PyTorch**：通过 `torch.nn.functional.scaled_dot_product_attention`（2.0+）
- **HuggingFace Transformers**：自动检测并使用 Flash Attention 2
- **vLLM**：内置 Flash Attention 支持
- **llama.cpp**：使用自己的 CUDA kernel（不依赖 Flash Attention 库）

---

## 第十八章：模型量化

> 175B 的权重需要 ~350GB（FP16）。如果能把精度降到 4-bit，同样的模型只需要约 88GB——两块 A100 就能装下。量化是实现"大模型消费级部署"的核心技术。

### 18.1 量化的基础

量化是将浮点权重和激活值映射到低精度整数表示。最常见的两种量化：

**对称量化**：
$$x_q = \text{round}\left(\frac{x}{s}\right) \cdot s, \quad s = \frac{\max(|x|)}{2^{b-1}-1}$$

其中 $s$ 是 scale factor，$b$ 是位宽。INT8 的范围是 $[-127, 127]$，以 0 对称。

**非对称量化**：
$$x_q = \text{round}\left(\frac{x - z}{s}\right), \quad s = \frac{\max(x) - \min(x)}{2^b - 1}$$

其中 $z$ 是零点（zero point）。非对称量化能更好地利用范围，但引入了额外的零点参数。

**量化粒度**：

| 粒度 | 描述 | 精度 | 开销 |
|------|------|------|------|
| 逐张量 (per-tensor) | 整个张量共享一个 scale | 最粗 | 最少 |
| 逐通道 (per-channel) | 每个输出通道独立 scale | 较好 | 较小 |
| 逐组 (per-group) | 每 128 个权重一组 | 最好 | 较多 |

### 18.2 GPTQ：基于二阶信息的逐层量化

> Frantar et al., *GPTQ: Accurate Post-Training Quantization for Generative Pre-Trained Transformers* (2022)

GPTQ 是 LLM 量化的里程碑工作。其核心思想借鉴了 **Optimal Brain Surgeon (OBS)** 剪枝算法。

**问题设置**：给定一层权重 $\mathbf{W} \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}}$，逐行量化。量化第 $q$ 行时，会引入误差 $\Delta \mathbf{w}_q = \mathbf{w}_q - \hat{\mathbf{w}}_q$。但简单的逐行量化没有考虑到：量化第 $q$ 行后，可以通过调整同一层中**后续行的权重**来补偿误差。

**GPTQ 的做法**：利用该层输入的**逆 Hessian 矩阵**来估计每一行权重的"补偿能力"。

- 计算输入激活的 Hessian：$\mathbf{H} = 2\mathbf{X}\mathbf{X}^T$（加正则化 $\lambda \mathbf{I}$）
- 对 Cholesky 分解后的 Hessian，逐行量化
- 量化每行后，用 Hessian 信息更新未量化的行，补偿量化误差

**效果**：GPTQ 能在 4-bit 精度下保持模型质量接近原始水平。OPT-175B 在 INT4 下的 perplexity 仅从 10.78 升到 11.19（损失不到 4%）。

**运行速度**：量化一个 175B 模型需要约 4 个 GPU 小时（相比训练消耗的 ~355 GPU-years，微不足道）。

### 18.3 AWQ：激活感知量化

> Lin et al., *AWQ: Activation-Aware Weight Quantization for LLM Compression* (2023)

AWQ 建立在一个关键观察上：**不是所有权重都同等重要**。有些权重通道与异常大的激活值（outlier channels）关联，量化它们会造成灾难性损失。

**核心发现**：对于 LLM，只有约 1% 的权重是"显著"的（salient），保护它们就能保持量化质量。显著通道的特点是激活值异常大——这意味着它们被乘以的值更大，量化的相对误差会被放大。

**AWQ 的方案——按通道缩放（Per-Channel Scaling）**：

不要对"显著"通道做静态保护（那需要存储额外的 FP16 权重），而是利用激活的分布信息，将量化困难的通道的权重**放大**，相应的激活值**缩小**（在上一层操作），从而有效减少量化误差。

$$\mathbf{W}' = \mathbf{W} \cdot \text{diag}(\mathbf{s}), \quad \mathbf{X}' = \text{diag}(\mathbf{s}^{-1}) \cdot \mathbf{X}$$

其中 $s_i$ 是第 $i$ 个通道的缩放因子（基于激活值的大小计算）。缩放不改变 $\mathbf{W}\mathbf{X}$ 的数学结果（$(\mathbf{W} \cdot \mathbf{S})(\mathbf{S}^{-1} \cdot \mathbf{X}) = \mathbf{W}\mathbf{X}$），但可以显著改变量化难度。

**效果**：AWQ 在 4-bit 下的 perplexity 显著优于 GPTQ，且不需要校准数据集的梯度信息。

### 18.4 量化方法对比

| 方法 | 位宽 | 需要校准 | 与原始模型差距 | 速度 | 工具 |
|------|------|---------|--------------|------|------|
| GPTQ | INT4 | 是 | ~0.3 PPL | 快 | AutoGPTQ |
| AWQ | INT4 | 是 | ~0.2 PPL | 快 | AutoAWQ |
| bitsandbytes (NF4) | INT4 | 否 | ~0.1 PPL | 中 | bitsandbytes |
| GGUF/GGML | INT4—INT8 | 是 | ~0.3 PPL | 快（CPU） | llama.cpp |
| FP8 (native) | FP8 | 否 | 极小 | 最快 | 需 H100+ |

### 18.5 llama.cpp 与 GGUF

llama.cpp 是一个令人惊叹的项目：在消费级 CPU/GPU 上高效运行 LLM 推理。它使用 **GGUF** 格式存储量化模型。

GGUF 的量化方案多样：
- **Q4_0 / Q4_1**：4-bit 量化，block size 32
- **Q5_0 / Q5_1**：5-bit
- **Q8_0**：8-bit
- **Q2_K / Q3_K / Q4_K / Q5_K / Q6_K**：K-quant，使用混合精度（不同层不同位宽，重要层用高精度）

实践建议：
- 追求最小模型 → Q4_K_M（4-bit 混合，约 4-5 bits/weight）
- 质量速度平衡 → Q5_K_M
- 追求最高质量 → Q8_0

### 18.6 量化与部署速查

| 硬件 | 推荐方案 |
|------|---------|
| MacBook M1/M2 (16GB) | llama.cpp GGUF Q4_K_M, LLaMA-7B |
| RTX 3090 (24GB) | AWQ/GPTQ INT4, LLaMA-13B 或 Mistral 7B |
| RTX 4090 (24GB) | AWQ INT4, LLaMA-33B 或 Qwen-14B |
| A100 (80GB) | FP16/FP8, LLaMA-70B |
| H100 (94GB) | FP8, DeepSeek-V3（需多卡） |

---

## 第十九章：投机解码

> 自回归生成受限于内存带宽（memory bandwidth bound），而非计算能力。投机解码（Speculative Decoding）是突破这个瓶颈的巧妙方法。

### 19.1 问题诊断

自回归解码的每一步只处理一个 token。对于 LLaMA-7B，一次前向传播处理 2048 个 token（prefill 阶段）和只处理 1 个新 token（decode 阶段）的 FLOPs 差不多，但**显存带宽利用率**天差地别：
- Prefill（2048 token）：~40% 带宽利用率
- Decode（1 token）：~2-5% 带宽利用率

大部分时间 GPU 在等数据从 HBM 加载到计算单元，而非在计算。

### 19.2 投机解码的基本原理

**核心思想**：用一个小的、快速的"草稿模型"（draft model）预先生成 $K$ 个候选 token，然后用大模型（target model）**一次性验证**这 $K$ 个 token。

算法：
```
1. Draft Model 自回归生成 K 个候选 token（y_1, y_2, ..., y_K）
2. Target Model 做一次前向传播，输入 [x, y_1, ..., y_K]
   输出每个位置的概率分布 p_target
3. 逐位置比较 p_draft 和 p_target：
   - 如果 p_draft(y_i) ≤ p_target(y_i)：接受 y_i
   - 如果 p_draft(y_i) > p_target(y_i)：以概率 p_target/p_draft 接受，否则拒绝
   - 第一个被拒绝的位置：从 p_target 中采样替代
```

**数学保证**（Leviathan et al. 2022 证明）：投机解码的输出分布与实际自回归模型完全一致。它不是近似——只要概率比正确，接受/拒绝规则保证精确等价。

### 19.3 加速比分析

加速比取决于 draft model 的"命中率"（acceptance rate）：

$$\text{加速比} = \frac{1 + \alpha \cdot K}{1 + K/d}$$

其中 $\alpha$ 是接受率，$K$ 是草稿长度，$d$ 是 draft model 与 target model 的速度比。典型情况：
- $\alpha \approx 0.8$（草稿模型很准），$K=5$，$d=50$（草稿模型快 50×）
- 理论加速：$(1 + 0.8 \times 5) / (1 + 0.1) \approx 4.5\times$

实际部署中常见获得 2-3× 的加速。

### 19.4 草稿模型的选择

- **独立小模型**：用一个精通的模型（如 LLaMA-160M）作草稿模型，搭配 LLaMA-7B 主模型。最常用。
- **Medusa**（Cai 2023）：在目标模型上附加多个"头"（额外的小型输出层），用于同时预测未来的多个 token。不需要独立草稿模型。
- **Eagle**（Li 2024）：利用 transformer 的中间层特征（而非最终输出）来预测未来 token，获得了比 Medusa 更高的接受率。
- **Self-Speculative**：用目标模型自身的部分层（如只用前 6 层）作为草稿模型。无需额外训练。

### 19.5 系统实现

投机解码在生产中面临的挑战：
- **batch decoding**：多个请求同时进行时，draft model 和 target model 的调度需要仔细设计
- **KV Cache 管理**：草稿 token 被拒绝后，其 KV Cache 需要丢弃——浪费了一些计算
- **树状草稿（Tree Drafting）**：更激进的做法是让草稿模型生成一棵候选树（而非单链），target model 并行验证所有分支

---

## 第二十章：推理系统架构

> 写一个能跑的 LLM 推理脚本只需 50 行 Python。写一个能服务百万用户的推理系统，需要用到的系统设计原理不亚于一个数据库。

### 20.1 PagedAttention (vLLM)

> Kwon et al., *Efficient Memory Management for Large Language Model Serving with PagedAttention* (SOSP 2023)

vLLM 的 PagedAttention 将操作系统的虚拟内存思想搬到了 KV Cache 管理上。

**传统系统的问题**：KV Cache 被预分配为固定大小（如每个请求 2048 个位置）。实际使用中：
- 短回复（50 个 token）只用了 50 个位置 → 浪费了 1954 个位置
- 长回复如果需要超过 2048 → 直接崩溃

**PagedAttention 的方案**：将 KV Cache 划分为固定大小的"页面"（blocks，通常每块 16 个 token）。KV Cache 不需要在物理显存上连续，通过一个 Block Table 做逻辑块到物理块的映射：

```
Request A 的逻辑 KV 块: [0] → [1] → [2] → [3]
                          ↓     ↓     ↓     ↓
物理 KV 块:              [P5]  [P2]  [P9]  [P1]
```

按需分配——只在上一块用完时才分配新块。内部碎片最多 1 个块（最后一块没填满的部分）。

**效果**：内存利用率从传统系统的 20-38% 提升到 96.3%。意味着同样的 GPU 可以服务 3-5 倍的并发请求。

### 20.2 内存共享

PagedAttention 的块抽象自然支持内存共享：

- **Parallel Sampling**：同一个 prompt 生成多个不同回复。所有回复共享 prompt 的 KV Cache。
- **Beam Search**：同一轮搜索的多个 beam 共享公共前缀的 KV Cache（写时复制，Copy-on-Write）。
- **Prefix Sharing**：多个请求有相同的 system prompt——只需存一份 system prompt 的 KV Cache。

在 vLLM 中，共享前缀可以将吞吐量提升 1.67-3.6×。

### 20.3 Continuous Batching

传统 batch 推理：所有请求必须等最长的那个完成才能出下一个 batch（"batch" 意味着同步）。

Continuous Batching（又称 in-flight batching）：请求可以随时加入和退出 batch，不需要等同一批的其他请求完成。

```
时间 →
请求 A: ████████████████（长回复）
请求 B:     ████（短回复，中途加入）
请求 C:       ██████（中途加入）
请求 D:         ██（中途加入，短回复）
```

当一个请求生成完回复（命中 EOS token），立即释放其占用的 KV Cache 块，新请求可以马上加入。这大幅提高了 GPU 利用率。

### 20.4 生产部署全景

一个典型的 LLM 推理部署架构：

```
                      ┌── Model Worker 1 (GPU 0,1)
API Gateway ─→ Scheduler ──┼── Model Worker 2 (GPU 2,3)
  (负载均衡)    (请求调度)  ├── Model Worker 3 (GPU 4,5)
                      └── Model Worker 4 (GPU 6,7)
                      │
           KV Cache Block Manager
           (跨 worker 共享块信息)
```

每个 Model Worker 使用张量并行（TP）将模型切分到 2+ 张 GPU 上，通过 NCCL 通信。Block Manager 协调跨 worker 的 KV Cache 块分配。

常用框架：
- **vLLM**：吞吐量最高，生产部署的首选
- **SGLang**：RadixAttention 支持更灵活的 prefix caching
- **TensorRT-LLM**：NVIDIA 官方方案，兼容性最好
- **llama.cpp Server**：轻量级，适合小规模部署

---

## 第二十一章：推理优化全景

### 21.1 加速技术全谱

| 技术 | 加速维度 | 典型加速比 | 代价 |
|------|---------|-----------|------|
| KV Cache | 避免重复计算 | ~10× | 显存占用 |
| GQA/MQA | 压缩 KV Cache | ~4-8× (缓存大小) | 微小质量下降 |
| MLA | 极致压缩 KV Cache | ~30× (缓存大小) | 架构复杂度 |
| Flash Attention | IO 优化 | 2-4× | 无 |
| INT4 量化 (GPTQ/AWQ) | 减少显存 → 增大 batch | 2-4× 吞吐 | ~0.3 PPL |
| 投机解码 | 突破带宽瓶颈 | 2-3× | 草稿模型成本 |
| PagedAttention | 消除内存碎片 | 2-4× | 实现复杂度 |
| Continuous Batching | 提高 GPU 利用 | 1.5-3× | 调度复杂度 |
| Prefix Caching | 共享前缀复用 | 1.5-3× | 无 |
| Tensor Parallelism | 多卡分担 | ~N× (N 卡) | 通信开销 |

### 21.2 蒸馏：大模型的"知识传承"

> **知识蒸馏**（Hinton 2015 提出）是"大模型教会小模型"的方法。

基本流程：
1. 用大模型（教师）在大量数据上生成回复（soft labels——不是硬标签，而是 token 概率分布）
2. 用小模型（学生）在这些 soft labels 上训练

与直接用 ground truth 训练相比，soft labels 包含了更多信息——教师的概率分布编码了"哪个 token 勉强可以接受，哪个完全不行"的细微差别。例如：
- Ground truth：下一个 token 是 "dog"
- Teacher's distribution："dog": 0.6, "puppy": 0.2, "cat": 0.05, ...
- 学生从 teacher 那里不仅学会了正确答案，还学会了"puppy"也是不错的备选

LLaMA 3 从 LLaMA 3-405B 蒸馏到 8B/70B 是当前蒸馏的最大规模实践。结果：蒸馏出的小模型在很多任务上超过了从零训练的同等大小模型。

### 21.3 端侧部署

在手机、笔记本电脑上运行 LLM 的特殊挑战：
- **功耗**：持续推理会快速耗尽电池
- **内存**：iPhone 16 也只有 8GB RAM
- **NPU/ANE**：Apple Neural Engine 需要特化的量化格式

解决方案：
- **CoreML / MLX**（Apple）：针对 Apple Silicon 优化
- **llama.cpp**（GGUF）：CPU 推理优化到极致，Metal 加速用于 M 系列芯片
- **MediaPipe**（Google）：Android 端 LLM 推理
- **Qualcomm AI Engine**：骁龙芯片的 NPU 推理

实际可在 iPhone 15 Pro 上运行的有：Gemma 2B, Phi-3-mini, 量化后的 LLaMA-7B（Q2_K）。

### 21.4 推理服务的经济学

自建 vs 调 API 的 cost 计算：

```
假设：每天 100 万次请求，平均每请求 500 output tokens
使用 GPT-4 级别模型

调 API（如 OpenAI）：
  100万 × 500 tokens × $10/1M tokens = $5,000/天 = $150,000/月

自建（8×H100 @ $3/GPU/小时）：
  硬件：8 × 24 × 30 × $3 = $17,280/月
  电力/冷却/运维：约 $5,000/月
  合计：约 $22,000/月（节省 ~85%）

但实际上还需要考虑：
  - H100 难以买到/租到
  - 自建的性能可能不如 API（调优需要专业知识）
  - API 提供方有大量优化（量化、投机解码、算子融合等）
```

**经验法则**：日均请求 < 1 万 → 调 API；日均请求 > 10 万 → 考虑自建；中间地带看 GPU 获取难度和团队能力。

### 21.5 推理优化的决策树

```
你的瓶颈是什么？
│
├─ 单次推理太慢 → Flash Attention + 算子融合
│
├─ 并发请求太多 → Continuous Batching + vLLM
│
├─ 显存放不下模型 → INT4 量化 (AWQ/GPTQ)
│   └→ 还不够 → 多卡张量并行
│
├─ decode 阶段太慢 → 投机解码 + KV Cache 量化
│
├─ 长上下文崩了 → GQA/MQA + KV Cache 淘汰策略
│
└─ GPU 利用率低 → Prefix Caching + 更好的 batch 调度
```

---

## 第四幕小结

推理优化是 LLM 从"实验室技术"到"工业产品"的最后一块拼图：
- **KV Cache**（§16）：自回归推理的基石——存着别重算
- **Flash Attention**（§17）：用 Online Softmax + Tiling 消除 $O(n^2)$ 显存
- **量化**（§18）：4-bit 精度下模型质量几乎不变，显存只需 1/4
- **投机解码**（§19）：小模型草稿 + 大模型验证 = 2-3× 加速
- **推理系统**（§20）：PagedAttention + Continuous Batching = 企业级服务
- **全景**（§21）：蒸馏、端侧部署、经济学——从理论到产线

---

## 总结：LLM 全栈技术地图

```
                         ┌──────────────────────────────┐
                         │      LLM 全栈技术地图          │
                         └──────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
   ┌────▼────┐                    ┌────▼────┐                    ┌─────▼────┐
   │ 架构设计 │                    │ 预训练   │                    │ 对齐     │
   │ §1-§6   │                    │ §7-§10   │                    │ §11-§15  │
   └────┬────┘                    └────┬────┘                    └─────┬────┘
        │                               │                               │
   · Transformer                · 数据工程                    · SFT
   · Attention 进化              · Scaling Laws               · RLHF/DPO
     MHA→MQA→GQA→MLA→NSA        · 分布式训练                  · GRPO (推理模型)
   · 位置编码                      · 训练稳定                   · 安全对齐
   · MoE 稀疏激活                                                · 评估基准
   · LLaMA/DeepSeek/Qwen
        │                               │                               │
        └───────────────────────────────┼───────────────────────────────┘
                                        │
                                ┌───────▼────────┐
                                │   推理部署      │
                                │   §16-§21      │
                                └───────┬────────┘
                                        │
                                · KV Cache
                                · Flash Attention
                                · 量化 (GPTQ/AWQ)
                                · 投机解码
                                · vLLM (PagedAttention)
                                · 蒸馏 + 端侧部署
```

## 附录 A：论文索引

### 架构
- [1706.03762] Vaswani et al., *Attention Is All You Need* (2017) — Transformer
- [2005.14165] Brown et al., *Language Models are Few-Shot Learners* (2020) — GPT-3
- [2101.03961] Fedus et al., *Switch Transformers* (2021) — MoE
- [2104.09864] Su et al., *RoFormer: Enhanced Transformer with Rotary Position Embedding* (2021) — RoPE
- [2302.13971] Touvron et al., *LLaMA: Open and Efficient Foundation Language Models* (2023)
- [2305.13245] Ainslie et al., *GQA: Training Generalized Multi-Query Transformers* (2023)
- [2307.09288] Touvron et al., *Llama 2: Open Foundation and Fine-Tuned Chat Models* (2023)
- [2401.04088] Jiang et al., *Mixtral of Experts* (2024) — MoE
- [2405.04434] DeepSeek, *DeepSeek-V2* (2024) — MLA + DeepSeekMoE
- [2412.19437] DeepSeek, *DeepSeek-V3* (2024) — FP8 Training + MTP
- [2502.xxxxx] DeepSeek, *NSA: Native Sparse Attention* (2025)

### 预训练
- [2001.08361] Kaplan et al., *Scaling Laws for Neural Language Models* (2020)
- [2203.15556] Hoffmann et al., *Training Compute-Optimal Large Language Models* (2022) — Chinchilla
- [2206.07682] Wei et al., *Emergent Abilities of Large Language Models* (2022)

### 对齐
- [2203.02155] Ouyang et al., *Training Language Models to Follow Instructions* (2022) — InstructGPT
- [2305.11206] Zhou et al., *LIMA: Less Is More for Alignment* (2023)
- [2305.18290] Rafailov et al., *Direct Preference Optimization* (NeurIPS 2023)
- [2501.12948] DeepSeek, *DeepSeek-R1* (2025)

### 推理优化
- [2205.14135] Dao et al., *FlashAttention: Fast and Memory-Efficient Exact Attention* (2022)
- [2307.08691] Dao, *FlashAttention-2* (2023)
- [2210.17323] Frantar et al., *GPTQ: Accurate Post-Training Quantization* (2022)
- [2306.00978] Lin et al., *AWQ: Activation-Aware Weight Quantization* (2023)
- [2211.17192] Leviathan et al., *Fast Inference from Transformers via Speculative Decoding* (2022)
- [2309.06180] Kwon et al., *Efficient Memory Management for LLM Serving with PagedAttention* (2023) — vLLM

## 附录 B：开源工具速查

| 工具 | 用途 | 特点 |
|------|------|------|
| PyTorch FSDP | 分布式训练 | PyTorch 原生 |
| DeepSpeed (ZeRO) | 分布式训练 | ZeRO-3 节省显存 |
| Megatron-LM | 大规模训练 | TP+PP 最优实现 |
| vLLM | 推理服务 | PagedAttention |
| SGLang | 推理服务 | RadixAttention 前缀缓存 |
| TensorRT-LLM | 推理服务 | NVIDIA 官方 |
| llama.cpp | 推理（CPU/GPU） | 消费级硬件 |
| AutoGPTQ | INT4 量化 | GPTQ 实现 |
| AutoAWQ | INT4 量化 | AWQ 实现 |
| HuggingFace TGI | 推理服务 | 易用 |
| Axolotl | 微调 | 一站式微调工具 |

## 附录 C：进一步阅读

本仓库内的相关文章：
- [思维链：从提示工程到推理时训练](../cot-survey) — CoT 全面综述，14 篇论文，5 个节点
- [RL 完全教程](../RL-Tutorial) — 从贝尔曼方程到 GRPO，24 篇论文
- [DeepSeek V4 注意力机制深度解析](../dsv4_att) — MLA、NSA、mHC 逐公式拆解
- [扩散模型数学基础](../diffusion-math) — DDPM、Flow Matching
- [机器学习数学基础](../math-primer-for-ml) — 线性代数、概率、微积分复习
- [世界模型综述](../world-models-survey) — Dreamer、JEPA

---

> **全文完**。本文梳理了 2017-2026 年大语言模型的四个核心维度：架构演进、预训练、对齐、推理优化。共 21 章，引用 30+ 篇核心论文，力求在深度和可读性之间取得平衡。
>
> 如果你发现错误或有改进建议，欢迎提交 Issue。
>
> 撰写于 2026 年 7 月。
>
> **统计**：2526 行，~13.3 万字，21 章，引用 30+ 篇核心论文，64 个配套素材文件（论文 PDF + 笔记）

---

## 附录 D：与已有文章的交叉引用矩阵

| 主题 | 本文覆盖 | [CoT 综述](../cot-survey) | [RL 教程](../RL-Tutorial) | [注意力解析](../dsv4_att) |
|------|---------|--------------------------|--------------------------|--------------------------|
| Transformer 架构 | ★★★ 完整 | — | — | ★★★ 注意力细节 |
| GPT 演进 | ★★★ 完整 | — | — | — |
| 注意力进化 (MHA→MLA) | ★★☆ 总结 | — | — | ★★★ 逐公式拆解 |
| 位置编码 | ★★★ 完整 | — | — | — |
| MoE | ★★★ 完整 | — | — | — |
| 预训练+数据 | ★★★ 完整 | — | — | — |
| Scaling Laws | ★★★ 完整 | — | — | — |
| 分布式训练 | ★★★ 完整 | — | — | — |
| SFT | ★★★ 完整 | — | — | — |
| RLHF | ★★★ 完整 | — | ★★★ PPO 推导 | — |
| DPO | ★★★ 完整 | — | — | — |
| GRPO | ★★☆ 总结 | ★★★ 四阶段训练 | ★★★ 公式对比 | — |
| CoT / 推理方法 | ★☆☆ 引用 | ★★★ 完整 | — | — |
| KV Cache | ★★★ 完整 | — | — | ★★★ 缓存计算 |
| Flash Attention | ★★★ 完整 | — | — | — |
| 量化 | ★★★ 完整 | — | — | — |
| 投机解码 | ★★★ 完整 | — | — | — |
| vLLM | ★★★ 完整 | — | — | — |

★★★ = 深度覆盖，★★☆ = 总结+引用，★☆☆ = 简要提及

[← 回到首页](..)
