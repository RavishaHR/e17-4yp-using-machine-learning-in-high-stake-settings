from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix
from pandas.core.frame import DataFrame
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, f1_score, accuracy_score, precision_score, recall_score
import language_tool_python
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import config
import data_processor as dp

lang_tool = language_tool_python.LanguageTool('en-US')


def standardize_data(x_train, x_test, cols_list):
    """Function for scaling after seperating into train/test."""
    # Create scaler
    ss = StandardScaler()
    features_train = x_train[cols_list]
    features_test = x_test[cols_list]

    # Fit scaler only for training data
    scaler = ss.fit(features_train)

    # Transform training data
    features_t = scaler.transform(features_train)
    x_train[cols_list] = features_t

    # Transforming test data
    for_test = scaler.transform(features_test)
    x_test[cols_list] = for_test

    return x_train, x_test


def create_features(data: DataFrame):
    data = add_statement_grammertical_error_feature(data)
    data = add_title_essay_relativity_score(data)
    data = add_desc_essay_relativity_score(data)
    return data.drop_duplicates()

def add_statement_grammertical_error_feature(data: DataFrame):
    # Creates a new feature called text size to error ratio
    data["Statement Error Ratio"] = len(lang_tool.check(
        str(data["Project Need Statement"]))) / len(str(data["Project Need Statement"]).split())
    return data

def add_title_essay_relativity_score(data: DataFrame):
    # Create a new feature that has the relatedness of title and essay
    # using cosine similarity

    # Create a TfidfVectorizer object
    vectorizer = TfidfVectorizer()

    # Fit and transform the 'text' column to obtain the TF-IDF matrix
    tfidf_matrix = vectorizer.fit_transform(data['Project Essay'])

    # Calculate the cosine similarity matrix between the 'topic' and 'text' columns
    similarity_matrix = cosine_similarity(tfidf_matrix, vectorizer.transform(data['Project Title']))

    # Create a new feature "Title Essay Relativity" in the DataFrame and assign the similarity scores
    data["Title Essay Relativity"] = similarity_matrix.diagonal()

    return data


def add_desc_essay_relativity_score(data: DataFrame):
    # Create a new feature that has the relatedness of description and essay
    # using cosine similarity

    # Create a TfidfVectorizer object
    vectorizer = TfidfVectorizer()

    # Fit and transform the 'text' column to obtain the TF-IDF matrix
    tfidf_matrix = vectorizer.fit_transform(data['Project Essay'])

    # Calculate the cosine similarity matrix between the 'topic' and 'text' columns
    similarity_matrix = cosine_similarity(tfidf_matrix, vectorizer.transform(data['Project Short Description']))

    # Create a new feature "Title Essay Relativity" in the DataFrame and assign the similarity scores
    data["Description Essay Relativity"] = similarity_matrix.diagonal()

    return data


def label_data_1(data: DataFrame, threshold: float, select_cols: list):
    # Create new features by aggregating
    data["Total Donations"] = data.groupby("Project ID")["Donation Amount"] \
                                                        .transform("sum")

    data["Donation to Cost"] = data["Donation Amount"] / data["Project Cost"]

    data["Fund Ratio"] = data.groupby("Project ID")["Donation to Cost"] \
                                                        .transform("sum")

    data["Label"] = data.apply(
        lambda x : 0  if x["Fund Ratio"] < threshold  else 1, axis=1)
    select_cols = select_cols + ["Label", "Project Posted Date"]
    return data[select_cols].drop_duplicates()

def get_best_label_threshold(data: DataFrame):
    actual_donation_period = 120


def label_data(data: DataFrame, threshold: float):
    data["Posted Date to Donation Date"] = data["Donation Received Date"] \
                                                 - data["Project Posted Date"]
    data["Posted Date to Donation Date"] = data["Posted Date to Donation Date"] \
                                                    / np.timedelta64(1, 'D')

    data = data[data["Posted Date to Donation Date"] < config.DONATION_PERIOD]

    data["Total Donations In The Period"] = data.groupby(
                            "Project ID")["Donation Amount"].transform("sum")
    data["Fund Ratio"] = np.where(
        data["Project Cost"] > 0, 
        data["Total Donations In The Period"] / data["Project Cost"], 1)

    data["Label"] = data.apply(
        lambda x : 0  if x["Fund Ratio"] < threshold  else 1, axis=1)

    return data.drop_duplicates()


