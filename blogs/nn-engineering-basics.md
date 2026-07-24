---
layout: default
title: 神经网络工程基础：PyTorch 训练框架与核心算子
---

# 神经网络工程基础：PyTorch 训练框架与核心算子
[← 回到首页](..)

> **Neural Network Engineering Basics: PyTorch Training Framework & Core Operators**
>
> 目标：用最少的示例串起 Tensor → Autograd → 核心算子 → 损失函数 → 优化器 → 完整训练循环
>
> 撰写于 2026 年 7 月

---

## 符号约定

| 符号 | 含义 |
|------|------|
| $\mathbf{x}$ | 输入张量 |
| $\mathbf{W}$ | 权重矩阵 |
| $\mathbf{b}$ | 偏置向量 |
| $\mathbf{y}$ / $\hat{\mathbf{y}}$ | 模型输出 / 预测值 |
| $\mathcal{L}$ | 损失函数 |
| $\frac{\partial \mathcal{L}}{\partial \mathbf{W}}$ | 损失对权重的梯度 |
| $\eta$ | 学习率 |
| $\mathbf{1}\{\cdot\}$ | 指示函数 |

---

## 第一章：Tensor 与 Autograd — 一切开始的地方

### 1.1 Tensor：不只是多维数组

在 NumPy 中，`ndarray` 就是一个装着数字的多维数组。PyTorch 的 `Tensor` 在 NumPy 数组的基础上加了一个关键字段：**`.grad`**。这个 `.grad` 让张量从"被动数据结构"变成了"自动微分图中的节点"。

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

# 创建一个需要梯度的张量
x = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
# x.grad 现在是 None，因为还没有进行任何计算
print(f"x.grad: {x.grad}")  # None
```

**Tensor 的三个核心属性**：

| 属性 | 类型 | 含义 |
|------|------|------|
| `.data` | Tensor | 张量中的数值本身（不参与梯度计算） |
| `.grad` | Tensor 或 None | 损失函数对该张量的梯度 |
| `.requires_grad` | bool | 是否需要计算梯度 |

此外还有三个与工程紧密相关的属性：

| 属性 | 示例 | 含义 |
|------|------|------|
| `.dtype` | `torch.float32` | 数据类型——决定了精度和显存占用 |
| `.device` | `cuda:0` | 设备——CPU 还是某张 GPU |
| `.shape` | `(2, 3, 256, 256)` | 形状——这是你自己定义的 |

**创建张量的常用方式**：

```python
# ── 从 Python 数据创建 ──
a = torch.tensor([1.0, 2.0, 3.0])            # 从 list（自动推断 dtype）
a_int = torch.tensor([1, 2, 3], dtype=torch.long)  # 指定 dtype

# ── 常量填充 ──
b_zeros = torch.zeros(3, 4)                   # 全 0 矩阵
b_ones  = torch.ones(3, 4)                    # 全 1 矩阵
b_full  = torch.full((3, 4), 7.0)             # 全 7 填充
b_eye   = torch.eye(3)                         # 3×3 单位矩阵
b_empty = torch.empty(3, 4)                   # 未初始化（内存里的废数据，速度快）

# ── 等差数列 ──
d = torch.arange(0, 10, step=2)               # [0, 2, 4, 6, 8] —— 左闭右开
d_lin = torch.linspace(0, 1, steps=5)          # [0.00, 0.25, 0.50, 0.75, 1.00] —— 闭区间
```

**随机初始化**（这是深度学习中最常用的创建方式）：

```python
# ── 正态分布 ──
r_normal = torch.normal(mean=0.0, std=1.0, size=(3, 4))   # 自定义均值和标准差
r_randn  = torch.randn(3, 4)        # 标准正态 N(0, 1)，等价于 normal(0, 1, ...)
# 直觉：约 68% 的值落在 [-1, 1]，约 95% 落在 [-2, 2]
# 用于：Linear 权重初始化（GPT-2 用 std=0.02）、生成随机噪声

# ── 均匀分布 ──
r_rand  = torch.rand(3, 4)          # [0, 1) 均匀分布
r_unif  = (torch.rand(3, 4) * 2 - 1)  # 手动缩放到 [-1, 1]

# _like 后缀：复用已有张量的 shape/dtype/device
r_randn_like = torch.randn_like(b_zeros)     # 和 b_zeros 形状相同的 N(0,1)
r_rand_like  = torch.rand_like(b_zeros)      # 和 b_zeros 形状相同的 [0,1)
r_zeros_like = torch.zeros_like(r_randn)     # 和 r_randn 形状相同的全 0

# ── 特定初始化公式（直接用 torch.nn.init）──
# 这些在 §2.2 中会详细讲，这里先看一眼：
import math
import torch.nn.init as init
w = torch.empty(256, 512)            # 先开空间，再填值
init.kaiming_uniform_(w, a=math.sqrt(5))  # He 初始化，ReLU 网络的标配
init.xavier_uniform_(w)              # Xavier/Glorot 初始化，tanh/sigmoid 用
init.normal_(w, std=0.02)            # 自定义标准差的正态初始化
# 末尾的 _ 表示 in-place 操作——直接修改 w 的值，不创建新张量
```

**设备与类型迁移**：

```python
# 与 NumPy 互转
import numpy as np
arr = np.array([1.0, 2.0])
t = torch.from_numpy(arr)                     # NumPy → Tensor（共享内存）
arr_back = t.numpy()                           # Tensor → NumPy（共享内存）

# 设备迁移
t_cpu = torch.randn(3, 4)                     # 默认在 CPU
t_gpu = t_cpu.cuda()                           # 移到 GPU:0
t_gpu2 = t_cpu.to('cuda:1')                    # 移到 GPU:1
t_back = t_gpu.cpu()                           # 移回 CPU
```

> **共享内存的陷阱**：`torch.from_numpy()` 和 `.numpy()` 创建的 Tensor/ndarray 与原始对象共享同一块内存。修改其中一方会影响另一方。如果需要独立拷贝，使用 `.clone()`。

### 1.2 Autograd：当你写 `loss.backward()` 时发生了什么

**自动微分**（automatic differentiation）是 PyTorch 的灵魂。它的本质是：你在写前向计算时，PyTorch 在后台为你构建了一张**计算图**（computation graph）。当你调用 `.backward()` 时，它沿着这张图从后往前传播梯度，把每条边上的导数乘起来。

```python
# 最小示例
x = torch.tensor([2.0], requires_grad=True)
y = x ** 2        # y = x²
y.backward()      # 计算 dy/dx = 2x = 4.0
print(x.grad)     # tensor([4.])
```

**为什么会得到 4.0？**

计算图非常简单：`x` → `pow(2)` → `y`。反向传播沿着这条边传回去，链式法则：

$$\frac{\partial y}{\partial x} = \frac{\partial}{\partial x} x^2 = 2x = 4.0$$

这个例子太简单了。来看一个更接近真实场景的例子：

```python
# 仿造一个"微型神经网络"：y = w * x + b
w = torch.tensor([3.0], requires_grad=True)
b = torch.tensor([1.0], requires_grad=True)
x = torch.tensor([2.0])           # 输入，不需要梯度

# 前向
z = w * x + b                     # z = 3*2 + 1 = 7
loss = (z - 10.0) ** 2            # loss = (7-10)² = 9

# 反向
loss.backward()

# 检查梯度
print(f"∂loss/∂w = {w.grad}")     # w.grad = 2*(z-10)*x = 2*(-3)*2 = -12
print(f"∂loss/∂b = {b.grad}")     # b.grad = 2*(z-10)*1 = -6

# 手动验证
# loss = (w*x + b - 10)²
# ∂loss/∂w = 2(w*x + b - 10) * x = 2*(7-10)*2 = -12 ✓
# ∂loss/∂b = 2(w*x + b - 10) * 1 = 2*(7-10)   = -6  ✓
```

**计算图长什么样？**

从 `loss` 出发反向追踪：`loss` 产生于 `(z - 10)²`，其输入 `z = w*x + b`，而 `z` 又来自 `w*x` 和 `b` 两条分支。`.backward()` 沿着这些边从后往前传梯度——`∂loss/∂[²]` 流向 `∂loss/∂[-]`，再分流到 `[+]` 和 `target`（不需求梯度），`[+]` 又分流到 `[*]` 和 `b`，最终 `w.grad` 和 `b.grad` 被填充。


### 1.3 三个关键规则

**规则一：`.backward()` 只能对**标量 **调用**

```python
z = w * x + b          # z 是标量吗？这个例子中是的，因为 x 和 w 都是一维标量
# 但如果是：
z = torch.randn(3, requires_grad=True)
# z.backward()         # RuntimeError! z 不是标量
z.sum().backward()      # 正确：先聚合成标量再 backward
```

原因很简单：反向传播的起点只能是一个数，因为你无法定义"一个向量对另一个向量的梯度"而不引入雅可比矩阵。

**规则二：计算图在 `.backward()` 后默认释放**

```python
x = torch.tensor([2.0], requires_grad=True)
y = x ** 2
y.backward()
# y.backward()         # RuntimeError! 计算图已被释放
```

如果想在同一张图上调用两次 `.backward()`（例如某些 GAN 的训练场景），需要 `retain_graph=True`：

```python
y.backward(retain_graph=True)  # 保留计算图
y.backward()                    # 第二次调用可以
```

**规则三：梯度是**累加 **的**

```python
w = torch.tensor([3.0], requires_grad=True)
for i in range(3):
    loss = (w - 2.0) ** 2
    loss.backward()
    print(w.grad)     # 第一次 2.0, 第二次 4.0, 第三次 6.0 —— 在累加！
