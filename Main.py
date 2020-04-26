from SelfishMiningDataManager import *
from sklearn.metrics import classification_report
from SelfishMiningClassifier import *
from GeneralSettings import chunk_size
from sklearn.externals import joblib


def main():
    algorithm = 'svm'
    data, target, filenames = get_dataset_from_json('Training/', 'labels.csv', chunk_size)
    X_test, X_train, idx1, idx2, y_test, y_train = get_train_test(data, filenames, target)
    clf = SelfishMiningClassifier(algorithm)
    clf.train_classifier(X_train, y_train)

    filename = f'Models/{algorithm}.joblib.pkl'
    joblib.dump(clf, filename)
    # clf2 = joblib.load(filename)

    predictions = clf.get_predictions(X_test)
    print_predictions(predictions, filenames, idx2)
    print(f"Accuracy Train =  {str(clf.get_accuracy(X_train, y_train))}")
    print(f"Accuracy Test  =  {str(clf.get_accuracy(X_test, y_test))}")
    print(classification_report(y_test, predictions))
    # clf.show_feature_importance(data, target)
    # clf.print_decision_function(X_test)
    # clf.print_prediction_probability(X_test)


if __name__ == '__main__':
    main()
