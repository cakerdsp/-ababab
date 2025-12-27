#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模拟退火算法 - 用于布图优化
"""

import random
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from .base import MetaheuristicAlgorithm, RepresentationMethod, OptimizationResult
from ..data.structures import FloorplanDesign
from ..evaluation.legality import ComprehensiveLegalityChecker, LegalityConstraints


class SimulatedAnnealing(MetaheuristicAlgorithm):
    """模拟退火算法类"""
    
    def __init__(self,
                 representation: RepresentationMethod,
                 initial_temperature: float = 1000.0,
                 final_temperature: float = 1.0,
                 cooling_rate: float = 0.95,
                 max_iterations: int = 10000,
                 moves_per_temperature: int = 100,
                 verbose: bool = True,
                 feedthrough_method: str = "original",
                 **kwargs):
        """初始化模拟退火算法"""
        super().__init__(
            name="Simulated Annealing",
            representation=representation,
            max_iterations=max_iterations,
            **kwargs
        )
        
        self.initial_temperature = initial_temperature
        self.final_temperature = final_temperature
        self.cooling_rate = cooling_rate
        self.moves_per_temperature = moves_per_temperature
        self.verbose = verbose
        self.feedthrough_method = feedthrough_method.lower()
        
        # 合法性检查
        legality_constraints = LegalityConstraints(
            enable_overlap_check=True,
            enable_boundary_check=True,
            enable_spacing_check=False,
            enable_alignment_check=False,
            enable_keepout_check=False,
            overlap_penalty_weight=10000.0,
            boundary_penalty_weight=1000.0
        )
        self.legality_checker = ComprehensiveLegalityChecker(legality_constraints)
        
        # 统计信息
        self.current_temperature = initial_temperature
        self.accepted_moves = 0
        self.rejected_moves = 0
        self.current_solution = None
        self.current_cost = float('inf')
        
    def optimize(self, design: FloorplanDesign, **kwargs) -> OptimizationResult:
        """执行模拟退火优化"""
        start_time = time.time()
        
        report_interval = kwargs.get('report_interval', 50)
        
        if self.verbose:
            print(f"开始模拟退火优化")
        
        # 初始化算法
        self._initialize_algorithm(design)
        
        # 生成初始解
        current_solution = self.representation.random_solution()
        current_design = self.representation.decode(current_solution)
        
        # 设置芯片边界用于合法性检查
        if current_design.chip_width > 0 and current_design.chip_height > 0:
            self.legality_checker.constraints.chip_boundary = (0, 0, current_design.chip_width, current_design.chip_height)
        
        # 寻找合法初始解
        legality_result = self.legality_checker.check_legality(current_design)
        retry_count = 0
        max_retries = 100
        
        while not legality_result.is_legal and retry_count < max_retries:
            current_solution = self.representation.random_solution()
            current_design = self.representation.decode(current_solution)
            legality_result = self.legality_checker.check_legality(current_design)
            retry_count += 1
        
        if not legality_result.is_legal:
            print(f"警告: 经过 {max_retries} 次尝试仍未找到合法初始解")
        
        # 评估初始解
        current_cost = self._evaluate_solution(current_design)
        
        # 设置最优解
        self.best_solution = self.representation.copy_representation(current_solution)
        self.best_cost = current_cost
        
        # 主循环
        temperature = self.initial_temperature
        iteration = 0
        moves_at_current_temp = 0
        
        illegal_moves_rejected = 0
        legal_moves_rejected = 0
        accepted_moves = 0
        
        while temperature >= self.final_temperature and iteration < self.max_iterations:
            # 生成邻域解
            neighbor_solution = self._generate_neighbor(current_solution)
            neighbor_design = self.representation.decode(neighbor_solution)
            
            # 合法性检查
            legality_result = self.legality_checker.check_legality(neighbor_design)
            
            if not legality_result.is_legal:
                illegal_moves_rejected += 1
                moves_at_current_temp += 1
                iteration += 1
                
                # 定期报告信息
                if iteration % report_interval == 0:
                    legal_rate = accepted_moves / max(1, iteration)
                    illegal_rate = illegal_moves_rejected / max(1, iteration)
                    
                    if self.best_solution is not None:
                        best_design = self.representation.decode(self.best_solution)
                        from ..evaluation.metrics import calculate_area, calculate_wirelength
                        
                        area = calculate_area(best_design) if best_design.modules else 0
                        wirelength = calculate_wirelength(best_design) if best_design.nets else 0
                        feedthrough = self._calculate_feedthrough_for_display(best_design) if best_design.nets else 0
                        
                        print(f"SA {iteration}: T={temperature:.1f}, 代价={self.best_cost:.0f}, "
                              f"面积={area:.0f}, 线长={wirelength:.0f}, FT={feedthrough}, "
                              f"接受率={legal_rate:.2f}, 违法率={illegal_rate:.2f}")
                    else:
                        print(f"SA {iteration}: T={temperature:.1f}, 代价=inf, 无有效解")
                
                continue
            
            # 评估邻域解
            neighbor_cost = self._evaluate_solution(neighbor_design)
            
            # 计算代价差
            delta_cost = neighbor_cost - current_cost
            
            # 接受准则
            accept = False
            if delta_cost <= 0:
                # 改进解，直接接受
                accept = True
            else:
                # 恶化解，按概率接受
                probability = math.exp(-delta_cost / temperature)
                if random.random() < probability:
                    accept = True
            
            if accept:
                current_solution = neighbor_solution
                current_cost = neighbor_cost
                accepted_moves += 1
                
                # 更新最优解
                if current_cost < self.best_cost:
                    self.best_solution = self.representation.copy_representation(current_solution)
                    self.best_cost = current_cost
            else:
                legal_moves_rejected += 1
            
            moves_at_current_temp += 1
            iteration += 1
            
            # 定期报告合法解的搜索进度
            if iteration % report_interval == 0:
                legal_rate = accepted_moves / max(1, iteration)
                illegal_rate = illegal_moves_rejected / max(1, iteration)
                
                if self.best_solution is not None:
                    best_design = self.representation.decode(self.best_solution)
                    from ..evaluation.metrics import calculate_area, calculate_wirelength
                    
                    area = calculate_area(best_design) if best_design.modules else 0
                    wirelength = calculate_wirelength(best_design) if best_design.nets else 0
                    feedthrough = self._calculate_feedthrough_for_display(best_design) if best_design.nets else 0
                    
                    print(f"SA {iteration}: T={temperature:.1f}, 代价={self.best_cost:.0f}, "
                          f"面积={area:.0f}, 线长={wirelength:.0f}, FT={feedthrough}, "
                          f"接受率={legal_rate:.2f}, 违法率={illegal_rate:.2f}")
                else:
                    print(f"SA {iteration}: T={temperature:.1f}, 代价=inf, 无有效解")
            
            # 温度更新
            if moves_at_current_temp >= self.moves_per_temperature:
                temperature *= self.cooling_rate
                moves_at_current_temp = 0
        
        return self._finalize_algorithm(start_time)
    
    def _calculate_feedthrough_for_display(self, design) -> int:
        """
        根据配置的feedthrough_method计算feedthrough用于显示
        Calculate feedthrough for display based on configured method
        """
        try:
            if self.feedthrough_method == 'ftafp':
                # 使用FTAFP方法
                from ..evaluation.FTAFP_feedthrough import calculate_ftafp_feedthrough
                ftafp_result = calculate_ftafp_feedthrough(design)
                return ftafp_result.total_feedthrough_number
            else:
                # 使用原始metrics方法
                from ..evaluation.metrics import calculate_feedthrough
                return calculate_feedthrough(design)
        except Exception as e:
            if self.verbose:
                print(f"计算feedthrough时出错: {e}, 使用fallback方法")
            # Fallback到简单方法
            from ..evaluation.metrics import calculate_feedthrough
            return calculate_feedthrough(design)
    
    def _finalize_algorithm(self, start_time: float) -> OptimizationResult:
        """完成算法"""
        runtime = time.time() - start_time
        convergence_iteration = self.current_iteration
        
        if self.best_solution is not None:
            best_design = self.representation.decode(self.best_solution)
        else:
            random_representation = self.representation.random_solution()
            best_design = self.representation.decode(random_representation)
        
        algorithm_info = self.get_algorithm_info()
        
        return OptimizationResult(
            design=best_design,
            best_cost=self.best_cost,
            iteration_costs=self.cost_history,
            convergence_iteration=convergence_iteration,
            runtime=runtime,
            evaluations=self.current_iteration,
            algorithm_info=algorithm_info
        )
    
    def _generate_neighbor(self, current_solution: Any) -> Any:
        """生成邻域解"""
        return self.representation.generate_neighbor(current_solution)
    
    def _accept_solution(self, delta_cost: float, temperature: float) -> bool:
        """接受准则"""
        if delta_cost <= 0:
            return True
        
        if temperature <= 0:
            return False
        
        probability = math.exp(-delta_cost / temperature)
        return random.random() < probability
    
    def get_algorithm_info(self) -> Dict[str, Any]:
        """获取算法信息"""
        return {
            'name': self.name,
            'representation': self.representation.name,
            'initial_temperature': self.initial_temperature,
            'final_temperature': self.final_temperature,
            'cooling_rate': self.cooling_rate,
            'max_iterations': self.max_iterations,
            'moves_per_temperature': self.moves_per_temperature,
            'current_temperature': self.current_temperature,
            'current_iteration': self.current_iteration,
            'best_cost': self.best_cost,
            'accepted_moves': self.accepted_moves,
            'rejected_moves': self.rejected_moves
        }


# 预定义的温度策略
class TemperatureSchedules:
    """温度策略集合"""
    
    @staticmethod
    def geometric(initial_temp: float, cooling_rate: float = 0.95):
        """几何降温策略"""
        def schedule(current_temp: float, iteration: int) -> float:
            return current_temp * cooling_rate
        return schedule
    
    @staticmethod
    def linear(initial_temp: float, final_temp: float, max_iterations: int):
        """线性降温策略"""
        def schedule(current_temp: float, iteration: int) -> float:
            progress = iteration / max_iterations
            return initial_temp - progress * (initial_temp - final_temp)
        return schedule
    
    @staticmethod
    def exponential(initial_temp: float, decay_rate: float = 0.01):
        """指数降温策略"""
        def schedule(current_temp: float, iteration: int) -> float:
            return initial_temp * math.exp(-decay_rate * iteration)
        return schedule
    
    @staticmethod
    def logarithmic(initial_temp: float, cooling_rate: float = 1.0):
        """对数降温策略"""
        def schedule(current_temp: float, iteration: int) -> float:
            return initial_temp / (1 + cooling_rate * math.log(1 + iteration))
        return schedule


# 创建预配置的SA算法
def create_fast_sa(representation: RepresentationMethod, verbose: bool = False, feedthrough_method: str = "original") -> SimulatedAnnealing:
    """创建快速SA配置"""
    return SimulatedAnnealing(
        representation=representation,
        initial_temperature=100.0,
        final_temperature=1.0,
        cooling_rate=0.9,
        max_iterations=1000,
        moves_per_temperature=50,
        verbose=verbose,
        feedthrough_method=feedthrough_method
    )


def create_standard_sa(representation: RepresentationMethod, verbose: bool = True, feedthrough_method: str = "original") -> SimulatedAnnealing:
    """创建标准SA配置"""
    return SimulatedAnnealing(
        representation=representation,
        initial_temperature=1000.0,
        final_temperature=1.0,
        cooling_rate=0.95,
        max_iterations=10000,
        moves_per_temperature=100,
        verbose=verbose,
        feedthrough_method=feedthrough_method
    )


def create_slow_sa(representation: RepresentationMethod, verbose: bool = True, feedthrough_method: str = "original") -> SimulatedAnnealing:
    """创建慢速高质量SA配置"""
    return SimulatedAnnealing(
        representation=representation,
        initial_temperature=5000.0,
        final_temperature=0.1,
        cooling_rate=0.98,
        max_iterations=50000,
        moves_per_temperature=200,
        verbose=verbose,
        feedthrough_method=feedthrough_method
    )


# 导出主要类和函数
__all__ = [
    'SimulatedAnnealing',
    'TemperatureSchedules',
    'create_fast_sa',
    'create_standard_sa',
    'create_slow_sa'
] 