```

这就是为什么每个训练步必须调用 `optimizer.zero_grad()` —— 把上一步的梯度清零。注意这和 §1.4 的梯度累积是两种不同的用法：梯度累积是**有意**跨多个 micro-batch 累加梯度来模拟大 batch，而这里不归零会导致上一步的过期梯度混入当前步的更新，相当于用两种不同 batch 数据的梯度混在一起来更新参数。

### 1.4 梯度累积与 no_grad

另外两个日常会用到的技巧：

```python
# 梯度累积（模拟更大的 batch size）
accumulation_steps = 4
optimizer.zero_grad()
for i, batch in enumerate(dataloader):
    loss = model(batch) / accumulation_steps
    loss.backward()                    # 梯度累加
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()               # 每 4 步更新一次
        optimizer.zero_grad()          # 清零

# 推理时禁用梯度计算
with torch.no_grad():
    predictions = model(test_input)    # 不构建计算图，节省显存
```

`torch.no_grad()` 在推理/验证时是必备的——它阻止 PyTorch 构建计算图，大幅减少显存占用，并加快推理速度。

### 1.5 计算图与 `.detach()`

有时你需要把某个张量从计算图中"拆"下来——它的值不变，但从它之后不再有梯度流回：

```python
x = torch.tensor([2.0], requires_grad=True)
y = x ** 2
z = y.detach()        # z = 4.0, 但 z 不再与 x 有梯度联系
w = z ** 2            # w = 16.0
w.backward()
print(x.grad)         # None —— 梯度被 detach 截断了
```

---

## 第二章：核心算子 — 神经网络的积木

有了 Tensor 和 Autograd 的基础，我们来看神经网络的积木。每个算子都可以从三个维度理解：

1. **前向公式**：给定输入，算出什么输出？
2. **参数**：有哪些可学习的参数？形状是什么？
3. **梯度**：损失对参数/输入的梯度如何计算？（PyTorch 帮你算，但你得知道它算的是什么）

### 2.1 矩阵基本功 — PyTorch 中的张量运算

在进入具体算子之前，先快速过一下本章反复使用的六种矩阵运算。它们不是 `nn.Module`，不存任何可学习参数，但构成了所有算子前向/反向传播的基础语言。

**（1）矩阵乘法 `@` —— 最核心的运算**

```python
A = torch.randn(4, 3)   # (4, 3)
B = torch.randn(3, 5)   # (3, 5)
C = A @ B                # (4, 5)

# 等价写法
C = torch.matmul(A, B)
C = torch.mm(A, B)       # 仅 2D
```

规则：`(m, n) @ (n, p)` → `(m, p)`。内维 `n` 必须相等，结果的每个元素是 A 的一行与 B 的一列的内积。

batch 矩阵乘法——高维张量中最后两维做矩阵乘法，前面的维度做 broadcast：

```python
A = torch.randn(2, 3, 4, 64)   # batch=2, heads=3, seq=4, d_k=64
B = torch.randn(2, 3, 64, 4)   # batch=2, heads=3, d_k=64, seq=4
C = A @ B                       # (2, 3, 4, 4) — 每个头独立做 QK^T
```

这就是 MHA 中 `Q @ K.transpose(-2, -1)` 的底层运算。

**（2）逐元素乘 `*` —— 门控、mask 的基础**

```python
A = torch.randn(3, 4)
B = torch.randn(3, 4)
C = A * B                # (3, 4)，每个元素独立相乘

# 等价写法
C = torch.mul(A, B)
```

逐元素乘用在 Dropout（`x * mask`）、SwiGLU 门控（`SiLU(xW1) * xW2`）、attention mask 等场景。

**（3）转置 `.T` 和维度交换 `.transpose()`**

```python
A = torch.randn(3, 4)
A.T                      # (4, 3)

# 通用版本：交换任意两个轴
A = torch.randn(2, 3, 4)
A.transpose(0, 2)        # (4, 3, 2)

# 高级版：任意排列维度
A.permute(1, 0, 2)       # (3, 2, 4)
```

**`.T` 和 `.transpose()` 都返回原张量的视图（共享内存），不拷贝数据**——这也是为什么以后缀 `_` 结尾的 in-place 操作（如 `.transpose_()`）需要格外小心，它们会修改原张量。

**（4）重塑形状 `.view()` / `.reshape()`**

```python
A = torch.randn(2, 3, 4, 64)     # (B, N, H, d_k)
A = A.transpose(1, 2)             # (B, H, N, d_k)
# 想把 H 和 d_k 合并 → 加 .contiguous() 确保内存连续
A = A.reshape(2, 3, -1)           # (2, 3, 256)，-1 表示自动推导
```

`view()` 要求张量在内存中是连续的（否则报错），`reshape()` 自动处理不连续的情况（必要时先拷贝）。多头的重组（拆头/拼回）几乎都是 `transpose` + `reshape` 的组合。

**（5）Broadcast — 形状不同也能运算**

```python
# 形状不同的张量自动"扩"到兼容形状
x = torch.randn(3, 4)             # (3, 4)
b = torch.randn(4)                # (4,) → 自动扩为 (3, 4)
y = x + b                         # (3, 4)，等价于每行加同一个偏置

# 这就是 nn.Linear 中 + bias 的底层机制！
# bias 形状 (d_out,) + broadcast → (n, d_out)
```

广播规则（从右往左对齐维度，逐一比较）：
1. 如果维度相同 → 直接匹配
2. 如果其中一个是 1 → 沿该维度复制
3. 如果大小不同且都不是 1 → 报错

典型场景：`bias` 加在所有样本上、BatchNorm 的 `γ` 和 `β` 沿 batch/空间维度广播。

**（6）沿轴求和 `.sum()` / 均值 `.mean()`**

```python
X = torch.randn(2, 3, 4)

X.sum()                  # 标量，所有元素求和
X.sum(dim=0)             # (3, 4)，沿 batch 维度坍缩
X.sum(dim=1)             # (2, 4)，沿第二维坍缩
X.sum(dim=-1)            # (2, 3)，沿最后一维坍缩