def get_best_proba_threshold_prediction(proba_predictions: list, y_test):
    thresholds = list(np.arange(0.3, 0.7, 0.05).round(2))
    best_threshold = None
    best_f1_score = 0.0
    best_prediction = None

    for threshold in thresholds:
        # Convert probabilities to binary predictions based on the threshold
        binary_predictions = (proba_predictions[:, 1] >= threshold).astype(int)

        # Calculate F1 score
        f1 = f1_score(y_test, binary_predictions)

        if f1 > best_f1_score:
            best_f1_score = f1
            best_threshold = threshold
            best_prediction = binary_predictions
    # print("best_f1_score = ", best_f1_score)
    return best_threshold, best_prediction


# Function to observe PR to select the best k
def prk_curve_for_top_k_projects(proba_predictions: list, k_start: int, k_end: int, k_gap: int, y_test, t_current):
    # Temp: consider 0 for failing projects and 1 for projects getting fully funded in four months
    # Select the probabilities for label 1
    probabilities = proba_predictions[:, 1]
    # Rank the probabilities in descending order
    temp = (-1 * probabilities).argsort()
    ranks = np.empty_like(temp)
    ranks[temp] = np.arange(len(probabilities))

    # Create new labels based on the k value and plot precision and recall
    precision = []
    recall = []
    k_value = []
    new_labels = []
    for k in range(k_start, k_end+k_gap, k_gap):
        k_labels = (ranks <= k).astype(int)
        new_labels.append(k_labels)
        k_value.append(k)
        k_precision = precision_score(y_test, k_labels)
        k_recall = recall_score(y_test, k_labels)
        precision.append(k_precision)
        recall.append(k_recall)

    # Plot the prk curve
    plt.cla()
    plt.plot(k_value, precision, label='precision')
    plt.plot(k_value, recall, label='recall')
    plt.xlabel('Value of k')
    plt.title("Model's Precision and Recall for Varying k")
    plt.legend()
    plt.savefig(config.K_PROJECTS_DEST+ f"prk_curve_for_{t_current[:10]}")
    plt.show()

    return


