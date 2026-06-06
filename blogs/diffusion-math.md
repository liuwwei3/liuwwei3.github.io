---
layout: default
title: Diffusion 模型的数学主线：从马尔可夫链到概率流
---
# Diffusion 模型的数学主线：从马尔可夫链到概率流
[← 回到首页](..)


> 本文梳理 2015–2025 年间 34 篇 Diffusion 核心论文的数学框架，找到一条贯穿始终的数学主线。
>
> **目标读者**：已学习概率论基础（随机变量、期望、高斯分布）的学生。第零章补充了理解扩散模型所需的所有进阶数学知识。

---

## 符号表

### 数据和模型

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $\mathbf{x}_0 \in \mathbb{R}^d$ | 原始数据点（干净图像） | §1.1 |
| $\mathbf{x}_t \in \mathbb{R}^d$ | 第 $t$ 步的噪声数据 | §1.1 |
| $\mathbf{x}_T$ | 纯噪声（扩散终点，$T$ 足够大时近似 $\mathcal{N}(0,\mathbf{I})$） | §1.1 |
| $q(\mathbf{x}_0)$ | 真实数据分布 | §1.1 |
| $p_\theta$ | 参数化的模型分布 | §1.1 |
| $\boldsymbol{\epsilon} \sim \mathcal{N}(0,\mathbf{I})$ | 标准高斯噪声 | §1.2 |
| $\hat{\mathbf{x}}_0$ | 从 $\mathbf{x}_t$ 估计的干净数据 | §2.1 |
| $\mathbf{c}$ | 条件（文本、类别等） | §4.2 |

### 噪声调度

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $\beta_t \in (0,1)$ | 第 $t$ 步的噪声方差 | §1.1 |
| $\alpha_t = 1 - \beta_t$ | 单步信号保留率 | §1.2 |
| $\bar{\alpha}_t = \prod_{s=1}^t \alpha_s$ | 累积信号保留率 | §1.2 |
| $\sigma_t$ | 第 $t$ 步的噪声标准差（VDM / EDM 记法） | §3.1 |
| $\text{SNR}(t) = \alpha_t^2 / \sigma_t^2$ | 信噪比 | §3.1 |
| $\lambda_t = \log(\alpha_t / \sigma_t)$ | 对数 SNR | §5.2 |

### SDE / ODE 框架

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $t \in [0, T]$ | 连续时间参数 | §2.2 |
| $\mathbf{w}_t$ | 标准布朗运动（Wiener 过程） | §2.2 |
| $\mathbf{f}(\mathbf{x}, t)$ | SDE 的漂移系数 | §2.2 |
| $g(t)$ | SDE 的扩散系数 | §2.2 |
| $\nabla_{\mathbf{x}}\log p_t(\mathbf{x})$ | **得分函数**（score function） | §2.2 |
| $\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)$ | 噪声预测网络 | §1.2 |
| $\mathbf{s}_\theta(\mathbf{x}_t, t)$ | 得分网络 | §1.2 |
| $D_\theta(\mathbf{x}; \sigma)$ | 去噪网络 | §3.1 |
| $v_\theta(\mathbf{x}, t)$ | 向量场网络（Flow Matching） | §5.1 |

### 训练与损失

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $\mathcal{L}_{\text{simple}}$ | DDPM 简化噪声预测损失 | §1.2 |
| $D_{\text{KL}}(q \Vert p)$ | KL 散度 | §0.2 |
| $\mathbb{E}_{q}[\,\cdot\,]$ | 在分布 $q$ 下的期望 | §1.1 |
| $\theta$ | 神经网络参数 | §1.1 |
| $\mathcal{N}(\mathbf{x}; \boldsymbol{\mu}, \boldsymbol{\Sigma})$ | 均值为 $\boldsymbol{\mu}$、协方差为 $\boldsymbol{\Sigma}$ 的高斯分布 | §0.1 |

### 流匹配与一致性

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $\phi_t: \mathbb{R}^d \to \mathbb{R}^d$ | 流映射（flow map） | §5.1 |
| $u_t(\mathbf{x})$ | 目标向量场 | §5.1 |
| $p_t(\mathbf{x})$ | 概率密度路径 | §5.1 |
| $f_\theta(\mathbf{x}_t, t)$ | 一致性函数 | §6.1 |

---

## 第零章：数学基础

> 本章为已有概率论基础（随机变量、期望、方差、高斯分布的基本定义）的读者补充理解扩散模型所需的进阶数学知识。若对某个概念已熟悉可跳过。

### 0.1 多元高斯分布

$d$ 维高斯分布 $\mathcal{N}(\boldsymbol{\mu}, \boldsymbol{\Sigma})$ 的概率密度函数为：

$$p(\mathbf{x}) = \frac{1}{(2\pi)^{d/2}|\boldsymbol{\Sigma}|^{1/2}}\exp\!\left(-\frac{1}{2}(\mathbf{x}-\boldsymbol{\mu})^\top\boldsymbol{\Sigma}^{-1}(\mathbf{x}-\boldsymbol{\mu})\right)$$

其中 $\boldsymbol{\mu} \in \mathbb{R}^d$ 是均值向量，$\boldsymbol{\Sigma} \in \mathbb{R}^{d \times d}$ 是协方差矩阵。

**各向同性高斯**（isotropic Gaussian）是扩散模型中最常用的形式：

$$\mathcal{N}(\boldsymbol{\mu}, \sigma^2\mathbf{I}) = \boldsymbol{\mu} + \sigma \cdot \mathcal{N}(0,\mathbf{I})$$

即每个维度独立同分布，方差相同。它的密度函数简化为 $p(\mathbf{x}) = \frac{1}{(2\pi\sigma^2)^{d/2}}\exp(-\frac{\Vert\mathbf{x}-\boldsymbol{\mu}\Vert^2}{2\sigma^2})$.

**条件高斯的封闭性**：若 $\mathbf{x}$ 和 $\mathbf{y}$ 的联合分布是高斯，则条件分布 $p(\mathbf{x}\mid\mathbf{y})$ 也是高斯。这是扩散模型前向/逆向过程全部用高斯分布建模的数学基础。

![高斯分布几何](figures/fig-gaussian-2d.png)

**几何直观**：左图是各向同性高斯——等高线是完美的圆，所有方向的方差相同（特征值相等）。
在扩散模型中，每一步加的就是这种"球形"噪声。
中图展示相关高斯——协方差矩阵的非对角元素使等高线倾斜，特征向量（箭头）标示了数据变化的主方向。
右图展示**条件高斯**的关键性质：固定 $x$ 的值（虚线），$y$ 的条件分布仍然是高斯——
这就是为什么扩散模型每步的去噪可以用单一的高斯条件分布来描述。

> **直觉**：如果联合分布是"椭球形"的（高斯），那么任何"切片"（条件分布）也是椭球形的。扩散模型的推理过程就是一个大高斯分布上的逐维切片。

### 0.2 KL 散度

Kullback-Leibler (KL) 散度衡量两个概率分布 $q$ 和 $p$ 的"距离"：

$$D_{\text{KL}}(q \| p) = \int q(\mathbf{x})\log\frac{q(\mathbf{x})}{p(\mathbf{x})}\,d\mathbf{x} = \mathbb{E}_{\mathbf{x}\sim q}\left[\log q(\mathbf{x}) - \log p(\mathbf{x})\right]$$

其中 $\mathbb{E}_{\mathbf{x}\sim q}[\cdot]$ 表示在 $\mathbf{x}$ 服从分布 $q$ 下的期望，等价简写为 $\mathbb{E}_q[\cdot]$。两者含义完全相同：对 $q$ 求积分。

**性质**：
- $D_{\text{KL}}(q \Vert p) \geq 0$，等于 $0$ 当且仅当 $q = p$（几乎处处）
- **非对称**：$D_{\text{KL}}(q \Vert p) \neq D_{\text{KL}}(p \Vert q)$
- 扩散模型中 $q$（前向过程）是已知的简单分布，$p_\theta$（逆向过程）被训练去逼近它

**两个高斯分布之间的 KL 散度**（有闭式解）：

$$
\begin{aligned}
D_{\text{KL}}\big(\mathcal{N}(\boldsymbol{\mu}_q,\boldsymbol{\Sigma}_q)\,\big\|\,\mathcal{N}(\boldsymbol{\mu}_p,\boldsymbol{\Sigma}_p)\big)
= \frac{1}{2}\!\Big[ &\log\frac{|\boldsymbol{\Sigma}_p|}{|\boldsymbol{\Sigma}_q|} - d \\
&+ \text{tr}(\boldsymbol{\Sigma}_p^{-1}\boldsymbol{\Sigma}_q) \\
&+ (\boldsymbol{\mu}_p-\boldsymbol{\mu}_q)^\top\boldsymbol{\Sigma}_p^{-1}(\boldsymbol{\mu}_p-\boldsymbol{\mu}_q)\Big]
\end{aligned}
$$

当 $\boldsymbol{\Sigma}_q = \boldsymbol{\Sigma}_p = \sigma^2\mathbf{I}$ 时简化为 $\frac{1}{2\sigma^2}\Vert\boldsymbol{\mu}_p - \boldsymbol{\mu}_q\Vert^2$. 这是 DDPM 将 ELBO 中的 KL 项转化为简单的 $\ell_2$ 回归的关键。

> **几何直觉**：当两个高斯的协方差相同时，KL 散度退化为**均值之间的欧几里得距离平方**
> （除以 $2\sigma^2$）。这意味着最小化 KL 等价于让模型的均值 $\boldsymbol{\mu}_p$ 尽可能接近
> 真实均值 $\boldsymbol{\mu}_q$——这正是 MSE 回归。当协方差不同时，KL 散度还惩罚方向性的不匹配（通过 $\log\frac{\lvert\Sigma_p\rvert}{\lvert\Sigma_q\rvert}$ 和 $\text{tr}(\Sigma_p^{-1}\Sigma_q)$ 项）。
> 详见第四章的 [fig-kl-geometry.png] 分析。

### 0.3 重参数化技巧

重参数化技巧是深度学习中使用随机变量的标准方法。核心思想：将**带参数的随机性**拆分为**确定性变换 + 无参数噪声**。

**示例**：抽样 $\mathbf{x} \sim \mathcal{N}(\boldsymbol{\mu}_{\theta}, \sigma_{\theta}^2\mathbf{I})$ 等价于：

$$\mathbf{x} = \boldsymbol{\mu}_\theta + \sigma_\theta \cdot \boldsymbol{\epsilon}, \quad \boldsymbol{\epsilon} \sim \mathcal{N}(0,\mathbf{I})$$

$\boldsymbol{\epsilon}$ 不依赖参数 $\theta$。
因此梯度可以穿过 $\boldsymbol{\mu}_\theta$ 和 $\sigma_\theta$ 反向传播。

在扩散模型中，前向过程 $\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}$ 就是重参数化的一次应用：使得 $\mathbf{x}_t$ 可以在一步中直接从 $\mathbf{x}_0$ 采样，无需模拟 $t$ 步链。

### 0.4 得分函数 (Score Function)

**定义**：分布 $p(\mathbf{x})$ 的得分函数是其对数概率密度对输入的梯度：

$$\mathbf{s}(\mathbf{x}) = \nabla_{\mathbf{x}}\log p(\mathbf{x})$$

**为什么取对数？** 两个原因：
(1) **消去归一化常数**。如果 $p(\mathbf{x}) = \frac{\tilde{p}(\mathbf{x})}{Z}$，则 $\nabla\log p = \nabla\log\tilde{p} - \nabla\log Z$，
而 $\log Z$ 是常数，梯度为 $0$——得分完全由未归一化的 $\tilde{p}$ 决定，不需要算 $Z$。
若直接用 $\nabla p$，则 $\nabla p = \frac{1}{Z}\nabla\tilde{p}$，$Z$ 仍然会出现。
(2) **将乘法变加法**。对于高斯分布 $p(\mathbf{x}) \propto \exp(-\frac{\|\mathbf{x}-\boldsymbol{\mu}\|^2}{2\sigma^2})$，
取对数后 $\log p(\mathbf{x}) = -\frac{\|\mathbf{x}-\boldsymbol{\mu}\|^2}{2\sigma^2} + C$，求梯度得到简洁的线性形式：
$\nabla\log p(\mathbf{x}) = -\frac{\mathbf{x}-\boldsymbol{\mu}}{\sigma^2}$。这一点在扩散模型的去噪得分匹配中至关重要。

**直观理解**：得分函数是指向更高密度区域的向量场——告诉你如何微调 $\mathbf{x}$ 来增加 $\log p(\mathbf{x})$.
注意 $\nabla\log p = \frac{\nabla p}{p}$——得分函数和直接梯度**方向相同**（都指向密度增长最快的方向），但**大小不同**：$p$ 小的地方得分被 $\frac{1}{p}$ 放大，$p$ 大的地方被缩小。
这种自适应缩放使得得分匹配在低密度区域也有强学习信号，而直接梯度匹配在低密度区域信号微弱。

**关键性质**：得分函数**不依赖于**概率密度的归一化常数。设 $p(\mathbf{x}) = \frac{\tilde{p}(\mathbf{x})}{Z}$，其中 $Z = \int\tilde{p}(\mathbf{x})d\mathbf{x}$，则：

$$\nabla_{\mathbf{x}}\log p(\mathbf{x}) = \nabla_{\mathbf{x}}\log\tilde{p}(\mathbf{x}) - \underbrace{\nabla_{\mathbf{x}}\log Z}_{=0} = \nabla_{\mathbf{x}}\log\tilde{p}(\mathbf{x})$$

这是"去噪得分匹配"可行的数学基础——我们不需要知道 $p_t(\mathbf{x})$ 的归一化常数也能估计其得分函数。

> **几何直觉**：得分函数在 1D 情形中就是 $\frac{d}{dx}\log p(x)$。想象一个钟形曲线（高斯密度）——
> 在曲线左侧，$\log p$ 随 $x$ 增大而增大，得分是**正的**（指向右，朝峰顶）；
> 在右侧，得分是**负的**（指向左，朝峰顶）；在峰顶，得分为零（已达最高点）。
> 详见第二章的 [fig-score-field.png]。

### 0.5 ELBO 与变分推断

对于隐变量模型 $p_\theta(\mathbf{x}) = \int p_\theta(\mathbf{x},\mathbf{z})d\mathbf{z}$，对数似然 $\log p_\theta(\mathbf{x})$ 通常无法直接计算（积分不可解）。

**证据下界**（Evidence Lower BOund, ELBO）提供了一种可优化的近似：

$$\log p_\theta(\mathbf{x}) \geq \mathbb{E}_{q(\mathbf{z}|\mathbf{x})}\left[\log\frac{p_\theta(\mathbf{x},\mathbf{z})}{q(\mathbf{z}|\mathbf{x})}\right] =: \text{ELBO}$$