# keepdim=True 保持维度数不变（方便后续 broadcast）
X.sum(dim=1, keepdim=True)  # (2, 1, 4)
```

这一条最简单但最容易被忽略。沿轴求和在以下场景中出现：

- **Loss 聚合**：`CrossEntropyLoss` 内部对 batch 维度求均值
- **BatchNorm**：$\mu = \text{mean}(x, \text{dim}=0)$，沿 batch 和空间维度
- **LayerNorm**：$\mu = \text{mean}(x, \text{dim}=-1)$，沿特征维度
- **Linear 梯度推导**：$\partial L / \partial b = \sum_i (\partial L / \partial Y)_{i,:}$（沿 batch 求和）

> 这六种运算贯穿全文。带着它们往下读——每个算子的公式和代码都会反复用到。如果你在某个地方看到 `@` 或 `.sum(dim=-1)`，知道它在干什么，就不会卡住。

### 2.2 nn.Linear — 全连接层

这是最基础、最常用的算子。任何一个深度网络几乎都含有 Linear 层。

**前向公式**：

$$\mathbf{y} = \mathbf{x}\mathbf{W}^T + \mathbf{b}$$

其中 $\mathbf{x} \in \mathbb{R}^{d_{\text{in}}}$，$\mathbf{W} \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}}$，$\mathbf{b} \in \mathbb{R}^{d_{\text{out}}}$。

注意这里写的是 $\mathbf{W}^T$ 而不是 $\mathbf{W}$——这和 PyTorch 源码一致：PyTorch 内部存的是 `(d_out, d_in)` 形状的权重矩阵，前向时做 `x @ W.T + b`。

对于 batch 数据（batch_size = n）：

$$\mathbf{Y} = \mathbf{X}\mathbf{W}^T + \mathbf{b}, \quad \mathbf{X} \in \mathbb{R}^{n \times d_{\text{in}}}, \quad \mathbf{Y} \in \mathbb{R}^{n \times d_{\text{out}}}$$

**参数**：

| 参数 | 形状 | 数量 |
|------|------|------|
| `weight` ($\mathbf{W}$) | `(out_features, in_features)` | `out_features × in_features` |
| `bias` ($\mathbf{b}$) | `(out_features,)` | `out_features` |

例如，`nn.Linear(512, 256)` 有 $512 \times 256 + 256 = 131,328$ 个参数。

**梯度推导**：

设下游传回的梯度为 $\frac{\partial \mathcal{L}}{\partial \mathbf{Y}} \in \mathbb{R}^{n \times d_{\text{out}}}$（每个输出元素对 loss 的影响），则：

$$\frac{\partial \mathcal{L}}{\partial \mathbf{W}} = \left(\frac{\partial \mathcal{L}}{\partial \mathbf{Y}}\right)^T \mathbf{X} \quad \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}}$$

$$\frac{\partial \mathcal{L}}{\partial \mathbf{b}} = \sum_{i=1}^{n} \frac{\partial \mathcal{L}}{\partial \mathbf{Y}_{i,:}} \quad \in \mathbb{R}^{d_{\text{out}}}$$

$$\frac{\partial \mathcal{L}}{\partial \mathbf{X}} = \frac{\partial \mathcal{L}}{\partial \mathbf{Y}} \mathbf{W} \quad \in \mathbb{R}^{n \times d_{\text{in}}}$$

这三行的含义分别是：
- **对 W 的梯度**：外积——输出通道的误差 × 输入值
- **对 b 的梯度**：沿 batch 维度求和——每个输出神经元收到多少"总误差"
- **对 X 的梯度**：将误差投影回输入空间——以便继续向前传播

PyTorch 中的实现位于 `torch.nn.functional.linear`，它调用了 C++/CUDA 后端来高效计算这些矩阵乘法。

> **Linear 是最能让你"看见"梯度的算子**——梯度公式干净，且与矩阵乘法的对称性完全对应。理解 Linear 的梯度，你就理解了反向传播的核心。

**初始化的讲究**：

```python
# PyTorch 默认初始化（Kaiming Uniform）
layer = nn.Linear(512, 256)
# weight: U(-sqrt(k), sqrt(k)), k = 1/in_features
# bias: U(-sqrt(k), sqrt(k))

# 实践中常用显式初始化
nn.init.xavier_uniform_(layer.weight)    # 适用于 tanh/sigmoid
nn.init.kaiming_uniform_(layer.weight)   # 适用于 ReLU 系列
nn.init.normal_(layer.weight, std=0.02)  # GPT-2 风格
```

### 2.3 nn.Conv2d — 卷积层

卷积是视觉模型的核心。理解它的关键是搞清楚**维度的角色**。

**前向公式**（忽略 batch 和通道，单输入单输出）：

$$\mathbf{y}[h, w] = \sum_{i=1}^{k_h} \sum_{j=1}^{k_w} \mathbf{W}[i, j] \cdot \mathbf{x}[h+i-1, w+j-1] + b$$

batch 情况下（同时处理 n 张图），输入形状为 $(n, C_{\text{in}}, H, W)$，输出形状为 $(n, C_{\text{out}}, H_{\text{out}}, W_{\text{out}})$：

$$H_{\text{out}} = \left\lfloor \frac{H + 2P - K}{S} \right\rfloor + 1$$

其中 $P$ 是 padding，$K$ 是 kernel size，$S$ 是 stride。

**参数**：

| 参数 | 形状 | 数量 |
|------|------|------|
| `weight` ($\mathbf{W}$) | `(out_channels, in_channels, kH, kW)` | `out_ch × in_ch × kH × kW` |
| `bias` (if bias=True) | `(out_channels,)` | `out_channels` |

例如 `nn.Conv2d(3, 64, 3, padding=1)`：$64 \times 3 \times 3 \times 3 + 64 = 1,792$ 参数。

**梯度**：卷积本质是线性运算（加权求和），所以它的反向传播是**转置卷积**（transposed convolution）。具体来说：

$$\frac{\partial \mathcal{L}}{\partial \mathbf{W}} = \text{conv2d}\bigl({\mathbf{X}}_{\text{input}},\; \frac{\partial \mathcal{L}}{\partial \mathbf{Y}},\; \text{groups}=\dots\bigr)$$

$$\frac{\partial \mathcal{L}}{\partial \mathbf{X}} = \text{conv\_transpose2d}\bigl(\frac{\partial \mathcal{L}}{\partial \mathbf{Y}},\; \mathbf{W}\bigr)$$

不用记住公式，关键是直觉：**Conv2d 的前向是从 input 中提取特征，反向是把输出误差"反卷积"回输入形状**。这个对称性是卷积网络能用 SGD 端到端训练的基础。

```python
# 最常用的卷积配置
conv = nn.Conv2d(
    in_channels=3,      # RGB
    out_channels=64,    # 输出 64 个特征图
    kernel_size=3,      # 3×3 核
    stride=1,           # 步长 1
    padding=1,          # 外圈填充 1（保持空间尺寸不变）
)
# 输入 (B, 3, 32, 32) → 输出 (B, 64, 32, 32)
```

### 2.4 BatchNorm2d — 批归一化

> Ioffe & Szegedy, *Batch Normalization*, 2015

BatchNorm 解决了深层网络训练中的"内部协变量偏移"问题——每一层的输入分布在训练中不断变化，前面层的一点小变化被后面层层放大，导致训练不稳定。

**前向公式**（对每个通道独立操作）：

$$\mu_c = \frac{1}{m} \sum_{i=1}^{m} x_{i,c}, \quad \sigma_c^2 = \frac{1}{m} \sum_{i=1}^{m} (x_{i,c} - \mu_c)^2$$

$$\hat{x}_{i,c} = \frac{x_{i,c} - \mu_c}{\sqrt{\sigma_c^2 + \epsilon}}$$

$$y_{i,c} = \gamma_c \cdot \hat{x}_{i,c} + \beta_c$$

其中 $m = n \times H \times W$（batch 中所有像素的总数）。关键细节：$\mu_c$ 和 $\sigma_c^2$ 是在 **batch 维度** 上统计的，每个通道独立。

**参数**：

| 参数 | 形状 | 含义 |
|------|------|------|
| `weight` ($\gamma$) | `(num_features,)` | 可学习的缩放 |
| `bias` ($\beta$) | `(num_features,)` | 可学习的偏移 |
| `running_mean` | `(num_features,)` | 训练时的指数移动平均（推理时用） |
| `running_var` | `(num_features,)` | 同上 |

**训练 vs 推理**：这是 BatchNorm 最容易被忽视的地方。

- **训练时**：用当前 mini-batch 的均值/方差做归一化，同时更新 `running_mean` / `running_var`
- **推理时**：用 `running_mean` / `running_var`（固定的，不更新）

因此，如果你的推理 batch 和训练 batch 差异很大（比如 batch=1），BatchNorm 的表现会显著下降。这也是为什么 BatchNorm 对 batch size 敏感——小 batch 下的统计量估计不稳定。

**梯度 vs LayerNorm**：BatchNorm 的梯度推导很复杂（涉及 $\mu$ 和 $\sigma$ 也依赖输入），但 PyTorch 通过 `torch.batch_norm` 的 C++/CUDA 后端高效实现了这一切。你不需要手算，但要记住：

- BatchNorm 的梯度有两条路径：一条通过归一化后的 $\hat{x}$，一条通过 $\mu$ 和 $\sigma$（因为 $\mu$ 和 $\sigma$ 也是从输入算出来的）
- 这正是为什么 `model.eval()` 如此重要：它告诉 BatchNorm 切换统计量来源

### 2.5 LayerNorm — 层归一化

> Ba et al., *Layer Normalization*, 2016

LayerNorm 是 Transformer 时代的标配。与 BatchNorm 在 batch 维度做归一化不同，LayerNorm 在**特征维度**上做归一化。

**前向公式**：

$$\mu = \frac{1}{d} \sum_{i=1}^{d} x_i, \quad \sigma^2 = \frac{1}{d} \sum_{i=1}^{d} (x_i - \mu)^2$$

$$\mathbf{y} = \gamma \odot \frac{\mathbf{x} - \mu}{\sqrt{\sigma^2 + \epsilon}} + \beta$$

对每个样本**独立**归一化——统计量在每个样本的特征维度上计算，而不需要跨样本。

**为什么 Transformer 用 LayerNorm 而不是 BatchNorm？**

1. **Batch Size 独立**：序列模型中 batch size 可能很小（长序列 + 大模型），LayerNorm 不需要跨 batch 统计
2. **推理一致性**：训练和推理的行为完全一样（不需要 running statistics）
3. **序列长度不敏感**：每个 token 的特征独立归一化

**RMSNorm**（LLaMA 使用）去掉了 LayerNorm 中的均值中心化：

$$\text{RMSNorm}(\mathbf{x}) = \frac{\mathbf{x}}{\sqrt{\frac{1}{d}\sum x_i^2 + \epsilon}} \odot \gamma$$

省去了计算均值这一步，比 LayerNorm 快约 10-15%。

**参数**：

| 参数 | 形状 | 含义 |
|------|------|------|
| `weight` ($\gamma$) | `(normalized_shape,)` | 可学习缩放 |
| `bias` ($\beta$) | `(normalized_shape,)` | 可学习偏移（可禁用） |

### 2.6 Dropout — 训练时的"健忘"

> Srivastava et al., *Dropout*, 2014

Dropout 的原理极其简单：训练时，以概率 $p$ 将神经元输出设为零；推理时，所有神经元都活跃，但输出乘以 $1-p$ 以保持期望一致。

```python
# 训练时等价于：
mask = torch.bernoulli(torch.full_like(x, 1 - p))  # 0/1 mask
out = x * mask / (1 - p)                             # 缩放以保持期望

