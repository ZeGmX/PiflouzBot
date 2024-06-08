import cairosvg
import chess
import chess.svg
import random
import json
import os
import pandas as pd

def load_chess_database(db_path = "chess_database/"):
    map_path = None
    for file in os.listdir(path=db_path):
        _,filextension = os.path.splitext(file)
        if filextension  == ".json":
            map_path = os.path.join(db_path,file)
            break

    assert map_path is not None
    with open(map_path,"r") as fd:
        mapping = json.load(fd)
    int_mapping = {int(key):[value[0],os.path.join(db_path,value[1])] for key,value in mapping.items()}
    return int_mapping

def lookup_problem(mapping, rating=1500):
    """Get a random problem in a given rating range

    Args:
        mapping (dict): A mapping of ratings to a tuple of (shardsize, shardfilename)
        rating (int, optional): The target problem rating. Defaults to 1500.

    Returns:
        pd.dataframe: The selected problem, with all the columns as in the base database.
    """
    nb_problems,filename = mapping[rating]

    random_problem_index = random.randint(0,nb_problems)
    full_problem_db = pd.read_csv(filename,skiprows=range(1,random_problem_index+1),nrows=1)

    full_problem = full_problem_db.iloc[0]
    return full_problem

if __name__ == "__main__":

    mapping = load_chess_database()
    print(mapping)

    rating = 1500
    import time 
    t0 = time.time()
    result = lookup_problem(mapping=mapping,rating=rating)
    t1 = time.time()
    assert result is not None
    print(f"Basic function took: {t1-t0:.2f}s")

    fen = result["FEN"]
    moves = result["Moves"].split(" ")
    actual_rating = result["Rating"]
    rating_deviation = result["RatingDeviation"]
    print(f"Puzzle rating: {actual_rating} - expected {rating}. Problem rating deviation: {rating_deviation}")
    board = chess.Board(fen=fen)

    for i, move in enumerate(moves):
        board.push(chess.Move.from_uci(move))

        svg_board = chess.svg.board(board=board, size=400, lastmove=chess.Move.from_uci(move))
        cairosvg.svg2png(bytestring=svg_board, write_to=f"board{i}.png")