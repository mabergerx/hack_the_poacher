import numpy as np
import argparse
import sys
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import os
from threading import Thread
import time

from patroller_cnn import Patroller_CNN
from patroller_rule import Patroller_Rule as Patroller_h
from poacher_cnn import Poacher
from poacher_rule import Poacher as Poacher_h
from env import Env
from replay_buffer import ReplayBuffer
from DeDOL_util import simulate_payoff
from DeDOL_util import calc_pa_best_response_PER as calc_pa_best_response
from DeDOL_util import extend_payoff
from DeDOL_util import calc_NE,calc_NE_zero
from DeDOL_util import calc_po_best_response_PER as calc_po_best_response
from DeDOL_util import tf_copy
from patroller_randomsweeping import RandomSweepingPatroller
from maps import Mountainmap, generate_map
from GUI_util import test_gui



global eps_pa
global eps_po
global pa_start_num
global po_strat_num 
eps_pa, eps_po = [], []
pa_strat_num, po_strat_num = 0, 0


def main(wizard_args=None):

    argparser = argparse.ArgumentParser()
    ########################################################################################
    ### Presets
    argparser.add_argument('--exac_loc_always_no_noise', type=bool, default=False)
    argparser.add_argument('--exac_loc_always_with_noise', type=bool, default=False)
    argparser.add_argument('--blur_loc_always_no_noise', type=bool, default=False)
    argparser.add_argument('--blur_loc_always_with_noise', type=bool, default=False)
    argparser.add_argument('--exac_loc_50_no_noise', type=bool, default=False)

    argparser.add_argument('--exac_loc_always_no_noise_no_vis', type=bool, default=False) #no files for this
    argparser.add_argument('--exac_loc_always_with_noise_no_vis', type=bool, default=False) #no files for this
    argparser.add_argument('--blur_loc_always_no_noise_no_vis', type=bool, default=False)
    argparser.add_argument('--blur_loc_always_with_noise_no_vis', type=bool, default=False)
    argparser.add_argument('--exac_loc_50_no_noise_no_vis', type=bool, default=False) #no files for this

    ### Changes by us
    argparser.add_argument('--footsteps', type=bool, default=False)
    argparser.add_argument('--po_bleeb', type=bool, default=False)
    argparser.add_argument('--filter_bleeb', type=bool, default=False)
    argparser.add_argument('--see_surrounding', type=bool, default=False)

    argparser.add_argument('--tourist_noise', type=float, default=0.01)
    argparser.add_argument('--po_scan_rate', type=float, default=0.10)

    argparser.add_argument('--extra_sensor_pa', type=bool, default=False)
    argparser.add_argument('--extra_sensor_po', type=bool, default=False)

    ### Test parameters
    argparser.add_argument('--pa_load_path', type=str, default='./Results5x5/')
    argparser.add_argument('--po_load_path', type=str, default='./Results5x5/')
    argparser.add_argument('--load', type=bool, default=False)

    ### Environment
    argparser.add_argument('--row_num', type=int, default=3)
    argparser.add_argument('--column_num', type=int, default=3)
    argparser.add_argument('--ani_den_seed', type=int, default=66)
    argparser.add_argument('--max_time', type=int, default=50)

    ### Patroller
    argparser.add_argument('--pa_state_size', type=int, default=-1)
    argparser.add_argument('--pa_num_actions', type=int, default=5)

    ### Poacher CNN
    argparser.add_argument('--snare_num', type=int, default=1)
    argparser.add_argument('--po_state_size', type=int, default=-1)  # yf: add self footprint to poacher
    argparser.add_argument('--po_num_actions', type=int, default=5)

    ### Poacher Rule Base
    argparser.add_argument('--po_act_den_w', type=float, default=3.)
    argparser.add_argument('--po_act_enter_w', type=float, default=0.3)
    argparser.add_argument('--po_act_leave_w', type=float, default=-1.0)
    argparser.add_argument('--po_act_temp', type=float, default=5.0)
    argparser.add_argument('--po_home_dir_w', type=float, default=3.0)

    ### Training
    argparser.add_argument('--map_type', type=str, default='random')
    argparser.add_argument('--advanced_training', type=bool, default=True)
    argparser.add_argument('--save_path', type=str, default='./Results33Parandom/')

    argparser.add_argument('--naive', type=bool, default=False)
    argparser.add_argument('--pa_episode_num', type=int, default=300000)
    argparser.add_argument('--po_episode_num', type=int, default=300000)
    argparser.add_argument('--pa_initial_lr', type=float, default=1e-4)
    argparser.add_argument('--po_initial_lr', type=float, default=5e-5)
    argparser.add_argument('--epi_num_incr', type=int, default=0)
    argparser.add_argument('--final_incr_iter', type=int, default=10)
    argparser.add_argument('--pa_replay_buffer_size', type=int, default=200000)
    argparser.add_argument('--po_replay_buffer_size', type=int, default=100000)
    argparser.add_argument('--test_episode_num', type=int, default=20000)
    argparser.add_argument('--iter_num', type=int, default=10)
    argparser.add_argument('--po_location', type=int, default=None)
    argparser.add_argument('--Delta', type=float, default=0.0)

    argparser.add_argument('--print_every', type=int, default=50)
    argparser.add_argument('--zero_sum', type=int, default=1)
    argparser.add_argument('--batch_size', type=int, default=32)
    argparser.add_argument('--target_update_every', type=int, default=2000)
    argparser.add_argument('--reward_gamma', type=float, default=0.95)
    argparser.add_argument('--save_every_episode', type=int, default=5000)
    argparser.add_argument('--test_every_episode', type=int, default=2000)
    argparser.add_argument('--gui_every_episode', type=int, default=500)
    argparser.add_argument('--gui_test_num', type=int, default=20)
    argparser.add_argument('--gui', type=int, default=0)
    argparser.add_argument('--mix_every_episode', type=int, default=250)  # new added
    argparser.add_argument('--epsilon_decrease', type=float, default=0.05)  # new added
    argparser.add_argument('--reward_shaping', type=bool, default=False)
    argparser.add_argument('--PER', type=bool, default=False)


    #########################################################################################
    args = argparser.parse_args()

    if not args.po_bleeb and args.filter_bleeb:
        raise ValueError('filter_bleeb cannot be true, while po_bleeb is false')

    #### PRESETS ####
    # print("HUH", args)
    # print("WIZARD:", wizard_args)
    # print("JAAA", args.exac_loc_always_with_noise)
    #

    # if args.row_num == 7:
    #     args.column_num = 7
    #     args.max_time = 75


    if wizard_args:
        for k, v in wizard_args.items():
            setattr(args, k, v)
    else:
        pass

    if args.exac_loc_always_no_noise:
        args.po_bleeb = True
        args.po_scan_rate = 1
        args.tourist_noise = 0
        args.filter_bleeb = False

        args.see_surrounding = True
        args.footsteps = False

    elif args.exac_loc_always_with_noise:
        # print("JA DIT TRIGGERED")
        args.po_bleeb = True
        args.po_scan_rate = 1
        args.tourist_noise = 0.05
        args.filter_bleeb = False

        args.column_num = 7
        args.row_num = 7
        args.map_type = "poacher"
