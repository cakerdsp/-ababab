#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
遗传算法 - Genetic Algorithm

实现用于布图优化的遗传算法
Implements genetic algorithm for floorplan optimization
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import time

from .base import PopulationBasedAlgorithm, OptimizationResult
from ..data.structures import FloorplanDesign
from ..evaluation.legality import ComprehensiveLegalityChecker, LegalityConstraints


@dataclass
class Individual:
    """个体(染色体)"""
    representation: Any  # 布图表示(序列对、B*树等)
    fitness: float = float('inf')  # 适应度(越小越好)
    age: int = 0  # 个体年龄
    is_legal: bool = False  # 是否合法
    violations: int = 0  # 违规数量
    
    def __post_init__(self):
        if self.fitness == float('inf'):
            self.fitness = random.uniform(1000, 10000)  # 随机初始适应度


class GeneticAlgorithm(PopulationBasedAlgorithm):
    """遗传算法类 - 带严格合法性检查"""
    
    def __init__(self, 
                 representation,
                 population_size: int = 50,
                 max_generations: int = 100,
                 crossover_rate: float = 0.8,
                 mutation_rate: float = 0.1,
                 selection_method: str = 'tournament',
                 tournament_size: int = 3,
                 elitism_ratio: float = 0.1,
                 strict_legality: bool = True,
                 repair_illegal: bool = True,
                 verbose: bool = False,
                 visualization_callback=None,
                 feedthrough_method: str = "original",
                 **kwargs):
        """初始化遗传算法"""
        super().__init__(
            name="Genetic Algorithm",
            representation=representation,
            population_size=population_size,
            max_generations=max_generations,
            **kwargs
        )
        
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.selection_method = selection_method
        self.tournament_size = tournament_size
        self.elitism_ratio = elitism_ratio
        self.strict_legality = strict_legality
        self.repair_illegal = repair_illegal
        self.verbose = verbose
        self.visualization_callback = visualization_callback
        self.feedthrough_method = feedthrough_method.lower()
        
        # 统一合法性检查
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
        self.generation_stats = []
        self.diversity_history = []
        self.legal_individuals_count = []
    
    def optimize(self, design: FloorplanDesign, **kwargs) -> OptimizationResult:
        """执行遗传算法优化"""
        start_time = time.time()
        
        if self.verbose:
            print(f"开始遗传算法优化")
            print(f"  种群大小: {self.population_size}")
            print(f"  最大代数: {self.max_generations}")
            print(f"  交叉率: {self.crossover_rate}")
            print(f"  变异率: {self.mutation_rate}")
        
        # 初始化
        self._initialize_algorithm(design)
        
        # 主循环
        for generation in range(self.max_generations):
            self.current_iteration = generation
            
            # 评估种群
            self._evaluate_population(design)
            
            # 更新最优解
            self._update_best_solution()
            
            # 记录统计信息
            self._record_generation_stats(generation)
            
            # 调用回调函数
            if self.best_solution:
                best_design = self.representation.decode(self.best_solution)
                self._call_callbacks(generation, self.best_cost, best_design)
                
                # 调用可视化回调(参考DREAMPlace)
                if self.visualization_callback:
                    try:
                        # 计算关键指标用于可视化
                        from ..evaluation.metrics import calculate_area, calculate_wirelength
                        
                        area = calculate_area(best_design) if best_design.modules else 0
                        wirelength = calculate_wirelength(best_design) if best_design.nets else 0
                        feedthrough = self._calculate_feedthrough_for_display(best_design) if best_design.nets else 0
                        
                        metrics = {
                            'area': area,
                            'wirelength': wirelength,
                            'feedthrough': feedthrough,
                            'generation': generation,
                            'cost': self.best_cost,
                            'population_size': self.population_size
                        }
                        self.visualization_callback(best_design, generation, metrics)
                    except Exception as e:
                        # 静默处理可视化错误,避免影响优化
                        pass
            
            # 检查收敛
            if self._check_convergence():
                break
            
            # 进化操作
            self._evolve_population()
        
        return self._finalize_algorithm(start_time)
    
    def _finalize_algorithm(self, start_time: float) -> OptimizationResult:
        """完成算法"""
        self.is_running = False
        
        runtime = time.time() - start_time
        convergence_iteration = self.current_iteration
        
        # 解码最优解并确保合法
        if self.best_solution is not None:
            best_design = self.representation.decode(self.best_solution)
            if self.verbose:
                print(f"使用最优合法解")
        else:
            # 🔧 **FIX**: 如果没有合法解,选择违规最少的个体
            if self.population:
                best_individual = min(self.population, key=lambda x: self._calculate_violation_penalty(x))
                best_design = self.representation.decode(best_individual.representation)
                if self.verbose:
                    print(f"使用违规最少的解(无合法解)")
            else:
                # 极端情况:生成随机解
                random_representation = self.representation.random_solution()
                best_design = self.representation.decode(random_representation)
                if self.verbose:
                    print(f"使用随机解(无种群)")
        
        # 确保best_design包含所有必要的模块
        if not best_design or len(best_design.modules) == 0:
            # 如果解码失败,创建基础设计
            from ..data.structures import FloorplanDesign
            best_design = FloorplanDesign("fallback_design")
            if hasattr(self.representation, 'original_design') and self.representation.original_design:
                # 复制原始设计的模块
                for module in self.representation.original_design.modules.values():
                    best_design.add_module(module)
        
        # 算法特定信息
        algorithm_info = {
            'algorithm_name': f"Genetic Algorithm ({self.representation.name})",
            'total_iterations': self.current_iteration,
            'acceptance_rate': getattr(self, 'accepted', 0) / max(1, self.current_iteration),
            'legal_rate': len([ind for ind in self.population if ind.is_legal]) / len(self.population) if self.population else 0.0,
            'population_size': self.population_size,
            'final_generation': self.current_iteration
        }
        
        return OptimizationResult(
            design=best_design,
            best_cost=self.best_cost,
            iteration_costs=self.cost_history,
            convergence_iteration=convergence_iteration,
            runtime=runtime,
            evaluations=self.evaluations,
            algorithm_info=algorithm_info
        )
    
    def _initialize_algorithm(self, design: FloorplanDesign):
        """初始化算法"""
        # 基本初始化
        self.is_running = True
        self.current_iteration = 0
        self.cost_history = []
        self.evaluations = 0
        
        # 首先初始化表示方法(准备模块数据)
        self.representation.initialize(design)
        
        # 保存原始设计用于边界设置
        self.original_design = design
        
        # 初始化种群
        self.population = []
        self.fitness_values = []
        
        for i in range(self.population_size):
            # 使用random_solution生成随机个体
            representation = self.representation.random_solution()
            individual = Individual(representation=representation)
            
            # 统一合法性检查:评估个体合法性
            decoded_design = self.representation.decode(individual.representation)
            
            # 设置芯片边界
            if hasattr(self, 'original_design') and self.original_design:
                if self.original_design.chip_width > 0 and self.original_design.chip_height > 0:
                    self.legality_checker.constraints.chip_boundary = (0, 0, self.original_design.chip_width, self.original_design.chip_height)
            
            legality_result = self.legality_checker.check_legality(decoded_design)
            
            if not legality_result.is_legal:
                individual.is_legal = False
                individual.violations = legality_result.total_violations
            else:
                individual.is_legal = True
                individual.violations = 0
            
            self.population.append(individual)
        
        self.generation_stats = []
        self.diversity_history = []
        self.legal_individuals_count = []
    
    def _evaluate_population(self, design: FloorplanDesign):
        """评估整个种群的适应度"""
        self.fitness_values = []  # 重置适应度列表
        legal_count = 0
        
        for individual in self.population:
            if individual.fitness == float('inf'):  # 只评估未评估的个体
                decoded_design = self.representation.decode(individual.representation)
                
                # 重新检查合法性(可能在进化过程中改变)
                if self.original_design.chip_width > 0 and self.original_design.chip_height > 0:
                    self.legality_checker.constraints.chip_boundary = (0, 0, self.original_design.chip_width, self.original_design.chip_height)
                
                legality_result = self.legality_checker.check_legality(decoded_design)
                individual.is_legal = legality_result.is_legal
                individual.violations = legality_result.total_violations
                
                if individual.is_legal:
                    # 合法个体:正常评估
                    individual.fitness = self._evaluate_solution(decoded_design)
                    legal_count += 1
                else:
                    # 不合法个体:给予惩罚值
                    if self.strict_legality:
                        # 严格模式:给予极大惩罚值,实际上会被淘汰
                        base_penalty = 100000.0
                        individual.fitness = base_penalty + individual.violations * 10000.0
                    else:
                        # 宽松模式:计算基础代价并加上惩罚
                        try:
                            base_cost = self._evaluate_solution(decoded_design)
                            penalty = individual.violations * 1000.0  # 每个违规增加1000惩罚
                            individual.fitness = base_cost + penalty
                        except:
                            individual.fitness = 50000.0  # 默认惩罚值
                
                self.evaluations += 1
            
            if individual.is_legal:
                legal_count += 1
            
            self.fitness_values.append(individual.fitness)
        
        self.legal_individuals_count.append(legal_count)
    
    def _evolve_population(self):
        """进化种群"""
        new_population = []
        
        # 精英保留 - 只保留合法的精英
        elite_count = int(self.population_size * self.elitism_ratio)
        elites = self._select_legal_elites(elite_count)
        new_population.extend(elites)
        
        # 生成新个体
        generation_attempts = 0
        max_generation_attempts = self.population_size * 3  # 防止无限循环
        
        while len(new_population) < self.population_size and generation_attempts < max_generation_attempts:
            generation_attempts += 1
            
            # 选择父母
            parent1 = self._selection()
            parent2 = self._selection()
            
            # 交叉
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1, parent2
            
            # 变异
            if random.random() < self.mutation_rate:
                child1 = self._mutation(child1)
            if random.random() < self.mutation_rate:
                child2 = self._mutation(child2)
            
            # 检查子代合法性
            children = [child1, child2]
            for child in children:
                if len(new_population) >= self.population_size:
                    break
                
                # 评估子代合法性
                decoded_child = self.representation.decode(child.representation)
                
                if self.original_design.chip_width > 0 and self.original_design.chip_height > 0:
                    self.legality_checker.constraints.chip_boundary = (0, 0, self.original_design.chip_width, self.original_design.chip_height)
                
                legality_result = self.legality_checker.check_legality(decoded_child)
                child.is_legal = legality_result.is_legal
                child.violations = legality_result.total_violations
                
                if self.strict_legality and not child.is_legal:
                    # 严格模式:直接拒绝不合法子代
                    continue
                
                # 如果不是严格模式,或者子代合法,则添加到新种群
                new_population.append(child)
        
        # 如果新种群不足,用随机个体填充
        while len(new_population) < self.population_size:
            random_individual = Individual(representation=self.representation.random_solution())
            new_population.append(random_individual)
        
        # 截断到指定大小
        self.population = new_population[:self.population_size]
        
        # 增加年龄
        for individual in self.population:
            individual.age += 1
            
        # 同步适应度值列表
        self._sync_fitness_values()
    
    def _select_legal_elites(self, count: int) -> List[Individual]:
        """选择合法的精英个体"""
        legal_individuals = [ind for ind in self.population if ind.is_legal]
        
        if not legal_individuals:
            return []  # 没有合法个体
        
        sorted_legal = sorted(legal_individuals, key=lambda x: x.fitness)
        selected_count = min(count, len(sorted_legal))
        
        return [self._copy_individual(ind) for ind in sorted_legal[:selected_count]]
    
    def _sync_fitness_values(self):
        """同步适应度值列表"""
        self.fitness_values = [individual.fitness for individual in self.population]
    
    def _update_best_solution(self):
        """更新最优解 - 只考虑合法个体"""
        legal_individuals = [ind for ind in self.population if ind.is_legal]
        
        if not legal_individuals:
            return  # 没有合法个体,不更新最优解
        
        best_legal = min(legal_individuals, key=lambda x: x.fitness)
        
        if best_legal.fitness < self.best_cost:
            self.best_cost = best_legal.fitness
            self.best_solution = self.representation.copy_representation(
                best_legal.representation
            )
            
            if self.verbose:
                print(f"  ↗ 新最优解: {self.best_cost:.2f}")
            
            # 如果有可视化回调,调用它
            if self.visualization_callback:
                try:
                    design = self.representation.decode(self.best_solution)
                    self.visualization_callback(design, self.current_iteration, {
                        'cost': self.best_cost,
                        'generation': self.current_iteration
                    })
                except Exception as e:
                    print(f"可视化回调失败: {e}")
    
    def _selection(self) -> Individual:
        """选择操作 - 偏向选择合法个体"""
        if self.selection_method == 'tournament':
            return self._tournament_selection()
        elif self.selection_method == 'roulette':
            return self._roulette_selection()
        elif self.selection_method == 'rank':
            return self._rank_selection()
        else:
            raise ValueError(f"Unknown selection method: {self.selection_method}")
    
    def _tournament_selection(self) -> Individual:
        """锦标赛选择 - 偏向合法个体"""
        tournament = random.sample(self.population, min(self.tournament_size, len(self.population)))
        
        # 首先尝试选择合法个体
        legal_contestants = [ind for ind in tournament if ind.is_legal]
        if legal_contestants:
            winner = min(legal_contestants, key=lambda x: x.fitness)
        else:
            # 如果没有合法个体,选择违规最少的
            winner = min(tournament, key=lambda x: (x.violations, x.fitness))
        
        return self._copy_individual(winner)
    
    def _roulette_selection(self) -> Individual:
        """轮盘赌选择"""
        # 转换为最大化问题(适应度越大越好)
        max_fitness = max(ind.fitness for ind in self.population)
        adjusted_fitness = []
        
        for ind in self.population:
            base_fitness = max_fitness - ind.fitness + 1
            # 给合法个体额外的选择优势
            if ind.is_legal:
                base_fitness *= 2.0
            adjusted_fitness.append(base_fitness)
        
        total_fitness = sum(adjusted_fitness)
        
        if total_fitness == 0:
            return random.choice(self.population)
        
        pick = random.uniform(0, total_fitness)
        current = 0
        
        for i, fitness in enumerate(adjusted_fitness):
            current += fitness
            if current >= pick:
                return self._copy_individual(self.population[i])
        
        return self._copy_individual(self.population[-1])
    
    def _rank_selection(self) -> Individual:
        """排名选择 - 考虑合法性"""
        # 首先按合法性分组,然后按适应度排序
        legal_individuals = [ind for ind in self.population if ind.is_legal]
        illegal_individuals = [ind for ind in self.population if not ind.is_legal]
        
        # 合法个体排在前面
        sorted_population = (sorted(legal_individuals, key=lambda x: x.fitness) + 
                           sorted(illegal_individuals, key=lambda x: (x.violations, x.fitness)))
        
        ranks = list(range(len(sorted_population), 0, -1))  # 排名越高权重越大
        total_rank = sum(ranks)
        
        pick = random.uniform(0, total_rank)
        current = 0
        
        for i, rank in enumerate(ranks):
            current += rank
            if current >= pick:
                return self._copy_individual(sorted_population[i])
        
        return self._copy_individual(sorted_population[-1])
    
    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """交叉操作"""
        representation_name = self.representation.name
        
        if representation_name == "SequencePair":
            return self._sequence_pair_crossover(parent1, parent2)
        else:
            # 默认基于邻域的交叉
            return self._neighborhood_based_crossover(parent1, parent2)
    
    def _sequence_pair_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """序列对的交叉操作"""
        gamma_plus1, gamma_minus1 = parent1.representation
        gamma_plus2, gamma_minus2 = parent2.representation
        
        if len(gamma_plus1) != len(gamma_plus2):
            return self._neighborhood_based_crossover(parent1, parent2)
        
        n = len(gamma_plus1)
        if n < 2:
            return self._copy_individual(parent1), self._copy_individual(parent2)
        
        # 随机选择交叉类型
        crossover_type = random.choice(['single_point', 'two_point', 'uniform'])
        
        if crossover_type == 'single_point':
            # 单点交叉
            crossover_point = random.randint(1, n - 1)
            
            # 对Γ+序列进行交叉
            child1_gamma_plus = self._single_point_crossover_sequence(
                gamma_plus1, gamma_plus2, crossover_point
            )
            child2_gamma_plus = self._single_point_crossover_sequence(
                gamma_plus2, gamma_plus1, crossover_point
            )
            
            # 对Γ-序列进行交叉
            child1_gamma_minus = self._single_point_crossover_sequence(
                gamma_minus1, gamma_minus2, crossover_point
            )
            child2_gamma_minus = self._single_point_crossover_sequence(
                gamma_minus2, gamma_minus1, crossover_point
            )
        
        elif crossover_type == 'two_point':
            # 两点交叉
            point1 = random.randint(1, n - 2)
            point2 = random.randint(point1 + 1, n - 1)
            
            child1_gamma_plus = self._two_point_crossover_sequence(
                gamma_plus1, gamma_plus2, point1, point2
            )
            child2_gamma_plus = self._two_point_crossover_sequence(
                gamma_plus2, gamma_plus1, point1, point2
            )
            
            child1_gamma_minus = self._two_point_crossover_sequence(
                gamma_minus1, gamma_minus2, point1, point2
            )
            child2_gamma_minus = self._two_point_crossover_sequence(
                gamma_minus2, gamma_minus1, point1, point2
            )
        
        else:  # uniform crossover
            # 均匀交叉
            child1_gamma_plus = self._uniform_crossover_sequence(gamma_plus1, gamma_plus2)
            child2_gamma_plus = self._uniform_crossover_sequence(gamma_plus2, gamma_plus1)
            
            child1_gamma_minus = self._uniform_crossover_sequence(gamma_minus1, gamma_minus2)
            child2_gamma_minus = self._uniform_crossover_sequence(gamma_minus2, gamma_minus1)
        
        # 创建子代个体
        child1 = Individual(representation=(child1_gamma_plus, child1_gamma_minus))
        child2 = Individual(representation=(child2_gamma_plus, child2_gamma_minus))
        
        return child1, child2
    
    def _single_point_crossover_sequence(self, seq1: List[int], seq2: List[int], 
                                       crossover_point: int) -> List[int]:
        """对序列进行单点交叉"""
        # 取seq1的前半部分和seq2的后半部分
        child = seq1[:crossover_point] + seq2[crossover_point:]
        
        # 确保序列的有效性(包含所有元素且无重复)
        return self._repair_sequence(child, len(seq1))
    
    def _two_point_crossover_sequence(self, seq1: List[int], seq2: List[int], 
                                    point1: int, point2: int) -> List[int]:
        """对序列进行两点交叉"""
        # 取seq1的两端和seq2的中间部分
        child = seq1[:point1] + seq2[point1:point2] + seq1[point2:]
        
        # 确保序列的有效性
        return self._repair_sequence(child, len(seq1))
    
    def _uniform_crossover_sequence(self, seq1: List[int], seq2: List[int]) -> List[int]:
        """对序列进行均匀交叉"""
        child = []
        for i in range(len(seq1)):
            if random.random() < 0.5:
                child.append(seq1[i])
            else:
                child.append(seq2[i])
        
        # 确保序列的有效性
        return self._repair_sequence(child, len(seq1))
    
    def _repair_sequence(self, sequence: List[int], expected_length: int) -> List[int]:
        """修复序列以确保包含所有期望的元素且无重复"""
        expected_elements = set(range(expected_length))
        sequence_set = set(sequence)
        
        # 找出缺失和重复的元素
        missing = expected_elements - sequence_set
        duplicates = []
        seen = set()
        
        for i, elem in enumerate(sequence):
            if elem in seen:
                duplicates.append(i)
            else:
                seen.add(elem)
        
        # 修复序列
        repaired = sequence.copy()
        missing_list = list(missing)
        
        for i, duplicate_index in enumerate(duplicates):
            if i < len(missing_list):
                repaired[duplicate_index] = missing_list[i]
        
        # 如果还有缺失的元素,随机替换
        for elem in missing_list[len(duplicates):]:
            # 找一个不在期望范围内的元素替换
            for i, val in enumerate(repaired):
                if val not in expected_elements:
                    repaired[i] = elem
                    break
        
        return repaired
    

    
    def _neighborhood_based_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """基于邻域的交叉操作(原方法,作为备选)"""
        # 使用表示方法的邻域操作作为交叉的基础
        neighbors1 = self.representation.neighborhood_operations(parent1.representation)
        neighbors2 = self.representation.neighborhood_operations(parent2.representation)
        
        if neighbors1 and neighbors2:
            # 随机选择邻域作为子代
            child1_repr = random.choice(neighbors1)
            child2_repr = random.choice(neighbors2)
        else:
            # 如果没有邻域,直接复制父代
            child1_repr = self.representation.copy_representation(parent1.representation)
            child2_repr = self.representation.copy_representation(parent2.representation)
        
        child1 = Individual(representation=child1_repr)
        child2 = Individual(representation=child2_repr)
        
        return child1, child2
    
    def _mutation(self, individual: Individual) -> Individual:
        """变异操作"""
        # 使用表示方法的邻域操作作为变异
        neighbors = self.representation.neighborhood_operations(individual.representation)
        
        if neighbors:
            mutated_repr = random.choice(neighbors)
        else:
            # 如果没有邻域,生成随机解
            mutated_repr = self.representation.random_solution()
        
        return Individual(representation=mutated_repr)
    
    def _copy_individual(self, individual: Individual) -> Individual:
        """复制个体"""
        copied_repr = self.representation.copy_representation(individual.representation)
        return Individual(
            representation=copied_repr,
            fitness=individual.fitness,
            age=individual.age,
            is_legal=individual.is_legal,
            violations=individual.violations
        )
    
    def _record_generation_stats(self, generation: int):
        """记录代数统计信息"""
        fitness_values = [ind.fitness for ind in self.population]
        legal_individuals = [ind for ind in self.population if ind.is_legal]
        
        stats = {
            'generation': generation,
            'best_fitness': min(fitness_values),
            'avg_fitness': np.mean(fitness_values),
            'worst_fitness': max(fitness_values),
            'std_fitness': np.std(fitness_values),
            'diversity': self._calculate_diversity(),
            'legal_count': len(legal_individuals),
            'legal_ratio': len(legal_individuals) / len(self.population),
            'best_legal_fitness': min([ind.fitness for ind in legal_individuals]) if legal_individuals else float('inf'),
            'avg_violations': np.mean([ind.violations for ind in self.population])
        }
        
        self.generation_stats.append(stats)
        self.diversity_history.append(stats['diversity'])
    
    def _calculate_diversity(self) -> float:
        """计算种群多样性"""
        if len(self.population) < 2:
            return 0.0
        
        # 基于适应度的多样性计算
        fitness_values = [ind.fitness for ind in self.population]
        unique_fitness = len(set(fitness_values))
        max_diversity = len(self.population)
        
        return unique_fitness / max_diversity
    
    def _calculate_violation_penalty(self, individual: Individual) -> float:
        """计算个体的违规惩罚值"""
        # 基础惩罚: 违规数量 + 适应度
        base_penalty = individual.violations * 1000.0
        fitness_penalty = individual.fitness if individual.fitness != float('inf') else 100000.0
        
        return base_penalty + fitness_penalty
    
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
    
    def get_algorithm_info(self) -> Dict[str, Any]:
        """获取算法信息"""
        base_info = super().get_algorithm_info()
        
        genetic_info = {
            'crossover_rate': self.crossover_rate,
            'mutation_rate': self.mutation_rate,
            'selection_method': self.selection_method,
            'tournament_size': self.tournament_size,
            'elitism_ratio': self.elitism_ratio,
            'strict_legality': self.strict_legality,
            'repair_illegal': self.repair_illegal,
            'current_diversity': self.diversity_history[-1] if self.diversity_history else 0.0,
            'avg_diversity': np.mean(self.diversity_history) if self.diversity_history else 0.0,
            'final_legal_ratio': self.legal_individuals_count[-1] / self.population_size if self.legal_individuals_count else 0.0
        }
        
        base_info.update(genetic_info)
        return base_info


# 导出类
__all__ = ['GeneticAlgorithm', 'Individual'] 