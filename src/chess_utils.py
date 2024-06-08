import cairosvg
import chess
import chess.svg
import imageio
import random
import json
import os
import pandas as pd

def load_chess_database(db_path = "chess_database/"):
    """Get the mapping dictionnary to load databases paths.

    Args:
        db_path (str, optional): The path to the folder containing the database. Defaults to "chess_database/".

    Returns:
        dict: A mapping of ratings to a tuple of (shardsize, shardfilename)
    """
    map_path = None
    for file in os.listdir(path=db_path):
        _,filextension = os.path.splitext(file)
        if filextension  == ".json":
            map_path = os.path.join(db_path,file)
            break

    assert map_path is not None
    with open(map_path,"r") as fd:
        mapping = json.load(fd)
    int_mapping = {int(key):(value[0],os.path.join(db_path,value[1])) for key,value in mapping.items()}
    return int_mapping

def lookup_problem(mapping, rating=1500):
    """Get a random problem in a given rating range

    Args:
        mapping (dict): A mapping of ratings to a tuple of (shardsize, shardfilename)
        rating (int, optional): The target problem rating. Defaults to 1500.

    Returns:
        dic: The selected problem, with all the attributes as in the base database.
    """
    nb_problems,filename = mapping[rating]

    random_problem_index = random.randint(0,nb_problems)
    full_problem_db = pd.read_csv(filename,skiprows=range(1,random_problem_index+1),nrows=1)

    full_problem = full_problem_db.iloc[0]
    full_problem_dic = {}
    for key in ["PuzzleId","FEN","Moves","Rating","RatingDeviation","Popularity","NbPlays","Themes","GameUrl","OpeningTags"]:
        full_problem_dic[key] = full_problem[key]
    return full_problem_dic

if __name__ == "__main__":

    mapping = load_chess_database()
    print(mapping)
    temp_filename = "board.png"

    rating = 2000
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
    board_images = []
    for i, move in enumerate(moves):
        board.push(chess.Move.from_uci(move))

        svg_board = chess.svg.board(board=board, size=400, lastmove=chess.Move.from_uci(move))
        cairosvg.svg2png(bytestring=svg_board, write_to=temp_filename)
        board_images.append(imageio.imread(temp_filename))
    
    os.remove(temp_filename)
    print(f"{i} moves to do: {moves}")
    imageio.mimsave("solution.gif",board_images,duration=2000)
