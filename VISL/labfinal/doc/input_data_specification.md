# 输入数据规范

## 1. 数据组织结构

### 1.1 核心数据张量

DREAMPlace使用PyTorch张量组织所有输入数据，采用扁平化存储结构以提高GPU访问效率：

```python
class PlaceDataCollection:
    # 位置数据
    pos: torch.Tensor[2 * num_nodes]      # 节点位置坐标
  
    # 几何信息  
    node_size_x: torch.Tensor[num_nodes]  # 节点宽度
    node_size_y: torch.Tensor[num_nodes]  # 节点高度
    pin_offset_x: torch.Tensor[num_pins]  # 引脚x偏移
    pin_offset_y: torch.Tensor[num_pins]  # 引脚y偏移
  
    # 连接信息
    flat_net2pin_map: torch.Tensor[total_pins]        # 网线-引脚映射
    flat_net2pin_start_map: torch.Tensor[num_nets+1]  # 网线起始索引
    pin2node_map: torch.Tensor[num_pins]              # 引脚-节点映射
    pin2net_map: torch.Tensor[num_pins]               # 引脚-网线映射
  
    # 权重信息
    net_weights: torch.Tensor[num_nets]   # 网线权重
    net_mask: torch.Tensor[num_nets]      # 网线掩码
```

### 1.2 节点索引组织

```python
# 节点类型分布
节点索引范围                          节点类型                 移动性
[0, num_movable_nodes)               可移动模块               可移动
[num_movable_nodes,                  固定模块/IO端口          固定
 num_physical_nodes)  
[num_physical_nodes, num_nodes)      填充节点                 可移动
```

## 2. 位置数据 (pos)

### 2.1 数据格式

```python
pos: torch.Tensor[2 * num_nodes]
pos[0:num_nodes]              # 所有节点的x坐标（左下角）
pos[num_nodes:2*num_nodes]    # 所有节点的y坐标（左下角）
```

### 2.2 坐标含义

- **坐标定义**: (x, y)表示模块的**左下角坐标**
- **坐标系**: 以芯片左下角为原点(0,0)，x轴向右，y轴向上
- **单位**: 与输入文件保持一致（通常为微米或数据库单位）

### 2.3 输入来源

#### Bookshelf格式 (.pl文件)

```
UCLA pl 1.0
# 节点名 x坐标 y坐标 : 方向
sb0 100 200 : N
sb1 300 150 : N  
p1 0 500 : N FIXED    # 固定IO端口
```

#### DEF格式

```verilog
COMPONENTS 100 ;
- inst1 cell_type + PLACED ( 1000 2000 ) N ;
- inst2 cell_type + FIXED ( 3000 1500 ) S ;
END COMPONENTS
```

## 3. 几何信息

### 3.1 节点尺寸

```python
node_size_x[i]: float  # 节点i的宽度
node_size_y[i]: float  # 节点i的高度
```

#### 输入来源 (.blocks文件)

**硬模块**:

```
bk1 hardrectilinear 4 (0,0) (0,133) (336,133) (336,0)
# 模块名 类型 顶点数 顶点坐标序列
# 从顶点坐标计算得到: width=336, height=133
```

**软模块**:

```
sb0 softrectangular 16318 0.300 3.000
# 模块名 类型 面积 最小长宽比 最大长宽比
# 算法会自动确定最优的width和height
```

**IO端口**:

```
p1 terminal
# IO端口通常尺寸为0或很小的固定值
```

### 3.2 引脚偏移

```python
pin_offset_x[pin_id]: float  # 引脚相对节点左下角的x偏移
pin_offset_y[pin_id]: float  # 引脚相对节点左下角的y偏移
```

#### 输入来源 (.nets文件)

```
NetDegree : 3 net1
sb0 I : 10 20     # sb0的输入引脚，偏移量(10, 20)
sb1 O : 50 25     # sb1的输出引脚，偏移量(50, 25)  
p1 I              # IO端口，默认偏移量(0, 0)
```

#### 引脚坐标计算

```python
# 引脚绝对坐标 = 节点坐标 + 引脚偏移
pin_x = node_x + pin_offset_x
pin_y = node_y + pin_offset_y
```

## 4. 连接性信息

### 4.1 扁平化存储结构

为了提高GPU访问效率，连接信息采用**扁平化存储**：

```python
# 传统的二维列表存储（低效）
net2pin_map = [
    [pin0, pin1, pin2],        # net0的引脚列表
    [pin3, pin4],              # net1的引脚列表  
    [pin5, pin6, pin7, pin8]   # net2的引脚列表
]

# 扁平化存储（高效）
flat_net2pin_map = [pin0, pin1, pin2, pin3, pin4, pin5, pin6, pin7, pin8]
flat_net2pin_start_map = [0, 3, 5, 9]  # 每个网线的起始索引
```

### 4.2 网线-引脚映射

```python
flat_net2pin_map: torch.Tensor[total_pins]        # 所有引脚ID的连续存储
flat_net2pin_start_map: torch.Tensor[num_nets+1]  # 每个网线的起始索引

# 获取网线i的所有引脚
def get_net_pins(net_i):
    start = flat_net2pin_start_map[net_i]
    end = flat_net2pin_start_map[net_i + 1]
    return flat_net2pin_map[start:end]
```

