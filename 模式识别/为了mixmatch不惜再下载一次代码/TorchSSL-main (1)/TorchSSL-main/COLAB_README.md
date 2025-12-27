# 🚀 在Google Colab上运行TorchSSL MixMatch

本指南将帮助您在Google Colab上成功运行MixMatch半监督学习算法。

## 📋 快速开始

### 1. 上传代码到Colab

将整个项目文件夹上传到Google Colab或通过Git克隆：

```bash
# 如果使用Git克隆
!git clone <your-repo-url>
%cd TorchSSL-main
```

### 2. 使用自动设置脚本（推荐）

我们提供了一个自动化脚本来简化Colab设置：

```python
# 安装依赖并运行MixMatch
!python colab_setup.py --algorithm mixmatch --dataset cifar10 --num_labels 250 --install_deps
```

### 3. 手动设置（如果需要更多控制）

```python
# 1. 安装必要依赖
!pip install tensorboard scikit-learn PyYAML pillow

# 2. 检查GPU
import torch
print(f"GPU可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU名称: {torch.cuda.get_device_name(0)}")

# 3. 运行MixMatch
!python mixmatch.py --c config/mixmatch/mixmatch_cifar10_250_0.yaml --overwrite True
```

## ⚙️ 已优化的配置

我们已经对代码进行了以下Colab适配：

### ✅ 路径修复

- **数据统计路径**: `./data_statistics/` → `{data_dir}/data_statistics/`
- **模型保存路径**: 使用相对路径，适合Colab环境
- **配置文件路径**: 自动生成Colab优化的配置

### ✅ 参数优化

- **多进程**: 禁用多进程分布式训练 (`multiprocessing_distributed: False`)
- **worker数量**: 减少为2，避免Colab内存问题
- **AMP**: 默认关闭，提高稳定性
- **批大小**: 保持64，适合Colab GPU内存

## 🎯 支持的配置

### 数据集

- `cifar10` (默认)
- `cifar100`
- `svhn`
- `stl10`

### 标签数量示例

- CIFAR-10: 40, 250, 4000
- CIFAR-100: 400, 2500, 10000
- SVHN: 40, 250, 1000

## 📁 目录结构

运行后会自动创建以下目录：

```
├── data/                    # 数据集下载目录
│   └── data_statistics/     # 数据统计文件
├── saved_models/            # 模型保存目录
├── config/                  # 配置文件
└── figures/                 # 图像文件
```

## 🔧 自定义配置

### 创建自定义配置

```python
# 仅设置，不运行训练
!python colab_setup.py --algorithm mixmatch --dataset cifar10 --num_labels 250 --setup_only

# 然后手动运行
!python mixmatch.py --c config/mixmatch/mixmatch_cifar10_250_colab.yaml
```

### 修改关键参数

如果要修改训练参数，可以编辑生成的配置文件或直接在命令行指定：

```python
!python mixmatch.py \
    --data_dir ./data \
    --save_dir ./saved_models \
    --dataset cifar10 \
    --num_labels 250 \
    --batch_size 64 \
    --num_train_iter 20000 \
    --overwrite True
```

## 📊 监控训练

### 使用TensorBoard

```python
# 加载TensorBoard
%load_ext tensorboard
%tensorboard --logdir saved_models/
```

### 查看训练日志

```python
# 查看最新的训练日志
!tail -f saved_models/*/log.txt
```

## 🚨 常见问题解决

### 1. 内存不足

```python
# 减小批大小
!python mixmatch.py --batch_size 32 --c config/mixmatch/mixmatch_cifar10_250_colab.yaml
```

### 2. CUDA内存错误

```python
# 重启运行时并清除缓存
import torch
torch.cuda.empty_cache()
```

### 3. 依赖包问题

```python
# 重新安装依赖
!python colab_setup.py --install_deps --setup_only
```

### 4. 路径问题

确保所有路径都使用相对路径。如果遇到路径错误，请检查：

- 数据目录是否存在
- 配置文件路径是否正确
- 模型保存目录是否可写

## 📈 性能优化建议

### 1. 使用GPU运行时

确保在Colab中启用GPU：

- Runtime → Change runtime type → Hardware accelerator → GPU

### 2. 优化批大小

根据GPU内存调整：

- T4 GPU: batch_size=64 (默认)
- 如果内存不足，减小到32或16

### 3. 减少训练迭代

对于快速测试：

```python
!python mixmatch.py --num_train_iter 5000 --c config/mixmatch/mixmatch_cifar10_250_colab.yaml
```

## 📝 示例命令

### 完整训练流程

```python
# CIFAR-10，250个标签
!python colab_setup.py --algorithm mixmatch --dataset cifar10 --num_labels 250 --install_deps

# CIFAR-100，2500个标签
!python colab_setup.py --algorithm mixmatch --dataset cifar100 --num_labels 2500 --install_deps

# SVHN，40个标签
!python colab_setup.py --algorithm mixmatch --dataset svhn --num_labels 40 --install_deps
```

### 仅设置环境

```python
!python colab_setup.py --setup_only --install_deps
```

## 🎉 验证安装

运行以下命令验证一切正常：

```python
# 快速测试（5分钟训练）
!python mixmatch.py \
    --dataset cifar10 \
    --num_labels 250 \
    --num_train_iter 1000 \
    --num_eval_iter 500 \
    --overwrite True
```

如果看到训练开始并输出loss值，说明配置成功！

---

## 🤝 需要帮助？

如果遇到问题：

1. 首先尝试重启Colab运行时
2. 确保按照步骤顺序执行
3. 检查GPU是否可用
4. 验证所有依赖包已安装

Happy training! 🚀
