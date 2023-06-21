DATA_SOURCE="/storage/scratch/e17-4yp-xai/Documents/e17-4yp-using-machine-learning-in-high-stake-settings/code/data/DsDnsPrScTch.csv"
DATA_DEST="/storage/scratch/e17-4yp-xai/Documents/e17-4yp-using-machine-learning-in-high-stake-settings/code/processed_data/"
MODEL_DEST="/storage/scratch/e17-4yp-xai/Documents/e17-4yp-using-machine-learning-in-high-stake-settings/code/trained_models/"
IMAGE_DEST="/storage/scratch/e17-4yp-xai/Documents/e17-4yp-using-machine-learning-in-high-stake-settings/code/model_outputs/figures/"

MAX_ROWS=10000

# To label data  
DONATION_PERIOD=30
THRESHOLD_RATIO=0.4

TRAINING_WINDOW = DONATION_PERIOD * 4

MAX_TIME="2015-12-01 00:00:00"
MIN_TIME="2013-01-01 00:00:00"



DATE_COLS=["Teacher First Project Posted Date", "Project Fully Funded Date", "Project Expiration Date",
            "Project Posted Date", "Donation Received Date"]
CATEGORICAL_COLS=["Project Type", "Project Subject Category Tree", "Project Subject Subcategory Tree", 
                    "Project Grade Level Category", "Project Resource Category", "School Metro Type",
                    "School State", "School County", "Teacher Prefix", "School Name", "School City", "School District"]

TRAINING_FEATURES=["Project Type", "Project Subject Category Tree", "Project Cost",
                  "Project Subject Subcategory Tree", "Project Grade Level Category", "Project Resource Category", 
                  "School Metro Type", "School Percentage Free Lunch", "School State", "School County",
                  "School Name", "School City", "School District",
                  "Teacher Prefix", "Teacher Project Posted Sequence",
                  "Statement Error Ratio", "Title Essay Relativity", "Description Essay Relativity"]

VARIABLES_TO_SCALE=["School Percentage Free Lunch", "Teacher Project Posted Sequence", "Project Cost",
                    "Statement Error Ratio", "Title Essay Relativity", "Description Essay Relativity"]