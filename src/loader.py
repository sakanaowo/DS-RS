import pandas as pd
from pathlib import Path

def load_cleaned_jobs():
    """
    Loads the cleaned and merged job postings data.

    This function reads the 'clean_jobs.csv' file from the 'data/processed'
    directory, which is the output of the 1_data_cleaning.ipynb notebook.

    Returns:
        pd.DataFrame: A DataFrame containing the cleaned job data.
    """
    # Define the path to the processed data file, relative to this script's location
    processed_path = Path(__file__).parent.parent / 'data' / 'processed' / 'clean_jobs.csv'

    if not processed_path.exists():
        raise FileNotFoundError(
            f"Cleaned data file not found at {processed_path}. "
            "Please run the '1_data_cleaning.ipynb' notebook first to generate it."
        )

    # Load the CSV file into a DataFrame
    df = pd.read_csv(processed_path)

    # Fill potential NaN values in key text columns for safety
    text_cols = ['title', 'description', 'skills', 'content']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('')

    return df

if __name__ == '__main__':
    # Example of how to use the loader and verify the data
    try:
        jobs_data = load_cleaned_jobs()
        print("Successfully loaded cleaned jobs data.")
        print(f"Shape of the DataFrame: {jobs_data.shape}")
        print("\nDataFrame Info:")
        jobs_data.info(verbose=False)
        print("\nFirst 5 rows:")
        print(jobs_data[['job_id', 'title', 'name', 'location', 'skills']].head())
    except FileNotFoundError as e:
        print(e)