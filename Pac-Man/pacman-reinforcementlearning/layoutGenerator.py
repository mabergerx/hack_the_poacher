import random
from numpy.random import choice as npchoice

def get_legal_places_on_line(line):
    return [index for index, place in enumerate(line) if place == " "]

# Obstacles

river = [(9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (9, 7), (9, 8), (9, 9),
         (10, 9),
         (12, 9),
         (13, 9),
         (1, 10),
         (2, 10), (2, 9), (2, 7), (2, 6), (2, 5), (2, 4),
         (3, 4),
         (4, 4), (4, 3), (4, 2), (4, 1),
         (1, 20),
         (3, 20),
         (4, 20), (4, 21), (4, 22),
         (5, 22),
         (6, 22), (6, 25), (6, 26), (6, 27), (6, 28)
        ]

trees = [(6, 12), (6, 13),
         (8, 18), (8, 28),
         (9, 27), (9, 28),
         (10, 28),
         (11, 17), (11, 18),
         (12, 18)
         ]

def get_grid_position(x, y, grid):
    return grid[x][y]

# Poachers

starting_locations_poacher = [
                      (11, 1),
                      (13, 20),
                      (1, 14),
                      (3, 28)
                     ]


def generate_random_entry_at_walls(lines):

    bottom_line = (lines[-2], "b")
    upper_line = (lines[1], "u")
    left_line = ([l[1] for l in lines], "l")
    right_line = ([l[28] for l in lines], "r")

    # First, select a line.
    chosen_line = random.choice([bottom_line, upper_line, left_line, right_line])

    # Second, select a valid point from the chosen line.
    chosen_point = random.choice(get_legal_places_on_line(chosen_line[0]))

    if chosen_line[1] == "b":
        entry_point = (13, chosen_point)
    elif chosen_line[1] == "u":
        entry_point = (1, chosen_point)
    elif chosen_line[1] == "l":
        entry_point = (chosen_point, 1)
    elif chosen_line[1] == "r":
        entry_point = (chosen_point, 27)
    else:
        entry_point = (1, chosen_point)

    return entry_point


# Animals

def generate_random_animal_positions(lines, num_animals=5):
    currently_placed_animals = []
    currently_occupied_cells = []

    enumerated_lines = list(enumerate(lines))

    for i in range(num_animals):
        # Pick an empty cell
        random_line = random.choice(enumerated_lines[1:-1])
        choice = random.choice(get_legal_places_on_line(random_line[1]))
        while choice in currently_occupied_cells:
            random_line = random.choice(enumerated_lines[1:-1])
            choice = random.choice(get_legal_places_on_line(random_line[1]))
        currently_occupied_cells.append(choice)
        currently_placed_animals.append((random_line[0], choice))

    return currently_placed_animals

# Given the coordinates of the obstacles, we want to spawn the animals according to some rules:

# Animals can spawn 1 cells range around the river with 0.5 chance.
# Animals can spawn 1 cells range around the trees with 0.4 chance.
# Animals can spawn on empty spaces with 0.1 chance.

def spawn_near_point(x, y):

    possible_x = [x+1, x-1]
    possible_y = [y+1, y-1]

    return (random.choice(possible_x), random.choice(possible_y))

def spawn_animal(grid, rivers=river, trees=trees):

    # Based in prob distribution, either spawn near a random river point, random tree point or random free point, while checking if point is legal.
    spawn_point = npchoice(["river", "trees", "free"], 1,
              p=[0.5, 0.4, 0.1])

    if spawn_point == "river":
        # First, select a random river point
        proximity_point = spawn_near_point(random.choice(rivers)[0], random.choice(rivers)[1])
        while get_grid_position(proximity_point[0], proximity_point[1], grid) != " ":
            proximity_point = spawn_near_point(random.choice(rivers)[0], random.choice(rivers)[1])
    elif spawn_point == "trees":
        proximity_point = spawn_near_point(random.choice(trees)[0], random.choice(trees)[1])
        while get_grid_position(proximity_point[0], proximity_point[1], grid) != " ":
            proximity_point = spawn_near_point(random.choice(rivers)[0], random.choice(rivers)[1])
    elif spawn_point == "free":
        proximity_point = generate_random_animal_positions(grid, 1)[0]
        while get_grid_position(proximity_point[0], proximity_point[1], grid) != " ":
            proximity_point = generate_random_animal_positions(grid, 1)
    else:
        proximity_point = generate_random_animal_positions(grid, 1)[0]
        while get_grid_position(proximity_point[0], proximity_point[1], grid) != " ":
            proximity_point = generate_random_animal_positions(grid, 1)

    return proximity_point


def generate_biased_animal_positions(grid, num_animals=5):
    # currently_placed_animals = []
    currently_occupied_cells = []

    for i in range(num_animals):
        # Pick an empty cell
        choice = spawn_animal(grid)
        while choice in currently_occupied_cells:
            choice = spawn_animal(grid)
        currently_occupied_cells.append(choice)
        # currently_placed_animals.append((random_line[0], choice))
        # print(choice)
    return currently_occupied_cells


def place_animals_on_grid(grid, num_animals=5, biased=False):

    if biased:
        animal_positions = generate_biased_animal_positions(grid, num_animals=num_animals)
    else:
        animal_positions = generate_random_animal_positions(grid, num_animals=num_animals)

    new_grid = grid[:]

    for animal_x, animal_y in animal_positions:
        line_to_modify = new_grid[animal_x]
        modified_line = line_to_modify[:animal_y] + "." + line_to_modify[animal_y + 1:]
        new_grid[animal_x] = modified_line

    return new_grid


def spawn_rangers(num_rangers=3, max_number_rangers=4):
    if num_rangers > max_number_rangers:
        num_rangers = max_number_rangers
        print("Maximum of 4 rangers exceeded! Generating 4 rangers instead...")

    rangers_to_place = []

    # between 24 and 27

    for i in range(num_rangers):
        rangers_to_place.append((1, 28 - i))

    return rangers_to_place


def place_rangers_on_grid(grid, num_rangers=3):

    ranger_positions = spawn_rangers(num_rangers=num_rangers)

    new_grid = grid[:]

    for ranger_x, rangers_y in ranger_positions:
        line_to_modify = new_grid[ranger_x]
        modified_line = line_to_modify[:rangers_y] + "G" + line_to_modify[rangers_y + 1:]
        new_grid[ranger_x] = modified_line

    return new_grid


def place_poacher_on_grid(initial_grid, controlled=False):

    if controlled:
        poacher_position = random.choice(starting_locations_poacher)
    else:
        poacher_position = generate_random_entry_at_walls(initial_grid)

    poacher_x = poacher_position[0]
    poacher_y = poacher_position[1]

    new_grid = initial_grid[:]

    line_to_modify = new_grid[poacher_x]
    modified_line = line_to_modify[:poacher_y] + "P" + line_to_modify[poacher_y + 1:]
    new_grid[poacher_x] = modified_line

    return new_grid


def populate_the_grid(num_rangers=3, num_animals=20,
                      biased_animals=True, controlled_poacher=True):

    # with open("Pac-Man/pacman-reinforcementlearning/layouts/baseGrid.lay") as f:
    #     lines = [line.strip() for line in f]

    f = open("layouts/baseGrid.lay")
    try:
        lines = [line.strip() for line in f]
    finally:
        f.close()

    new_grid = lines[:]

    poacher_grid = place_poacher_on_grid(new_grid, controlled=controlled_poacher)

    ranger_grid = place_rangers_on_grid(poacher_grid, num_rangers)

    animals_grid = place_animals_on_grid(ranger_grid, num_animals, biased=biased_animals)

    return animals_grid