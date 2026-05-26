---
layout: default
title: 扩散模型数学基础（三）：Flow Matching 与生成
---
[← 回到首页](../README)

# 第三组：流范式与一步生成 (2022-2024)

## 09. Flow Matching (Lipman et al., 2023) — CNF 训练新范式

### Continuous Normalizing Flow (CNF)
流 $\phi_t: \mathbb{R}^d \to \mathbb{R}^d$ 由向量场 $v_t$ 定义：
$$\frac{d}{dt}\phi_t(\mathbf{x}) = v_t(\phi_t(\mathbf{x})), \quad \phi_0(\mathbf{x}) = \mathbf{x}$$

概率路径通过 push-forward 演化：
$$p_t = [\phi_t]_* p_0, \quad [\phi_t]_* p_0(\mathbf{x}) = p_0(\phi_t^{-1}(\mathbf{x}))\det\left|\frac{\partial\phi_t^{-1}}{\partial\mathbf{x}}(\mathbf{x})\right|$$

### Flow Matching 目标
$$L_{\text{FM}}(\theta) = \mathbb{E}_{t, p_t(\mathbf{x})}\left[\|v_t(\mathbf{x};\theta) - u_t(\mathbf{x})\|^2\right]$$

其中 $u_t(\mathbf{x})$ 是目标向量场，$t \sim U[0,1]$.

### Conditional Flow Matching（核心技巧）
引入条件概率路径 $p_t(\mathbf{x}|\mathbf{x}_1)$ 和条件向量场 $u_t(\mathbf{x}|\mathbf{x}_1)$：

$$p_t(\mathbf{x}) = \int p_t(\mathbf{x}|\mathbf{x}_1)\,q(\mathbf{x}_1)\,d\mathbf{x}_1$$

$$u_t(\mathbf{x}) = \int u_t(\mathbf{x}|\mathbf{x}_1)\,\frac{p_t(\mathbf{x}|\mathbf{x}_1)\,q(\mathbf{x}_1)}{p_t(\mathbf{x})}\,d\mathbf{x}_1$$

**关键定理**：$u_t$ 生成 $p_t$，且 CFM 损失与 FM 损失有相同梯度：
$$L_{\text{CFM}}(\theta) = \mathbb{E}_{t, q(\mathbf{x}_1), p_t(\mathbf{x}|\mathbf{x}_1)}\left[\|v_t(\mathbf{x};\theta) - u_t(\mathbf{x}|\mathbf{x}_1)\|^2\right]$$

$$\nabla_\theta L_{\text{FM}}(\theta) = \nabla_\theta L_{\text{CFM}}(\theta)$$

### 高斯条件路径
$$p_t(\mathbf{x}|\mathbf{x}_1) = \mathcal{N}(\mathbf{x}; \mu_t(\mathbf{x}_1), \sigma_t^2\mathbf{I})$$

- **扩散路径**：$\mu_t = \mathbf{x}_1$, $\sigma_t = \sigma_{1-t}$（对应传统扩散）
- **最优传输 (OT) 路径**：$\mu_t = t\mathbf{x}_1$, $\sigma_t = 1 - (1-\sigma_{\min})t$

OT 路径形成**直线概率路径**，更简单、更高效。

---

## 08. Rectified Flow (Liu et al., 2023) — 直线流

### 传输映射问题
寻找 $T: \mathbb{R}^d \to \mathbb{R}^d$ 使得 $T(Z_0) \sim \pi_1$ 当 $Z_0 \sim \pi_0$.

### Rectified Flow 定义
给定耦合 $(X_0, X_1) \sim \pi_0 \times \pi_1$，定义线性插值：
$$\mathbf{X}_t = t\mathbf{X}_1 + (1-t)\mathbf{X}_0$$

学习 ODE 来匹配这些直线路径：
$$\min_{v}\mathbb{E}_{(\mathbf{X}_0,\mathbf{X}_1)}\left[\int_0^1\left\|\frac{d\mathbf{X}_t}{dt} - v(\mathbf{X}_t, t)\right\|^2 dt\right]$$

由于 $\frac{d\mathbf{X}_t}{dt} = \mathbf{X}_1 - \mathbf{X}_0$（常数），训练简化为：
$$\min_{v}\mathbb{E}_{(\mathbf{X}_0,\mathbf{X}_1), t}\left[\|(\mathbf{X}_1 - \mathbf{X}_0) - v(\mathbf{X}_t, t)\|^2\right]$$

### Reflow（关键过程）
1. 训练 1-Rectified Flow: $Z_t = \text{ODE}(v_1, Z_0)$
2. 采样端点 $(Z_0, Z_1)$
3. 用新端点训练 2-Rectified Flow
4. 重复...

每次 Reflow 使轨迹更直。**2-Rectified Flow 几乎完全直线。**

