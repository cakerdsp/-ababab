#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyFloorplan - 高性能VLSI布图规划优化框架
A Professional VLSI Floorplanning Optimization Framework
"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# 读取长描述
long_description = (here / 'README.md').read_text(encoding='utf-8')

# 读取版本信息
def get_version():
    version_file = here / 'src' / '__init__.py'
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return '0.1.0'

setup(
    # 基础信息
    name='pyfloorplan',
    version=get_version(),
    description='高性能VLSI布图规划优化框架',
    long_description=long_description,
    long_description_content_type='text/markdown',
    
    # 项目链接
    url='https://github.com/username/pyfloorplan',
    project_urls={
        'Bug Reports': 'https://github.com/username/pyfloorplan/issues',
        'Source': 'https://github.com/username/pyfloorplan',
        'Documentation': 'https://pyfloorplan.readthedocs.io/',
    },
    
    # 作者信息
    author='PyFloorplan Team',
    author_email='author@example.com',
    
    # 分类信息
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    
    # 关键词
    keywords='vlsi, floorplanning, eda, optimization, algorithm, layout',
    
    # 包配置
    packages=find_packages(),
    python_requires='>=3.8',
    
    # 依赖包
    install_requires=[
        'numpy>=1.21.0',
        'scipy>=1.7.0',
        'matplotlib>=3.5.0',
        'seaborn>=0.11.0',
        'pandas>=1.3.0',
        'pyyaml>=6.0',
        'colorlog>=6.0.0',
        'tqdm>=4.62.0',
        'networkx>=2.6.0',
    ],
    
    # 可选依赖
    extras_require={
        'gpu': ['torch>=2.0.0', 'torchvision>=0.15.0'],
        'viz': ['plotly>=5.0.0'],
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
        ],
        'docs': [
            'sphinx>=4.0.0',
            'sphinx-rtd-theme>=1.0.0',
        ],
        'performance': ['numba>=0.56.0'],
    },
    
    # 包数据
    package_data={
        'pyfloorplan': [
            'config/*.yaml',
            'examples/*.py',
            'tests/test_data/*',
        ],
    },
    
    # 数据文件
    data_files=[
        ('config', ['config/algorithms.yaml', 'config/datasets.yaml']),
    ],
    
    # 入口点
    entry_points={
        'console_scripts': [
            'pyfloorplan=src.cli:main',
        ],
    },
    
    # 包含所有文件
    include_package_data=True,
    
    # 压缩安全
    zip_safe=False,
) 