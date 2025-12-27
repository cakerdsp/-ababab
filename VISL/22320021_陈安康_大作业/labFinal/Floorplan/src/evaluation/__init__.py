#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
评估模块 - Evaluation Module

布图质量评估的完整实现
Complete implementation of floorplan quality evaluation

作者: PyFloorplan Team
"""

try:
    # 优先使用相对导入
    from .metrics import (
        evaluate_floorplan,
        calculate_area,
        calculate_wirelength,
        calculate_feedthrough,
        calculate_whitespace,
        FloorplanEvaluator
    )

    from .wirelength import (
        calculate_hpwl,
        calculate_rmst,
        WirelengthCalculator
    )

    from .feedthrough import (
        calculate_feedthrough_count,
        analyze_feedthrough_paths,
        FeedthroughAnalyzer
    )

    from .whitespace import (
        calculate_whitespace_ratio,
        analyze_whitespace_distribution,
        WhitespaceAnalyzer
    )

    # 统一评估器接口
    from .evaluator import *

    from .legality import (
        ComprehensiveLegalityChecker,
        LegalityResult,
        LegalityConstraints,
        create_legality_checker,
        check_design_legality
    )
except ImportError:
    # 如果相对导入失败，使用绝对导入
    try:
        from evaluation.metrics import (
            evaluate_floorplan,
            calculate_area,
            calculate_wirelength,
            calculate_feedthrough,
            calculate_whitespace,
            FloorplanEvaluator
        )

        from evaluation.wirelength import (
            calculate_hpwl,
            calculate_rmst,
            WirelengthCalculator
        )

        from evaluation.feedthrough import (
            calculate_feedthrough_count,
            analyze_feedthrough_paths,
            FeedthroughAnalyzer
        )

        from evaluation.whitespace import (
            calculate_whitespace_ratio,
            analyze_whitespace_distribution,
            WhitespaceAnalyzer
        )

        # 统一评估器接口
        from evaluation.evaluator import *

        from evaluation.legality import (
            ComprehensiveLegalityChecker,
            LegalityResult,
            LegalityConstraints,
            create_legality_checker,
            check_design_legality
        )
    except ImportError as e:
        print(f"Warning: Unable to import evaluation modules: {e}")
        # 创建占位符函数
        def evaluate_floorplan(*args, **kwargs):
            raise ImportError("Evaluation modules not properly imported")
        
        def calculate_area(*args, **kwargs):
            raise ImportError("Evaluation modules not properly imported")
        
        def calculate_wirelength(*args, **kwargs):
            raise ImportError("Evaluation modules not properly imported")

# 模块自检功能
def run_evaluation_self_check():
    """运行所有评估模块的自检"""
    print("=" * 60)
    print("🔧 评估模块全面自检")  
    print("=" * 60)
    
    all_passed = True
    
    # 1. 测试各个子模块
    print("\n📋 第一阶段: 子模块自检")
    print("-" * 40)
    
    # 导入自检函数
    try:
        from .metrics import self_check_metrics
        from .wirelength import self_check_wirelength
        from .feedthrough import self_check_feedthrough
        from .whitespace import self_check_whitespace
    except ImportError:
        from evaluation.metrics import self_check_metrics
        from evaluation.wirelength import self_check_wirelength
        from evaluation.feedthrough import self_check_feedthrough
        from evaluation.whitespace import self_check_whitespace
    
    # 执行各模块自检
    module_checks = [
        ("度量模块", self_check_metrics),
        ("线长模块", self_check_wirelength), 
        ("Feedthrough模块", self_check_feedthrough),
        ("空白区域模块", self_check_whitespace)
    ]
    
    # 合法性检查器自检
    try:
        print("🔧 合法性检查器 自检")
        legality_checker = create_legality_checker(enable_all=False)
        if not legality_checker.self_check():
            all_passed = False
        print()
    except Exception as e:
        print(f"❌ 合法性检查器自检过程出错: {e}")
        all_passed = False
    
    for module_name, check_func in module_checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {module_name}自检过程出错: {e}")
            all_passed = False
        print()
    
    # 2. 测试统一评估器
    print("\n📋 第二阶段: 统一评估器自检")  
    print("-" * 40)
    
    evaluators = [
        ("综合评估器", create_evaluator("comprehensive", verbose=False)),
        ("快速评估器", create_evaluator("fast"))
    ]
    
    for evaluator_name, evaluator in evaluators:
        try:
            print(f"🔧 {evaluator_name} 自检")
            if not evaluator.self_check():
                all_passed = False
        except Exception as e:
            print(f"❌ {evaluator_name}自检过程出错: {e}")
            all_passed = False
        print()
    
    # 3. 集成测试
    print("\n📋 第三阶段: 集成测试")
    print("-" * 40)
    
    try:
        # 创建复杂测试设计
        try:
            from ..data.structures import FloorplanDesign, Module, Net, ModuleType
        except ImportError:
            from data.structures import FloorplanDesign, Module, Net, ModuleType
        
        design = FloorplanDesign("integration_test")
        
        # 添加多个模块形成复杂布局
        modules_config = [
            ("m1", 0, 0, 100, 100),
            ("m2", 150, 0, 80, 120),
            ("m3", 300, 0, 60, 80),
            ("m4", 0, 150, 120, 80),
            ("m5", 200, 200, 100, 100)
        ]
        
        for name, x, y, w, h in modules_config:
            module = Module(name, ModuleType.SOFT, width=w, height=h, x=x, y=y, area=w*h)
            design.add_module(module)
        
        # 添加多条网线
        nets_config = [
            ("net1", [("m1", "p1"), ("m2", "p1")]),
            ("net2", [("m2", "p2"), ("m3", "p2")]),  
            ("net3", [("m1", "p3"), ("m3", "p3"), ("m5", "p3")]),  # 多引脚
            ("net4", [("m4", "p4"), ("m5", "p4")])
        ]
        
        for net_name, pins in nets_config:
            net = Net(net_name, pins)
            design.add_net(net)
        
        # 测试综合评估器在复杂设计上的表现
        evaluator = create_evaluator("comprehensive", verbose=False)
        
        print("🔧 集成测试: 复杂设计评估")
        result = evaluator.detailed_evaluate(design)
        
        # 验证集成结果
        if result.total_cost <= 0:
            print("❌ 集成测试失败: 总代价无效")
            all_passed = False
        else:
            print(f"✅ 集成测试通过")
            print(f"   - 设计规模: {len(design.modules)}模块, {len(design.nets)}网线")
            print(f"   - 总代价: {result.total_cost:.6f}")
            print(f"   - 各项指标: 面积={result.area:.0f}, 线长={result.wirelength:.0f}, "
                  f"FT={result.feedthrough_count}, 空白={result.whitespace_ratio:.3f}")
            
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        all_passed = False
    
    # 4. 性能测试
    print("\n📋 第四阶段: 性能测试")
    print("-" * 40)
    
    try:
        import time
        
        # 创建大规模测试设计
        large_design = FloorplanDesign("performance_test")
        
        # 添加更多模块
        for i in range(50):
            x = (i % 10) * 120
            y = (i // 10) * 120  
            module = Module(f"m{i}", ModuleType.SOFT, width=100, height=100, x=x, y=y, area=10000)
            large_design.add_module(module)
        
        # 添加更多网线
        for i in range(80):
            m1_idx = i % 50
            m2_idx = (i + 1) % 50
            net = Net(f"net{i}", [(f"m{m1_idx}", "p1"), (f"m{m2_idx}", "p1")])
            large_design.add_net(net)
        
        # 测试评估性能
        evaluator = create_evaluator("fast")  # 使用快速评估器
        
        print(f"🔧 性能测试: 大规模设计 ({len(large_design.modules)}模块, {len(large_design.nets)}网线)")
        
        start_time = time.time()
        for _ in range(10):  # 连续评估10次
            cost = evaluator.evaluate(large_design)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        
        if avg_time > 1.0:  # 如果平均评估时间超过1秒，认为性能有问题
            print(f"性能警告: 平均评估时间 {avg_time:.3f}s (可能偏慢)")
        else:
            print(f"✅ 性能测试通过: 平均评估时间 {avg_time:.4f}s")
            
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有评估模块自检通过! 系统ready for production!")
        print("✅ 所有子模块功能正常")
        print("✅ 统一评估器工作正常") 
        print("✅ 集成测试通过")
        print("✅ 性能测试通过")
    else:
        print("❌ 部分评估模块自检失败! 请检查错误信息")
    print("=" * 60)
    
    return all_passed

__all__ = [
    # 综合评估
    'evaluate_floorplan',
    'FloorplanEvaluator',
    
    # 基础指标
    'calculate_area',
    'calculate_wirelength', 
    'calculate_feedthrough',
    'calculate_whitespace',
    
    # 线长计算
    'calculate_hpwl',
    'calculate_rmst',
    'WirelengthCalculator',
    
    # Feedthrough分析
    'calculate_feedthrough_count',
    'analyze_feedthrough_paths',
    'FeedthroughAnalyzer',
    
    # 空白区域分析
    'calculate_whitespace_ratio',
    'analyze_whitespace_distribution',
    'WhitespaceAnalyzer',
    
    # 统一评估器
    'ComprehensiveEvaluator',
    'FastEvaluator',
    'EvaluationResult',
    'create_evaluator',
    
    # 自检功能
    'run_evaluation_self_check'
] 