# 用于解析命令行参数的标准库
import argparse
# OpenAI Gym提供的强化学习环境
import gym
import matplotlib.pyplot as plt
import numpy as np
from argument import dqn_arguments, pg_arguments


# 解析器
def parse():
    parser = argparse.ArgumentParser(description="SYSU_RL_HW2")
    parser.add_argument('--train_pg', default=False, type=bool, help='whether train policy gradient')
    parser.add_argument('--train_dqn', default=True, type=bool, help='whether train DQN')

    parser = dqn_arguments(parser)
    # parser = pg_arguments(parser)
    args = parser.parse_args()
    return args


def run(args):
    # 如果是PG的话
    if args.train_pg:
        env_name = args.env_name
        env = gym.make(env_name)
        from agent_dir.agent_pg import AgentPG
        agent = AgentPG(env, args)
        agent.run()
    # 如果是DQN的话
    if args.train_dqn:
        env_name = args.env_name
        env = gym.make(env_name)
        from agent_dir.agent_dqn import AgentDQN
        # 创建代理
        agent = AgentDQN(env, args)
        # 运行代理
        return agent.run()

def plot_reward(reward_list, n):
    # for i in range(n):
    #     episodes_list = list(range(len(reward_list[0])))
    #     plt.plot(episodes_list, reward_list[i])
    v = np.array(reward_list)
    mean_v = np.mean(v, axis=0)
    std_v = np.std(v, axis=0)
    episodes_list = list(range(len(reward_list[0])))
    plt.plot(episodes_list, mean_v, color = 'r')
    # plt.plot(episodes_list, std_v, color = 'black')
    plt.fill_between(episodes_list, mean_v - std_v, mean_v + std_v, color='red', alpha=0.2, )
    plt.xlabel('Episodes')
    plt.ylabel('Returns')
    plt.title('DQN on CartPole-v0')
    plt.show()

if __name__ == '__main__':
    args = parse()
    rl = []
    rl.append(run(args))
    rl.append(run(args))
    rl.append(run(args))
    plot_reward(rl, len(rl))


