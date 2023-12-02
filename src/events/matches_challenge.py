import asyncio
from copy import copy
from itertools import chain
from math import inf
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
from random import randint, choice
import re
import time


class Matches_Interface:

    MATCH_INIT_SCALE = 75

    # segments used to draw each number
    # Xs is a small version of X, Xb is a big version of X
    MATCHES = {
        '0' : [0, 1, 2, 3, 4, 5],
        '0s' : [6, 2, 3, 4],
        '1'  : [1, 2],
        '1s' : [11],
        '2'  : [0, 1, 6, 4, 3],
        '3'  : [0, 1, 6, 2, 3],
        '4'  : [1, 2, 5, 6],
        '4s' : [6, 7, 8],
        '5'  : [0, 5, 6, 2, 3],
        '6'  : [0, 5, 4, 3, 2, 6],
        '6s' : [5, 4, 3, 2, 6],
        '7'  : [0, 1, 2],
        '7b' : [5, 0, 1, 2],
        '8'  : [0, 1, 2, 3, 4, 5, 6],
        '8s' : [0, 1, 5, 6, 10],
        '9'  : [0, 1, 2, 3, 5, 6],
        '9s' : [0, 1, 2, 5, 6],
        '+'  : [6, 7],
        '-'  : [6],
        '='  : [6, 9]
    }

    # Position and orientation of the match image corresponding to each segment
    # WARNING: segment 11 = segment 7
    POS = [
        (0.5, 2, 90),
        (1, 1.5, 0),
        (1, 0.5, 0),
        (0.5, 0, 90),
        (0, 0.5, 0),
        (0, 1.5, 0),
        (0.5, 1, 90),
        (0.5, 1, 0),
        (0.25, 1.25, 135),
        (0.5, 1.25, 90),
        (0.5, 1.5, 90),
        (0.5, 1, 0)
    ]

    IMG_BACKGROUND = Image.open('src/events/assets/framecool2.png').resize((1920, 1080), Image.LANCZOS)
    IMG_MATCH = Image.open('src/events/assets/allu.png').resize((MATCH_INIT_SCALE, MATCH_INIT_SCALE), Image.LANCZOS)


    def __init__(self, riddle, main_sol, all_sols):
        self.riddle = riddle
        self.main_sol = main_sol
        self.all_sols = all_sols


    @staticmethod
    async def new():
        """
        Generates a new riddle
        --
        output:
            res: Matches_Interface
        """
        riddle, main_sol, all_sols = await get_riddle()
        return Matches_Interface(riddle, main_sol, all_sols)


    @staticmethod
    def draw_char(char, offset, scale, base, ax) :
        """
        Draws one character on the canvas
        --
        input:
            char: str -> character to draw
            offset: int -> offset from the first character
            scale: int -> scale of the image
            base: tuple -> base position of the first character
            ax: matplotlib axis
        """
        matches_to_draw = Matches_Interface.MATCHES[char]

        for match in matches_to_draw :
            x, y, angle = Matches_Interface.POS[match]
            x = base[0] + (offset + x) * scale * Matches_Interface.MATCH_INIT_SCALE
            y = base[1] - y * scale * Matches_Interface.MATCH_INIT_SCALE
            angle += randint(-2, 2)

            tr = mpl.transforms.Affine2D().scale(scale).translate(x, y) + ax.transData
            ax.imshow(Matches_Interface.IMG_MATCH.rotate(angle), transform=tr)


    @staticmethod
    def draw_expr(expr, scale, base, ax) :
        """
        Draws all the characters of the expression
        --
        input:
            expr: Matches_Expression -> expression to draw
            scale: float -> scale multiplier of the image
            base: float 2-tuple -> base position of the first character
            ax: plt axis
        """
        for i, char in enumerate(expr.chars) :
            Matches_Interface.draw_char(char, i * 1.5, scale, base, ax)


    def save_riddle(self, folder):
        """
        Generates the image of the riddle, without the solution
        --
        input:
            folder: str -> folder where to save the image
        """
        _, ax = plt.subplots()
        ax.imshow(Matches_Interface.IMG_BACKGROUND)

        plt.axis("off")
        plt.xlim(0, 1920)
        plt.ylim(0, 1080)
        ax.invert_yaxis()
        
        scale = 1156 / (len(self.riddle.chars) * 1.5 * Matches_Interface.MATCH_INIT_SCALE)
        scale = min(scale, 2)  # to avoid too big images

        Matches_Interface.draw_expr(self.riddle, scale, (241, 615 + Matches_Interface.MATCH_INIT_SCALE * scale / 2), ax)

        y1 = 615 + scale * Matches_Interface.MATCH_INIT_SCALE
        y2 = 615 - scale * Matches_Interface.MATCH_INIT_SCALE

        plt.savefig(folder + "riddle.png", bbox_inches='tight', pad_inches=0)
    

    def save_solution(self, folder):
        """
        Generates the image of the riddle + solution together
        --
        input:
            folder: str -> folder where to save the image
        """
        _, ax = plt.subplots()
        ax.imshow(Matches_Interface.IMG_BACKGROUND)

        plt.axis("off")
        plt.xlim(0, 1920)
        plt.ylim(0, 1080)
        ax.invert_yaxis()

        scale = 1156 / (max(len(self.riddle.chars), len(self.main_sol.chars)) * 1.5 * Matches_Interface.MATCH_INIT_SCALE)
        scale = min(scale, 1)  # to avoid too big images

        Matches_Interface.draw_expr(self.riddle, scale, (241, 615 - .7 * Matches_Interface.MATCH_INIT_SCALE * scale), ax)

        Matches_Interface.draw_expr(self.main_sol, scale, (241, 615 + 1.8 * Matches_Interface.MATCH_INIT_SCALE * scale), ax)

        y1 = 615 + scale * Matches_Interface.MATCH_INIT_SCALE
        y2 = 615 - scale * Matches_Interface.MATCH_INIT_SCALE

        plt.savefig(folder + "solution.png", bbox_inches='tight', pad_inches=0)


    def save_all(self, folder):
        """
        Saves both images
        --
        input:
            folder: str -> folder where to save the images
        """
        self.save_riddle(folder)
        self.save_solution(folder)
    
    
