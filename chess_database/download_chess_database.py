import json
import os
import numpy as np

import pandas as pd
import wget
import zstandard

bdd_name = "lichess_db_puzzle"

min_rating = 500        # Remove ratings under this
max_rating = 2200       # Remove ratings about this
threshold_plays = 100   # Remove puzzles with fewer plays than this
step_size = 100         # Batch the database according to this elo range.

main_db_filename = bdd_name+".csv" # Filename for the DB. Will only be stored locally.

if not os.path.exists(main_db_filename):
    #Download and uncompress the database
    url = "https://database.lichess.org/lichess_db_puzzle.csv.zst"
    print(f"Downloading chess puzzles database from {url}")
    compressed_filename = wget.download(url)
    with open(compressed_filename, 'rb') as compressed:
        decomp = zstandard.ZstdDecompressor()
        with open(main_db_filename,"wb") as destination:
            print(f"\nUnpacking database to {main_db_filename}, removing archive.")
            decomp.copy_stream(compressed,destination)
    os.remove(compressed_filename)

df = pd.read_csv(main_db_filename)

source_df = df # To be able to access the full df at some point if needed.
removed_items = pd.DataFrame({})

print("Base database is downloaded and ready to go.")
df.info()


###### Filter ratings within a bound
print(f"{'-'*5}Filtering out some ratings{'-'*5}")



rating_indexes = (df["Rating"] <= max_rating) & (df["Rating"]>=min_rating)
removed_indexes = (df["Rating"] > max_rating) | (df["Rating"]<min_rating)

to_remove = df[removed_indexes]
removed_items = pd.concat([removed_items,to_remove])
df = df[rating_indexes]

print(f"{len(df)} problems left")

print(f"Removed {len(to_remove)} items with this operation.")

##### Filter out problems that have less than a certain number of plays
print(f"{'-'*5}Filtering out low played problems{'-'*5}")


removed_indexes = df["NbPlays"]<threshold_plays
plays_indexes = df["NbPlays"]>= threshold_plays

to_remove = df[removed_indexes]
removed_items = pd.concat([removed_items,to_remove])
df = df[plays_indexes]

print(f"{len(df)} problems left.")
print(f"Removed {len(to_remove)} items with this operation.")


##### Split the database by ratings
print(f"Rating range: {min_rating}-{max_rating}")


split_ratings = np.arange(min_rating,max_rating,step_size)

split_dfs = {}
for rating in split_ratings:
    top_rating = rating + step_size - 1
    current_rating_pbs = df[(df["Rating"] <= top_rating) & (df["Rating"]>=rating)]
    print(f"{rating}-{top_rating}: {len(current_rating_pbs)}")
    split_dfs[rating] = current_rating_pbs

# Save the split databases and a mapping to the correct lengths, 
# so that it does not need to recompute the lengths at runtime.
mapping = {}
for rating,batch in split_dfs.items():
    batch:pd.DataFrame
    split_db_filename = f"{bdd_name}_Rating{rating}.csv"
    batch.to_csv(split_db_filename)
    mapping[int(rating)]=(int(len(batch)),split_db_filename)
with open(f"{bdd_name}_ratingmapping.json","w") as fd:
    json.dump(mapping,fd)


# Delete the downloaded database
print(f"Cleaning up {main_db_filename}")
os.remove(main_db_filename)