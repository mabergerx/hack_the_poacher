from __future__ import print_function, unicode_literals
from PyInquirer import style_from_dict, Token, prompt
from PyInquirer import Validator, ValidationError
from examples import custom_style_3

from os import listdir, getcwd

options = ["Custom"]
path = getcwd()
files = listdir(path)
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
        False

def handle_custom(answers):
    if 'model_settings' in answers.keys():
        return answers['model_settings'] == 'Custom'
    elif 'change_arguments' in answers.keys():
        return answers['change_arguments']
    else:
        False

def build_params(params):
    # Which file do we run?
    if answers['gui'] == 'Train a model':
        params.append("DeDOL.py")
    else:
        params.append("GUI.py")

    # Save path/load path
    params.append(path + "\\" + answers['model_name'])

    # Episode numbers
    if "episodes" in answers.keys(): 
        params.append(answers["episodes"])

    if "model_settings" in answers.keys():
        if answers["model_settings"] != "Custom":
            load_model_settings(answers['model_name'])
        else:
            add_radar_arguments(params);
        
    if "change_arguments" in answers.keys():
        if answers["change_arguments"]:
            add_radar_arguments(params)
        else:
            load_model_settings(answers['model_name'])

def add_radar_arguments(params):
    params.append(answers["footsteps"])
    params.append(answers["radar"])
    if answers["radar"]:
        params.append(answers["detection_rate"])
        params.append(answers["blur"])
        params.append(answers["tourist_noise"])

answers = prompt(questions, style=style)
print('Order receipt:')
print(answers)

params = []

build_params(params)
print(params)