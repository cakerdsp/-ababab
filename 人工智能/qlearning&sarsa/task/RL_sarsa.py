import random
from maze_env import Maze
import numpy as np
import pandas as pd


class Sarsa:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9,episode = 50):
        self.actions = actions  # a list
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.episode = episode
        self.times = 0
        self.path = []
        ''' build q table'''
        ############################

        # YOUR IMPLEMENTATION HERE #

        ############################
        self.q_table = {}

    def choose_action(self, observation):
        self.check_state_exist(observation)
        if np.random.rand() < self.epsilon * (1 - float(self.times) / self.episode):
            action = np.random.choice(self.actions)
        else:
            action = self.get_max_Q_action(self.q_table[observation])
        return action

    def choose_action_test(self,observation):
        self.check_state_exist(observation)
        action = self.get_max_Q_action(self.q_table[observation])
        return action

    def learn(self, s, a, r, s_):
        self.check_state_exist(s)
        self.check_state_exist(s_)
        a_ = self.choose_action(s_)
        self.q_table[s][a] = self.q_table[s][a] + self.lr * (r + self.gamma * self.q_table[s_][a_] - self.q_table[s][a])
        return a_


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
            min_val += 1e-6
            state_actions_ = [x + min_val for x in state_actions]
        else:
            state_actions_ = [x for x in state_actions]
        action = random.choices(range(len(state_actions_)),state_actions_)[0]
        # return state_actions.index(max(state_actions))
        return action



    def coords_to_state(self, coords):
        x = int((coords[0] - 5) / 40)
        y = int((coords[1] - 5) / 40)
        self.path.append([x,y])

    def path_clear(self):
        self.path = []