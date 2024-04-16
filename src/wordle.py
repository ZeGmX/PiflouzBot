import random
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image


class Wordle:
    
    from assets.wordle_words import ACCEPTED_WORDS,SOLUTIONS
    
    WORD_SIZE = 5
    NB_ATTEMPTS = 6
    

    def __init__(self, solution=None, debug=False):
        self.debug =debug
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
            if res_status != "":
                continue

            if nbs[letter] < tot[letter]:
                res[i] = "🟨"
                nbs[letter] += 1
            else:
                res[i] = "⬛"

        return "".join(res)

    def is_hard_solution(self, words: list[str]) -> bool:
        """
        Returns whether the solution is for hard mode
        --
        input:
            words (str): The list of guessed words

        output:
            bool: whether the solution is hard mode.
        """
        if self.debug:
            print(f"Launching is_hard function, words {words}, solution: {self.solution}")
        green_letters = [None for _ in range(self.WORD_SIZE)]

        yellow_letters = {}

        black_letters = set()

        correct_letters_count = {} # Will contain (letter:number of known occurence)

        for i_word, word in enumerate(words):
            res = self.guess(word)

            if self.debug:
                print(f"Handling {word}, results: {res}")

            # Check if the previous constraints are met
            # Check the green letters are at the right position
            for letter_position, letter in enumerate(green_letters):
                if letter is not None and res[letter_position]!="🟩":
                    if self.debug:
                        print(f"Index {letter_position} was found to have been {letter}, but is {word[letter_position]} instead")
                    return False

            # Check the yellow letters are indeed in the word.
            for yellow_letter,tested_positions in yellow_letters.items():
                letter_current_position = word.find(yellow_letter)
                if letter_current_position ==-1:
                    # Note: this is handled more precisely by the count check, but we check it now to avoid errors.
                    if self.debug:
                        print(f"Letter {yellow_letter} should have been in {word}.")
                    return False
                elif letter_current_position in tested_positions:
                    if self.debug:
                        print(f"Guess {word}: Letter {yellow_letter} has already been tested at position {letter_current_position}.")
                    return False

            current_correct_letters_count = {letter:0 for letter in word}

            # Check if the localisation constraints are met
            for letter_position,(letter,color) in enumerate(zip(word,res)):
                if self.debug:
                    print(f"Handling position {letter_position}, letter {letter}, color {color}")
                if color == "⬛":
                    if letter in black_letters:
                        if self.debug:
                            print(f"Letter {letter} was already eliminated in a previous guess")
                        return False

                elif color == "🟨":
                    current_correct_letters_count[letter] += 1
                elif color == "🟩":
                    current_correct_letters_count[letter] += 1
                else: # This case should not happen
                    # TODO: switch this to an error raised?
                    print(f"Unexpected color {color} in 'is_hard_solution'")
                    return False

            # Check the correct number of letters of each type is used:
            for letter,number_constraint in correct_letters_count.items():
                if letter not in current_correct_letters_count:
                    if self.debug:
                        print(f"Letter {letter} should have been in the word {word}")
                    return False
                elif current_correct_letters_count[letter]<number_constraint:
                    if self.debug:
                        print(f"Letter {letter} should have been in the word {word} at least {number_constraint} times, but was only {current_correct_letters_count[letter]} times.")
                    return False
                else:
                    pass

            if self.debug:
                print("Updating constraints")

            # Update the count constraints
            for letter,new_number_constraint in current_correct_letters_count.items():
                # Note: Could have used a max, but we check new_number_constraint >= correct_letters_count[letter] above
                if new_number_constraint>0:
                    correct_letters_count[letter] = new_number_constraint


            # Update the spatial constraints
            for letter_position, (letter,color) in enumerate(zip(word,res)):
                if color == "⬛":
                    if letter not in black_letters:
                        # Note: this should ALSO handle the case of multiple guesses of 1 letter
                        # The extra one will be black and thus we have the exact number.
                        black_letters.add(letter)
                    if letter in yellow_letters:
                        yellow_letters[letter].append(letter_position)
                elif color =="🟨":
                    if letter in yellow_letters:
                        yellow_letters[letter].append(letter_position)
                    else: # First time a yellow letter appears
                        yellow_letters[letter] = [letter_position]
                if color == "🟩":
                    green_letters[letter_position] = letter
            

        if self.debug:
            print("This was determined to be a hard solution!")
        return True


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


if __name__=="__main__":
    DEBUG = True
    test_wordle = Wordle("fjord",DEBUG)
    def is_hard_solution_wrapped(words):
        res = test_wordle.is_hard_solution(words)
        test_wordle.generate_image(words)
        print("-" * 50)
        return res


    # Constraint 1: cannot use already denied letters
    assert not is_hard_solution_wrapped(["shush","shush","fjord"]) # all letters from shush reused
    assert not is_hard_solution_wrapped(["shush","arson","fjord"]) # s from shush reused in arson
    assert is_hard_solution_wrapped(["shush","imply","fjord"]) # No common letters between shush and imply

    # Constraint 2: all green letters remain at the same position
    assert not is_hard_solution_wrapped(["flush","dwarf","fjord"]) # f from dwarf is not at the right place
    assert not is_hard_solution_wrapped(["flush","frore","fairy","fjord"]) # o is not in fairy
    assert is_hard_solution_wrapped(["flush","frown","fjord"])  # f remains
    
    # Constraint 3: if a yellow letter appears, it must appear again in a non-green part of the word, but at a different position
    assert not is_hard_solution_wrapped(["voice","youth","fjord"]) # the yellow o remains at the same place
    assert not is_hard_solution_wrapped(["floor","stomp","photo"]) # the 2nd o from floor is yellow -> there is a o in "stomp" but it corresponds to an already green o
    assert is_hard_solution_wrapped(["allow","onset","fjord"]) # the o is yellow and changes position
    assert is_hard_solution_wrapped(["allow","oxids","mound","fjord"])  # the o and d change position
    
    # Constraint 4: if a yellow letter appears yellow/green, it must appear again at least as many times
    test_wordle.solution = "ozone"
    assert not is_hard_solution_wrapped(["bosom","olive","ozone"]) # the o should appear at least twice
    assert is_hard_solution_wrapped(["bosom","outgo","ozone"]) # the o always appears 2 times
    test_wordle.solution = "evade"
    assert is_hard_solution_wrapped(["merit","elpee","evade"]) # the o appears 3 > 1 time
    
    # Constraint 5: if a letter appears gray, it must appear exactly as many times as the amount of times it appears green/yellow
    test_wordle.solution = "bbabb"
    assert not is_hard_solution_wrapped(["axxxa","yaayy","evade"]) # the a (yellow in axxxa) should only appear once
    assert is_hard_solution_wrapped(["axxxa","yayyy","evade"]) # the a appears once
    test_wordle.solution = "abbba"
    assert not is_hard_solution_wrapped(["axaax","ayyyy","abbba"]) # the a (green and yellow in axaax) only appears once
    assert is_hard_solution_wrapped(["axaax","aayyy","abbba"]) # the a (green and yellow in axaax) appears exactly twice
    assert not is_hard_solution_wrapped(["axaax","aayya","abbba"]) # the a (green and yellow in axaax) appears 3 times instead of 2
    
    # Constraint 6: if a letter is gray, it must not appear at the same position
    # (this is also true for yellow, see constraint 3)
    assert not is_hard_solution_wrapped(["riris","bored", "fjord"])  # The r from bored appears at the position of the gray r

    print("All trials are sucessfulls")
