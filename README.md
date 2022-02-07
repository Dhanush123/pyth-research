# solana-research
The purpose of this research is to compare Pyth vs Chainlink price feed updates on Solana.

Usage steps:
1. `pip install -r requirements.txt` The pyth library requires 3.7 or later. I personally used 3.8.0.
2.1 To get Pyth data, run `python pyth.py`. There's an optional first parameter of `main` or `dev` (defaults to `dev`) to specify network and optional second parameter of time in minutes such as `20` (defaults to `10`). For example, `python pyth.py dev 20`.
2.2 To get Chainlink data, run `python chainlink.py`. Just like `pyth.py`, there's an optional first time parameter, so something like `python chainlink.py 20` is also valid. As Chainlink is only available on devnet on Solana, there's no network parameter.

Notes:
* `pyth.py` will generate a CSV with Price, Confidence Interval, and Timestamp data
* `chainlink.py` will generate Timestamp data

The devnet data gathered from the two Python files was used in this [Google Colab analysis](https://colab.research.google.com/drive/1-xB7xCSp1oPpb2LlNAX5-7LpBe2VA5uY?usp=sharing)
