import random
import numpy as np
import time
import copy
from tkinter import *
from math import floor

class Env(object):
    def __init__(self, args, animal_density, cell_length, canvas, gui):
        '''
        the game env
        params:
            args: a namespace arg determing all relating properties of the game.
            animal_density: specifying the animal density of each grid.
            cell_length: for GUI usage, determine the lenght of a grid in the GUI window.
            canavas: a tkiner object for GUI showing.
            GUI: bool, whether to show GUI.
        '''
        self.args = args
        self.footsteps = self.args.footsteps
        self.po_bleeb = self.args.po_bleeb
        self.filter_bleeb = self.args.filter_bleeb
        self.tourist_noise = self.args.tourist_noise
        self.po_scan_rate = self.args.po_scan_rate
        self.see_surrounding = self.args.see_surrounding
        self.row_num = self.args.row_num
        self.column_num = self.args.column_num
        self.animal_density = animal_density
        self.gui = gui
        self.poacher_first_home = True
        self.home_flag = False
        self.catch_flag = False
        self.poacher_snare_num = args.snare_num
        self.canvas = None
        self.end_game = False

        if args.extra_sensor_pa:
            from extra_sensor import extra_sensor_pa

        if args.extra_sensor_po:
            from extra_sensor import extra_sensor_po

        self.radar_objs = {}

        if self.gui:
            self.canvas = canvas
            self.canvas_width = args.column_num * cell_length
            self.canvas_height = args.row_num * cell_length
            self.cell_length = cell_length
            self.quarter_cell = cell_length / 4.
            self.cell_3_8 = cell_length * (3. / 8)
            self.cell_5_8 = cell_length * (5. / 8)

    def make_grid(self):
        '''
        For GUI usage, build the game grid world.
        '''
        for x in range(self.cell_length, self.canvas_width, self.cell_length):
            self.canvas.create_line(x, 0, x, self.canvas_height, fill="#476042")
        for y in range(self.cell_length, self.canvas_height, self.cell_length):
            self.canvas.create_line(0, y, self.canvas_width, y, fill="#476042")

        def hex_string(x):
            hex_str = hex(x)
            hex_str = hex_str[2:]
            hex_str = '0' * (2 - len(hex_str)) + hex_str
            return '#' + hex_str * 3

        for row in range(self.args.row_num):
            for col in range(self.args.column_num):
                color = hex_string(int(255 - 255 * self.animal_density[row, col]))
                coord = col * self.cell_length + 2.5*self.quarter_cell,row * self.cell_length + 2.5*self.quarter_cell,col * self.cell_length + 5.5*self.quarter_cell,row * self.cell_length + 5.5* self.quarter_cell
                arc = self.canvas.create_arc(coord, start=90, extent=90, fill=color, outline="")
