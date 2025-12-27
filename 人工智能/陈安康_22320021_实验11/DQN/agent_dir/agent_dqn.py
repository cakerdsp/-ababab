import os
import random
import copy
import numpy as np
# 用于构建神经网络的
import torch
from pathlib import Path
from tensorboardX import SummaryWriter
from torch import nn, optim
import matplotlib.pyplot as plt
# from agent_dir.agent import Agent


# Q学习神经网络
class QNetwork(nn.Module):
    # 输入层大小，隐藏层大小，输出层大小
    def __init__(self, input_size, hidden_size, output_size):
        super(QNetwork, self).__init__()
        ##################
        # YOUR CODE HERE #
        ##################
        # 包含输入层，一个隐藏层，输出层的神经网络构建
        self.input = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.ouput = nn.Linear(hidden_size, output_size)
        
    
    # 前向传播
    def forward(self, inputs):
        ##################
        # YOUR CODE HERE #
        ##################
        x = self.input(inputs)
        x = self.relu(x)
        x = self.ouput(x)
        return x

# 用于经验回放的缓冲区
class ReplayBuffer:
    def __init__(self, buffer_size):
        ##################
        # YOUR CODE HERE #
        ##################
        self.buffer_size = buffer_size
        self.buffer = []

    def __len__(self):
        ##################
        # YOUR CODE HERE #
        ##################
        return len(self.buffer)

    def push(self, *transition):
        ##################
        # YOUR CODE HERE #
        ##################
        if len(self.buffer) >= self.buffer_size:
            self.buffer.pop(0)
        self.buffer.append(transition)

    def sample(self, batch_size):
        ##################
        # YOUR CODE HERE #
        ##################
        return random.sample(self.buffer, batch_size)

    def clean(self):
        ##################
        # YOUR CODE HERE #
        ##################
        self.buffer = []


class AgentDQN():
    def __init__(self, env, args):
        """
        Initialize every things you need here.
        For example: building your model
        初始化你需要的任何东西，例如构建你的模型
        """
        # super(AgentDQN, self).__init__(env)
        ##################
        # YOUR CODE HERE #
        ##################
        self.args = args
        self.env = env
        self.hidden_size = args.hidden_size
        self.batch_size = 16
        self.lr = args.lr
        self.gamma = args.gamma
        self.buffer_size = 10000
        self.epsilon = 0.01
        self.max_steps = 10
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        random.seed(args.seed)
        np.random.seed(args.seed)
        # self.env.seed(args.seed)
        torch.manual_seed(args.seed)

        self.q_network = QNetwork(env.observation_space.shape[0], self.hidden_size, env.action_space.n).to(self.device)
        self.target_q_network = QNetwork(env.observation_space.shape[0], self.hidden_size, env.action_space.n).to(self.device)
        self.target_q_network.load_state_dict(self.q_network.state_dict())

        self.optimizer = optim.Adam(self.q_network.parameters(), lr = self.lr)
        self.loss_fn = nn.MSELoss()
        self.replay_buffer = ReplayBuffer(self.buffer_size)

        # 更新频率
        self.target_update = 10
        # 迭代次数
        self.num_episodes = 500
        self.step = 0
        self.mini_size = 100
        self.reward_list = []

    def init_game_setting(self):
        """

        Testing function will call this function at the begining of new game
        Put anything you want to initialize if necessary
        测试函数将会调用这个函数在新游戏的一开始
        将你想要初始化的所有东西放在这里
        """
        ##################
        # YOUR CODE HERE #
        ##################
        pass

    def train(self):
        """
        Implement your training algorithm here
        实现训练算法
        """
        ##################
        # YOUR CODE HERE #
        ##################
        if self.replay_buffer.__len__() < self.mini_size:
            return

        batch = self.replay_buffer.sample(self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.tensor(states, dtype=torch.float32).to(self.device)
        actions = torch.tensor(actions, dtype=torch.int64).unsqueeze(1).to(self.device)
        rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1).to(self.device)
        next_states = torch.tensor(next_states, dtype=torch.float32).to(self.device)
        dones = torch.tensor(dones, dtype=torch.float32).unsqueeze(1).to(self.device)

        q_values = self.q_network(states).gather(1, actions)
        # next_q_values = self.target_q_network(next_states).max(1, keepdim=True)[0]
        next_q_values = self.target_q_network(next_states).max(1)[0].view(-1, 1)
        target_q_values = rewards + (self.gamma * next_q_values * (1 - dones))

        loss = self.loss_fn(q_values, target_q_values.detach())
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.step % self.target_update == 0:
            self.target_q_network.load_state_dict(self.q_network.state_dict())

        self.step += 1

    def make_action(self, observation, test=True):
        """
        Return predicted action of your agent
        Input:observation
        Return:action
        返回预测的动作
        输入是观察
        输出是动作
        """
        ##################
        # YOUR CODE HERE #
        ##################
        if test or random.random() > self.epsilon:
            observation = torch.tensor(observation, dtype=torch.float32).unsqueeze(0).to(self.device)
            # with torch.no_grad():
            q_values = self.q_network(observation).to(self.device)
            action = q_values.max(1)[1].item()
        else:
            action = action = np.random.randint(self.env.action_space.n)

        return action

    def run(self):
        """
        Implement the interaction between agent and environment here
        实现智能体与环境的互动
        """
        ##################
        # YOUR CODE HERE #
        ##################
        for episode in range(self.num_episodes):
            state = self.env.reset()[0]
            total_reward = 0
            while True:
                action = self.make_action(state, test=False)
                next_state, reward, terminated, truncated, _ = self.env.step(action)
                done = terminated or truncated
                total_reward += reward

                self.replay_buffer.push(state, action, reward, next_state, done)
                state = next_state

                self.train()

                if done:
                    break

            print(f"Episode {episode}, Total Reward: {total_reward}")
            self.reward_list.append(total_reward)
        return self.reward_list
