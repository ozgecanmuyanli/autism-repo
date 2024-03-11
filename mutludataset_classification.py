# -*- coding: utf-8 -*-
"""mutluDataset-classification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dMP0JEM8-bKaQ9tTOb9bMWgic_PMnXgR
"""

pip install ReliefF

pip install alibi

pip install shap

!mkdir -p drive
!google-drive-ocamlfuse drive

from google.colab import drive
drive.mount('/content/drive')

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.gridspec as grid_spec
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import roc_curve,roc_auc_score, auc
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.metrics import f1_score
from sklearn import tree
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.naive_bayes import BernoulliNB
from sklearn import preprocessing # Import label encoder

# Feature Importance
from ReliefF import ReliefF
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
from sklearn.feature_selection import mutual_info_classif
from sklearn.feature_selection import RFE

# XAI
import shap
shap.initjs()
from alibi.explainers import KernelShap

np.random.seed(42)

"""# FUNCTIONS

## Feature Selection Functions
"""

def get_features_reliefF(data, target, n_features_to_select):
  fs = ReliefF(n_neighbors=1, n_features_to_keep=n_features_to_select)
  features = fs.fit_transform(data.to_numpy(), target.to_numpy()).T

  columns = data.columns.to_list()
  reliefF_features = []
  for feature in features:
      for column in columns:
        idx = (data[column] == feature)
        if idx.all() == True:
          reliefF_features.append(column)
          break

  #print('Top-10 features: \n', reliefF_features)
  return reliefF_features

def get_features_chi2(data, target, number_of_features):
  features_norm = MinMaxScaler().fit_transform(data)
  chi_selector = SelectKBest(chi2, k=number_of_features)
  chi_selector.fit(features_norm, target)

  chi_support = chi_selector.get_support()
  chi_feature = data.loc[:,chi_support].columns.tolist()
  #print('Top-10 features: \n', chi_feature)
  return chi_feature

def get_features_rfe(data, target, number_of_features):
  features_norm = MinMaxScaler().fit_transform(data)
  rfe_selector = RFE(estimator=LogisticRegression(), n_features_to_select=number_of_features, step=10, verbose=5)
  rfe_selector.fit(features_norm, target)

  rfe_support = rfe_selector.get_support()
  rfe_features = data.loc[:,rfe_support].columns.tolist()
  #print('Top-10 features: \n', rfe_features)
  return rfe_features

def get_features_infoGain(data, target, number_of_features):
  # determine the mutual information
  mutual_info = mutual_info_classif(data, target)

  mutual_info = pd.Series(mutual_info)
  mutual_info.index = data.columns
  mutual_info.sort_values(ascending=False)

  # Select the  top 10 important features
  sel_ten_cols = SelectKBest(mutual_info_classif, k=number_of_features)
  sel_ten_cols.fit(data, target)
  infoGain_features = data.columns[sel_ten_cols.get_support()].to_list()
  #print('Top-10 features: \n', infoGain_features)
  return infoGain_features

def get_features_dt(data, target, number_of_features):
  # Initialize the DecisionTreeClassifier
  clf = DecisionTreeClassifier()

  # Scale data
  scaler = StandardScaler().fit(data)
  data_scaled = scaler.transform(data)
  # Fit the classifier on the data
  clf.fit(data_scaled, target)

  # Get the feature importances
  feature_importances = clf.feature_importances_

  # Sort the feature importances and get the top 10 features
  top_10_features = pd.DataFrame(feature_importances, index=data.columns, columns=['Importance']).sort_values(by='Importance', ascending=False).head(number_of_features)

  # Return the names of the top 10 features
  dt_features = top_10_features.index.to_list()
  return dt_features

def get_features_wrapper(classifier, number_of_features):
  # Initialize an empty set to hold the selected features
  selected_features = set()

  # Repeat the following steps until ten features have been selected
  while len(selected_features) < number_of_features:
      best_accuracy = 0
      best_feature = None

      # Iterate over all features that have not been selected yet
      for feature in X_train.columns:
          if feature not in selected_features:
              # Train the classifier using the selected features plus the current feature
              classifier.fit(X_train[list(selected_features) + [feature]], y_train)

              # Make predictions on the test set
              y_pred = classifier.predict(X_test[list(selected_features) + [feature]])

              # Calculate the accuracy
              accuracy = accuracy_score(y_test, y_pred)

              # Check if this feature leads to the best accuracy so far
              if accuracy > best_accuracy:
                  best_accuracy = accuracy
                  best_feature = feature

      # Add the best feature to the set of selected features
      selected_features.add(best_feature)

      # Print the best feature and its accuracy
      # print(f"Selected feature: {best_feature}, Accuracy: {best_accuracy:.2f}")
  #print(sorted(selected_features))
  return selected_features


def filter_selected_features(features):
  X_train_selected = X_train[features]
  X_test_selected = X_test[features]
  return X_train_selected, X_test_selected

"""# XAI Methods"""

def get_features_shapTree(classifier):
  explainer = shap.TreeExplainer(classifier)
  shap_values = explainer.shap_values(X_test)
  shap.summary_plot(shap_values, X_test)

