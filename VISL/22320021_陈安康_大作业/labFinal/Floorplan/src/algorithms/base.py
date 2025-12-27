#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
算法基类 - Algorithm Base Classes

定义布图规划算法的基础接口和抽象类
Defines base interfaces and abstract classes for floorplanning algorithms
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    torch = None
    HAS_TORCH = False

from dataclasses import dataclass
import copy
import time

try:
    from ..data.structures import FloorplanDesign, Module
except ImportError:
    from data.structures import FloorplanDesign, Module


@dataclass
class OptimizationResult:
    """
    优化结果 - Optimization Result
    
    存储算法优化过程的结果和统计信息
    Stores results and statistics from algorithm optimization process
    """
    design: FloorplanDesign       # 最优设计
    best_cost: float             # 最优代价
    iteration_costs: List[float]  # 迭代代价历史
    convergence_iteration: int   # 收敛迭代次数
    runtime: float               # 运行时间（秒）
    evaluations: int             # 评估次数
    
    # 详细指标
    final_wirelength: float = 0.0
    final_area: float = 0.0
    final_feedthrough: int = 0
    final_whitespace: float = 0.0
    
    # 算法特定信息
    algorithm_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.algorithm_info is None:
            self.algorithm_info = {}


class RepresentationMethod(ABC):
    """
    表示方法抽象基类 - Representation Method Abstract Base Class
    
    定义布图拓扑表示方法的统一接口
    Defines unified interface for floorplan topology representation methods
    """
    
    def __init__(self, name: str):
        self.name = name
        self.modules = []  # 模块列表
        self.module_map = {}  # 模块名到索引的映射
    
    @abstractmethod
    def initialize(self, design: FloorplanDesign) -> Any:
        """
        初始化表示 - Initialize representation
        
        Args:
            design: 布图设计
            
        Returns:
            初始表示
        """
        pass
    
    @abstractmethod
    def random_solution(self) -> Any:
        """
        生成随机解 - Generate random solution
        
        Returns:
            随机表示
        """
        pass
    
    @abstractmethod
    def decode(self, representation: Any) -> FloorplanDesign:
        """
        解码表示为布图 - Decode representation to floorplan
        
        Args:
            representation: 表示
            
        Returns:
            布图设计
        """
        pass
    
    @abstractmethod
    def neighborhood_operations(self, representation: Any) -> List[Any]:
        """
        生成邻域操作 - Generate neighborhood operations
        
        Args:
            representation: 当前表示
            
        Returns:
            邻域表示列表
        """
        pass
    
    def copy_representation(self, representation: Any) -> Any:
        """复制表示 - Copy representation"""
        return copy.deepcopy(representation)
    
    def get_representation_info(self, representation: Any) -> Dict[str, Any]:
        """获取表示信息 - Get representation information"""
        return {
            'type': self.name,
            'size': len(self.modules) if hasattr(self, 'modules') else 0
        }


class FloorplanAlgorithm(ABC):
    """
    布图规划算法抽象基类 - Floorplan Algorithm Abstract Base Class
    
    定义布图规划算法的统一接口
    Defines unified interface for floorplanning algorithms
    """
    
    def __init__(self, 
                 name: str,
                 representation: RepresentationMethod,
                 **kwargs):
        """
        初始化算法
        
        Args:
            name: 算法名称
            representation: 表示方法
            **kwargs: 其他参数
        """
        self.name = name
        self.representation = representation
        self.config = kwargs
        
        # 运行状态
        self.is_running = False
        self.current_iteration = 0
        self.best_solution = None
        self.best_cost = float('inf')
        self.cost_history = []
        
        # 回调函数
        self.callbacks = []
        
        # 评估器
        self.evaluator = None
    
    @abstractmethod
    def optimize(self, design: FloorplanDesign, **kwargs) -> OptimizationResult:
        """
        执行优化算法 - Execute optimization algorithm
        
        Args:
            design: 初始布图设计
            **kwargs: 算法特定参数
            
        Returns:
            优化结果
        """
        pass
    
    def set_evaluator(self, evaluator):
        """设置评估器"""
        self.evaluator = evaluator
    
    def add_callback(self, callback):
        """添加回调函数"""
        self.callbacks.append(callback)
    
    def _evaluate_solution(self, design: FloorplanDesign) -> float:
        """评估解的质量"""
        if callable(self.evaluator):
            return self.evaluator(design)
        elif hasattr(self.evaluator, 'evaluate'):
            return self.evaluator.evaluate(design)
        else:
            raise ValueError("评估器必须是可调用的或有evaluate方法")
    
    def _call_callbacks(self, iteration: int, current_cost: float, current_design: FloorplanDesign):
        """调用回调函数 - Call callback functions"""
        for callback in self.callbacks:
            try:
                callback(iteration, current_cost, current_design, self)
            except Exception as e:
                print(f"Warning: Callback failed at iteration {iteration}: {e}")
    
    def _check_convergence(self, tolerance: float = 1e-6, patience: int = 100) -> bool:
        """
        检查收敛条件 - Check convergence condition
        
        Args:
            tolerance: 容忍度
            patience: 耐心值（多少迭代无改善则收敛）
            
        Returns:
            是否收敛
        """
        if len(self.cost_history) < patience:
            return False
        
        recent_costs = self.cost_history[-patience:]
        cost_variance = np.var(recent_costs)
        
        return cost_variance < tolerance
    
    def get_algorithm_info(self) -> Dict[str, Any]:
        """获取算法信息 - Get algorithm information"""
        return {
            'name': self.name,
            'representation': self.representation.name,
            'current_iteration': self.current_iteration,
            'best_cost': self.best_cost,
            'is_running': self.is_running,
            'config': self.config
        }
    
    def save_checkpoint(self, filepath: str):
        """保存检查点 - Save checkpoint"""
        checkpoint = {
            'algorithm_name': self.name,
            'representation': self.representation,
            'current_iteration': self.current_iteration,
            'best_solution': self.best_solution,
            'best_cost': self.best_cost,
            'cost_history': self.cost_history,
            'config': self.config
        }
        
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint, f)
    
    def load_checkpoint(self, filepath: str):
        """加载检查点 - Load checkpoint"""
        import pickle
        with open(filepath, 'rb') as f:
            checkpoint = pickle.load(f)
        
        self.current_iteration = checkpoint['current_iteration']
        self.best_solution = checkpoint['best_solution']
        self.best_cost = checkpoint['best_cost']
        self.cost_history = checkpoint['cost_history']
        self.config.update(checkpoint['config'])


