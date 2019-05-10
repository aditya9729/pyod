# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function

import os
import sys

import unittest
# noinspection PyProtectedMember
from sklearn.utils.testing import assert_allclose
from sklearn.utils.testing import assert_array_less
from sklearn.utils.testing import assert_equal
from sklearn.utils.testing import assert_greater
from sklearn.utils.testing import assert_greater_equal
from sklearn.utils.testing import assert_less_equal
from sklearn.utils.testing import assert_raises
from sklearn.utils.testing import assert_true
from sklearn.utils.estimator_checks import check_estimator

from sklearn.metrics import roc_auc_score
from scipy.stats import rankdata

# temporary solution for relative imports in case pyod is not installed
# if pyod is installed, no need to use the following line
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyod.models.hbos import HBOS
from pyod.utils.data import generate_data


class TestHBOS(unittest.TestCase):
    def setUp(self):
        self.n_train = 200
        self.n_test = 100
        self.contamination = 0.1
        self.roc_floor = 0.8
        self.X_train, self.y_train, self.X_test, self.y_test = generate_data(
            n_train=self.n_train, n_test=self.n_test,
            contamination=self.contamination, random_state=42)

        self.clf = HBOS(contamination=self.contamination)
        self.clf.fit(self.X_train)

    def test_sklearn_estimator(self):
        check_estimator(self.clf)

    def test_parameters(self):
        assert_true(hasattr(self.clf, 'decision_scores_') and
                    self.clf.decision_scores_ is not None)
        assert_true(hasattr(self.clf, 'labels_') and
                    self.clf.labels_ is not None)
        assert_true(hasattr(self.clf, 'threshold_') and
                    self.clf.threshold_ is not None)
        assert_true(hasattr(self.clf, '_mu') and
                    self.clf._mu is not None)
        assert_true(hasattr(self.clf, '_sigma') and
                    self.clf._sigma is not None)
        assert_true(hasattr(self.clf, 'hist_') and
                    self.clf.hist_ is not None)
        assert_true(hasattr(self.clf, 'bin_edges_') and
                    self.clf.bin_edges_ is not None)

    def test_train_scores(self):
        assert_equal(len(self.clf.decision_scores_), self.X_train.shape[0])

    def test_prediction_scores(self):
        pred_scores = self.clf.decision_function(self.X_test)

        # check score shapes
        assert_equal(pred_scores.shape[0], self.X_test.shape[0])

        # check performance
        assert_greater(roc_auc_score(self.y_test, pred_scores), self.roc_floor)

    def test_prediction_labels(self):
        pred_labels = self.clf.predict(self.X_test)
        assert_equal(pred_labels.shape, self.y_test.shape)

    def test_prediction_proba(self):
        pred_proba = self.clf.predict_proba(self.X_test)
        assert_greater_equal(pred_proba.min(), 0)
        assert_less_equal(pred_proba.max(), 1)

    def test_prediction_proba_linear(self):
        pred_proba = self.clf.predict_proba(self.X_test, method='linear')
        assert_greater_equal(pred_proba.min(), 0)
        assert_less_equal(pred_proba.max(), 1)

    def test_prediction_proba_unify(self):
        pred_proba = self.clf.predict_proba(self.X_test, method='unify')
        assert_greater_equal(pred_proba.min(), 0)
        assert_less_equal(pred_proba.max(), 1)

    def test_prediction_proba_parameter(self):
        with assert_raises(ValueError):
            self.clf.predict_proba(self.X_test, method='something')

    def test_fit_predict(self):
        pred_labels = self.clf.fit_predict(self.X_train)
        assert_equal(pred_labels.shape, self.y_train.shape)

    def test_fit_predict_score(self):
        self.clf.fit_predict_score(self.X_test, self.y_test)
        self.clf.fit_predict_score(self.X_test, self.y_test,
                                   scoring='roc_auc_score')
        self.clf.fit_predict_score(self.X_test, self.y_test,
                                   scoring='prc_n_score')
        with assert_raises(NotImplementedError):
            self.clf.fit_predict_score(self.X_test, self.y_test,
                                       scoring='something')

    # def test_score(self):
    #     self.clf.score(self.X_test, self.y_test)
    #     self.clf.score(self.X_test, self.y_test, scoring='roc_auc_score')
    #     self.clf.score(self.X_test, self.y_test, scoring='prc_n_score')
    #     with assert_raises(NotImplementedError):
    #         self.clf.score(self.X_test, self.y_test, scoring='something')

    def test_predict_rank(self):
        pred_socres = self.clf.decision_function(self.X_test)
        pred_ranks = self.clf._predict_rank(self.X_test)

        # assert the order is reserved
        assert_allclose(rankdata(pred_ranks), rankdata(pred_socres), atol=2)
        assert_array_less(pred_ranks, self.X_train.shape[0] + 1)
        assert_array_less(-0.1, pred_ranks)

    def test_predict_rank_normalized(self):
        pred_socres = self.clf.decision_function(self.X_test)
        pred_ranks = self.clf._predict_rank(self.X_test, normalized=True)

        # assert the order is reserved
        assert_allclose(rankdata(pred_ranks), rankdata(pred_socres), atol=2)
        assert_array_less(pred_ranks, 1.01)
        assert_array_less(-0.1, pred_ranks)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
