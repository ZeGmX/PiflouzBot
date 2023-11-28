import pandas as pd
from random import randint, sample
from unidecode import unidecode


class Subseq_challenge:
    """
    A subsequence challenge is a challenge where the user has to find a word that has a given subsequence
    """


    def __init__(self, subseq, sol):
        self.subseq = subseq
        self.sol = sol


    def check(self, answer):
        """
        Checks if the given answer has the subsequence
        --
        input:
            answer: str
        output:
            bool
        """
        answer = self._clean_word(answer)
        df = pd.read_csv("src/events/assets/french_words.csv", sep=";")
        df = df.astype({"Word": "str"})
        
        if not any(answer == self._clean_word(w) for w in df["Word"]): return False

        it = iter(answer)
        return all(c in it for c in self.subseq)
        


    @staticmethod
    def new(length):
        """
        Generates a new subsequence (and example solution) of the given length
        --
        input:
            length: int -> length of the subsequence
        output:
            Subseq_challenge
        """
        df = pd.read_csv("src/events/assets/french_words.csv", sep=";")
        df = df.astype({"Word": "str"})
        df.sort_values(by="freqlivres", inplace=True, ascending=False)

        # We only chose a solution among the 2000 most common words, not containing punctuation
        # We filter the words that have a length > length + 1 (at least 2 missing letters)
        df = df.head(2000)
        df = df[(df["Word"].str.len() > length + 1) & (~df["Word"].str.contains("[ -.']", regex=True))]
        
        solution = df.iloc[randint(0, len(df) - 1)]["Word"]
        solution_clean = Subseq_challenge._clean_word(solution)

        # We generate a random subsequence of the solution
        subseq_indices = sample(range(len(solution_clean)), length)
        subseq = "".join([solution_clean[i] for i in sorted(subseq_indices)])
        
        return Subseq_challenge(subseq, solution)


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
    