# 推理时：
out = x    # 什么都不做
```

除以 $1-p$ 的意义：被保留的神经元的输出期望保持不变。
$$\mathbb{E}[\text{output}] = (1-p) \cdot \frac{x}{1-p} + p \cdot 0 = x$$

**梯度**：Dropout 的梯度非常简单——对保留的神经元，梯度乘以 $1/(1-p)$；对被丢弃的神经元，梯度为零。

**为什么有效？** 解释有很多，最直观的一个：Dropout 相当于训练大量共享参数的子网络，推理时相当于所有子网络的集成。它强制每个神经元不能依赖特定同伴的存在，增强了泛化能力。

Dropout 在现代 Transformer 中已经基本不用（被 LayerNorm/RMSNorm 和足够大的数据量取代），但在 CNN 和小数据集场景中依然有效。

### 2.7 激活函数全家桶

激活函数引入**非线性**。没有激活函数，无论堆多少层 Linear，最终都等价于一个 Linear（因为矩阵乘法的结合性：$\mathbf{x}W_1W_2 = \mathbf{x}(W_1W_2)$）。

**ReLU**（最经典的"默认选择"）：

$$\text{ReLU}(x) = \max(0, x), \quad \frac{d}{dx}\text{ReLU}(x) = \begin{cases} 1 & x > 0 \\ 0 & x \leq 0 \end{cases}$$

优点：梯度要么 1 要么 0，不衰减（缓解梯度消失）。缺点：$x \leq 0$ 时梯度为 0（"死神经元"——一旦一个神经元对所有输入都输出 0，它再也不会被更新）。

```python
# 死神经元的一次性诊断
dead_ratio = (layer_output <= 0).float().mean().item()
if dead_ratio > 0.5:
    print(f"WARNING: {dead_ratio:.1%} neurons are dead!")
```

**GELU**（Transformer 时代的标准选择）：

$$\text{GELU}(x) = x \cdot \Phi(x) \approx 0.5x\left(1 + \tanh\left[\sqrt{2/\pi}(x + 0.044715x^3)\right]\right)$$

其中 $\Phi(x)$ 是标准正态分布的累积分布函数。GELU 是 ReLU 的"平滑版"：它不像 ReLU 那样一刀切，而是在 0 附近有一个平滑的过渡。BERT、GPT 系列都使用 GELU。

$$\frac{d}{dx}\text{GELU}(x) \approx \Phi(x) + x \cdot \phi(x)$$

**SiLU / Swish**（LLaMA 系列使用）：

$$\text{SiLU}(x) = x \cdot \sigma(x) = \frac{x}{1 + e^{-x}}$$

$$\frac{d}{dx}\text{SiLU}(x) = \sigma(x) + x \cdot \sigma(x)(1-\sigma(x)) = \sigma(x)(1 + x - x\cdot\sigma(x))$$

SiLU 和 GELU 形状极像，但 SiLU 的实现更简单（只需要 sigmoid 而非正态 CDF）。LLaMA 用 SiLU 配合门控机制（SwiGLU）构建 FFN。

**Sigmoid**（已退出主流，但在门控/输出层仍有用）：

$$\sigma(x) = \frac{1}{1 + e^{-x}}, \quad \frac{d\sigma}{dx} = \sigma(x)(1 - \sigma(x))$$

**Tanh**（RNN 时代的回忆）：

$$\tanh(x) = \frac{e^x - e^{-x}}{e^x + e^{-x}}, \quad \frac{d}{dx}\tanh(x) = 1 - \tanh^2(x)$$

**选用速查**：

| 场景 | 推荐激活函数 | 原因 |
|------|-------------|------|
| CNN / MLP 隐层 | ReLU / GELU | 简单有效 |
| Transformer 隐层 | GELU / SiLU | 平滑性对注意力有益 |
| 门控机制（GLU 变体） | SiLU | SwiGLU 标配 |
| 二分类输出层 | Sigmoid | 输出 [0,1] 概率 |
| 多分类输出层 | Softmax | 输出概率分布 |
| RNN/LSTM | Tanh | 历史惯性 |

### 2.8 nn.Embedding — 查表层

**前向**：取 `self.weight` 矩阵的第 `input_ids` 行。

```python
# nn.Embedding 的本质（从矩阵乘法视角）
def embedding_lookup(weight, input_ids):
    # weight: (V, d_model)
    # input_ids: (n,) — n 个 token 的整数 ID
    one_hot = F.one_hot(input_ids, num_classes=weight.shape[0]).float()  # (n, V)
    return one_hot @ weight   # (n, d_model)
    # 等价于 weight[input_ids]，但用矩阵乘法来理解
