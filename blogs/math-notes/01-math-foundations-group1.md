---
layout: default
title: 扩散模型数学基础（一）：ELBO、重参数化与前向扩散
---
[← 回到首页](../README)

# 第一组：数学基础——从离散扩散到连续时间 (2015-2021)

## 01. Sohl-Dickstein (2015) — 非平衡热力学起源

### 前向过程 (Forward Diffusion)
将数据分布 $q(\mathbf{x}_0)$ 通过 $T$ 步马尔可夫链逐步加噪至简单先验：

$$q(\mathbf{x}_{1:T}|\mathbf{x}_0) = \prod_{t=1}^{T} q(\mathbf{x}_t|\mathbf{x}_{t-1})$$

$$q(\mathbf{x}_t|\mathbf{x}_{t-1}) = \mathcal{N}\left(\mathbf{x}_t; \sqrt{1-\beta_t}\,\mathbf{x}_{t-1},\; \beta_t\mathbf{I}\right)$$

### 逆向过程 (Reverse Process)
学习参数化高斯转移核：

$$p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t) = \mathcal{N}\left(\mathbf{x}_{t-1}; \boldsymbol{\mu}_\theta(\mathbf{x}_t, t),\; \boldsymbol{\Sigma}_\theta(\mathbf{x}_t, t)\right)$$

### 训练目标：变分下界
$$\log p(\mathbf{x}_0) \geq \mathbb{E}_q\left[\log p_\theta(\mathbf{x}_0|\mathbf{x}_1) - \sum_{t=2}^T D_{\text{KL}}(q(\mathbf{x}_{t-1}|\mathbf{x}_t,\mathbf{x}_0) \| p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t))\right]$$

### 核心洞察
当 $\beta_t$ 足够小（扩散缓慢），逆向过程 $q(\mathbf{x}_{t-1}|\mathbf{x}_t,\mathbf{x}_0)$ 也是高斯的，可用神经网络近似。

---

## 02. DDPM (Ho et al., 2020) — 实用化突破

### 重参数化前向过程
令 $\alpha_t = 1 - \beta_t$, $\bar{\alpha}_t = \prod_{s=1}^t \alpha_s$:

$$\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\,\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\,\boldsymbol{\epsilon}, \quad \boldsymbol{\epsilon} \sim \mathcal{N}(0,\mathbf{I})$$

### 简化训练目标（核心创新）
不做均值预测，转向**噪声预测**：

$$\mathcal{L}_{\text{simple}} = \mathbb{E}_{t, \mathbf{x}_0, \boldsymbol{\epsilon}}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)\|^2\right]$$

其中 $\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\,\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\,\boldsymbol{\epsilon}$.

### 与 Score Matching 的联系
$$\nabla_{\mathbf{x}_t}\log q(\mathbf{x}_t|\mathbf{x}_0) = -\frac{\boldsymbol{\epsilon}}{\sqrt{1-\bar{\alpha}_t}}$$

因此 $\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)$ 本质上在学习 $-\sqrt{1-\bar{\alpha}_t}\,\nabla_{\mathbf{x}_t}\log q(\mathbf{x}_t)$，即**得分函数**（up to a scale）。

### 采样
固定方差：$\boldsymbol{\Sigma}_\theta(\mathbf{x}_t, t) = \sigma_t^2\mathbf{I}$，其中 $\sigma_t^2 = \beta_t$ 或 $\tilde{\beta}_t = \frac{1-\bar{\alpha}_{t-1}}{1-\bar{\alpha}_t}\beta_t$.

---

## 02b. DDIM (Song et al., 2021) — 非马尔可夫泛化

### 关键观察
DDPM 的目标函数 $\mathcal{L}_{\text{simple}}$ 仅依赖于边缘分布 $q(\mathbf{x}_t|\mathbf{x}_0)$，不依赖具体的联合分布 $q(\mathbf{x}_{1:T}|\mathbf{x}_0)$。

### 非马尔可夫前向过程
定义一族推理分布，由参数 $\sigma \in \mathbb{R}_{\geq 0}^T$ 索引：

$$q_\sigma(\mathbf{x}_{1:T}|\mathbf{x}_0) = q_\sigma(\mathbf{x}_T|\mathbf{x}_0)\prod_{t=2}^T q_\sigma(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{x}_0)$$

其中 $q_\sigma(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{x}_0)$ 是精心构造的高斯分布，确保边缘分布 $q(\mathbf{x}_t|\mathbf{x}_0) = \mathcal{N}(\sqrt{\bar{\alpha}_t}\mathbf{x}_0, (1-\bar{\alpha}_t)\mathbf{I})$ 不变.

