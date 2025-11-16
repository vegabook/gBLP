import pytest
from gBLP.client_gblp import Bbg 
import datetime as dt

global bbg
bbg = None

def test_Bbg():
    global bbg
    bbg = Bbg()
    assert bbg is not None

def test_historicalData():
    startDate = dt.date.today() - dt.timedelta(days=365)
    endDate = dt.date.today()
    data = bbg.historicalDataRequest(["AAPL US Equity", "AMD US Equity"], 
                                     ["PX_LAST", "PX_BID"], 
                                     start = startDate, end = endDate)
    breakpoint()



