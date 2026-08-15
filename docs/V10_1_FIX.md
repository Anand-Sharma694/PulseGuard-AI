# v10.1 startup fix

The v10 package contained the same `/api/health` endpoint twice. Flask therefore
reported:

`AssertionError: View function mapping is overwriting an existing endpoint function: health`

v10.1 removes the duplicate endpoint. No database, AI, or frontend behavior
was intentionally changed.

The AI training output you obtained in v10 was already successful:
Accuracy 1.000, Precision 1.000, Recall 1.000, F1 1.000 on the synthetic
demonstration dataset.