```

**梯度**：只有被查过的行才能收到梯度。你用一个 token "cat"，其它 99999 个 token 的嵌入不变。

```python
embed = nn.Embedding(10000, 512)
x = torch.tensor([1, 42, 999])  # 只查这 3 行
y = embed(x).sum()
y.backward()
print((embed.weight.grad.sum(dim=1) != 0).sum())  # → 3（只有 3 行有梯度）
```

### 2.9 Multi-Head Attention — 用已有算子搭一个 MHA

MHA 是 Transformer 的核心。搞懂它的架构设计和搞懂它**在代码层面是什么**是两回事。这一节的目标是：用本章已经讲过的 `nn.Linear`，从零写出一个 MHA。

#### 2.9.1 MHA 的本质拆解

从工程视角看，MHA 的流程是五个步骤：

1. **投影**：输入 `x` 分别经过 `Linear_Q`、`Linear_K`、`Linear_V`，得到 Q、K、V 三个矩阵，每个形状为 `(batch, seq_len, d_model)`
2. **拆头**：把 `d_model` 拆成 `h × d_k`，得到 `(batch, h, seq_len, d_k)` —— 每个头独立拥有自己的子空间
3. **计算注意力**：`softmax(Q @ K.T / √d_k) @ V`，在每个头内独立完成
4. **拼回头**：把所有头的输出沿特征维拼接，恢复为 `(batch, seq_len, d_model)`
5. **输出投影**：经过 `Linear_O` 做最后一次线性变换

四个关键数字：

| 符号 | 含义 | 示例（LLaMA-7B） |
|------|------|------------------|
| `d_model` | 模型的隐藏维度 | 4096 |
| `h` | 注意力头数 | 32 |
| `d_k` | 每个头的维度 = d_model / h | 128 |
| `d_v` | value 的维度（通常 = d_k） | 128 |

所以 MHA 里所有的"学习"都在这四组 Linear 的权重矩阵里——没有任何其他可学习参数。注意力本身（QK^T → softmax → 加权 V）是**纯数学运算，不含任何参数**。

#### 2.9.2 代码实现

下面是标准的实现——用一个大 `nn.Linear(d_model, d_model)` 做 Q/K/V 投影，然后 reshape 拆成多头。这是 Transformer 论文和所有主流框架（PyTorch、HuggingFace）的通用做法：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class MultiHeadAttention(nn.Module):
    """
    用 nn.Linear + 标准矩阵运算实现 Multi-Head Attention。

    输入: (batch, seq_len, d_model)
    输出: (batch, seq_len, d_model)
    """

    def __init__(self, d_model=512, num_heads=8, dropout=0.0):
        super().__init__()
        assert d_model % num_heads == 0, "d_model 必须能被 num_heads 整除"
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        # Q、K、V 的投影矩阵 —— 三个 nn.Linear
        # 注意：这里的 weight 形状是 (d_model, d_model)，不是按头拆分
        # 等价于把 h 个 (d_model, d_k) 小矩阵并排拼成一个大矩阵
        self.W_Q = nn.Linear(d_model, d_model, bias=False)
        self.W_K = nn.Linear(d_model, d_model, bias=False)
        self.W_V = nn.Linear(d_model, d_model, bias=False)

        # 输出投影矩阵
        self.W_O = nn.Linear(d_model, d_model, bias=False)

        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        """
        x: (batch, seq_len, d_model)
        mask: (batch, seq_len, seq_len), True 表示"不能看"的位置
        返回: (batch, seq_len, d_model)
        """
        B, N, D = x.shape
        H, d_k = self.num_heads, self.d_k

        # ─── 步骤 1：投影 ───
        # 每个都是一次 x @ W.T（回忆 §2.2：nn.Linear 的 forward）
        Q = self.W_Q(x)         # (B, N, D)
        K = self.W_K(x)         # (B, N, D)
        V = self.W_V(x)         # (B, N, D)

        # ─── 步骤 2：拆成多头 ───
        # 把 d_model 拆成 h × d_k，然后把 h 移到 batch 维度之前
        # view:  (B, N, D)       → (B, N, H, d_k)
        # permute → (B, H, N, d_k)
        Q = Q.view(B, N, H, d_k).transpose(1, 2)   # (B, H, N, d_k)
        K = K.view(B, N, H, d_k).transpose(1, 2)   # (B, H, N, d_k)
        V = V.view(B, N, H, d_k).transpose(1, 2)   # (B, H, N, d_k)

        # ─── 步骤 3：计算注意力 ───
        # Q @ K^T: (B, H, N, d_k) × (B, H, d_k, N) → (B, H, N, N)
        # 结果的 [b, h, i, j] 表示 batch b 的第 h 个头中，位置 i 对位置 j 的注意力分数
        attn_scores = (Q @ K.transpose(-2, -1)) / math.sqrt(d_k)

        # Causal Mask（自回归模型用）：位置 i 不能看到位置 > i
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask, float('-inf'))

        # Softmax：把分数变成概率
        attn_weights = F.softmax(attn_scores, dim=-1)     # (B, H, N, N)
        attn_weights = self.dropout(attn_weights)

        # ─── 步骤 4：加权求和 ───
        # attn @ V: (B, H, N, N) × (B, H, N, d_k) → (B, H, N, d_k)
        out = attn_weights @ V

        # ─── 步骤 5：拼回头 + 输出投影 ───
        # transpose: (B, H, N, d_k) → (B, N, H, d_k)
        # reshape:   (B, N, H, d_k) → (B, N, D)
        out = out.transpose(1, 2).contiguous().view(B, N, D)

        out = self.W_O(out)    # 最后一次 Linear
        return out
```

#### 2.9.3 逐步骤拆解

对照上面的代码，每一步只用到了本章讲过的算子：

```
步骤 1 (投影)      nn.Linear × 3       §2.2
步骤 2 (拆头)      .view() + .transpose() 纯形状变换（§2.1 的 (3)(4)）
步骤 3 (注意力分数) 矩阵乘法 @             §2.1 的 (1)
                  / sqrt(d_k)           §2.1 的 (5) broadcast
                  F.softmax()           §2.7 的激活函数
步骤 4 (加权求和)   矩阵乘法 @             同上
步骤 5 (拼回)      .transpose() + .view() 纯形状变换（§2.1 的 (3)(4)）
                  nn.Linear × 1        §2.2
```

整个 MHA 里**只有四组 `nn.Linear` 的权重是可学习的**。其余操作——reshape、transpose、矩阵乘法、softmax——全是没有参数的计算。

#### 2.9.4 两个值得注意的细节

**(1) 为什么 Q/K/V 的 Linear 用 `(d_model, d_model)` 而不是直接按头拆分？**

工程上用一个大的 `nn.Linear(d_model, d_model)` + reshape 比用 $h$ 个小的 `nn.Linear(d_model, d_k)` 更高效。原因是 GPU 对大矩阵乘法做了极致优化（cuBLAS），一次大矩阵乘法的速度远快于 $h$ 次小矩阵乘法的速度。reshape 本身是零开销的——它只改张量的 shape 元数据，不移动任何数据。

**(2) `bias=False` 的意义**

四个 Linear 层都设了 `bias=False`。这是 Transformer 的惯例——在实际效果上没有明显损失，且省掉了 `4 × d_model` 个参数（对于 LLaMA-7B 的 4096 维，就是 4×4096 ≈ 16K 参数）。论文里常见的写法甚至直接省略命名——只提 QKV 的权重矩阵。

#### 2.9.5 验证：因果 mask 的正确性

```python
# 构建 causal mask：位置 i 不能看到位置 j (j > i)
seq_len = 4
causal_mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
print(causal_mask)
# tensor([[False,  True,  True,  True],    ← 位置 0 只能看自己
#         [False, False,  True,  True],    ← 位置 1 能看 0,1
#         [False, False, False,  True],    ← 位置 2 能看 0,1,2
#         [False, False, False, False]])   ← 位置 3 能看全部

# 测试
mha = MultiHeadAttention(d_model=256, num_heads=8)
x = torch.randn(2, 4, 256)                        # batch=2, seq=4
out = mha(x, mask=causal_mask.unsqueeze(0))        # 加 mask
print(out.shape)                                    # (2, 4, 256) ✓
```

#### 2.9.6 一句话总结

> **MHA = 把输入过四组 `nn.Linear`，中间用 `softmax(QK^T/√d_k) @ V` 对各 token 的信息做了一次重分配。** 理解这一点后，MQA/GQA/MLA 不过是改变 QK 共享方式的工程优化——核心框架没有变。

---

## 第三章：损失函数 — 告诉模型什么是"对"

损失函数将"模型输出"和"正确答案"之间的差距压缩成一个标量。这个标量就是 `.backward()` 的起点。

### 3.1 CrossEntropyLoss — 分类任务的默认选择

这是最常用的损失函数，值得深入理解它的每一步。

**前向**（以单样本为例，模型输出 3 类 logits）：

> **Logits** 是模型最后一层输出的原始分数——未经 softmax 或 sigmoid 归一化的实数。它们可以是任意实数（正/负/零），之间的大小关系反映模型的相对倾向，但绝对值没有概率意义。"logit" 这个词来自 logistic/log-odds：logits 本质上是对数尺度上的未归一化概率，softmax 只是将它们拉回概率空间。

$$\mathbf{z} = [2.0, 1.0, 0.1] \quad \text{（模型的原始输出，logits）}$$

$$\text{softmax}(\mathbf{z})_i = \frac{e^{z_i}}{\sum_j e^{z_j}} = \frac{e^{z_i}}{e^{2.0} + e^{1.0} + e^{0.1}} = [0.659, 0.242, 0.099]$$

$$L = -\log p_{\text{true class}} = -\log(0.659) = 0.417$$

**PyTorch 的 `CrossEntropyLoss` 是一个组合算子**：它等价于 `LogSoftmax + NLLLoss`。关键是——你传入的是 **原始 logits**，而不是 softmax 之后的概率！PyTorch 内部做 log-softmax，这在数值上更稳定。

```python
# 正确用法
loss_fn = nn.CrossEntropyLoss()
logits = torch.tensor([[2.0, 1.0, 0.1]])   # 原始 logits
target = torch.tensor([0])                   # 正确类别索引
loss = loss_fn(logits, target)               # → 0.417

# 错误用法（绝对不要这样写）
# probs = F.softmax(logits, dim=1)
# loss = loss_fn(probs, target)              # 数值不稳定！
```

**梯度**：CrossEntropyLoss 的梯度有一个非常优雅的形式：

$$\frac{\partial L}{\partial z_i} = p_i - \mathbf{1}\{i = \text{target}\}$$

其中 $p_i = \text{softmax}(z_i)$ 是模型预测的概率。这被称为"softmax 的玻尔兹曼性质"——梯度的方向是"把正确类别的概率推向 1，把错误类别的概率推向 0"。

用一句话记住：**损失对 logit 的梯度 = 模型预测的概率 - 正确答案的 one-hot**。这是整个分类训练的核心机制。

### 3.2 MSELoss — 回归任务的标配

$$\text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2$$

$$\frac{\partial \text{MSE}}{\partial \hat{y}_i} = -\frac{2}{n}(y_i - \hat{y}_i)$$

梯度就是**误差的负数**（乘以常数）——预测大于目标，梯度为负（应该减小）；预测小于目标，梯度为正（应该增大）。

