# Consignes officielles des juges

Les consignes des deux juges ne sont pas recopiées ici : elles sont lues chez leurs auteurs, à des versions figées,
et vérifiées par empreinte SHA-256.

| Juge | Fichier officiel | Version figée | SHA-256 | Licence |
|---|---|---|---|---|
| J (principal, `gpt-4o-mini-2024-07-18`, température 0) | [`evaluation/metrics/llm_judge.py` de Mem0](https://github.com/mem0ai/mem0/blob/393a4fd5a6cfeb754857a2229726f567a9fadf36/evaluation/metrics/llm_judge.py) | commit `393a4fd5a6cfeb754857a2229726f567a9fadf36` | `311050fd39e991220e220b5e4b753725c3e7616d8cef84e8c737eb902fc13af8` | Apache-2.0 |
| Strict (`gpt-4o-2024-08-06`, température 0) | [`src/evaluation/evaluate_qa.py` de LongMemEval](https://github.com/xiaowu0162/LongMemEval/blob/d6dc8b50a2d9ac0c99485ea28fa5755c62414c34/src/evaluation/evaluate_qa.py) | commit `d6dc8b50a2d9ac0c99485ea28fa5755c62414c34` | `ecce9c4c79dc89d99534ac17b383a5cbb5b9f0c69ee98adaf0684742e3d95251` | MIT |
| Abstention, catégorie 5 (`gpt-4o-2024-08-06`) | le mode `abstention` du même `evaluate_qa.py` | idem | idem | MIT |

Le juge J reprend la consigne `ACCURACY_PROMPT` de Mem0 (réponse jugée CORRECT ou WRONG au regard de la réponse de
référence). Le juge strict reprend la consigne de LongMemEval (gabarit « raisonnement temporel » pour la catégorie 2,
gabarit « information donnée par l'utilisateur » pour les autres). Chaque juge ne voit que la question, la réponse de
référence et la réponse finale du lecteur, jamais le raisonnement.

Pour rejuger : téléchargez ces fichiers chez leurs auteurs, vérifiez les empreintes ci-dessus, et appliquez-les aux
réponses de `reponses/` avec le jeu LoCoMo (question et réponse de référence, à télécharger chez Snap Research).
