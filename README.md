# gBLP - Bloomberg V3 API gRPC Server

![background](images/finvids.gif#gh-dark-mode-only)
![background](images/finvids.gif#gh-light-mode-only)


$$\textcolor{JungleGreen}{\rule{120cm}{0.5mm}}$$
### Legal Notice
This software is provided "as is," without warranty of any kind, express or implied. The developer of this software assumes no responsibility or liability for any use of the software by any party. It is the sole responsibility of the user to ensure that their use of this software complies with all applicable laws, regulations, and the terms and conditions of the Bloomberg API. By using this software, you acknowledge and agree that the developer shall not be held liable for any consequences arising from the use of this software, including but not limited to, any violations of the Bloomberg API terms.

$$\textcolor{JungleGreen}{\rule{120cm}{0.5mm}}$$


## Why?
* Streaming: a fully featured subscription API in your python or Jupyter repl, that updates in real time.
* Multi-language: gRPC allows you to use the same API in any language that supports it. 
* Multi-OS: No more Windows-only (see licence below). 


## Status
Beta as of 24 Nov 2024. 
* `historicalDataRequest` is working (daily data).
* `intradayBarRequest` is working (minute or greater bars).
* `referenceDataRequest` is working.
* `sub` / `unsub` are working.
* full status message support.
* For now python client only in this repo. More soon. 
* Beta testers welcome (you'll need a Bloomberg terminal).

## Installation
`pip install gBLP --extra-index-url https://blpapi.bloomberg.com/repository/releases/python/simple/`  
Generate security certificates with the following command.   
`server_gblp --gencerts --grpchost <server_ip_or_hostname>`  
Here `localhost` is fine if you're staying on Windows on the same VM or machine, but otherwise you should use an IP address that is reachable from your client.  
Later you can `server_gblp --delcerts` to remove the certificates, or `--gencerts` to regenerate them.  
Done. You can now run the server and client.  

## Usage
#### Server. 
In a Windows cmd or powershell terminal run  
`server_gblp --grpchost <server_ip_or_hostname>`  
where `<server_ip_or_hostname>` is what you specified when generating the certificates on a machine with a Bloomberg Terminal.

#### Client
From a python REPL or script, on Windows, on WSL, or in a Linux VM, run the following code. This will not work if `<server_ip_or_hostname>` is not reachable from your client. Use `ping <server_ip_or_hostname>` from the client to check.
```
from gBLP.client_glp import Bbg
bbg = Bbg(grpc_host="<server_ip_or_hostname>")
test_hist = bbg.historicalDataRequest(["AAPL US Equity", "USDZAR Curncy"], ["PX_BID", "PX_ASK"])
```
Note that the client is threaded and will continue to allow you to use python/IPython while it runs. 
When you're done, `bbg.close()` will close the connection and clean up server side. Once closed, you cannot use the client again without reinstating it. 

#### Client Methods
* `historicalDataRequest`
* `intradayBarRequest`
* `referenceDataRequest`
* `sub`
* `unsub`
* `subscriptionsInfo`
Note that `sub` is a _live_ subscription. `bbg.sub(["XBTUSD Curncy"])` will populate the `bbg.subsdata` decque continuously.  
You may specify your own handler. See the examples. 

## Licence
#### Bloomberg
Please see the [licence](https://github.com/vegabook/gBLP/blob/main/src/bbg_copyright.txt) for the Bloomberg API code contained in this package. 
#### gBLP
GNU General Public License v3.0 [🔗](https://www.gnu.org/licenses/gpl-3.0.en.html) [full text](https://www.gnu.org/licenses/gpl-3.0.html).

 