### 3.3 BCEWithLogitsLoss — 二分类专用

$$\text{BCE} = -[y \log \sigma(z) + (1-y) \log(1 - \sigma(z))]$$

和 CrossEntropyLoss 类似，**传入 logits 而非概率**。内部使用 log-sigmoid 以保证数值稳定。

```python
loss_fn = nn.BCEWithLogitsLoss()    # 传入 logits
logits = torch.tensor([2.0])        # 模型的原始输出
target = torch.tensor([1.0])
loss = loss_fn(logits, target)      # 内部：log(sigmoid(2.0)) 的数值稳定版本
```

---

## 第四章：优化器 — 参数更新的艺术

损失函数告诉模型"什么是错"，优化器告诉模型"怎么改"。

### 4.1 SGD — 最原始的更新规则

**无动量 SGD**：

$$\theta \leftarrow \theta - \eta \cdot \nabla_\theta \mathcal{L}$$

```python
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
```

**带动量 SGD**：

$$\mathbf{v}_t = \mu \cdot \mathbf{v}_{t-1} + \nabla_\theta \mathcal{L}$$
$$\theta \leftarrow \theta - \eta \cdot \mathbf{v}_t$$

动量的物理直觉：想象一个小球在损失曲面上滚动。每步不只是看当前位置的梯度，还保留了之前累积的速度。如果连续的梯度指向同一个方向，速度会累积起来（加速下降）；如果方向来回变化，速度会相互抵消（减少抖动）。

```python
optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
```

**Nesterov 动量**（SGD 的"提前看一步"变体）：

$$\mathbf{v}_t = \mu \cdot \mathbf{v}_{t-1} + \nabla_\theta \mathcal{L}(\theta - \eta \cdot \mu \cdot \mathbf{v}_{t-1})$$

区别：Nesterov 动量在计算梯度时，先沿着上一动量方向走半步（θ - η·μ·v），在那个位置算梯度。这相当于"提前看一步"，能更快地感知到损失曲面的弯曲。

```python
optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9, nesterov=True)
```

### 4.2 Adam — 自适应学习率的工业标准

Adam（Adaptive Moment Estimation）结合了两个思想：
1. **动量**（一阶矩）：像 SGD momentum 一样累积梯度方向
2. **自适应学习率**（二阶矩）：对每个参数，用梯度平方的累积量对其梯度的"波动"进行归一化——波动大的参数用小步长，波动小的参数用大步长

$$\mathbf{m}_t = \beta_1 \cdot \mathbf{m}_{t-1} + (1-\beta_1) \cdot \nabla_\theta \mathcal{L} \quad \text{（一阶矩 = 梯度的指数移动平均）}$$

$$\mathbf{v}_t = \beta_2 \cdot \mathbf{v}_{t-1} + (1-\beta_2) \cdot (\nabla_\theta \mathcal{L})^2 \quad \text{（二阶矩 = 梯度平方的指数移动平均）}$$

$$\hat{\mathbf{m}}_t = \frac{\mathbf{m}_t}{1 - \beta_1^t}, \quad \hat{\mathbf{v}}_t = \frac{\mathbf{v}_t}{1 - \beta_2^t} \quad \text{（偏差校正：初始化时矩估计偏向 0）}$$

$$\theta \leftarrow \theta - \eta \cdot \frac{\hat{\mathbf{m}}_t}{\sqrt{\hat{\mathbf{v}}_t} + \epsilon}$$

默认参数 $\beta_1 = 0.9, \beta_2 = 0.999, \epsilon = 10^{-8}$。

```python
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
```

### 4.3 AdamW — 正确的权重衰减

AdamW 是 Adam + **解耦的权重衰减**。区别在于正则化项的位置：

**Adam + L2 正则化**（错误做法，但历史上是这么写的）：
$$\nabla_\theta \mathcal{L}_{\text{L2}} = \nabla_\theta \mathcal{L} + \lambda \theta$$
梯度先被 L2 项污染，再进 Adam 的自适应机制——权重衰减的强度被每个参数的自适应学习率扭曲了。

**AdamW**（正确做法，Loshchilov & Hutter 2019）：
$$\theta \leftarrow \theta - \eta \cdot \left(\frac{\hat{\mathbf{m}}_t}{\sqrt{\hat{\mathbf{v}}_t} + \epsilon} + \lambda \theta\right)$$

权重衰减直接作用在参数上，与自适应学习率解耦。效果：更好的泛化，特别是在 Transformer 训练中。

```python
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
```

**选型建议**：

| 场景 | 优化器 | 典型 lr | 备注 |
|------|--------|--------|------|
| Transformer 预训练 | AdamW | 1e-4 → 1e-3 | weight_decay=0.1 |
| CNN 图像分类 | SGD + momentum | 0.1 | 配合 step decay |
| 微调 LLM（LoRA） | AdamW | 1e-4 → 5e-5 | weight_decay=0.01 |
| GAN 训练 | Adam | 2e-4 (β1=0.5) | 低动量防止震荡 |
| 快速原型 | Adam | 1e-3 | 默认参数即可 |

### 4.4 学习率调度

好的学习率调度能让收敛速度快 2-3 倍。最常用的几种：

```python
# [1] Cosine Annealing — Transformer 训练标配
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=1000)
# lr 从初始值平滑降低到 0，形状像余弦曲线

# [2] Linear Warmup + Cosine Decay — LLM 训练标配
import math
def get_lr(step, warmup_steps, max_steps, max_lr):
    if step < warmup_steps:
        return max_lr * step / warmup_steps      # 线性增长
    else:
        progress = (step - warmup_steps) / (max_steps - warmup_steps)
        return max_lr * 0.5 * (1 + math.cos(math.pi * progress))
# Warmup 是必需的：在训练初期，模型权重是随机的，梯度方向混乱。
# 先用小学习率让优化器（Adam）建立可靠的动量/二阶矩估计，
# 再逐步加速，避免初始化阶段的不稳定。

# [3] Step Decay — 老派 CNN 训练标配
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)
# 每 30 个 epoch lr 降为 1/10
```

**PyTorch 中 scheduler 的调用时机**（一个常见的坑）：

```python
# 正确：scheduler.step() 在 optimizer.step() 之后
for epoch in range(num_epochs):
    for batch in dataloader:
        loss = model(batch)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    scheduler.step()   # ← 每个 epoch 结束调用，不是每个 batch!
```

---

## 第五章：训练循环 — 把一切串起来

### 5.1 最简训练循环（5 行核心代码）

如果你只能记住 5 行代码，就记住这些：

```python
for x, y in dataloader:                    # 1. 取一个 batch
    optimizer.zero_grad()                  # 2. 上一次的梯度清空
    loss = loss_fn(model(x), y)            # 3. 前向传播计算损失
    loss.backward()                        # 4. 反向传播计算梯度
    optimizer.step()                       # 5. 根据梯度更新参数
```

这 5 行的执行流程：

1. `model(x)` 做前向传播，输出 logits
2. `loss_fn(logits, y)` 算出损失标量
3. `loss.backward()` 沿着计算图反向传播，把每个参数的 `.grad` 填好
4. `optimizer.step()` 用 `.grad` 按优化器规则更新参数（如 SGD：`θ -= lr * θ.grad`）

### 5.2 完整的训练/验证框架

实际项目中你需要的框架比上面 5 行多一些——加上验证循环、metric 追踪、checkpoint 保存：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

def train_one_epoch(model, dataloader, loss_fn, optimizer, device):
    """训练一个 epoch，返回平均损失和准确率"""
    model.train()                    # ← 关键！开启训练模式（影响 Dropout, BatchNorm）
    total_loss, correct, total = 0.0, 0, 0

    for x, y in dataloader:
        x, y = x.to(device), y.to(device)

        # 核心 5 行
        optimizer.zero_grad()
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()

        # 统计
        total_loss += loss.item() * x.size(0)
        correct += (logits.argmax(dim=1) == y).sum().item()
        total += x.size(0)

    return total_loss / total, correct / total


@torch.no_grad()                    # ← 关键！禁用梯度，节省显存
def evaluate(model, dataloader, loss_fn, device):
    """验证/测试，不更新参数"""
    model.eval()                     # ← 关键！开启评估模式
    total_loss, correct, total = 0.0, 0, 0

    for x, y in dataloader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        loss = loss_fn(logits, y)

        total_loss += loss.item() * x.size(0)
        correct += (logits.argmax(dim=1) == y).sum().item()
        total += x.size(0)

    return total_loss / total, correct / total