def get_features_shapKernelExplainer(classifier):
  explainer = shap.KernelExplainer(classifier.predict_proba, X_train_scaled)
  shap_values = explainer.shap_values(X_test_scaled)
  shap.summary_plot(shap_values, X_test, plot_type="bar")

"""## Metrics"""

def get_percision_recall_scores(y_test, y_pred, algorithm_name):
    rs=recall_score(y_test, y_pred)
    ps=precision_score(y_test, y_pred)

    print("\n")
    print("Recall Score of ", algorithm_name, " : ",rs)
    print("Precision Score of ", algorithm_name, " : ",ps)
    print()

def plot_roc_curve(fpr, tpr):
    plt.figure(figsize=(5,5))
    plt.title('Receiver Operating Characteristic')
    plt.plot(fpr,tpr, color='red',label = roc_auc_score)
    plt.legend(loc = 'lower right')
    plt.plot([0, 1], [0, 1],linestyle='--')
    plt.axis('tight')
    plt.ylabel('True Positive Rate')
    plt.xlabel('False Positive Rate')

def conf_mtrx(y_test, y_pred, model):

    cm = confusion_matrix(y_test,y_pred)

    f, ax = plt.subplots(figsize =(5,5))
    cm = confusion_matrix(y_test,y_pred)

    sns.heatmap(cm,annot = True, linewidths=0.5, linecolor="red",fmt = ".0f",ax=ax)
    plt.xlabel("predicted y values")
    plt.ylabel("real y values")
    plt.title("\nConfusion Matrix")
    plt.show()

# Function for machine learning algorithms

def ML_Algorithms(X_train, X_test, y_train, y_test, alg_name, model ,value):

    model.fit(X_train,y_train)

    y_pred = model.predict(X_test)


    conf_mtrx(y_test, y_pred, model)
    print(" ")
    print("*****",alg_name," ALGORITHM:")

    print("Score for ", alg_name," train set:"  ,  model.score(X_train,y_train))
    print("Score for ", alg_name, " test set: ", model.score(X_test,y_test))
    print(" ")

    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy: %.2f%%" % (accuracy * 100.0))
    print(" ")

    print(" ")
    print("F1-score: ", f1_score(y_test, y_pred, average='weighted'))
    print(" ")

    if(value==1):
        get_percision_recall_scores(y_test, y_pred, alg_name)

        tn, fp, fn, tp = confusion_matrix([0, 1, 0, 1], [1, 1, 1, 0]).ravel()
        y_prob = model.predict_proba(X_test)[:,1] # This will give you positive class prediction probabilities
        y_pred = np.where(y_prob > 0.5, 1, 0) # This will threshold the probabilities to give class predictions.

        fpr, tpr, thresholds = roc_curve(y_test, y_prob)

        probs = model.predict_proba(X_test)
        probs = probs[:, 1]

        auc = roc_auc_score(y_test, probs)
        print('AUC: %.2f' % auc)

        auc = roc_auc_score(y_test, probs)
        print('AUC: %.2f' % auc)
        plot_roc_curve(fpr, tpr)

    return model

"""# DATASET"""

data = pd.read_csv('drive/MyDrive/TEZ/autism-code/DuyguDurumları_veriseti/1_MutluDataSET.csv')
data.head(5) # To display the top 5 rows

data = data.drop(['Participant'], axis=1) # remove participant column

# label_encoder object knows how to understand word labels.
label_encoder = preprocessing.LabelEncoder()

# Encode labels in column 'Class'. OSB is 1, NG is 0
data['Class']= label_encoder.fit_transform(data['Class'])

data['Class'].unique()

y = data.pop('Class')

features_list = list(data.columns)
len(features_list)

"""# SPLIT DATA"""

X_train, X_test, y_train, y_test = train_test_split(data, y, test_size=0.2, random_state=33)

print("Training records: {}".format(X_train.shape[0]))
print("Testing records: {}".format(X_test.shape[0]))

scaler = StandardScaler().fit(X_train)
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)

"""# Feature Selection:

Trying different approaches:

- ReliefF
- Chi-2;
- RFE;
- Information Gain;
- Decision Tree;
- Wrapper;
  - Decision Tree
  - Gaussion NB
  - k-NN

## ReliefF
"""

reliefF_features = get_features_reliefF(data, y, 20)

"""## Chi-squared"""

chi_feature = get_features_chi2(data, y, 20)

"""## Recursive Feature Removal"""

rfe_features = get_features_rfe(data, y, 20)

"""## Information Gain"""

infoGain_features = get_features_infoGain(data, y, 20)

"""## Decision Tree"""

dt_features = get_features_dt(data, y, 20)

"""## Wrapper
- Decision Tree
- Gaussian NB
- k-NN
"""

wrapper_dt_features = get_features_wrapper(DecisionTreeClassifier(criterion='entropy'), 20)
wrapper_NB_features = get_features_wrapper(GaussianNB(), 20)
wrapper_knn_features = get_features_wrapper(KNeighborsClassifier(n_neighbors=5), 20)

