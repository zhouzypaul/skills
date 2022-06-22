# skills
portable skills in Reinforcement Learning

## using the ensemble agent
```bash
python3 -m skills.ensemble.train -e experiment_name -s skill_type --start_state room1 --agent ensemble --steps 1000 [--options]  # train
python3 -m skills.ensemble.test -l saving_dir_to_load [--options]  # test
python3 -m skills.ensemble.transfer -l experiment_name_to_load -t a_list_of_targets -s skill_type --agent ensemble -s skill_type  # transfer and meta learn
python3 -m skills.ensemble.transfer --plot -l load -t a_list_of_targets -s skill_type --agent ensemble # plot after transfer experiment
```

## getting baseline performance (DQN)
```bash
python3 -m skills.baseline.train --experiment_name debug --agent dqn --env MontezumaRevengeNoFrameskip-v4 [--options]  # train  
```

## training a skill
```shell
python3 -m skills.train [--options]
```

## executing a skill
```shell
python3 -m skills.execute --saved_option saving_path [--options]
```

## control an agent to step through a gym env
```shell
python3 -m skills.play [--options]
```

## control an agent to generate trajectories
```shell
python3 -m skills.generate_traj [--options]
```
