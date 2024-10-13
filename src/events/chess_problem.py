import cairosvg
import chess
import chess.svg
import imageio
import os

from chess_utils import lookup_problem
from constant import Constants


class ChessProblem:

    def __init__(self, fen, moves, rating, rating_deviation) -> None:
        self.fen = fen
        self.moves = moves
        self.moves_list = self.moves.split(' ')
        self.rating = rating
        self.rating_deviation = rating_deviation

    @staticmethod
    def new_problem(rating):
        """
        Returns a new chess problem with the given rating

        Parameters
        ----------
        rating : int
            Desired rating of the problem

        Returns
        -------
        res (ChessProblem)
        """
        problem = lookup_problem(Constants.CHESS_DATABASE_MAPPING)
        return ChessProblem(
            fen=problem["FEN"],
            moves=problem["Moves"],
            rating=problem["Rating"],
            rating_deviation=problem["RatingDeviation"]
        )

    def save_all(self, folder):
        """
        Saves all images in the execution + result gif

        Parameters
        ----------
        folder (str):
            folder where to save the images
        """
        board = chess.Board(fen=self.fen)
        board_images = []
        for i, move in enumerate(self.moves_list):
            board.push(chess.Move.from_uci(move))
            image_location = os.path.join(folder, f"board{i}.png")

            svg_board = chess.svg.board(board=board, size=400, lastmove=chess.Move.from_uci(move))
            cairosvg.svg2png(bytestring=svg_board, write_to=image_location)
            board_images.append(imageio.imread(image_location))

        imageio.mimsave(os.path.join(folder, "chess_puzzle_solution.gif"), board_images, duration=2000)