print("Selected features from chi:         ", sorted(chi_feature))
print("Selected features from rfe:         ", sorted(rfe_features))
print("Selected features from reliefF:     ", sorted(reliefF_features))
print("Selected features from infoGain:    ", sorted(infoGain_features))
print("Selected features from dt:          ", sorted(dt_features))
print("Selected features from wrapper DT:  ", sorted(wrapper_dt_features))
print("Selected features from wrapper NB:  ", sorted(wrapper_NB_features))
print("Selected features from wrapper knn: ", sorted(wrapper_knn_features))

"""## SELECT THE FEATURE SELECTION METHOD FOR THE MODELS

"""

# X_train_selected, X_test_selected = filter_selected_features(chi_feature)
# X_train_selected, X_test_selected = filter_selected_features(rfe_features)
# X_train_selected, X_test_selected = filter_selected_features(reliefF_features)
# X_train_selected, X_test_selected = filter_selected_features(infoGain_features)
# X_train_selected, X_test_selected = filter_selected_features(dt_features)
# X_train_selected, X_test_selected = filter_selected_features(wrapper_dt_features)
# X_train_selected, X_test_selected = filter_selected_features(wrapper_NB_features)
# X_train_selected, X_test_selected = filter_selected_features(wrapper_knn_features)

# common_features = [
# 'DA 7',
# 'DA 8',
# 'DA 10',
# 'DA 11',
# 'M Y1',
# 'M Y2',
# 'M Y6',
# 'M Y7',
# 'M Y8',
# 'M Y9',
# 'M Y11',
# 'M B6',
# 'M B7',
# 'X_Y5',
# 'X_Y6',
# 'N7']
# X_train_selected, X_test_selected = filter_selected_features(common_features)

# scaler = StandardScaler().fit(X_train_selected)
# X_train_scaled = scaler.transform(X_train_selected)
# X_test_scaled = scaler.transform(X_test_selected)

"""# ML MODELS

## DECISION TREE
"""

classifier_dt = ML_Algorithms(X_train_scaled, X_test_scaled, y_train, y_test, "DECISION TREE CLASSIFIER",
              DecisionTreeClassifier(criterion='gini', max_depth=5, min_samples_split=7, min_samples_leaf=10, random_state=42), 1)

"""## RANDOM FOREST"""

classifier_rf = ML_Algorithms(X_train_scaled, X_test_scaled, y_train, y_test, "RANDOM FOREST CLASSIFIER",
              RandomForestClassifier(criterion='entropy', max_depth=5, min_samples_split=10, min_samples_leaf=5, random_state=42),1)

"""## LOGISTIC REGRESSION"""

classifier_lr = ML_Algorithms(X_train_scaled, X_test_scaled, y_train, y_test, "LOGISTIC REGRESSION",
              LogisticRegression(C=100.0, penalty='l2', solver='liblinear'),1)

"""## NAIVE BAYES"""

classifier_bNB = ML_Algorithms(X_train_scaled, X_test_scaled, y_train, y_test, "Bernoulli NB",
              BernoulliNB(alpha=0.0001, binarize=0.9),1)

classifier_gNB = ML_Algorithms(X_train_scaled, X_test_scaled, y_train, y_test, "GAUSSIAN NB",
              GaussianNB(),1)

"""## KNN"""

# knn hyperparameter tuning / determine k

k_range = list(range(1,15))
scores = []
for k in k_range:
    knn = KNeighborsClassifier(n_neighbors=k)
    knn.fit(X_train_scaled, y_train)
    y_pred = knn.predict(X_test_scaled)
    scores.append(accuracy_score(y_test, y_pred))

plt.plot(k_range, scores)
plt.xlabel('Value of k for KNN')
plt.ylabel('Accuracy Score')
plt.title('Accuracy Scores for Values of k of k-Nearest-Neighbors')
plt.show()

classifier_knn = ML_Algorithms(X_train_scaled, X_test_scaled, y_train, y_test, "K-NEIGHBORS CLASSIFIER",
              KNeighborsClassifier(n_neighbors=8),1)

"""## Gradient Boosting"""

classifier_gb = ML_Algorithms(X_train_scaled, X_test_scaled, y_train, y_test, "Gradient Boosting Classifier",
              GradientBoostingClassifier(n_estimators=15, learning_rate=0.4, max_features=20, max_depth=12, random_state=0),1)

"""## Neural Networks: MLP Classifier"""

classifier_mlp = ML_Algorithms(X_train_scaled, X_test_scaled, y_train, y_test, "NN - MLPCLASSIFIER",
              MLPClassifier(hidden_layer_sizes=(1000, ),alpha=0.001,  learning_rate_init=0.001, power_t=0.9, max_iter=50),1)

"""# XAI METHODS"""

get_features_shapTree(classifier_rf)

get_features_shapTree(classifier_dt)

get_features_shapTree(classifier_gb)

get_features_shapKernelExplainer(classifier_knn)

get_features_shapKernelExplainer(classifier_gNB)

get_features_shapKernelExplainer(classifier_bNB)

get_features_shapKernelExplainer(classifier_lr)

get_features_shapKernelExplainer(classifier_mlp)

