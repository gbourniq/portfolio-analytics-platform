from portfolio_analytics.common.utils.instruments import Currency, StockIndex

def test_currency_enum():
    assert Currency.USD.value == "USD"
    assert Currency.EUR.value == "EUR"
    assert Currency.GBP.value == "GBP"

    # Test all expected currencies exist
    expected_currencies = {"USD", "EUR", "GBP"}
    assert {c.value for c in Currency} == expected_currencies

def test_stock_index_enum():
    assert StockIndex.SP500.value == "SP500"
    assert StockIndex.FTSE100.value == "FTSE100"
    assert StockIndex.EUROSTOXX50.value == "EUROSTOXX50"

    # Test all expected indices exist
    expected_indices = {"SP500", "FTSE100", "EUROSTOXX50"}
    assert {idx.value for idx in StockIndex} == expected_indices