**推导**：对任意 $q(\mathbf{z}|\mathbf{x})$，有 $\log p_\theta(\mathbf{x}) = \mathbb{E}_q[\log p_\theta(\mathbf{x})] = \mathbb{E}_q\!\left[\log\frac{p_\theta(\mathbf{x},\mathbf{z})}{p_\theta(\mathbf{z}|\mathbf{x})}\right]$，
分子分母同乘 $q(\mathbf{z}|\mathbf{x})$：
$$\log p_\theta(\mathbf{x}) = \mathbb{E}_q\!\left[\log\frac{p_\theta(\mathbf{x},\mathbf{z})}{q(\mathbf{z}|\mathbf{x})}\right] + \mathbb{E}_q\!\left[\log\frac{q(\mathbf{z}|\mathbf{x})}{p_\theta(\mathbf{z}|\mathbf{x})}\right] = \text{ELBO} + D_{\text{KL}}(q\,\|\,p_\theta)$$
因为 KL $\geq 0$，所以 $\log p_\theta(\mathbf{x}) \geq \text{ELBO}$，即 $\log p_\theta(\mathbf{x}) = \text{ELBO} + \text{KL 间隙}$。这就是"证据下界"的名字由来。

在扩散模型中：
- $\mathbf{z} = \mathbf{x}_{1:T}$ 是隐变量序列
- $q(\mathbf{z}\mid\mathbf{x}) = q(\mathbf{x}_{1:T}\mid\mathbf{x}_0)$ 是固定的前向过程（不需要学习）
- $p_\theta(\mathbf{x},\mathbf{z}) = p_\theta(\mathbf{x}_{0:T})$ 是学习的逆向过程

训练目标就是最大化 ELBO。

> **ELBO 与神经网络 Loss 的关系——用抛硬币讲清楚**。
>
> 假设一枚硬币，正面概率未知，记为 $z$。抛 10 次，7 次正面。
> 如果 $z$ 是固定参数，直接最大化似然 $z^7(1-z)^3$ 就行，得 $z=0.7$。
>
> 但如果 $z$ 本身也是随机变量（硬币是从一堆偏置不同的硬币里随机抽的），
> 对数似然 $\log p(\text{数据}) = \log \int_0^1 p(\text{7正3反}|z)\,p(z)\,dz$ 无法直接计算（积分里有未知分布）。
>
> ELBO 的做法：引入一个参数化的近似分布 $q_\phi(z)$（Beta 分布），最大化下界：
> $$\text{ELBO} = \mathbb{E}_{z \sim q_\phi}\big[\log p(\text{7正3反}|z)\big] - D_{\text{KL}}(q_\phi \,\Vert\, p_{\text{prior}}(z))$$
> 其中 $p_{\text{prior}}(z)$ 是**先验**——看到数据之前对 $z$ 的初始信念。
> 这里取 $\text{Beta}(1,1)$（即 $[0,1]$ 上的均匀分布），表示"抛之前我们认为任何偏置都等可能"。
> ELBO 第一项用数据修正信念，第二项防止偏离先验太远。
>
> **为什么不直接最大化似然？** 因为代码里的 `log_likelihood` 是拿**采样出来的 $z$** 算的，
> 而 $z$ 来自 $q_\phi$。如果只最大化似然、去掉 KL 项，$q_\phi$ 会坍缩成
> $\text{Beta}(8, 4)$ 的尖峰（只在 $z=0.7$ 附近有值），丢失"硬币偏置可能不同"的不确定性。
> KL 项就像正则化——保持 $q_\phi$ 有一定宽度，不 collapse 到点估计。
> 在扩散模型中这个区别更大：KL 项的闭式解是整个训练能简化为 MSE 的关键。
>
> **把这段逻辑写成神经网络的训练代码**（伪代码，但结构完整）：
>
> ```python
> # 观测数据（硬币实验结果）
> heads, tails = 7, 3
>
> # 网络：输入 2 个数 → 输出 Beta 分布的参数 α, β
> model = nn.Sequential(
>     nn.Linear(2, 16), nn.ReLU(),
>     nn.Linear(16, 2), nn.Softplus()  # Softplus 保证 α,β > 0
> )
>
> # 先验：Beta(1,1)，即 [0,1] 均匀分布
> prior_alpha, prior_beta = 1.0, 1.0
>
> for epoch in range(1000):
>     # 前向传播：输入观测 [7, 3]，输出 α, β
>     alpha, beta = model(torch.tensor([heads, tails], dtype=torch.float))
>
>     # 从 q_φ = Beta(α, β) 中采样 z
>     z_sample = torch.distributions.Beta(alpha, beta).rsample()
>
>     # 第一项：数据似然 = z^7 * (1-z)^3
>     log_likelihood = heads * torch.log(z_sample) + tails * torch.log(1 - z_sample)
>
>     # 第二项：KL(q_φ || 先验)，Beta 之间 KL 有闭式解
>     kl = beta_kl_divergence(alpha, beta, prior_alpha, prior_beta)
>
>     # Loss = 负 ELBO
>     loss = -(log_likelihood - kl)
>
>     # 反向传播
>     loss.backward()
>     optimizer.step()
>     optimizer.zero_grad()
> ```
>
> 关键点：(1) **输入是观测数据** `[7, 3]`，不是 label——这里没有监督标签；
> (2) 网络输出的是**分布参数** $\alpha, \beta$，不是 $z$ 本身；
>     Diffusion 也是如此——网络输出噪声预测 $\boldsymbol{\epsilon}_\theta$，
>     而 $\boldsymbol{\epsilon}_\theta$ 决定了逆向高斯分布 $p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t) = \mathcal{N}(\boldsymbol{\mu}_\theta, \sigma_t^2\mathbf{I})$ 的均值
>     （$\boldsymbol{\mu}_\theta$ 由 $\boldsymbol{\epsilon}_\theta$ 和 $\mathbf{x}_t$ 计算得到，参见 §1.2）。
>     区别只在于抛硬币学的是 Beta 分布参数，扩散学的是高斯分布参数；
> (3) 从 $q_\phi$ 抽样用 `rsample()`（重参数化，§0.3），梯度才能穿过；
> (4) Loss 是负 ELBO，最小化它等价于最大化下界。
>
> **扩散模型就是这个套路**。隐变量从一个 $p$ 变成 $T$ 步噪声 $\mathbf{x}_{1:T}$，
> 输入从 `[7,3]` 变成被噪声污染的图像 $\mathbf{x}_t$，
> 输出从 $(\alpha,\beta)$ 变成预测噪声 $\boldsymbol{\epsilon}_\theta$，
> Loss 从负 ELBO 化简为 §1.2 的 MSE。

> **几何直觉**：ELBO 可以理解为"代理目标"。真正想优化的是 $\log p(\mathbf{x})$（数据的对数似然），
> 但这无法直接计算（需要积分所有可能的隐变量路径）。ELBO 是它的**下界**（lower bound）——
> 总是小于或等于真实值。两个量之间的差距恰好是 $D_{KL}(q \Vert p)$。
> 训练就是同时做两件事：(1) **提升 ELBO**（让模型更好），(2) **缩小 KL 差距**（让近似更紧）。
> 详见 [fig-elbo-geometry.png]。

### 0.6 马尔可夫链

**定义**：随机过程 $\{\mathbf{x}_t\}_{t=0}^T$ 是马尔可夫链，如果：

$$p(\mathbf{x}_t | \mathbf{x}_{t-1}, \mathbf{x}_{t-2}, \ldots, \mathbf{x}_0) = p(\mathbf{x}_t | \mathbf{x}_{t-1})$$

即未来状态只依赖于当前状态，与历史无关。

**转移核**：$p(\mathbf{x}_t \mid \mathbf{x}_{t-1})$ 完全描述了一个马尔可夫链的动力学。

**扩散模型**：前向过程是人为设计的马尔可夫链（每步加高斯噪声），逆向过程是神经网络学习的另一个马尔可夫链（每步去噪）。

![马尔可夫链](figures/fig-markov-chain.png)

**几何直观**：左图是两状态离散马尔可夫链——未来状态只取决于当前所在位置，转移概率矩阵 $P$ 完全定义了动力学。
右图展示了连续状态空间中的马尔可夫随机游走：每个位置的"下一步"是一个以当前位置为中心的高斯分布
（淡蓝色云），这意味着**给定当前位置，下一位置的条件分布被完全确定**——无论你是如何到达当前点的。

> **直觉**：马尔可夫链就像**喝醉的人走路**——下一步往哪走只取决于现在站在哪里，不记得怎么来的。扩散模型的前向过程就是醉汉向着噪声方向走，逆向过程是神经网络引导他反向走回原点。

### 0.7 随机微分方程 (SDE) 基础

#### 布朗运动（Wiener 过程）

$\mathbf{w}_t$ 是一个连续时间随机过程，满足：
- $\mathbf{w}_0 = 0$
- $\mathbf{w}_{t+\Delta} - \mathbf{w}_t \sim \mathcal{N}(0, \Delta \cdot \mathbf{I})$（增量独立且高斯）
- 样本路径连续但**处处不可微**——因为增量 $\Delta w \sim \mathcal{N}(0, \Delta)$，所以 $\Delta w / \Delta \sim \mathcal{N}(0, 1/\Delta)$，当 $\Delta \to 0$ 时方差 $\to \infty$，导数不存在。这是理解 SDE 为什么需要 Itô 积分的关键。

**直观**：布朗运动是随机游走的连续极限——每个无穷小时间段内有一个微小的随机位移。

#### Itô SDE

一个 Itô 随机微分方程的形式为：

$$d\mathbf{x}_t = \mathbf{f}(\mathbf{x}_t, t)\,dt + g(t)\,d\mathbf{w}_t$$

- $\mathbf{f}(\mathbf{x}_t, t)\,dt$：**漂移项**，描述确定性的运动方向
- $g(t)\,d\mathbf{w}_t$：**扩散项**，注入随机噪声
- $d\mathbf{w}_t$ 是布朗运动的无穷小增量

**直观理解**：SDE 描述了在确定性"推力"和随机"噪声"共同作用下的粒子运动。

#### 逆向时间 SDE（Anderson, 1982）

如果前向 SDE 为 $d\mathbf{x} = \mathbf{f}dt + g d\mathbf{w}$，则存在一个逆向 SDE：

$$d\mathbf{x} = \big[\mathbf{f}(\mathbf{x}, t) - g(t)^2\nabla_{\mathbf{x}}\log p_t(\mathbf{x})\big]dt + g(t)\,d\bar{\mathbf{w}}$$

其中 $\bar{\mathbf{w}}$ 是**逆向时间**的布朗运动。

**这是整个扩散模型领域的核心定理**。它告诉我们：如果知道每个时间点的得分函数 $\nabla\log p_t$，就可以将噪声"倒带"回数据。

逐项拆解逆向 SDE 的几何意义：
$$d\mathbf{x} = \underbrace{\mathbf{f}(\mathbf{x}, t)dt}_{\text{① 原始漂移反向}} - \underbrace{g(t)^2\nabla_{\mathbf{x}}\log p_t(\mathbf{x})dt}_{\text{② 得分引导力}} + \underbrace{g(t)d\bar{\mathbf{w}}}_{\text{③ 逆向随机扰动}}$$

- **① $\mathbf{f}dt$**：正向漂移的惯性。正向 SDE 中 $\mathbf{f}$ 把数据推向噪声，逆向时保留这个方向分量（符号不变，因为 $dt$ 在逆向时间中自然翻转）。
- **② $-g^2\nabla\log p_t\,dt$**：**得分引导力**——这是逆向独有的项，也是整个扩散模型学习的核心。$\nabla\log p_t(\mathbf{x})$ 指向当前噪声水平下更"像数据"的方向（见 §0.4）。$g(t)^2$ 缩放这个力——噪声越大，需要的引导越强。负号表示这是**吸引子**：把粒子拉回数据流形。
- **③ $g(t)d\bar{\mathbf{w}}$**：逆向布朗噪声。即使方向正确，路径仍需随机探索以保证覆盖整个分布。$\bar{\mathbf{w}}$ 是逆向时间的 Wiener 过程。

> **本质**：逆向 SDE 就是在原始漂移上叠加一个**指向数据的力**（得分），外加随机探索。得分函数是唯一需要学习的东西——知道它，就掌握了从任意噪声回到数据的全部动力学。

![SDE可视化](figures/fig-brownian-sde.png)

**几何直观**：

**左上（纯布朗运动）**：粒子完全随机游走，没有确定性方向。灰色包络 $\pm 2\sqrt{t}$ 显示标准差随 $\sqrt{t}$ 增长——这是扩散过程的特征行为。每条路径是连续但处处不可微的（锯齿状）。

**右上（漂移 + 扩散）**：粒子在随机游走的同时被一个向下的力（$\mu=-1$）拉向负方向。黑色虚线是确定性部分（$\mu t$），灰色包络是叠加的随机扩散（$\pm 2\sigma\sqrt{t}$）。

**左下（漂移 vs 扩散的对比）**：漂移 $\mathbf{f}$（蓝色箭头）确定方向，扩散（红色区域）添加随机扰动。
在实际扩散模型中，**正向 SDE** 的 $\mathbf{f}$ 指向噪声，**逆向 SDE** 的 $\mathbf{f} - g^2\nabla\log p_t$ 指向数据。

**右下（离散→连续极限）**：步数越多（$N$ 越大），离散马尔可夫链越接近连续 SDE 的轨迹。扩散模型的 $T=1000$ 步离散化就是对连续 SDE 的精细近似。

> **类比映射**：正扩散就像**河上的落叶**——
> - **漂移项 $\mathbf{f}dt$** = 河水流速，把叶子（数据）推向噪声方向（下游）
> - **扩散项 $g(t)d\mathbf{w}$** = 湍流，随机晃动的幅度由 $g(t)$ 控制
> - **得分函数 $\nabla\log p_t$** = 你需要的"地图"——每个位置标注了"哪边更可能是数据源头"
>
> 正向过程你只知道河水怎么流（$\mathbf{f}$ 和 $g$ 是人工设计的），不知道叶子从哪来的。
> 逆向过程的关键：**一旦掌握了得分函数这张地图，加上河水的流动规律，就可以逆流而上把叶子送回起点。**
> Anderson 定理的威力在于——得分函数是唯一缺失的拼图，其余都是已知的。

### 0.8 常微分方程 (ODE) 与概率流

#### ODE 的微分方程定义

常微分方程描述一个确定性的动力学系统：

$$\frac{d\mathbf{x}}{dt} = v(\mathbf{x}, t) \quad \text{或微分形式} \quad d\mathbf{x} = v(\mathbf{x}, t)\,dt$$

其中 $v(\mathbf{x}, t)$ 是**向量场**——空间中每一点 $(t, \mathbf{x})$ 都有一个确定的速度向量。

