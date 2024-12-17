# Hints

## General

* You can get market data using the Yfinance package https://pypi.org/project/yfinance/
* This useful gist gets all data for the S&P500 https://gist.github.com/quantra-go-algo/ac5180bf164a7894f70969fa563627b2
* Streamlit (https://streamlit.io/) and Dash (https://dash.plotly.com/) are popular frameworks for build data driven
  apps in Python
* Python code structure guidance can be found at https://docs.python-guide.org/writing/structure/
* There is some useful information about creating a tool
  at https://dataheadhunters.com/academy/how-to-create-a-stock-market-analysis-tool-in-python-for-finance/

## Portfolio Analysis

All examples use the [provided portfolio](input/portfolio.csv).

### Positions v. Trades

The values are the **end of day position** for the stocks, not the trades.

```
Date,AAPL
30/08/2024,0
03/09/2024,0
04/09/2024,13
05/09/2024,24
06/09/2024,0
```

So this means the trades were.

```
Date,AAPL
30/08/2024,0
03/09/2024,0
04/09/2024,+13
05/09/2024,+11
06/09/2024,-24
```

### Execution Price

Normally the execution price would be provided as part of the portfolio. For this example please use the Mid-price for
the day in question.

For AAPL the High, Low and calculated Mid-price would be.

```
Date		High		Low			Mid
2024-08-30	230.146792	227.230003	228.688398
2024-09-03	228.748326	220.926929	224.837628
2024-09-04	221.536270	217.240993	219.388632
2024-09-05	225.232189	221.276549	223.254369
2024-09-06	224.992472	219.528482	222.260477
```

Thus, the trades with execution price would be.

```
Date,AAPL
30/08/2024,0      @ 228.688398
03/09/2024,0      @ 224.837628
04/09/2024,+13    @ 219.388632
05/09/2024,+11    @ 223.254369
06/09/2024,-24    @ 222.260477
```

### Calculating P&L

As this a technical task rather than a quant/accounting task we will take a naive approach to calculating the P&L.

All you need to do is calculate the profit made from the hypothetical trades with the Mid-price.

For our example the total P&L would be \$26.41.

```
13 * $219.388632 = $2852.04
11 * $223.254369 = $2455.80
-24 * $222.260477 = -$5334.25

$2852.04 + $2455.80 + -$5334.25 = -$26.41
```

You need to flip the sign on the result to get the P&L or you could invert earlier to represent the cash flow in your
portfolio. You spend cash when buying a stock and gain cash when selling it.
