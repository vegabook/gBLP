# gBLP - Bloomberg V3 API gRPC Server

![background](images/finvids.gif#gh-dark-mode-only)
![background](images/finvids.gif#gh-light-mode-only)


$$\textcolor{JungleGreen}{\rule{120cm}{0.5mm}}$$
### Legal Notice
This software is provided "as is," without warranty of any kind, express or implied. The developer of this software assumes no responsibility or liability for any use of the software by any party. It is the sole responsibility of the user to ensure that their use of this software complies with all applicable laws, regulations, and the terms and conditions of the Bloomberg API. By using this software, you acknowledge and agree that the developer shall not be held liable for any consequences arising from the use of this software, including but not limited to, any violations of the Bloomberg API terms.

$$\textcolor{JungleGreen}{\rule{120cm}{0.5mm}}$$


## Why?
* You want to use the Bloomberg API from other languages than python, C++, C#, or Java. Now you can use it from any language that has a gRPC implementation.
* You want to have a proper, fully featured subscription API in your python or Jupyter repl, that updates in real time.


## Status
Graduating this project to beta 0.1.0 (16 November 2024)
* `historicalDataRequest` is working (daily data).
* `intradayBarRequest` is working (minute or greater bars).
* `subscribe` / `unsubscribe` is working via a threaded async class that does not take over your REPL.
* full status message support.
* For now python only. 
* Looking for beta testers. You'll need access to a Bloomberg Terminal.

## Installation

#### Server
1. In a Microsoft Windows shell, Clone this repo and `cd gRPC`. 
2. Ensure Python 3.10+ is installed and `pip install -r requirements.txt`.
3. In the `src` directory you will find `server_gblp.py` which is your server. 
4. You need the IP address of the machine running the Bloomberg Terminal. Get it with `ipconfig`.
5. First you must generate a CA authority and keys: `python server_gblp.py --grpchost <your_ip> --gencerts`
6. Then you can start the server: `python server_gblp.py --grpchost <your_ip> --grpcport 50051`

#### Client
An example Python client is provided which will say hello a few times and run a sample `historicalDataRequest`.
It is also located in the `src` directory. Now you can be on a mac, on Linux, WSL, wherever. Naturally, 
you will need access to the IP address of your server. 
1. In a shell on your client machine, clone this repo and `cd gRPC/src`. 
2. Ensure Python 3.10+ is installed and `pip install -r requirements.txt`.
3. Run the client: `python client_gblp.py --grpchost <your_ip> --grpcport 50051`

## Usage

#### Functions
* Delcerts
* historicalDataRequest
* intradayBarRequest
* subscribe and unsubscribe to bars or ticks

Please also see the [licence](https://github.com/vegabook/gBLP/blob/main/src/bbg_copyright.txt) for the Bloomberg API code contained in this package. 

 

