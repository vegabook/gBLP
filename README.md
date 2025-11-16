# gBLP - Bloomberg V3 API gRPC Server

![background](images/finvids.gif#gh-dark-mode-only)
![background](images/finvids.gif#gh-light-mode-only)


$$\textcolor{JungleGreen}{\rule{120cm}{0.5mm}}$$
### Legal Notice
This software is provided "as is," without warranty of any kind, express or implied. The developer of this software assumes no responsibility or liability for any use of the software by any party. It is the sole responsibility of the user to ensure that their use of this software complies with all applicable laws, regulations, and the terms and conditions of the Bloomberg API. By using this software, you acknowledge and agree that the developer shall not be held liable for any consequences arising from the use of this software, including but not limited to, any violations of the Bloomberg API terms.

$$\textcolor{JungleGreen}{\rule{120cm}{0.5mm}}$$

## What?
A gRPC server that wraps the Bloomberg V3 API. 


## Why?
* Finally you're not limited to Windows and Python for developing using the Bloomberg API.  Even Terminal users can [WS]Linux (or VM) and use any programming language they want that supports Google's excellent gRPC library.  
* Streaming: a fully featured subscription API that operates in a separate thread in python, and uses idiomatic gRPC streams in other programming languages. 
* Most used historical data functions are implemented. 
* Multi-language: gRPC allows you to use the same API in any language that supports it. 
* Blpapi on Linux, MacOS, or Windows (see the licence).
* Robust threaded server implementation that isolates the (sometimes fragile and noisy neighbour) Bloomberg API runtime in its own process.  

## Clients
* Python: an example python workflow is shown in `client_gblp.py` (see below)  
* Elixir: see https://github.com/vegabook/blxx  
* Proto files are provided which you can use to make gRPC stubs for any other programming language. See directory `protos`.      

## What's working
* Subscription subsystem. Unlike most api libraries, this one supports live data. 
* HistoricalDataRequest. Daily or longer periodicity data. 
* IntradayBarRequest. Minute or greater bars.
* ReferenceDataRequest. Information on any security. 

## Not yet
This functionality is deemed of secondary importance and is not yet implemented. 
* IntradayTickRequest
* instrumentListRequest
* curveListRequest
* govtListRequest
* FieldListRequest
* FieldSearchRequest
* FieldInfoRequest

## Installation of Python server (Windows)
install [uv](https://docs.astral.sh/uv/getting-started/installation/)  
`git clone https://github.com/vegabook/gBLP`  
`cd gBLP\gBLP`  
Generate security certificates with the following command.   
`uv run server_gblp --gencerts --grpchost <server_ip_or_hostname>`  
Here `localhost` is fine if you're staying on Windows on the same VM or machine, but otherwise you should use an IP address that is reachable from your client.  Please note that going "off machine" in a hardware sense requires a B-PIPE licence. 
Later you can `server_gblp --delcerts` to remove the certificates, or `--gencerts` to regenerate them.  

## Installation of Python client on Win/MacOs/Linux
`git clone https://github.com/vegabook/gBLP`
install [uv](https://docs.astral.sh/uv/getting-started/installation/)  

## Usage
#### Server (Windows)
Make sure your Bloomberg Terminal is running, and logged in.  
`cd gBLP/gBLP`
`uv run server_gblp --grpchost <server_ip_or_hostname>`  
where `<server_ip_or_hostname>` is what you specified when generating the certificates on a machine with a Bloomberg Terminal.

#### Python client
Make sure the server is up and running, that you have a reachable IP or hostname, and that you have done the `--gencerts` on the server.  
An example python client is provided in `client_gBLP.py` but this is not packaged, so you will have to modify it yourself if you want to use it in your apps, although this client does drop you into iPython so it should be easy to convert to notebooks etc.  Or you can use the class workflow. 
```
cd gBLP\gBLP
uv run client_gBLP.py --grpchost <server_ip_or_hostname>
```
This will download some historical data for you and start a few subscriptions which you can query using `blp.subsdata` decque.  

This project uses ssl-protected gRPC. The first time you run the client, it will not find certificates. Instead it will prompt you input a word (any word). The server will repeat that word to you and you have 10 seconds to type `Yes` (case sensitive) so that it will send certs to your client, which will save them. If you don't recgonise the word, or don't want to authorise the client, wait the 10 seconds or type anything other than `Yes`. Once you are certified then you are free to start using the client. 
  
Alternatively you can import the `Bbg` class, after ensuring file `client_gblp` is in scope.   
`from client_gblp import Bbg`  
`bbg = Bbg("<server_ip_or_hostname>")`  
`bbg.historicalDataRequest(["USDZAR Curncy", "SPX Index"], ["LAST_PRICE"])`  
`bbg.intradayBarRequest("GBPUSD Curncy", start = dt.datetime.now() - dt.timedelta(days = 90), end = dt.datetime.now(), interval = 1)`. Also takes an `options` parameter which is a dictionary. see the bloomberg api [docs](https://data.bloomberglp.com/professional/sites/10/2017/03/BLPAPI-Core-Developer-Guide.pdf)  
`bbg.referenceDataRequest(["SPX Index", "CAC Index"], ["CUR_MKT_CAP", "INDX_MEMBERS"])`  
subscribe using `bbg.sub(["EURUSD Curncy", "XBTUSD Curncy"])` which will run a background subscription process. You can query the data decque through `bbg.subsdata`.  

Note that the client is threaded and will continue to allow you to use python/IPython while it runs. 
When you're done, `bbg.close()` will close the connection and clean up server side. Once closed, you cannot use the client again without reinstating it. 

#### Python Client Methods
All in class `Bbg`:  
* `historicalDataRequest`
* `intradayBarRequest`
* `referenceDataRequest`
* `sub`
* `unsub`
* `subscriptionsInfo`
  
## Licence
#### Bloomberg
Please see the [licence](https://github.com/vegabook/gBLP/blob/main/src/bbg_copyright.txt) for the Bloomberg API code contained in this package. 
#### gBLP
GNU General Public License v3.0 [🔗](https://www.gnu.org/licenses/gpl-3.0.en.html) [full text](https://www.gnu.org/licenses/gpl-3.0.html).

 

