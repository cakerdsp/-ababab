import numpy as np
import pandas as pd
from maze_env import Maze
import random

class QLearning:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.1, episode = 50):
        self.actions = actions  # a list
        #学习率
        self.lr = learning_rate
        #奖励折扣因子，标记未来奖励的重要性
        self.gamma = reward_decay
        #探索率
        self.epsilon = e_greedy
        # 迭代次数
        self.episode = episode
        self.times = 0

        self.path = []
        ''' build q table'''
        ############################

        # YOUR IMPLEMENTATION HERE #

        ############################
        #状态用智能体的坐标来表示
        self.q_table = {}



    # 根据当前状态选择动作，使用 ε-greedy 策略。
    # 以概率 ε 选择随机动作（探索），以概率 1-ε 选择 Q 值最大的动作（利用）。
    def choose_action(self, observation):
        self.check_state_exist(observation)
        if np.random.rand() < self.epsilon * (1 - float(self.times) / self.episode):
            action = np.random.choice(self.actions)
        else:
            action = self.get_max_Q_action(self.q_table[observation])
        return action

    # 更新 Q 表中的 Q 值。
    # 接收四个参数：当前状态 s、采取的动作 a、获得的奖励 r、下一个状态 s_。
    def learn(self, s, a, r, s_):
        self.check_state_exist(s)
        self.check_state_exist(s_)
        self.q_table[s][a] = self.q_table[s][a] + self.lr * (r + self.gamma * max(self.q_table[s_]) - self.q_table[s][a])

    # 检查当前状态是否存在于 Q 表中。
    # 如果状态不存在，则将其添加到 Q 表中，以便后续学习
    def check_state_exist(self, state):
        if state not in self.q_table:
            if state == 'good_terminal':
                init_actions = [5.0, 5.0, 5.0, 5.0]
                self.q_table[state] = init_actions
                return
            if state == 'bad_terminal':
                init_actions = [-5.0, -5.0, -5.0, -5.0]
                self.q_table[state] = init_actions
                return
            init_actions = [0.0, 0.0, 0.0, 0.0]
            self.q_table[state] = init_actions


    def get_max_Q_action(self,state_actions):
        min_val = min(state_actions)
        #不能有负的
        if min_val <= 0:
            min_val = -min_val
            min_val += 1e-3
            state_actions_ = [(x + min_val) for x in state_actions]
        else:
            state_actions_ = [x for x in state_actions]
        action = random.choices(range(len(state_actions_)),state_actions_)[0]
        # return state_actions.index(max(state_actions))
        return action


    def choose_action_test(self,observation):
        self.check_state_exist(observation)
        action = self.get_max_Q_action(self.q_table[observation])
        return action


    def coords_to_state(self, coords):
        x = int((coords[0] - 5) / 40)
        y = int((coords[1] - 5) / 40)
        self.path.append([x,y])

    def path_clear(self):
        self.path = []