### 确定性采样 ($\sigma = 0$)
当 $\sigma_t = 0$，逆过程变为**确定性的**：

$$\mathbf{x}_{t-1} = \sqrt{\bar{\alpha}_{t-1}}\,\hat{\mathbf{x}}_0 + \sqrt{1-\bar{\alpha}_{t-1}}\,\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)$$

其中 $\hat{\mathbf{x}}_0 = \frac{1}{\sqrt{\bar{\alpha}_t}}(\mathbf{x}_t - \sqrt{1-\bar{\alpha}_t}\,\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t))$.

### ODE 视角
DDIM 的确定性采样是 Probability Flow ODE 的 Euler 离散化。

---

## 03. Score SDE (Song et al., 2021) — 连续时间统一

### 正向 SDE
将离散扩散推广到连续时间：

$$d\mathbf{x} = \mathbf{f}(\mathbf{x}, t)\,dt + g(t)\,d\mathbf{w}$$

### 逆向 SDE (Anderson, 1982)
$$d\mathbf{x} = \left[\mathbf{f}(\mathbf{x}, t) - g(t)^2\nabla_\mathbf{x}\log p_t(\mathbf{x})\right]dt + g(t)\,d\bar{\mathbf{w}}$$

逆向时间布朗运动 $\bar{\mathbf{w}}$。

### Probability Flow ODE
与 SDE 具有相同边缘分布的确定性 ODE：

$$d\mathbf{x} = \left[\mathbf{f}(\mathbf{x}, t) - \frac{1}{2}g(t)^2\nabla_\mathbf{x}\log p_t(\mathbf{x})\right]dt$$

### 统一 VP-SDE 和 VE-SDE
- **VP-SDE** (对应 DDPM): $\mathbf{f} = -\frac{1}{2}\beta(t)\mathbf{x}$, $g(t) = \sqrt{\beta(t)}$
- **VE-SDE** (对应 NCSN): $\mathbf{f} = 0$, $g(t) = \sqrt{\frac{d[\sigma^2(t)]}{dt}}$

### Score 估计：去噪得分匹配
$$\theta^* = \arg\min_\theta \mathbb{E}_t\left[\lambda(t)\mathbb{E}_{\mathbf{x}_0,\mathbf{x}_t}\left[\|\mathbf{s}_\theta(\mathbf{x}_t, t) - \nabla_{\mathbf{x}_t}\log p_{0t}(\mathbf{x}_t|\mathbf{x}_0)\|^2\right]\right]$$

---

## 04. Improved DDPM (Nichol & Dhariwal, 2021) — 似然优化

### 可学习方差
$$\boldsymbol{\Sigma}_\theta(\mathbf{x}_t, t) = \exp(v\log\beta_t + (1-v)\log\tilde{\beta}_t)$$

其中 $v$ 是神经网络输出，在 $\log\beta_t$ 和 $\log\tilde{\beta}_t$ 之间插值。

### 余弦噪声调度
$$\bar{\alpha}_t = \frac{f(t)}{f(0)}, \quad f(t) = \cos\left(\frac{t/T + s}{1 + s} \cdot \frac{\pi}{2}\right)^2$$

解决了线性调度中信息过早被破坏的问题。

### 混合目标
$$\mathcal{L}_{\text{hybrid}} = \mathcal{L}_{\text{simple}} + \lambda\mathcal{L}_{\text{vlb}}$$

---

## 26. VDM (Kingma et al., 2021) — 变分视角与 SNR

### SNR 参数化
定义信噪比 $\text{SNR}(t) = \alpha_t^2 / \sigma_t^2$，则：

$$\mathbf{x}_t = \alpha_t\mathbf{x}_0 + \sigma_t\boldsymbol{\epsilon}$$

### 扩散 VLB 的简洁形式
连续时间 VLB 可写成：

$$-\text{VLB} = \frac{1}{2}\mathbb{E}_{\boldsymbol{\epsilon}\sim\mathcal{N}(0,\mathbf{I}), t\sim U(0,1)}\left[\frac{d\log\text{SNR}}{dt}\|\boldsymbol{\epsilon} - \hat{\boldsymbol{\epsilon}}_\theta(\mathbf{x}_t, t)\|^2\right]$$

### 关键定理
**连续时间 VLB 对噪声调度不变，只依赖于端点 SNR(t=0) 和 SNR(t=1)。**

这允许学习最优噪声调度以最小化 VLB 估计的方差。

### 傅里叶特征
使用 $\sin$ 和 $\cos$ 傅里叶特征编码时间步，替代简单的标量编码。

[← 回到首页](../README)
