---
layout: default
title: 扩散模型数学基础（二）：引导与采样器
---
[← 回到首页](../README)

# 第二组：引导、设计空间与高效求解器 (2021-2022)

## 05. Classifier Guidance (Dhariwal & Nichol, 2021)

### 核心数学：贝叶斯规则在得分空间

利用预训练分类器 $p(y|\mathbf{x}_t)$ 在采样时引导生成：

$$\nabla_{\mathbf{x}_t}\log p(\mathbf{x}_t|y) = \nabla_{\mathbf{x}_t}\log p(\mathbf{x}_t) + \nabla_{\mathbf{x}_t}\log p(y|\mathbf{x}_t)$$

带强度的引导：

$$\nabla_{\mathbf{x}_t}\log p_w(\mathbf{x}_t|y) = \nabla_{\mathbf{x}_t}\log p(\mathbf{x}_t) + w \cdot \nabla_{\mathbf{x}_t}\log p(y|\mathbf{x}_t)$$

### 噪声预测形式
$$\hat{\boldsymbol{\epsilon}}_\theta(\mathbf{x}_t, y) = \boldsymbol{\epsilon}_\theta(\mathbf{x}_t) - w\sqrt{1-\bar{\alpha}_t}\,\nabla_{\mathbf{x}_t}\log p_\phi(y|\mathbf{x}_t)$$

$w > 1$ 放大条件信号，提高保真度，降低多样性（保真度-多样性权衡）。

---

## 06. CFG — Classifier-Free Guidance (Ho & Salimans, 2021)

### 核心数学：隐式分类器

无需显式分类器，通过条件/无条件模型的插值实现引导。

### 训练
以概率 $p_{\text{uncond}}$ 随机丢弃条件 $c$：
$$\mathcal{L} = \mathbb{E}_{t,\mathbf{x}_0,\boldsymbol{\epsilon},c}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, c, t)\|^2\right]$$

### 采样（外推）
$$\tilde{\boldsymbol{\epsilon}}_\theta(\mathbf{x}_t, c) = (1 + w)\,\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, c) - w\,\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, \varnothing)$$

等效于：
$$\tilde{\boldsymbol{\epsilon}}_\theta(\mathbf{x}_t, c) = \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, \varnothing) + w\left[\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, c) - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, \varnothing)\right]$$

### 与 Classifier Guidance 的联系
可以证明 CFG 隐式地估计了：
$$\nabla_{\mathbf{x}_t}\log\tilde{p}_w(\mathbf{x}_t|c) = \nabla_{\mathbf{x}_t}\log p(\mathbf{x}_t) + w\left[\nabla_{\mathbf{x}_t}\log p(\mathbf{x}_t|c) - \nabla_{\mathbf{x}_t}\log p(\mathbf{x}_t)\right]$$

---

## 24. EDM (Karras et al., 2022) — 设计空间统一

### 统一 ODE 形式
以噪声标准差 $\sigma$ 为自变量（替代时间 $t$）：

$$d\mathbf{x} = -\dot{\sigma}(t)\,\sigma(t)\,\nabla_\mathbf{x}\log p(\mathbf{x};\sigma(t))\,dt$$

或更简洁：
$$d\mathbf{x} = -\sigma\,\nabla_\mathbf{x}\log p(\mathbf{x};\sigma)\,d\sigma$$

### 去噪函数（Preconditioning）
核心创新：对网络输入/输出进行缩放以均衡训练：

$$D_\theta(\mathbf{x};\sigma) = c_{\text{skip}}(\sigma)\,\mathbf{x} + c_{\text{out}}(\sigma)\,F_\theta\big(c_{\text{in}}(\sigma)\,\mathbf{x};\,c_{\text{noise}}(\sigma)\big)$$

其中 $F_\theta$ 是原始神经网络。$c_{\text{skip}}$, $c_{\text{out}}$, $c_{\text{in}}$, $c_{\text{noise}}$ 是精心设计的缩放因子。