class Matches_Expression:
    """
    Class representing an equation
    """
    # Caracters: 0, 0s, 1, 1s, 2, 3, 4, 4s, 5, 6, 6s, 7, 7b, 8, 8s, 9, 9s, +, -, =, nothing
    # BIG PLUS ? Small 3 ?
    ADD_MATCH = {
        '0': ['8'],
        '0s': ['6s', '8s', '9s'],
        '1': ['7'],
        '1s': ['1', '+'],
        '2': [],
        '3': ['9'],
        '4': ['9s'],
        '4s': [],
        '5': ['6', '9'],
        '6': ['8'],
        '6s': ['6'],
        '7': ['7b'],
        '7b': ['9s'],
        '8': [],
        '8s': [],
        '9': ['8'],
        '9s': ['9'],
        '+': ['4s'],
        '-': ['+', '='],
        '=': []
    }
    REMOVE_MATCH = {
        '0': [],
        '0s': [],
        '1': ['1s'],
        '1s': ['nothing'],
        '2': [],
        '3': [],
        '4': [],
        '4s': ['+'],
        '5': [],
        '6': ['5', '6s'],
        '6s': ['0s'],
        '7': ['1'],
        '7b': ['7'],
        '8': ['0', '6', '9'],
        '8s': ['0s'],
        '9': ['3', '5', '9s'],
        '9s': ['0s', '4', '7b'],
        '+': ['-'],
        '-': ['nothing'],
        '=': ['-']
    }
    MOVE_MATCH = {
        '0': ['6', '9'],
        '0s': ['4', '7b'],
        '1': ['+'], # 11s
        '1s': ['-'],
        '2': ['3'],
        '3': ['2', '5', '9s'],
        '4': ['0s', '7b'], #big plus here 11
        '4s': [],
        '5': ['3', '6s', '9s'],
        '6': ['0', '9'],
        '6s': ['5', '8s', '9s'],
        '7': [],
        '7b': ['0s', '4'], # +1 ? 11
        '8': [],
        '8s': ['6s', '9s'],
        '9': ['0', '6'],
        '9s': ['3', '5', '6s', '8s'],
        '+': ['1', '='],
        '-': ['1s'],
        '=': ['+']
    }
    SAME_MATCH = {
        '0': ['0', '0s'],
        '1': ['1', '1s'],
        '2': ['2'],
        '3': ['3'],
        '4': ['4', '4s'],
        '5': ['5'],
        '6': ['6', '6s'],
        '7': ['7', '7b'],
        '8': ['8', '8s'],
        '9': ['9', '9s'],
        '+': ['+'],
        '-': ['-'],
        '=': ['=']
    }
    
    
    def __init__(self, L=None, s=None):
        if L is None:
            self.chars = list(s)
            self.str = s
        elif s is None:
            self.chars = L
            self._update_str()
    

    def _update_str(self):
        """
        Re-generates the `str` attribute based on the char list
        """
        self.str = "".join(char[0] for char in self.chars)  # the str representation does not account for big/small versions of numbers


    def is_valid(self):
        """
        Checks if the expression is valid: it's an equality
        --
        output:
            bool -> True if the entry is valid, False otherwise
        """
        self.remove_spaces()
        
        # check if the expression is an equation
        m = re.match(r"^-?\d+([+-]{1}\d+)*=-?\d+([+-]{1}\d+)*$", self.str)
        
        return m and m.group(0) == self.str


    def remove_spaces(self):
        """
        Removes all spaces from the expression
        """
        self.str = self.str.replace(" ", "")
        self.chars = list(filter(lambda x: x != " ", self.chars))
    

    def is_correct(self, preprocess=False):
        """
        Checks whether the expression has the semantics of an equation and is correct 
        --
        input:
            preprocess: bool -> whether we need to remove spaces and check for the validity of the entry
        --
        output:
            bool -> True if the entry is correct, False otherwise
        """
        if  preprocess:
            if not self.is_valid():
                return False

        # check if the entry is correct
        e1, e2 = self.str.split("=")
        return evaluate_term(list(e1)) == evaluate_term(list(e2))


    def clean(self):
        """
        Removes unwanted characters to simplify the expression
        """
        while 'nothing' in self.chars:
            self.chars.remove('nothing')
        while '11s' in self.chars:
            k = self.index('11s')
            self = self.chars[:k] + ['1s', '1s'] + self.chars[k + 1:]
        while '11' in self.chars:
            k = self.index('11')
            self = self.chars[:k] + ['1', '1'] + self.chars[k + 1:]
        self._update_str()


    def alter_some_characters(self):
        """
        Returns a semantically equivalent expression, with some altered characters (e.g. smaller numbers)
        --
        output:
            res: char list
        """
        return [Matches_Expression.SAME_MATCH[char][randint(0, len(Matches_Expression.SAME_MATCH[char]) - 1)] for char in self.chars]


    def has_fancy_char(self):
        """
        Checks whether the expression has non-classic digits (e.g. small 1)
        --
        output:
            res: bool
        """
        return any(len(char) > 1 for char in self.chars)
    

    def move_far(self):
        """
        Generator for expression obtained by moving one match from one digit to another, or to create a new '1' or '-'
        ⚠️ this cannot generate partial expressions with digits that are not full
        --
        output:
            new_expr: Matches_Expression
        """
        for i, symbol in enumerate(self.chars):
            for new_symbol in Matches_Expression.REMOVE_MATCH[symbol]:
                
                # Move the match on another digit
                for j, symbol2 in enumerate(self.chars):
                    for new_symbol2 in Matches_Expression.ADD_MATCH[symbol2]:

                        if i != j:
                            new_expr_list = copy(self.chars)
                            new_expr_list[i] = new_symbol
                            new_expr_list[j] = new_symbol2

                            new_expr = Matches_Expression(new_expr_list)
                            new_expr.clean()

                            yield new_expr

                # Add a one or a "-" somewhere
                for j in range(len(self.chars) + 1):
                    
                    new_expr_list = copy(self.chars)
                    new_expr_list[i] = new_symbol
                    new_expr_list.insert(j, '1s')
                    
                    new_expr = Matches_Expression(new_expr_list)
                    new_expr.clean()
                    yield new_expr

                    new_expr_list = copy(self.chars)
                    new_expr_list[i] = new_symbol
                    new_expr_list.insert(j, '-')

                    new_expr = Matches_Expression(new_expr_list)
                    new_expr.clean()
                    yield new_expr


    def move_change(self):
        """
        Generator for expression obtained by moving one match from one digit to itself
        ⚠️ this cannot generate partial expressions with digits that are not full
        --
        output:
            final_expr: Matches_Expression
        """
        for i, symbol in enumerate(self.chars):
            for new_symbol in Matches_Expression.MOVE_MATCH[symbol]:
                final_expr_list = copy(self.chars)
                final_expr_list[i] = new_symbol

                final_expr = Matches_Expression(final_expr_list)
                final_expr.clean()
                yield final_expr


    def __str__(self):
        return self.str + " - " + str(self.chars)


    def __repr__(self):
        return self.str + " - " + str(self.chars)