**与 SDE（§0.7）的直接对比**：
$${\color{#2E86AB}\text{ODE:}}\; d\mathbf{x} = v(\mathbf{x}, t)\,dt \qquad {\color{#A23B72}\text{SDE:}}\; d\mathbf{x} = \mathbf{f}(\mathbf{x}, t)\,dt + g(t)\,d\mathbf{w}$$

SDE 比 ODE 多了一个随机项 $g(t)\,d\mathbf{w}$——这是唯一的区别。
去掉随机项，SDE 就退化为 ODE。在扩散模型的语境中，$v$ 和 $\mathbf{f}$ 都是向量场，
不同文献用不同符号；$g$ 是 SDE 的扩散系数，在 PF-ODE 中作为得分的缩放因子出现。

#### 正向过程与逆向过程

给定 ODE $d\mathbf{x} = v(\mathbf{x}, t)\,dt$，改变时间方向就得到正向/逆向：

- **正向过程**（$t: 0 \to T$）：$\mathbf{x}$ 沿 $v$ 的方向演化。在扩散中，正向 SDE 将数据加噪；正向 ODE 也是数据→噪声。
- **逆向过程**（$t: T \to 0$）：$\mathbf{x}$ 沿 $-v$ 的方向逆演化。只需将 $dt$ 变为 $-dt$，向量场取反：

$$d\mathbf{x} = -v(\mathbf{x}, T-t)\,dt$$

**直觉**：ODE 正向和逆向的区别仅仅是**时间箭头的方向**。就像视频正放和倒放——正放时粒子沿 $v$ 的方向移动，倒放时沿 $-v$ 的方向退回。因为 ODE 是确定性的，正放和倒放互为唯一逆映射。

**在扩散模型中的应用**：
- 前向 SDE $d\mathbf{x} = \mathbf{f}dt + g d\mathbf{w}$（数据→噪声，有随机性）
- 逆向 SDE $d\mathbf{x} = [\mathbf{f} - g^2\nabla\log p_t]dt + g d\bar{\mathbf{w}}$（噪声→数据，有随机性）
- PF-ODE $d\mathbf{x} = [\mathbf{f} - \frac{1}{2}g^2\nabla\log p_t]dt$（或正向或逆向，取决于 $dt$ 符号）

逆向 ODE 直接给出噪声到数据的确定映射——这是 DDIM 和所有 ODE 采样器的理论基础。

**为什么不直接学习整个向量场 $v(\mathbf{x},t)$ 而要拆成 $\mathbf{f},g,\nabla\log p_t$ 三个量？**
因为 $\mathbf{f}$ 和 $g$ 是**人为设计的前向噪声调度，完全已知**，唯一的未知量是得分 $\nabla\log p_t$。
举一个具体例子：VP-SDE 中 $\mathbf{f} = -\frac{1}{2}\beta(t)\mathbf{x}$，$g(t) = \sqrt{\beta(t)}$，其中 $\beta(t)$ 是我选的线性调度。
这两个量连参数都没有——不需要学习。网络只需学得分，而得分恰好等于 $-\boldsymbol{\epsilon}/\sqrt{1-\bar{\alpha}_t}$（§1.2），
所以网络最终只学一个量：预测噪声。如果试图直接学习 $v$，网络需要隐式地同时推断 $\mathbf{f}$、$g$ 和得分——
而前两者是已知的，让网络重学是浪费容量。

#### 流 (Flow) 与向量场

**$\phi_t(\mathbf{x})$ 的定义**：从初始点 $\mathbf{x}$ 出发，沿 ODE 运动到时间 $t$ 所到达的位置。
它是 ODE 的**解映射**：
$$\frac{d}{dt}\phi_t(\mathbf{x}) = v(\phi_t(\mathbf{x}), t), \quad \phi_0(\mathbf{x}) = \mathbf{x}$$

**如何获得 $\phi_t$**：ODE 一般无闭式解，通过数值积分获得——从小步长 $\Delta t$ 逐步沿 $v$ 推进。

**几何示例——向量场与积分曲线**：

![ODE流与向量场](figures/fig-ode-flow.png)

- **左图**：每个箭头是向量场 $v(\mathbf{x})$ 在某点的方向和大小。从任意点出发，沿箭头连续移动形成积分曲线（品红），这就是 $\phi_t$ 的轨迹。中心不动点是 $v = 0$ 处。
- **右图**：Euler 方法用折线逼近光滑曲线。步长越大误差越大——但 ODE 的确定性允许高阶方法（DPM-Solver）用大得多的步长。

> **直觉**：ODE 流就像**天气预报的风场图**——每点有确定的风向风速。叶子放在任意位置都会沿积分曲线飞行。

#### Probability Flow ODE（概率流 ODE）

在扩散模型中，Score SDE 论文推导出以下 ODE，其边缘分布与对应 SDE 完全相同：

$$d\mathbf{x} = \left[\mathbf{f}(\mathbf{x}, t) - \frac{1}{2}g(t)^2\nabla_{\mathbf{x}}\log p_t(\mathbf{x})\right]dt$$

**各符号来源**：$\mathbf{f}$ 和 $g$ 来自 SDE（§0.7，前向扩散的漂移和扩散系数），$\nabla\log p_t$ 是得分函数（§0.4）。合在一起构成了一个确定性的向量场——不需要随机噪声就能产生与 SDE 相同分布的样本。

**逆向使用（采样）**：将 $dt$ 取负即可得到噪声→数据的 ODE：
$$d\mathbf{x} = -\left[\mathbf{f}(\mathbf{x}, t) - \frac{1}{2}g(t)^2\nabla_{\mathbf{x}}\log p_t(\mathbf{x})\right]dt$$

#### 数值求解

Euler 方法——最基本的 ODE 步进：
$$\mathbf{x}_{t-\Delta t} \approx \mathbf{x}_t - h(\mathbf{x}_t, t) \cdot \Delta t$$
其中 $h$ 是 ODE 右端函数（即 $v$ 或 PF-ODE 的 $[\mathbf{f} - \frac{1}{2}g^2\nabla\log p_t]$）。高阶方法（Heun、RK4）使用更多中间评估换精度，是 DPM-Solver 和 EDM 的基础。

### 0.9 变量替换与 Push-forward

若 $\mathbf{z} \sim p_{\mathbf{z}}(\mathbf{z})$（先验），经过可逆变换 $\mathbf{x} = \phi(\mathbf{z})$，
则 $\mathbf{x}$ 的分布 $p_{\mathbf{x}}(\mathbf{x})$ 由**变量替换公式**给出：

$$p_{\mathbf{x}}(\mathbf{x}) = p_{\mathbf{z}}(\phi^{-1}(\mathbf{x}))\left|\det\frac{\partial\phi^{-1}}{\partial\mathbf{x}}(\mathbf{x})\right|$$

**推导**（一维情形，高维类推）：设 $x = \phi(z)$，$z = \phi^{-1}(x)$。
根据概率守恒：$p_{\mathbf{x}}(x)\,dx = p_{\mathbf{z}}(z)\,dz$，即 $dx$ 区间内的概率等于对应 $dz$ 区间内的概率。
因此 $p_{\mathbf{x}}(x) = p_{\mathbf{z}}(z) \cdot \left|\frac{dz}{dx}\right| = p_{\mathbf{z}}(\phi^{-1}(x)) \cdot \left|\frac{d}{dx}\phi^{-1}(x)\right|$。
高维推广：一阶导数变成 Jacobian 矩阵的行列式。

这个操作称为将分布 $p_{\mathbf{z}}$ **前推 (push-forward)** 为 $p_{\mathbf{x}}$，记作 $p_{\mathbf{x}} = [\phi]_*\,p_{\mathbf{z}}$。

在连续归一化流（CNF）和 Flow Matching 中，流映射 $\phi_t$ 将简单先验 $p_{\mathbf{z}}$ 连续地变换为目标分布 $p_{\mathbf{x}}$。

![Push-forward](figures/fig-pushforward.png)

**左上→右上**：500 个高斯噪声点（$\mathbf{z} \sim \mathcal{N}(0,\mathbf{I})$）经过仿射变换 $\phi(\mathbf{z}) = \mathbf{W}\mathbf{z} + \mathbf{b}$ 后，云团被拉伸、旋转和平移。每个灰线连接了变换前后的对应点。

**左下（密度变化）**：当 $x = e^z$ 将高斯压缩时，密度也发生变化——$p_{\mathbf{x}}(x)$ 不再是高斯，而是对数正态分布。Push-forward 公式 $p_{\mathbf{x}}(x) = p_{\mathbf{z}}(\phi^{-1}(x))\,\lvert\det \partial\phi^{-1}\!/\partial x\rvert$ 中的 Jacobian 因子精确地补偿了这种体积变化。

**右下（体积缩放）**：雅可比矩阵 $\mathbf{J} = \partial\phi/\partial\mathbf{z}$ 的行列式 $\det(\mathbf{J})$ 度量了变换 $\phi$ 对小体积元的放大倍数。蓝色正方形被拉伸为红色平行四边形，面积放大了 $\det(\mathbf{J}) = 1.56$ 倍。Push-forward 公式中除以 $\det(\mathbf{J})$：空间被拉伸时，点被"稀释"——密度按 $1/1.56$ 倍降低，保证变换后概率总质量仍为 $1$（总概率守恒）。

> **数值实例**（用右下图的均匀分布）：设先验 $p_{\mathbf{z}}$ 是蓝色正方形 $[-1,1] \times [-1,1]$ 上的均匀分布，密度为常数
> $p_{\mathbf{z}}(\mathbf{z}) = \frac{1}{\text{面积}} = \frac{1}{4}$（正方形面积 = $2 \times 2 = 4$）。
> 变换 $\mathbf{x} = \phi(\mathbf{z}) = \mathbf{W}\mathbf{z} + \mathbf{b}$，其中 $\mathbf{W} = \begin{bmatrix}1.5 & 0.8 \\ 0.3 & 1.2\end{bmatrix}$，$\mathbf{b} = \mathbf{0}$。
> 则 $\det(\mathbf{J}) = \det(\mathbf{W}) = 1.5 \times 1.2 - 0.8 \times 0.3 = 1.56$。
> 正方形被拉伸为红色平行四边形，面积 = $4 \times 1.56 = 6.24$。
> 取平行四边形内一点 $\mathbf{x}_0 = [1.5, 1.2]^\top$（对应 $\mathbf{z}_0 = [1, 1]^\top$，在正方形内）：
> $$p_{\mathbf{x}}(\mathbf{x}_0) = p_{\mathbf{z}}(\mathbf{z}_0) / |\det(\mathbf{J})| = \frac{1/4}{1.56} = \frac{1}{6.24}$$
> 面积从 $4$ 扩大到 $6.24$，密度从 $1/4 = 0.25$ 降到 $1/6.24 \approx 0.16$——总和仍是 $6.24 \times 0.16 \approx 1$，概率守恒。

> **直觉**：Push-forward 就像**揉面团**——初始均匀分布的面团（先验）被各种拉伸、旋转、折叠（流映射 $\phi_t$），最终变成我们想要的形状（数据分布）。Flow Matching 训练的就是这个揉面团的"手法"。

### 0.10 期望和 L2 范数记号

- $\mathbb{E}_{q(\mathbf{x})}[f(\mathbf{x})] = \int f(\mathbf{x})q(\mathbf{x})d\mathbf{x}$：在分布 $q$ 下的期望。实际训练中用 Monte Carlo 估计（小批量平均）。
- $\mathbb{E}_{\mathbf{x}\sim q}[f(\mathbf{x})]$ 是等价写法，$\mathbf{x}\sim q$ 表示 $\mathbf{x}$ 从分布 $q$ 中采样。类似的 $\mathbb{E}_{t,\mathbf{x}_0,\boldsymbol{\epsilon}}$ 表示同时对 $t$、$\mathbf{x}_0$、$\boldsymbol{\epsilon}$ 三个随机变量求期望。
- $\Vert\mathbf{x}\Vert^2 = \mathbf{x}^\top\mathbf{x} = \sum_i x_i^2$：向量的平方 $\ell_2$ 范数。
- $\Vert\boldsymbol{\epsilon} - \hat{\boldsymbol{\epsilon}}\Vert^2$ 形式的目标函数本质上是回归任务的均方误差 (MSE)。

---

## 主线总览

```
离散马尔可夫链 (2015)
    │
    └→ 噪声预测 + 得分匹配 (2020)
         │
         ├→ 非马尔可夫泛化 → ODE 确定性采样 (2021)
         ├→ 连续时间 SDE → PF-ODE 统一 (2021)
         ├→ SNR 参数化 → VLB 简洁形式 (2021)
         │
         ├→ 引导数学 (2021-2022)
         ├→ 设计空间统一 (2022)
         ├→ 半线性 ODE 快速求解 (2022)
         │
         └→ 向量场 / 流范式 (2023)
              │
              ├→ 直线流 + Reflow (2023)
              ├→ 自洽性 → 一步生成 (2023)
              │
              └→ Transformer 扩展律 (2023-2025)
```

**核心数学对象**：生成概率路径的**向量场**。

这个向量场在不同语言中有不同名称——它是得分函数 $\nabla\log p_t$，是噪声预测器 $\boldsymbol{\epsilon}_\theta$，是去噪器 $D_\theta$，是流速场 $v_t$——但它们描述的是**同一个东西**：如何从噪声分布移动到数据分布。

---

## 第一章：离散扩散——马尔可夫链的变分框架

### 1.1 起源 (Sohl-Dickstein, 2015)

一切从非平衡统计物理开始。给定数据分布 $q(\mathbf{x}_0)$，定义一个**前向扩散过程**：

$$q(\mathbf{x}_{1:T}|\mathbf{x}_0) = \prod_{t=1}^T q(\mathbf{x}_t|\mathbf{x}_{t-1})$$

$$q(\mathbf{x}_t|\mathbf{x}_{t-1}) = \mathcal{N}\left(\mathbf{x}_t; \sqrt{1-\beta_t}\,\mathbf{x}_{t-1}, \beta_t\mathbf{I}\right)$$

其中 $0 < \beta_1 < \cdots < \beta_T < 1$ 是噪声调度。

**关键性质**：当 $\beta_t$ 足够小，逆向条件分布 $q(\mathbf{x}_{t-1}\mid\mathbf{x}_t)$ 也是高斯的（尽管显式形式需要 $\mathbf{x}_0$）——这来自 §0.1 中高斯条件分布的封闭性。

定义一个参数化的**逆向马尔可夫链**：

$$p_\theta(\mathbf{x}_{0:T}) = p(\mathbf{x}_T)\prod_{t=1}^T p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t)$$

训练最大化数据似然，利用 §0.5 中的**变分下界 (ELBO)**：

$$\log p_\theta(\mathbf{x}_0) \geq \mathbb{E}_q\left[\log p_\theta(\mathbf{x}_0|\mathbf{x}_1) - \sum_{t=2}^T D_{\text{KL}}\big(q(\mathbf{x}_{t-1}|\mathbf{x}_t,\mathbf{x}_0)\,\big\|\,p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t)\big)\right]$$

### 1.2 实用化转机：噪声预测 (DDPM, Ho et al., 2020)

DDPM 做了两个关键简化。

**一、重参数化边缘分布**。利用 §0.3 的重参数化技巧，令 $\bar{\alpha}_t = \prod_{s=1}^t(1-\beta_s)$，则：

