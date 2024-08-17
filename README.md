# gBLP

![background](images/finvids.gif#gh-dark-mode-only)
![background](images/finvids.gif#gh-light-mode-only)

gRPC for the Bloomberg API V3

$${\color{red}LEGAL NOTICE}$$

This software is provided "as is," without warranty of any kind, express or implied. The developer of this software assumes no responsibility or liability for any use of the software by any party. It is the sole responsibility of the user to ensure that their use of this software complies with all applicable laws, regulations, and the terms and conditions of the Bloomberg API. By using this software, you acknowledge and agree that the developer shall not be held liable for any consequences arising from the use of this software, including but not limited to, any violations of the Bloomberg API terms.}

## Status
_This is an alpha work in progress_

## Installation
_todo_
`pip install gBLP` or
`nix develop`

## Aims 
To allow users of any gRPC programming language to use the Bloomberg V3 API. 
Supports:
* Historica APIs (`//refdata`).
* Streaming APIs (`//subdata`).
* Full control over session options. 
* Protocol buffer `.proto` files usable by any programming language that has a gRPC implementation.

## FAQ
#### Why not REST?
Rest is not typed, Rest doesn't do streaming, BLPAPI's "correlationID" concept maps easily to function calls. 
#### Is this legal?
For Terminal users: yes long as you use both gRPC server (this software), and client, on the same machine. 

## Dependencies
This is a python package and depends on Python 3.10+

## Clients
_todo_
* Elixir
* Swift
* Javascript
* Roll your own
    * Use the proto files with the protocul buffers compile `protoc` (see [here](https://grpc.io/docs/protoc-installation/)) to generate function stubs for your programming language.
    * Note that you will likely have to install a `protoc` plugin. Here fore example is the [plugin for Elixir](https://github.com/brexhq/protobuf-elixir). Here is Elixir's [gRPC library](https://github.com/elixir-grpc/grpc)
 