def get_number(digit_list):
    """
    Returns the integer corresponding to a several-digit list (e.g. ["1", "2", "3"] -> 123)
    --
    input:
        digit_list: char/int list, with each char in [0-9]
    --
    output:
        res: int
    """
    return sum([int(dig) * 10 ** i for (i, dig) in enumerate(digit_list[::-1])])


def get_list(number):
    """
    Turns a number into the list of its digit
    --
    input:
        number: int
    --
    output:
        res: char list with elements in [0-9]
    """
    return [dig for dig in list(str(number))]


def gen_number(max_size):
    """
    Generates a random list-representation of a number with up to `max_size` digits
    --
    input:
        max_size: int, > 0
    --
    output:
        res: char list with element in [0-9]
    """
    k = randint(1, max_size)
    return [str(randint(0, 9)) for _ in range(k)]


def evaluate_term(L):
    """
    Evaluates one side of an equation (removes leading 0s then uses eval())
    --
    input:
        L: char list
    --
    output:
        int
    """
    new_L = copy(L)
    to_remove = []
    for i, char in enumerate(new_L):
        if char != "0" or i == len(new_L) - 1: continue

        if i == 0 or ((i - 1 in to_remove or new_L[i - 1] in "+-") and new_L[i + 1] not in "+-"):
            to_remove.append(i)

    for i, j in enumerate(to_remove):
        del new_L[j - i]
    return eval("".join(new_L))


