from __future__ import print_function, unicode_literals
from PyInquirer import style_from_dict, Token, prompt
from PyInquirer import Validator, ValidationError
from examples import custom_style_3
from GUI import main as GUImain
import re
from DeDOL import main as DeDOLmain

from os import listdir, getcwd

options = ["Custom"]
path = getcwd()
# get only folders
files = list(filter(lambda x: not("." in x or "LICENSE" in x) , listdir(path)))
options += files

basic_color = "#96ff55"
pri_color = "#ff6955"
sec_color = "#55e3ff"


style = style_from_dict({
    Token.QuestionMark: pri_color + ' bold',
    Token.Selected: sec_color,
    Token.Pointer: pri_color + ' bold',
    Token.Instruction: basic_color,  # default
    Token.Answer: sec_color + ' bold',
    Token.Question: basic_color
})

class NumberValidation(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number.',
                cursor_position=len(document.text))


class ZeroOneValidation(Validator):
    def validate(self, document):
        try:
            p = float(document.text)
            if p < 0 or p > 1:
                raise ValidationError(
                    message='Please enter a number between 0 and 1.',
                    cursor_position=len(document.text))
        except ValueError:
            raise ValidationError(
                message='Please enter a valid number.',
                cursor_position=len(document.text)
                )


class NotEmptyValidation(Validator):
    def validate(self, document):
        if len(document.text) <= 0:
            raise ValidationError(
                message='Please enter string.',
                cursor_position=len(document.text))
        if len(document.text.split()) > 1:
            raise ValidationError(
                message='Please don\'t use spaces in the model name.',
                cursor_position=len(document.text))
        if len(document.text.split('.')) > 1:
            raise ValidationError(
                message='Please don\'t use \'.\' in the model name.',
                cursor_position=len(document.text))
            

print("+---------------------------------+")
print("| HACK THE POACHER - DeDOL-master |")
print("+---------------------------------+")

questions = [
    {
        'type': 'list',
        'name': 'gui',
        'message': 'What operation would you like to run?',
        'choices': ['Train a model', 'Visualise a trained model']
    },
    {
        # TRAINING
        'type': 'input',
        'name': 'model_name',
        'message': 'What\'s the name of this model version?',
        'when': lambda answers: answers['gui'] == 'Train a model',
        'validate': NotEmptyValidation
    },
    {
        # TRAINING
        'type': 'input',
        'name': 'episodes',
        'message': 'How many episodes should the model train? It is adviced to have more van 10.000 episodes.',
        'when': lambda answers: answers['gui'] == 'Train a model',
        'validate': NumberValidation
    },
    {
        # TRAINING
        'type': 'list',
        'name': 'model_settings',
        'message': 'You can either choose a previous model settings or make a custom one from scratch.',
        'choices': options,
        'when': lambda answers: answers['gui'] == 'Train a model'
    },
    {
        # GUI
        'type': 'list',
        'name': 'model_name',
        'message': 'Which model would you like to run?',
        'choices': options[1:],
        'when': lambda answers: answers['gui'] == 'Visualise a trained model'
    },
    {
        # GUI
        'type': 'confirm',
        'name': 'change_arguments',
        'message': 'Would you like to change the arguments? (not advised)',
        'when': lambda answers: answers['gui'] == 'Visualise a trained model',
        'default': False
    },
    {
        # TRAINING & GUI
        'type': 'confirm',
        'name': 'footsteps',
        'message': 'Are both agents able to see footsteps?',
        'when': lambda answers: handle_custom(answers)
    },
    {
        # TRAINING & GUI
        'type': 'confirm',
        'name': 'radar',
        'message': 'Does the ranger make use of the datasystem?',
        'when': lambda answers: handle_custom(answers),
    },
    {
        # TRAINING & GUI
        'type': 'input',
        'name': 'detection_rate',
        'message': 'What is the rate of succesful detections of the datasystem? (A number between 0 and 1)',
        'when': lambda answers: check_radar(answers),
        'validate': ZeroOneValidation
    },
    {
        # TRAINING & GUI
        'type': 'confirm',
        'name': 'blur',
        'message': 'Are the recieved signals blured/spread out?',
        'when': lambda answers: check_radar(answers)
    },
    {
        # TRAINING & GUI
        'type': 'input',
        'name': 'tourist_noise',
        'message': 'How much tourist noise is visible in the datasystem? (A number between 0 and 1)',
        'when': lambda answers: check_radar(answers),
        'validate': ZeroOneValidation
    }
]

def check_radar(answers):
    if 'radar' in answers.keys():
        return answers['radar']
    else:
        return False

