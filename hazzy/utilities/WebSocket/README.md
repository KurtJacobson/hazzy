WebSockets & ProtoBuf
=

Some notes...

http example client:

```
client.html
```

RunTime requirements(apt):

```
# apt install python-protobuf
```

Build requirements(to update linuxcnc.proto):


protoc built from sources

```
$ git clone https://github.com/google/protobuf.git
$ cd protobuf
$ ./autogen.sh
$ ./configure
$ make
# make install

```

Build steps:

```
$ protoc -I=hazzy/utilities/WebSocket/proto --python_out=hazzy/utilities/WebSocket hazzy/utilities/WebSocket/proto/linuxcnc.proto
```

Do not edit the resulting python code

notes from:

https://github.com/google/protobuf
https://developers.google.com/protocol-buffers/docs/pythontutorial