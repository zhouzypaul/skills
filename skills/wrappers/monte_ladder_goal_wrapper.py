import os

import numpy as np
from gym import Wrapper

from skills.option_utils import get_player_position, get_player_room_number


class GoalsCollection:
    def __init__(self, room, file_names, goal_file_dir='resources/monte_info'):
        """
        room: the room number these goals are in
        file_names: a list of filenames of the np arrays that store the goal positions
        goal_file_dir: where the goal files are stored
        """
        self.room = room
        self.goals = [np.loadtxt(os.path.join(goal_file_dir, f)) for f in file_names]
    
    def __len__(self):
        return len(self.goals)
    
    def __contains__(self, item):
        """
        make sure the argument item is a numpy array
        """
        return item in self.goals
    
    def is_within_goal_position(self, room_number, player_pos, tol):
        """
        check that whether the player is within an epsilon tolerance to one of 
        the goal positions
        args:
            player_pos: make sure this is np array: (x, y)
            tol: pixel-wise tolerance from the ground truth goal
        """
        if room_number != self.room:
            return False
        for goal in self.goals:
            if np.linalg.norm(player_pos - goal) < tol:
                return True
        return False


room_to_goals = {
    0: GoalsCollection(0, [
        'room0_ladder_bottom_pos.txt'
    ]),
    1: GoalsCollection(1, [
        'middle_ladder_bottom_pos.txt',
        'right_ladder_bottom_pos.txt',
        'left_ladder_bottom_pos.txt',
    ]),
    2: GoalsCollection(2, [
        'room2_ladder_bottom_pos.txt'
    ]),
    3: GoalsCollection(3, [
        'room3_ladder_bottom_pos.txt'
    ]),
    4: GoalsCollection(4, [
        'room4_bottom_ladder_bottom_pos.txt'
    ]),
    5: GoalsCollection(5, [
        'room5_ladder_bottom_pos.txt'
    ]),
    6: GoalsCollection(6, [
        'room6_ladder_bottom_pos.txt'
    ]),
    7: GoalsCollection(7, [
        'room7_ladder_bottom_pos.txt'
    ]),
    10: GoalsCollection(10, [
        'room10_ladder_bottom_pos.txt'
    ]),
    11: GoalsCollection(11, [
        'room11_bottom_ladder_bottom_pos.txt'
    ]),
    13: GoalsCollection(13, [
        'room13_bottom_ladder_bottom_pos.txt'
    ]),
    14: GoalsCollection(14, [
        'room14_ladder_bottom_pos.txt'
    ]),
}


class MonteLadderGoalWrapper(Wrapper):
    """
    for training a "go to the bottom of a ladder" skill
    The goals are defined to be the bottom of every ladder in the room the agent
    started out in.
    when the goal is hit, done will be true and the reward will be 1. The other
    default rewards, such as getting a key, are overwritten to be 0.
    """
    def __init__(self, env, epsilon_tol=4, info_only=False):
        """
        Args:
            epsilon_tol: tolerance of nearness to goal, count as within goal 
                            if inside this epsilon ball to the goal
            info_only: if true, don't override the reward and done from the environment, 
                        but only add a field `reached_goal` to the info dict
        """
        super().__init__(env)
        self.env = env
        self.epsilon_tol = epsilon_tol
        self.info_only = info_only
        self.room_number = get_player_room_number(self.env.unwrapped.ale.getRAM())
        self.goal_regions = room_to_goals[self.room_number]
    
    def reached_goal(self, player_pos, room_number):
        """
        determine if the player has reached the goal
        """
        in_same_room = room_number == self.room_number
        in_goal_region = self.goal_regions.is_within_goal_position(room_number, player_pos, self.epsilon_tol)
        return in_same_room and in_goal_region

    def finished_skill(self, player_pos, room_number, done, info):
        """
        determine if the monte agent has finished the skill
        return reward, terminal, info
        """
        # record whether reached goal
        reached_goal = self.reached_goal(player_pos, room_number)
        info['reached_goal'] = reached_goal
        # override
        if reached_goal:
            done = True
            reward = 1
        else:
            reward = 0  # override reward, such as when got key
        # terminate if agent enters another room
        in_same_room = room_number == self.room_number
        if not in_same_room:
            done = True
        # override needs_real_reset for EpisodicLifeEnv
        self.env.unwrapped.needs_real_reset = done or info.get("needs_reset", False)
        return reward, done, info
    
    def step(self, action):
        """
        override done and reward
        """
        next_state, reward, done, info = self.env.step(action)
        ram = self.env.unwrapped.ale.getRAM()
        player_pos = np.array(get_player_position(ram))
        room = get_player_room_number(ram)
        goal_reward, terminal, info = self.finished_skill(player_pos, room, done, info)
        if not self.info_only:
            reward = goal_reward
            done = terminal
        return next_state, reward, done, info
