# AMF-Placer 详细配置部署文档 (Win11 + Ubuntu WSL)

## 🎯 项目概述

**AMF-Placer 2.0** 是一个开源的时序驱动分析式混合尺寸FPGA布局器，**专门适合您的宏单元放置任务**。

### ✅ 现有质量评估能力分析

通过代码分析，AMF-Placer **已经具备**以下质量评估功能：

#### 1. **HPWL(Half-Perimeter Wire Length)计算** ✅

- **实现位置**: `src/lib/HiFPlacer/placement/globalPlacement/WirelengthOptimizer.cc`
- **功能**: 实时计算和优化总线长
- **API**: `placementInfo->updateB2BAndGetTotalHPWL()`
- **输出示例**: `HPWL after QP=602421.562500`

#### 2. **实时质量监控** ✅

- **位置**: `src/lib/HiFPlacer/placement/globalPlacement/GlobalPlacer.cc`
- **功能**:
  - 在全局放置过程中持续监控HPWL变化
  - 提供lowerBound和upperBound HPWL评估
  - 支持质量收敛分析

#### 3. **时序质量评估** ✅

- **功能**: 内置静态时序分析器，支持关键路径延迟评估
- **位置**: `src/lib/HiFPlacer/placement/placementTiming/`

### ❌ 缺失功能 (您的机会点)

- ❌ **Feedthrough数量计算**: 没有找到相关实现
- ❌ **空白面积(Whitespace)评估**: 没有专门的白空间计算模块
- ❌ **独立的质量评估接口**: 质量评估与放置流程紧密耦合

**这正好为您的课题提供了绝佳的集成机会！**

---

## 🖥️ 系统要求

### 硬件要求

- **CPU**: 多核处理器，推荐8核以上
- **内存**: 最少16GB，推荐32GB+
- **存储**: 最少20GB可用空间

### 软件要求

- **操作系统**: Win11 + Ubuntu 22.04 LTS (WSL2)
- **编译器**: GCC 9.0+ 或 Clang 10.0+
- **CMake**: 3.15+

---

## 🔧 环境配置 (Win11 + Ubuntu WSL)

### 步骤1: 配置WSL2环境

```powershell
# 在Windows PowerShell中执行(管理员权限)
wsl --install Ubuntu-22.04
wsl --set-default-version 2

# 验证安装
wsl --list --verbose
```

### 步骤2: 进入Ubuntu WSL环境

```bash
# 启动Ubuntu WSL
wsl

# 更新系统包
sudo apt update && sudo apt upgrade -y
```

### 步骤3: 配置基础开发环境

```bash
# 安装基础开发工具
sudo apt install -y build-essential cmake git

# 安装C++编译器
sudo apt install -y gcc-9 g++-9 clang-10

# 设置默认编译器
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 90
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 90

# 验证安装
gcc --version
g++ --version
cmake --version
```

---

## 📦 依赖安装

### 步骤1: 安装Qt5(用于GUI)

```bash
# 安装Qt5开发库
sudo apt install -y qt5-default qtbase5-dev qttools5-dev qttools5-dev-tools

# 如果上面命令在Ubuntu 22.04中失败，使用以下替代方案:
sudo apt install -y qtbase5-dev qttools5-dev-tools qt5-qmake

# 验证Qt5安装
qmake --version
```

### 步骤2: 安装数学库

```bash
# 安装基础数学库
sudo apt install -y libeigen3-dev libfftw3-dev

# 安装线性代数库
sudo apt install -y liblapack-dev libblas-dev libopenblas-dev

# 安装其他科学计算库
sudo apt install -y libarmadillo-dev
```

### 步骤3: 安装Python相关依赖(用于分析脚本)

```bash
# 安装Python和pip
sudo apt install -y python3 python3-pip python3-dev python3-venv

# 创建虚拟环境(推荐)
python3 -m venv ~/amf_env
source ~/amf_env/bin/activate

# 安装数据分析库
pip3 install numpy matplotlib pandas scipy
```

### 步骤4: 安装其他必需工具

```bash
# 安装其他有用工具
sudo apt install -y vim curl wget unzip tree

# 安装Git LFS(如果需要处理大文件)
sudo apt install -y git-lfs
```

---

## 🔨 编译与构建

### 步骤1: 导航到项目目录

```bash
# 假设您已经在labfinal目录中
cd /mnt/c/Users/86135/Desktop/VISL/labfinal/AMF-Placer

# 或者使用WSL路径
cd ~/labfinal/AMF-Placer
```

### 步骤2: 检查项目结构

```bash
# 查看项目结构
tree -L 2
ls -la

# 检查必要文件
ls src/
ls benchmarks/
```

### 步骤3: 创建构建目录

```bash
# 创建构建目录
mkdir -p build
cd build

# 清理之前的构建(如果存在)
rm -rf *
```

### 步骤4: 配置CMake

