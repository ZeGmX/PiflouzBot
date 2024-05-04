import bisect
import pandas as pd
from random import sample, choice
import re
from unidecode import unidecode


class Subseq_challenge:
    """
    A subsequence challenge is a challenge where the user has to find a word that has a given subsequence
    """


    def __init__(self, subseq):
        self.subseq = subseq


    def check_default(self, answer, all_clean_words=None, check_if_real_word=True):
        """
        Checks if the given answer is a real word and has the subsequence
        --
        input:
            answer: str
            all_clean_words: List[str] -> list of all accepted (clean) words
            check_if_real_word: bool -> whether to check if the answer is in the list of all accepted words
        --
        output:
            bool
        """
        answer = self._clean_word(answer)
        if all_clean_words is None:
            all_clean_words = Subseq_challenge.get_word_list("src/events/assets/all_french_words_clean.txt")
        
        if check_if_real_word:
            # Binary search to check if the answer is in the list of all accepted words (faster than using "in" since the list is sorted)
            i = bisect.bisect_left(all_clean_words, answer)
            if i == len(all_clean_words) or all_clean_words[i] != answer: return False

        it = iter(answer)
        return all(c in it for c in self.subseq)
    

    def check_projection(self, answer):
        """
        Verifies that the subsequence is a projection of the answer, ie, all letters in the subsequence appear exactly as many times in the answer
        E.g. subseq = "abc", answer = "abracadabra" -> False because there are several "a"s and "b"s in the answer
        E.g. subseq = "aaaaabbc", answer = "abracadabra" -> True
        --
        input:
            answer: str
        --
        output:
            bool
        """
        answer = self._clean_word(answer)
        return all(answer.count(c) == self.subseq.count(c) for c in self.subseq)


    def check_with_intermediate(self, answer):
        """
        Verifies that the answer has the correct subsequence, including at least one letter between each pair of letters in the subsequence
        E.g. subseq = "abc", answer = "abracadabra" -> False: need to match as [a][b]ra[c]adabra, but there is no letter between "a" and "b"
        E.g. subseq = "aba", answer = "abracadabra" -> True: [a]bracada[b]r[a]
        --
        input:  
            answer: str
        --
        output:
            bool
        """
        answer = self._clean_word(answer)
        pattern = ".*" + ".+".join(self.subseq) + ".*"
        return bool(re.match(pattern, answer))


    @staticmethod
    def new(length):
        """
        Generates a new subsequence (and example solution) of the given length
        --
        input:
            length: int -> length of the subsequence
        output:
            Subseq_challenge
            List[int] -> how many solutions there are for each level
            str -> example solution that solves all levels
        """
        easy_words = Subseq_challenge.get_word_list("src/events/assets/easy_french_words.txt")
        all_clean_words = Subseq_challenge.get_word_list("src/events/assets/all_french_words_clean.txt")
        all_words = Subseq_challenge.get_word_list("src/events/assets/all_french_words.txt")
        
        i = 1
        res = Subseq_challenge.attempt_find_new(easy_words, all_words, all_clean_words, length)
        while res is None:
            i += 1
            res = Subseq_challenge.attempt_find_new(easy_words, all_words, all_clean_words, length)

        print(f"Found in {i} iterations")
        
        subseq, solutions = res
        return subseq, [len(set(s)) for s in solutions], solutions[3][0]
    

    @staticmethod
    def attempt_find_new(easy_words, all_words, all_clean_words, length):
        """
        Attempts to find a new subsequence challenge, meeting the following difficulty conditions:
        - There exists a solution in the top 2000 most common words
        - There exists a solution for each level (= there exists a level 4 condition)
        - There are no solutions obtained by adding less than 2 letters
        --
        input:
            easy_words: List[str] -> list of the top 2000 most common words
            all_words: List[str] -> list of all words  = all accepted answers
            all_clean_words: List[str] -> list of all (cleaned) words
            length: int -> length of the subsequence
        --
        output:
            subseq: Subseq_challenge -> the subsequence object
            all_sols: List[List[str]] -> list of solutions for each level
        """
        # Condition 1: there exists a solution in the top 2000 most common words
        solution_lvl1 = choice(easy_words)
        solution_lvl1_clean = Subseq_challenge._clean_word(solution_lvl1)

        if len(solution_lvl1_clean) < length + 2: return None

        # We generate a random subsequence of the solution
        subseq_indices = sample(range(len(solution_lvl1_clean)), length)
        subseq = "".join([solution_lvl1_clean[i] for i in sorted(subseq_indices)])

        # Count how many solutions  match each level
        subseq = Subseq_challenge(subseq)
        all_sols = [[], [], [], []]

        for i, word_clean in enumerate(all_clean_words):
            word = all_words[i]
            b1 = subseq.check_default(word_clean, all_clean_words=easy_words, check_if_real_word=False)
            b2 = subseq.check_projection(word_clean)
            b3 = subseq.check_with_intermediate(word_clean)

            # Condition 2: there are no solutions obtained by adding less than 2 letters
            if b1 and len(word) < len(subseq.subseq) + 2: return None
            
            if b1: all_sols[0].append(word)
            if b1 and b2: all_sols[1].append(word)
            if b1 and b3: all_sols[2].append(word)
            if b1 and b2 and b3: all_sols[3].append(word)
        
        # Condition 3: there exists a solution for each level
        if any(len(s) == 0 for s in all_sols): return None

        return subseq, all_sols


    @staticmethod
    def _clean_word(word):
        """
        Sanitizes a word by removing accents and punctuation, and converting it to lowercase
        --
        input:
            word: str
        --
        output:
            str
        """
        res = unidecode(word.lower())
        return "".join(filter(lambda c: c in "abcdefghijklmnopqrstuvwxyz", res))

    
    @staticmethod
    def get_word_list(path):
        """
        Returns word list from a given path
        --
        input:
            path: str -> path to the file containing the word list. Each word should be on a separate line, with no header
        --
        output:
            List[str]
        """
        df = pd.read_csv(path, header=None, encoding="latin-1")
        return df.astype(str)[0].tolist()


    @staticmethod
    def get_unclean_equivalent(*words):
        """
        Returns the unclean equivalent of the given clean words
        --
        input:
            words: List[str] -> list of clean words
        --
        output:
            List[str] -> list of unclean words
        """
        all_clean_words = Subseq_challenge.get_word_list("src/events/assets/all_french_words_clean.txt")
        all_words = Subseq_challenge.get_word_list("src/events/assets/all_french_words.txt")
        
        res = []
        for word in words:
            i = bisect.bisect_left(all_clean_words, word)
            
            if i == len(all_clean_words) or all_clean_words[i] != word:
                raise ValueError(f"Word {word} not found in the list of all clean words")

            res.append(all_words[i])
        return res