$$\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\,\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\,\boldsymbol{\epsilon}$$

由此可以**闭合形式**地写出——即用已知量（$\mathbf{x}_0, \mathbf{x}_t, \bar{\alpha}_t, \beta_t$）的直接公式表达，不需要迭代或数值近似。闭合形式的关键价值：训练时每一步的 KL 散度可以直接计算（$q$ 的均值和方差全都已知），不需要从 $t=1$ 模拟到 $t$ 再反推——这使得训练扩散模型在计算上是可行的。

$$q(\mathbf{x}_{t-1}|\mathbf{x}_t,\mathbf{x}_0) = \mathcal{N}\left(\mathbf{x}_{t-1}; \frac{\sqrt{\bar{\alpha}_{t-1}}\beta_t}{1-\bar{\alpha}_t}\mathbf{x}_0 + \frac{\sqrt{\alpha_t}(1-\bar{\alpha}_{t-1})}{1-\bar{\alpha}_t}\mathbf{x}_t,\; \tilde{\beta}_t\mathbf{I}\right)$$

其中 $\tilde{\beta}_t = \frac{1-\bar{\alpha}_{t-1}}{1-\bar{\alpha}_t}\beta_t$.

**二、从预测 $\mathbf{x}_0$ 转向预测 $\boldsymbol{\epsilon}$**。代入 ELBO 的 KL 项，利用 $\mathbf{x}_0 = (\mathbf{x}_t - \sqrt{1-\bar{\alpha}_t}\,\boldsymbol{\epsilon})/\sqrt{\bar{\alpha}_t}$。根据 §0.2，当两个高斯有相同协方差时，KL 散度正比于均值差的平方。由此得到：

$$\mathcal{L}_{\text{simple}} = \mathbb{E}_{t,\mathbf{x}_0,\boldsymbol{\epsilon}}\left[\big\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta\big(\sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon},\,t\big)\big\|^2\right]$$

这个简洁的形式与**去噪得分匹配**（§0.4）是等价的——网络预测噪声等价于学习得分函数。

**得分与噪声的线性关系推导**：前向一步扩散 $q(\mathbf{x}_t|\mathbf{x}_0) = \mathcal{N}(\mathbf{x}_t; \sqrt{\bar{\alpha}_t}\mathbf{x}_0, (1-\bar{\alpha}_t)\mathbf{I})$ 是一个高斯分布。
取对数后 $\log q(\mathbf{x}_t|\mathbf{x}_0) = -\frac{\|\mathbf{x}_t - \sqrt{\bar{\alpha}_t}\mathbf{x}_0\|^2}{2(1-\bar{\alpha}_t)} + C$，对 $\mathbf{x}_t$ 求梯度：
$$\nabla_{\mathbf{x}_t}\log q(\mathbf{x}_t|\mathbf{x}_0) = -\frac{\mathbf{x}_t - \sqrt{\bar{\alpha}_t}\mathbf{x}_0}{1-\bar{\alpha}_t} = -\frac{\boldsymbol{\epsilon}}{\sqrt{1-\bar{\alpha}_t}}$$

**得分为什么是噪声的线性函数？** 因为 $q(\mathbf{x}_t|\mathbf{x}_0)$ 是高斯分布——高斯分布的对数是二次型，二次型的梯度是线性的。
只要前向过程使用高斯转移核，这个线性关系就**无条件成立**。这是扩散模型的核心简化之一。

**$q(\mathbf{x}_t|\mathbf{x}_0)$ 与 $q(\mathbf{x}_{t-1}|\mathbf{x}_t,\mathbf{x}_0)$ 的关系**：
前者是**边缘分布**——从 $\mathbf{x}_0$ 一步跳到 $\mathbf{x}_t$（利用重参数化直接写闭式，见上一条公式）。
后者是**后验分布**——已知 $\mathbf{x}_0$ 和 $\mathbf{x}_t$ 条件下 $\mathbf{x}_{t-1}$ 的分布。
两者通过贝叶斯规则连接：$q(\mathbf{x}_{t-1}|\mathbf{x}_t,\mathbf{x}_0) \propto q(\mathbf{x}_t|\mathbf{x}_{t-1})\,q(\mathbf{x}_{t-1}|\mathbf{x}_0)$。
因为每一步都是高斯的，后验也是高斯，且均值和方差都有闭式解（见上方的 $q(\mathbf{x}_{t-1}|\mathbf{x}_t,\mathbf{x}_0)$ 公式）。
这个后验分布正是 ELBO 中 KL 项的"ground truth"——网络 $p_\theta$ 要逼近它。

因此 $\mathbf{s}_\theta(\mathbf{x}_t, t) = -\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)/\sqrt{1-\bar{\alpha}_t}$，**预测噪声 = 预测得分**。

**去噪得分匹配是扩散模型训练的理论基础**。核心技巧：
(1) 用已知高斯噪声扰动数据，条件分布 $q(\mathbf{x}_t|\mathbf{x}_0)$ 的得分有闭式解 $\nabla\log q = -\boldsymbol{\epsilon}/\sqrt{1-\bar{\alpha}_t}$；
(2) 这个闭式解只依赖于添加的噪声 $\boldsymbol{\epsilon}$，不需要知道数据分布 $q(\mathbf{x}_0)$ 本身；
(3) 训练网络匹配这个已知得分，等价于预测噪声。
一句话总结：**用已知条件分布的得分去教网络估计未知边缘分布的得分**——这是扩散模型能高效训练的根本原因。

#### 几何直观：前向扩散与逆向生成

![前向扩散过程](figures/fig-forward-diffusion.png)

上图展示了一个 2D 环形数据分布（t=0）如何在 5 步扩散中逐渐被高斯噪声淹没。SNR 从 ∞ dB 衰减到接近 0 dB——信息被系统性地抹去。

**训练**：随机采样 $t$、$\mathbf{x}_0$、$\boldsymbol{\epsilon}$，构造 $\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}$，
让网络 $\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)$ 预测 $\boldsymbol{\epsilon}$，最小化 $\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta\|^2$。

**生成（采样）**：训练完成后，如何用网络生成新数据？从纯噪声 $\mathbf{x}_T \sim \mathcal{N}(0,\mathbf{I})$ 开始，对 $t = T, T-1, \ldots, 1$ 迭代：

$$\mathbf{x}_{t-1} = \frac{1}{\sqrt{\alpha_t}}\left(\mathbf{x}_t - \frac{1-\alpha_t}{\sqrt{1-\bar{\alpha}_t}}\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)\right) + \sigma_t\mathbf{z}$$

其中 $\mathbf{z} \sim \mathcal{N}(0,\mathbf{I})$，$\sigma_t^2 = \tilde{\beta}_t$（或取 $\sigma_t = 0$ 即 DDIM 确定采样）。

**$\boldsymbol{\epsilon}_\theta$ 的角色**：每一步，网络看当前噪声图像 $\mathbf{x}_t$，**猜出这一步加了多少噪声** $\boldsymbol{\epsilon}_\theta$，然后从 $\mathbf{x}_t$ 中减去它——向干净图像 $\mathbf{x}_{t-1}$ 逼近。就像一层层揭掉噪声的纱，每一步都比上一步更清晰。

![重参数化技巧](figures/fig-reparam-trick.png)

左图：直接抽样 $\mathcal{N}(\mu,\sigma^2)$。中图：$\epsilon \sim \mathcal{N}(0,1)$ 独立于 $\mu,\sigma$，梯度可以穿过参数。右图：$\mathbf{x}_t$ 是数据和噪声的线性混合。

> **直觉练习**：想象一张猫的照片（$\mathbf{x}_0$）。前向过程就像往照片上倒牛奶——最初牛奶很淡，猫清晰可见；随着倒入的牛奶增多，画面越来越模糊；最终只剩一片白色（纯噪声）。逆向过程就是网络学习**如何把牛奶从照片中分离出来**。

**主线节点 1**：从 ELBO 到 $\mathcal{L}_{\text{simple}}$，扩散模型与得分匹配建立了第一座桥梁。

---

## 第二章：从离散到连续——SDE 统一

### 2.1 打破马尔可夫锁链 (DDIM, Song et al., 2021)

DDIM 的关键观察：**DDPM 的损失 $\mathcal{L}_{\text{simple}}$ 只依赖于边缘分布 $q(\mathbf{x}_t\mid\mathbf{x}_0)$，不依赖于联合分布 $q(\mathbf{x}_{1:T}\mid\mathbf{x}_0)$ 的具体形式**。
这意味着用同一组训练好的参数 $\theta$，可以搭配不同的采样链。

**Loss 不变**：DDIM 的**训练目标与 DDPM 完全相同**（$\mathcal{L}_{\text{simple}}$），不需要重新训练。
DDIM 只是换了一种采样方式——**训练过程与 DDPM 完全相同**，随机采样 $t$ 和 $\mathbf{x}_t$，最小化 $\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta\|^2$。DDIM 的非马尔可夫前向过程仅用于推导新的逆采样公式，训练时并不使用——训练完拿到 $\boldsymbol{\epsilon}_\theta$ 后，DDIM 用不同的公式从 $\mathbf{x}_T$ 迭代生成样本。

构建一族**非马尔可夫**前向过程，参数化为 $\sigma \in \mathbb{R}_{\geq 0}^T$：

$$q_\sigma(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{x}_0) = \mathcal{N}\left(\sqrt{\bar{\alpha}_{t-1}}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_{t-1} - \sigma_t^2}\,\frac{\mathbf{x}_t - \sqrt{\bar{\alpha}_t}\mathbf{x}_0}{\sqrt{1-\bar{\alpha}_t}},\; \sigma_t^2\mathbf{I}\right)$$

参数 $\sigma_t$ 控制随机性：$\sigma_t = 0$ → 确定采样，$\sigma_t = \sqrt{(1-\bar{\alpha}_{t-1})/(1-\bar{\alpha}_t)}\sqrt{1-\bar{\alpha}_t/\bar{\alpha}_{t-1}}$ → 退化为 DDPM。

当 $\sigma_t = 0$，采样变为**确定的**：

$$\mathbf{x}_{t-1} = \sqrt{\bar{\alpha}_{t-1}}\underbrace{\left(\frac{\mathbf{x}_t - \sqrt{1-\bar{\alpha}_t}\,\boldsymbol{\epsilon}_\theta}{\sqrt{\bar{\alpha}_t}}\right)}_{\hat{\mathbf{x}}_0} + \sqrt{1-\bar{\alpha}_{t-1}}\,\boldsymbol{\epsilon}_\theta$$

**与得分函数的关系**：用 $\boldsymbol{\epsilon}_\theta = -\sqrt{1-\bar{\alpha}_t}\,\mathbf{s}_\theta$ 替换可得纯得分形式。
DDIM 确定采样 = PF-ODE 的 Euler 离散（只是当时尚未被严格阐明）。

**与 DDPM 的几何对比**：从同一噪声 $\mathbf{x}_T$ 出发生成两次：
- **DDPM**：逆向过程每步都注入新的随机噪声 $\sigma_t\mathbf{z}$（$\sigma_t > 0$），两个路径迅速分叉，像醉汉——大致方向对，但步伐摇晃，每次走的路线都不同。
- **DDIM**（$\sigma_t=0$）：逆向过程完全确定，没有随机注入，给定 $\mathbf{x}_T$ 后路径唯一。像沿着导航规划的路线精确返回——光滑、可预测、可逆。
这使得 DDIM 支持**反演**：给定 $\mathbf{x}_0$ 和噪声 $\mathbf{x}_T$ 之间的确定映射，可以在潜空间中做插值和编辑。

**加速**：DDPM 需要 $T=1000$ 步（因为每步的逆向高斯需要足够小的步长），DDIM 只需 $50$-$100$ 步——
因为确定映射允许更大的跳跃而不积累随机误差。

### 2.2 连续时间 SDE 统一 (Score SDE, Song et al., 2021)

将离散扩散推到连续极限 $T \to \infty$，噪声扰动由 SDE 描述：

$$d\mathbf{x} = \mathbf{f}(\mathbf{x}, t)\,dt + g(t)\,d\mathbf{w}$$

**训练 Loss**：连续版本的得分匹配——在每一个连续时间点 $t$ 上匹配扰动分布的得分：
$$\mathcal{L}_{\text{score}} = \mathbb{E}_{t, \mathbf{x}_0, \mathbf{x}_t}\Big[\lambda(t)\|\mathbf{s}_\theta(\mathbf{x}_t, t) - \nabla_{\mathbf{x}_t}\log p_{0t}(\mathbf{x}_t|\mathbf{x}_0)\|^2\Big]$$

其中 $\lambda(t) > 0$ 是**时间权重函数**——对不同噪声水平 $t$ 的 Loss 加权。
$\|\mathbf{s}_\theta - \nabla\log p\|^2$ 是网络预测得分与真实得分之间的平方 $\ell_2$ 距离。
当 $\lambda(t) = 1-\bar{\alpha}_t$ 时，该 Loss 与 DDPM 的 $\mathcal{L}_{\text{simple}}$ 完全等价（代入 $\mathbf{s}_\theta = -\boldsymbol{\epsilon}_\theta/\sqrt{1-\bar{\alpha}_t}$ 即得 MSE 形式）。

其中 $\lambda(t)$ 是权重函数。这个 Loss 与 DDPM 的 $\mathcal{L}_{\text{simple}}$ 是**同一个 Loss 的连续形式**：离散时间点的噪声预测 $\iff$ 连续时间得分匹配，唯一的区别是离散 vs 连续、预测噪声 vs 预测得分。

**核心方程——Anderson (1982) 逆 SDE**（§0.7）：

$$d\mathbf{x} = \big[\mathbf{f}(\mathbf{x}, t) - g(t)^2\nabla_\mathbf{x}\log p_t(\mathbf{x})\big]dt + g(t)\,d\bar{\mathbf{w}}$$

生成方向（噪声→数据）的动力学完全由**得分函数** $\nabla_\mathbf{x}\log p_t(\mathbf{x})$ 决定——
知道得分就掌握了全部逆向动力学。$\mathbf{f}$ 和 $g$ 是人为设计的，唯一需要学习的就是得分。

### 2.3 Probability Flow ODE

去除 SDE 的随机项得到等价的**确定 ODE**：

$$d\mathbf{x} = \left[\mathbf{f}(\mathbf{x}, t) - \frac{1}{2}g(t)^2\nabla_\mathbf{x}\log p_t(\mathbf{x})\right]dt$$

**为什么是 $\frac{1}{2}$ 而不是 $1$？** 正向 SDE $d\mathbf{x} = \mathbf{f}dt + g d\mathbf{w}$ 对应的 Fokker-Planck 方程为 $\partial_t p = -\nabla\cdot(\mathbf{f}p) + \frac{1}{2}\nabla\cdot(g^2\nabla p)$。要让 ODE 产生相同的边缘演化，OD 的漂移需同时补偿 $\mathbf{f}$ 项和 $\frac{1}{2}g^2\nabla\log p$ 扩散项——$\frac{1}{2}$ 来自 Fokker-Planck 中扩散项的系数。逆 SDE 是 $g^2$ 无 $\frac{1}{2}$，因为它保留了随机项来显式建模扩散。

