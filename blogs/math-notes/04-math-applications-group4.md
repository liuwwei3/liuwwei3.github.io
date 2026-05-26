---
layout: default
title: 扩散模型数学基础（四）：应用
---
[← 回到首页](../README)

# 第四组：架构与应用数学 (2022-2025)

## 11. Latent Diffusion / Stable Diffusion (Rombach et al., 2022)

### 潜空间压缩
$$\mathbf{z} = \mathcal{E}(\mathbf{x}), \quad \hat{\mathbf{x}} = \mathcal{D}(\mathbf{z})$$

VAE 训练目标：
$$\mathcal{L}_{\text{VAE}} = \|\mathbf{x} - \hat{\mathbf{x}}\|^2 + \beta\cdot D_{\text{KL}}(q_\phi(\mathbf{z}|\mathbf{x})\,\|\,\mathcal{N}(0,\mathbf{I}))$$

压缩比：$H \times W \times C \to h \times w \times c$，通常 4-8× 空间压缩。

### 潜空间扩散
在潜变量 $\mathbf{z}$ 上训练扩散/去噪过程：
$$\mathcal{L}_{\text{LDM}} = \mathbb{E}_{\mathcal{E}(\mathbf{x}), \boldsymbol{\epsilon}, t}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{z}_t, t, \tau_\theta(\mathbf{y}))\|^2\right]$$

### 交叉注意力条件注入
$$\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^\top}{\sqrt{d}}\right)\mathbf{V}$$

其中 $\mathbf{Q} = \mathbf{W}_Q \cdot \mathbf{h}_{\text{U-Net}}$, $\mathbf{K},\mathbf{V} = \mathbf{W}_K,\mathbf{W}_V \cdot \tau_\theta(\mathbf{y})$.

$\tau_\theta$ 是文本编码器（CLIP），$\mathbf{h}_{\text{U-Net}}$ 是 U-Net 中间特征。

### 计算革命
$O(HW)$ 计算量 → $O(hw)$ 计算量，使得在消费级 GPU 上运行扩散模型成为可能。

---

## 19. ControlNet (Zhang et al., 2023)

### 零卷积初始化
可训练复制 $\theta_c$ 的初始输出为零：
$$\mathbf{y} = \mathcal{F}(\mathbf{x}; \Theta) + \mathcal{Z}(\mathcal{F}(\mathbf{x} + \mathbf{Z}(\mathbf{c}); \Theta_{\text{zero}}); \Theta_c)$$

其中 $\mathcal{Z}$ 是初始化为零的 1×1 卷积（权重和偏置均为零）。

### 条件编码
将控制信号（Canny 边缘、深度图、姿态等）通过小型网络编码后注入 U-Net 复制。

数学上：冻结原始 U-Net 参数 $\Theta$，只训练复制编码器的参数 $\Theta_c$.

### 训练目标
与原始 SD 相同：
$$\mathcal{L} = \mathbb{E}_{\mathbf{z}_0, t, \mathbf{c}_t, \mathbf{c}_f, \boldsymbol{\epsilon}}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{z}_t, t, \mathbf{c}_t, \mathbf{c}_f)\|^2\right]$$

其中 $\mathbf{c}_t$ = 文本条件，$\mathbf{c}_f$ = 控制信号条件。

---

## 14. DreamBooth (Ruiz et al., 2023)

### 先验保持损失
$$\mathcal{L} = \mathcal{L}_{\text{SD}}(\mathbf{x}, \mathbf{c}) + \lambda\mathcal{L}_{\text{prior}}(\mathbf{x}_{\text{pr}}, \mathbf{c}_{\text{pr}})$$

其中：
- $\mathcal{L}_{\text{SD}}$: 标准 SD 损失，使用包含特定物体的图像和稀有标识符
- $\mathcal{L}_{\text{prior}}$: 使用类别先验样本和对应的类别提示，防止过拟合

### 数学本质
在预训练扩散模型的权重空间中做**约束微调**。先验保持损失充当正则化：
$$\min_{\Delta\Theta} \mathbb{E}_{\text{instance}}\left[\mathcal{L}(\Theta + \Delta\Theta)\right] \quad \text{s.t.} \quad \mathbb{E}_{\text{class}}\left[\mathcal{L}_{\text{prior}}(\Theta + \Delta\Theta)\right] \leq \epsilon$$

---

## 16-17. Video Diffusion & Imagen Video (Ho et al., 2022)

### 3D U-Net
将 2D U-Net 扩展为时空 U-Net：空间注意力 + 时间注意力（帧间）。

输入：$\mathbf{x} \in \mathbb{R}^{B \times F \times H \times W \times C}$

### 级联时空超分辨率
$$p(\mathbf{x}|\mathbf{y}) = \text{TSR}\left(\text{SSR}\left(p_{\text{base}}(\mathbf{x}_{\text{low}}|\mathbf{y})\right)\right)$$

- 基础模型：低分辨率、低帧率
- SSR：空间超分辨率
- TSR：时间超分辨率（帧插值）

### v-prediction
$$\mathbf{v} = \alpha_t\boldsymbol{\epsilon} - \sigma_t\mathbf{x}_0$$

在视频生成中比 $\epsilon$-prediction 更稳定。

---

## 30. Lumiere (Bar-Tal et al., 2024) — Space-Time U-Net

### 核心创新
一次生成完整视频（所有帧），而非逐帧或关键帧+插值。

在 U-Net 的空间下/上采样之外，增加**时间下/上采样**层。

### 数学
$$\mathbf{x}_t \in \mathbb{R}^{F \times H \times W \times C}$$

U-Net 编码器-解码器在空间和时间维度同时压缩：
$$(F, H, W) \xrightarrow{\text{encoder}} \left(\frac{F}{s_t}, \frac{H}{s_s}, \frac{W}{s_s}\right) \xrightarrow{\text{decoder}} (F, H, W)$$

---

## 33. CogVideoX (Yang et al., 2024)

### Expert Transformer
3D VAE 压缩视频 + DiT 骨干 + 3D RoPE 位置编码。

### 数学核心
$$p(\mathbf{x}|\mathbf{c}) = \int p(\mathbf{x}_T|\mathbf{c})\prod_{t=1}^T p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{c})\,d\mathbf{x}_{1:T}$$

其中 $\mathbf{x}$ 是视频 latents，$\mathbf{c}$ 是文本条件。

---

## 35. HunyuanVideo (Kong et al., 2024)

### 系统化视频生成框架
$$\text{HunyuanVideo} = \text{3D VAE} + \text{DiT}(13B+) + \text{SSTA} + \text{Dual-Encoder}$$

- SSTA (Selective Sliding Tile Attention): 稀疏注意力，1.87× 加速
- Dual-Channel Text Encoder: Qwen2.5-VL + Glyph-ByT5

---

## 36. Wan (Alibaba, 2025)

### 全开放视频套件
- Wan-14B: DiT 骨干，Flow Matching 训练
- Wan-1.3B: 仅需 8.19GB VRAM
- 支持 T2V, I2V, 视频编辑, 个性化生成

---

## 37. Seedance (ByteDance, 2025)

### 解耦时空架构
空间层和时间层分离：
$$\text{Block}(\mathbf{x}) = \text{Spatial-Attention}(\mathbf{x}) + \text{Temporal-Attention}(\mathbf{x})$$

### 多阶段蒸馏
教师模型 → 逐步蒸馏 → 学生模型，实现 ~10× 推理加速。

### 视频 RLHF
多维度奖励函数：视觉质量、文本对齐、运动质量、镜头质量。

[← 回到首页](../README)
