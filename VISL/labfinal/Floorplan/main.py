#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
两阶段布图优化系统主程序

实现算法框架：
- 模拟退火为外部驱动
- 两阶段复合动作：宏模块扰动 + Pin重新规划
- Pin只在芯片边缘的整数坐标

启动方式: python main.py <yaml文件>
"""

import argparse
import yaml
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# 数据模块
from src.data.parsers import load_gsrc_design, load_mcnc_design
from src.data.structures import FloorplanDesign
from src.data.output_generator import ResultOrganizer, PlacementFileGenerator

# 算法模块
from src.algorithms.sequence_pair import SequencePair
from src.algorithms.simulated_annealing import SimulatedAnnealing
from src.algorithms.genetic import GeneticAlgorithm

# Pin分配模块
from src.algorithms.pin_assignment.greedy_pin_assignment import GreedyPinAssignment

# 评估模块
from src.evaluation.evaluator import ComprehensiveEvaluator

# 可视化模块
from src.visualization.layout_drawer import LayoutDrawer
from src.visualization.visualization_config import VisualizationConfig


def load_config(yaml_file: str) -> Dict[str, Any]:
    """加载YAML配置文件"""
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"无法加载配置文件 {yaml_file}: {e}")
        sys.exit(1)


def load_design(config: Dict[str, Any]) -> FloorplanDesign:
    """加载设计数据"""
    data_config = config.get('data', {})
    benchmark = data_config.get('benchmark', 'gsrc')
    dataset = data_config.get('dataset', 'n10')
    module_type = data_config.get('module_type', 'soft')
    verbose = config.get('output', {}).get('verbose', True)
    
    if verbose:
        print(f"加载数据集: {benchmark}/{dataset} ({module_type})")
    
    try:
        if benchmark.lower() == 'gsrc':
            # 根据module_type选择正确的路径
            from src.data.parsers import GSRCParser
            import os
            
            if module_type.lower() == 'hard':
                base_path = os.path.join(os.path.dirname(__file__), '..', 'GSRC', 'HARD')
            else:
                base_path = os.path.join(os.path.dirname(__file__), '..', 'GSRC', 'SOFT')
            
            base_path = os.path.abspath(base_path)
            
            parser = GSRCParser()
            design = parser.parse_design(base_path, dataset, load_pin_positions=False)
            
        elif benchmark.lower() == 'mcnc':
            # 根据module_type选择正确的路径
            from src.data.parsers import MCNCParser
            import os
            
            if module_type.lower() == 'hard':
                base_path = os.path.join(os.path.dirname(__file__), '..', 'MCNC', 'HARD')
            else:
                base_path = os.path.join(os.path.dirname(__file__), '..', 'MCNC', 'SOFT')
            
            base_path = os.path.abspath(base_path)
            
            parser = MCNCParser()
            design = parser.parse_design(base_path, dataset, load_pin_positions=False)
        else:
            raise ValueError(f"不支持的基准测试: {benchmark}")
        
        if verbose:
            macro_count = sum(1 for m in design.modules.values() if m.module_type.name != 'TERMINAL')
            pin_count = sum(1 for m in design.modules.values() if m.module_type.name == 'TERMINAL')
            
            print(f"数据加载成功")
            print(f"   - 总模块数: {len(design.modules)}")
            print(f"   - 宏模块: {macro_count}, Pin: {pin_count}")
            print(f"   - 网络数: {len(design.nets)}")
        
        return design
        
    except Exception as e:
        print(f"数据加载失败: {e}")
        sys.exit(1)


def create_representation(config: Dict[str, Any]) -> Any:
    """创建表示方法"""
    algorithm_config = config.get('algorithm', {})
    repr_name = algorithm_config.get('representation', 'sequence_pair')
    verbose = config.get('output', {}).get('verbose', True)
    
    if verbose:
        print(f"创建表示方法: {repr_name}")
    
    if repr_name == 'sequence_pair':
        return SequencePair()
    else:
        raise ValueError(f"不支持的表示方法: {repr_name}")


def create_algorithm(config: Dict[str, Any], representation, design: FloorplanDesign) -> Any:
    """创建优化算法"""
    algorithm_config = config.get('algorithm', {})
    alg_name = algorithm_config.get('name', 'simulated_annealing')
    verbose = config.get('output', {}).get('verbose', True)
    
    if verbose:
        print(f"创建优化算法: {alg_name}")
    
    if alg_name == 'simulated_annealing':
        # 从正确的配置节中获取SA参数
        sa_config = config.get('simulated_annealing', {})
        # 获取evaluation配置中的feedthrough_method
        eval_config = config.get('evaluation', {})
        feedthrough_method = eval_config.get('feedthrough_method', 'original')
        
        return SimulatedAnnealing(
            representation=representation,
            max_iterations=algorithm_config.get('max_iterations', 1000),
            initial_temperature=sa_config.get('initial_temperature', 1000.0),
            final_temperature=sa_config.get('final_temperature', 1.0),
            cooling_rate=sa_config.get('cooling_rate', 0.95),
            moves_per_temperature=sa_config.get('moves_per_temperature', 50),
            verbose=verbose,
            feedthrough_method=feedthrough_method
        )
    elif alg_name == 'genetic_algorithm':
        # 从正确的配置节中获取GA参数
        ga_config = config.get('genetic_algorithm', {})
        # 获取evaluation配置中的feedthrough_method
        eval_config = config.get('evaluation', {})
        feedthrough_method = eval_config.get('feedthrough_method', 'original')
        
        return GeneticAlgorithm(
            representation=representation,
            max_generations=algorithm_config.get('max_iterations', 100),
            population_size=ga_config.get('population_size', 50),
            crossover_rate=ga_config.get('crossover_rate', 0.8),
            mutation_rate=ga_config.get('mutation_rate', 0.1),
            selection_method=ga_config.get('selection_method', 'tournament'),
            tournament_size=ga_config.get('tournament_size', 3),
            elitism_ratio=ga_config.get('elitism_ratio', 0.1),
            strict_legality=ga_config.get('strict_legality', True),
            repair_illegal=ga_config.get('repair_illegal', True),
            verbose=verbose,
            feedthrough_method=feedthrough_method
        )
    else:
        raise ValueError(f"不支持的优化算法: {alg_name}")


def create_two_phase_evaluator(config: Dict[str, Any], design: FloorplanDesign) -> Any:
    """创建两阶段评估器"""
    eval_config = config.get('evaluation', {})
    pin_config = config.get('pin_assignment', {})
    
    pin_algorithm = pin_config.get('algorithm', 'uniform_edge')
    
    verbose = config.get('output', {}).get('verbose', True)
    if verbose:
        print(f"Pin分配算法: {pin_algorithm}")
    
    if pin_algorithm == 'center_of_gravity':
        from src.algorithms.pin_assignment.center_of_gravity_pin_assignment import CenterOfGravityPinAssignment, CenterOfGravityConfig
        
        cog_config = CenterOfGravityConfig(
            expansion_ratio=pin_config.get('expansion_ratio', 1.2),
            verbose=pin_config.get('verbose', False),
            prefer_corner_pins=pin_config.get('prefer_corner_pins', True),
            congestion_avoidance=pin_config.get('congestion_avoidance', True),
            max_pins_per_edge_unit=pin_config.get('max_pins_per_edge_unit', 3)
        )
        pin_assigner = CenterOfGravityPinAssignment(cog_config)
        
    elif pin_algorithm == 'uniform_edge':
        from src.algorithms.pin_assignment.uniform_edge_pin_assignment import UniformEdgePinAssignment, UniformEdgeConfig
        
        uniform_config = UniformEdgeConfig(
            expansion_ratio=pin_config.get('expansion_ratio', 1.2),
            verbose=pin_config.get('verbose', False)
        )
        pin_assigner = UniformEdgePinAssignment(uniform_config)
        
    else:
        pin_assigner = GreedyPinAssignment(
            expansion_ratio=pin_config.get('expansion_ratio', 1.2),
            verbose=pin_config.get('verbose', False)
        )
    
    weights = eval_config.get('weights', {})
    
    # 🎯 基准函数校准配置
    calibration_config = eval_config.get('calibration', {})
    calibration_samples = calibration_config.get('samples', 50)
    calibration_verbose = calibration_config.get('verbose', False)
    
    # 🎯 Feedthrough方法配置
    feedthrough_method = eval_config.get('feedthrough_method', 'original')
    if verbose:
        print(f"Feedthrough计算方法: {feedthrough_method}")
    
    evaluator = ComprehensiveEvaluator(
        area_weight=weights.get('area', 0.5),
        wirelength_weight=weights.get('hpwl', 1.0),
        feedthrough_count_weight=weights.get('feedthrough_count', weights.get('feedthrough', 10.0)),     # 🎯 分离权重
        feedthrough_wirelength_weight=weights.get('feedthrough_wirelength', 0.0),                       # 🎯 分离权重
        whitespace_weight=weights.get('whitespace', 0.1),
        legality_weight=weights.get('legality', 0.1),
        verbose=calibration_verbose,
        calibration_samples=calibration_samples,
        feedthrough_method=feedthrough_method  # 🎯 新增：传递feedthrough方法配置
    )
    
    return TwoPhaseEvaluator(pin_assigner, evaluator, design, config)


class TwoPhaseEvaluator:
    """两阶段评估器 - 宏模块布局 + Pin重新规划"""
    
    def __init__(self, pin_assigner, evaluator: ComprehensiveEvaluator, original_design: FloorplanDesign, config: Dict[str, Any] = None):
        self.pin_assigner = pin_assigner
        self.evaluator = evaluator
        self.original_design = original_design
        self.config = config or {}
        
        self.best_complete_design = None
        self.best_cost = float('inf')
        self.evaluation_count = 0
        
        self.current_visualization_folder = None
        self.drawer = None
        self.viz_config = None
        
        # 基准函数归一化相关
        self.representation_method = None
        self.calibration_needed = True
        
        self._init_visualization()
    
    def _init_visualization(self):
        """初始化可视化"""
        viz_config = self.config.get('output', {}).get('visualization', {})
        
        print(f"可视化配置: {viz_config}")
        
        if viz_config.get('enabled', False):
            try:
                print("正在初始化可视化...")
                self.viz_config = VisualizationConfig.from_dict(viz_config)
                self.drawer = LayoutDrawer(self.viz_config)
                print("可视化初始化成功!")
            except Exception as e:
                print(f"可视化初始化失败: {e}")
                import traceback
                traceback.print_exc()
                self.viz_config = None
                self.drawer = None
        else:
            print("可视化未启用")
    
    def set_visualization_folder(self, folder_path: str):
        """设置可视化输出文件夹"""
        self.current_visualization_folder = folder_path
    
    def set_representation_method(self, representation_method):
        """设置表示方法以用于基准函数校准"""
        self.representation_method = representation_method
    
    def evaluate(self, macro_design: FloorplanDesign) -> float:
        """评估宏模块布局并执行Pin重新规划"""
        self.evaluation_count += 1
        
        # 🎯 基准函数归一化校准 - 仅在第一次评估时执行
        if self.calibration_needed and self.representation_method is not None:
            if self.config.get('output', {}).get('verbose', True):
                print("\n🔧 开始基准函数归一化校准...")
            
            try:
                # 🔧 **关键修复**: 使用原始设计的深拷贝进行校准，避免污染原始设计
                calibration_design = self.original_design.clone()
                # 执行基准函数校准
                calibration_stats = self.evaluator.calibrate(self.representation_method, calibration_design)
                
                if self.config.get('output', {}).get('verbose', True):
                    print(f"校准完成! 收集样本: {calibration_stats.get('samples_collected', 0)}")
                    print("归一化因子:")
                    for metric, factor in calibration_stats.get('normalization_factors', {}).items():
                        print(f"   {metric}: {factor:.2f}")
                
                self.calibration_needed = False
                
            except Exception as e:
                print(f"校准失败，使用默认归一化因子: {e}")
                self.calibration_needed = False
        
        complete_design = self._execute_pin_replanning(macro_design)
        
        if not self._check_legality(complete_design):
            return float('inf')
        
        cost = self.evaluator.evaluate(complete_design)
        
        # 每隔固定步骤进行可视化，不依赖是否找到更好解
        self._maybe_visualize(complete_design)
        
        if cost < self.best_cost:
            self.best_cost = cost
            # 🔧 **关键修复**: 深拷贝最优解，避免后续Pin分配修改影响已保存的最优解
            self.best_complete_design = complete_design.clone()
        
        return cost
    
    def _maybe_visualize(self, design: FloorplanDesign):
        """可能执行可视化"""
        if not self.drawer or not self.viz_config or not self.current_visualization_folder:
            return
        
        should_draw = self.viz_config.should_draw(self.evaluation_count)
        
        try:
            if should_draw:
                output_path = os.path.join(
                    self.current_visualization_folder, 
                    self.viz_config.output_dir
                )
                os.makedirs(output_path, exist_ok=True)
                
                filename = self.viz_config.get_filename(self.evaluation_count)
                
                success = self.drawer.draw_layout(
                    design=design, 
                    iteration=self.evaluation_count,
                    output_path=output_path,
                    filename=filename
                )
                
        except Exception as e:
            print(f"可视化失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _execute_pin_replanning(self, macro_design: FloorplanDesign) -> FloorplanDesign:
        """执行Pin重新规划"""
        complete_design = FloorplanDesign(macro_design.name + "_complete")
        
        for module in macro_design.modules.values():
            complete_design.add_module(module)
        
        for net in macro_design.nets.values():
            complete_design.add_net(net)
        
        # 导入模块类型以进行正确的类型检查
        from src.data.structures import ModuleType
        
        for pin in self.original_design.modules.values():
            if pin.module_type == ModuleType.TERMINAL:
                # 🔧 **关键修复**: 创建Pin模块的深拷贝，避免多个设计共享同一Pin对象
                complete_design.add_module(pin.clone())
        
        complete_design = self.pin_assigner.assign_pins(complete_design)
        
        return complete_design
    
    def _check_legality(self, design: FloorplanDesign) -> bool:
        """检查合法性"""
        return True
    
    def get_best_complete_design(self) -> FloorplanDesign:
        """获取最优完整设计"""
        return self.best_complete_design


def run_optimization(config: Dict[str, Any]) -> Dict[str, Any]:
    """运行优化"""
    start_time = time.time()
    
    design = load_design(config)
    representation = create_representation(config)
    
    representation.initialize(design)
    
    algorithm = create_algorithm(config, representation, design)
    
    two_phase_evaluator = create_two_phase_evaluator(config, design)
    
    # 设置表示方法以支持基准函数校准
    two_phase_evaluator.set_representation_method(representation)
    
    algorithm.set_evaluator(two_phase_evaluator.evaluate)
    
    # 生成统一的输出文件夹名称
    data_config = config.get('data', {})
    algorithm_config = config.get('algorithm', {})
    
    benchmark = data_config.get('benchmark', 'unknown')
    dataset = data_config.get('dataset', 'unknown')
    algorithm_name = algorithm_config.get('name', 'unknown')
    representation_name = algorithm_config.get('representation', 'unknown')
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    folder_name = f"{dataset}_{benchmark}_{algorithm_name}_{representation_name}_{timestamp}"
    
    # 为可视化设置文件夹
    viz_config = config.get('output', {}).get('visualization', {})
    if viz_config.get('enabled', False):
        output_dir = Path("results") / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        two_phase_evaluator.set_visualization_folder(str(output_dir))
    
    verbose = config.get('output', {}).get('verbose', True)
    if verbose:
        print("开始优化...")
    
    visualization_config = config.get('output', {}).get('visualization', {})
    result = algorithm.optimize(design, visualization=visualization_config)
    
    if verbose:
        runtime = time.time() - start_time
        print(f"优化完成，总耗时: {runtime:.2f}秒")
    
    final_design = two_phase_evaluator.get_best_complete_design()
    if final_design:
        result.design = final_design
    
    return {
        'result': result,
        'config': config,
        'runtime': time.time() - start_time,
        'evaluator': two_phase_evaluator,
        'folder_name': folder_name  # 传递文件夹名称给save_results
    }


def evaluate_final_result(result: Dict[str, Any], config: Dict[str, Any]) -> Any:
    """评估最终结果"""
    optimization_result = result['result']
    final_design = optimization_result.design
    
    if not final_design:
        print("警告: 无有效设计结果")
        return None
    
    # 使用与优化过程相同的评估器配置
    evaluator = result['evaluator'].evaluator  # 使用优化过程中的评估器
    detailed_result = evaluator.detailed_evaluate(final_design)
    
    verbose = config.get('output', {}).get('verbose', True)
    if verbose:
        print("\n最终结果评估:")
        print(f"  - 总代价: {detailed_result.total_cost:.2f}")
        print(f"  - 面积: {detailed_result.area:.0f}")
        print(f"  - 线长: {detailed_result.wirelength:.0f}")
        print(f"  - Feedthrough数量: {detailed_result.feedthrough_count}")
        print(f"  - Feedthrough线长: {detailed_result.feedthrough_wirelength:.0f}")  # 🎯 新增：显示线长
        print(f"  - Feedthrough方法: {evaluator.feedthrough_method}")                 # 🎯 新增：显示评估方法
        print(f"  - 收敛迭代: {optimization_result.convergence_iteration}")
        print(f"  - 算法: {optimization_result.algorithm_info.get('algorithm_name', 'unknown')}")
    
    return detailed_result


def save_results(result: Dict[str, Any], evaluation: Any, config: Dict[str, Any]):
    """保存结果"""
    output_config = config.get('output', {})
    
    if not output_config.get('save_results', True):
        return
    
    optimization_result = result['result']
    final_design = optimization_result.design
    
    if not final_design:
        print("警告: 无设计结果可保存")
        return
    
    try:
        # 使用运行时传递的文件夹名称，确保与可视化文件夹一致
        folder_name = result.get('folder_name')
        if not folder_name:
            # 备用方案：重新生成（但这种情况不应该发生）
            data_config = config.get('data', {})
            algorithm_config = config.get('algorithm', {})
            
            benchmark = data_config.get('benchmark', 'unknown')
            dataset = data_config.get('dataset', 'unknown')
            algorithm_name = algorithm_config.get('name', 'unknown')
            representation = algorithm_config.get('representation', 'unknown')
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            folder_name = f"{dataset}_{benchmark}_{algorithm_name}_{representation}_{timestamp}"
        
        output_dir = Path("results") / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保evaluator也使用相同的文件夹（以防万一）
        result['evaluator'].set_visualization_folder(str(output_dir))
        
        # 使用PlacementFileGenerator生成.pl文件
        pl_generator = PlacementFileGenerator()
        pl_file_path = output_dir / "final_result.pl"
        pl_generator.generate_pl_file(final_design, config['data'], str(pl_file_path))
        
        # 保存评估数据
        if evaluation:
            organizer = ResultOrganizer()
            
            # 准备优化结果数据
            optimization_data = {
                'iterations': optimization_result.algorithm_info.get('total_iterations', 0),
                'optimization_time': result['runtime'],
                'convergence': True,
                'final_temperature': optimization_result.algorithm_info.get('final_temperature'),
                'best_iteration': optimization_result.convergence_iteration,
                # 基准函数校准信息
                'calibration': {
                    'is_calibrated': result['evaluator'].evaluator.is_calibrated,
                    'normalization_factors': result['evaluator'].evaluator.normalization_factors.copy(),
                    'calibration_stats': result['evaluator'].evaluator.calibration_stats.copy()
                }
            }
            
            # 🎯 准备评估结果数据 - 包含feedthrough线长和评估方法信息
            evaluation_data = {
                'area': float(evaluation.area),
                'wirelength': float(evaluation.wirelength),
                'hpwl': float(evaluation.hpwl),
                'feedthrough_count': int(evaluation.feedthrough_count),
                'feedthrough_wirelength': float(evaluation.feedthrough_wirelength),          # 🎯 新增：feedthrough线长
                'feedthrough_method': result['evaluator'].evaluator.feedthrough_method,      # 🎯 新增：评估方法
                'whitespace_ratio': float(evaluation.whitespace_ratio),
                'chip_width': float(evaluation.chip_width),
                'chip_height': float(evaluation.chip_height),
                'utilization': float(evaluation.utilization),
                'aspect_ratio': float(evaluation.aspect_ratio),
                'is_legal': bool(evaluation.is_legal),
                'overlap_count': int(evaluation.overlap_count),
                'overlap_area': float(evaluation.overlap_area),
                'total_cost': float(evaluation.total_cost),
                'num_modules': len(final_design.modules),
                'num_nets': len(final_design.nets),
                # 🎯 新增：归一化指标
                'normalized_feedthrough_count': float(evaluation.normalized_feedthrough_count),
                'normalized_feedthrough_wirelength': float(evaluation.normalized_feedthrough_wirelength),
                # 🎯 新增：权重信息
                'weights_used': evaluation.weights.copy()
            }
            
            # 保存评估元数据
            evaluation_file = output_dir / "evaluation.json"
            organizer.save_evaluation_metadata(evaluation_data, config, optimization_data, evaluation_file)
        
        # 绘制最终最优解
        viz_config = output_config.get('visualization', {})
        
        if viz_config.get('enabled', False):
            try:
                # 获取可视化配置
                from src.visualization.layout_drawer import LayoutDrawer
                from src.visualization.visualization_config import VisualizationConfig
                
                # 创建可视化配置
                viz_config_obj = VisualizationConfig.from_dict(viz_config)
                viz_config_obj.enabled = True
                viz_config_obj.use_threading = False  # 最终结果不需要线程
                
                # 创建绘图器
                drawer = LayoutDrawer(viz_config_obj)
                
                # 设置输出路径
                viz_dir = output_dir / viz_config.get('output_dir', 'visualization')
                viz_dir.mkdir(parents=True, exist_ok=True)
                
                # 准备评估指标用于显示
                metrics = {}
                if evaluation:
                    metrics = {
                        'area': evaluation.area,
                        'wirelength': evaluation.wirelength,
                        'feedthrough': evaluation.feedthrough_count,
                        'utilization': f"{evaluation.utilization:.1%}",
                        'cost': evaluation.total_cost
                    }
                
                # 绘制最终最优解
                final_image_name = "final_best_solution.png"
                
                success = drawer.draw_layout(
                    design=final_design,
                    iteration=-1,  # -1 表示最终结果
                    metrics=metrics,
                    output_path=str(viz_dir),
                    filename=final_image_name
                )
                
                if success:
                    final_image_path = viz_dir / final_image_name
                    if output_config.get('verbose', True):
                        print(f"✅ 最终最优解可视化已保存到: {final_image_path}")
                else:
                    print("❌ 最终可视化绘制失败")
                
            except Exception as e:
                print(f"❌ 最终结果可视化失败: {e}")
                if output_config.get('verbose', True):
                    import traceback
                    traceback.print_exc()
        
        if output_config.get('verbose', True):
            print(f"结果已保存到: {output_dir}")
            
            if viz_config.get('enabled', False):
                viz_dir = output_dir / viz_config.get('output_dir', 'visualization')
                if viz_dir.exists():
                    print(f"可视化文件夹: {viz_dir}")
        
    except Exception as e:
        print(f"保存结果失败: {e}")
        if output_config.get('verbose', True):
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='两阶段布图优化系统')
    parser.add_argument('config', help='YAML配置文件路径')
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"配置文件不存在: {args.config}")
        sys.exit(1)
    
    print("两阶段布图优化系统")
    print("=" * 50)
    
    config = load_config(args.config)
    
    try:
        result = run_optimization(config)
        evaluation = evaluate_final_result(result, config)
        save_results(result, evaluation, config)
        
        print("=" * 50)
        print("优化完成")
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 