class MetaheuristicAlgorithm(FloorplanAlgorithm):
    """
    元启发式算法基类 - Metaheuristic Algorithm Base Class
    
    为模拟退火、遗传算法等元启发式方法提供通用框架
    Provides common framework for metaheuristic methods like SA, GA, etc.
    """
    
    def __init__(self, 
                 name: str,
                 representation: RepresentationMethod,
                 max_iterations: int = 10000,
                 **kwargs):
        super().__init__(name, representation, **kwargs)
        self.max_iterations = max_iterations
    
    def _initialize_algorithm(self, design: FloorplanDesign):
        """初始化算法 - Initialize algorithm"""
        self.is_running = True
        self.current_iteration = 0
        self.cost_history = []
        
        # 初始化表示方法
        self.representation.initialize(design)
    
    def _finalize_algorithm(self, start_time: float) -> OptimizationResult:
        """完成算法 - Finalize algorithm"""
        self.is_running = False
        
        runtime = time.time() - start_time
        convergence_iteration = len(self.cost_history)
        
        # 解码最优解
        if self.best_solution is not None:
            best_design = self.representation.decode(self.best_solution)
        else:
            best_design = None
        
        return OptimizationResult(
            design=best_design,
            best_cost=self.best_cost,
            iteration_costs=self.cost_history,
            convergence_iteration=convergence_iteration,
            runtime=runtime,
            evaluations=len(self.cost_history),
            algorithm_info=self.get_algorithm_info()
        )


class PopulationBasedAlgorithm(FloorplanAlgorithm):
    """
    基于种群的算法基类 - Population-Based Algorithm Base Class
    
    为遗传算法、粒子群优化等基于种群的方法提供框架
    Provides framework for population-based methods like GA, PSO, etc.
    """
    
    def __init__(self, 
                 name: str,
                 representation: RepresentationMethod,
                 population_size: int = 50,
                 max_generations: int = 100,
                 **kwargs):
        super().__init__(name, representation, **kwargs)
        self.population_size = population_size
        self.max_generations = max_generations
        
        # 种群相关
        self.population = []
        self.fitness_values = []
    
    def _initialize_population(self, design: FloorplanDesign):
        """初始化种群 - Initialize population"""
        self.representation.initialize(design)
        
        self.population = []
        self.fitness_values = []
        
        for _ in range(self.population_size):
            individual = self.representation.random_solution()
            self.population.append(individual)
            
            # 评估适应度
            decoded_design = self.representation.decode(individual)
            fitness = self._evaluate_solution(decoded_design)
            self.fitness_values.append(fitness)
    
    def _update_best_solution(self):
        """更新最优解 - Update best solution"""
        best_idx = np.argmin(self.fitness_values)
        current_best_cost = self.fitness_values[best_idx]
        
        if current_best_cost < self.best_cost:
            self.best_cost = current_best_cost
            self.best_solution = self.representation.copy_representation(
                self.population[best_idx]
            )
    
    def get_population_stats(self) -> Dict[str, float]:
        """获取种群统计信息 - Get population statistics"""
        if not self.fitness_values:
            return {}
        
        return {
            'best_fitness': min(self.fitness_values),
            'worst_fitness': max(self.fitness_values),
            'average_fitness': np.mean(self.fitness_values),
            'fitness_std': np.std(self.fitness_values)
        }


# 常用回调函数
class ProgressCallback:
    """进度回调 - Progress Callback"""
    
    def __init__(self, print_interval: int = 100):
        self.print_interval = print_interval
    
    def __call__(self, iteration: int, cost: float, design: FloorplanDesign, algorithm: FloorplanAlgorithm):
        if iteration % self.print_interval == 0:
            print(f"[{algorithm.name}] Iteration {iteration}: Cost = {cost:.2f}")


class HistoryCallback:
    """历史记录回调 - History Recording Callback"""
    
    def __init__(self):
        self.history = {
            'iterations': [],
            'costs': [],
            'designs': []
        }
    
    def __call__(self, iteration: int, cost: float, design: FloorplanDesign, algorithm: FloorplanAlgorithm):
        self.history['iterations'].append(iteration)
        self.history['costs'].append(cost)
        self.history['designs'].append(design.clone())
    
    def get_history(self) -> Dict[str, List]:
        return self.history


# 导出主要类
__all__ = [
    'FloorplanAlgorithm',
    'RepresentationMethod',
    'MetaheuristicAlgorithm',
    'PopulationBasedAlgorithm',
    'OptimizationResult',
    'ProgressCallback',
    'HistoryCallback'
] 