def gen_equality(nb_num_left, nb_num_right):
    """
    Generates a random equality
    --
    input:
        nb_num_left, nb_num_right: int -> amount of numbers on each side of the equal sign
    --
    output:
        Expression
    """

    left_term = gen_number(3)
    res = get_number(left_term)

    # Generating the left part of the equation
    for _ in range(nb_num_left-1):
        op = ['+', '-'][randint(0, 1)]
        new_number = gen_number(3)
        left_term += [op] + new_number
        
    right_term = []
    for _ in range(nb_num_right-1):
        op = ['+', '-'][randint(0, 1)]
        new_number = gen_number(3)
        right_term += [op] + new_number

    res_left = evaluate_term(left_term)
    res_right = evaluate_term(right_term)

    if res_left < res_right:
        pref = ['-']
        res = -res
    else:
        pref = []

    res = left_term + ['='] + pref + get_list(abs(res_left - res_right)) + right_term
    final = [str(t) for t in res]
    #final = alter_some_characters(final) # HEEEEEEEEEEEEEEEEEEEEEEEEEERE
    return Matches_Expression(final)
    

def generate_game(eq, nb_try=300, max_time=inf):
    """
    Generates a riddle. The solution moves exactly one match on another digit, and one match on the same one
    The solution equation is the one with the lowest amount of solutions
    --
    input:
        eq: Matches_Expression
        nb_try: int -> how many modified equations are checked
        max_time: float -> threshold computation time (seconds)
    --
    output:
        riddle: Matches_Expression -> the initial riddle
        sols: str list -> all found possible solutions
    """
    t1 = time.time()
    min_sol = inf
    sols = []
    riddle = None

    move_set1 = list(chain(eq.move_far(), eq.move_change()))
    for i in range(nb_try):
        found = False

        # Computing a valid candidate
        while not found and (i == 0 or time.time() - t1 < max_time):
            cand = choice(move_set1)
            move_set2 = list(chain(cand.move_far(), cand.move_change()))
            candidate = choice(move_set2)
            found = candidate.is_valid() and not candidate.has_fancy_char() and not candidate.is_correct()

        if not found:
            break

        # Counting its solutions
        new_sols = get_all_solutions(candidate)

        if len(new_sols) < min_sol:
            min_sol = len(new_sols)
            sols = new_sols
            riddle = candidate
        
        # If there is only one solution, we can't do better
        if min_sol == 1:
            break

    print(f"Stopped after finding {max(1, i)} candidates")
    return riddle, eq, sols


def get_all_solutions(riddle):
    """
    Computes all the 2-moves solutions from the riddle (the intermediate state must be a valid solution)
    --
    output:
        sols: str list -> equations that would be valid solutions for the given riddle
    """
    sols = []
    for access in chain(riddle.move_change(), riddle.move_far()):
        for accessible in chain(access.move_far(), access.move_change()):
            if accessible.is_valid() and accessible.is_correct() and accessible.str not in sols:
                sols.append(accessible.str)
    
    return sols


async def get_riddle():
    """
    Finds a riddle
    --
    output:
        (Matches_Expression, Matches_Expression, Matches_Expression list) -> solution, initial eq, amount of ways to go from one to the other    
    """
    return await asyncio.to_thread(generate_game, gen_equality(2, 2), max_time=30)