**边缘分布相同的证明思路**：PF-ODE 的 Fokker-Planck 方程与正向 SDE 时间反演后的方程完全一致 →
两个动力学系统产生相同的时序边缘分布 $p_t(\mathbf{x})$。这意味着从同一 $\mathbf{x}_T \sim p_T$ 出发，ODE 采样和 SDE 采样在任意时刻 $t$ 的分布相同 →
**统计意义上生成质量等价**（FID、IS 等分布度量不能区分 ODE 和 SDE 样本）。

**与 DDIM 的关系**：DDIM 的确定采样（$\sigma_t=0$）就是这个 PF-ODE 在特定离散化下的 Euler 步。

**几何对比**：
- **SDE**：随机轨迹，每次不同，适合探索分布的全部模式（覆盖度高）
- **PF-ODE**：确定轨迹，可逆，适合潜空间插值、图像编辑和似然评估
- 两者在分布层面等价，但单次采样行为不同：SDE 多样性更高，ODE 确定可逆

### 2.4 DDPM 和 NCSN 的统一

Score SDE 的统一性在于：**任何以高斯噪声逐步破坏数据的马尔可夫过程，都可以写成 SDE。**

**NCSN**（Noise Conditional Score Network, Song & Ermon 2019）：得分匹配 + Langevin 动力学的先驱。用多个递增噪声水平 $\sigma_1 < \sigma_2 < \cdots < \sigma_N$ 训练得分网络，采样时在每个噪声水平上跑 Langevin MCMC：$\mathbf{x}_{m} = \mathbf{x}_{m-1} + \epsilon\,\mathbf{s}_\theta(\mathbf{x}, \sigma) + \sqrt{2\epsilon}\,\mathbf{z}$。

两种典型的 SDE 设计：

- **VP-SDE**（Variance Preserving，对应 DDPM）：$\mathbf{f} = -\frac{1}{2}\beta(t)\mathbf{x}$, $g(t) = \sqrt{\beta(t)}$。
  方差始终有界：$\text{Var}(\mathbf{x}_t) \to \mathbf{I}$（不会爆炸），$\bar{\alpha}_T \to 0$ 时 $\mathbf{x}_T \sim \mathcal{N}(0,\mathbf{I})$。
- **VE-SDE**（Variance Exploding，对应 NCSN）：$\mathbf{f} = 0$, $g(t) = \sqrt{\frac{d[\sigma^2(t)]}{dt}}$。
  方差随 $t$ 增长到 $\sigma_{\text{max}}^2 \gg 1$，先验为 $\mathcal{N}(0, \sigma_{\text{max}}^2\mathbf{I})$。

**$\mathbf{f}$ 和 $g$ 的设计约束**：只需要保证——
(1) $t=0$ 时 $\mathbf{x}_0 \sim p_{\text{data}}$（噪声为 0）；(2) $t=T$ 时 $\mathbf{x}_T$ 接近纯高斯分布（便于采样起始）。
其余的选择是自由的——不同的 $\mathbf{f},g$ 只是定义了从数据到噪声的不同"路径"。

**本章核心信息**：DDPM 和 NCSN 不是两个不同的方法，而是**同一个 SDE 框架的两种离散化特例**。区别仅在于噪声调度——VP 保持方差有界，VE 让方差自由增长。

**SDE→ODE 转换是通用的**。**任何**形如 $d\mathbf{x} = \mathbf{f}dt + g d\mathbf{w}$ 的 SDE，只要 $\mathbf{f}$ 和 $g$ 足够光滑，都可以通过 PF-ODE 公式 $d\mathbf{x} = [\mathbf{f} - \frac{1}{2}g^2\nabla\log p_t]dt$ 转换为等价的确定 ODE。转换的充分条件是 SDE 有良好定义的 Fokker-Planck 方程——几乎所有实用的 SDE 都满足。

#### 几何直观：得分函数是指向数据的"罗盘"

![得分函数向量场](figures/fig-score-field.png)

左图显示了一个双峰分布 $p(\mathbf{x})$（两个高斯混合）。右图的箭头是**得分函数** $\nabla_{\mathbf{x}}\log p(\mathbf{x})$——每个箭头指向最近的高密度区域。为清晰展示方向，箭头已归一化为等长：

- **箭头的方向**指向密度增长最快的方向（the direction of steepest ascent in probability）
- 每个 mode 像"吸引子"一样吸引周围的点——无论初始位置在哪，顺着箭头走最终都会到达某个峰值

**物理类比**：将 $-\log p(\mathbf{x})$ 看作"势能"（potential energy），则得分函数 $-\nabla\log p$ 就是指向势能最低处的力（force）。扩散模型的逆向过程就像是**粒子在势能场中向低势能区滑动的运动**。

#### SDE vs ODE：随机路径与确定路径

![SDE vs ODE](figures/fig-sde-vs-ode.png)

左图：SDE 从同一个起点出发的 10 条路径——每条不同（随机性）。右图：PF-ODE 从 6 个不同起点出发的确定路径——每个起点唯一确定一条轨迹。

两者的**边缘分布**在所有时间点上完全相同——这意味着 ODE 可以替代 SDE 进行采样。ODE 的优势在于**确定性和可逆性**：给定 $\mathbf{x}_0$ 和 $\mathbf{x}_T$，噪声和图像之间存在一对一的映射——这就是 DDIM 反演和图像编辑的数学基础。

**主线节点 2**：离散扩散 → 连续时间 SDE → PF-ODE，得分函数 $\nabla\log p_t$ 是统一核心。

### 2.5 从 SDE 到训练数据：前向过程的完整解析

理解了 $\mathbf{f}, g, \nabla\log p_t$ 三个量后，自然会问：**前向过程到底怎么跑？训练数据怎么采样？** 本节以 VP-SDE、VE-SDE 和 PF-ODE 为例，从头到尾走一遍。

#### VP-SDE（对应 DDPM）的前向过程

VP-SDE 定义为 $d\mathbf{x} = -\frac{1}{2}\beta(t)\mathbf{x}\,dt + \sqrt{\beta(t)}\,d\mathbf{w}$。

**解析解**（由 §0.7 的 SDE 理论）：这个线性 SDE 有闭式解，其转移分布为：
$$\mathbf{x}_t | \mathbf{x}_0 \sim \mathcal{N}\left(\mathbf{x}_t; \sqrt{\bar{\alpha}(t)}\,\mathbf{x}_0,\; (1-\bar{\alpha}(t))\mathbf{I}\right)$$
其中 $\bar{\alpha}(t) = \exp(-\int_0^t \beta(s)ds)$ 是连续版本的累积信号保留率（对比离散的 $\bar{\alpha}_t = \prod_{s=1}^t(1-\beta_s)$）。

**三个量的对应关系**：
- $\mathbf{f}(\mathbf{x}, t) = -\frac{1}{2}\beta(t)\mathbf{x}$——向原点收缩的力，$\beta(t)$ 越大收缩越快
- $g(t) = \sqrt{\beta(t)}$——噪声注入强度，与收缩力同步增大
- $\nabla\log p_t(\mathbf{x})$——得分，网络要学的量。对于给定的 $\mathbf{x}_0$，条件得分 $= -\frac{\boldsymbol{\epsilon}}{\sqrt{1-\bar{\alpha}(t)}}$

#### VE-SDE（对应 NCSN）的前向过程

VE-SDE 定义为 $d\mathbf{x} = \sqrt{\frac{d[\sigma^2(t)]}{dt}}\,d\mathbf{w}$（$\mathbf{f}=0$，无漂移）。

**解析解**：$\mathbf{x}_t | \mathbf{x}_0 \sim \mathcal{N}(\mathbf{x}_t; \mathbf{x}_0,\; \sigma^2(t)\mathbf{I})$——均值不变，方差随 $t$ 爆炸。

**三个量**：$\mathbf{f}=0$（无漂移，纯噪声累积），$g(t) = \sqrt{d[\sigma^2]/dt}$，得分 $\nabla\log p_t = -\frac{\boldsymbol{\epsilon}}{\sigma(t)}$。

#### 如何采样训练数据

**VP-SDE 具体示例**：

1. **取一张真实图像** $\mathbf{x}_0 \sim p_{\text{data}}$
2. **随机采样时间** $t \sim U(0, T)$
3. **计算 $\bar{\alpha}(t)$**。例如线性调度 $\beta(t) = \beta_{\min} + t(\beta_{\max}-\beta_{\min})$，则 $\bar{\alpha}(t) = \exp(-\beta_{\min}t - \frac{1}{2}(\beta_{\max}-\beta_{\min})t^2)$
4. **采样噪声** $\boldsymbol{\epsilon} \sim \mathcal{N}(0, \mathbf{I})$
5. **构造噪声图像** $\mathbf{x}_t = \sqrt{\bar{\alpha}(t)}\,\mathbf{x}_0 + \sqrt{1-\bar{\alpha}(t)}\,\boldsymbol{\epsilon}$
6. **网络预测** $\hat{\boldsymbol{\epsilon}} = \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)$
7. **Loss** $= \|\boldsymbol{\epsilon} - \hat{\boldsymbol{\epsilon}}\|^2$，反向传播

**SDE/ODE 的通用训练框架**（适用于任意 $\mathbf{f},g$ 设计，不仅是 VP-SDE）：

核心思路是：前向 SDE 定义了从 $\mathbf{x}_0$ 到 $\mathbf{x}_t$ 的随机映射，只要这个映射有**解析解**（闭式条件分布），训练就只需要 $\mathbf{x}_0$ 和噪声——不需要逐步模拟 SDE。

通用步骤：
1. **选定 SDE**：设计 $\mathbf{f}$ 和 $g$，满足 $\mathbf{x}_T \approx$ 纯高斯
2. **求条件分布**：解 Fokker-Planck 或直接解 SDE，得到 $\mathbf{x}_t|\mathbf{x}_0$ 的分布（通常是高斯）
3. **写出条件得分**：$\nabla\log p_{0t}(\mathbf{x}_t|\mathbf{x}_0)$ 由该高斯分布的参数给出
4. **训练网络**：采样 $t$、$\mathbf{x}_0$、$\mathbf{x}_t$，最小化 $\|\mathbf{s}_\theta(\mathbf{x}_t, t) - \nabla\log p_{0t}\|^2$（或等价地预测噪声）
5. **采样生成**：训练完后，用 PF-ODE 或逆 SDE + 数值 solver 从 $\mathbf{x}_T \sim \mathcal{N}(0,\mathbf{I})$ 生成

**关键洞察**：整个过程只需要 $\mathbf{x}_0$ 和 $\boldsymbol{\epsilon}$——因为前向过程有解析解，一步到位得到 $\mathbf{x}_t$，**不需要逐步模拟 SDE**。这是扩散模型与 VAE/flow 的根本区别：前向过程是固定的数学公式，不是学出来的。

#### VP vs VE 的对比总结

| | VP-SDE (DDPM) | VE-SDE (NCSN) |
|---|---|---|
| $\mathbf{f}$ | $-\frac{1}{2}\beta(t)\mathbf{x}$（向原点收缩） | $0$（无漂移） |
| $g(t)$ | $\sqrt{\beta(t)}$ | $\sqrt{d[\sigma^2]/dt}$ |
| $\mathbf{x}_t\mid\mathbf{x}_0$ | $\mathcal{N}(\sqrt{\bar{\alpha}(t)}\mathbf{x}_0, (1-\bar{\alpha}(t))\mathbf{I})$ | $\mathcal{N}(\mathbf{x}_0, \sigma^2(t)\mathbf{I})$ |
| 条件得分 | $-\frac{\boldsymbol{\epsilon}}{\sqrt{1-\bar{\alpha}(t)}}$ | $-\frac{\boldsymbol{\epsilon}}{\sigma(t)}$ |
| 先验 $p_T$ | $\mathcal{N}(0,\mathbf{I})$ | $\mathcal{N}(0, \sigma^2_{\max}\mathbf{I})$ |
| 设计直觉 | 方差始终有界，数值稳定 | 无漂移，纯噪声累积，概念更简单 |

**两种方案的共同点**：无论 VP 还是 VE，前向过程都是**手写的**（$\mathbf{f}$ 和 $g$ 预先选定），唯一的未知量是得分 $\nabla\log p_t$——网络要学的只有这个。

#### PF-ODE 的前向过程

PF-ODE 本身**不是**一个独立的噪声调度——它是从 VP-SDE 或 VE-SDE **推导出来的**确定版本。给定一个 SDE，直接套公式得到对应的 ODE：
$$d\mathbf{x} = \left[\mathbf{f}(\mathbf{x}, t) - \frac{1}{2}g(t)^2\nabla_{\mathbf{x}}\log p_t(\mathbf{x})\right]dt$$

**训练时**：PF-ODE **不参与**。训练只用 SDE 的前向过程采样 $\mathbf{x}_t$（方便、有闭式解）。
**采样时**：PF-ODE 替代 SDE（或逆 SDE）——更快（高阶 solver）、确定（可逆）。

以 VP-SDE 为例，其 PF-ODE 为：
$$d\mathbf{x} = \left[-\frac{1}{2}\beta(t)\mathbf{x} - \frac{1}{2}\beta(t)\nabla_{\mathbf{x}}\log p_t(\mathbf{x})\right]dt$$

训练完 $\boldsymbol{\epsilon}_\theta$ 后，代入 $\nabla\log p_t = -\boldsymbol{\epsilon}_\theta/\sqrt{1-\bar{\alpha}(t)}$，OD 变成纯网络驱动的确定动力学——这就是 DPM-Solver 和 DDIM 的数学基础。

---

## 第三章：信号噪声比——变分视角的统一语言

### 3.0 问题引入：为什么需要 SNR？

前两章用 $\beta_t, \bar{\alpha}_t$ 描述噪声调度，用 $\mathbf{f}, g$ 定义 SDE。但有一个隐患：**参数太多，且互相冗余**。回忆一下：
- 离散 DDPM：$\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}$，用 $\bar{\alpha}_t$ 做参数
- VDM 连续版：$\mathbf{x}_t = \alpha_t\mathbf{x}_0 + \sigma_t\boldsymbol{\epsilon}$，有两个参数 $\alpha_t, \sigma_t$

问题：$\alpha_t$ 和 $\sigma_t$ 不是独立的——通常 $\alpha_t^2 + \sigma_t^2 = 1$（VP）或 $\alpha_t = 1$（VE）。能否用**一个**变量同时描述"信号有多强"和"噪声有多大"？

答案就是 **SNR（Signal-to-Noise Ratio，信噪比）**——信号的功率与噪声功率之比：
$$\text{SNR}(t) = \frac{\alpha_t^2}{\sigma_t^2}, \qquad \mathbf{x}_t = \alpha_t\mathbf{x}_0 + \sigma_t\boldsymbol{\epsilon}$$