```bash
# 配置CMake(Release模式获得最佳性能)
cmake ../src -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17

# 如果需要Debug模式进行开发
# cmake ../src -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_STANDARD=17

# 如果遇到Qt5问题，指定Qt5路径
# cmake ../src -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/usr/lib/x86_64-linux-gnu/cmake/Qt5
```

### 步骤5: 编译项目

```bash
# 使用多线程编译(根据CPU核心数调整-j参数)
make -j$(nproc)

# 或者使用具体线程数
make -j8

# 检查编译输出
echo "编译状态: $?"
```

### 步骤6: 验证编译成功

```bash
# 检查生成的可执行文件
ls -la app/AMFPlacer/
file app/AMFPlacer/AMFPlacer

# 运行版本检查
./app/AMFPlacer/AMFPlacer --help

# 如果看到帮助信息，说明编译成功
```

---

## 🧪 运行测试

### 步骤1: 准备测试数据

```bash
# 回到项目根目录
cd ..
pwd

# 检查benchmark目录
ls benchmarks/
ls benchmarks/VCU108/

# 检查设计文件
ls benchmarks/VCU108/design/
ls benchmarks/VCU108/device/
```

### 步骤2: 准备配置文件

```bash
# 查看现有配置文件
ls benchmarks/testConfig/
cat benchmarks/testConfig/simple.json
```

### 步骤3: 运行简单测试

```bash
# 进入构建目录
cd build

# 创建结果目录
mkdir -p results
cd results

# 运行一个简单的测试配置
# 注意：具体命令需要根据实际benchmark调整
../app/AMFPlacer/AMFPlacer \
    --config ../../benchmarks/testConfig/digitRecognition.json \
    --verbose

# 如果上述命令不工作，尝试基础运行测试
../app/AMFPlacer/AMFPlacer
```

### 步骤4: 检查输出结果

```bash
# 检查运行日志
ls -la
cat *.log 2>/dev/null || echo "没有找到日志文件"

# 查找HPWL输出
grep -i "hpwl" *.log 2>/dev/null || echo "没有找到HPWL信息"

# 检查placement结果
ls *.pl *.rpt 2>/dev/null || echo "没有找到placement结果文件"
```

---

## 🔗 集成您的质量评估算法

基于您的课题需求，这里提供集成建议：

### 方案1: 扩展PlacementInfo类 (推荐)

1. **添加质量评估接口**:

```cpp
// 在 src/lib/HiFPlacer/placement/placementInfo/PlacementInfo.h 中添加:

class QualityEvaluator {
public:
    // 计算feedthrough数量
    int calculateFeedthrough();
  
    // 计算空白面积
    float calculateWhitespace();
  
    // 综合质量评估
    float calculateOverallQuality();
  
    // 快速评估接口
    float fastQualityEstimate();
};

// 在PlacementInfo类中添加:
private:
    QualityEvaluator* qualityEvaluator;
  
public:
    // 获取feedthrough数量
    int getFeedthroughCount();
  
    // 获取空白面积比例
    float getWhitespaceRatio();
  
    // 获取综合质量分数
    float getQualityScore();
```

2. **创建独立的质量评估模块**:

```bash
# 创建新的质量评估模块目录
mkdir -p src/lib/HiFPlacer/qualityEvaluation

# 创建基础文件
touch src/lib/HiFPlacer/qualityEvaluation/QualityEvaluator.h
touch src/lib/HiFPlacer/qualityEvaluation/QualityEvaluator.cc
touch src/lib/HiFPlacer/qualityEvaluation/CMakeLists.txt
```

### 方案2: 创建插件式架构

1. **创建质量评估插件**:

```cpp
// QualityPlugin.h
class QualityPlugin {
public:
    virtual float evaluateQuality(PlacementInfo* info) = 0;
    virtual std::string getPluginName() = 0;
};

class FeedthroughEvaluator : public QualityPlugin {
public:
    float evaluateQuality(PlacementInfo* info) override;
    std::string getPluginName() override { return "FeedthroughEvaluator"; }
};
```

### 集成到现有优化流程

在 `src/lib/HiFPlacer/placement/globalPlacement/GlobalPlacer.cc` 中添加质量评估调用：

```cpp
// 在全局放置迭代中添加质量评估
for (int i = 0; i < iterNum; i++) {
    // ... 现有的HPWL优化代码 ...
  
    // 添加您的质量评估
    int feedthrough = placementInfo->getFeedthroughCount();
    float whitespace = placementInfo->getWhitespaceRatio();
    float quality = placementInfo->getQualityScore();
  
    print_info("Iteration#" + std::to_string(i) + 
              " HPWL=" + std::to_string(upperBoundHPWL) +
              " Feedthrough=" + std::to_string(feedthrough) +
              " Whitespace=" + std::to_string(whitespace) +
              " Quality=" + std::to_string(quality));
  
    // ... 继续优化流程 ...
}
```

---

## 📊 使用GSRC/MCNC数据集

