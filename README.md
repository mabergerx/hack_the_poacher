# Hack the Poacher

This repository serves as an entry point for training and visualizing reinforcement learning algorithms that relate to the field of Green Security Games. It was developed for the 2020 Data Systems Project of the Information Studies Master's program at the University of Amsterdam. 

## Requirements

1. Python 2.7 for running the Pac-Man module
2. Python 3.6.4+ for running the DeDOL module
3. [direnv](https://direnv.net/)

## direnv

direnv eases the use of the module by providing a streamlined automatic creation of the needed development environment. It first creates a virtual Python environment and then installs all the needed packages.

## Foundations

### Pac-Man (single agent (tabular) reinforcement learning)

We based our Pac-Man implementation on the [Berkeley AI Reinforcement Learning project](http://ai.berkeley.edu/reinforcement.html). We adjusted certain reward numbers, the way ghost operates (PatrolGhost) and  we added our own layout generation scripts, among multiple minor adjustments. 

To train a tabular Q-learning based model you can use where `x` indicates the amount of training episodes and `n` indicates `x + test games` amount, so to train for 10000 games and test the agent on another 15 games, you use:

`python2.7 pacman.py -p PacmanQAgent -x 10000 -n 10015`

To record a game for future retrieval (for example when training the agent on a remote server) you can use the `-r` flag. To then playback the recorded game, you use:

`python2.7 pacman.py -p PacmanQAgent  --replay ./recorded-games-approximateqlearning/recorded-game-791001score:2448`

### DeDOL (multi agent (deep) reinforcement learning)

We based our implementation of the algorithm on the paper [Deep Reinforcement Learning for Green Security Games with Real-Time Information', AAAI 2019](https://github.com/AIandSocialGoodLab/DeDOL). We modified the [original codebase](https://github.com/AIandSocialGoodLab/DeDOL) heavily to extend and tailor it to our specific case of using sensor information. We introduced multiple information-based parameters such as a filter signal on the poacher, detection probability for the ranger, the ability for the agents to look in cells around them and introducing tourist noise. We have also simplified the original reward function to the point of only including rewarding the poacher for caught animals and getting home safely, and the ranger actually preventing the poaching of animals and catching the poacher.

For this implementation, we created an interactive wizard from which you can both train and test trained models. You can train a model by supplying parameters which are retrieved by multiple non-expert friendly prompts. 

You can use this wizard by calling

`python HTP_wizard.py`

