import matplotlib.pyplot as plt
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier


class SelfishMiningClassifier:
    def __init__(self, algorithm):
        if algorithm == 'knn':
            self._classifier = KNeighborsClassifier(n_neighbors=6)
        elif algorithm == 'linear':
            self._classifier = LogisticRegression()  # alternative => (C=100) / (C=0.01)
        elif algorithm == 'linearMulti':
            self._classifier = LinearSVC()
        elif algorithm == 'decisionTree':
            self._classifier = DecisionTreeClassifier(random_state=0)  # alternative => max_depth=4
        elif algorithm == 'randomForest':
            self._classifier = RandomForestClassifier(n_estimators=100, random_state=0)
        elif algorithm == 'gradientBoosting':
            self._classifier = GradientBoostingClassifier(random_state=0)  # alternative => max_depth=1, learning_rate=0.01
        elif algorithm == 'svm':
            self._classifier = SVC()  # alternative => C=1000, gamma=1000. Also pre-process data
        elif algorithm == 'neuralNetworks':
            self._classifier = MLPClassifier(random_state=0)  # alternative => max_iter=1000, alpha=1. Also pre-process data
        else:
            print('Algorithm not found')

    def train_classifier(self, X_train, y_train):
        self._classifier.fit(X_train, y_train)

    def get_predictions(self, X_test):
        return self._classifier.predict(X_test)

    def get_accuracy(self, X_test, y_test):
        return self._classifier.score(X_test, y_test)

    def show_feature_importance(self, data, target):
        """Only works with algorithms that have feature_importances_ attribute"""
        plt.plot(self._classifier.feature_importances_, 'o')
        plt.xticks(range(data.shape[1]), target, rotation=90);
        plt.show()

    def print_decision_function(self, X_test):
        """Only works with algorithms that have decision_function method"""
        print(self._classifier.decision_function(X_test))
        # We can recover the predictions by computing the argmax
        print(np.argmax(self._classifier.decision_function(X_test), axis=1))
        print(self._classifier.predict(X_test))

    def print_prediction_probability(self, X_test):
        """Only works with algorithms that have predict_proba method"""
        print(self._classifier.predict_proba(X_test))
        # We can recover the predictions by computing the argmax
        print(np.argmax(self._classifier.decision_function(X_test), axis=1))
        print(self._classifier.predict(X_test))


def print_predictions(predictions, filenames, idx2):
    for i in range(0, len(predictions)):
        print(f" The file '{filenames[idx2[i]]} is {str(predictions[i])}")

