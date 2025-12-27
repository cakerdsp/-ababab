# AMF-Placer 运行原理与配置详解

## 📑 目录

- [系统架构与运行原理](#系统架构与运行原理)
- [程序启动与加载流程](#程序启动与加载流程)
- [核心算法运行原理](#核心算法运行原理)
- [配置参数详解](#配置参数详解)
- [数据集组织格式](#数据集组织格式)
- [质量评估机制](#质量评估机制)
- [集成扩展指南](#集成扩展指南)

---

## 🏗️ 系统架构与运行原理

### 系统整体架构

AMF-Placer是一个**时序驱动的分析式混合尺寸FPGA布局器**，采用分层次、模块化设计：

```
AMF-Placer 系统架构
├── 主程序入口 (main.cc)
├── 核心控制器 (AMFPlacer.h/.cc)
├── 设备信息管理 (DeviceInfo)
├── 设计信息管理 (DesignInfo)  
├── 布局信息管理 (PlacementInfo)
├── 全局布局器 (GlobalPlacer)
├── 时序优化器 (PlacementTimingOptimizer)
├── 初始打包器 (InitialPacker)
├── 增量打包器 (IncrementalBELPacker)
└── 并行CLB打包器 (ParallelCLBPacker)
```

### 核心设计理念

1. **混合尺寸支持**: 同时处理标准单元和宏单元
2. **时序驱动**: 以时序收敛为优化目标
3. **分析式方法**: 使用数学优化而非启发式搜索
4. **模块化架构**: 便于功能扩展和定制

---

## 🚀 程序启动与加载流程

### 1. 主程序入口 (`main.cc`)

```cpp
int main(int argc, char **argv)
{
    // 1. 命令行参数解析
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <config JSON file> [-gui]" << std::endl;
        return 1;
    }
  
    // 2. 创建AMFPlacer对象
    AMFPlacer *placer = new AMFPlacer(argv[1], guiEnable);
  
    // 3. 启动布局线程
    std::thread threadPlacer(runPlacer, placer);
  
    // 4. 可选启动可视化线程
    if (guiEnable)
        threadPaint = new std::thread(runVisualization, placer);
}
```

### 2. AMFPlacer构造函数加载流程

```cpp
AMFPlacer(std::string JSONFileName, bool guiEnable)
{
    // 步骤1: 解析JSON配置文件
    JSON = parseJSONFile(JSONFileName);
  
    // 步骤2: 验证必需参数
    assert(JSON.find("vivado extracted device information file") != JSON.end());
    assert(JSON.find("vivado extracted design information file") != JSON.end());
    // ... 其他必需参数验证
  
    // 步骤3: 设置并行线程数
    omp_set_num_threads(std::stoi(JSON["jobs"]));
  
    // 步骤4: 加载设备信息
    deviceinfo = new DeviceInfo(JSON, "VCU108");
  
    // 步骤5: 加载设计信息
    designInfo = new DesignInfo(JSON, deviceinfo);
  
    // 步骤6: 初始化绘图数据库
    paintData = new PaintDataBase();
}
```

### 3. 详细的数据加载顺序

#### 设备信息加载 (DeviceInfo)

```
1. 读取设备归档文件 (exportSiteLocation.zip)
2. 解析站点信息 (Sites: SLICE_X59Y220, RAMB18_X7Y88, etc.)
3. 解析BEL信息 (Basic Elements: LUTs, FFs, DSPs, etc.)
4. 构建时钟区域信息 (Clock Regions)
5. 建立兼容性映射表
```

#### 设计信息加载 (DesignInfo)

```
1. 读取设计归档文件 (OpenPiton_allCellPinNet.zip)
2. 解析网表信息 (Cells, Pins, Nets)
3. 识别单元类型 (LUT, FF, DSP, BRAM, CARRY, etc.)
4. 建立连通性信息
5. 加载用户定义的聚类信息 (可选)
6. 加载时钟信息
```

---

## ⚙️ 核心算法运行原理

### AMFPlacer::run() 完整流程

```cpp
void run()
{
    // === 阶段1: 初始化阶段 ===
    // 1.1 创建布局信息对象
    placementInfo = new PlacementInfo(designInfo, deviceinfo, JSON);
  
    // 1.2 初始打包 - 识别和创建宏单元
    InitialPacker *initialPacker = new InitialPacker(...);
    initialPacker->pack();  // 找到CARRY、MUX、BRAM、DSP宏
  
    // 1.3 创建网格箱和验证设备兼容性
    placementInfo->createGridBins(5.0, 5.0);
    placementInfo->verifyDeviceForDesign();
  
    // 1.4 构建时序图
    placementInfo->buildSimpleTimingGraph();
    PlacementTimingOptimizer *timingOptimizer = new PlacementTimingOptimizer(...);
  
    // === 阶段2: 全局布局阶段 ===
    globalPlacer = new GlobalPlacer(placementInfo, JSON);
  
    // 2.1 聚类布局 - 初始粗粒度布局
    globalPlacer->clusterPlacement();
    timingOptimizer->clusterLongPathInOneClockRegion(longPathThr, 0.5);
  
    // 2.2 固定CLB元素布局
    globalPlacer->GlobalPlacement_fixedCLB(1, 0.0002);
  
    // 2.3 第一轮CLB元素布局（粗调）
    globalPlacer->GlobalPlacement_CLBElements(iterNum/3, false, 5, true, true, 200, timingOptimizer);
  
    // === 阶段3: 精化布局阶段 ===
    // 3.1 调整伪网权重和参数
    globalPlacer->setPseudoNetWeight(pseudoNetWeight * 0.85);
    placementInfo->createGridBins(2.5, 2.5);  // 更细的网格
  
    // 3.2 第二轮CLB元素布局（中调）
    globalPlacer->GlobalPlacement_CLBElements(iterNum*2/9, true, 5, true, true, 200, timingOptimizer);
  
    // === 阶段4: 增量打包阶段 ===
    // 4.1 LUT-FF配对
    incrementalBELPacker = new IncrementalBELPacker(...);
    incrementalBELPacker->LUTFFPairing(4.0);
    incrementalBELPacker->FFPairing(4.0);
  
    // 4.2 第三轮CLB元素布局（细调）
    globalPlacer->GlobalPlacement_CLBElements(iterNum*2/9, true, 5, true, true, 25, timingOptimizer);
  
    // === 阶段5: 最终打包阶段 ===
    // 5.1 静态时序分析
    timingOptimizer->conductStaticTimingAnalysis();
  
    // 5.2 并行CLB打包
    parallelCLBPacker = new ParallelCLBPacker(...);
    parallelCLBPacker->packCLBs(30, true);
  
    // 5.3 最终质量评估和结果输出
    placementInfo->checkClockUtilization(true);
    print_info("Current Total HPWL = " + std::to_string(placementInfo->updateB2BAndGetTotalHPWL()));
}
```

### 关键算法模块详解

#### 1. **聚类算法 (ClusterPlacer)**

```
目的: 将相关单元聚集在一起，减少布局复杂度
方法: 
- 基于连通性的图分割
- 考虑时序关键路径
- 使用模拟退火优化聚类位置
```

#### 2. **线长优化 (WirelengthOptimizer)**

```
目的: 最小化总线长(HPWL)
方法:
- 二次规划求解器
- 伪网技术处理重叠
- MKL数学库加速计算
```

#### 3. **时序优化 (PlacementTimingOptimizer)**

```
目的: 满足时序约束，最小化关键路径延迟
方法:
- 构建时序图并进行STA分析
- 识别关键路径
- 基于slack的网权重调整
- 时序驱动的单元移动
```

#### 4. **合法化 (Legalizers)**

```
宏合法化 (MacroLegalizer): DSP/BRAM等大单元的位置合法化
CLB合法化 (CLBLegalizer): 标准单元到SLICE的映射
```

---

## 📋 配置参数详解

### 必需参数 (Required Parameters)

#### 输入文件路径参数

```json
{
    "vivado extracted device information file": "../benchmarks/VCU108/device/exportSiteLocation.zip",
    "vivado extracted design information file": "../benchmarks/VCU108/design/OpenPiton/OpenPiton_allCellPinNet.zip",
    "cellType2fixedAmo file": "../benchmarks/VCU108/compatibleTable/cellType2fixedAmo",
    "cellType2sharedCellType file": "../benchmarks/VCU108/compatibleTable/cellType2sharedCellType",
    "sharedCellType2BELtype file": "../benchmarks/VCU108/compatibleTable/sharedCellType2BELtype"
}
```

**解释:**

- **设备信息文件**: FPGA器件的物理布局信息
- **设计信息文件**: 电路网表、单元、引脚连接信息
- **兼容性映射文件**: 单元类型到BEL类型的映射关系

#### 核心算法参数

```json
{
    "GlobalPlacementIteration": "30",           // 全局布局迭代次数
    "ClockPeriod": "10",                       // 目标时钟周期(ns)
    "PseudoNetWeight": "0.0025",               // 伪网权重
    "Simulated Annealing IterNum": "30000000", // 模拟退火迭代次数
    "jobs": "8"                                // 并行线程数
}
```

### 可选参数 (Optional Parameters)

#### 时序优化参数

```json
{
    "DSPCritical": "true",                     // 启用DSP关键路径优化
    "ClockPeriod:specific_clock": "3.3",       // 特定时钟域的周期约束
    "y2xRatio": "0.4"                          // Y/X坐标权重比
}
```

#### 调试和输出参数

```json
{
    "GlobalPlacerPrintHPWL": "true",           // 打印HPWL信息
    "GlobalPlacerVerbose": "false",            // 详细日志输出
    "DumpCLBPacking": "./DumpCLBPacking",      // CLB打包结果输出
    "DumpClockUtilization": "true",            // 时钟利用率输出
    "dumpDirectory": "./dumpData_OpenPiton"    // 结果输出目录
}
```

#### 设备特定参数

```json
{
    "clockRegionXNum": "5",                    // 时钟区域X方向数量
    "clockRegionYNum": "8",                    // 时钟区域Y方向数量
    "clockRegionDSPNum": "30",                 // 每个时钟区域DSP数量
    "clockRegionBRAMNum": "96"                 // 每个时钟区域BRAM数量
}
```

### 高级参数 (Advanced Parameters)

#### 算法调优参数

```json
{
    "Simulated Annealing restartNum": "600",   // SA重启次数
    "RandomInitialPlacement": "true",          // 随机初始布局
    "MKL": "true",                            // 使用Intel MKL库
    "useUnconstrainedCG": "false",            // 使用无约束共轭梯度
    "DirectMacroLegalize": "false"            // 直接宏合法化
}
```

---

## 📁 数据集组织格式

### AMF-Placer完整的Benchmarks目录结构

```
AMF-Placer/benchmarks/
├── VCU108/                    # 主要数据集目录
│   ├── device/                # 🔧 FPGA设备物理信息
│   ├── design/                # 📊 电路设计数据集合
│   ├── compatibleTable/       # 🔗 映射兼容性表
│   └── preprocessPython/      # 🐍 数据预处理脚本
├── testConfig/                # ⚙️ 测试配置文件集
│   ├── *.json                 # 各设计的配置文件
│   └── testConfigSets/        # 参数调优配置集
├── analysisScripts/           # 📈 结果分析脚本
├── vivadoScripts/            # 🔨 Vivado数据提取脚本
├── DSE/                      # 🎯 设计空间探索工具
├── versionPerformance/       # 📊 性能基准测试结果
└── helperPythonScripts/      # 🛠️ 辅助工具脚本
```

### 📊 **设计数据集详细分析** (VCU108/design/)

#### 可用的设计基准按规模排序:

| 设计名称 | 网表文件大小 | 复杂度 | 推荐用途 |
|---------|-------------|--------|----------|
| **BLSTM_DSPDomain** | 7.9M | ⭐⭐ | **最小测试** - 内存受限时首选 |
| **faceDetect** | 8.5M | ⭐⭐ | 小规模验证 |
| **halfsqueezenet** | 8.4M | ⭐⭐ | 神经网络应用 |
| **digitRecognition** | 14M | ⭐⭐⭐ | 中等规模测试 |
| **OpenPiton** | 17M | ⭐⭐⭐⭐ | 复杂处理器设计 |
| **BLSTM_midDensity** | 17M | ⭐⭐⭐⭐ | 中高密度设计 |
| **MemN2N** | 18M | ⭐⭐⭐⭐ | 内存网络 |
| **optimsoc** | 26M | ⭐⭐⭐⭐⭐ | 大规模SoC |
| **minimap2** | 43M | ⭐⭐⭐⭐⭐ | **最大规模** - 高性能需求 |

#### 每个设计包含的标准文件:
```
design/[设计名]/
├── [设计名]_allCellPinNet.zip    # 🔗 完整网表信息 (核心数据)
├── [设计名]_fixedUnits           # 📌 固定单元约束
├── [设计名]_clocks              # ⏰ 时钟域定义
├── [设计名]_clusters.zip        # 🎯 用户定义聚类 (可选)
└── [设计名]_unpredictableMacros  # 🔧 不可预测宏定义
```

### 🔧 **设备信息结构** (VCU108/device/)

```
VCU108/device/
├── exportSiteLocation.zip    # 📍 站点位置坐标 (7.4MB)
│   └── 包含所有SLICE、DSP、BRAM等站点的物理坐标
├── VCU108DeviceSite.zip     # 🏗️ 设备站点详细信息 (9.1MB)  
│   └── 详细的BEL和资源信息
├── PCIEPin2SwXY             # 🔌 PCIe引脚坐标映射 (541KB)
└── PCIEPin2Sw               # 🔌 PCIe引脚开关映射 (802KB)
```

### 🔗 **兼容性映射表** (VCU108/compatibleTable/)

```
VCU108/compatibleTable/
├── cellType2fixedAmo              # 单元类型 → 固定数量
├── cellType2sharedCellType        # 单元类型 → 共享类型  
├── sharedCellType2BELtype         # 共享类型 → BEL类型
├── mergedSharedCellType2sharedCellType # 合并类型映射
└── cellType2BELinSite             # 单元在站点中的BEL映射
```

### ⚙️ **测试配置管理** (testConfig/)

#### 主要配置文件:
```
testConfig/
├── BLSTM_DSPDomain.json      # 🥇 推荐: 最小测试用例
├── faceDetect.json           # 🥈 推荐: 小规模验证
├── digitRecognition.json     # 🥉 推荐: 中等规模
├── OpenPiton.json           # 经典处理器设计
├── MemN2N.json              # 内存网络
├── halfsqueezenet.json      # 神经网络
├── optimsoc.json            # 大规模SoC
├── minimap2.json            # 超大规模 (需要高性能)
└── testConfigSets/          # 参数调优配置
    ├── config0/ → config6/   # 不同参数组合
    └── outputs/             # 配置测试结果
```

### 🛠️ **辅助工具集**

#### 📈 分析脚本 (analysisScripts/)
```
analysisScripts/
├── paintPlacement.py         # 布局可视化
├── coordDensityVisualization.py # 密度分析
├── densityVisualization.py   # 密度可视化
├── VivadoGraphUtil.py       # Vivado图形工具
└── figProcess.py            # 图像处理
```

#### 🔨 Vivado脚本 (vivadoScripts/)
```
vivadoScripts/
├── extractNetlist.tcl       # 网表提取
├── extractDeviceInfo.tcl    # 设备信息提取
├── extractDesignInfo.tcl    # 设计信息提取
├── extractTileSite.tcl      # 瓦片站点提取
├── extractFixedUnits.tcl    # 固定单元提取
├── extractLUTRAMs.tcl       # LUTRAM提取
├── checkCriticalPath.tcl    # 关键路径检查
└── clockCheck.tcl           # 时钟检查
```

#### 🎯 设计空间探索 (DSE/)
```
DSE/
├── DSE.py                   # 设计空间探索主程序
└── AMF-Vivado.py           # AMF与Vivado集成脚本
```

#### 📊 性能基准 (versionPerformance/)
```
versionPerformance/
├── 20220627, 20220712, ...  # 历史性能数据
├── 20220408.csv            # CSV格式基准数据
└── benchmarksScreenshots/   # 基准测试截图
```

### 🎯 **推荐的测试策略**

#### 1. **内存受限环境** (如您当前7.6GB)
```bash
# 首选: 最小设计
./AMFPlacer ../benchmarks/testConfig/BLSTM_DSPDomain.json

# 备选: 小规模设计  
./AMFPlacer ../benchmarks/testConfig/faceDetect.json
```

#### 2. **正常测试环境** (16GB+)
```bash
# 中等规模验证
./AMFPlacer ../benchmarks/testConfig/digitRecognition.json

# 经典测试用例
./AMFPlacer ../benchmarks/testConfig/OpenPiton.json
```

#### 3. **高性能环境** (32GB+)
```bash
# 大规模SoC设计
./AMFPlacer ../benchmarks/testConfig/optimsoc.json

# 超大规模设计
./AMFPlacer ../benchmarks/testConfig/minimap2.json
```

### 📝 **与您课题的关联**

#### 🎯 **课题要求的数据集对比**

根据您的课题要求，标准的floorplan数据集是：

| 标准数据集 | AMF-Placer数据集 | 区别与联系 |
|------------|------------------|------------|
| **GSRC** (n10, n30, n50, n100, n200, n300) | **VCU108/design/** 的9个设计 | AMF-Placer是FPGA数据集，GSRC是ASIC数据集 |
| **MCNC** (ami33, ami49, apte, hp, xero) | **testConfig/** 中的配置文件 | 都包含blocks、nets、placement信息 |
| `.blocks` 文件 (硬/软模块) | `_allCellPinNet.zip` 文件 | AMF-Placer更详细，包含FPGA特定信息 |
| `.nets` 文件 (连接关系) | 网表信息在zip文件中 | 格式不同但都描述连通性 |
| `.pl` 文件 (布局位置) | `_fixedUnits` 和约束文件 | AMF-Placer支持更复杂的约束 |

#### 🔄 **数据集格式转换建议**

**如果您需要使用标准GSRC/MCNC数据集：**

1. **下载标准数据集**：
   ```bash
   # 您可以从课题提供的链接下载
   # GSRC: http://vlsicad.eecs.umich.edu/BK/GSRCbench/
   # MCNC: http://vlsicad.eecs.umich.edu/BK/MCNCbench/
   ```

2. **集成方式建议**：
   ```cpp
   // 在AMF-Placer框架中添加GSRC/MCNC解析器
   class GSRCDataLoader {
       void loadBlocksFile(string blocksFile);
       void loadNetsFile(string netsFile);  
       void loadPlacementFile(string plFile);
       // 转换为AMF-Placer的数据结构
   };
   ```

3. **或者直接在AMF-Placer现有数据集上验证**：
   - AMF-Placer的数据集**更加真实和复杂**
   - 包含完整的FPGA约束和时序信息
   - 更适合验证您的质量评估算法

#### 🎯 **为您课题的优势**

**使用AMF-Placer数据集的好处：**

1. **完整的宏单元信息**: 包含DSP、BRAM等复杂宏单元
2. **真实的feedthrough场景**: FPGA布局中天然存在大量feedthrough需求  
3. **多层次的空白区域**: 支持更精确的whitespace分析
4. **时序驱动的评估**: 可以验证质量评估与时序的correlation
5. **可扩展的测试平台**: 从小到大的设计规模，便于算法验证

#### 🔧 **集成您的质量评估算法**

这些数据集为您的**feedthrough和whitespace质量评估算法**提供了完整的测试平台：

1. **多样性**: 从7.9M到43M的不同规模设计
2. **真实性**: 来自实际FPGA应用的复杂设计  
3. **完整性**: 包含网表、约束、时钟等完整信息
4. **可扩展性**: 便于集成您的质量评估指标

#### 🚀 **推荐的实施策略**

1. **第一阶段**: 在AMF-Placer框架中实现和验证您的算法
2. **第二阶段**: 如果需要，添加GSRC/MCNC数据集的支持  
3. **第三阶段**: 在论文中对比两套数据集的结果

**建议从`BLSTM_DSPDomain`开始测试，成功后逐步尝试更大的设计！**

### 关键文件格式解析

#### 1. **设备信息文件** (`exportSiteLocation.zip`)

**格式示例:**

```
site=> SLICE_X59Y220 tile=> CLEL_R_X36Y220 sitetype=> SLICEL tiletype=> CLE_R 
centerx=> 37.25 centery=> 220.15
BELs=> [SLICE_X59Y220/A5LUT,SLICE_X59Y220/A6LUT,SLICE_X59Y220/AFF,SLICE_X59Y220/AFF2,...]

site=> RAMB18_X7Y88 tile=> BRAM_X36Y220 sitetype=> RAMBFIFO18 tiletype=> CLE_R 
centerx=> 36.75 centery=> 221.96
BELs=> [RAMB18_X7Y88/RAMBFIFO18]
```

**字段含义:**

- `site`: 站点名称 (物理位置标识)
- `tile`: 所属瓦片
- `sitetype`: 站点类型 (SLICEL, SLICEM, RAMBFIFO18, etc.)
- `centerx/centery`: 物理坐标
- `BELs`: 包含的基本元素列表

#### 2. **设计网表文件** (`OpenPiton_allCellPinNet.zip`)

**格式示例:**

```
curCell=> design_1_i/axis_clock_converter_0/inst/.../FSM_sequential_gen_fwft.curr_fwft_state[0]_i_1
type=> LUT4
    pin=> .../FSM_sequential_gen_fwft.curr_fwft_state[0]_i_1/O
    dir=> OUT 
    net=> .../next_fwft_state__0[0]
    drivepin=> .../FSM_sequential_gen_fwft.curr_fwft_state[0]_i_1/O
    pin=> .../FSM_sequential_gen_fwft.curr_fwft_state[0]_i_1/I0
    dir=> IN 
    net=> .../rd_en
    drivepin=> .../input_r_TREADY_INST_0/O
```

**字段含义:**

- `curCell`: 单元实例名称
- `type`: 单元类型 (LUT4, FF, DSP48E2, etc.)
- `pin`: 引脚名称和方向
- `net`: 连接的网络名称
- `drivepin`: 驱动该引脚的源引脚

#### 3. **兼容性映射文件**

**cellType2fixedAmo:**

```
LUT1 1
LUT2 1  
LUT3 1
LUT4 1
LUT5 1
LUT6 1
DSP48E2 1
RAMB18E2 1
RAMB36E2 1
```

**cellType2sharedCellType:**

```
LUT1 LUT
LUT2 LUT
LUT3 LUT
FDRE FF
FDSE FF
DSP48E2 DSP
```

#### 4. **时钟文件** (`OpenPiton_clocks`)

**格式示例:**

```
clk_out1 design_1_i/clk_wiz_0/inst/clk_out1
clk_out2 design_1_i/clk_wiz_0/inst/clk_out2
```

---

## 📊 质量评估机制

### 现有质量指标

#### 1. **HPWL (Half-Perimeter Wire Length)**

```cpp
// 实时HPWL计算
float totalHPWL = placementInfo->updateB2BAndGetTotalHPWL();
print_info("Current Total HPWL = " + std::to_string(totalHPWL));
```

**特点:**

- 实时监控布局质量
- 支持增量更新
- 作为主要优化目标

#### 2. **时序质量评估**

```cpp
// 静态时序分析
float criticalPathDelay = timingOptimizer->conductStaticTimingAnalysis();
// 获取关键路径
std::vector<int> criticalPath = timingOptimizer->findCriticalPath();
```

**功能:**

- 关键路径延迟计算
- Slack分析
- 时序收敛检查

#### 3. **资源利用率**

```cpp
// 时钟利用率检查
placementInfo->checkClockUtilization(true);
// 拥塞分析
placementInfo->dumpCongestion(JSON["dumpDirectory"] + "/congestionInfo");
```

### 🎯 **您的扩展机会: 缺失的质量指标**

AMF-Placer目前**缺少**以下重要质量指标，这正是您课题的价值：

#### 1. **Feedthrough数量计算**

```cpp
// 建议在PlacementInfo类中添加
int calculateFeedthroughCount();
float evaluateFeedthroughQuality();
```

#### 2. **空白面积(Whitespace)评估**

```cpp
// 建议扩展
float calculateWhitespaceRatio();
std::vector<float> getRegionDensity();
```

#### 3. **独立质量评估接口**

```cpp
// 建议创建QualityEvaluator类
class QualityEvaluator {
    float evaluateHPWL();
    int evaluateFeedthrough();
    float evaluateWhitespace();
    float calculateOverallQuality();
};
```

---

## 🔧 集成扩展指南

### 为您的质量评估算法集成AMF-Placer

#### 1. **推荐集成位置**

**在PlacementInfo类中扩展:**

```cpp
// PlacementInfo.h 中添加
class PlacementInfo {
    // ... 现有代码 ...
  
    // 您的扩展
    int calculateFeedthroughCount();
    float evaluateWhitespaceQuality();
    void integrateYourQualityMetrics();
};
```

**在GlobalPlacer中集成:**

```cpp
// GlobalPlacer.cc 的优化循环中
void GlobalPlacer::GlobalPlacement_CLBElements(...) {
    // ... 现有优化逻辑 ...
  
    // 添加您的质量评估
    float feedthroughQuality = placementInfo->calculateFeedthroughCount();
    float whitespaceQuality = placementInfo->evaluateWhitespaceQuality();
  
    print_info("Feedthrough Count = " + std::to_string(feedthroughQuality));
    print_info("Whitespace Quality = " + std::to_string(whitespaceQuality));
}
```

#### 2. **建议的实现步骤**

1. **理解现有代码结构**: 熟悉PlacementInfo和GlobalPlacer
2. **实现质量计算函数**: 在PlacementInfo中添加您的算法
3. **集成到优化循环**: 在适当位置调用质量评估
4. **添加配置参数**: 在JSON配置中添加相关控制参数
5. **验证和测试**: 使用GSRC/MCNC数据集测试

#### 3. **与现有系统的接口**

**数据访问接口:**

```cpp
// 获取单元位置
auto& cellLocations = placementInfo->getCellId2location();

// 获取网表信息  
auto& nets = placementInfo->getPlacementNets();

// 获取设备信息
auto deviceInfo = placementInfo->getDeviceInfo();
```

**质量监控集成:**

```cpp
// 在适当位置添加您的指标
if (JSONCfg.find("EnableFeedthroughEvaluation") != JSONCfg.end()) {
    float feedthroughScore = evaluateFeedthrough();
    // 根据结果调整优化策略
}
```

### 🎯 **下一步行动建议**

1. **立即开始**: 按照部署文档配置AMF-Placer环境
2. **熟悉代码**: 重点研究PlacementInfo.h和GlobalPlacer.cc
3. **实现算法**: 扩展现有框架添加feedthrough和whitespace计算
4. **集成测试**: 使用OpenPiton等数据集验证效果
5. **性能对比**: 与现有HPWL指标进行correlation分析

通过这种方式，您的质量评估算法将seamlessly集成到AMF-Placer中，充分利用其成熟的框架和优化引擎！
