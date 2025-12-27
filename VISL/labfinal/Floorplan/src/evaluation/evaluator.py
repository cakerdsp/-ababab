#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一评估器接口 - Unified Evaluator Interface

真正用于指导优化过程的评估算法
Real evaluation algorithms that guide the optimization process

作者: PyFloorplan Team
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import time
import numpy as np

try:
    from ..data.structures import FloorplanDesign, EvaluationResult
except ImportError:
    from data.structures import FloorplanDesign, EvaluationResult


# EvaluationResult已移至data.structures避免重复定义


class FloorplanEvaluator(ABC):
    """
    布图评估器抽象基类 - Floorplan Evaluator Abstract Base Class
    
    定义评估器接口，用于在优化过程中评估解的质量
    Defines evaluator interface for assessing solution quality during optimization
    """
    
    def __init__(self, name: str):
        self.name = name
        self.evaluation_count = 0
        self.total_evaluation_time = 0.0
        
    @abstractmethod
    def evaluate(self, design: FloorplanDesign) -> float:
        """
        快速评估，返回单一代价值（用于优化循环）
        Fast evaluation returning single cost value (for optimization loop)
        """
        pass
    
    @abstractmethod
    def detailed_evaluate(self, design: FloorplanDesign) -> EvaluationResult:
        """
        详细评估，返回完整结果（用于分析）
        Detailed evaluation returning comprehensive results (for analysis)
        """
        pass
    
    def self_check(self) -> bool:
        """
        自检功能 - Self-check functionality
        验证评估器是否正确实现
        """
        try:
            # 创建简单测试设计
            test_design = self._create_test_design()
            
            # 测试快速评估
            start_time = time.time()
            cost = self.evaluate(test_design)
            evaluation_time = time.time() - start_time
            
            # 验证返回值
            if not isinstance(cost, (int, float)) or cost < 0:
                print(f"❌ {self.name}: evaluate() 返回无效值: {cost}")
                return False
            
            # 测试详细评估
            result = self.detailed_evaluate(test_design)
            if not isinstance(result, EvaluationResult):
                print(f"❌ {self.name}: detailed_evaluate() 返回类型错误")
                return False
            
            print(f"✅ {self.name}: 自检通过")
            print(f"   - 快速评估: {cost:.2f} (耗时: {evaluation_time:.4f}s)")
            print(f"   - 详细评估: 包含 {len(result.__dict__)} 个指标")
            return True
            
        except Exception as e:
            print(f"❌ {self.name}: 自检失败: {e}")
            return False
    
    def _create_test_design(self) -> FloorplanDesign:
        """创建简单的测试设计"""
        try:
            from ..data.structures import Module, Net, ModuleType, Pin
        except ImportError:
            from data.structures import Module, Net, ModuleType, Pin
        
        design = FloorplanDesign("test_design")
        
        # 添加几个测试模块
        module1 = Module("m1", ModuleType.SOFT, width=100, height=100, x=0, y=0, area=10000)
        module2 = Module("m2", ModuleType.SOFT, width=80, height=120, x=150, y=0, area=9600)
        module3 = Module("m3", ModuleType.HARD, width=60, height=60, x=300, y=0, area=3600)
        
        design.add_module(module1)
        design.add_module(module2)
        design.add_module(module3)
        
        # 添加几个测试网线
        net1 = Net("net1", [("m1", "pin1"), ("m2", "pin1")])
        net2 = Net("net2", [("m2", "pin2"), ("m3", "pin1")])
        net3 = Net("net3", [("m1", "pin2"), ("m3", "pin2")])
        
        design.add_net(net1)
        design.add_net(net2)
        design.add_net(net3)
        
        return design
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取评估器统计信息"""
        return {
            'name': self.name,
            'evaluation_count': self.evaluation_count,
            'total_evaluation_time': self.total_evaluation_time,
            'avg_evaluation_time': self.total_evaluation_time / max(1, self.evaluation_count)
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.evaluation_count = 0
        self.total_evaluation_time = 0.0


class ComprehensiveEvaluator(FloorplanEvaluator):
    """
    综合评估器 - Comprehensive Evaluator
    
    集成所有评估模块的完整评估器，支持动态归一化
    Complete evaluator with dynamic normalization for robust optimization
    """
    
    def __init__(self, 
                 area_weight: float = 0.15,
                 wirelength_weight: float = 0.35, 
                 feedthrough_count_weight: float = 0.15,        # 🎯 分离：feedthrough数量权重
                 feedthrough_wirelength_weight: float = 0.10,   # 🎯 分离：feedthrough线长权重
                 whitespace_weight: float = 0.1,
                 legality_weight: float = 0.15,
                 verbose: bool = False,
                 calibration_samples: int = 50,
                 feedthrough_method: str = "original"):
        """
        初始化综合评估器
        
        Args:
            area_weight: 面积权重
            wirelength_weight: 线长权重  
            feedthrough_count_weight: Feedthrough数量权重
            feedthrough_wirelength_weight: Feedthrough线长权重
            whitespace_weight: 空白区域权重
            legality_weight: 合法性权重
            verbose: 是否详细输出
            calibration_samples: 校准阶段样本数量
            feedthrough_method: feedthrough计算方法 ('original' | 'ftafp')
        """
        super().__init__("ComprehensiveEvaluator")
        
        # 🎯 权重配置 - 分离feedthrough数量和线长权重
        self.weights = {
            'area': area_weight,
            'wirelength': wirelength_weight,
            'feedthrough_count': feedthrough_count_weight,
            'feedthrough_wirelength': feedthrough_wirelength_weight,
            'whitespace': whitespace_weight,
            'legality': legality_weight
        }
        
        # 归一化权重
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v/total_weight for k, v in self.weights.items()}
        
        self.verbose = verbose
        self.calibration_samples = calibration_samples
        
        # 🎯 Feedthrough模块选择配置
        self.feedthrough_method = feedthrough_method.lower()
        if self.feedthrough_method not in ['original', 'ftafp']:
            print(f"警告: 不支持的feedthrough方法 '{feedthrough_method}', 使用默认'original'")
            self.feedthrough_method = 'original'
        
        if self.verbose:
            print(f"Feedthrough计算方法: {self.feedthrough_method}")
        
        # 动态归一化 - 关键改进！
        self.is_calibrated = False
        self.normalization_factors = {
            'area': 1.0,
            'wirelength': 1.0,
            'feedthrough': 1.0,
            'feedthrough_wirelength': 1.0,  # 🎯 新增：feedthrough线长归一化因子
            'whitespace': 1.0,
            'legality': 1.0
        }
        
        # 校准统计信息
        self.calibration_stats = {}
        
        # 延迟导入避免循环依赖
        self._metrics_module = None
        self._wirelength_module = None
        self._feedthrough_module = None
        self._ftafp_module = None  # 🎯 新增：FTAFP模块
        self._whitespace_module = None
        self._legality_module = None
        self._legality_checker = None
    
    def _import_modules(self):
        """延迟导入评估模块"""
        if self._metrics_module is None:
            try:
                from . import metrics as _metrics_module
                from . import wirelength as _wirelength_module
                from . import feedthrough as _feedthrough_module
                from . import FTAFP_feedthrough as _ftafp_module  # 🎯 新增：导入FTAFP模块
                from . import whitespace as _whitespace_module
                from . import legality as _legality_module
            except ImportError:
                import evaluation.metrics as _metrics_module
                import evaluation.wirelength as _wirelength_module
                import evaluation.feedthrough as _feedthrough_module
                import evaluation.FTAFP_feedthrough as _ftafp_module  # 🎯 新增：导入FTAFP模块
                import evaluation.whitespace as _whitespace_module
                import evaluation.legality as _legality_module
            
            self._metrics_module = _metrics_module
            self._wirelength_module = _wirelength_module
            self._feedthrough_module = _feedthrough_module
            self._ftafp_module = _ftafp_module  # 🎯 新增：保存FTAFP模块
            self._whitespace_module = _whitespace_module
            self._legality_module = _legality_module
            
            # 创建合法性检查器 - 与零容忍检查器保持一致
            if self._legality_checker is None:
                self._legality_checker = self._legality_module.create_legality_checker(enable_all=True)
    
    def _calculate_feedthrough_metrics(self, design) -> tuple:
        """
        🎯 计算feedthrough指标 - 根据配置选择不同的计算方法
        
        Returns:
            tuple: (feedthrough_count, feedthrough_wirelength)
        """
        if self.feedthrough_method == 'ftafp':
            # 使用FTAFP方法
            ftafp_result = self._ftafp_module.calculate_ftafp_feedthrough(design)
            return ftafp_result.total_feedthrough_number, ftafp_result.total_feedthrough_wirelength
        else:
            # 使用原始方法 (兼容性：线长默认为0)
            feedthrough_count = self._feedthrough_module.calculate_feedthrough_count(design)
            return feedthrough_count, 0.0
    
    def calibrate(self, representation_method, design: FloorplanDesign) -> Dict[str, float]:
        """
        校准阶段 - 动态计算归一化因子
        Calibration phase - dynamically compute normalization factors
        
        这是解决归一化问题的核心方法！
        Core method to solve the normalization problem!
        
        Args:
            representation_method: 表示方法对象
            design: 布图设计
            
        Returns:
            校准统计信息
        """
        if self.verbose:
            print(f"开始动态归一化校准阶段 (样本数: {self.calibration_samples})")
        
        self._import_modules()
        
        # 校准数据收集
        area_samples = []
        wirelength_samples = []
        feedthrough_samples = []
        feedthrough_wirelength_samples = []  # 🎯 新增：feedthrough线长样本
        whitespace_samples = []
        legality_samples = []
        
        # 初始化表示方法
        representation_method.initialize(design)
        
        # 生成随机样本
        for i in range(self.calibration_samples):
            try:
                # 生成随机解
                random_repr = representation_method.random_solution()
                
                # 解码为设计
                random_design = representation_method.decode(random_repr)
                
                # 计算各项指标
                area = self._metrics_module.calculate_area(random_design)
                wirelength = self._wirelength_module.calculate_hpwl(random_design)
                feedthrough_count, feedthrough_wirelength = self._calculate_feedthrough_metrics(random_design)
                whitespace_ratio = self._whitespace_module.calculate_whitespace_ratio(random_design)
                legality_penalty = self._legality_checker.calculate_penalty(random_design)
                
                # 收集样本
                if area > 0:  # 只收集有效样本
                    area_samples.append(area)
                    wirelength_samples.append(wirelength)
                    feedthrough_samples.append(feedthrough_count)
                    feedthrough_wirelength_samples.append(feedthrough_wirelength)  # 🎯 新增：收集线长样本
                    whitespace_samples.append(whitespace_ratio)
                    legality_samples.append(legality_penalty)
                
                if self.verbose and (i + 1) % 10 == 0:
                    print(f"  校准进度: {i+1}/{self.calibration_samples}")
                    
            except Exception as e:
                if self.verbose:
                    print(f"  校准样本 {i} 失败: {e}")
                continue
        
        # 计算归一化因子（使用平均值）
        if area_samples:
            self.normalization_factors['area'] = np.mean(area_samples)
            self.normalization_factors['wirelength'] = np.mean(wirelength_samples)
            self.normalization_factors['feedthrough'] = max(np.mean(feedthrough_samples), 1.0)
            self.normalization_factors['feedthrough_wirelength'] = max(np.mean(feedthrough_wirelength_samples), 1.0)  # 🎯 新增
            self.normalization_factors['whitespace'] = max(np.mean(whitespace_samples), 0.1)
            self.normalization_factors['legality'] = max(np.mean(legality_samples), 1.0)
        else:
            print("警告: 校准样本收集失败，使用默认归一化因子")
            # 使用默认归一化因子
            self.normalization_factors = {
                'area': 100000.0,
                'wirelength': 50000.0,
                'feedthrough': 10.0,
                'feedthrough_wirelength': 10000.0,  # 🎯 新增：默认线长归一化因子
                'whitespace': 0.5,
                'legality': 1000.0
            }
        
        # 记录校准统计
        self.calibration_stats = {
            'samples_collected': len(area_samples),
            'target_samples': self.calibration_samples,
            'normalization_factors': self.normalization_factors.copy(),
            'sample_ranges': {
                'area': (min(area_samples), max(area_samples)) if area_samples else (0, 0),
                'wirelength': (min(wirelength_samples), max(wirelength_samples)) if wirelength_samples else (0, 0),
                'feedthrough': (min(feedthrough_samples), max(feedthrough_samples)) if feedthrough_samples else (0, 0),
                'feedthrough_wirelength': (min(feedthrough_wirelength_samples), max(feedthrough_wirelength_samples)) if feedthrough_wirelength_samples else (0, 0),  # 🎯 新增
                'whitespace': (min(whitespace_samples), max(whitespace_samples)) if whitespace_samples else (0, 0),
                'legality': (min(legality_samples), max(legality_samples)) if legality_samples else (0, 0)
            }
        }
        
        self.is_calibrated = True
        
        if self.verbose:
            print(f"校准完成! 归一化因子:")
            for metric, factor in self.normalization_factors.items():
                print(f"   {metric}: {factor:.2f}")
        
        return self.calibration_stats

    def evaluate(self, design: FloorplanDesign) -> float:
        """
        快速评估 - 用于优化循环
        Fast evaluation for optimization loop
        
        使用动态归一化确保权重系统有效性
        Uses dynamic normalization to ensure weight system effectiveness
        """
        start_time = time.time()
        
        try:
            self._import_modules()
            
            # 注意：校准功能可选，系统使用默认归一化因子也能正常工作
            
            # 计算基础指标
            area = self._metrics_module.calculate_area(design)
            wirelength = self._wirelength_module.calculate_hpwl(design)
            feedthrough_count, feedthrough_wirelength = self._calculate_feedthrough_metrics(design)
            whitespace_ratio = self._whitespace_module.calculate_whitespace_ratio(design)
            
            # 确保芯片边界与设计一致
            if hasattr(design, 'chip_width') and hasattr(design, 'chip_height'):
                if design.chip_width > 0 and design.chip_height > 0:
                    # 更新合法性检查器的芯片边界
                    self._legality_checker.constraints.chip_boundary = (0, 0, design.chip_width, design.chip_height)
                else:
                    # 如果设计没有设置芯片尺寸，暂时禁用边界检查
                    self._legality_checker.constraints.enable_boundary_check = False
            else:
                # 如果设计没有芯片尺寸属性，禁用边界检查
                self._legality_checker.constraints.enable_boundary_check = False
            
            # 计算合法性惩罚
            legality_penalty = self._legality_checker.calculate_penalty(design)
            
            # 动态归一化 - 关键改进！
            normalized_area = area / self.normalization_factors['area']
            normalized_wirelength = wirelength / self.normalization_factors['wirelength']
            normalized_whitespace = whitespace_ratio / self.normalization_factors['whitespace']
            normalized_legality = legality_penalty / self.normalization_factors['legality']
            
            # 🎯 Feedthrough归一化 - 分别计算数量和线长
            normalized_feedthrough_count = feedthrough_count / self.normalization_factors['feedthrough']
            normalized_feedthrough_wl = feedthrough_wirelength / self.normalization_factors['feedthrough_wirelength']
            
            # 🎯 计算加权总代价 - 分别使用数量和线长权重
            feedthrough_cost = (
                self.weights['feedthrough_count'] * normalized_feedthrough_count +
                self.weights['feedthrough_wirelength'] * normalized_feedthrough_wl
            )
            
            total_cost = (
                self.weights['area'] * normalized_area +
                self.weights['wirelength'] * normalized_wirelength +
                feedthrough_cost +
                self.weights['whitespace'] * normalized_whitespace +
                self.weights['legality'] * normalized_legality
            )
            
            # 更新统计
            self.evaluation_count += 1
            self.total_evaluation_time += time.time() - start_time
            
            if self.verbose and self.evaluation_count % 100 == 0:
                print(f"   评估#{self.evaluation_count}: 总代价={total_cost:.4f} [方法:{self.feedthrough_method}]")
                if self.feedthrough_method == 'ftafp':
                    print(f"     面积={normalized_area:.3f}, 线长={normalized_wirelength:.3f}, "
                          f"FT数量={normalized_feedthrough_count:.3f}({feedthrough_count}), "
                          f"FT线长={normalized_feedthrough_wl:.3f}({feedthrough_wirelength:.0f}), "
                          f"空白={normalized_whitespace:.3f}, 合法性={normalized_legality:.3f}")
                else:
                    print(f"     面积={normalized_area:.3f}, 线长={normalized_wirelength:.3f}, "
                          f"FT数量={normalized_feedthrough_count:.3f}({feedthrough_count}), "
                          f"FT线长={normalized_feedthrough_wl:.3f}(N/A), "
                          f"空白={normalized_whitespace:.3f}, 合法性={normalized_legality:.3f}")
            
            return total_cost
            
        except Exception as e:
            print(f"警告: 评估过程出错: {e}")
            return float('inf')  # 返回无穷大作为惩罚
    
    def detailed_evaluate(self, design: FloorplanDesign) -> EvaluationResult:
        """
        详细评估 - 用于分析和报告
        Detailed evaluation for analysis and reporting
        """
        start_time = time.time()
        
        try:
            self._import_modules()
            
            # 基础指标
            area = self._metrics_module.calculate_area(design)
            hpwl = self._wirelength_module.calculate_hpwl(design)
            rmst = self._wirelength_module.calculate_rmst(design)
            feedthrough_count, feedthrough_wirelength = self._calculate_feedthrough_metrics(design)
            whitespace_ratio = self._whitespace_module.calculate_whitespace_ratio(design)
            
            # 高级分析
            wl_calculator = self._wirelength_module.WirelengthCalculator(method='hpwl')
            ft_analyzer = self._feedthrough_module.FeedthroughAnalyzer()
            ws_analyzer = self._whitespace_module.WhitespaceAnalyzer()
            
            wl_result = wl_calculator.detailed_analysis(design)
            ft_result = ft_analyzer.analyze(design)
            ws_result = ws_analyzer.analyze(design)
            
            # 🔧 **统一合法性检查**: 使用专业的legality.py系统
            from .legality import ComprehensiveLegalityChecker, LegalityConstraints
            
            # 创建与算法中相同配置的合法性检查器
            legality_constraints = LegalityConstraints(
                enable_overlap_check=True,
                enable_boundary_check=True,
                enable_spacing_check=False,
                enable_alignment_check=False,
                enable_keepout_check=False,
                overlap_penalty_weight=10000.0,
                boundary_penalty_weight=1000.0
            )
            unified_checker = ComprehensiveLegalityChecker(legality_constraints)
            
            # 确保边界设置正确
            if hasattr(design, 'chip_width') and hasattr(design, 'chip_height'):
                if design.chip_width > 0 and design.chip_height > 0:
                    unified_checker.constraints.chip_boundary = (0, 0, design.chip_width, design.chip_height)
                    if self.verbose:
                        print(f"  评估器: 使用设计芯片尺寸 {design.chip_width} x {design.chip_height}")
                        print(f"  设计模块数量: {len(design.modules)}")
                else:
                    if self.verbose:
                        print(f"  警告：设计芯片尺寸无效({design.chip_width} x {design.chip_height})")
            else:
                if self.verbose:
                    print(f"  警告：设计缺少芯片尺寸属性")
            
            # 使用统一的合法性检查
            legality_result = unified_checker.check_legality(design)
            
            if self.verbose:
                print(f"  评估器合法性结果: {'合法' if legality_result.is_legal else '不合法'}, 违规: {legality_result.total_violations}")
                if not legality_result.is_legal:
                    print(f"    重叠违规: {legality_result.overlap_violations}")
                    print(f"    边界违规: {legality_result.boundary_violations}")
            
            # 拥塞分析
            congestion_map = wl_calculator.get_congestion_map(design)
            max_congestion = float(congestion_map.max()) if congestion_map.size > 0 else 0.0
            
            # 计算严重feedthrough
            severe_ft_count = sum(1 for path in ft_result.feedthrough_paths if path.severity > 2.0)
            
            # 🎯 归一化指标 - 分别计算feedthrough数量和线长
            if area > 0:
                normalized_wirelength = hpwl / area
                normalized_feedthrough_count = feedthrough_count / max(len(design.nets), 1)
                normalized_feedthrough_wirelength = feedthrough_wirelength / max(area, 1)  # 基于面积归一化
                normalized_whitespace = whitespace_ratio
                normalized_congestion = max_congestion / 100.0  # 假设最大拥塞为100
                normalized_legality = legality_result.total_penalty / 10000.0
            else:
                normalized_wirelength = 0.0
                normalized_feedthrough_count = 0.0
                normalized_feedthrough_wirelength = 0.0
                normalized_whitespace = 0.0
                normalized_congestion = 0.0
                normalized_legality = legality_result.total_penalty / 10000.0
            
            # 🎯 计算总代价 - 分别使用feedthrough数量和线长权重
            feedthrough_total_cost = (
                self.weights['feedthrough_count'] * normalized_feedthrough_count +
                self.weights['feedthrough_wirelength'] * normalized_feedthrough_wirelength
            )
            
            total_cost = (
                self.weights['area'] * (area / 1000000) +
                self.weights['wirelength'] * normalized_wirelength +
                feedthrough_total_cost +
                self.weights['whitespace'] * normalized_whitespace +
                self.weights['legality'] * normalized_legality
            )
            
            evaluation_time = time.time() - start_time
            
            return EvaluationResult(
                total_cost=total_cost,
                wirelength=hpwl,
                feedthrough_count=feedthrough_count,
                feedthrough_wirelength=feedthrough_wirelength,  # 🎯 新增：包含feedthrough线长
                area=area,
                whitespace_ratio=whitespace_ratio,
                hpwl=hpwl,
                rmst=rmst,
                max_congestion=max_congestion,
                severe_feedthrough_count=severe_ft_count,
                fragmentation_index=ws_result.fragmentation_index,
                is_legal=legality_result.is_legal,
                legality_penalty=legality_result.total_penalty,
                violation_count=legality_result.total_violations,
                overlap_violations=legality_result.overlap_violations,
                boundary_violations=legality_result.boundary_violations,
                normalized_wirelength=normalized_wirelength,
                normalized_feedthrough_count=normalized_feedthrough_count,        # 🎯 分离字段
                normalized_feedthrough_wirelength=normalized_feedthrough_wirelength, # 🎯 分离字段
                normalized_whitespace=normalized_whitespace,
                normalized_congestion=normalized_congestion,
                normalized_legality=normalized_legality,
                weights=self.weights.copy(),
                evaluation_time=evaluation_time
            )
            
        except Exception as e:
            print(f"详细评估失败: {e}")
            return EvaluationResult(
                total_cost=float('inf'),
                wirelength=0.0,
                feedthrough_count=0,
                area=0.0,
                whitespace_ratio=0.0,
                evaluation_time=time.time() - start_time
            )
    
    def output_debug_info(self, design: FloorplanDesign, prefix: str = "") -> str:
        """
        输出调试信息 - 在各自模块中实现
        Output debug information - implemented in respective modules
        """
        result = self.detailed_evaluate(design)
        
        debug_info = f"{prefix}=== 综合评估器调试信息 ===\n"
        debug_info += f"{prefix}总代价: {result.total_cost:.6f}\n"
        debug_info += f"{prefix}权重配置: {result.weights}\n"
        debug_info += f"{prefix}原始指标:\n"
        debug_info += f"{prefix}  - 面积: {result.area:.0f}\n"
        debug_info += f"{prefix}  - HPWL: {result.hpwl:.0f}\n" 
        if self.feedthrough_method == 'ftafp':
            debug_info += f"{prefix}  - Feedthrough: {result.feedthrough_count} (线长: {result.feedthrough_wirelength:.0f})\n"
        else:
            debug_info += f"{prefix}  - Feedthrough: {result.feedthrough_count}\n"
        debug_info += f"{prefix}  - 空白比例: {result.whitespace_ratio:.3f}\n"
        debug_info += f"{prefix}  - 合法性: {'合法' if result.is_legal else '不合法'}\n"
        debug_info += f"{prefix}  - 违规数量: {result.violation_count}\n"
        debug_info += f"{prefix}  - 合法性惩罚: {result.legality_penalty:.2f}\n"
        debug_info += f"{prefix}归一化指标:\n"
        debug_info += f"{prefix}  - 线长: {result.normalized_wirelength:.6f}\n"
        debug_info += f"{prefix}  - Feedthrough数量: {result.normalized_feedthrough_count:.6f}\n"
        debug_info += f"{prefix}  - Feedthrough线长: {result.normalized_feedthrough_wirelength:.6f}\n"
        debug_info += f"{prefix}  - 空白: {result.normalized_whitespace:.6f}\n"
        debug_info += f"{prefix}  - 拥塞: {result.normalized_congestion:.6f}\n"
        debug_info += f"{prefix}  - 合法性: {result.normalized_legality:.6f}\n"
        debug_info += f"{prefix}评估耗时: {result.evaluation_time:.4f}s\n"
        
        return debug_info
    
    def update_weights(self, **new_weights):
        """更新权重配置"""
        for key, value in new_weights.items():
            if key in self.weights:
                self.weights[key] = value
        
        # 重新归一化
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v/total_weight for k, v in self.weights.items()}
        
        if self.verbose:
            print(f"更新权重: {self.weights}")


class FastEvaluator(FloorplanEvaluator):
    """
    快速评估器 - Fast Evaluator
    
    只计算最关键的指标，用于需要极高速度的场景
    Only computes most critical metrics for high-speed scenarios
    """
    
    def __init__(self, wirelength_weight: float = 0.7, feedthrough_weight: float = 0.3):
        super().__init__("FastEvaluator")
        self.wirelength_weight = wirelength_weight
        self.feedthrough_weight = feedthrough_weight
    
    def evaluate(self, design: FloorplanDesign) -> float:
        """超快速评估"""
        start_time = time.time()
        
        try:
            # 只计算最关键的两个指标
            from .metrics import calculate_wirelength
            from .feedthrough import calculate_feedthrough_count
            
            wirelength = calculate_wirelength(design, method="hpwl")
            feedthrough_count = calculate_feedthrough_count(design)
            
            # 简单归一化
            total_area = sum(m.area for m in design.modules.values())
            normalized_wl = wirelength / max(total_area, 1)
            normalized_ft = feedthrough_count / max(len(design.nets), 1)
            
            cost = self.wirelength_weight * normalized_wl + self.feedthrough_weight * normalized_ft
            
            self.evaluation_count += 1
            self.total_evaluation_time += time.time() - start_time
            
            return cost
            
        except Exception as e:
            return float('inf')
    
    def detailed_evaluate(self, design: FloorplanDesign) -> EvaluationResult:
        """简化的详细评估"""
        cost = self.evaluate(design)
        
        from .metrics import calculate_area, calculate_wirelength
        from .feedthrough import calculate_feedthrough_count
        
        return EvaluationResult(
            total_cost=cost,
            wirelength=calculate_wirelength(design, method="hpwl"),
            feedthrough_count=calculate_feedthrough_count(design),
            area=calculate_area(design),
            whitespace_ratio=0.0,  # 不计算
            weights={'wirelength': self.wirelength_weight, 'feedthrough': self.feedthrough_weight}
        )


def create_evaluator(evaluator_type: str = "comprehensive", **kwargs) -> FloorplanEvaluator:
    """
    评估器工厂函数 - Evaluator factory function
    
    Args:
        evaluator_type: 评估器类型 ("comprehensive", "fast")
        **kwargs: 评估器参数
        
    Returns:
        评估器实例
    """
    if evaluator_type == "comprehensive":
        return ComprehensiveEvaluator(**kwargs)
    elif evaluator_type == "fast":
        return FastEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# 导出主要类和函数
__all__ = [
    'FloorplanEvaluator',
    'ComprehensiveEvaluator',
    'FastEvaluator',
    'EvaluationResult',
    'create_evaluator'
] 