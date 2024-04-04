import random
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image


class Wordle:
    
    from assets.wordle_words import ACCEPTED_WORDS,SOLUTIONS
    
    WORD_SIZE = 5
    NB_ATTEMPTS = 6
    
    
    def __init__(self, solution=None):
        if solution is None:
            solution = random.choice(self.SOLUTIONS)
        
        self.solution = solution


    def is_valid(self, word):
        """
        Checks if the word is a valid english word
        --
        input:
            word: str
        --
        output:
            res: bool
        """
        return word.lower() in self.SOLUTIONS or word in self.ACCEPTED_WORDS

    
    def guess(self, word):
        """
        Returns the string corresponding to the guess of the given word
        --
        input:
            word: str
        --
        output:
            res: str
        """
        word = word.lower()
        res = []

        nbs = {letter: 0 for letter in self.solution}
        tot = {letter: self.solution.count(letter) for letter in self.solution}

        for i, letter in enumerate(word):
            if self.solution[i] == letter: 
                res.append("🟩")  
                nbs[letter] += 1
            elif letter not in self.solution:
                res.append("⬛")
            else: res.append("")

        for i, (letter, res_status) in enumerate(zip(word, res)):
            if res_status != "": continue

            if nbs[letter] < tot[letter]:
                res[i] = "🟨"
                nbs[letter] += 1
            else: 
                res[i] = "⬛"

        return "".join(res)
        
        
    def generate_image(self, words, path="wordle.png"):
        """
        Creates an image representing the current state of a wordle game
        --
        input:
            words: str list -> the different guesses
            path: str -> where the image will be generated
        """
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_aspect("equal")
        plt.xlim(-10, 110)
        plt.ylim(-50, 130)
        plt.axis("off")

        fill_colors = {"🟩": "green", "🟨": "y", "⬛": "black"}
        outline_color = "gray"    
        key_status = {letter: "gray" for letter in "abcdefghijklmnopqrstuvwxyz"}

        # Drawing the guesses
        for i_word, word in enumerate(words):
            res = self.guess(word)
            for j, result_status in enumerate(res):
                i = self.WORD_SIZE - i_word # in order to draw the words from the top
                letter = word[j]
                color = fill_colors[result_status]
                position = (20 * j, 20 * i)
                rect = Rectangle(position, 17, 17, edgecolor="none", facecolor=color)
                ax.add_patch(rect)
                plt.text(position[0] + 8.5, position[1] + 7.5, letter.upper(), color="white", fontsize=32, ha="center", va="center")

                if color == "green":
                    key_status[letter] = "green"
                elif color == "y" and key_status[letter] != "green":
                    key_status[letter] = "y"
                elif color == "black" and key_status[letter] == "gray":
                    key_status[letter] = "black"

        # Drawing the grid outline
        for i in range(self.NB_ATTEMPTS):
            for j in range(self.WORD_SIZE):
                rect = Rectangle((20 * j, 20 * i), 17, 17, edgecolor=outline_color, facecolor="none", linewidth=3)
                ax.add_patch(rect)

        # Drawing the keyboard
                keyboard_layout = ["azertyuiop", "qsdfghjklm", "wxcvbn"]   
        for i, row in enumerate(keyboard_layout):
            shift = 5 * (i - .5)
            for j, letter in enumerate(row):
                position = (10 * j + shift, -10 * i - 20)
                rect = Rectangle(position, 8, 8, edgecolor="none", facecolor=key_status[letter])
                ax.add_patch(rect)

                color = "white" if key_status[letter] != "black" else "black"
                plt.text(position[0] + 3.8, position[1] + 3.5, letter.upper(), color=color, fontsize=12, ha="center", va="center")

        plt.savefig(path, transparent=True)
        # Cropping the white outline
        img = Image.open(path)
        img.load()
        cropped = img.crop((250, 150, img.size[0] - 250, img.size[1] - 130))
        cropped.save(path)
        