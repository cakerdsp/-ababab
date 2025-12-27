"""
Reinforcement learning maze example.

Red rectangle:          explorer.
Black rectangles:       hells       [reward = -1].
Yellow bin circle:      paradise    [reward = +1].
All other states:       ground      [reward = 0].

This script is the main part which controls the update method of this example.
"""

from maze_env import Maze
from RL_q_learning import QLearning
from RL_sarsa import Sarsa
import matplotlib.pyplot as plt
import random

def update_sarsa():
    good = 0
    bad = 0
    normal = 0
    for episode in range(RL.episode):
        # initial observation
        observation = env.reset()
        # action = random.choice(RL.actions)
        action = RL.choose_action(str(observation))
        while True:
            RL.times += 1
            env.render()
            # action = RL.choose_action(str(observation))
            # RL take action and get next observation and reward
            observation_, reward, done = env.step(action)

            action_ = RL.learn(str(observation), action, reward, str(observation_))
            # swap observation
            observation = observation_
            action = action_
            # break while loop when end of this episode
            if done:
                if observation == 'good_terminal':
                    good += 1
                elif observation == 'bad_terminal':
                    bad += 1
                else:
                    normal += 1
                break
    print(f'Sarsa: good = {good} | bad = {bad} | normal = {normal}')

    # end of game
    print('train over')
    # env.destroy()

def update_q_learning():
    good = 0
    bad = 0
    normal = 0
    for episode in range(RL.episode):
        # initial observation
        observation = env.reset()
        # action = random.choice(RL.actions)
        # action = RL.choose_action(str(observation))
        while True:
            RL.times += 1
            env.render()
            action = RL.choose_action(str(observation))
            # RL take action and get next observation and reward
            observation_, reward, done = env.step(action)

            RL.learn(str(observation), action, reward, str(observation_))
            # swap observation
            observation = observation_
            # action = action_
            # break while loop when end of this episode
            if done:
                if observation == 'good_terminal':
                    good += 1
                elif observation == 'bad_terminal':
                    bad += 1
                else:
                    normal += 1
                break
    print(f'Q-Learning: good = {good} | bad = {bad} | normal = {normal}')

    # end of game
    print('train over')
    # env.destroy()


# def test_sarsa():
#     good = 0
#     bad = 0
#     normal = 0
#     for episode in range(50):
#         # initial observation
#         observation = env.reset()
#         # action = random.choice(RL.actions)
#         # action = RL.choose_action_test(str(observation))
#         while True:
#             env.render()


#             action = RL.choose_action(str(observation))
#             # RL take action and get next observation and reward
#             observation_, reward, done = env.step(action)
#             # action_ = RL.choose_action_test(str(observation_))
#             # action_ = RL.learn(str(observation), action, reward, str(observation_))
#             # swap observation
#             observation = observation_
#             # action = action_
#             if done:
#                 if observation == 'good_terminal':
#                     good += 1
#                 elif observation == 'bad_terminal':
#                     bad += 1
#                 else:
#                     normal += 1
#                 break
#     print(f'good = {good} | bad = {bad} | normal = {normal}')
#     print('game over')
#     env.destroy()

def test():
    good = 0
    bad = 0
    normal = 0
    for episode in range(20):
        # initial observation
        observation = env.reset()
        # action = random.choice(RL.actions)
        while True:
            RL.coords_to_state(observation)
            env.render()
            action = RL.choose_action_test(str(observation))
            # RL take action and get next observation and reward
            observation_, reward, done = env.step(action)
            # swap observation
            observation = observation_
            if done:
                if observation == 'good_terminal':
                    RL.path.append("good")
                    good += 1
                elif observation == 'bad_terminal':
                    RL.path.append("bad")
                    bad += 1
                else:
                    normal += 1
                break
        print(RL.path)
        RL.path_clear()
    print(f'good = {good} | bad = {bad} | normal = {normal}')
    print('game over')
    # env.destroy()
    return good, bad


if __name__ == "__main__":
    env = Maze()

    '''
    build RL Class
    RL = QLearning(actions=list(range(env.n_actions)))
    RL = Sarsa(actions=list(range(env.n_actions)))
    '''
    ############################

    # YOUR IMPLEMENTATION HERE #

    ############################
    #解开对应注释启动对应的算法
    RL = QLearning(actions=list(range(env.n_actions)))
    # RL = Sarsa(actions=list(range(env.n_actions)))
    update_q_learning()
    # update_sarsa()
    success_rate = []
    for i in range(10):
        g,b = test()
        success_rate.append(float(g) / (g + b))
    plt.plot(range(len(success_rate)),success_rate, color = 'g')
    plt.xlabel("episodes")
    plt.ylabel("success_rate")
    plt.show()
    env.destroy()
    # env.after(100, test)
    # env.mainloop()