### 去噪器与得分的关系
$$D(\mathbf{x};\sigma) \approx \mathbb{E}[\mathbf{x}_0|\mathbf{x}_t=\mathbf{x}]$$

$$\nabla_\mathbf{x}\log p(\mathbf{x};\sigma) = \frac{D(\mathbf{x};\sigma) - \mathbf{x}}{\sigma^2}$$

### 训练目标
$$\mathcal{L} = \mathbb{E}_{\sigma,\mathbf{x}_0,\mathbf{n}}\left[\lambda(\sigma)\|D_\theta(\mathbf{x}_0+\mathbf{n};\sigma) - \mathbf{x}_0\|^2\right]$$

$\lambda(\sigma) = 1/\sigma^2$ 使得等权重的训练在所有噪声水平上效果均衡。

### Heun 二阶采样器
$$\mathbf{x}_{i+1} = \mathbf{x}_i + (\sigma_{i+1} - \sigma_i)\cdot\frac{1}{2}\left[\left(\frac{\mathbf{x}_i - D_\theta(\mathbf{x}_i;\sigma_i)}{\sigma_i}\right) + \left(\frac{\mathbf{x}_i' - D_\theta(\mathbf{x}_i';\sigma_{i+1})}{\sigma_{i+1}}\right)\right]$$

### 噪声调度
$$\sigma_i = \left(\sigma_{\text{max}}^{1/\rho} + \frac{i}{N-1}(\sigma_{\text{min}}^{1/\rho} - \sigma_{\text{max}}^{1/\rho})\right)^\rho$$

$\rho = 7$ 在实践中效果最好。

---

## 25. DPM-Solver (Lu et al., 2022) — 专用快速 ODE 求解器

### 核心洞察：半线性 ODE 结构

扩散 ODE 可写为：
$$\frac{d\mathbf{x}_t}{dt} = f(t)\mathbf{x}_t + \frac{g(t)^2}{2\sigma_t}\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)$$

### 精确解（变数分离）
利用线性部分可精确求解：
$$\mathbf{x}_s = \frac{\alpha_s}{\alpha_t}\mathbf{x}_t + \alpha_s\int_{\lambda_t}^{\lambda_s} e^{-\lambda}\hat{\boldsymbol{\epsilon}}_\theta(\hat{\mathbf{x}}_\lambda, \lambda)\,d\lambda$$

其中 $\lambda_t = \log\frac{\alpha_t}{\sigma_t}$ 是对数 SNR.

### 关键变量变换
$$\bar{\mathbf{x}}_t = \frac{\mathbf{x}_t}{\alpha_t}$$

将 ODE 简化为：
$$\frac{d\bar{\mathbf{x}}_t}{dt} = \frac{\sigma_t}{\alpha_t}\frac{d\lambda_t}{dt}\,\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)$$

### DPM-Solver-2 (二阶)
$$\bar{\mathbf{x}}_{t_{i-1}} = \bar{\mathbf{x}}_{t_i} + \frac{h_i}{2r_i}\left[\boldsymbol{\epsilon}_\theta(\mathbf{x}_{t_i}, t_i) - \boldsymbol{\epsilon}_\theta(\mathbf{x}_{s_i}, s_i)\right] + \frac{h_i}{2}\boldsymbol{\epsilon}_\theta(\mathbf{x}_{s_i}, s_i)$$

### DPM-Solver-3 (三阶)
15-20 次函数评估可达 DDPM 1000 步质量。

---

## 07. Cascaded Diffusion (Ho et al., 2021)

### 数学框架
在低分辨率扩散模型基础上堆叠条件超分辨率扩散模型：

$$p(\mathbf{x}|\mathbf{y}) = \int p(\mathbf{x}_T|\mathbf{y})\prod_{t=1}^T p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{y})\,d\mathbf{x}_{1:T}$$

其中 $\mathbf{y}$ 是低分辨率图像。每个阶段的条件通过通道拼接注入 U-Net。

[← 回到首页](../README)