def handle_custom(answers):
    if 'model_settings' in answers.keys():
        return answers['model_settings'] == 'Custom'
    elif 'change_arguments' in answers.keys():
        return answers['change_arguments']
    else:
        return False


def find_pa_checkpoint(path):
    files = listdir(path)
    biggest_number = 0
    latest_checkpoint = None
    for f in files:
        if "pa_model" in f:
            getal = max([int(d) for d in f.split("_") if d.isdigit()])
            if getal > biggest_number:
                biggest_number = getal
                latest_checkpoint = f
    return ".".join(latest_checkpoint.split(".")[:-1])


def find_po_checkpoint(path):
    files = listdir(path)
    biggest_number = 0
    latest_checkpoint = None
    for f in files:
        if "po_model" in f:
            getal = max([int(d) for d in f.split("_") if d.isdigit()])
            if getal > biggest_number:
                biggest_number = getal
                latest_checkpoint = f
    return ".".join(latest_checkpoint.split(".")[:-1])


def build_params(params):
    # Which file do we run?
    if answers['gui'] == 'Train a model':

#         params.append("python3 DeDOL.py --save_path ./" + str(answers['model_name']))

        # params.append("python3 DeDOL.py--save_path ./" + str(answers['model_name']))
        params['save_path'] = answers['model_name']
        params["naive"] = True

    else:
        #params.append("python3 GUI.py --load True --pa_load_path./" + str(answers['model_name']))
        params['load'] = True
        ### TO DO ###
        # load patroller path and load poacher path for model (don't forget to remove everything after .ckpt)

        params['pa_load_path'] = "./" + answers['model_name'] + "/" + find_pa_checkpoint("./" + answers['model_name'])
        params['po_load_path'] = "./" + answers['model_name'] + "/" + find_po_checkpoint("./" + answers['model_name'])

    # params.append("--map_type poacher --row_num 7 --column_num 7 --naive True")
    params["map_type"] = "poacher"
    params["row_num"] = 7
    params["column_num"] = 7

    # Episode numbers
    if "episodes" in answers.keys():

        params["pa_episode_num"] = answers["episodes"]
        params["po_episode_num"] = answers["episodes"]

        # params.append("--pa_episode_num " + str(answers["episodes"]))
        # params.append("--po_episode_num " + str(answers["episodes"]))

    return params

    # if "model_settings" in answers.keys():
    #     if answers["model_settings"] != "Custom":
    #         load_model_settings(answers['model_settings'])
    #     else:
    #         add_radar_arguments(params);
    #
    # if "change_arguments" in answers.keys():
    #     if answers["change_arguments"]:
    #         add_radar_arguments(params)
    #     else:
    #         load_model_settings(answers['model_name'])


def add_radar_arguments(params):

    if "footsteps" in answers:
        params["footsteps"] = answers["footsteps"]
    else:
        params["footsteps"] = True

    if "po_bleeb" in answers:
        params["po_bleeb"] = answers["radar"]
    else:
        params["po_bleeb"] = True


    # params.append("--footsteps " + str(answers["footsteps"]))
    # params.append("--po_bleeb " + str(answers["radar"]))
    if "radar" in answers:
        params["po_scan_rate"] = float(answers["detection_rate"])
        params["filter_bleeb"] = answers["blur"]
        params["tourist_noise"] = float(answers["tourist_noise"])
    else:
        params["po_scan_rate"] = 1
        params["filter_bleeb"] = False
        params["tourist_noise"] = 0


        # params.append("--po_scan_rate " + str(answers["detection_rate"]))
        # params.append("--filter_bleeb " + str(answers["blur"]))
        # params.append("--tourist_noise " + str(answers["tourist_noise"]))

    return params


###############
#### TO DO ####
###############
# Loads the missing arguments of the models preset
# def load_model_settings(path):
#     # load_args
#     import json
#     print(path + "\\train_args.jaon")
#     with open(path + "\\train_args.json", "r") as f:
#         args = json.loads(f).items()
#         params.append("--footsteps " + str(args["footsteps"]))
#         params.append("--po_bleeb " + str(args["po_bleeb"]))
#         params.append("--po_scan_rate " + str(args["po_scan_rate"]))
#         params.append("--filter_bleeb " + str(args["filter_bleeb"]))
#         params.append("--tourist_noise " + str(args["tourist_noise"]))
#


answers = prompt(questions, style=style)
# print('Order receipt:')
# print(answers)

# <<<<<<< HEAD
params = build_params({})
params = add_radar_arguments(params)
print(params)
# final = ' '.join(params)
# print(final)


if answers['gui'] == "Visualise a trained model":
    GUImain(params)
else:
    DeDOLmain(params)


# =======
# params = {}
# >>>>>>> e153c0f8db0108f7fc0f64b52c03ef41db7e94db

