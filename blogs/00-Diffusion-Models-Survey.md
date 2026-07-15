# Diffusion 模型：从起源到前沿 —— 近十年关键论文综述

> 本文收录 2015–2025 年间 39 篇 Diffusion 领域最具影响力的论文，按时间线和主题组织，逐一阐述其核心贡献。
>
> **数学分析**：[MATHEMATICAL-MAINLINE.md](MATHEMATICAL-MAINLINE.md) — 贯穿全部论文的数学主线
> **逐篇笔记**：[math-notes/](math-notes/) 目录下 4 组分论文数学推导

---

## 目录

1. [起源与理论基础 (2015–2019)](#1-起源与理论基础-20152019)
2. [突破之年：DDPM 与 Score-Based 框架 (2020–2021)](#2-突破之年ddpm-与-score-based-框架-20202021)
3. [质量提升与无分类器引导 (2021–2022)](#3-质量提升与无分类器引导-20212022)
4. [文生图革命：从 GLIDE 到 Imagen (2021–2022)](#4-文生图革命从-glide-到-imagen-20212022)
5. [高效采样与加速推理 (2022)](#5-高效采样与加速推理-2022)
6. [精细控制、个性化与编辑 (2022–2023)](#6-精细控制个性化与编辑-20222023)
7. [视频生成时代：从 SVD 到 Seedance (2022–2025)](#7-视频生成时代从-svd-到-seedance-20222025)
   - 7.1 早期探索（Video Diffusion / Imagen Video）
   - 7.2 潜空间视频扩散（SVD / Emu Video / Lumiere）
   - 7.3 DiT 大规模视频模型（Sora / CogVideoX / Movie Gen / HunyuanVideo / Wan）
   - 7.4 字节跳动 Seed 系列（Seaweed / Seedance 1.0 / Seedance 1.5 Pro）
8. [Flow Matching 范式 (2023–2024)](#8-flow-matching-范式-20232024)
9. [Scaling Up：DiT、SDXL、SD3 与大模型时代 (2023–2025)](#9-scaling-updit-sdxlsd3-与大模型时代-20232025)
10. [论文索引表](#10-论文索引表)

---

## 1. 起源与理论基础 (2015–2019)

### Deep Unsupervised Learning using Nonequilibrium Thermodynamics
**Sohl-Dickstein et al., ICML 2015** | `01-SohlDickstein2015-Deep-Unsupervised-Nonequilibrium-Thermodynamics.pdf`

**核心贡献：扩散模型的开山之作。**

- 将非平衡统计力学中的**扩散过程**引入机器学习，提出通过马尔可夫链逐步将数据分布转化为已知先验（如高斯噪声），再学习逆过程来生成数据。
- 建立了**前向扩散过程**（逐步加噪）与**反向去噪过程**（逐步还原）的数学框架。
- 证明了只要前向过程每一步添加的噪声足够小，逆过程就可以用高斯分布近似，且可通过神经网络参数化。
- 受限于当时的算力和网络设计，实验规模较小（MNIST/CIFAR-10），但奠定了整个领域的理论基础。

---

## 2. 突破之年：DDPM 与 Score-Based 框架 (2020–2021)

### Denoising Diffusion Probabilistic Models (DDPM)
**Ho, Jain & Abbeel, NeurIPS 2020** | `DDPM.pdf`（根目录）

**核心贡献：让扩散模型真正进入实用阶段。**

- 重新诠释了扩散模型，将其与**噪声条件得分匹配（Noise Conditional Score Network, NCSN）** 联系起来，证明扩散模型本质上在建模数据的得分函数。
- 提出极简训练目标：**预测添加的噪声**（ε-prediction），而非预测数据本身，大幅降低了训练难度。
- 引入**固定方差调度**（linear schedule）和简化损失函数 L_simple，使得训练稳定且易于复现。
- 在 CIFAR-10（FID ~3.17）和 LSUN 上达到当时最好的生成质量，开启了 diffusion 替代 GAN 的序幕。

### Denoising Diffusion Implicit Models (DDIM)
**Song, Meng & Ermon, ICLR 2021** | `02-Song2021-DDIM.pdf`

**核心贡献：将扩散模型从马尔可夫链的约束中解放出来。**

- 提出一类**非马尔可夫**的逆扩散过程，允许以更少的采样步数生成高质量样本（从 1000 步降至 50–100 步）。
- 证明了 DDPM 的训练目标等价于一个更广泛的变分下界，其中前向过程可以是确定性的，从而实现了**确定性反演**（deterministic inversion）。
- 因反演能力，DDIM 成为后续图像编辑、插值、风格迁移等任务的核心工具。

### Score-Based Generative Modeling through Stochastic Differential Equations (Score SDE)
**Song et al., ICLR 2021** | `03-Song2021-Score-SDE.pdf`

**核心贡献：统一了 Score-Based 模型与 DDPM，建立了扩散模型的连续时间 SDE 框架。**

- 将离散的扩散步数推广到**连续时间随机微分方程**（SDE）：前向过程 → SDE，逆向过程 → 逆 SDE。
- 提出 **Probability Flow ODE**：与 SDE 具有相同边缘分布的常微分方程，为高效采样和似然评估提供了新工具。
- 统一了 NCSN (VE-SDE) 和 DDPM (VP-SDE) 两大流派，并提供了一套通用理论框架。
- 提出了 ODE 采样器的设计原则，影响了后续几乎所有加速采样方法。

### Improved Denoising Diffusion Probabilistic Models
**Nichol & Dhariwal, ICML 2021** | `04-Nichol2021-Improved-DDPM.pdf`

**核心贡献：系统性地改进了 DDPM 的训练与采样。**

- 提出**可学习的方差**（learned Σ），使用插值形式 Σ_θ = exp(v log β_t + (1−v) log β̃_t)，在维持采样质量的同时大幅提升似然。
- 引入**余弦噪声调度**（cosine schedule），替代 DDPM 的线性调度，解决了信息过早被噪声淹没的问题。
- 提出重要性采样改进 VLB 训练，实现了更好的 likelihood（在 ImageNet 64×64 上 NLL = 3.37 bits/dim）。

---

## 3. 质量提升与无分类器引导 (2021–2022)

### Diffusion Models Beat GANs on Image Synthesis
**Dhariwal & Nichol, NeurIPS 2021** | `05-Dhariwal2021-Diffusion-Beat-GANs.pdf`

**核心贡献：首次在图像生成质量上全面超越 GAN。**

- 引入**分类器引导**（classifier guidance）：在采样过程中利用预训练分类器的梯度引导生成朝向特定类别。
- 提出了一系列架构改进：**自适应 GroupNorm**、更深的 U-Net、多分辨率注意力（multi-head / multi-resolution attention）、BigGAN 风格的上/下采样。
- 在 ImageNet 256×256 上以 FID 2.97 超越 BigGAN-deep（FID 6.95），被视为 diffusion 替代 GAN 的标志性事件。
- 展示了 classifier guidance 的 scale 效应：增大引导强度能提升保真度但牺牲多样性。

### Classifier-Free Diffusion Guidance
**Ho & Salimans, NeurIPS 2021** | `06-Ho2022-Classifier-Free-Guidance.pdf`

**核心贡献：提出无需额外训练分类器的引导方法，成为后续所有文生图模型的标准技术。**

- 核心思想：在训练时随机丢弃条件标签（以概率 p_uncond），使模型同时学会条件分布和无条件分布。
- 采样时，通过外推 p(x|c) ∝ p_θ(x|c)^w · p_θ(x)^(1−w)，用**引导强度 w** 控制条件 vs 无条件之间的权衡。
- 优点：(1) 无需额外分类器；(2) 对难以用分类器描述的条件（如文本、分割图）也适用；(3) 实现简单，仅需修改训练时的 dropout。
- 成为 Stable Diffusion、DALL-E 2、Imagen 等后续所有大规模文生图模型的标配。

### Cascaded Diffusion Models for High Fidelity Image Generation
**Ho et al., JMLR 2022** | `07-Ho2021-Cascaded-Diffusion.pdf`

**核心贡献：提出级联扩散架构，为后续大规模文生图系统提供可扩展的框架。**

- 使用**流水线式级联**（cascaded pipeline）：先训练低分辨率基础扩散模型（如 64×64），再训练一系列超分辨率扩散模型逐级提高分辨率。
- 级联设计使得每个模型专注于单一任务，可以独立优化超参数和噪声调度。
- 配合 classifier-free guidance，在 ImageNet 上取得当时最高的 FID。
- 这一架构直接启发了 DALL-E 2 和 Imagen 的设计。

---

## 4. 文生图革命：从 GLIDE 到 Imagen (2021–2022)

### GLIDE: Towards Photorealistic Image Generation and Editing with Text-Guided Diffusion Models
**Nichol et al., ICML 2022** | `10-Nichol2021-GLIDE.pdf`

**核心贡献：首次将扩散模型大规模应用于文生图，展示惊人写实能力。**

- 比较了两种文本条件注入方式：**classifier-free guidance** vs **CLIP guidance**，发现前者在人类评估中更优。
- 使用大规模 Transformer 文本编码器（而非固定的 CLIP），并同时支持图像编辑（inpainting）。
- 核心发现：classifier-free guidance 比 classifier guidance 在主观质量上更受人类偏好，推动了整个领域转向 CFG。
- 为 DALL-E 2 提供了直接的工程经验。

### High-Resolution Image Synthesis with Latent Diffusion Models (Stable Diffusion)
**Rombach et al., CVPR 2022** | `11-Rombach2022-Latent-Diffusion.pdf`

**核心贡献：提出在潜空间（latent space）而非像素空间进行扩散，极大降低了计算成本，使文生图走向大众。**

- 使用预训练的 VQ-VAE 或 VAE 将图像压缩到低维潜空间（如 256×256 → 32×32 latent，4-8 倍压缩），在潜空间中进行扩散。
- 引入**交叉注意力**（cross-attention）机制，将文本/布局/语义图等多种条件注入 U-Net。
- 在保持高质量的同时，训练和推理成本降低一个数量级，使 **Stable Diffusion** 能在消费级 GPU 上运行。
- 开源策略促进了整个 AIGC 生态的爆发（ControlNet、LoRA、DreamBooth 等均基于此）。

### DALL-E 2 (unCLIP)
**Ramesh et al., 2022** | `12-Ramesh2022-DALLE2.pdf`

**核心贡献：提出两阶段生成架构，先通过 CLIP 潜空间生成嵌入，再基于嵌入生成图像。**

- 第一阶段：**先验（prior）** 模型，从文本描述生成 CLIP 图像嵌入。
- 第二阶段：**解码器（decoder）** 扩散模型，从 CLIP 图像嵌入生成最终图像。
- 展示了 CLIP 潜空间的强语义表达能力：在该空间中的插值对应图像内容的语义混合。
- 支持图像变体（variation）和风格迁移，在写实性、文本相关性、分辨率上达到新的 SOTA。

### Photorealistic Text-to-Image Diffusion Models with Deep Language Understanding (Imagen)
**Saharia et al., NeurIPS 2022** | `13-Saharia2022-Imagen.pdf`

**核心贡献：证明大型语言模型（T5）比单纯增大文本编码器对文生图的帮助更大。**

- 关键发现：使用**冻结的大语言模型**（T5-XXL）编码文本，效果远超 CLIP 或训练好的 Transformer 编码器。
- 采用级联架构（类 DALL-E 2）：基础扩散模型 64×64 → 两阶段超分辨率至 256×256 和 1024×1024。
- 提出 **DrawBench** 基准，系统评估文生图模型的组合性、基数性、空间关系等能力。
- 在人类评估中远超 DALL-E 2 和 GLIDE，并引出 "scaling the text encoder is more effective than scaling the diffusion U-Net" 的重要经验。

### eDiff-I: Text-to-Image Diffusion Models with an Ensemble of Expert Denoisers
**Balaji et al., 2023** | `15-Balaji2022-eDiffI.pdf`

**核心贡献：提出专家去噪器集成，在不同扩散阶段使用不同的模型专注于不同频段。**

- 将去噪过程分为多个阶段，每个阶段由专门的专家模型处理（低频结构 → 中频纹理 → 高频细节）。
- 在训练过程中使用不同的噪声调度和资源分配，各专家关注不同的生成子任务。
- 支持 "paint-by-text" 交互式编辑，可用文本笔刷修改图像的特定区域。
- 在 COCO FID 上领先于 DALL-E 2 和 Imagen。

---

## 5. 高效采样与加速推理 (2022)

### DPM-Solver: A Fast ODE Solver for Diffusion Probabilistic Model Sampling
**Lu et al., NeurIPS 2022** | `25-Lu2022-DPM-Solver.pdf`

**核心贡献：专为扩散模型的半线性 ODE 结构设计的快速求解器。**

- 观察到扩散 ODE 具有**半线性**结构：线性部分可精确求解，非线性部分需要近似。
- 利用指数积分（exponential integrator）将去噪函数从 ODE 中解耦，在每个子区间内做有限阶 Taylor / Runge-Kutta 展开。
- DPM-Solver++ (3 阶) 仅需 **15–20 步**即可达到 DDPM 1000 步的质量，成为 Stable Diffusion 社区最常用的加速采样器之一。

### Elucidating the Design Space of Diffusion-Based Generative Models (EDM)
**Karras et al., NeurIPS 2022** | `24-Karras2022-EDM.pdf`

**核心贡献：系统性地梳理和优化扩散模型的设计空间。**

- 提出统一视角重新参数化扩散过程，不再沿用 VP/VE 的分类，而是从 ODE/SDE 求解的角度重新设计。
- 引入 **Preconditioning（预条件）** 策略：对网络输入、输出和损失函数进行缩放，使训练在所有噪声水平上均衡。
- 提出 **Heun's 2nd order sampler** 和噪声条件的调度策略，仅需 35 步即可达到高质量。
- 在 FFHQ、ImageNet 等基准上全面刷新 SOTA，被广泛认为是扩散模型的最优训练/采样配置之一。

### Variational Diffusion Models
**Kingma et al., NeurIPS 2021** | `26-Kingma2021-Variational-Diffusion.pdf`

**核心贡献：从变分自编码器（VAE）角度重新理解扩散模型，并实现负 ELBO 直接优化。**

- 证明了扩散模型是 VAE 的连续扩展（无限层、连续时间），将扩散损失重写为标准 VAE 的变分下界。
- 引入**傅里叶特征**（Fourier features）编码噪声水平，提升训练稳定性。
- 提出可学习的噪声调度（而非固定的线性/余弦调度），模型自适应学习最优的去噪策略。
- 在无损压缩方面展示了扩散模型的可能性（可达与 SOTA 接近的 bits/dim）。

---

## 6. 精细控制、个性化与编辑 (2022–2023)

### DreamBooth: Fine Tuning Text-to-Image Diffusion Models for Subject-Driven Generation
**Ruiz et al., CVPR 2023** | `14-Ruiz2022-DreamBooth.pdf`

**核心贡献：仅需 3–5 张特定物体的照片即可将该物体"植入"扩散模型，使其能在任意上下文中生成该物体。**

- 微调预训练的文生图模型，使用稀有词（如 "sks"）作为标识符绑定特定物体。
- 提出 **Prior Preservation Loss**：在微调时同时生成同类别的泛化样本，防止过拟合和灾难性遗忘。
- 支持物体在不同场景、姿态、光照、背景下的逼真重合成。
- 引发了 "个性化生成" 研究热潮，是 LoRA + SD 生态中的核心玩法之一。

### ControlNet: Adding Conditional Control to Text-to-Image Diffusion Models
**Zhang et al., ICCV 2023** | `19-Zhang2023-ControlNet.pdf`

**核心贡献：为预训练的扩散模型添加精确的空间条件控制，同时保持原始能力不变。**

- 设计**锁死原始权重 + 可训练复制**的架构：原始 U-Net 权重冻结，训练一个复制的编码器处理额外条件（边缘、深度、姿态、分割图等）。
- 使用**零卷积**（zero-convolution，初始化为零的 1×1 卷积）连接可训练分支和冻结主干，确保训练初期不影响原始输出。
- 支持 Canny 边缘、HED 边界、深度图、法线图、人体姿态、涂鸦等多种条件，且可组合使用。
- 极大拓展了 SD 在可控生成中的应用范围，成为 AIGC 工作流的标准组件。

### InstructPix2Pix: Learning to Follow Image Editing Instructions
**Brooks, Holynski & Efros, CVPR 2023** | `29-Brooks2023-InstructPix2Pix.pdf`

**核心贡献：基于文本指令直接编辑图像，无需冗长的输入输出描述。**

- 联合微调 GPT-3 生成的编辑指令对和 Prompt-to-Prompt 生成的配对图像，构建大规模编辑数据集。
- 在潜空间扩散模型中注入文本指令条件，使模型学会 "按照指令修改图像" 而非 "描述目标图像"。
- 支持多种编辑操作：替换物体、改变风格、修改天气/季节、调整表情等，用户只需要自然语言告诉模型 "让天空变成日落"。
- 推理仅需单次前向扩散 + 反演过程，无需每张图像单独微调，比 DreamBooth 更轻量。

### DreamFusion: Text-to-3D using 2D Diffusion
**Poole et al., ICLR 2023** | `27-Poole2022-DreamFusion.pdf`

**核心贡献：利用预训练的 2D 文生图扩散模型生成 3D 内容，无需 3D 训练数据。**

- 提出 **Score Distillation Sampling (SDS)**：将 2D 扩散模型的得分/梯度反向传播到 3D 表示（NeRF），优化 3D 参数使任意视角渲染的 2D 投影都符合文本描述。
- 这是首次展示 2D 扩散模型可以作为 3D 生成的"先验"，无需任何 3D 标注数据。
- 启发了 DreamGaussian、Magic3D 等大量后续 Text-to-3D 工作。

---

## 7. 视频生成时代：从 SVD 到 Seedance (2022–2025)

> 视频生成是扩散模型从学术走向产业的关键赛道。从 2022 年的 3D U-Net 探索，到 2024–2025 年百花齐放的 DiT 大模型（Sora、Movie Gen、Seedance），视频扩散模型在架构、效率、可控性上完成了质的飞跃。

### 7.1 早期探索

#### Video Diffusion Models
**Ho et al., NeurIPS 2022** | `16-Ho2022-Video-Diffusion.pdf`

**核心贡献：将扩散模型从图像生成推广到视频生成。**

- 使用 **3D U-Net** 架构：在空间维度上使用 2D 卷积，时间维度上引入帧间注意力，联合处理多帧。
- 提出联合训练图像和视频数据的策略，利用图像数据缓解视频数据稀缺的问题。
- 展示了无条件视频生成、文本条件视频生成和自回归视频预测的能力。

#### Imagen Video: High Definition Video Generation with Diffusion Models
**Ho et al., 2022** | `17-Ho2022-Imagen-Video.pdf`

**核心贡献：基于 Imagen 文生图流水线扩展到高分辨率视频。**

- 采用**级联时空超分辨率**流水线：基础模型生成低分辨率低帧率 → 时间超分辨率（TSR）提升帧率 → 空间超分辨率（SSR）提升分辨率。
- 使用 **v-prediction** 参数化（预测速度而非噪声），在视频生成中表现更稳定。
- 生成 1280×768、128 帧的视频，证明了 T5 文本编码器 + 级联架构的视频扩展能力。

### 7.2 潜空间视频扩散

#### Stable Video Diffusion (SVD)
**Blattmann et al., 2023** | `31-Blatmann2023-Stable-Video-Diffusion.pdf`

**核心贡献：将 Stable Diffusion 的潜空间扩散范式系统性地扩展到视频领域并开源。**

- 提出**三阶段训练框架**：图像预训练（SD 2.1）→ 低分辨率大规模视频预训练（LVD-F，1.52 亿样本）→ 高质量小数据集微调。
- 设计了**系统性视频数据筛选流水线**：级联切分检测、光流运动评分、OCR 文本剔除、CLIP 美学评分。
- 支持多任务：文本到视频、图像到视频、帧插值、多视图生成。
- 提出 **Camera Motion LoRA**，用 LoRA 模块控制镜头运动（平移、前进、静止等）。

#### Emu Video
**Girdhar et al., 2023** | `32-Girdhar2023-Emu-Video.pdf`

**核心贡献：提出"分解式"文生视频方法，将视频生成分解为图像生成 + 图像动画化两步。**

- 第一阶段：基于文本提示生成单帧高质量图像。
- 第二阶段：以文本 + 生成的图像为条件，生成视频序列。
- 这种分解策略显著降低了视频生成的难度，在人类评估中优于当时的一步式方法。

#### Lumiere: A Space-Time Diffusion Model for Video Generation
**Bar-Tal et al., 2024** | `30-BarTal2024-Lumiere.pdf`

**核心贡献：提出 Space-Time U-Net (STUNet)，一次生成完整时间跨度的视频。**

- 区别于级联式逐段生成，STUNet 在 U-Net 内部进行**时空联合下/上采样**，在紧凑的时空表示中处理整个视频。
- 一次生成 **80 帧 @ 16fps**（约 5 秒），实现全局连贯的运动。
- 基于冻结的 T2I 模型，仅训练新增的时间层，利用 **Multidiffusion** 实现空间超分辨率。
- 支持文生视频、图生视频、视频修复、风格化生成和 Cinemagraph。

### 7.3 DiT 大规模视频模型

#### Sora (OpenAI)
**OpenAI, 2024** | *仅网页技术报告，无 PDF*

**核心贡献：首次将 Diffusion Transformer (DiT) 扩展到视频领域，展示"视频世界模拟"的可能性。**

- 将视频压缩为**时空补丁（spacetime patches）**，类比 LLM 中的文本 token，使用 DiT 在潜空间中进行去噪。
- 原生支持**可变时长、分辨率和宽高比**的视频生成。
- 涌现的模拟能力：3D 一致性、长程物体持久性、基本物理交互、数字世界模拟（如 Minecraft）。
- 最长可生成 **60 秒**视频，远超市面上其他模型（当时普遍 2–16 秒）。
- 使用 DALL-E 3 风格的**重标注（re-captioning）** 提升文本理解，限制在于物理建模仍不可靠。

#### CogVideoX
**Yang et al., ICLR 2025** | `33-Yang2024-CogVideoX.pdf`

**核心贡献：开源的高质量 DiT 文生视频模型，引入专家 Transformer 设计。**

- 使用**3D 因果 VAE** 进行时空压缩，在潜空间中应用 DiT 进行去噪。
- 引入**专家 Transformer**模块处理不同帧率和运动模式的视频数据。
- 完全开源（代码 + 权重），在开源社区中影响力巨大，性能直逼闭源商业模型。

#### Movie Gen: A Cast of Media Foundation Models
**Meta, 2024** | `34-Meta2024-Movie-Gen.pdf`

**核心贡献：Meta 的 30B 视频 + 13B 音频联合生成系统。**

- **Movie Gen Video**：基于 Llama 3 架构的 30B Transformer，使用 Flow Matching，生成 1080p@16fps 最长 16 秒视频。
- **Movie Gen Audio**：13B Transformer 生成 48kHz 影院级音效和音乐，与视频同步。
- 关键技术：**Temporal Autoencoder (TAE)** 实现 8× 时空压缩；**分解式可学习位置编码**（高/宽/时间独立编码）；线性二次时间步调度（~50 步推理）。
- 在整体视频质量上超越 Runway Gen-3、Sora 和 Kling 1.5。

#### HunyuanVideo
**Kong et al., 2024** | `35-Kong2024-HunyuanVideo.pdf`

**核心贡献：腾讯开源的 13B+ 参数视频生成系统。**

- 当时最大的开源视频生成模型，提供从数据策展到架构设计到大规模训练的完整方案。
- 使用 **3D VAE + Full DiT** 架构，全面拥抱 DiT 路线。
- 开源后打破了闭源/开源的性能差距，推动了社区生态发展。

#### Wan: Open and Advanced Large-Scale Video Generative Models
**Alibaba Tongyi Lab, 2025** | `36-Wan2025-Wan.pdf`

**核心贡献：阿里开源的全能视频基础模型套件。**

- 提供 **1.3B（仅需 8.19GB VRAM）和 14B** 两个版本，兼顾消费级和前沿性能。
- 覆盖 **8 种下游任务**：文生视频、图生视频、指令视频编辑、个性化视频生成等。
- 在多个 benchmark 上全面超越开源和商业方案，同时保持完全开放（代码 + 权重 + 论文）。
- 衍生工作丰富：Wan-S2V（音频驱动视频）、Wan-Alpha（透明度通道生成）等。

### 7.4 字节跳动 Seed 视频生成系列

#### Seaweed-7B
**ByteDance Seed, 2025** | `38-ByteDance2025-Seaweed.pdf`

**核心贡献：70 亿参数的高效视频基础模型，仅用 665K H100 GPU 小时完成训练。**

- 以极低的训练成本实现媲美甚至超越更大模型的性能（仅需约 27.7 天 × 1000 H100）。
- "Seaweed" = Seed Video 缩写，展示了在算力约束下的高效扩展策略。

#### Seedance 1.0
**ByteDance Seed, 2025** | `37-ByteDance2025-Seedance.pdf`

**核心贡献：字节跳动旗舰视频生成模型，在质量和效率上全面突破。**

- **多源数据策展 + 精准视频字幕**：高质量数据是性能的基础。
- **解耦空间/时间层**：高效架构设计，原生支持多镜头生成，联合学习 T2V 和 I2V。
- **视频专用 RLHF**：多维奖励机制（视觉质量、运动自然度、文本对齐度）的精细化 SFT 和 RL 对齐。
- **~10× 推理加速**：多阶段蒸馏 + 系统优化，在 NVIDIA L20 上仅需 **41.4 秒**生成 5 秒 1080p 视频。

#### Seedance 1.5 Pro
**ByteDance Seed, 2025** | *2512.13507（需单独下载）*

**核心贡献：业界首个原生音视频联合生成基础模型。**

- **双分支 DiT 架构**：音频分支和视频分支在潜空间中通过跨模态联合模块交互。
- 原生联合生成视频 + 同步音频，支持**精准多语言口型同步**和**动态电影级相机控制**。
- 多阶段数据管线确保音视频语义对齐，已在火山引擎上线。

---

## 8. Flow Matching 范式 (2023–2024)

### Flow Matching for Generative Modeling
**Lipman et al., ICLR 2023** | `09-Lipman2023-Flow-Matching.pdf`

**核心贡献：提出 Flow Matching 框架，为连续归一化流（CNF）提供简单高效的训练方法。**

- Diffusion 模型是 CNF 的特例（概率路径固定为先验分布之间的高斯条件路径），Flow Matching 将其推广到任意概率路径。
- 核心公式 L_FM(θ) = E[||v_t(x) − u_t(x|x_1)||²]，通过条件流匹配避免了传统 CNF 需要仿真 ODE 来获取训练目标的高昂代价。
- 导出了三种条件概率路径：扩散路径（diffusion）、最优传输路径（OT）和带调度路径（scheduling）。
- OT 路径实现**直线流**（straight-line flows），理论上允许一步采样。

### Rectified Flow
**Liu et al., ICLR 2023** | `08-Liu2023-Rectified-Flow.pdf`

**核心贡献：提出重流（Rectified Flow）方法，通过多次整流将弯曲的流动路径"拉直"，实现少步采样。**

- 将生成建模看作从噪声分布到数据分布的**传输映射**（transport map），使用 ODE 连接两者。
- **重流过程**（Reflow）：训练一个"学生"模型来学习"教师"模型的 ODE 轨迹，重复此过程使流线越来越直。
- 直线流允许在极少的采样步数下保持质量（甚至一步生成）。
- 与 Flow Matching 有深厚的数学联系，两者共同推动了扩散模型向"一步生成"的演进。

---

## 9. Scaling Up：DiT、SDXL、SD3 与大模型时代 (2023–2025)

### Scalable Diffusion Models with Transformers (DiT)
**Peebles & Xie, ICCV 2023** | `18-Peebles2023-DiT.pdf`

**核心贡献：用纯 Transformer 架构（ViT + AdaLN）取代 U-Net 作为扩散模型的骨干网络。**

- 将图像 Patchify 为 token 序列，使用多层 Transformer block 处理，条件（如时间步、类别标签）通过**自适应层归一化**（AdaLN）注入。
- 展示了扩散模型遵循与 LLM 相似的**扩展律**（scaling law）：更大的 Transformer 模型 + 更多计算量 → 单调提升的生成质量。
- 四种方案比较后确定 adaLN-Zero 是最优的条件注入方式。
- 直接启发 Sora（DiT + 视频数据）和 SD3（MM-DiT 架构）的设计。

### SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis
**Podell et al., ICLR 2024** | `21-Podell2023-SDXL.pdf`

**核心贡献：将 Stable Diffusion 扩展到高分辨率原生生成（1024×1024）。**

- 将 U-Net 参数量扩大 3 倍（860M → 2.6B），更深的骨干和更多的注意力头。
- 引入**两个文本编码器**（CLIP ViT-L + OpenCLIP ViT-bigG）联合编码，互补长短文本理解。
- 提出**大小条件**（size conditioning）和**裁剪条件**（crop conditioning），解决训练数据尺寸不统一的问题。
- 使用**精细化器**（refiner）：在最终阶段用单独的扩散模型对细节进行优化。
- 提供了高质量 midjourney 风格的文生图开源方案。

### Consistency Models
**Song et al., ICML 2023** | `20-Song2023-Consistency-Models.pdf`

**核心贡献：提出一致性模型，支持单步生成，将扩散模型推理速度提升到极致。**

- 学习一个**一致性函数** f(x_t, t) → x_0，使得从同一 PF-ODE 轨迹上任意点出发都映射到同一个干净样本。
- 可通过**蒸馏**（Consistency Distillation，从预训练扩散模型中蒸馏）或**直接训练**两种方式获得。
- 仅需 **1–2 步推理**即可生成高质量图像，在 CIFAR-10 和 ImageNet 上接近扩散模型 1000 步的质量。
- 对实时应用和边缘设备部署具有巨大意义。

### SiT: Exploring Flow and Diffusion-based Generative Models with Scalable Interpolant Transformers
**Ma et al., 2024** | `22-Ma2024-SiT.pdf`

**核心贡献：将 Diffusion Transformer (DiT) 与 Flow Matching 统一在插值框架下。**

- 提出可扩展的**插值 Transformer（SiT）**，系统比较了不同插值路径（diffusion vs. flow）、不同预测目标（x0, ε, v）和不同采样器的影响。
- 关键结论：**连续时间 Flow Matching + v-prediction + ODE 采样**在 ImageNet 上全面超越 DiT。
- 为 Flow Matching 在大规模图像生成上的应用提供了强有力的实证支撑。

### Scaling Rectified Flow Transformers for High-Resolution Image Synthesis (Stable Diffusion 3)
**Esser et al., 2024** | `23-Esser2024-SD3.pdf`

**核心贡献：将 Rectified Flow、DiT 架构和大规模训练统一，推出 SD3。**

- 使用 **MM-DiT（多模态 DiT）**：文本 token 和图像 token 在同一个 Transformer 中联合处理，通过双流注意力（separate weights for text and image）交互。
- 采用 **Rectified Flow** 作为生成框架（而非传统的 DDPM/DDIM），使用直线概率路径。
- 大规模训练（80 亿参数），展示了 **"scaling the model works"**——文本理解能力、视觉质量、拼写准确性随模型增大而提升。
- 在人类评估中全面优于 SDXL、DALL-E 3 和 Midjourney v6。

---

## 10. 论文索引表

| 编号 | 文件名 | 作者/年份 | 核心关键词 |
|------|--------|-----------|-----------|
| 01 | SohlDickstein2015 | Sohl-Dickstein, 2015 | 非平衡热力学，扩散概率模型基础 |
| 02 | Song2021-DDIM | Song et al., 2021 | 非马尔可夫逆过程，确定性反演，加速采样 |
| 03 | Song2021-Score-SDE | Song et al., 2021 | SDE统一框架，Probability Flow ODE |
| 04 | Nichol2021-Improved-DDPM | Nichol & Dhariwal, 2021 | 可学习方差，余弦调度，似然优化 |
| 05 | Dhariwal2021-Diffusion-Beat-GANs | Dhariwal & Nichol, 2021 | 分类器引导，架构优化，超越GAN |
| 06 | Ho2022-Classifier-Free-Guidance | Ho & Salimans, 2022 | 无分类器引导，CFG标配 |
| 07 | Ho2021-Cascaded-Diffusion | Ho et al., 2021 | 级联扩散架构，超分辨率流水线 |
| 08 | Liu2023-Rectified-Flow | Liu et al., 2023 | 重流，直线概率路径，少步生成 |
| 09 | Lipman2023-Flow-Matching | Lipman et al., 2023 | 流匹配，最优传输路径 |
| 10 | Nichol2021-GLIDE | Nichol et al., 2021 | 文生图先驱，classifier-free优于CLIP引导 |
| 11 | Rombach2022-Latent-Diffusion | Rombach et al., 2022 | Stable Diffusion，潜空间扩散，交叉注意力 |
| 12 | Ramesh2022-DALLE2 | Ramesh et al., 2022 | unCLIP，CLIP潜空间，两阶段生成 |
| 13 | Saharia2022-Imagen | Saharia et al., 2022 | T5编码器，DrawBench，级联超分辨率 |
| 14 | Ruiz2022-DreamBooth | Ruiz et al., 2022 | 主体驱动生成，Prior Preservation Loss |
| 15 | Balaji2022-eDiffI | Balaji et al., 2022 | 专家去噪器集成，分阶段生成 |
| 16 | Ho2022-Video-Diffusion | Ho et al., 2022 | 3D U-Net，视频扩散模型 |
| 17 | Ho2022-Imagen-Video | Ho et al., 2022 | 文本到视频，级联时空超分辨率 |
| 18 | Peebles2023-DiT | Peebles & Xie, 2023 | Transformer替代U-Net，扩散扩展律 |
| 19 | Zhang2023-ControlNet | Zhang et al., 2023 | 零卷积，空间条件控制 |
| 20 | Song2023-Consistency-Models | Song et al., 2023 | 一致性模型，1-2步生成 |
| 21 | Podell2023-SDXL | Podell et al., 2023 | 高分辨率原生生成，大小/裁剪条件 |
| 22 | Ma2024-SiT | Ma et al., 2024 | 插值Transformer，Flow vs Diffusion |
| 23 | Esser2024-SD3 | Esser et al., 2024 | MM-DiT，Rectified Flow，大规模扩展 |
| 24 | Karras2022-EDM | Karras et al., 2022 | 设计空间梳理，Preconditioning，Heun采样 |
| 25 | Lu2022-DPM-Solver | Lu et al., 2022 | 半线性ODE，指数积分器，15-20步采样 |
| 26 | Kingma2021-Variational-Diffusion | Kingma et al., 2021 | VAE角度，可学习噪声调度，傅里叶特征 |
| 27 | Poole2022-DreamFusion | Poole et al., 2022 | SDS，2D扩散→3D生成 |
| 28 | OpenAI2023-DALLE3 | OpenAI, 2023 | 图像字幕重标注，提升文本遵循能力 |
| 29 | Brooks2023-InstructPix2Pix | Brooks et al., 2023 | 文本指令图像编辑，单次推理 |
| 30 | BarTal2024-Lumiere | Bar-Tal et al., 2024 | Space-Time U-Net，一次生成完整视频 |
| 31 | Blattmann2023-Stable-Video-Diffusion | Blattmann et al., 2023 | SVD，三阶段训练，Camera Motion LoRA |
| 32 | Girdhar2023-Emu-Video | Girdhar et al., 2023 | 分解式T2V：先生成图像再动画化 |
| 33 | Yang2024-CogVideoX | Yang et al., 2024 | 专家Transformer，开源DiT视频模型 |
| 34 | Meta2024-Movie-Gen | Meta, 2024 | 30B视频+13B音频，Flow Matching |
| 35 | Kong2024-HunyuanVideo | Kong et al., 2024 | 13B+开源视频模型，Full DiT架构 |
| 36 | Wan2025-Wan | Alibaba, 2025 | 1.3B/14B，8种任务，全开放视频套件 |
| 37 | ByteDance2025-Seedance | ByteDance, 2025 | 解耦时空层，视频RLHF，10×推理加速 |
| 38 | ByteDance2025-Seaweed | ByteDance, 2025 | 7B高效视频基础模型，665K GPU时 |
| 39 | Liu2024-Sora-Review | Liu et al., 2024 | Sora综述：背景、技术、局限与机遇 |

---

## 附：技术脉络图

```
2015  非平衡热力学 (Sohl-Dickstein)
       │
2020  DDPM (Ho) ─────── 奠定实用框架
       │
2021  ├─ DDIM (Song) ── 加速 + 确定性反演
       ├─ Score SDE (Song) ── 连续时间统一框架
       ├─ Improved DDPM (Nichol) ── 质量优化
       ├─ Classifier-Guided (Dhariwal) ── 超越 GAN
       ├─ CFG (Ho) ── 无分类器引导
       ├─ VDM (Kingma) ── VAE 视角
       │
2022  ├─ Latent Diffusion (Rombach) ── Stable Diffusion
       ├─ DALL-E 2 / Imagen / eDiff-I ── 文生图爆发
       ├─ GLIDE ── 文生图先驱
       ├─ DreamBooth ── 个性化
       ├─ EDM (Karras) ── 设计空间优化
       ├─ DPM-Solver (Lu) ── 快速采样
       ├─ Video Diffusion / Imagen Video ── 早期视频探索
       │
2023  ├─ ControlNet (Zhang) ── 精确控制
       ├─ InstructPix2Pix (Brooks) ── 指令编辑
       ├─ DiT (Peebles) ── Transformer 骨干
       ├─ Rectified Flow / Flow Matching ── 新范式
       ├─ Consistency Models (Song) ── 一步生成
       ├─ SDXL (Podell) ── 高分辨率开源
       ├─ DreamFusion (Poole) ── 2D→3D
       ├─ SVD (Blattmann) ── 潜空间视频扩散
       ├─ Emu Video (Girdhar) ── 分解式T2V
       │
2024  ├─ SD3 (Esser) ── MM-DiT + Rectified Flow
       ├─ SiT (Ma) ── 插值框架
       ├─ Sora (OpenAI) ── 视频 DiT，世界模拟
       ├─ Lumiere (Bar-Tal) ── Space-Time U-Net
       ├─ CogVideoX (Yang) ── 开源 DiT 视频
       ├─ Movie Gen (Meta) ── 30B 视频+音频
       ├─ HunyuanVideo (Kong) ── 13B+ 开源视频
       │
2025  ├─ Wan (Alibaba) ── 全开放视频套件
       ├─ Seaweed / Seedance (ByteDance) ── 高效视频+音视频联合
       └─ → 实时生成、世界模型、物理仿真 ...
```

---

> **整理日期**：2026-05-18
> **论文总篇数**：39（38 篇 PDF 已完整下载 + 1 篇 Sora 仅网页技术报告）
> **PDF 总大小**：784 MB
> **PDF 存储目录**：`diffusion-papers/`