$\alpha_t^2$ 是信号保留的能量，$\sigma_t^2$ 是噪声注入的能量。SNR 大 → 信号主导（数据清晰），SNR 小 → 噪声主导（模糊）。一个数，统一了 $\alpha_t$ 和 $\sigma_t$。

### 3.1 关键定理：VLB 的噪声调度不变性

VLB（Variational Lower Bound）就是 §0.5 的 ELBO——变分下界。VDM（Variational Diffusion Models, Kingma et al. 2021）是第一个用 SNR 语言系统分析扩散模型的框架，将 DDPM 的离散公式推广到连续时间。VDM 用"VLB"这个称呼，本质是同一个东西：$\log p(\mathbf{x}) \geq \text{VLB}$。

VDM 的核心发现：用 SNR 参数化后，连续时间 VLB 写成极简形式：

$$-\text{VLB} = \frac{1}{2}\mathbb{E}_{t,\boldsymbol{\epsilon}}\left[\frac{d\log\text{SNR}}{dt}\big\|\boldsymbol{\epsilon} - \hat{\boldsymbol{\epsilon}}_\theta(\mathbf{x}_t, t)\big\|^2\right]$$

**VLB 与 Loss 的关系**：$-\text{VLB}$（负 VLB）就是训练用的 Loss。最大化 ELBO/VLB $\iff$ 最小化 $-\text{VLB}$。上表中三行都是 Loss 的不同写法：DDPM 的 $\mathcal{L}_{\text{simple}}$ 是近似，Score SDE 的 $\mathcal{L}_{\text{score}}$ 是连续化，VDM 的 $-\text{VLB}$ 给出了最优的权重系数。

**与前面公式的对比**：

| 公式 | 来源 | 形式 |
|------|------|------|
| $\mathcal{L}_{\text{simple}} = \mathbb{E}\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta\|^2$ | §1.2 DDPM | 离散时间，等权重 |
| $\mathcal{L}_{\text{score}} = \mathbb{E}[\lambda(t)\|\mathbf{s}_\theta - \nabla\log p_{0t}\|^2]$ | §2.2 Score SDE | 连续时间，任意权重 $\lambda(t)$ |
| $-\text{VLB} = \frac{1}{2}\mathbb{E}[\frac{d\log\text{SNR}}{dt}\|\boldsymbol{\epsilon} - \hat{\boldsymbol{\epsilon}}_\theta\|^2]$ | 本章 VDM | 连续时间，SNR 自然权重 |

VDM 的贡献在于确定了最优权重：$\lambda(t) = \frac{d\log\text{SNR}}{dt}$。

**理解这个权重**：VLB 公式中 $\frac{d\log\text{SNR}}{dt}$ 是每个时间 $t$ 的 Loss 权重。
如果直接按 $t \sim U(0,T)$ 均匀采样时间，SNR 变化快的区域（如 $t$ 接近 $0$ 或 $T$）权重过大，
中间区域权重过小——训练不均衡。

**SNR 空间**是指用 $\lambda = \log\text{SNR}$ 代替 $t$ 作为自变量。
在这个空间里，$\frac{d\log\text{SNR}}{dt}dt = d\lambda$，VLB 简化为：
$$-\text{VLB} \propto \mathbb{E}_{\lambda}\big[\|\boldsymbol{\epsilon} - \hat{\boldsymbol{\epsilon}}_\theta\|^2\big]$$
权重消失了——每个对数 SNR 水平贡献相同。在 $\lambda$ 空间均匀采样，所有噪声水平（从几乎干净到几乎纯噪声）获得相等的训练关注度。这避免了某些 SNR 区域"吃不饱"、某些"吃撑"的问题。

**VDM 的前向/逆向过程与 DDPM 的区别**：VDM 用 $\alpha_t, \sigma_t$ 参数化（不强制 $\alpha_t^2 + \sigma_t^2 = 1$），前向过程仍是 $\mathbf{x}_t = \alpha_t\mathbf{x}_0 + \sigma_t\boldsymbol{\epsilon}$，逆向仍是高斯条件分布。区别在于 SNR 参数化使得噪声调度可以**学习**——VDM 证明了调度只影响训练效率（不影响最终 VLB），因此可以选择使训练方差最小的调度，而非手工设计。

**定理**：连续时间 VLB 只依赖于端点 SNR 值——而不依赖于具体的噪声调度路径。

这意味着：只要 $\text{SNR}(0) \gg 1$（干净数据）和 $\text{SNR}(T) \ll 1$（纯噪声），任何单调递减的 SNR 函数都等价。

**具体示例**：取 $T=1$，三种调度：
- **线性** $\beta(t) = 0.1 + 19.9t$ → $\text{SNR}(t) \approx \exp(-0.1t - 9.95t^2)$
- **余弦** $\beta(t)$ 使 $\bar{\alpha}(t) = \cos^2(\frac{\pi}{2}t)$ → $\text{SNR}(t) = \frac{\cos^2(\pi t/2)}{1-\cos^2(\pi t/2)}$
- **指数** $\text{SNR}(t) = e^{-20t}$

三个调度的 $\text{SNR}(0) \approx \infty$，$\text{SNR}(1) \approx 0$。VDM 定理保证：三个模型训练出来的**生成模型完全相同**——中间的路径选择只影响训练效率。

![SNR调度](figures/fig-snr-schedule.png)

**左图**：三种 SNR 调度——线性、余弦、指数。**右图**：端点相同则 VLB 等价。这就像爬山——不管走哪条路，只要从山脚（噪声，SNR≈0）爬到山顶（数据，SNR→∞），终点相同。

### 3.2 SNR 的物理和几何意义

**物理意义**：SNR 是信号能量与噪声能量之比。工程中常用的分贝单位：$\text{SNR}_{\text{dB}} = 10\log_{10}(\text{SNR})$。扩散前向过程把 SNR 从 $+\infty$ dB（纯信号）拉到 $-\infty$ dB（纯噪声）。

**几何意义**：$\mathbf{x}_t = \alpha_t\mathbf{x}_0 + \sigma_t\boldsymbol{\epsilon}$。在 VP 情形 $\alpha_t^2 + \sigma_t^2 = 1$，$\mathbf{x}_t$ 在半径为 $\Vert\mathbf{x}_0\Vert$ 的球面上——SNR 是信号分量 $\alpha_t$ 和噪声分量 $\sigma_t$ 的长度比平方。SNR 从 $\infty$（$\alpha=1,\sigma=0$）单调降到 $0$（$\alpha=0,\sigma=1$）。

**对数 SNR $\lambda_t$**：$\lambda_t = \frac{1}{2}\log\text{SNR} = \log(\alpha_t/\sigma_t)$。为什么取对数？SNR 从前到后跨越 6+ 个数量级（$10^6 \to 10^{-6}$），对数空间均匀采样才能让训练均匀覆盖各噪声水平。第五章将看到，基于 $\lambda$ 的 ODE 求解器能大幅压缩采样步数。

**主线节点 3**：SNR 统一了 $\alpha_t$ 和 $\sigma_t$。噪声调度的具体路径不重要，端点 SNR 才重要。对数 SNR $\lambda_t$ 是 ODE 的自然坐标。

---

## 第四章：引导与控制——得分空间的贝叶斯规则

### 4.0 问题引入：从"随机出图"到"按需生成"

至此我们训练的扩散模型只能**无条件生成**——从随机噪声出发，抽到什么算什么。
但我们想要的是：给定文字描述"一只猫"，就生成猫的图片；给定"夕阳下的海滩"，就画海滩。

换句话说，我们需要的是**条件生成** $p(\mathbf{x} \mid c)$，其中 $c$ 是条件（文字、类别标签等）。

**直接做法**：把条件 $c$ 输入网络，从头训练一个条件扩散模型。这确实可行，但成本高——每换一种条件（文字、类别、布局……）都要重新训练。

**引导的做法**：训练一个无条件模型，然后在采样时"引导"它朝条件方向偏移。不需要重新训练模型，只需要在采样过程中修改得分。

**核心思想**：采样过程由得分函数驱动（第二章），如果能将"靠近条件"编码为得分的修正，就等于在采样时告诉模型"往这个方向走"。引导的本质就是**在得分空间施加一个偏转力**。

### 4.1 Classifier Guidance——用分类器偏转得分

**思路**：既然得分 $\nabla\log p(\mathbf{x})$ 指向"更像真实图像"的方向，那加一个"更像类别 $y$"的梯度，不就同时满足两者了？

**贝叶斯推导**：
$$p(\mathbf{x} \mid y) = \frac{p(y \mid \mathbf{x})\,p(\mathbf{x})}{p(y)}$$
取对数梯度（$p(y)$ 是常数，梯度为零）：
$$\nabla_{\mathbf{x}}\log p(\mathbf{x} \mid y) = \nabla_{\mathbf{x}}\log p(y \mid \mathbf{x}) + \nabla_{\mathbf{x}}\log p(\mathbf{x})$$

这是标准贝叶斯。但实践中 $p(y \mid \mathbf{x})$ 不够强——我们想**更强调**条件。于是引入放大系数 $w$：
$$\nabla_{\mathbf{x}}\log p_w(\mathbf{x} \mid y) = \underbrace{\nabla_{\mathbf{x}}\log p(\mathbf{x})}_{\text{无条件得分}} + w \cdot \underbrace{\nabla_{\mathbf{x}}\log p(y \mid \mathbf{x})}_{\text{分类器梯度}}$$

$w = 1$：标准贝叶斯。$w > 1$：放大条件信号——生成样本更"像"类别 $y$。$w \to \infty$：只关注类别，忽略多样性。

**在扩散模型中落地**：需要一个能对**噪声图像** $\mathbf{x}_t$ 做分类的分类器 $p_\phi(y \mid \mathbf{x}_t)$（需要在噪声数据上额外训练）。采样时用它计算梯度，修正噪声预测：
$$\hat{\boldsymbol{\epsilon}}_\theta(\mathbf{x}_t, y) = \boldsymbol{\epsilon}_\theta(\mathbf{x}_t) - w\sqrt{1-\bar{\alpha}_t}\,\nabla_{\mathbf{x}_t}\log p_\phi(y \mid \mathbf{x}_t)$$

注意：$\boldsymbol{\epsilon}_\theta(\mathbf{x}_t)$ 是**无条件**扩散模型（网络没见过 $y$），$\hat{\boldsymbol{\epsilon}}_\theta$（戴帽子）是采样时被分类器**修正后**的预测。$\nabla p_\phi(y\mid\mathbf{x}_t)$ 来自独立训练的分类器 $p_\phi$。$y$ 变化时，只改分类器的输入标签，扩散模型和分类器都**不需要重训**——引导是在采样时动态计算的。

**为什么扩散模型没见过类别也能被"引导"？** 可以把得分函数理解成一张地图——$\nabla\log p(\mathbf{x})$ 告诉你在当前位置 $\mathbf{x}$ 往哪走能找到"真图像"。分类器梯度 $\nabla\log p(y\mid\mathbf{x})$ 告诉你往哪走能找到"类别 $y$"。两个方向的向量叠加，就是同时往"真图像"和"类别 $y$"走。扩散模型不需要知道"类别 $y$ 长什么样"——它只需要知道"真图像在哪"就够了，分类器负责"在真图像中挑出 $y$"。两者分工：扩散模型画边界（区分真/假），分类器在边界内指方向（区分类别）。

**缺点**：需要额外训练一个对噪声图像做分类的分类器，实现复杂。

### 4.2 Classifier-Free Guidance——扔掉分类器

**思路**：能否不要分类器，直接从扩散模型本身获得引导信号？

**观察**：$\nabla_{\mathbf{x}}\log p(\mathbf{x} \mid c) - \nabla_{\mathbf{x}}\log p(\mathbf{x})$ 就是"条件 $c$ 对得分的影响"——一个指向条件方向的向量。如果网络同时学会条件得分和无条件得分，两者的差自然就是引导方向。

**训练**：以概率 $p_{\text{uncond}}$（通常 10%-20%）将条件标签替换为空（$\varnothing$），同一个网络同时学习：
- 有条件时：$\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, c, t)$
- 无条件时：$\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, \varnothing, t)$

**采样**：条件方向 = $\boldsymbol{\epsilon}_\theta(c) - \boldsymbol{\epsilon}_\theta(\varnothing)$，沿此方向外推：
$$\tilde{\boldsymbol{\epsilon}}_\theta(\mathbf{x}, c) = \boldsymbol{\epsilon}_\theta(\mathbf{x}, \varnothing) + w\big[\boldsymbol{\epsilon}_\theta(\mathbf{x}, c) - \boldsymbol{\epsilon}_\theta(\mathbf{x}, \varnothing)\big]$$

或者等价地：
$$\tilde{\boldsymbol{\epsilon}}_\theta(\mathbf{x}, c) = (1+w)\boldsymbol{\epsilon}_\theta(\mathbf{x}, c) - w\,\boldsymbol{\epsilon}_\theta(\mathbf{x}, \varnothing)$$

**训练目标完全相同**：Loss 仍是 $\mathcal{L}_{\text{simple}} = \|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, \tilde{c}, t)\|^2$，唯一变化是条件输入 $\tilde{c}$ 以概率 $p_{\text{uncond}}$ 被替换为 $\varnothing$。推理时再把 $\boldsymbol{\epsilon}_\theta(\varnothing)$ 和 $\boldsymbol{\epsilon}_\theta(c)$ 叠加即得引导。

**为什么叫 classifier-free**：不需要显式分类器。条件得分和无条件得分的差本身就编码了"条件信息的方向"。

**它为什么有效**：在得分空间，无条件得分指向"成为一张真实图像"，条件得分指向"成为一张符合描述 $c$ 的真实图像"。两者的差就是"更像 $c$ 的方向"。CFG 做的事情就是沿这个方向多走一步。

**CFG 成为标准**：实现极其简单——训练时随机丢条件，采样时做加权组合。它成为 Stable Diffusion、DALL·E、Imagen 等所有大规模文生图模型的标配。

### 4.3 最小实现：Stable Diffusion 的核心骨架

以 Stable Diffusion（§5.1 的 Latent Diffusion 架构）为例，下面是去除所有优化后的最简训练和推理伪代码：

