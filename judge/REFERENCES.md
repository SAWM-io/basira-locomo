# Official judge prompts

The prompts of the two judges are not copied here: they are read from their authors' repositories, at pinned
versions, and verified by SHA-256 checksum.

| Judge | Official file | Pinned version | SHA-256 | License |
|---|---|---|---|---|
| J (main, `gpt-4o-mini-2024-07-18`, temperature 0) | [Mem0's `evaluation/metrics/llm_judge.py`](https://github.com/mem0ai/mem0/blob/393a4fd5a6cfeb754857a2229726f567a9fadf36/evaluation/metrics/llm_judge.py) | commit `393a4fd5a6cfeb754857a2229726f567a9fadf36` | `311050fd39e991220e220b5e4b753725c3e7616d8cef84e8c737eb902fc13af8` | Apache-2.0 |
| Strict (`gpt-4o-2024-08-06`, temperature 0) | [LongMemEval's `src/evaluation/evaluate_qa.py`](https://github.com/xiaowu0162/LongMemEval/blob/d6dc8b50a2d9ac0c99485ea28fa5755c62414c34/src/evaluation/evaluate_qa.py) | commit `d6dc8b50a2d9ac0c99485ea28fa5755c62414c34` | `ecce9c4c79dc89d99534ac17b383a5cbb5b9f0c69ee98adaf0684742e3d95251` | MIT |
| Abstention, category 5 (`gpt-4o-2024-08-06`) | the `abstention` mode of the same `evaluate_qa.py` | same | same | MIT |

The J judge uses Mem0's `ACCURACY_PROMPT` prompt (answer graded CORRECT or WRONG against the reference answer).
The strict judge uses LongMemEval's prompt ("temporal reasoning" template for category 2, "information provided by
the user" template for the others). Each judge sees only the question, the reference answer and the reader's final
answer, never the reasoning.

To re-judge: download these files from their authors, check the checksums above, and apply them to the answers in
`answers/` together with the LoCoMo dataset (question and reference answer, to be downloaded from Snap Research).
