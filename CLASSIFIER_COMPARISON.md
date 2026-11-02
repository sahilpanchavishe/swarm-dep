# Classifier comparison (accuracy is not safety)

Protocol: leave-ONE-PARTICIPANT-out (no leakage). Key metric: STOP misread rate (drives the
dependability result), alongside overall hold accuracy. Reproduce: compare_classifiers_ext.py,
train_gru.py (GRU/LSTM/BiGRU/BiLSTM), train_advanced.py (1D-CNN/ST-GCN).
Numbers: data/classifier_comparison_full.csv.

## Headline
A transparent rule-based classifier misreads the safety-critical STOP gesture 1.6% of the time.
Every LEARNED model tested - KNN, SVM, RandomForest, XGBoost, MLP, whole-gesture SVM/XGBoost,
GRU, LSTM, BiGRU, BiLSTM, 1D-CNN - reaches higher OVERALL accuracy (up to 95%) yet misreads STOP
5-13x more often (7.4%-20.8%). Higher recognition accuracy did NOT buy STOP safety.

Cause: STOP (open palm) vs CLUSTER (OK-sign) is a pose-SHAPE ambiguity in the landmarks. Temporal
and bidirectional sequence modelling cannot resolve a confusion that is not temporal.

## Honest caveats (state these in the paper)
- Per-fold STOP counts are small (~19/fold); STOP misread ranges 0-42% across participants. The
  aggregate ordering is robust; exact percentages are noisy -> motivates the dedicated STOP dataset.
- 1D-CNN is the best learned model (95% acc, 7.4% STOP) but still ~5x the rule on STOP.
- ST-GCN reached only 56% overall accuracy: a high-capacity skeleton graph network OVERFITS ~1088
  holds. Its STOP number is NOT evidence about the architecture - it is evidence that heavy skeleton
  models (ST-GCN, ProtoGCN, etc.) are inappropriate at this dataset size. One-line cautionary note only.

## Paper claim (defensible)
"Across learned models from KNN to bidirectional RNNs to a 1D-CNN, higher overall recognition
accuracy never closed the STOP-safety gap; the best learned model remained ~5x worse than a
transparent rule, and high-capacity skeleton graph networks overfit the available data. This
motivates treating the safety-critical STOP command as a distinct, explainable decision rather than
one class in an accuracy-optimised recogniser."
