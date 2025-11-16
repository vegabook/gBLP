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
* Streaming: a fully featured subscription API that operates in a separate thread, allowing REPL or Jupyter interactivity.
* Multi-language: gRPC allows you to use the same API in any language that supports it. 
* Blpapi on Linux, MacOS, or Windows (see the licence).
* Robust gRPC based API mapping with almost total coverage of the Bloomberg API. 

## Clients
* Python: an example python workflow is shown in `client_gblp.py` (see below)  
* Elixir: see https://github.com/vegabook/blxx  
* Proto files are provided which you can use to make gRPC stubs for any other programming language. See directory  protos    

## What's working
* Subscription subsystem. Unlike most api libraries, this one supports live data. 
* HistoricalDataRequest. Daily or longer periodicity data. 
* IntradayBarRequest. Minute or greater bars.
* ReferenceDataRequest. Information on any security. 

## Not yet
* IntradayTickRequest
* instrumentListRequest
* curveListRequest
* govtListRequest
* FieldListRequest
* FieldSearchRequest
* FieldInfoRequest

## Installation of Python server on Windows
install [uv](https://docs.astral.sh/uv/getting-started/installation/)  
`git clone https://github.com/vegabook/gBLP`
`cd gBLP\gBLP`  
Generate security certificates with the following command.   
`uv run server_gblp --gencerts --grpchost <server_ip_or_hostname>`  
Here `localhost` is fine if you're staying on Windows on the same VM or machine, but otherwise you should use an IP address that is reachable from your client.  
Later you can `server_gblp --delcerts` to remove the certificates, or `--gencerts` to regenerate them.  
Done. You can now run the server and client.  

## Installation of Python client on Win/MacOs/Linux
clone repo.   
install [uv](https://docs.astral.sh/uv/getting-started/installation/)  
`git clone https://github.com/vegabook/gBLP`
`cd gBLP/gBLP`  
`python -m pip install poetry` of if you're on nix, `nix develop`  
`poetry build`

## Usage
#### Server (Windows)
Make sure your Bloomberg Terminal is running, and logged in.  
`cd gBLP/gBLP`
`uv run server_gblp --grpchost <server_ip_or_hostname>`  
where `<server_ip_or_hostname>` is what you specified when generating the certificates on a machine with a Bloomberg Terminal.

#### Python client
An example python client is provided in `client_gBLP.py` but this is not packaged, so you will have to modify it yourself if you want to use it in your apps, although this client does drop you into iPython so it should be easy to convert to notebooks etc.   
```
cd gBLP\gBLP
uv run client_gBLP.py --grpchost <server_ip_or_hostname>
```
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
Note that `sub` is a _live_ subscription. `bbg.sub(["XBTUSD Curncy"])` will populate the `bbg.subsdata` decque continuously.  
You may specify your own handler. See the examples. 

## Licence
#### Bloomberg
Please see the [licence](https://github.com/vegabook/gBLP/blob/main/src/bbg_copyright.txt) for the Bloomberg API code contained in this package. 
#### gBLP
GNU General Public License v3.0 [🔗](https://www.gnu.org/licenses/gpl-3.0.en.html) [full text](https://www.gnu.org/licenses/gpl-3.0.html).

 