```python
# ===== 组件 =====
vae = AutoencoderKL()           # 图像↔潜空间 8×压缩
unet = UNet2DCondition()        # 潜空间去噪网络
clip = CLIPTextModel()          # 文本编码器
noise_scheduler = DDPMScheduler()  # 噪声调度

# ===== 训练 =====
for images, captions in dataloader:
    # 1. 文本编码
    text_emb = clip(captions)  # [B, 77, 768]

    # 2. 图像→潜空间
    latents = vae.encode(images)  # [B, 4, H/8, W/8]

    # 3. 加噪
    t = random.randint(0, T)
    noise = randn_like(latents)
    noisy = sqrt(alpha_bar[t]) * latents + sqrt(1-alpha_bar[t]) * noise

    # 4. CFG 训练：随机丢弃条件
    if random() < p_uncond:
        text_emb = zero_like(text_emb)  # 无条件训练

    # 5. 预测噪声 + Loss
    pred_noise = unet(noisy, t, text_emb)
    loss = mse_loss(noise, pred_noise)
    loss.backward(); optimizer.step()

# ===== 推理（CFG 采样）=====
latents = randn([1, 4, 64, 64])          # 纯噪声潜变量
text_emb_cond = clip("a cat")            # 条件编码
text_emb_uncond = clip("")               # 无条件编码（空字符串）

for t in range(T, 0, -1):
    # CFG：条件 + 无条件预测叠加
    eps_cond   = unet(latents, t, text_emb_cond)
    eps_uncond = unet(latents, t, text_emb_uncond)
    eps = eps_uncond + w * (eps_cond - eps_uncond)  # CFG 公式

    # DDIM 步
    latents = scheduler.step(eps, t, latents)

image = vae.decode(latents)              # 潜空间→图像
```

**三个关键组件**：VAE 压缩图像（降低计算量）、U-Net 在潜空间去噪、CLIP 编码文本条件。CFG 的威力体现在推理的极简两行：分别跑条件和无条件预测，加权叠加。

#### 几何直观：引导是分布空间的"锐化"

![引导几何](figures/fig-guidance-geometry.png)

**图的含义**：横轴是生成样本的某一特征值 $x$（如"猫的毛色从白到黑"），纵轴是概率密度 $p(x)$。两条虚曲线分别代表无条件分布（灰虚线）和条件分布（蓝色模式附近）。彩色实线是不同 $w$ 下的引导结果。

**左图（Classifier Guidance）**：$w=1$（灰色）是标准贝叶斯条件分布——诚实地反映了分类器提供的信息。$w=3$（红色）时峰值变高、变窄、向条件模式方向偏移——这就是**锐化**：分布被挤压到分类器认为"最像目标类别"的狭窄区域。

**右图（CFG）**：$w=1$（灰色）接近无条件分布。$w=5$（蓝色）时分布向条件方向大幅偏移，峰值高度增至数倍——这就是 CFG 在实践中 $w=5\sim 7$ 的标准用法。

**锐化的直观理解**：无条件模型生成的样本平均分布在所有可能模式上；加上引导后，得分在每个采样步都朝条件方向偏转，重复数百步积累的效果就是——初始的宽广分布被"挤压"成尖峰，像用手把一团面捏成细条。$w$ 越大，捏得越细，样本越集中在条件描述的核心特征上，但极端多样性丧失（所有样本趋于雷同）。

**峰值偏移的意义**：$w=3/5$ 时峰值略偏向条件模式一侧（不是完全在模式正上方），这是因为引导力在得分空间是加法，在分布空间会压缩方差同时微调均值位置。

---

## 第五章：概率流范式——从去噪得分到向量场
### 5.0 问题引入：扩散的弯路径

回顾扩散模型的前向过程：$\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}$。从数据到噪声的路径是**弯曲的**——在空间中走的是弧线而非直线。弯曲有什么问题？两点：
1. **采样步数多**：弯路径需要小步长才能用 Euler 方法精确跟踪，大跨步会偏离轨道。
2. **训练信号不均匀**：不同 $t$ 处 SNR 变化速率不同（第三章），有些地方学得不充分。

能否直接定义**直线路径**？从噪声直接滑到数据，没有弯绕？

> **注**：Flow Matching 时间约定与扩散相反——$t=0$ 是纯噪声，$t=1$ 是干净数据 $\mathbf{x}_0$。这是 FM 文献的标准写法。本节遵循此约定，但数据样本始终记为 $\mathbf{x}_0$。

### 5.1 Flow Matching——直接学习向量场 (Lipman et al., 2023)

**核心思想**：不再从 SDE 推导，而是直接定义一条从噪声（$t=0$）到数据 $\mathbf{x}_0$（$t=1$）的概率路径 $p_t(\mathbf{x})$。设 $u_t(\mathbf{x})$ 是驱动这条路径的**目标向量场**（真实的速度），$v_t^\theta(\mathbf{x})$ 是我们用网络去拟合它的**学习向量场**。关系：$u_t$ 是 ground truth（训练目标），$v_t^\theta$ 是网络的输出（预测值），类似 DDPM 中 $\boldsymbol{\epsilon}$（真实噪声）vs $\boldsymbol{\epsilon}_\theta$（预测噪声）。
$$d\mathbf{x}_t = u_t(\mathbf{x}_t)\,dt, \quad \text{用 } v_t^\theta \text{ 逼近 } u_t$$

**关键问题**：$v_t$ 没有监督信号——我们不知道"正确的速度"是什么。

**条件 Flow Matching 技巧**：

关键障碍：总概率路径 $p_t(\mathbf{x})$ 和**总向量场** $u_t(\mathbf{x})$ 都是未知的（涉及对所有数据积分）。$u_t(\mathbf{x})$ 是驱动 $p_t(\mathbf{x})$ 演化的速度场——$d\mathbf{x} = u_t(\mathbf{x})dt$。它在 Flow Matching 中的角色等价于扩散模型中 PF-ODE 的漂移项 $[\mathbf{f} - \frac{1}{2}g^2\nabla\log p_t]$（§2.3）——两者都是"粒子该怎么走"的确定速度。区别在于：扩散先学得分 $\nabla\log p_t$，再组合成速度；FM 直接学这个速度。但如果我们限定在**一个样本**上，事情就简单了。

对某个具体训练样本 $\mathbf{x}_0$（一张真实图像），定义**条件概率路径** $p_t(\mathbf{x} \mid \mathbf{x}_0)$——
在时间 $t$，给定终点是 $\mathbf{x}_0$，当前噪声样本 $\mathbf{x}$ 的概率分布。
设条件高斯路径为 $p_t(\mathbf{x}\mid\mathbf{x}_0) = \mathcal{N}(\mathbf{x}; \mu_t(\mathbf{x}_0), \sigma_t^2\mathbf{I})$，则条件向量场的闭式解为：
$$u_t(\mathbf{x}\mid\mathbf{x}_0) = \frac{d\mu_t}{dt} + \frac{d\sigma_t}{dt}\cdot\frac{\mathbf{x} - \mu_t}{\sigma_t}$$
这个公式是通用的——给定均值和方差的导数，向量场直接写出。两个例子：
- **扩散路径**（$\mu_t = \mathbf{x}_0$，$\sigma_t$ 递增）：$u_t = \frac{d\sigma_t}{dt}\cdot\frac{\mathbf{x} - \mathbf{x}_0}{\sigma_t}$——向量指向 $\mathbf{x}_0$，被方差变化率缩放
- **OT 直线路径**（$\mu_t = t\mathbf{x}_0$，$\sigma_t = 1-t$）：$u_t = \mathbf{x}_0 - \frac{\mathbf{x} - t\mathbf{x}_0}{1-t} = \frac{\mathbf{x}_0 - \mathbf{x}}{1-t}$

现在定义两个 Loss：
- $\mathcal{L}_{\text{FM}}(\theta) = \mathbb{E}_{t,p_t(\mathbf{x})}\|v_\theta(\mathbf{x},t) - u_t(\mathbf{x})\|^2$——匹配未知的总向量场（无法直接算）
- $\mathcal{L}_{\text{CFM}}(\theta) = \mathbb{E}_{t,q(\mathbf{x}_0),p_t(\mathbf{x}\mid\mathbf{x}_0)}\|v_\theta(\mathbf{x},t) - u_t(\mathbf{x}\mid\mathbf{x}_0)\|^2$——匹配条件向量场（可以算！）

**核心定理**：两者的梯度相等——$\nabla_\theta\mathcal{L}_{\text{FM}} = \nabla_\theta\mathcal{L}_{\text{CFM}}$。
这意味着**用条件路径训练等价于用总路径训练**，而条件路径的向量场 $u_t(\mathbf{x}\mid\mathbf{x}_0)$ 对每个样本都可以解析计算，训练变得可行。

**扩散是特例**：如果选 $p_t(\mathbf{x}\mid\mathbf{x}_0) = \mathcal{N}(\mathbf{x}; \mathbf{x}_0, \sigma_t^2\mathbf{I})$（均值固定在 $\mathbf{x}_0$，方差随 $t$ 增大），条件向量场为 $u_t(\mathbf{x}\mid\mathbf{x}_0) = \frac{\mathbf{x}_0 - \mathbf{x}}{\sigma_t}\frac{d\sigma_t}{dt}$。代入 CFM Loss，等价于匹配得分 $\nabla\log p_t(\mathbf{x}\mid\mathbf{x}_0)$——退化为标准扩散的得分匹配。

**OT 直线路径**：Flow Matching 的真正威力在于可以选更优的路径。最优传输路径直接走直线：
$$p_t(\mathbf{x}\mid\mathbf{x}_0) = \mathcal{N}(\mathbf{x}; t\mathbf{x}_0, (1-t)^2\mathbf{I})$$

**为什么叫"直线"**：条件均值 $\mu_t = t\mathbf{x}_0$ 在空间中沿直线从 $0$（$t=0$，噪声）均匀移动到 $\mathbf{x}_0$（$t=1$，数据）。每个样本的轨迹近乎笔直。

**SNR 约束**：$\text{SNR}(t) = t^2/(1-t)^2$，满足端点条件 $\text{SNR}(0)=0$（纯噪声）、$\text{SNR}(1)\to\infty$（纯净数据）。第三章的 VLB 调度不变性对 FM 不直接适用——FM 没有 VLB，它直接回归向量场。但 SNR 端点约束的思想是一致的：只要路径从噪声走到数据，中间怎么走都行，直线是最短的。

直线 = 最简单的向量场 = 训练更快、采样步数更少。

#### 直觉对比：得分 vs 向量场

得分 $\nabla\log p_t$ 指向密度增长最快的方向——它是概率密度 $p_t$ 的**空间**几何描述。
但 PF-ODE 的漂移项 $[\mathbf{f} - \frac{1}{2}g^2\nabla\log p_t]$ 多出了 $\mathbf{f}$ 和 $g^2$。
得分本身不就是天然的速度场吗？为什么不能直接用 $\nabla\log p_t$ 做漂移？

**核心原因：得分描述的是"密度在哪"，不是"粒子怎么动"。**

看前向 SDE：$d\mathbf{x} = \mathbf{f}dt + g d\mathbf{w}$。粒子在两个力驱动下运动——确定性的漂移 $\mathbf{f}$（人工设计的，推粒子朝噪声方向走）和随机扩散 $g d\mathbf{w}$（布朗运动，把粒子散布开来）。得分 $\nabla\log p_t$ 是 $p_t$ 密度的梯度——它告诉你**当前**状态下"哪里密度更高"，但**不包含粒子是如何到达当前状态的动力学信息**。换句话说：
- 得分告诉你"数据源头在哪个方向"（密度往上走）
- 但它不知道"水流 $\mathbf{f}$ 正把你往下游冲"（前向漂移）

如果你只用 $-\nabla\log p_t$ 做逆向漂移（忽略 $\mathbf{f}$ 和 $g$），粒子会朝密度峰值走，但**不会沿时间反演的轨迹走**——你会得到一个新的概率流，其边缘分布不等于 $p_t$。

**从 Fokker-Planck 方程看**：$p_t$ 的演化由 $\partial_t p = -\nabla\cdot(\mathbf{f}p) + \frac{1}{2}\nabla\cdot(g^2\nabla p)$ 描述。
时间反演后（$t \to T-t$），这个方程要求漂移变为 $\mathbf{f} - g^2\nabla\log p_t$（逆 SDE）或 $\mathbf{f} - \frac{1}{2}g^2\nabla\log p_t$（PF-ODE，确定性）。两式中 $\mathbf{f}$ 和 $g$ 的出现是**强制性的**——它们来自正向 SDE 的物理过程，不是可选修饰。

**Flow Matching 的洞察**：既然 $\mathbf{f}$ 和 $g$ 是已知的（你设计的），得分是唯一需要学的量，整个 PF-ODE 漂移就是 $\mathbf{f}$、$g$、$\nabla\log p_t$ 的代数组合。FM 说：这个组合本身也是一个向量场 $u_t$，为什么不直接学它？FM 绕开了"分拆→分别建模→再组合"的过程，直接在向量场空间做端到端回归。

### 5.2 Rectified Flow——让流越来越直 (Liu et al., 2023)

**动机**：Flow Matching 的直线路径需要精心选择条件分布。Rectified Flow 给了一个更直接的配方：把数据对 $(X_0, X_1)$ 的线性插值当目标：
$$X_t = tX_1 + (1-t)X_0$$

训练极简——向量 $X_1-X_0$ 沿直线是常数，直接做回归：
$$\min_v \mathbb{E}_{(X_0,X_1),t}\Big[\|(X_1 - X_0) - v(X_t, t)\|^2\Big]$$

**Reflow——核心创新**：第一次训练的流通常还是弯的（因为随机配对 $X_0,X_1$ 会导致轨迹交叉）。Reflow 的做法：
1. 用学到的流生成新配对 $(Z_0, Z_1)$——这些配对沿流是因果相关的
2. 用新配对**重新训练**
3. 重复——每次都更直

理论上两步 Reflow 后流几乎完全直线，1 次 Euler 步即可精准模拟。就像用 GPS 反复优化路线——每次迭代都更接近最短路径。

### 5.3 统一视角：SiT 的实验结论 (Ma et al., 2024)

SiT 在统一插值框架 $\mathbf{x}_t = \alpha_t\mathbf{x}_* + \sigma_t\boldsymbol{\epsilon}$ 下系统比较：
- **预测噪声 $\epsilon$**：DDPM 传统，适合高 SNR
- **预测 $\mathbf{x}_0$**：去噪目标，适合低 SNR
- **$v$-prediction**：$v = \alpha_t\epsilon - \sigma_t\mathbf{x}_0$，统一两者

**结论**：Flow Matching + $v$-prediction + ODE 采样在 ImageNet 上全面超越传统扩散。

#### 几何直观

![概率路径](figures/fig-probability-path.png)
概率密度从先验到数据平滑变形。Flow Matching 学习驱动这条变形的速度场。

![OT vs Diffusion](figures/fig-ot-vs-diffusion.png)
扩散路径（左）弯曲，OT 路径（右）笔直。直线 = Euler 完美 = 少步精准。

**主线节点 5**：扩散→Flow 是自然进化。直线路径训练更快、采样更少、效果更好。

---

## 第六章：一步生成——从 ODE 到自洽性

### 6.0 问题引入：能不能一步到位？

前面几章的方法——无论是扩散（§2.3 的 PF-ODE）还是 Flow Matching（§5.1 的直线 ODE）——都需要**多步 ODE 求解**，每一步都要跑一遍网络。能不能**一步生成**？从噪声开始，一次网络前向就输出干净图像？

### 6.1 Consistency Models——把 ODE 轨迹折叠成一个点 (Song et al., 2023)

