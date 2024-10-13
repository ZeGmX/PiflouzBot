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
        self.rating = int(rating)
        self.rating_deviation = int(rating_deviation)

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
        problem = lookup_problem(Constants.CHESS_DATABASE_MAPPING, rating)
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

        imageio.mimsave(os.path.join(folder, "chess_puzzle_solution.gif"), board_images, duration=2000, loop=0)

    def to_dict(self):
        return {
            "fen": self.fen,
            "moves": self.moves,
            "rating": self.rating,
            "rating_deviation": self.rating_deviation
        }

    @staticmethod
    def from_dict(data):
        return ChessProblem(**data)

    def check_moves(self, moves):
        """
        Check if the given moves are correct

        Parameters
        ----------
        moves (List[str]):
            List of moves to check

        Returns
        -------
        res (bool):
            True if the moves correspond to the solution the start of the solution
        """
        moves_str = ' '.join(moves)
        return self.moves.startswith(moves_str)