def run_pipeline(data, model):
    # Initiate lists to store data
    t_current_list = []
    t_current_accuracy = []

    # Initiate timing variables
    max_t = pd.Timestamp(config.MAX_TIME)
    min_t = pd.Timestamp(config.MIN_TIME)
    time_period = timedelta(days=config.DONATION_PERIOD)        # 30 days
    training_window = timedelta(days=config.TRAINING_WINDOW)    # 30 * 4 = 120 days

    t_current = min_t
    print("================\n", t_current, max_t, training_window)

    probability_thresholds = []
    model_eval_metrics =  {"accuracy": [], "f1_score": [], "model_score": []}

    folds = 0

    while(t_current < max_t - training_window):

        t_current_list += [t_current]
        t_start = t_current
        t_end = t_current + training_window
        t_filter = t_end - time_period

        # Filter rows for the relevant time period
        data_window = data[
            data["Project Posted Date"] < pd.to_datetime(t_end)]
        data_window = data_window[
            data_window["Project Posted Date"] > pd.to_datetime(t_start)]
        
        print("iteration_data.shape = ", data_window.shape)

        x_train, y_train, x_test, y_test = dp.split_time_series_train_test_data(
            data=data_window, filter_date=t_filter)
        
        # Training will be done on data from t_start to t_filter
        # Testing will be done on data from t_filter to t_end

        # Scaling
        x_train, x_test = standardize_data(x_train, x_test, config.VARIABLES_TO_SCALE)

        # Model Training
        model = model.fit(x_train, y_train.values.ravel())

        # Predicting
        y_hat = model.predict_proba(x_test)

        # Find the best probability threshold for classifying
        best_threshold ,best_prediction = get_best_proba_threshold_prediction(y_hat, y_test)

        # Evaluate the model
        f1 = f1_score(y_test, best_prediction)
        accuracy = accuracy_score(y_test, best_prediction)
        model_score = model.score(x_test, y_test)

        probability_thresholds.append(best_threshold)
        model_eval_metrics["accuracy"].append(accuracy)
        model_eval_metrics["f1_score"].append(f1)
        model_eval_metrics["model_score"].append(model_score)
        
        print("==============================================================================")
        print(f"Traing  from {str(t_start)[:10]} to {str(t_filter)[:10]}")
        print(f"Testing from {str(t_filter)[:10]} to {str(t_end)[:10]}")
        print("Training set shape = ", x_train.shape)
        print("Testing set shape = ", x_test.shape)
        print("Prediction evaluation scores for testing: ")
        print("best_threshold = ", best_threshold)
        print("F1 score = ", f1)
        print("Accuracy = ", accuracy)
        print("Model score = ", model_score)

        # break
        # y_pred = model.predict_proba(x_train)

        # Evaluate
        # cm = confusion_matrix(y_test, y_hat)
        # sns.heatmap(cm, square=True, annot=True, cbar=False)
        # plt.xlabel('Predicted Value')
        # plt.ylabel('Actual Value')
        # plt.savefig(config.IMAGE_DEST + f"Confusion matrix for {str(t_current)[:10]}")
        # plt.clf()

        # print("Prediction evaluation scores for training: ")
        # print(classification_report(y_train, y_pred, output_dict=True))


        # print(classification_report(y_test, y_hat, output_dict=True))
        print("==============================================================================\n")
        t_current = t_current + time_period
        folds += 1
    
    print("")
    print("probability_thresholds = ", probability_thresholds)
    print("accuracies = ", model_eval_metrics["accuracy"])
    print("f1_scores = ", model_eval_metrics["f1_score"])
    print("model_scores = ", model_eval_metrics["model_score"])

    avg_metrics = {"avg_accuracy": sum(model_eval_metrics["accuracy"])/len(model_eval_metrics["accuracy"]),
                   "avg_f1_score": sum(model_eval_metrics["f1_score"])/len(model_eval_metrics["f1_score"]),
                   "avg_model_score": sum(model_eval_metrics["model_score"])/len(model_eval_metrics["model_score"]),
                   "avg_proba_thresh": sum(probability_thresholds)/len(probability_thresholds)}

    print("")
    print("Average accuracy = ", avg_metrics["avg_accuracy"])
    print("Average f1_score = ", avg_metrics["avg_f1_score"])
    print("Average model score = ", avg_metrics["avg_model_score"])
    print("Average probability_threshold = ", avg_metrics["avg_proba_thresh"])

    

    # Filter rows for the relevant time period
    data_window = data[
        data["Project Posted Date"] < pd.to_datetime(max_t)]
    data_window = data_window[
        data_window["Project Posted Date"] > pd.to_datetime(min_t)]
    t_filter = max_t - folds * time_period

    x_train, y_train, x_test, y_test = dp.split_time_series_train_test_data(
            data=data_window, filter_date=t_filter)
    
    # Scaling
    x_train, x_test = standardize_data(x_train, x_test, config.VARIABLES_TO_SCALE)

    # Model Training
    model = model.fit(x_train, y_train.values.ravel())

    return model, model_eval_metrics, avg_metrics


def plot_k_fold_evaluation_metrics(model_eval_metrics: dict):
    x_labels = [f"Fold {i+1}" for i in range(len(model_eval_metrics.get("accuracy", 0)))]
    x_positions = np.arange(len(x_labels))
    bar_width = 0.2
    
    # Plot accuracy and f1 score for all the folds
    print( x_positions, bar_width, len(model_eval_metrics["accuracy"]), len(model_eval_metrics["f1_score"]))
    plt.bar(x_positions - bar_width, model_eval_metrics["accuracy"], width=bar_width, label='Accuracy')
    plt.bar(x_positions, model_eval_metrics["f1_score"], width=bar_width, label='F1 Score')
    
    plt.xlabel('Evaluation Metrics')
    plt.ylabel('Values')
    plt.title("Model's Accuracy and F1 Score for Each validation fold")
    plt.xticks(x_positions, x_labels, rotation = 90)
    plt.legend()
    plt.savefig(config.IMAGE_DEST+'cross_validation_plot.png')
    plt.show()

    # Plot the model accuracy for all the folds
    plt.cla()
    plt.plot(x_labels, model_eval_metrics["model_score"])

    plt.xlabel('Fold')
    plt.ylabel('Model Score')
    plt.title("Model Score for each fold")
    plt.xticks(x_positions, x_labels, rotation = 90)
    plt.savefig(config.IMAGE_DEST+'model_score_plot.png')
    plt.show()