### 4.3 引脚-节点/网线映射

```python
pin2node_map[pin_id]: int  # 引脚pin_id属于哪个节点
pin2net_map[pin_id]: int   # 引脚pin_id属于哪个网线
```

### 4.4 输入来源 (.nets文件)

```
UCLA nets 1.0
NumNets : 50      # 网线数量
NumPins : 150     # 引脚数量

NetDegree : 3 net1    # net1连接3个引脚
sb0 I                 # 连接sb0的输入引脚
sb1 O                 # 连接sb1的输出引脚
sb2 I                 # 连接sb2的输入引脚

NetDegree : 2 net2    # net2连接2个引脚  
sb1 O
p1 I
```

### 4.5 网线权重和掩码

```python
net_weights[net_i]: float      # 网线重要性权重（默认1.0）
net_mask[net_i]: bool         # 是否参与评估（True=参与，False=忽略）
```

#### 权重输入 (.wts文件，可选)

```
net1 2.5    # net1权重为2.5（重要网线）
net2 1.0    # net2权重为1.0（普通网线）
net3 0.1    # net3权重为0.1（次要网线）
```

#### 掩码规则

```python
# 自动生成掩码规则
if net_degree >= 2 and net_degree < ignore_net_degree:
    net_mask[i] = True   # 参与评估
else:
    net_mask[i] = False  # 忽略单引脚网线和超大度数网线
```

## 5. 布局区域信息

### 5.1 芯片边界

```python
xl, yl: float   # 芯片左下角坐标
xh, yh: float   # 芯片右上角坐标
```

### 5.2 输入来源 (.scl文件)

```
UCLA scl 1.0
NumRows : 10

CoreRow Horizontal
  Coordinate    : 0       # 行的y坐标  
  Height        : 100     # 行高
  Sitewidth     : 1       # 位点宽度
  Sitespacing   : 1       # 位点间距
  Siteorient    : N       # 位点方向
  Subrows       : 1000 0  # 子行长度和起始x坐标
End

# 从所有行信息计算芯片边界
xl = min(所有行的起始x坐标)
xh = max(所有行的结束x坐标) 
yl = min(所有行的y坐标)
yh = max(所有行的y坐标 + 行高)
```

### 5.3 密度评估网格

```python
num_bins_x: int          # x方向网格数量
num_bins_y: int          # y方向网格数量  
bin_size_x: float        # 网格x方向尺寸 = (xh-xl)/num_bins_x
bin_size_y: float        # 网格y方向尺寸 = (yh-yl)/num_bins_y
target_density: float    # 目标密度 [0.0, 1.0]
```

#### 配置方式 (JSON参数文件)

```json
{
    "num_bins_x": 32,
    "num_bins_y": 32, 
    "target_density": 0.8,
    "density_weight": 8e-5
}
```

## 6. 器件约束信息

### 6.1 行列约束

```python
site_width: float     # 标准单元位点宽度
row_height: float     # 标准单元行高
num_sites_x: int      # x方向总位点数  
num_sites_y: int      # y方向总行数
```

### 6.2 围栏区域约束

```python
flat_region_boxes: torch.Tensor[num_regions * 4]      # 区域边界[xl,yl,xh,yh,...]
flat_region_boxes_start: torch.Tensor[num_regions+1]  # 区域起始索引
node2fence_region_map: torch.Tensor[num_movable_nodes] # 节点到区域映射
```

#### 输入来源 (.regions文件，可选)

```
UCLA regions 1.0
NumRegions : 2

Region region1
  4           # 矩形区域，4个顶点
  0 0         # 左下角
  100 0       # 右下角  
  100 100     # 右上角
  0 100       # 左上角
End

Group group1
  region1     # 约束区域
  sb0 sb1     # 被约束的模块
End
```

## 7. 数据验证和预处理

### 7.1 输入验证

```python
def validate_input_data():
    # 检查张量维度一致性
    assert pos.size(0) == 2 * num_nodes
    assert node_size_x.size(0) == num_nodes
    assert pin2node_map.max() < num_nodes
    assert pin2net_map.max() < num_nets
  
    # 检查坐标边界
    assert (pos >= 0).all()
    assert pos[:num_nodes].max() <= xh  # x坐标检查
    assert pos[num_nodes:].max() <= yh  # y坐标检查
```

### 7.2 数据预处理

```python
def preprocess_data():
    # 坐标归一化（可选）
    if params.normalize_coordinates:
        pos[:num_nodes] /= (xh - xl)      # x坐标归一化
        pos[num_nodes:] /= (yh - yl)      # y坐标归一化
  
    # 网线过滤
    net_mask = (net_degrees >= 2) & (net_degrees < ignore_net_degree)
  
    # 数据类型转换
    pos = pos.to(device=device, dtype=dtype)
```

这种数据组织方式确保了算法的高效性和可扩展性，同时保持了与标准EDA格式的兼容性。