### 理论保证
对于任意凸代价函数 $c$，Reflow 不增加传输代价：
$$W_c(T_{k+1}\#\pi_0, \pi_1) \leq W_c(T_k\#\pi_0, \pi_1)$$

---

## 20. Consistency Models (Song et al., 2023) — 一步生成

### 自洽性原理
学习函数 $f_\theta(\mathbf{x}_t, t) \to \mathbf{x}_0$，使得从同一 PF-ODE 轨迹上任意两点映射到相同的 $\mathbf{x}_0$：
$$f_\theta(\mathbf{x}_t, t) = f_\theta(\mathbf{x}_{t'}, t') = \mathbf{x}_0$$

### PF-ODE 设置
$$d\mathbf{x}_t = \left[\mu(\mathbf{x}_t, t) - \frac{1}{2}\sigma(t)^2\nabla\log p_t(\mathbf{x}_t)\right]dt$$

采用 Karras 设置：$\mu = 0$, $\sigma(t) = \sqrt{2t}$.

### 参数化
$$f_\theta(\mathbf{x}, t) = c_{\text{skip}}(t)\,\mathbf{x} + c_{\text{out}}(t)\,F_\theta(\mathbf{x}, t)$$

其中 $c_{\text{skip}}(0) = 1$, $c_{\text{out}}(0) = 0$ 保证边界条件。

### 训练方法 1：蒸馏
$$\mathcal{L}_{\text{CD}} = \mathbb{E}_{n, \mathbf{x}_{t_{n+1}}}\left[d(f_\theta(\mathbf{x}_{t_{n+1}}, t_{n+1}), f_{\theta^-}(\hat{\mathbf{x}}_{t_n}, t_n))\right]$$

其中 $\hat{\mathbf{x}}_{t_n}$ 由预训练扩散模型的 ODE 步得到，$d$ 是距离度量。

### 训练方法 2：直接训练
$$\mathcal{L}_{\text{CT}} = \mathbb{E}_{n, \mathbf{x}_0, \mathbf{z}}\left[d(f_\theta(\mathbf{x}_{t_{n+1}}, t_{n+1}), f_{\theta^-}(\mathbf{x}_{t_n}, t_n))\right]$$

其中 $\mathbf{x}_{t_{n+1}} = \mathbf{x}_0 + t_{n+1}\mathbf{z}$, $\mathbf{x}_{t_n} = \mathbf{x}_0 + t_n\mathbf{z}$.

### 采样
从噪声一步生成：$\hat{\mathbf{x}}_0 = f_\theta(\mathbf{x}_T, T)$
或多步精炼：重复 $\mathbf{x}_{t_{n-1}} = \hat{\mathbf{x}}_0 + t_{n-1}\hat{\mathbf{z}} \to$ 再次通过 $f_\theta$.

---

## 18. DiT (Peebles & Xie, 2023) — Transformer 替代 U-Net

### Patch 化
$$\mathbf{x} \in \mathbb{R}^{H \times W \times C} \to \text{Patchify} \to \text{tokens} \in \mathbb{R}^{(H/p) \times (W/p) \times d}$$

### 条件注入：adaLN-Zero
$$\text{adaLN}(h, c) = \gamma(c) \cdot h + \beta(c)$$

其中 $c = [t_{\text{emb}}; \text{class}_{\text{emb}}]$，$\gamma$ 和 $\beta$ 由 MLP 回归。

初始化 $\gamma = 0$（零初始化），训练稳定。

### DiT Block
$$\mathbf{h}' = \mathbf{h} + \text{MSA}(\text{LN}_1(\mathbf{h}); c)$$
$$\mathbf{h}'' = \mathbf{h}' + \text{MLP}(\text{LN}_2(\mathbf{h}'); c)$$

### 扩展律
模型规模 $GFLOPs$ $\uparrow$ $\implies$ FID $\downarrow$（单调改善），与 LLM 相似。

---

## 22. SiT (Ma et al., 2024) — 插值框架

### 插值框架
$$\mathbf{x}_t = \alpha_t\mathbf{x}_* + \sigma_t\boldsymbol{\epsilon}$$

其中 $\mathbf{x}_*$ 可以是 $\mathbf{x}_0$（数据预测）或 $\mathbf{x}_1$（目标）。

### 预测目标比较
- **$\epsilon$-prediction**：预测噪声，DDPM 标准
- **$x_0$-prediction**：预测干净数据
- **$v$-prediction**：预测速度 $v = \alpha_t\boldsymbol{\epsilon} - \sigma_t\mathbf{x}_0$

### 核心发现
**Flow Matching + v-prediction + ODE 采样** 在 ImageNet 上全面超越扩散模型。

### 损失函数
$$\mathcal{L} = \mathbb{E}_{t, \mathbf{x}_0, \boldsymbol{\epsilon}}\left[w(t)\|v_\theta(\mathbf{x}_t, t) - v_t\|^2\right]$$

$w(t)$ 在不同预测目标下有不同最优形式。

---

## 23. SD3 (Esser et al., 2024) — 大规模 Rectified Flow

### MM-DiT（多模态 DiT）
分离的文本和图像 token，通过**双流注意力**交互：

$$\text{Attention}_\text{text}(\mathbf{Q}_t, \mathbf{K}_t, \mathbf{V}_t),\quad \text{Attention}_\text{image}(\mathbf{Q}_i, \mathbf{K}_i, \mathbf{V}_i)$$

交叉注意力允许文本和图像信息互相流动。

### Rectified Flow 训练
$$\mathcal{L} = \mathbb{E}_{t, \mathbf{x}_0, \mathbf{x}_1, \boldsymbol{\epsilon}}\left[\|\mathbf{v}_\theta(\mathbf{x}_t, \mathbf{c}, t) - (\mathbf{x}_1 - \mathbf{x}_0)\|^2\right]$$

### 加权方案（ln-SNR）
$$w(t) = \frac{\sigma_t^2}{(\sigma_t^2 + 1)^2}$$

### 核心经验：Scaling Works
模型越大（8B参数），文本理解、视觉质量、拼写准确率全面提升。

[← 回到首页](../README)
