import cairosvg
import chess
import chess.svg
import time
import pandas as pd


def lookup_problem(rating=1500):
    #TODO: Add other arguments, such as max number of moves?
    # Path to the CSV file
    csv_file_path = "lichess_db_puzzle.csv"
    
    # Columns needed
    usecols = ['Rating', 'RatingDeviation', 'PuzzleId']  # Replace 'PuzzleID' with the actual problem identifier column

    # Chunk size
    chunksize = 20000  # Adjust based on memory constraints

    # Initialize an empty DataFrame to collect potential problems
    potential_problems = pd.DataFrame()

    # Read the CSV file in chunks
    for chunk in pd.read_csv(csv_file_path, usecols=usecols, chunksize=chunksize,header=0):
        # Calculate the lower and upper bounds
        chunk['RatingLowerBound'] = chunk['Rating'] - chunk['RatingDeviation']
        chunk['RatingUpperBound'] = chunk['Rating'] + chunk['RatingDeviation']

        # Filter the chunk
        filtered_chunk = chunk[(rating >= chunk['RatingLowerBound']) & (rating <= chunk['RatingUpperBound'])]

        # Append the filtered chunk to the potential problems DataFrame
        potential_problems = pd.concat([potential_problems, filtered_chunk])

    # If no problems are found, return None
    if potential_problems.empty:
        print(f"Failed to find a chess problem for rating {rating}")
        return None

    # Randomly select one problem from the potential problems
    selected_problem = potential_problems.sample(1)
    selected_index = selected_problem.index.values.astype(int)[0]

    full_problem_csv = pd.read_csv(csv_file_path,skiprows=range(1,selected_index+1),nrows=1)

    full_problem = full_problem_csv.iloc[0]

    #Sanity check.
    assert selected_problem.iloc[0]["PuzzleId"] == full_problem["PuzzleId"], "Wrong rating returned."

    return full_problem



if __name__ == "__main__":
    rating = 1500

    t0 = time.time()
    result = lookup_problem(rating)
    t1 = time.time()
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