def train(model, train_loader, val_loader, loss_fn, optimizer, scheduler,
          num_epochs, device, save_path='best_model.pt'):
    """完整训练流程"""
    best_val_acc = 0.0

    for epoch in range(num_epochs):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, loss_fn, optimizer, device
        )
        val_loss, val_acc = evaluate(model, val_loader, loss_fn, device)
        scheduler.step()  # 每个 epoch 更新学习率

        print(f"Epoch {epoch+1:3d}/{num_epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), save_path)  # 保存最佳模型

    print(f"Best val acc: {best_val_acc:.4f}")
    return model
```

**`model.train()` vs `model.eval()` 的区别**：

| 行为 | `model.train()` | `model.eval()` |
|------|----------------|----------------|
| Dropout | 按概率丢弃神经元 | 不丢弃（全部激活） |
| BatchNorm | 用当前 batch 的 μ/σ | 用 running_mean / running_var |

---

## 第六章：示例一 — 用 MLP 串起所有基础算子（~40 行）

一个 MLP 分类器包含了 Linear + ReLU + CrossEntropyLoss + SGD 这四个核心元素。40 行代码，但每一行都值得理解：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

# ============ 1. 数据（合成数据） ============
torch.manual_seed(42)
n_samples = 1000
X = torch.randn(n_samples, 20)               # 1000 个样本，每个 20 维
y = (X[:, 0] + X[:, 1] > 0).long()           # 二分类：前两维之和 > 0 为正类

dataset = TensorDataset(X, y)
train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

# ============ 2. 模型定义 ============
class SimpleMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(20, 64)          # 20 → 64, 参数: 20×64+64 = 1344
        self.fc2 = nn.Linear(64, 32)          # 64 → 32, 参数: 64×32+32 = 2080
        self.fc3 = nn.Linear(32, 2)           # 32 → 2,  参数: 32×2+2   = 66
        # 总参数: 1344 + 2080 + 66 = 3490

    def forward(self, x):
        x = F.relu(self.fc1(x))              # (32, 20) → (32, 64)
        x = F.relu(self.fc2(x))              # (32, 64) → (32, 32)
        x = self.fc3(x)                       # (32, 32) → (32, 2) — logits
        return x

model = SimpleMLP()
print(f"参数总量: {sum(p.numel() for p in model.parameters()):,}")  # 3,490

# ============ 3. 损失函数 & 优化器 ============
loss_fn = nn.CrossEntropyLoss()                # softmax + NLLLoss
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

# ============ 4. 训练 ============
for epoch in range(50):
    model.train()
    total_loss, correct = 0.0, 0
    for x_batch, y_batch in train_loader:
        optimizer.zero_grad()                  # 清零梯度
        logits = model(x_batch)                # 前向
        loss = loss_fn(logits, y_batch)        # 计算损失
        loss.backward()                        # 反向传播
        optimizer.step()                       # 参数更新

        total_loss += loss.item()
        correct += (logits.argmax(1) == y_batch).sum().item()

    acc = correct / n_samples
    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch+1:3d} | Loss: {total_loss/len(train_loader):.4f} | Acc: {acc:.4f}")
```

**这个示例串起了什么？**

| 组件 | 出现位置 | 作用 |
|------|---------|------|
| `nn.Linear` | fc1, fc2, fc3 | 全连接层，存储权重矩阵 W 和偏置 b |
| `F.relu` | forward 中 | 激活函数，引入非线性 |
| `nn.CrossEntropyLoss` | loss_fn | 计算预测与标签的差距，产生标量 loss |
| `SGD` | optimizer | 用 loss 的梯度更新参数 |
| `zero_grad / backward / step` | 训练循环 | 梯度清零 → 计算 → 更新的标准流程 |

---

## 第七章：示例二 — CNN on MNIST（加入卷积与归一化，~60 行）

在 MLP 的基础上，CNN 示例新引入了 `Conv2d`、`BatchNorm2d`、`MaxPool2d`、`Dropout` 和 `Adam`：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# ============ 1. 数据准备 ============
transform = transforms.Compose([
    transforms.ToTensor(),                     # PIL Image → Tensor, 自动 [0,1]
    transforms.Normalize((0.1307,), (0.3081,)) # MNIST 的 μ 和 σ
])

train_data = datasets.MNIST('./data', train=True, download=True, transform=transform)
test_data  = datasets.MNIST('./data', train=False, transform=transform)
train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
test_loader  = DataLoader(test_data,  batch_size=64, shuffle=False)

# ============ 2. 模型定义 ============
class SimpleCNN(nn.Module):
    """
    输入: (B, 1, 28, 28)
    经过两层卷积 + 两层全连接
    输出: (B, 10) — 10 个数字类别的 logits
    """
    def __init__(self, num_classes=10):
        super().__init__()
        # Block 1: Conv → BN → ReLU → Pool
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        # 参数: 32 × 1 × 3 × 3 + 32 = 320
        self.bn1   = nn.BatchNorm2d(32)
        # 参数: 32(γ) + 32(β) = 64

        # Block 2: Conv → BN → ReLU → Pool
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        # 参数: 64 × 32 × 3 × 3 + 64 = 18,496
        self.bn2   = nn.BatchNorm2d(64)
        # 参数: 64 + 64 = 128

        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        # 无参数！MaxPool2d 不存任何权重

        self.dropout = nn.Dropout(0.25)
        # 无参数！Dropout 只在训练时生效

        # 全连接分类器
        # 经过两次 2×2 pool 后，28×28 → 14×14 → 7×7
        self.fc1 = nn.Linear(64 * 7 * 7, 128)  # 参数: 3136×128+128 = 401,536
        self.fc2 = nn.Linear(128, num_classes)   # 参数: 128×10+10 = 1,290

    def forward(self, x):
        # Block 1
        x = self.conv1(x)          # (B,1,28,28) → (B,32,28,28)
        x = self.bn1(x)            # BatchNorm
        x = F.relu(x)              # 激活
        x = self.pool(x)           # (B,32,28,28) → (B,32,14,14)

        # Block 2
        x = self.conv2(x)          # (B,32,14,14) → (B,64,14,14)
        x = self.bn2(x)            # BatchNorm
        x = F.relu(x)              # 激活
        x = self.pool(x)           # (B,64,14,14) → (B,64,7,7)

        x = self.dropout(x)

        # Flatten → FC
        x = x.view(x.size(0), -1)  # (B,64,7,7) → (B, 3136)
        x = F.relu(self.fc1(x))    # → (B, 128)
        x = self.dropout(x)
        x = self.fc2(x)            # → (B, 10) logits
        return x

model = SimpleCNN()
print(f"参数总量: {sum(p.numel() for p in model.parameters()):,}")

# 验证参数形状
for name, param in model.named_parameters():
    print(f"  {name:20s} shape={str(param.shape):20s} numel={param.numel():,}")

# ============ 3. 损失函数 & 优化器 ============
loss_fn   = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.7)

# ============ 4. 判断设备 ============
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

# ============ 5. 训练 ============
for epoch in range(10):
    # ---- 训练 ----
    model.train()
    train_loss, train_correct = 0.0, 0
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)

        optimizer.zero_grad()
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()

        train_loss += loss.item() * x.size(0)
        train_correct += (logits.argmax(1) == y).sum().item()

    scheduler.step()

    # ---- 验证 ----
    model.eval()
    val_loss, val_correct = 0.0, 0
    with torch.no_grad():
        for x, y in test_loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            loss = loss_fn(logits, y)
            val_loss += loss.item() * x.size(0)
            val_correct += (logits.argmax(1) == y).sum().item()

    n_train, n_val = len(train_data), len(test_data)
    print(f"Epoch {epoch+1:2d} | "
          f"Train Loss: {train_loss/n_train:.4f} Acc: {train_correct/n_train:.4f} | "
          f"Val Loss: {val_loss/n_val:.4f} Acc: {val_correct/n_val:.4f}")