#                self.canvas.create_oval(col * self.cell_length + 2.5 * self.quarter_cell,
#                                             row * self.cell_length + 2.5 * self.quarter_cell,
#                                             col * self.cell_length + self.cell_length,
#                                             row * self.cell_length + self.cell_length,
#                                             outline="", fill=color)
                if self.animal_density[row,col] <= 0:
                    color = "#%02x%02x%02x" % (98, 211, 245)    
                    if row == 5 and col == 4:
                        color = "dark olive green"
                    elif row == 3 and col == 2:
                        color = "dark olive green"
                    elif row == 5 and col == 6:
                        color = "dark olive green"
                    else:
                        color = "#%02x%02x%02x" % (98, 211, 245)
                    self.canvas.create_rectangle(col * self.cell_length,
                                             row * self.cell_length,
                                             col * self.cell_length + self.cell_length,
                                             row * self.cell_length + self.cell_length,
                                             fill=color)

    def reset_game(self, mode = None):
        '''
        reset all internal variables of the game.
        Params: 
            mode: specify the mode of the game. If none, the mode is args.po_location; if a number, then the mode is the number.
        Return:
            the inital state of poacher and patroller. 
        '''
        self.poacher_snare_num = self.args.snare_num
        self.poacher_first_home = True
        self.home_flag = False
        self.catch_flag = False
        self.po_initial_loc = self.get_po_initial_loc(self.args.po_location)
        if mode is not None:
            if self.row_num == 7:
                self.po_initial_loc = self.get_po_initial_loc(mode, poacher_map = True)
            else:
                self.po_initial_loc = self.get_po_initial_loc(mode)
        self.po_loc = self.po_initial_loc

        if self.row_num == 7:
            self.pa_loc = [0, 6]
        else:
            self.pa_loc = self.pa_initial_loc = [self.row_num //2, self.column_num // 2]
        self.pa_trace = {}
        self.po_trace = {}  # pos -> [(E, W, S, N)_0, (E, W, S, N)_1]
        self.snare_state = []
        self.snare_object = {}
        self.time = 0
        self.end_game = False
        self.pa_memory = np.zeros([self.row_num, self.column_num, 8])  # the memory of footprints
        self.po_memory = np.zeros([self.row_num, self.column_num, 8])
        self.po_self_memory = np.zeros([self.row_num, self.column_num, 8]) #yf: add self footprint mem, [(E,S,W,N)_in, (E,S,W,N)_out]
        self.pa_self_memory = np.zeros([self.row_num, self.column_num, 8]) #yf: add self footprint mem, [(E,S,W,N)_in, (E,S,W,N)_out]
        self.pa_visit_number = np.zeros([self.row_num, self.column_num])
        self.po_visit_number = np.zeros([self.row_num, self.column_num])
        
        for row in range(self.row_num):
            for col in range(self.column_num):
                self.pa_trace[(row, col)] = np.zeros(8)
                self.po_trace[(row, col)] = np.zeros(8)

                
        if self.gui:
            self.canvas.delete("all")
            self.canvas['bg'] = "#%02x%02x%02x" % (218, 235, 213)
            self.make_grid()

            img = PhotoImage(file='po.png')
            self.canvas.img = img
            self.po_ball = self.canvas.create_image((((self.po_loc[1] + 1) * self.cell_length - self.quarter_cell)-(self.po_loc[1] * self.cell_length + self.quarter_cell))/2+(self.po_loc[1] * self.cell_length + self.quarter_cell),
            
            ((self.po_loc[0] * self.cell_length + self.quarter_cell)-((self.po_loc[0] + 1) * self.cell_length - self.quarter_cell))/2+((self.po_loc[0] + 1) * self.cell_length - self.quarter_cell), image=img, tags="ball")
            
            img1 = PhotoImage(file='pa.png')
            self.canvas.img1 = img1
            self.pa_ball = self.canvas.create_image((((self.pa_loc[1] + 1) * self.cell_length - self.quarter_cell)-(self.pa_loc[1] * self.cell_length + self.quarter_cell))/2+(self.pa_loc[1] * self.cell_length + self.quarter_cell),
            
            ((self.pa_loc[0] * self.cell_length + self.quarter_cell)-((self.pa_loc[0] + 1) * self.cell_length - self.quarter_cell))/2+((self.pa_loc[0] + 1) * self.cell_length - self.quarter_cell), image=img1, tags="ball")

        return self.get_pa_state(), self.get_po_state()

    def get_po_mode(self):
        if self.po_initial_loc == [0,0]:
            mode = '0'
        elif self.po_initial_loc == [0,self.column_num - 1]:
            mode = '1'
        elif self.po_initial_loc == [self.row_num - 1,0]:
            mode  = '2'
        elif self.po_initial_loc == [self.row_num - 1,self.column_num - 1]:
            mode = '3'
        return mode

    def step(self, pa_action, po_action, snare_flag, train = True):
        '''
        The environment moves on a step, doing the follows:
            poacher puts snares and move;
            patroller moves;
            poacer returns home if possible;
            patroller removes snares;
            snares kill animals;
            patroller arrest poachers;
        Param: 
            pa_action: patroller move action
            po_action: poacher move action
            snare_flag: If true, poacher puts a snare
            train: if true, reward genetrated in the training mode with reward shaping; if false, test reward
        Return: 
            patroller next state, poacher next state, patroller reward, poacher reward, game_end flag
        '''
        # Place the snare by the poacher
        if snare_flag and self.poacher_snare_num > 0:
            self.place_snare(self.po_loc)
        else:
            self.delete_snare(self.po_loc)

        if self.gui:
            for y in range(0, self.column_num - 1):
                for x in range(0, self.row_num - 1):
                    if (y,x) in self.canvas.keys():
                        self.canvas.delete(self.radar_objs[(y,x)])

        # Update the position and traces of poacher and patroller
        po_ori_loc, po_new_loc = self.update_po_loc(po_action)
        pa_ori_loc, pa_new_loc = self.update_pa_loc(pa_action)
        self.update_pa_memory()
        self.update_po_memory()

        # if poacher has run out of snares and has returned home
        if self.poacher_snare_num == 0 and tuple(self.po_initial_loc) == tuple(self.po_loc) and not tuple(self.pa_loc) == tuple(self.po_loc):
            self.home_flag = True
            if self.gui:
                self.canvas.delete(self.po_ball)
            # With this flag, the patroller cannot catch poacher anymore.
            # the poacher will stay at home at the rest of the episode.

        # Calculate reward for both sides
        # this process includes remove snares and kill animals
        if train:
            pa_reward, po_reward = self.get_reward_train()
        else:
            pa_reward, po_reward = self.get_reward_test()
        
        self.update_time()

        if self.gui:
            if (self.catch_flag and len(self.snare_state) == 0):
                self.canvas.create_text(270,280,fill='#%02x%02x%02x' % (255, 111, 0),font='System 30 bold',text='Poacher caught', tags="text")
                #does not work..
                self.canvas.tag_raise("text")
            if (self.home_flag and len(self.snare_state) == 0):
                self.canvas.create_text(260,280,fill='#%02x%02x%02x' % (255, 111, 0),font='System 30 bold',text='Poacher went home', tags="text")
                #does not work..
                self.canvas.tag_raise("text")
        if (self.catch_flag and len(self.snare_state) == 0) or (self.home_flag and len(self.snare_state) == 0):
            self.end_game = True
        else:
            self.end_game = False

        return self.get_pa_state(), pa_reward, self.get_po_state(), po_reward, self.end_game

    def update_po_loc(self, action):
        # print("_____________________")
        # print("Action PO: ", action)
        if action == 'still':
            self.po_visit_number[self.po_loc[0], self.po_loc[1]] += 1
            return self.po_loc, self.po_loc
            
        if action == 'up':
            new_row, new_col = self.po_loc[0] - 1, self.po_loc[1]
            if self.in_bound(new_row, new_col):
                self.po_self_memory[new_row][new_col][1] = 1 # yf: add to self footprint memory
                self.po_self_memory[self.po_loc[0]][self.po_loc[1]][7] = 1
        elif action == 'down':
            new_row, new_col = self.po_loc[0] + 1, self.po_loc[1]
            if self.in_bound(new_row, new_col):
                self.po_self_memory[new_row][new_col][3] = 1
                self.po_self_memory[self.po_loc[0]][self.po_loc[1]][5] = 1
        elif action == 'left':
            new_row, new_col = self.po_loc[0], self.po_loc[1] - 1
            if self.in_bound(new_row, new_col):
                self.po_self_memory[new_row][new_col][0] = 1
                self.po_self_memory[self.po_loc[0]][self.po_loc[1]][6] = 1
        elif action == 'right':
            new_row, new_col = self.po_loc[0], self.po_loc[1] + 1
            if self.in_bound(new_row, new_col):
                self.po_self_memory[new_row][new_col][2] = 1
                self.po_self_memory[self.po_loc[0]][self.po_loc[1]][4] = 1
        else:
            print('Action Error!')
            exit(1)

        original_loc = self.po_loc
        if self.in_bound(new_row, new_col):
            self.po_loc = [new_row, new_col]

        if list(self.po_loc) != list(original_loc):  # in case the tuple and list issue
            if self.gui:
                if action == 'up':
                    self.canvas.move(self.po_ball, 0, -self.cell_length)
                elif action == 'down':
                    self.canvas.move(self.po_ball, 0, self.cell_length)
                elif action == 'left':
                    self.canvas.move(self.po_ball, -self.cell_length, 0)
                elif action == 'right':
                    self.canvas.move(self.po_ball, self.cell_length, 0)

            self._update_po_trace(original_loc, self.po_loc, action)

        self.po_visit_number[self.po_loc[0], self.po_loc[1]] += 1
        return original_loc, self.po_loc

    def update_pa_loc(self, action):
    
        # print("Action PA: ", action)
        # print("_____________________")

        if action == 'still':
            self.pa_visit_number[self.pa_loc[0], self.pa_loc[1]] += 1
            return self.pa_loc, self.pa_loc

        if action == 'up':
            new_row, new_col = self.pa_loc[0] - 1, self.pa_loc[1]
            if self.in_bound(new_row, new_col):
                self.pa_self_memory[new_row][new_col][1] = 1 # yf: add to self footprint memory
                self.pa_self_memory[self.pa_loc[0]][self.pa_loc[1]][7] = 1
        elif action == 'down':
            new_row, new_col = self.pa_loc[0] + 1, self.pa_loc[1]
            if self.in_bound(new_row, new_col):
                self.pa_self_memory[new_row][new_col][3] = 1
                self.pa_self_memory[self.pa_loc[0]][self.pa_loc[1]][5] = 1
        elif action == 'left':
            new_row, new_col = self.pa_loc[0], self.pa_loc[1] - 1
            if self.in_bound(new_row, new_col):
                self.pa_self_memory[new_row][new_col][0] = 1
                self.pa_self_memory[self.pa_loc[0]][self.pa_loc[1]][6] = 1
        elif action == 'right':
            new_row, new_col = self.pa_loc[0], self.pa_loc[1] + 1
            if self.in_bound(new_row, new_col):
                self.pa_self_memory[new_row][new_col][2] = 1
                self.pa_self_memory[self.pa_loc[0]][self.pa_loc[1]][4] = 1
        else:
            print('Action Error!')
            exit(1)

        original_loc = self.pa_loc
        if self.in_bound(new_row, new_col):
            self.pa_loc = [new_row, new_col]

        if list(self.pa_loc) != list(original_loc):
            if self.gui:
                if action == 'up':
                    self.canvas.move(self.pa_ball, 0, -self.cell_length)
                elif action == 'down':
                    self.canvas.move(self.pa_ball, 0, self.cell_length)
                elif action == 'left':
                    self.canvas.move(self.pa_ball, -self.cell_length, 0)
                elif action == 'right':
                    self.canvas.move(self.pa_ball, self.cell_length, 0)

            self._update_pa_trace(original_loc, self.pa_loc, action)

        self.pa_visit_number[self.pa_loc[0], self.pa_loc[1]] += 1
        return original_loc, self.pa_loc

    def _update_po_trace(self, ori_loc, new_loc, action):
        ori_loc = tuple(ori_loc)
        new_loc = tuple(new_loc)

        if action == 'up':
            self.po_trace[ori_loc][4] = 1
            self.po_trace[new_loc][1] = 1

            if self.gui:
                self.canvas.create_line(ori_loc[1] * self.cell_length + self.cell_3_8,
                                        ori_loc[0] * self.cell_length,
                                        ori_loc[1] * self.cell_length + self.cell_3_8,
                                        ori_loc[0] * self.cell_length + self.quarter_cell,
                                        arrow=FIRST, width=5, fill="red")
                self.canvas.create_line(new_loc[1] * self.cell_length + self.cell_3_8,
                                        new_loc[0] * self.cell_length + 3 * self.quarter_cell,
                                        new_loc[1] * self.cell_length + self.cell_3_8,
                                        new_loc[0] * self.cell_length + self.cell_length,
                                        arrow=FIRST, width=5, fill="red")
        elif action == 'down':
            self.po_trace[ori_loc][5] = 1
            self.po_trace[new_loc][0] = 1

            if self.gui:
                self.canvas.create_line(ori_loc[1] * self.cell_length + self.cell_3_8,
                                        ori_loc[0] * self.cell_length + 3 * self.quarter_cell,
                                        ori_loc[1] * self.cell_length + self.cell_3_8,
                                        ori_loc[0] * self.cell_length + self.cell_length,
                                        arrow=LAST, width=5, fill="red")
                self.canvas.create_line(new_loc[1] * self.cell_length + self.cell_3_8,
                                        new_loc[0] * self.cell_length,
                                        new_loc[1] * self.cell_length + self.cell_3_8,
                                        new_loc[0] * self.cell_length + self.quarter_cell,
                                        arrow=LAST, width=5, fill="red")
        elif action == 'left':
            self.po_trace[ori_loc][6] = 1
            self.po_trace[new_loc][3] = 1

            if self.gui:
                self.canvas.create_line(ori_loc[1] * self.cell_length,
                                        ori_loc[0] * self.cell_length + self.cell_3_8,
                                        ori_loc[1] * self.cell_length + self.quarter_cell,
                                        ori_loc[0] * self.cell_length + self.cell_3_8,
                                        arrow=FIRST, width=5, fill="red")
                self.canvas.create_line(new_loc[1] * self.cell_length + self.cell_length,
                                        new_loc[0] * self.cell_length + self.cell_3_8,
                                        new_loc[1] * self.cell_length + 3 * self.quarter_cell,
                                        new_loc[0] * self.cell_length + self.cell_3_8,
                                        arrow=LAST, width=5, fill="red")
        elif action == 'right':
            self.po_trace[ori_loc][7] = 1
            self.po_trace[new_loc][2] = 1

            if self.gui:
                self.canvas.create_line(ori_loc[1] * self.cell_length + self.cell_length,
                                        ori_loc[0] * self.cell_length + self.cell_3_8,
                                        ori_loc[1] * self.cell_length + 3 * self.quarter_cell,
                                        ori_loc[0] * self.cell_length + self.cell_3_8,
                                        arrow=FIRST, width=5, fill="red")
                self.canvas.create_line(new_loc[1] * self.cell_length,
                                        new_loc[0] * self.cell_length + self.cell_3_8,
                                        new_loc[1] * self.cell_length + self.quarter_cell,
                                        new_loc[0] * self.cell_length + self.cell_3_8,
                                        arrow=LAST, width=5, fill="red")

    def _update_pa_trace(self, ori_loc, new_loc, action):
        ori_loc = tuple(ori_loc)
        new_loc = tuple(new_loc)


        if action == 'up':
            self.pa_trace[ori_loc][4] = 1
            self.pa_trace[new_loc][1] = 1

            if self.gui:
                self.canvas.create_line(ori_loc[1] * self.cell_length + self.cell_5_8,
                                        ori_loc[0] * self.cell_length,
                                        ori_loc[1] * self.cell_length + self.cell_5_8,
                                        ori_loc[0] * self.cell_length + self.quarter_cell,
                                        arrow=FIRST, width=5, fill="blue")
                self.canvas.create_line(new_loc[1] * self.cell_length + self.cell_5_8,
                                        new_loc[0] * self.cell_length + 3 * self.quarter_cell,
                                        new_loc[1] * self.cell_length + self.cell_5_8,
                                        new_loc[0] * self.cell_length + self.cell_length,
                                        arrow=FIRST, width=5, fill="blue")
        elif action == 'down':
            self.pa_trace[ori_loc][5] = 1
            self.pa_trace[new_loc][0] = 1

            if self.gui:
                self.canvas.create_line(ori_loc[1] * self.cell_length + self.cell_5_8,
                                        ori_loc[0] * self.cell_length + 3 * self.quarter_cell,
                                        ori_loc[1] * self.cell_length + self.cell_5_8,
                                        ori_loc[0] * self.cell_length + self.cell_length,
                                        arrow=LAST, width=5, fill="blue")
                self.canvas.create_line(new_loc[1] * self.cell_length + self.cell_5_8,
                                        new_loc[0] * self.cell_length,
                                        new_loc[1] * self.cell_length + self.cell_5_8,
                                        new_loc[0] * self.cell_length + self.quarter_cell,
                                        arrow=LAST, width=5, fill="blue")
        elif action == 'left':
            self.pa_trace[ori_loc][6] = 1
            self.pa_trace[new_loc][3] = 1

            if self.gui:
                self.canvas.create_line(ori_loc[1] * self.cell_length,
                                        ori_loc[0] * self.cell_length + self.cell_5_8,
                                        ori_loc[1] * self.cell_length + self.quarter_cell,
                                        ori_loc[0] * self.cell_length + self.cell_5_8,
                                        arrow=FIRST, width=5, fill="blue")
                self.canvas.create_line(new_loc[1] * self.cell_length + self.cell_length,
                                        new_loc[0] * self.cell_length + self.cell_5_8,
                                        new_loc[1] * self.cell_length + 3 * self.quarter_cell,
                                        new_loc[0] * self.cell_length + self.cell_5_8,
                                        arrow=LAST, width=5, fill="blue")
        elif action == 'right':
            self.pa_trace[ori_loc][7] = 1
            self.pa_trace[new_loc][2] = 1

            if self.gui:
                self.canvas.create_line(ori_loc[1] * self.cell_length + self.cell_length,
                                        ori_loc[0] * self.cell_length + self.cell_5_8,
                                        ori_loc[1] * self.cell_length + 3 * self.quarter_cell,
                                        ori_loc[0] * self.cell_length + self.cell_5_8,
                                        arrow=FIRST, width=5, fill="blue")
                self.canvas.create_line(new_loc[1] * self.cell_length,
                                        new_loc[0] * self.cell_length + self.cell_5_8,
                                        new_loc[1] * self.cell_length + self.quarter_cell,
                                        new_loc[0] * self.cell_length + self.cell_5_8,
                                        arrow=LAST, width=5, fill="blue")

    def update_time(self):
        self.time += 1

    def kill_animal(self, number = None):
        # Maybe this negative reward is not helpful.
        if number is None:
            kill_list = []
            for row, col in self.snare_state:
                if random.random() < (self.animal_density[row, col]):
                    kill_list.append([row, col])
                    # print("-------killed an animal--------")
                    self.poacher_snare_num -= 1
            return kill_list
        else:
            kill_list = []
            # assert len(number) == len(self.snare_state)
            for i in range(len(self.snare_state)):
                if (1 << i) & number > 0:
                # if number[i] != 0:
                    kill_list.append([self.snare_state[i][0], self.snare_state[i][1]])
            return kill_list


    def get_reward_train(self):
        pa_reward, po_reward = 0.0, 0.0

        # from removing snares
        # remove_num = 0
        # if (self.pa_loc[0], self.pa_loc[1]) in self.snare_state:
        #     while (self.pa_loc[0], self.pa_loc[1]) in self.snare_state:
        #         pa_reward += 2
        #         remove_num += 1
        #         print("par:", pa_reward)
        #         self.snare_state.remove((self.pa_loc[0], self.pa_loc[1]))
        #
        #     if self.gui:
        #         for snare_obj in self.snare_object[(self.pa_loc[0], self.pa_loc[1])]:
        #             self.canvas.delete(snare_obj)
        #         del self.snare_object[(self.pa_loc[0], self.pa_loc[1])]
        
        # from killing animals
        kill_list = self.kill_animal()
        # for row, col in kill_list:
        #     # self.snare_state.remove((row, col))
        #     if self.gui:
        #         assert (row, col) in self.snare_object and len(self.snare_object[(row, col)]) > 0
        #         self.canvas.delete(self.snare_object[(row, col)][0])
        #         self.snare_object[(row, col)].pop(0)
        #         if len(self.snare_object[(row, col)]) == 0:
        #             del self.snare_object[(row, col)]

        # poacher gets killing reward if it has not returned home, or has not been caught
        if not self.home_flag and not self.catch_flag: 
            po_reward += 2 * len(kill_list)
            pa_reward -= po_reward


        # print("Home:", self.home_flag)

        if self.home_flag and not self.catch_flag and self.poacher_snare_num == 0:
            # print("Before:", po_reward)
            po_reward += 20
            # print("After:", po_reward)
            pa_reward -= 10

        # from catch poachers
        # Only get catching reward when catch the poacher for the first time
        # only able to catch the poacher if it has not returned home
        if not self.catch_flag and not self.home_flag:  
            if list(self.pa_loc) == list(self.po_loc):
                self.catch_flag = 1
                pa_reward += 20.
                po_reward -= 20.
                if self.gui:
                    self.canvas.delete(self.po_ball)

        # Reward shaping
        # po_ori_loc = np.array(po_ori_loc)
        # po_new_loc = np.array(po_new_loc)
        # pa_ori_loc = np.array(pa_ori_loc)
        # pa_new_loc = np.array(pa_new_loc)
        # po_initial_loc = np.array(self.po_initial_loc)

        # if self.args.reward_shaping:
        #      # patroller reward shaping: the distance change to the poacher
        #     if not self.catch_flag and not self.home_flag:
        #         pa_reward += np.sqrt(np.sum(np.square(pa_ori_loc - po_ori_loc))) - \
        #                     np.sqrt(np.sum(np.square(pa_new_loc - po_new_loc)))
        #         print("par:", pa_reward)

             # patroller reward shaping: weighted distance change to the snares
            # if len(self.snare_state) > 0:
            #     snare_pos = np.array(self.snare_state)
            #     snare_weight = np.array([self.animal_density[i, j] for i, j in self.snare_state]) / 0.6
            #
            #     pa_reward += np.mean(
            #         snare_weight * (
            #             np.sqrt(np.sum(np.square(pa_ori_loc - snare_pos), axis=1)) -
            #             np.sqrt(np.sum(np.square(pa_new_loc - snare_pos), axis=1))
            #         )
            #     )

        # Go away from patroller
        # if not self.catch_flag and not self.home_flag:
        #     far_pa_reward = np.sqrt(np.sum(np.square(pa_new_loc - po_new_loc))) - \
        #                     np.sqrt(np.sum(np.square(pa_ori_loc - po_ori_loc)))
        #     if far_pa_reward < 0:
        #         po_reward += far_pa_reward

        # poacher reward shaping: get weighted reward from putted snares 
        # if not self.catch_flag and not self.home_flag:
        #     if len(self.snare_state) > 0:
        #        snare_weight = np.array([self.animal_density[i, j] for i, j in self.snare_state]) * 0.6
        #        po_reward += np.sum(snare_weight)

        # poacher reward shaping: encourage to go back home when snares are run out 
        # if not self.home_flag and no_snare and not self.catch_flag:
        #     po_reward += np.sqrt(np.sum(np.square(po_ori_loc - po_initial_loc))) - \
        #                     np.sqrt(np.sum(np.square(po_new_loc - po_initial_loc)))            
        
        # poacher reward shaping: when first get back to home, get a positive reward
        # if self.home_flag and not self.catch_flag:
        #     if self.poacher_first_home:
        #         po_reward += 0.5
        #     self.poacher_first_home = False
        # if cfr:
        #     return pa_reward, po_reward, remove_num
        # print("REWARDS:", po_reward, pa_reward)
        return pa_reward, po_reward

    def get_reward_test(self):

        pa_reward, po_reward = self.get_reward_train()
        return pa_reward, po_reward

        # remove_cnt = 0

        # ### Patroller will clear the snare if find one
        # if (self.pa_loc[0], self.pa_loc[1]) in self.snare_state:
        #     while (self.pa_loc[0], self.pa_loc[1]) in self.snare_state:
        #         remove_cnt += 1
        #         pa_reward += 2
        #         self.snare_state.remove((self.pa_loc[0], self.pa_loc[1]))
        #
        #     if self.gui:
        #         for snare_obj in self.snare_object[(self.pa_loc[0], self.pa_loc[1])]:
        #             self.canvas.delete(snare_obj)
        #         del self.snare_object[(self.pa_loc[0], self.pa_loc[1])]

        ### kill animals
        # kill_list = self.kill_animal(number = number)
        # print("Kill list:", kill_list)
        # if not self.catch_flag and not self.home_flag:
        #     po_reward += 2 * len(kill_list)
        # pa_reward -= 2 * len(kill_list)
        # for row, col in kill_list:
        #     self.snare_state.remove((row, col))
        #     if self.gui:
        #         assert (row, col) in self.snare_object and len(self.snare_object[(row, col)]) > 0
        #         self.canvas.delete(self.snare_object[(row, col)][0])
        #         self.snare_object[(row, col)].pop(0)
        #         if len(self.snare_object[(row, col)]) == 0:
        #             del self.snare_object[(row, col)]

        # only get this negative reward of being caught for the first time 
        # if not self.catch_flag and not self.home_flag:
        #     # If get caught
        #     if list(self.pa_loc) == list(self.po_loc):
        #         self.catch_flag = 1
        #         po_reward -= 8
        #         pa_reward += 8
        #         if self.gui:
        #             self.canvas.delete(self.po_ball)
        #
        # if self.args.zero_sum == 0:
        #     return pa_reward, po_reward
        # else:
        #     if not cfr:
        #         return pa_reward, -pa_reward
        #     else:
        #         return pa_reward, -pa_reward, remove_cnt

        # return pa_reward, -pa_reward
    def place_snare(self, loc):
        # print("Placed snare at", loc)
        if (loc[0], loc[1]) not in self.snare_state:
            self.snare_state.append((loc[0], loc[1]))
        if self.gui:
            rec = self.canvas.create_rectangle(loc[1] * self.cell_length,
                                               loc[0] * self.cell_length,
                                               loc[1] * self.cell_length + self.quarter_cell,
                                               loc[0] * self.cell_length + self.quarter_cell, fill="red", tags="poach_rec")

            if (loc[0], loc[1]) not in self.snare_object:
                self.snare_object[(loc[0], loc[1])] = [rec]
            else:
                self.snare_object[(loc[0], loc[1])].append(rec)
        
        
    def delete_snare(self, loc):
        
#        print("REC:", self.rec)
#        print(self.canvas.find_all())
        
        if (loc[0], loc[1]) in self.snare_state:
            self.snare_state.remove((loc[0], loc[1]))
        if self.gui:
            self.canvas.delete("poach_rec")
            
    def get_local_ani_den(self, loc):
        if self.in_bound(loc[0], loc[1]):
            den = [self.animal_density[loc[0], loc[1]]]
        else:
            den = [0.]

        up_loc = (loc[0] - 1, loc[1])
        if self.in_bound(up_loc[0], up_loc[1]):
            den.append(self.animal_density[up_loc[0], up_loc[1]])
        else:
            den.append(0.)

        down_loc = (loc[0] + 1, loc[1])
        if self.in_bound(down_loc[0], down_loc[1]):
            den.append(self.animal_density[down_loc[0], down_loc[1]])
        else:
            den.append(0.)

        left_loc = (loc[0], loc[1] - 1)
        if self.in_bound(left_loc[0], left_loc[1]):
            den.append(self.animal_density[left_loc[0], left_loc[1]])
        else:
            den.append(0.)

        right_loc = (loc[0], loc[1] + 1)
        if self.in_bound(right_loc[0], right_loc[1]):
            den.append(self.animal_density[right_loc[0], right_loc[1]])
        else:
            den.append(0.)

        return np.array(den)

    def get_local_pa_trace(self, loc):
        if tuple(loc) in self.pa_trace:
            return self.pa_trace[tuple(loc)]
        else:
            return np.zeros(8)

    def get_local_po_trace(self, loc):
        return self.po_trace[tuple(loc)]

    def update_pa_memory(self):
        self.pa_memory[self.pa_loc[0], self.pa_loc[1]] = self.po_trace[tuple(self.pa_loc)]

    def update_po_memory(self):
        self.po_memory[self.po_loc[0], self.po_loc[1]] = self.pa_trace[tuple(self.po_loc)]

    def blur_locations(self, in_field):
        field = np.copy(in_field)
        coords = np.argwhere(field==1)

        for coord in coords:
            not_orientations = set()
            i_row_num, i_column_num = coord[0], coord[1]

            if i_row_num == 0:
                not_orientations.add(2)
                not_orientations.add(3)
            elif i_row_num == self.row_num - 1:
                not_orientations.add(0)
                not_orientations.add(1)

            if i_column_num == 0:
                not_orientations.add(1)
                not_orientations.add(3)
            elif i_column_num == self.column_num - 1:
                not_orientations.add(0)
                not_orientations.add(2)

            possible_orientations = {0, 1, 2, 3} - not_orientations
            orientation = np.random.choice(list(possible_orientations))

            if orientation == 0:
                field[i_row_num:i_row_num+2, i_column_num:i_column_num+2] = 1
            elif orientation == 1:
                field[i_row_num:i_row_num+2, i_column_num-1:i_column_num+1] = 1
            elif orientation == 2:
                field[i_row_num-1:i_row_num+1, i_column_num:i_column_num+2] = 1
            else:
                field[i_row_num-1:i_row_num+1, i_column_num-1:i_column_num+1] = 1


        return field
        
    def observation_grid(self, obs_coords, target_coords):
        dist = sum(np.absolute(np.subtract(obs_coords, target_coords)))
        coordinate = np.zeros([self.row_num, self.column_num])
        
        if dist==1:
            coordinate[target_coords] = 1
        return coordinate
        
    
    def get_pa_state(self):
        state = self.pa_self_memory

        # yf: add self footprint memory as state
        if self.footsteps:
            state = np.concatenate((state, self.pa_memory), axis = 2)

        ani_den = np.expand_dims(self.animal_density, axis=2)
        state = np.concatenate((state, ani_den), axis=2)
            

        if self.po_bleeb:
            coordinate = np.zeros([self.row_num, self.column_num])
            if np.random.random() < self.po_scan_rate:
                coordinate[self.po_loc[0], self.po_loc[1]] = 1
            rand_field = np.random.random((self.row_num, self.column_num)) < self.tourist_noise
            coordinate = np.logical_or(rand_field, coordinate).astype(int)
            if self.filter_bleeb:
                coordinate = self.blur_locations(coordinate)
            coordinate = np.expand_dims(coordinate, axis=2)
            if self.canvas:
                self.show_Filter_In_Grid(coordinate)
            state = np.concatenate((state, coordinate), axis=2)
            
        coordinate = np.zeros([self.row_num, self.column_num])
        coordinate[self.pa_loc[0], self.pa_loc[1]] = 1
        coordinate = np.expand_dims(coordinate, axis=2)
        state = np.concatenate((state, coordinate), axis=2)
        
        if self.see_surrounding:
            coordinate = self.observation_grid(tuple(i for i in self.pa_loc), tuple(i for i in self.po_loc))
            coordinate = np.expand_dims(coordinate, axis=2)
            state = np.concatenate((state, coordinate), axis=2)
            
        if self.args.extra_sensor_pa:
            coordinate = extra_sensor_pa(self.pa_loc, self.po_loc, self.animal_density, self.row_num, self.column_num)
            coordinate = np.expand_dims(coordinate, axis=2)
            state = np.concatenate((state, coordinate), axis=2)
                                    
        visit_num_norm = np.expand_dims(self.pa_visit_number / 10., axis=2)
        state = np.concatenate((state, visit_num_norm), axis=2)

        time_left = np.ones([self.row_num, self.column_num]) * float(self.time) / (self.args.max_time / 2.)
        time_left = np.expand_dims(time_left, axis=2)
        state = np.concatenate((state, time_left), axis=2)
        # print("State shape")
        # print(state.shape)
        # print("Tupel")
        # print((self.row_num, self.column_num, self.args.pa_state_size))
        assert state.shape == (self.row_num, self.column_num, self.args.pa_state_size)
        return state

    def show_Filter_In_Grid(self, ohe_coord):
        for y, row in enumerate(ohe_coord):
            for x, i in enumerate(row):
                if i[0] == 0:
                    self.place_radar_rec((y, x), "black")
                    #self.canvas.delete()
                else:
                    self.place_radar_rec((y, x), "gold")


    def place_radar_rec(self, loc, color):
        rec = self.canvas.create_rectangle(loc[1]* self.cell_length,
                                     loc[0] * self.cell_length,
                                     loc[1] * self.cell_length + self.cell_length,
                                     loc[0] * self.cell_length + self.cell_length, outline=color, width=3)
        self.radar_objs[loc] = rec

    def get_po_state(self):
        snare_num = self.poacher_snare_num
        state = self.po_self_memory
        
        # yf: add self footprint memory as state
        if self.footsteps:
            state = np.concatenate((state, self.po_memory), axis = 2)
        
        ani_den = np.expand_dims(self.animal_density, axis=2)
        state = np.concatenate((state, ani_den), axis=2)

        coordinate = np.zeros([self.row_num, self.column_num])
        coordinate[self.po_loc[0], self.po_loc[1]] = 1.
        coordinate = np.expand_dims(coordinate, axis=2)
        state = np.concatenate((state, coordinate), axis=2)

        visit_num_norm = np.expand_dims(self.po_visit_number / 10., axis=2)
        state = np.concatenate((state, visit_num_norm), axis=2)

        snare_num_left = np.ones([self.row_num, self.column_num]) * float(snare_num) / self.args.snare_num
        snare_num_left = np.expand_dims(snare_num_left, axis=2)
        state = np.concatenate((state, snare_num_left), axis=2)

        time_left = np.ones([self.row_num, self.column_num]) * float(self.time) / (self.args.max_time / 2.)
        time_left = np.expand_dims(time_left, axis=2)
        state = np.concatenate((state, time_left), axis=2)
        
        if self.see_surrounding:
            coordinate = self.observation_grid(tuple(i for i in self.po_loc), tuple(i for i in self.pa_loc))
            coordinate = np.expand_dims(coordinate, axis=2)
            state = np.concatenate((state, coordinate), axis=2)
            
        if self.args.extra_sensor_po:
            coordinate = extra_sensor_po(self.po_loc, self.pa_loc, self.animal_density, self.row_num, self.column_num)
            coordinate = np.expand_dims(coordinate, axis=2)
            state = np.concatenate((state, coordinate), axis=2)

        initial_loc = np.zeros([self.row_num, self.column_num])
        initial_loc[self.po_initial_loc[0], self.po_initial_loc[1]] = 1.
        initial_loc = np.expand_dims(initial_loc, axis=2)
        state = np.concatenate((state, initial_loc), axis=2)
        assert state.shape == (self.row_num, self.column_num, self.args.po_state_size)
        return state

    def get_local_snare(self, loc):
        if (loc[0], loc[1]) in self.snare_state:
            num = 0
            for snare_loc in self.snare_state:
                if snare_loc == (loc[0], loc[1]):
                    num += 1
            return num
        else:
            return 0.

    def in_bound(self, row, col):
        return row >= 0 and row <= (self.row_num - 1) and col >= 0 and col <= (self.column_num - 1)


    def get_po_initial_loc(self, idx = None, poacher_map = True):
        if poacher_map:
            candidate = [[0, 0], [3, 0], [6, 0]]
        else:
            candidate = [[0, 0], [0, self.column_num - 1], [self.row_num - 1, self.column_num - 1], [self.row_num - 1, 0]]

        if idx is not None:
            return candidate[idx]

        index = random.randint(0, 2)
        # print("Candidate:", candidate[index], poacher_map)
        return candidate[index]

    ##################################################################################
    ######The functions below are for transfering the game into a game tree ##########
    ##################################################################################
    
    def patrollerstep(self, pa_action):
        '''
        For building the Tree of the Game.
        '''
        pre_pa_loc = self.pa_loc.copy()
        new_loc = self.pa_loc.copy()
        if pa_action == 'up':
            new_loc[0] -= 1
        elif pa_action == 'down':
            new_loc[0] += 1
        elif pa_action == 'left':
            new_loc[1] -= 1
        elif pa_action == 'right':
            new_loc[1] += 1
        pre_pre_loc_trace = self.pa_trace[tuple(pre_pa_loc)].copy()
        pre_new_loc_trace = self.pa_trace[tuple(new_loc)].copy()

        # pre_pa_trace = copy.deepcopy(self.pa_trace)
        _, _ = self.update_pa_loc(pa_action)
        return pre_pa_loc, new_loc, pre_pre_loc_trace, pre_new_loc_trace 
    
    def patrollerundo(self, pregame):
        '''
        For building the game tree
        '''
        pre_pa_loc, new_loc, pre_pre_loc_trace, pre_new_loc_trace = pregame
        self.pa_loc = pre_pa_loc
        self.pa_trace[tuple(pre_pa_loc)] = pre_pre_loc_trace
        self.pa_trace[tuple(new_loc)] = pre_new_loc_trace 

    def poacherstep(self, po_action, snare_flag):
        '''
        For building the game tree
        '''
        pre_po_loc = self.po_loc.copy()
        new_loc = self.po_loc.copy()
        pre_snare_state = self.snare_state.copy()
        # pre_po_trace = copy.deepcopy(self.po_trace)
        pre_snare_num = self.poacher_snare_num

        if po_action == 'up':
            new_loc[0] -= 1
        elif po_action == 'down':
            new_loc[0] += 1
        elif po_action == 'left':
            new_loc[1] -= 1
        elif po_action == 'right':
            new_loc[1] += 1

        pre_pre_loc_trace = self.po_trace[tuple(pre_po_loc)].copy()
        pre_new_loc_trace = self.po_trace[tuple(new_loc)].copy()

        if snare_flag and self.poacher_snare_num > 0:
            self.place_snare(self.po_loc)

        _, _ = self.update_po_loc(po_action)

        pa_ob_footprint = ''
        po_ob_footprint = ''
        for i in range(8):
            if self.po_trace[tuple(self.pa_loc)][i] == 1:
                pa_ob_footprint += str(i)

        for i in range(8):
            if self.pa_trace[tuple(self.po_loc)][i] == 1:
                po_ob_footprint += str(i)
            
        pre = [pre_po_loc, new_loc, pre_pre_loc_trace, pre_new_loc_trace,  pre_snare_num, pre_snare_state]
        # pre = [pre_po_loc, pre_po_trace,  pre_snare_num, pre_snare_state]
        return pre, pa_ob_footprint, po_ob_footprint

    def poacherundo(self, pregame):
        '''
        for building the game tree
        '''
        pre_po_loc, new_loc, pre_pre_loc_trace, pre_new_loc_trace,  pre_snare_num, pre_snare_state = pregame
        # pre_po_loc, pre_po_trace,  pre_snare_num, pre_snare_state = pregame
        self.po_loc = pre_po_loc
        self.snare_state = pre_snare_state
        self.poacher_snare_num = pre_snare_num
        self.po_trace[tuple(pre_po_loc)] = pre_pre_loc_trace
        self.po_trace[tuple(new_loc)] = pre_new_loc_trace
        # self.po_trace = pre_po_trace
        
    def chancestep(self, number = None):
        '''
        For building the game tree
        '''
        pre_snare_state = self.snare_state.copy()
        pre_catch_flag = self.catch_flag
        pre_home_flag = self.home_flag 
        pre_time = self.time
        pre_end_game = self.end_game

        # if poacher has run out of snares and has returned home
        if self.poacher_snare_num == 0 and tuple(self.po_initial_loc) == tuple(self.po_loc) and not tuple(self.pa_loc) == tuple(self.po_loc):
            self.home_flag = True
            if self.gui:
                self.canvas.delete(self.po_ball)

        # Calculate reward for both sides
        # this process includes remove snares and kill animals
        pa_reward, po_reward, pa_remove_cnt = self.get_reward_test(cfr = True, number = number) 

        self.update_time()
        if (self.catch_flag and len(self.snare_state) == 0) \
            or (self.home_flag and len(self.snare_state) == 0) or self.time == self.args.max_time:
            self.end_game = True
        else:
            self.end_game = False

        pre = [pre_snare_state, pre_catch_flag, pre_home_flag, pre_time, pre_end_game]
        return pre, pa_reward, po_reward, pa_remove_cnt

    def chanceundo(self, pregame):
        '''
        For building the game tree
        '''
        pre_snare_state, pre_catch_flag, pre_home_flag, pre_time, pre_end_game = pregame
        self.snare_state = pre_snare_state
        self.catch_flag = pre_catch_flag
        self.home_flag = pre_home_flag
        self.time = pre_time
        self.end_game = pre_end_game

    def show_traces(self, trace, descrip = None):
        # print(descrip)
        '''
        For game tree building debug usage
        '''
        for i in range(self.args.row_num):
            for j in range(self.args.column_num):
                for k in range(8):
                    if trace[i,j][k] == 1:
                        print(str(descrip) + ' trace location ({0}, {1}) footprint type {2}'.format(i,j,k))


    def get_chance_actions(self):
        '''
        For building the game tree.
        the chance action is represented by a number in its binary form.
        If the bit is one, then the snare at the corresponding cell is removed 
        '''
        snare_state_copy = copy.copy(self.snare_state)

        # if (self.pa_loc[0], self.pa_loc[1]) in snare_state_copy:
        #     while (self.pa_loc[0], self.pa_loc[1]) in snare_state_copy:
        #         snare_state_copy.remove((self.pa_loc[0], self.pa_loc[1]))

        num = len(snare_state_copy)
        # print('number of snares are:', num)
        probs = []
        # actions = [np.zeros(num) for i in range(2 ** num)]
        for i in range(2 ** num):
            p = 1.
            for j in range(num):
                if (1 << j) & i  == 1 << j: ###############
                    # actions[i][j] = 1
                    p *= self.animal_density[snare_state_copy[j][0], snare_state_copy[j][1]] / 5.
                else:
                    p *= (1 - self.animal_density[snare_state_copy[j][0], snare_state_copy[j][1]] / 5.) 
            probs.append(p)

        # print(np.sum(probs))
        assert np.abs(np.sum(probs) - 1) < 1e-10
        # return actions, probs
        return range(2 ** num), probs


    def get_pa_actions(self):
        '''
        For building game tree usage
        '''
        action = ['still', 'up', 'down', 'left', 'right']
        if self.pa_loc[0] == 0:
            action.remove('up')
        if self.pa_loc[0] == self.row_num - 1:
            action.remove('down')
        if self.pa_loc[1] == 0:
            action.remove('left')
        if self.pa_loc[1] == self.column_num - 1:
            action.remove('right')
        return action
    
    def get_po_actions(self):
        '''
        For building game tree usage
        '''
        action = [('still', 1), ('up',0), ('down',0), ('left',0), ('right',0)]
        if self.po_loc[0] == 0:
            action.remove(('up',0))
        if self.po_loc[0] == self.row_num - 1:
            action.remove(('down',0))
        if self.po_loc[1] == 0:
            action.remove(('left',0))
        if self.po_loc[1] == self.column_num - 1:
            action.remove(('right',0))
        if self.poacher_snare_num == 0:
            ret = []
            for x in action:
                if x[1] != 1:
                    ret.append(x)
        else:
            ret = action
        return ret

