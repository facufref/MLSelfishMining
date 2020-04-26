from scipy.io import wavfile
import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np


def get_train_test(data, filenames, target):
    indices = np.arange(len(filenames))
    X_train, X_test, y_train, y_test, idx1, idx2 = train_test_split(data, target, indices, random_state=0, shuffle=True, train_size=0.75)
    return X_test, X_train, idx1, idx2, y_test, y_train


def get_dataset_from_json(root, file_name, chunk_size):
    df = pd.read_csv(root + file_name)
    data, target, filenames = get_data_and_filenames(df, root, chunk_size)
    return data, target, filenames


def get_data_and_filenames(df, root, chunk_size):
    list_time_rates = []
    filenames = []
    target = []
    df.set_index('fname', inplace=True)
    for f in df.index:
        file = pd.read_json(root + f)
        rates = get_time_rate(file.chain)
        split_rates = list(chunks(rates, chunk_size))
        if len(split_rates[-1]) < chunk_size:  # Remove element if it is not the same size than the others
            split_rates.remove(split_rates[-1])
        repeated_filenames = [f] * len(split_rates)
        filenames.extend(repeated_filenames)
        repeated_target = [df.at[f, 'class']] * len(split_rates)
        target.extend(repeated_target)
        append_meta_data(split_rates, file.iterations_to_consult[0], file.complexity[0], file.nodes[0])
        list_time_rates.append(split_rates)
    data = np.vstack(list_time_rates)
    return data, target, filenames


def append_meta_data(rates, iterations, complexity, nodes):
    for item in rates:
        item.append(iterations)
        item.append(complexity)
        item.append(nodes)


def get_time_rate(chain):
    last_timestamp = -1
    rates = []
    for block in chain:
        timestamp = block['timestamp']
        if last_timestamp == -1:
            last_timestamp = timestamp
            continue
        rate = timestamp - last_timestamp
        rates.append(rate)
        last_timestamp = timestamp
    return rates


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def pre_process(X_test, X_train):
    """One way to pre process I found on "Introduction to machine learning with Python: a guide for data scientists." Chapter 2
        There must be a better way to do this"""
    # compute the mean value per feature on the training set
    mean_on_train = X_train.mean(axis=0)
    # compute the standard deviation of each feature on the training set
    std_on_train = X_train.std(axis=0)
    # subtract the mean, scale by inverse standard deviation
    # afterwards, mean=0 and std=1
    X_train_scaled = (X_train - mean_on_train) / std_on_train
    # use THE SAME transformation (using training mean and std) on the test set
    X_test_scaled = (X_test - mean_on_train) / std_on_train
    return X_test_scaled, X_train_scaled

