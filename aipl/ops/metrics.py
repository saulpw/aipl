from aipl.table import Table
from aipl import defop, LazyRow
import numpy as np

def _is_int(val):
    try:
        int(val)
        return True
    except ValueError:
        return False

def _to_np_int_array(t:Table, colname:str) -> np.array:
    column = [int(row[colname]) if _is_int(row[colname]) else np.nan for row in t]
    return np.array(column)

def _true_positives(predictions:np.array, true_values:np.array) -> float:
    return ((predictions == 1) & (true_values == 1)).sum()

def _true_negatives(predictions:np.array, true_values:np.array) -> float:
    return ((predictions == 0) & (true_values == 0)).sum()

def _false_positives(predictions:np.array, true_values:np.array) -> float:
    return ((predictions == 1) & (true_values == 0)).sum()

def _false_negatives(predictions:np.array, true_values:np.array) -> float:
    return ((predictions == 0) & (true_values == 1)).sum()

def _recall(predictions:np.array, true_values:np.array) -> float:
    N = true_values.shape[0]
    return (true_values == predictions).sum() / N

def _precision(predictions:np.array, true_values:np.array) -> float:
    TP = _true_positives(predictions, true_values)
    FP = _false_positives(predictions, true_values)
    return TP / (TP+FP)

def _balanced_accuracy(predictions:np.array, true_values:np.array, add_one_smoothing:bool) -> float:
    TP = _true_positives(predictions, true_values)
    TN = _true_negatives(predictions, true_values)
    FP = _false_positives(predictions, true_values)
    FN = _false_negatives(predictions, true_values)
    if add_one_smoothing:
        true_positive_rate = (TP + 1) / (TP + FN + 1)
        true_negative_rate = (TN + 1) / (TN + FP + 1)
    else:
        true_positive_rate = TP / (TP + FN)
        true_negative_rate = TN / (TN + FP)
    return (true_positive_rate + true_negative_rate) / 2

@defop('metrics-accuracy', 1.5, 0)
def op_accuracy(aipl, t:Table, predictions_colname:str, true_values_colname:str, add_one_smoothing:bool=None) -> float:
    true_values = _to_np_int_array(t, true_values_colname)
    predictions = _to_np_int_array(t, predictions_colname)
    return _balanced_accuracy(predictions, true_values, add_one_smoothing=='True')

@defop('metrics-precision', 1.5, 0)
def op_precision(aipl, t:Table, predictions_colname:str, true_values_colname:str, add_one_smoothing:bool=None) -> float:
    true_values = _to_np_int_array(t, true_values_colname)
    predictions = _to_np_int_array(t, predictions_colname)
    return _precision(predictions, true_values)

@defop('metrics-recall', 1.5, 0)
def op_precision(aipl, t:Table, predictions_colname:str, true_values_colname:str, add_one_smoothing:bool=None) -> float:
    true_values = _to_np_int_array(t, true_values_colname)
    predictions = _to_np_int_array(t, predictions_colname)
    return _recall(predictions, true_values)