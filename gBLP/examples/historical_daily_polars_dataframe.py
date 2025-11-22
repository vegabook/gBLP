# Example historical daily data into a polars dataframe.
# This code must be run from the "examples" directory

from google.protobuf.json_format import MessageToDict # for parsing grpc responses
import polars as pl
import json
import sys
from pathlib import Path
import datetime as dt
import IPython
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from client_gblp import Bbg

if __name__ == "__main__":
    bbg = Bbg(grpchost = "signaliser.com")
    with open("tickers/crypto.json") as jf:
        cryptos = json.load(jf)["crypto"]

    cc = bbg.historicalDataRequest(cryptos, 
                                   ["last_price"], 
                                   start = dt.datetime.now() - dt.timedelta(days = 365 * 2), 
                                   end = dt.datetime.now())
    ccd = MessageToDict(cc)

    cce = [x for x in ccd["securityData"] if x.get("timeData")]

    df = pl.concat([pl.DataFrame({"date": [x["fields"]["date"]["timevalue"] for x in y["timeData"]], 
                                  "price": [x["fields"]["last_price"]["doublevalue"] for x in y["timeData"]], 
                                  "crypto": [y["security"].split(" ")[0] for x in y["timeData"]]}) 
        for y in cce]).pivot("crypto", index = "date")\
        .sort("date")
    print(df)
    IPython.embed()
    bbg.close()