### 准备标准数据集

```bash
# 创建数据集目录
mkdir -p ~/datasets
cd ~/datasets

# 下载GSRC数据集 (如果可访问外网)
# wget http://vlsicad.eecs.umich.edu/BK/GSRCbench/GSRC.zip
# unzip GSRC.zip

# 下载MCNC数据集
# wget http://vlsicad.eecs.umich.edu/BK/MCNCbench/MCNC.zip
# unzip MCNC.zip

# 如果无法下载，手动放置数据集文件到此目录
```

### 数据格式转换

```bash
# 创建数据转换脚本
cd ~/labfinal/AMF-Placer
mkdir -p scripts

cat > scripts/convert_gsrc_to_amf.py << 'EOF'
#!/usr/bin/env python3
"""
GSRC/MCNC数据集到AMF-Placer格式转换脚本
"""

import sys
import os
import json

def convert_blocks_file(blocks_file, output_dir):
    """转换.blocks文件"""
    # 实现转换逻辑
    pass

def convert_nets_file(nets_file, output_dir):
    """转换.nets文件"""
    # 实现转换逻辑
    pass

def convert_pl_file(pl_file, output_dir):
    """转换.pl文件"""
    # 实现转换逻辑
    pass

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 convert_gsrc_to_amf.py <input_dir> <output_dir>")
        sys.exit(1)
  
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
  
    # 执行转换
    convert_blocks_file(os.path.join(input_dir, "*.blocks"), output_dir)
    convert_nets_file(os.path.join(input_dir, "*.nets"), output_dir)
    convert_pl_file(os.path.join(input_dir, "*.pl"), output_dir)
  
    print(f"转换完成: {input_dir} -> {output_dir}")
EOF

chmod +x scripts/convert_gsrc_to_amf.py
```

---

## 🐛 常见问题解决

### 问题1: CMake配置失败

```bash
# 解决方案1: 更新CMake
sudo apt remove cmake
sudo apt install -y software-properties-common
sudo apt-add-repository 'deb https://apt.kitware.com/ubuntu/ bionic main'
sudo apt update
sudo apt install -y cmake

# 解决方案2: 手动指定依赖路径
cmake ../src -DCMAKE_BUILD_TYPE=Release \
    -DEIGEN3_INCLUDE_DIR=/usr/include/eigen3 \
    -DQt5_DIR=/usr/lib/x86_64-linux-gnu/cmake/Qt5
```

### 问题2: Qt5找不到

```bash
# 解决方案1: 安装完整Qt5包
sudo apt install -y qt5-default qtbase5-dev qttools5-dev-tools qtdeclarative5-dev

# 解决方案2: 手动指定Qt5路径
export Qt5_DIR=/usr/lib/x86_64-linux-gnu/cmake/Qt5
cmake ../src -DCMAKE_PREFIX_PATH=$Qt5_DIR
```

### 问题3: 编译内存不足

```bash
# 解决方案: 减少并行编译线程
make -j2  # 而不是 make -j8

# 或者增加WSL内存限制
# 在Windows中创建 C:\Users\[用户名]\.wslconfig 文件:
echo "[wsl2]
memory=8GB
processors=4" > /mnt/c/Users/$USER/.wslconfig

# 重启WSL
wsl --shutdown
```

### 问题4: 运行时找不到库

```bash
# 解决方案: 设置环境变量
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# 添加到~/.bashrc使其永久生效
echo 'export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

---

## 🚀 性能优化建议

### 1. 编译优化

```bash
# 使用优化编译选项
cmake ../src -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_FLAGS="-O3 -march=native -mtune=native"
```

### 2. 运行时优化

```bash
# 设置并行线程数
export OMP_NUM_THREADS=$(nproc)

# 如果安装了MKL，加载MKL环境
# source /opt/intel/mkl/bin/mklvars.sh intel64
```

### 3. 内存优化

```bash
# 增加swap空间(如果内存不足)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📝 下一步建议

1. **熟悉现有代码结构**:

   - 研究 `PlacementInfo.h` 中的HPWL计算方法
   - 理解 `GlobalPlacer.cc` 中的优化流程
2. **实现质量评估算法**:

   - 基于现有的HPWL框架扩展feedthrough计算
   - 添加空白面积计算模块
   - 集成到优化循环中
3. **验证和测试**:

   - 使用GSRC/MCNC数据集验证算法正确性
   - 与baseline结果对比
   - 性能分析和优化
4. **文档和报告**:

   - 记录实现细节
   - 准备实验结果
   - 撰写课题报告

---

## 📞 技术支持

如果在配置过程中遇到问题，可以：

1. 检查 `/var/log/` 中的系统日志
2. 使用 `ldd ./app/AMFPlacer/AMFPlacer` 检查依赖
3. 参考项目的 GitHub Issues: https://github.com/zslwyuan/AMF-Placer/issues

**祝您项目顺利！** 🎉
