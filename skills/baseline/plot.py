import os
import pickle

import pandas
import seaborn as sns
import matplotlib.pyplot as plt


def first_char_upper(game_name):
    """
    make the first letter upper case
    """
    return game_name[0].upper() + game_name[1:]


def plot_eight_procgen_games(results_dir):
    """
    plot the eight procgen games in one big plot
    """
    games = ['bigfish', 'coinrun', 'dodgeball', 'heist', 'jumper', 'leaper', 'maze', 'ninja']
    nrows = 2
    ncols = 4
    figsize = (22, 12)
    if ncols == 2:
        figsize = (17, 20)
    fig, axes = plt.subplots(nrows, ncols, sharex=True, figsize=figsize)
    for i, game in enumerate(games):
        experiment_dir = os.path.join(results_dir, game)
        # get data
        rewards_mean = process_training_curve_csv_file(experiment_dir)
        # plot
        sns.lineplot(
            ax=axes[i // ncols, i % ncols],
            data=rewards_mean,
            x='level_total_steps',
            y='ep_reward_mean',
            hue='agent',
            style='agent',
            errorbar='se',
        )
        # title 
        axes[i // ncols, i % ncols].set_title(first_char_upper(game), fontsize=22)
        # ylabel
        if i % ncols == 0:
            axes[i // ncols, i % ncols].set_ylabel('Episodic Reward', fontsize=20)
        else:
            axes[i // ncols, i % ncols].set_ylabel('')
        # xlabel
        axes[i // ncols, i % ncols].set_xlabel('Steps', fontsize=20)
        # ticks
        axes[i // ncols, i % ncols].tick_params(axis='y', which='major', labelsize=15)
        if ncols == 2:
            axes[i // ncols, i % ncols].tick_params(axis='x', which='major', labelsize=15)
        # shared legend
        axes[i // ncols, i % ncols].legend().remove()
        if i == ncols * nrows - 1:
            handles, labels = axes[i // ncols, i % ncols].get_legend_handles_labels()
            fig.legend(handles, labels, loc='lower center', ncol=4, prop={'size': 22})
    
    # adjustments
    if ncols == 4:
        plt.subplots_adjust(wspace=0.2, hspace=0.2, right=0.96, left=0.07, bottom=0.13, top=0.90)
    elif ncols == 2:
        plt.subplots_adjust(wspace=0.2, hspace=0.25, right=0.96, left=0.07, bottom=0.08, top=0.92)
    fig.suptitle('Training Curve Averaged Across Levels', fontsize=25)

    # save
    save_path = os.path.join(results_dir, 'procgen_results.png')
    fig.savefig(save_path)
    with open(os.path.join(results_dir, 'procgen_results.pkl'), 'wb') as f:
        pickle.dump((fig, axes), f)
    print(f'saved to {save_path}')


def process_training_curve_csv_file(exp_dir, average_across_levels=True):
    """
    read from the progress.csv file and return a dataframe with the relevant information
    find all the csv files in exp_dir (all seeds, and all agents) and process all
    """
    rewards = []
    for agent in os.listdir(exp_dir):
        agent_dir = os.path.join(exp_dir, agent)
        if not os.path.isdir(agent_dir):
            continue
        for seed in os.listdir(agent_dir):
            seed_dir = os.path.join(agent_dir, seed)
            csv_path = os.path.join(seed_dir, 'progress.csv')
            assert os.path.exists(csv_path)
            try:
                df = pandas.read_csv(csv_path, comment='#')
            except pandas.errors.EmptyDataError:
                raise
            assert df['total_steps'].max() == 10_000_000, f"total steps is not complete (20 * 500k): {csv_path}"  # check that csv is complete
            df = df[['level_total_steps', 'level_index', 'ep_reward_mean', 'total_steps']].copy()
            df['agent'] = first_char_upper(agent)
            df['seed'] = int(seed)
            rewards.append(df)
    rewards = pandas.concat(rewards, ignore_index=True)
    max_nan_step = rewards.loc[rewards.isna().any(axis=1)]['level_total_steps'].max()
    subset = rewards.query(f"level_total_steps > {max_nan_step}")

    if not average_across_levels:
        # sparsify the data because confidence interval will take a long time
        subset = subset[subset['level_total_steps'] % 5_000 == 0]
        return subset

    # average across different level_index
    rewards_mean = subset.groupby(['level_total_steps', 'agent', 'seed']).mean().reset_index()
    return rewards_mean


def plot_transfer_exp_training_curve_across_levels(exp_dir, unrolled=False):
    """
    x-axis: steps in each level
    y-axis: reward, averaged across different levels
    if plotting the unrolled curve, we will not average across the levels
    """
    rewards_mean = process_training_curve_csv_file(exp_dir, average_across_levels=not unrolled)
    to_plot_x = 'total_steps' if unrolled else 'level_total_steps'
    # plot
    if unrolled:
        plt.figure(figsize=(10, 5))
    sns.lineplot(
        data=rewards_mean,
        x=to_plot_x,
        y='ep_reward_mean',
        hue='agent',
        style='agent',
        errorbar='se',
    )
    plt.title(f'Training Curve Averaged Across Levels :{exp_dir}')
    plt.xlabel('Steps')
    plt.ylabel('Episodic Reward')
    file_name = '/training_curve.png' if not unrolled else '/training_curve_unrolled.png'
    save_path = os.path.dirname(exp_dir) + file_name
    plt.savefig(save_path)
    print(f'saved to {save_path}')
    plt.close()


def plot_transfer_exp_all_level_curves(exp_dir):
    """
    x-axis: steps in each level
    y-axis: reward in a single level
    there should be 20 lines (one for each level)
    This is mainly used for debugging purposes
    """
    rewards = process_training_curve_csv_file(exp_dir, average_across_levels=False)
    agents = rewards['agent'].unique()
    agents.sort()
    assert len(agents) == 4
    # constraints 
    rewards = rewards.groupby(['level_index', 'level_total_steps', 'agent']).mean().reset_index()  # average across seeds
    rewards = rewards[rewards['level_index'] < 20]
    
    nrows = 2
    ncols = 2
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20, 14))
    for i, agent in enumerate(agents):
        agent_rewards = rewards[rewards['agent'] == agent]
        # plot
        sns.lineplot(
            ax=axes[i // ncols, i % ncols],
            data=agent_rewards,
            x='level_total_steps',
            y='ep_reward_mean',
            hue='level_index',
            style='agent',
            errorbar=('ci', False),
        )
        axes[i // ncols, i % ncols].set_title(agent, fontsize=20)
        # axes[i // ncols, i % ncols].set_ylim(0, 2)

    save_path = os.path.dirname(exp_dir) + '/all_level_learning_curve.png'
    fig.savefig(save_path)
    print(f'saved to {save_path}')
    plt.close()


def plot_transfer_exp_eval_curve(exp_dir):
    """
    x-axis: levels
    y-axis: eval reward at that level, averaged across the last few timesteps
    """
    rewards = []
    for agent in os.listdir(exp_dir):
        agent_dir = os.path.join(exp_dir, agent)
        if not os.path.isdir(agent_dir):
            continue
        for seed in os.listdir(agent_dir):
            seed_dir = os.path.join(agent_dir, seed)
            csv_path = os.path.join(seed_dir, 'progress.csv')
            assert os.path.exists(csv_path)
            df = pandas.read_csv(csv_path, comment='#')
            df = df[['level_total_steps', 'eval_ep_reward_mean', 'level_index']].copy()
            df = df.groupby('level_index').tail(100)  # only keep the last 20 timesteps
            df = df.groupby('level_index').mean().reset_index()  # and mean across those timesteps
            df['agent'] = agent
            df['seed'] = int(seed)
            rewards.append(df)
    rewards = pandas.concat(rewards, ignore_index=True)

    # plot
    sns.lineplot(
        data=rewards,
        x='level_index',
        y='eval_ep_reward_mean',
        hue='agent',
        style='agent',
        errorbar='se',
    )
    plt.title(f'Eval Reward after Trained on Level 1 - k: {exp_dir}')
    plt.xlabel('Level')
    plt.ylabel('Eval Reward (averaged over last 20 steps at level k)')
    plt.xticks(range(len(rewards['level_index'].unique())))
    save_path = os.path.dirname(exp_dir) + '/eval_curve.png'
    plt.savefig(save_path)
    print(f'saved to {save_path}')
    plt.close()


def plot_reward_curve(csv_dir):
    """
    this is used to plot for a single agent
    read progress.csv and plot the reward curves, save in the save dir as csv
    """
    csv_path = os.path.join(csv_dir, 'progress.csv')
    df = pandas.read_csv(csv_path, comment='#')

    # get rid of the NaN data points
    max_nan_step = df.loc[df.isna().any(axis=1)]['level_total_steps'].max()
    df = df.query(f"level_total_steps > {max_nan_step}")

    steps = df['total_steps']
    train_reward = df['ep_reward_mean']
    eval_reward = df['eval_ep_reward_mean']
    plt.plot(steps, train_reward, label='train')
    plt.plot(steps, eval_reward, label='eval')
    plt.legend()
    plt.title('Learning Curve')
    plt.xlabel('Steps')
    plt.ylabel('Episodic Reward')
    save_path = os.path.dirname(csv_path) + '/learning_curve.png'
    plt.savefig(save_path)
    plt.close()


def plot_train_eval_curve(exp_dir, kind='eval'):
    """
    plot the eval-curve of ensemble 1 and ensemble 3 and compare
    """
    assert kind in ['eval', 'train']
    keyword = 'eval_ep_reward_mean' if kind == 'eval' else 'ep_reward_mean'
    rewards = []
    for agent in os.listdir(exp_dir):
        if agent not in ['ensemble-1', 'ensemble-3']:
            continue
        agent_dir = os.path.join(exp_dir, agent)
        for seed in os.listdir(agent_dir):
            seed_dir = os.path.join(agent_dir, seed)
            csv_path = os.path.join(seed_dir, 'progress.csv')
            assert os.path.exists(csv_path)
            
            df = pandas.read_csv(csv_path, comment='#')
            # get rid of the NaN data points
            max_nan_step = df.loc[df.isna().any(axis=1)]['level_total_steps'].max()
            df = df.query(f"level_total_steps > {max_nan_step}")

            df = df[['total_steps', keyword]].copy()
            sparsity = 5  # only plot every 4 points
            df = df[df.total_steps % (sparsity * 800) == 0]
            df[[keyword]] = df[[keyword]].rolling(20).mean()  # rolling mean to denoise
            df['agent'] = agent
            df['seed'] = int(seed)
            rewards.append(df)

    rewards = pandas.concat(rewards, ignore_index=True)

    # plot
    sns.lineplot(
        data=rewards,
        x='total_steps',
        y=keyword,
        hue='agent',
        style='agent',
        errorbar='se',
    )
    plt.title(f'{kind} Curve')
    plt.xlabel('Steps')
    plt.ylabel('Episodic Reward')
    save_path = os.path.dirname(exp_dir) + f'/{kind}_curve.png'
    plt.savefig(save_path)
    print(f'saved to {save_path}')
    plt.close()


def plot_all_agents_reward_data(exp_dir):
    """
    given an experiments dir, find all the subdirs that represent different agents
    and gather their eval_ep_reward_mean data
    """
    rewards = []
    for agent in os.listdir(exp_dir):
        agent_dir = os.path.join(exp_dir, agent)
        if not os.path.isdir(agent_dir):
            continue
        for seed in os.listdir(agent_dir):
            seed_dir = os.path.join(agent_dir, seed)
            csv_path = os.path.join(seed_dir, 'progress.csv')
            assert os.path.exists(csv_path)
            df = pandas.read_csv(csv_path, comment='#')
            # get rid of the NaN data points
            max_nan_step = df.loc[df.isna().any(axis=1)]['level_total_steps'].max()
            df = df.query(f"level_total_steps > {max_nan_step}")
            # df = df[df['total_steps'] % 32000 == 0]

            eval_df = df[['total_steps', 'eval_ep_reward_mean']].copy()
            eval_df['seed'] = int(seed)
            eval_df['agent'] = agent
            eval_df['kind'] = 'eval'
            eval_df.rename(columns={'eval_ep_reward_mean': 'reward'}, copy=False, inplace=True)

            train_df = df[['total_steps', 'ep_reward_mean']].copy()
            train_df['seed'] = int(seed)
            train_df['agent'] = agent
            train_df['kind'] = 'train'
            train_df.rename(columns={'ep_reward_mean': 'reward'}, copy=False, inplace=True)

            new_df = pandas.concat([eval_df, train_df], ignore_index=True)
            rewards.append(new_df)
    rewards = pandas.concat(rewards, ignore_index=True)

    # plot
    sns.lineplot(
        data=rewards,
        x='total_steps',
        y='reward',
        hue='agent',
        style='kind',
        errorbar='se',
    )
    plt.title(f'Learning Curve: {exp_dir}')
    plt.xlabel('Steps')
    plt.ylabel('Episodic Reward')
    save_path = os.path.join(exp_dir, 'learning_curve.png')
    plt.savefig(save_path)
    plt.close()


def plot_all_agents_generalization_gap(exp_dir):
    """
    given an experiment dir, find all the subdirs that represent different agents
    and plot the difference between the training reward curve and the eval reward curve
    """
    rewards = []
    for agent in os.listdir(exp_dir):
        agent_dir = os.path.join(exp_dir, agent)
        if not os.path.isdir(agent_dir):
            continue
        for seed in os.listdir(agent_dir):
            seed_dir = os.path.join(agent_dir, seed)
            csv_path = os.path.join(seed_dir, 'progress.csv')
            assert os.path.exists(csv_path)
            df = pandas.read_csv(csv_path, comment='#')
            # get rid of the NaN data points
            max_nan_step = df.loc[df.isna().any(axis=1)]['level_total_steps'].max()
            df = df.query(f"level_total_steps > {max_nan_step}")

            new_df = df[['total_steps']].copy()
            new_df['seed'] = int(seed)
            new_df['agent'] = agent
            new_df['reward_diff'] = df['ep_reward_mean'] - df['eval_ep_reward_mean']
            rewards.append(new_df)
        rewards = pandas.concat(rewards, ignore_index=True)

    # plot
    sns.lineplot(
        data=rewards,
        x='total_steps',
        y='reward_diff',
        hue='agent',
        style='agent',
        errorbar='se',
    )
    plt.title(f'Generalization Gap: {exp_dir}')
    plt.xlabel('Steps')
    plt.ylabel('Episodic Training Reward - Episodic Eval Reward')
    save_path = os.path.join(exp_dir, 'generalization_gap.png')
    plt.savefig(save_path)
    plt.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', '-l', required=True, help='path to the csv file')
    parser.add_argument('--compare', '-c', action='store_true', help='compare all agents in the same dir', default=False)
    parser.add_argument('--gap', '-g', action='store_true', help='plot the generalization gap', default=False)
    parser.add_argument('--evaluation', '-e', action='store_true', help='plot the evaluation curve', default=False)
    parser.add_argument('--train', '-t', action='store_true', help='plot the training curve', default=False)
    parser.add_argument('--transfer', '-f', action='store_true', help='plot the transfer curve', default=False)
    parser.add_argument('--unrolled', '-u', action='store_true', help='the transfer curve, but do not average acorss level', default=False)
    parser.add_argument('--procgen', '-p', action='store_true', help='plot the 8 procgen games combined', default=False)
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode', default=False)
    args = parser.parse_args()
    if args.compare:
        plot_all_agents_reward_data(args.load)
    elif args.gap:
        plot_all_agents_generalization_gap(args.load)
    elif args.evaluation:
        plot_train_eval_curve(args.load, kind='eval')
    elif args.train:
        plot_train_eval_curve(args.load, kind='train')
    elif args.transfer:
        if args.debug:
            plot_transfer_exp_all_level_curves(args.load)
        else:
            # plot_transfer_exp_eval_curve(args.load)
            plot_transfer_exp_training_curve_across_levels(args.load, args.unrolled)
    elif args.procgen:
        plot_eight_procgen_games(args.load)
    else:
        plot_reward_curve(args.load)