**核心洞察**：任何 ODE（扩散的 PF-ODE 或 FM 的 Flow ODE）都将噪声 $\mathbf{x}_T$ 光滑地映射到数据 $\mathbf{x}_0$。关键观察：如果训练一个网络，让它学习"从轨迹上任意一点直接跳回原点"，一步就够了。这个思想**不依赖 ODE 的类型**——PF-ODE 还是 Flow ODE 只是具体的轨迹形状不同。

**自洽性条件**：定义一致性函数 $f(\mathbf{x}_t, t) \to \mathbf{x}_0$，要求同一 ODE 轨迹上任意两点映射到同一结果：
$$\forall t, t': \quad f(\mathbf{x}_t, t) = f(\mathbf{x}_{t'}, t') = \mathbf{x}_0$$

**两种训练方式**：

| | 蒸馏 | 独立训练 |
|---|---|---|
| 需要预训练模型？ | 是 | 否 |
| 训练数据来源 | 预训练模型 + ODE solver 生成相邻点对 | 重参数化直接生成 $\mathbf{x}_t = t\mathbf{x}_0 + (1-t)\boldsymbol{\epsilon}$ |
| 对扩散适用？ | ✓ | ✓（用扩散的 $\alpha_t, \sigma_t$ 重参数化） |
| 对 FM 适用？ | ✓ | ✓（FM 的直线路径天然适配重参数化） |

**FM 下的独立训练尤其简单**：因为 $\mathbf{x}_t = t\mathbf{x}_0 + (1-t)\boldsymbol{\epsilon}$ 路径本身就是直线，相邻时间步 $\mathbf{x}_{t_n}$ 和 $\mathbf{x}_{t_{n+1}}$ 沿同一直线，不需要复杂的噪声调度转换。训练 Loss 为：
$$\mathcal{L} = \mathbb{E}_{\mathbf{x}_0,\mathbf{z},n}\Big[d\big(f_\theta(\mathbf{x}_0 + t_{n+1}\mathbf{z},\,t_{n+1}),\; f_{\theta^-}(\mathbf{x}_0 + t_n\mathbf{z},\,t_n)\big)\Big]$$

**采样**：$\hat{\mathbf{x}}_0 = f_\theta(\mathbf{x}_T, T)$，无论底层是扩散还是 FM——一次网络前向即可。也可以多步精炼提升质量。

#### 几何直观

![一致性模型](figures/fig-consistency-model.png)
每条彩色曲线是 ODE 轨迹（可以是 PF-ODE 或 Flow ODE）。自洽性 = 曲线上所有点都映射到同一个星形 $\mathbf{x}_0$。小段一致性通过链式传播覆盖全轨迹。

**主线节点 6**：自洽性是 ODE 的通用性质——无论底层是扩散还是 FM，轨迹上所有点映射到同一原点，一步生成成为可能。

---

## 第七章：从 U-Net 到 Transformer——通往规模化之路

### 7.0 问题引入：U-Net 的瓶颈

前面各章的所有模型都基于 U-Net：一个编码器-解码器结构，用卷积提取特征，用跳跃连接保留细节。但 LLM 领域已经证明——Transformer + 更大规模 = 更好的性能。而 U-Net 不像 Transformer 那样天然可无限堆叠：卷积感受野有限、跳跃连接固定了分辨率层级、没有统一的 token 接口。本章讲两件事：**DiT 把 U-Net 换成 Transformer**，**SD3 把全书数学整合到一个 80 亿参数模型**。

### 7.1 DiT——用 Transformer 做扩散 (Peebles & Xie, 2023)

#### 从 U-Net 到 DiT 的思维过程

回顾 §1.2 的 DDPM 训练：网络输入是噪声图像 $\mathbf{x}_t$ 和时间步 $t$，输出是预测噪声。网络需要知道两件事：图像的结构（**空间信息**）和当前噪声水平（**时间条件**）。U-Net 用卷积处理空间、用广播注入时间。DiT 换了一种思路：把图像当成 token 序列（像 ViT），把时间条件融入 Transformer 的每一层。

#### U-Net 的骨架（简化代码）

```python
class UNetBlock(nn.Module):
    def forward(self, x, t_emb):
        h = self.conv1(x)
        h = h + self.time_proj(t_emb)[:, :, None, None]  # 时间条件广播到所有空间位置
        h = F.relu(h)
        return h
```

时间嵌入为什么要广播到每个空间位置？因为噪声是在整个图像上**均匀**添加的——$t$ 时刻每个像素被同等程度的噪声污染。所以网络在每个位置都需要知道"现在是第几步"来决定去噪力度。广播是最简单的实现方式。

#### DiT 的骨架（简化代码）

**DiT 的做法**（Patchify + Transformer + AdaLN）：

```python
class DiTBlock(nn.Module):
    def __init__(self, dim, num_heads):
        self.norm1 = nn.LayerNorm(dim, elementwise_affine=False)  # 不做自带缩放
        self.attn  = nn.MultiheadAttention(dim, num_heads)
        self.norm2 = nn.LayerNorm(dim, elementwise_affine=False)
        self.mlp   = nn.Sequential(nn.Linear(dim, 4*dim), nn.GELU(), nn.Linear(4*dim, dim))
        self.adaLN_modulation = nn.Sequential(nn.SiLU(), nn.Linear(cond_dim, 6*dim))

    def forward(self, x, c):
        # c 是条件向量（时间步+类别嵌入），通过 MLP 生成 6 组参数
        shift_msa, scale_msa, gate_msa, shift_mlp, scale_mlp, gate_mlp = \
            self.adaLN_modulation(c).chunk(6, dim=1) 

        # Self-Attention with AdaLN
        x = x + gate_msa * self.attn(
            self.norm1(x) * (1 + scale_msa) + shift_msa
        )
        # MLP with AdaLN
        x = x + gate_mlp * self.mlp(
            self.norm2(x) * (1 + scale_mlp) + shift_mlp
        )
        return x
```

核心差异：U-Net 用卷积 + 时间广播注入条件；DiT 把图像当 token 序列，用 AdaLN 注入条件。

**六组参数的含义**：`adaLN_modulation(c)` 从条件向量生成 6 组向量，每组维度 = token 维度。三对参数分别作用于 Self-Attention 和 MLP 两个子层：

| 参数 | 子层 | 作用 | 直观理解 |
|------|------|------|---------|
| `shift_msa` / `shift_mlp` | Attention / MLP | 偏移归一化后的特征 | 调"基准线" |
| `scale_msa` / `scale_mlp` | Attention / MLP | 缩放归一化后的特征 | 调"音量" |
| `gate_msa` / `gate_mlp` | Attention / MLP | 门控整个子层的输出 | 调"开关"——0=跳过该子层，1=正常通过 |

门控（gate）是关键创新：如果某个噪声水平不需要 attention 或 MLP 的处理，gate 可以接近 0，网络自动跳过该子层。

#### AdaLN 是什么？为什么需要它？

标准 Transformer 没有内置的"条件注入"机制。AdaLN（Adaptive Layer Normalization）是让 Transformer **感知条件（时间步、文本、类别）** 的方法。

数学形式：
$$\text{AdaLN}(\mathbf{h}, \mathbf{c}) = \boldsymbol{\gamma}(\mathbf{c}) \odot \frac{\mathbf{h} - \mu}{\sigma} + \boldsymbol{\beta}(\mathbf{c})$$

其中 $\mathbf{c}$ 是条件向量（时间嵌入 + 文本嵌入拼接），通过一个小 MLP 映射出两个向量：
- **$\boldsymbol{\gamma}(\mathbf{c})$（scale / 缩放）**：逐元素缩放归一化后的特征，控制每个维度的"音量"
- **$\boldsymbol{\beta}(\mathbf{c})$（shift / 偏移）**：逐元素平移归一化后的特征，控制每个维度的"基准线"

**几何意义**：LayerNorm 把特征压缩到零均值单位方差的球面附近。$\boldsymbol{\gamma}$ 和 $\boldsymbol{\beta}$ 在这个球面上做**仿射变换**——$\boldsymbol{\gamma}$ 拉伸/压缩不同方向（改变各维度的相对重要性），$\boldsymbol{\beta}$ 平移原点（改变各维度的基准值）。条件不同，拉伸方向和偏移量就不同——网络通过不同的 $\boldsymbol{\gamma},\boldsymbol{\beta}$ 表达不同的噪声水平/文本语义。

实际代码中常写成 $\mathbf{h}' = \boldsymbol{\gamma} \odot \text{LN}(\mathbf{h}) + \boldsymbol{\beta}$ 或等价的 $\mathbf{h}' = \text{LN}(\mathbf{h}) \cdot (1+\boldsymbol{\gamma}) + \boldsymbol{\beta}$.



#### AdaLN-Zero 是什么？

**AdaLN-Zero** 是 DiT 论文中的初始化技巧：将 $\boldsymbol{\gamma}$ 的初始值设为零，这样训练开始时 AdaLN 退化为 $\mathbf{h}' = \text{LN}(\mathbf{h})$（即恒等变换 + LayerNorm）。网络的每个 block 起步时不做任何条件调整——就像一个普通 Transformer。随着训练进行，$\boldsymbol{\gamma}$ 逐步偏离零，网络逐步"学会"利用条件信息。

**为什么这样好？** 类似于 ResNet 的残差思想——"先学会恒等，再学偏差"。如果初始化时有随机条件偏转，网络需要在学习的早期阶段同时解决"怎么去噪"和"条件信号怎么用"两个问题，容易不稳定。Zero-init 把这两个问题解耦了。

**关键发现——扩展律**：实验表明，DiT 参数越多 → FID 越低。FID（Fréchet Inception Distance）是图像生成的"考试分数"——越小越好，度量生成图像与真实图像在特征空间的分布距离。单调下降证明扩散模型也遵循和 LLM 相同的扩展律：**把模型做大就能更好**，不需要改架构或算法。

#### DIT只是换了一种网络结构预测得分/向量场，不影响其数学部分
- **§1.2（DDPM 训练）**：DiT 的训练目标和 Loss 与 DDPM 完全相同——$\mathcal{L} = \|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta\|^2$。换架构不换 Loss
- **§2.3（PF-ODE）**：DiT 的去噪网络驱动 ODE 采样——得分 $\to$ 噪声预测 $\to$ ODE 步进——逻辑链贯穿
- **§4.2（CFG）**：DiT 的条件注入（adaLN）天然支持 CFG。CFG 需要同时跑条件和无条件两个预测。在 DiT 中，无条件只需把条件向量 $\mathbf{c}$ 置为零向量——`adaLN_modulation(zero)` 自动生成全零的 shift/scale/gate，网络退化为无条件的去噪器。不需要像 U-Net 那样额外维护一个无条件分支或做条件 dropout——零初始化天然就是无条件路径。
- **§5.1（Flow Matching）**：DiT 作为骨干同时适用于扩散和 FM——后文的 SD3 就是 DiT + Rectified Flow 的组合


### 7.2 SD3——前面数学的集大成者 (Esser et al., 2024)

SD3（Stable Diffusion 3）是 Stability AI 在 2024 年发布的大规模文生图模型（80 亿参数），将本书前几章的核心思想整合到一个模型中：

- **架构**：MM-DiT——多模态 DiT，文本 token 和图像 token 用分离的注意力权重交互
- **训练目标**：Rectified Flow（§5.2）直线路径 + $v$-prediction（§5.3）
- **加权方案**：ln-SNR 权重（§3.1）
- **采样**：确定性 ODE + CFG（§4.2）

$$\text{SD3} = \text{MM-DiT} + \text{Rectified Flow} + \text{大规模训练}$$

**核心经验**：Scaling Works。80 亿参数模型在文本理解、视觉质量、拼写准确率上全面超越小模型。

**SD3 核心推理代码**（基于 HuggingFace Diffusers 官方实现，精简版）：

```python
from diffusers import StableDiffusion3Pipeline
pipe = StableDiffusion3Pipeline.from_pretrained(
    "stabilityai/stable-diffusion-3-medium-diffusers"
)
image = pipe("a cat", num_inference_steps=28, guidance_scale=7.0).images[0]
```

如果想理解内部，SD3 的采样循环本质上是：

```python
# 伪代码：SD3 采样循环（Rectified Flow + CFG）
latents = torch.randn(1, 16, H//8, W//8)
pos_emb = pipe.transformer.pos_embed         # MM-DiT 位置编码
text_emb = pipe.encode_prompt("a cat")       # 文本编码

for t in pipe.scheduler.timesteps:
    # CFG：条件 + 无条件预测
    eps_cond   = pipe.transformer(latents, t, text_emb, pos_emb)
    eps_uncond = pipe.transformer(latents, t, null_emb, pos_emb)
    eps = eps_uncond + guidance_scale * (eps_cond - eps_uncond)
    # Rectified Flow 步进
    latents = pipe.scheduler.step(eps, t, latents)

image = pipe.vae.decode(latents)
```

关键点：`pipe.transformer` 就是 MM-DiT——文本和图像 token 在同一个 Transformer 中通过分离的注意力权重交互。采样循环中 CFG 和 Rectified Flow 步进各占一行，正是本书 §4.2 和 §5.2 的直接实现。

---

## 总结：一条主线，三个方程

贯穿 34 篇论文的数学主线可以通过**三个演变阶段的方程**来总结：

### 阶段 I：离散扩散 (2015-2020)

$$\mathcal{L} = \mathbb{E}_{t,\mathbf{x}_0,\boldsymbol{\epsilon}}\Big[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon},\,t)\|^2\Big]$$

### 阶段 II：连续时间 SDE/ODE (2021-2022)

$$d\mathbf{x} = \underbrace{\big[\mathbf{f}(\mathbf{x},t) - \frac{1}{2}g(t)^2\nabla_{\mathbf{x}}\log p_t(\mathbf{x})\big]dt}_{\text{概率流 ODE}}$$

$$\nabla_{\mathbf{x}}\log p(\mathbf{x};\sigma) = \frac{D_\theta(\mathbf{x};\sigma) - \mathbf{x}}{\sigma^2}$$

### 阶段 III：概率流 / 向量场 / 一步生成 (2023-2025)

$$\min_{v} \mathbb{E}_{(X_0, X_1), t}\Big[\|(X_1 - X_0) - v_\theta(X_t, t)\|^2\Big]$$

$$f_\theta(\mathbf{x}_T, T) \to \mathbf{x}_0 \quad \text{(一步生成)}$$


这三个方程讲的是同一个故事：**找到一条从噪声到数据的路径，并沿着它移动**。

- **阶段 I** 用小步马尔可夫链（§0.6）逼近，每一步预测噪声（§0.3）
- **阶段 II** 发现整个过程由一个 ODE（§0.8）描述，核心是得分函数（§0.4），并利用 Anderson 逆向 SDE 定理（§0.7）
- **阶段 III** 认识到可以直接学习这个 ODE 的向量场（§0.9），且直线路径是最优的，一步生成是终极目标

数学语言从 KL 散度 → SDE → ODE → 向量场回归，但**核心问题从未改变：如何最有效地从 $\mathcal{N}(0,\mathbf{I})$ 走到 $p_{\text{data}}$**。

[← 回到首页](..)
