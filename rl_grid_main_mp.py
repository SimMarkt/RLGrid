# ---------------------------------------------------------------------------------------------
# RL_Grid: Grid world for analyzing maximization bias in RL with Q-learning and Double Q-learning
#
# rl_grid_main_mp.py:
# > Main script for running the RL project with multiprocessing
# ---------------------------------------------------------------------------------------------

import numpy as np
import multiprocessing as mp
from tqdm import tqdm
from src.rl_grid_config import RLGridConfiguration
from src.rl_grid_env import GridWorldEnv
from src.rl_grid_agents import QAgent, DoubleQAgent
from src.rl_grid_utils import plot_results

def train_agent(agent_class, config, queue, agent_type):
    """ Train a single agent in a separate process """
    env = GridWorldEnv(config)
    agent = agent_class(config, env.actions)

    q_max_hist = np.zeros((config.num_runs, config.num_episodes))
    q_ae_hist = np.zeros((config.num_runs, config.num_episodes))

    for run in tqdm(range(config.num_runs), desc=f"Training Runs ({agent_type})"):
        agent.reset(config, env.actions)
        for i in range(config.num_episodes):
            state = env.reset(config)['state']
            done = False

            while not done:
                action = agent.take_action(state)
                obs, reward, done = env.step(action)
                next_state = obs['state']
                agent.q_learning_update(state, action, reward, next_state)
                state = next_state
            
            q_max_hist[run, i] = max(agent.q_pi[env.init_state[0], env.init_state[1], a] for a in [0, 2, 3])
            q_ae_hist[run, i] = agent.q_pi[env.init_state[0], env.init_state[1], 1]

    queue.put((agent_type, np.mean(q_max_hist, axis=0), np.mean(q_ae_hist, axis=0)))

def main():
    config = RLGridConfiguration()  
    queue = mp.Queue()  # Use a queue to collect results from processes

    agents = [
        (QAgent, "Q-Learning"),
        (DoubleQAgent, "DoubleQ-Learning")
    ]

    processes = []
    for agent_class, agent_type in agents:
        p = mp.Process(target=train_agent, args=(agent_class, config, queue, agent_type))
        processes.append(p)
        p.start()

    results = {}
    for _ in agents:
        agent_type, q_max_avg, q_ae_avg = queue.get()
        results[agent_type] = (q_max_avg, q_ae_avg)

    for p in processes:
        p.join()

    # Extract results and plot
    plot_results(results["Q-Learning"][0], results["Q-Learning"][1], results["DoubleQ-Learning"][0], results["DoubleQ-Learning"][1])

if __name__ == "__main__":
    main()