# 预期：10 个 epoch 后，测试准确率约 98-99%
```

**这个 CNN 示例串起了什么？**（对比 MLP 新增的用 ★ 标记）

| 组件 | 出现位置 | 参数形状 | 作用 |
|------|---------|---------|------|
| `nn.Conv2d` ★ | conv1, conv2 | `(C_out, C_in, kH, kW)` | 空间局部特征提取 |
| `nn.BatchNorm2d` ★ | bn1, bn2 | `(C,)` 各一对 γ,β | 稳定训练、加速收敛 |
| `nn.MaxPool2d` ★ | pool | 无参数 | 降采样，增大感受野 |
| `nn.Dropout` ★ | dropout | 无参数 | 正则化，防过拟合 |
| `F.relu` | forward | 无参数 | 非线性 |
| `nn.Linear` | fc1, fc2 | `(d_out, d_in)` | 全局分类器 |
| `nn.CrossEntropyLoss` | loss_fn | 无参数 | 多分类损失 |
| `Adam` ★ | optimizer | — | 自适应学习率优化 |
| `StepLR` ★ | scheduler | — | 学习率衰减 |
| `.to(device)` ★ | — | — | GPU/CPU 设备管理 |
| `model.train()/eval()` | 训练/验证 | — | 切换 Dropout/BN 行为 |

---

## 第八章：实用调试技巧

### 8.1 过拟合一个小 batch

在开始正式训练前，先确认你的流程是通的——拿一个小 batch（比如 8 个样本），过拟合到接近 100% 准确率：

```python
def overfit_check(model, x_batch, y_batch):
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    for step in range(200):
        opt.zero_grad()
        loss = F.cross_entropy(model(x_batch), y_batch)
        loss.backward()
        opt.step()
        if step % 50 == 0:
            acc = (model(x_batch).argmax(1) == y_batch).float().mean()
            print(f"  Step {step:3d}: loss={loss.item():.4f}, acc={acc:.4f}")
    return loss.item()

# 测试：cnn 能在 200 步内完全记住 8 张图
x_test, y_test = next(iter(train_loader))
x_test, y_test = x_test[:8].to(device), y_test[:8].to(device)
overfit_check(SimpleCNN().to(device), x_test, y_test)
```

**如果过拟合测试不过**：模型能力不够（层数太少/宽度不够）或者有 bug。

**如果过拟合测试过了但正式训练不好**：正则化太强、数据预处理有问题、学习率不合适。

### 8.2 梯度检查

怀疑某个层的梯度有问题？手动验证：

```python
def check_gradient(layer, input_tensor):
    """数值梯度 vs 自动梯度"""
    layer.zero_grad()
    out = layer(input_tensor)
    loss = out.sum()
    loss.backward()

    # 取权重的第一个元素，用有限差分验证
    w = layer.weight.data[0, 0].clone()
    eps = 1e-6

    layer.weight.data[0, 0] = w + eps
    loss_plus = layer(input_tensor).sum().item()

    layer.weight.data[0, 0] = w - eps
    loss_minus = layer(input_tensor).sum().item()

    layer.weight.data[0, 0] = w    # 恢复

    grad_numerical = (loss_plus - loss_minus) / (2 * eps)
    grad_autograd  = layer.weight.grad[0, 0].item()

    rel_err = abs(grad_numerical - grad_autograd) / (abs(grad_numerical) + abs(grad_autograd) + 1e-8)
    print(f"Numerical: {grad_numerical:.8f}, Autograd: {grad_autograd:.8f}, "
          f"RelErr: {rel_err:.2e} {'✓' if rel_err < 1e-4 else '✗ FAIL'}")
```

相对误差应该在 $10^{-4}$ 以内。如果不在——说明反传实现有 bug。

### 8.3 常见问题速查表

| 症状 | 可能原因 | 检查方法 |
|------|---------|---------|
| Loss 不下降 | 学习率太小/太大 | 尝试 `lr=1e-3`, `1e-4`, `1e-5` |
| Loss = NaN | 梯度爆炸 / lr 太大 | 加梯度裁剪 `clip_grad_norm_(model.parameters(), 1.0)` |
| 训练 loss 降但 val loss 不降 | 过拟合 | 加 Dropout / weight_decay / 数据增强 |
| val loss 比 train loss 还低 | `model.train()` 忘切 `model.eval()` | BatchNorm 用 batch μ 而非 running μ |
| 梯度全是 0 | 某层挂了 / 数据不对 | `print([p.grad.norm() for p in model.parameters()])` |
| 显存 OOM | batch 太大 / 模型太大 | 梯度累积 / gradient checkpointing / 减小 batch |
| 准确率不涨但 loss 在降 | 标签映射错了 | 打印几个预测和标签对比 |

### 8.4 打印模型统计信息的工具函数

```python
def model_summary(model, input_shape):
    """打印每一层的输出形状和参数量"""
    from torchsummary import summary  # pip install torchsummary
    summary(model, input_shape)

# 或手动版本（不需要额外库）
def print_param_count(model):
    """打印每个模块的参数量"""
    total = 0
    for name, module in model.named_children():
        n = sum(p.numel() for p in module.parameters())
        total += n
        print(f"  {name:20s}: {n:>10,} params")
    print(f"  {'TOTAL':20s}: {total:>10,} params")

print_param_count(SimpleCNN())
```

输出示例：
```
  conv1               :        320 params
  bn1                 :         64 params
  conv2               :     18,496 params
  bn2                 :        128 params
  pool                :          0 params
  dropout             :          0 params
  fc1                 :    401,536 params  ← 全连接层占大头
  fc2                 :      1,290 params
  TOTAL               :    421,834 params
```

### 8.5 显存分析

```python
def print_gpu_memory():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**2
        reserved  = torch.cuda.memory_reserved()  / 1024**2
        print(f"GPU Memory: {allocated:.1f} MB allocated, {reserved:.1f} MB reserved")

# 在训练循环中检查显存使用
print_gpu_memory()           # 训练前
x = x.to(device)
print_gpu_memory()           # 数据加载后
logits = model(x)
print_gpu_memory()           # 前向传播后
loss.backward()
print_gpu_memory()           # 反向传播后（梯度会额外占用显存）
```

---

## 第九章：梯度裁剪与 distributed 基础

### 9.1 梯度裁剪 — 防止梯度爆炸

当你的 loss 突然变成 NaN 时，第一个操作是加梯度裁剪：

```python
# 在 loss.backward() 之后，optimizer.step() 之前：
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

它会计算所有参数梯度的范数 $\|\mathbf{g}\|$，如果超过 `max_norm`，就按比例缩放：$\mathbf{g} \leftarrow \mathbf{g} \cdot \frac{\text{max\_norm}}{\|\mathbf{g}\|}$。

### 9.2 Gradient Checkpointing — 用计算换显存

训练大模型时的必备技巧：不存储所有中间激活值，在反向传播时重新计算需要的部分：

```python
from torch.utils.checkpoint import checkpoint

# 在 forward 中用 checkpoint 包裹计算量大的模块
x = checkpoint(self.conv_block, x, use_reentrant=False)
```

显存节省约 40-60%，代价是约 20% 的训练时间增加（多算一次前向）。

### 9.3 混合精度训练 (AMP)

用 FP16 做前向/反向、FP32 做参数更新，速度提升约 1.5-2×，显存节省约 30%：

```python
# PyTorch 2.4+ 统一 API（推荐）
scaler = torch.amp.GradScaler('cuda')          # 如果是旧版：torch.cuda.amp.GradScaler()

for x, y in dataloader:
    optimizer.zero_grad()

    with torch.amp.autocast('cuda'):            # 旧版：torch.cuda.amp.autocast()
        logits = model(x)
        loss = loss_fn(logits, y)

    scaler.scale(loss).backward()               # 放大 loss，防止 FP16 梯度下溢
    scaler.step(optimizer)                      # 更新参数（自动跳过 inf/NaN 的步）
    scaler.update()                             # 动态调整缩放因子
```

关键：**不是所有操作在 FP16 下都是安全的**。`softmax`、`log`、大数值的求和（如 `LayerNorm` 的方差计算）通常需要 FP32 精度。PyTorch 的 `autocast` 会自动判断哪些操作用 FP16、哪些用 FP32。

---

## 第十章：小结 — 从工程回到直觉

本文覆盖了 PyTorch 训练框架的全套基础组件。如果你能不看笔记回答出以下问题，说明你已经内化了这些知识：

1. `loss.backward()` 完成后，`w.grad` 里是什么？—— **损失对 w 的梯度 $\partial \mathcal{L} / \partial w$**
2. `optimizer.step()` 里发生了什么？—— **根据 gradient 和优化器规则更新每个参数**
3. `optimizer.zero_grad()` 为什么必须调用？—— **梯度默认累加，不归零会用过期梯度**
4. `model.train()` vs `model.eval()` 的本质区别？—— **Dropout 是否生效 + BatchNorm 用当前统计还是全局统计**
5. `nn.Linear` 的前向是什么矩阵运算？—— **$\mathbf{xW}^T + \mathbf{b}$**
6. `CrossEntropyLoss` 传入的是 logits 还是概率？—— **logits（原始分数）**
7. `Conv2d` 的梯度反传等价于什么？—— **转置卷积**
8. `BatchNorm` 为什么对小 batch 敏感？—— **小 batch 的 μ/σ 估计方差大**
9. Adam vs AdamW 的区别？—— **权重衰减与自适应学习率解耦**
10. `torch.no_grad()` 和 `model.eval()` 的区别？—— **no_grad 阻止计算图构建（省显存），eval 改变层行为（Dropout/BN 的开关）**

