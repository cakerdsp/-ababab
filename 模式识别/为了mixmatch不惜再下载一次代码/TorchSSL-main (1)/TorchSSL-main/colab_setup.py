#!/usr/bin/env python3
"""
Colab Setup Script for TorchSSL MixMatch
==============================================

This script helps you set up and run MixMatch on Google Colab.
It handles common Colab-specific configurations and path settings.

Usage:
    python colab_setup.py --algorithm mixmatch --dataset cifar10 --num_labels 250

Author: AI Assistant
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required dependencies for Colab environment."""
    print("📦 Installing dependencies...")
    
    # Install required packages
    packages = [
        "tensorboard",
        "scikit-learn",
        "PyYAML",
        "pillow"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")

def setup_directories(data_dir="./data", save_dir="./saved_models"):
    """Create necessary directories."""
    print("📁 Setting up directories...")
    
    dirs_to_create = [
        data_dir,
        save_dir,
        "./config",
        os.path.join(data_dir, "data_statistics"),
        "./figures"
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def generate_colab_config(algorithm="mixmatch", dataset="cifar10", num_labels=250, 
                         data_dir="./data", save_dir="./saved_models"):
    """Generate a Colab-optimized configuration file."""
    print("⚙️ Generating Colab configuration...")
    
    config = {
        'save_dir': save_dir,
        'save_name': f'{algorithm}_{dataset}_{num_labels}_colab',
        'resume': False,
        'load_path': None,
        'overwrite': True,  # Allow overwriting for Colab
        'use_tensorboard': True,
        'epoch': 1,
        'num_train_iter': 20000,
        'num_eval_iter': 1000,
        'num_labels': num_labels,
        'batch_size': 64,
        'eval_batch_size': 1024,
        'uratio': 1,
        'alpha': 0.5,
        'T': 0.5,
        'ulb_loss_ratio': 100,
        'ramp_up': 0.4,
        'ema_m': 0.999,
        'optim': 'SGD',
        'lr': 0.03,
        'momentum': 0.9,
        'weight_decay': 0.0005,
        'amp': False,  # Disable AMP for better Colab compatibility
        'net': 'WideResNet',
        'net_from_name': False,
        'depth': 28,
        'widen_factor': 2,
        'leaky_slope': 0.1,
        'dropout': 0.0,
        'data_dir': data_dir,
        'dataset': dataset,
        'train_sampler': 'RandomSampler',
        'num_classes': 10 if 'cifar10' in dataset.lower() else 100,
        'num_workers': 2,  # Reduce workers for Colab
        'alg': algorithm,
        'seed': 0,
        'world_size': 1,
        'rank': 0,
        'multiprocessing_distributed': False,  # Disable for Colab
        'dist_url': 'tcp://127.0.0.1:10027',
        'dist_backend': 'nccl',
        'gpu': 0,
    }
    
    # Adjust num_classes based on dataset
    if 'cifar100' in dataset.lower():
        config['num_classes'] = 100
    elif 'svhn' in dataset.lower():
        config['num_classes'] = 10
    elif 'stl10' in dataset.lower():
        config['num_classes'] = 10
    
    # Save config file
    config_dir = f"./config/{algorithm}"
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, f"{algorithm}_{dataset}_{num_labels}_colab.yaml")
    
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Configuration saved to: {config_file}")
    return config_file

def check_gpu():
    """Check if GPU is available."""
    import torch
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"🚀 GPU available: {gpu_name}")
        return True
    else:
        print("⚠️  No GPU detected. Performance will be limited.")
        return False

def run_training(algorithm, config_file):
    """Run the training script."""
    print(f"🚀 Starting {algorithm} training...")
    
    # Construct command
    cmd = [
        sys.executable, f"{algorithm}.py",
        "--c", config_file,
        "--overwrite", "True"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Training completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Training failed with error: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Setup and run SSL algorithms on Google Colab")
    
    parser.add_argument("--algorithm", type=str, default="mixmatch",
                       choices=["mixmatch", "fixmatch", "remixmatch", "flexmatch", "pseudolabel"],
                       help="SSL algorithm to run")
    parser.add_argument("--dataset", type=str, default="cifar10",
                       choices=["cifar10", "cifar100", "svhn", "stl10"],
                       help="Dataset to use")
    parser.add_argument("--num_labels", type=int, default=250,
                       help="Number of labeled samples")
    parser.add_argument("--data_dir", type=str, default="./data",
                       help="Data directory")
    parser.add_argument("--save_dir", type=str, default="./saved_models",
                       help="Model save directory")
    parser.add_argument("--install_deps", action="store_true",
                       help="Install dependencies")
    parser.add_argument("--setup_only", action="store_true",
                       help="Only setup, don't run training")
    
    args = parser.parse_args()
    
    print("🔧 TorchSSL Colab Setup")
    print("=" * 50)
    
    # Install dependencies if requested
    if args.install_deps:
        install_dependencies()
    
    # Check GPU
    check_gpu()
    
    # Setup directories
    setup_directories(args.data_dir, args.save_dir)
    
    # Generate config
    config_file = generate_colab_config(
        algorithm=args.algorithm,
        dataset=args.dataset,
        num_labels=args.num_labels,
        data_dir=args.data_dir,
        save_dir=args.save_dir
    )
    
    if args.setup_only:
        print("🎉 Setup completed! You can now run:")
        print(f"python {args.algorithm}.py --c {config_file}")
        return
    
    # Run training
    success = run_training(args.algorithm, config_file)
    
    if success:
        print("\n🎉 All done! Check your results in:", args.save_dir)
    else:
        print("\n❌ Training failed. Please check the logs above.")

if __name__ == "__main__":
    main() 