#log_file = open('./Results_33_random/log.txt', 'w')
        args.see_surrounding = True
        args.footsteps = False

    elif args.blur_loc_always_no_noise:
        args.po_bleeb = True
        args.po_scan_rate = 1
        args.tourist_noise = 0
        args.filter_bleeb = True

        args.column_num = 7
        args.row_num = 7
        args.map_type = "poacher"
        args.see_surrounding = True
        args.footsteps = False

    elif args.blur_loc_always_with_noise:
        args.po_bleeb = True
        args.po_scan_rate = 1
        args.tourist_noise = 0.05
        args.filter_bleeb = False

        args.column_num = 7
        args.row_num = 7
        args.map_type = "poacher"
        args.see_surrounding = True
        args.footsteps = False

    elif args.exac_loc_50_no_noise:
        args.po_bleeb = True
        args.po_scan_rate = 0.5
        args.tourist_noise = 0
        args.filter_bleeb = False

        args.see_surrounding = True
        args.footsteps = False

    elif args.exac_loc_always_no_noise_no_vis:
        args.po_bleeb = True
        args.po_scan_rate = 1
        args.tourist_noise = 0
        args.filter_bleeb = False

        args.see_surrounding = False
        args.footsteps = False

        args.map_type = 'poacher'
        args.naive = True
        args.row_num = 7
        args.column_num = 7


    elif args.exac_loc_always_with_noise_no_vis:
        args.po_bleeb = True
        args.po_scan_rate = 1
        args.tourist_noise = 0.05
        args.filter_bleeb = False

        args.see_surrounding = False
        args.footsteps = False

        args.map_type = 'poacher'
        args.naive = True
        args.row_num = 7
        args.column_num = 7

    elif args.blur_loc_always_no_noise_no_vis:
        args.po_bleeb = True
        args.po_scan_rate = 1
        args.tourist_noise = 0
        args.filter_bleeb = True

        args.see_surrounding = False
        args.footsteps = False

        args.map_type = 'poacher'
        args.naive = True
        args.row_num = 7
        args.column_num = 7

    elif args.blur_loc_always_with_noise_no_vis:
        args.po_bleeb = True
        args.po_scan_rate = 1
        args.tourist_noise = 0
        args.filter_bleeb = True

        args.see_surrounding = False
        args.footsteps = False

        args.map_type = 'poacher'
        args.naive = True
        args.row_num = 7
        args.column_num = 7

    elif args.exac_loc_50_no_noise_no_vis:
        args.po_bleeb = True
        args.po_scan_rate = 0.5
        args.tourist_noise = 0
        args.filter_bleeb = False

        args.see_surrounding = False
        args.footsteps = False

        args.map_type = 'poacher'
        args.naive = True
        args.row_num = 7
        args.column_num = 7


    if args.po_state_size == -1:
        args.po_state_size = 14 + (8 * args.footsteps) + (1 * args.see_surrounding) + (1 * args.extra_sensor_po)

    if args.pa_state_size == -1:
        args.pa_state_size = 12 + (8 * args.footsteps) + (1 * args.po_bleeb) + (1 * args.see_surrounding) + (
                    1 * args.extra_sensor_pa)


    print("ARGS IN GUI:", args)
    ################## for initialization ###########################
    global log_file

    # log_file = open('./Results_33_random/log.txt', 'w')
    # log_file = open('./Results_33_random/log.txt', 'w')

    animal_density = generate_map(args)
    # env = Env(args, animal_density, cell_length=None, canvas=None, gui=False)

    patrollers = [Patroller_CNN(args, 'pa_model' + str(i)) for i in range(5)]
    poachers = [Poacher(args, 'po_model' + str(i)) for i in range(5)]

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.Session(config=config)
    sess.run(tf.global_variables_initializer())

    args.po_location = None
    ### load the DQN models you have trained
    if args.load:
        # poachers[0] = Poacher_h(args, animal_density)
        # patrollers[0] = Patroller_h(args, animal_density)

        poachers[1].load(sess, args.po_load_path)
        patrollers[1].load(sess, args.pa_load_path)

        test_gui(poachers[1], patrollers[1], sess, args, pa_type='DQN', po_type='DQN')

    ### test the random sweeping patroller and the heuristic poacher
    else:
        poacher = Poacher_h(args, animal_density)
        patroller = RandomSweepingPatroller(args)
        test_gui(poacher, patroller, sess, args, pa_type='RS', po_type='PARAM')


if __name__ == "__main__":
    main()
