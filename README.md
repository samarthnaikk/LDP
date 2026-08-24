# LLM Direct Protocol (LDP) - Transport Foundation

This repository establishes the foundational transport layer and interface boundaries for the LLM Direct Protocol (LDP). The current implementation strictly focuses on the peer-to-peer communication protocol, enabling two different systems to seamlessly stream data without the overhead of model splitting or inference engines.

## Protocol Interface

The communication boundary between nodes is defined via Protocol Buffers to ensure highly optimized binary serialization.

* **Definition File:** `ldp_service.proto` defines the structural messaging format and interface boundaries.


* **Core Service:** `LLMPipelineService` handles the sequential execution chain via the `ForwardActivationStream` RPC.


* **Activation Payload:** Transmits the `token_index`, 5120-dimension `tensor_data` array, `tensor_shape`, and `target_next_layer` offset verification.


* **Forward Response:** Returns a `status_success` boolean alongside an `error_message` string for stack diagnostics if processing fails.



## Transport Architecture

The network layer completely discards custom message queues or raw sockets in favor of gRPC operating over an HTTP/2 transport layer.

* **Persistent Streams:** Communication relies on a single long-lived, multiplexed TCP connection between consecutive nodes to bypass repeated socket handshake overhead.


* **Unidirectional Flow:** Data moves strictly in a linear direction from a transmitter to a receiver.


* **Asynchronous Decoupling:** Network reception is explicitly separated from active compute threads to prevent blocking during data transfer.



## Implementation Components

To establish a usable connection between two distinct systems, the following architectural components must be implemented on each instance:

* **Network Receiver:** A gRPC server buffer that accepts incoming activation payloads.


* **Thread-Safe Queue:** An asynchronous holding structure where the receiver safely pushes incoming payloads.


* **Client Transmitter:** A gRPC client that pushes the forward payload to the next node in the pipeline.


* **Loopback Channel:** A lightweight backchannel that returns the final predicted token ID to the master head node.



## Testing the Connection

Before integrating the computation core, validate the transport layer by generating a dummy 20.48 KB float array, which represents the strict deterministic payload size of a single token evaluation. Stream this payload from System 1 to System 2 to confirm that the pipeline successfully routes the data and triggers a successful response.