import Foundation
import CoreMIDI
import NIO
import NIOHTTP1
import NIOWebSocket
import WebSocketKit

// MARK: - MIDI: Create a virtual destination and a sender
final class MIDISender {
    private var client = MIDIClientRef()
    private var outPort = MIDIPortRef()
    private var destEndpoint = MIDIEndpointRef()

    init?(virtualDestinationName: String = "Fadebender Out") {
        var status = noErr

        status = MIDIClientCreate("FadebenderClient" as CFString, nil, nil, &client)
        guard status == noErr else { return nil }

        status = MIDIOutputPortCreate(client, "FadebenderOutPort" as CFString, &outPort)
        guard status == noErr else { return nil }

        // Create a virtual destination endpoint that DAWs can see.
        status = MIDIDestinationCreate(client, virtualDestinationName as CFString, nil, nil, &destEndpoint)
        guard status == noErr else { return nil }
        print("✅ CoreMIDI virtual destination created: \(virtualDestinationName)")
    }

    func sendCC(channel: Int, controller: Int, value: Int) {
        // Clamp to MIDI ranges
        let ch = UInt8(max(1, min(16, channel)) - 1) // 0-15 for status low nibble
        let cc = UInt8(max(0, min(127, controller)))
        let val = UInt8(max(0, min(127, value)))

        var packetList = MIDIPacketList()
        let bufferSize = MemoryLayout<MIDIPacketList>.size + 3
        withUnsafeMutablePointer(to: &packetList) { pktListPtr in
            let pkt = MIDIPacketListInit(pktListPtr)
            let status: UInt8 = 0xB0 | ch // Control Change
            var data: [UInt8] = [status, cc, val]
            _ = MIDIPacketListAdd(pktListPtr, bufferSize, pkt, 0, data.count, &data)
            MIDISend(outPort, destEndpoint, pktListPtr)
        }
    }
}

// MARK: - JSON payload
struct CCMessage: Codable {
    let cc: Int
    let channel: Int
    let value: Int
    let target: String?
}
struct BridgeEnvelope: Codable {
    let op: String
    let payload: [CCMessage]
}

// MARK: - WebSocket Server
final class BridgeServer {
    private let group = MultiThreadedEventLoopGroup(numberOfThreads: System.coreCount)
    private var server: WebSocketServer?

    private let midi: MIDISender

    init?(midi: MIDISender) {
        self.midi = midi
        self.server = nil
    }

    func start(host: String = "127.0.0.1", port: Int = 17890) throws {
        let app = NIOHTTP1Server.bootstrap(group: group) { channel in
            NIOWebSocketServerUpgrader(shouldUpgrade: { _, _ in channel.eventLoop.makeSucceededFuture(HTTPHeaders()) },
                                       upgradePipelineHandler: { ws, _ in
                self.handle(ws: ws)
            })
        }

        // Start HTTP server with WS upgrader
        let bootstrap = ServerBootstrap(group: group)
            .childChannelInitializer { channel in
                let httpHandler = NIOHTTPHandler { req, res in
                    // Tiny health endpoint for sanity checks
                    if req.uri == "/health" {
                        res.writeHead(status: .ok)
                        res.write("OK")
                        res.end()
                    } else {
                        res.writeHead(status: .notFound)
                        res.end()
                    }
                }
                return channel.pipeline.configureHTTPServerPipeline().flatMap {
                    channel.pipeline.addHandler(httpHandler)
                }
            }
            .serverChannelOption(ChannelOptions.backlog, value: 256)
            .serverChannelOption(ChannelOptions.socketOption(.so_reuseaddr), value: 1)

        // Replace with WebSocketKit's convenience
        let wsServer = WebSocketServer(group: group)
        wsServer.errorCallback = { print("WS error: \($0)") }
        wsServer.onUpgrade = { ws, _ in self.handle(ws: ws) }

        self.server = wsServer
        try wsServer.start(host: host, port: port).wait()
        print("✅ Fadebender Bridge WebSocket listening on ws://\(host):\(port)")

        // prevent exit
        dispatchMain()
    }

    private func handle(ws: WebSocket) {
        print("🔌 WS client connected")
        ws.onText { [weak self] ws, text in
            guard let self else { return }
            do {
                let env = try JSONDecoder().decode(BridgeEnvelope.self, from: Data(text.utf8))
                if env.op == "emit_cc" {
                    for cc in env.payload {
                        self.midi.sendCC(channel: cc.channel, controller: cc.cc, value: cc.value)
                        print("🎛 Sent CC ch\(cc.channel) #\(cc.cc) = \(cc.value) \(cc.target.map { "(\($0))" } ?? "")")
                    }
                    ws.send(#"{"ok":true}"#)
                } else {
                    ws.send(#"{"ok":false,"error":"unknown op"}"#)
                }
            } catch {
                ws.send(#"{"ok":false,"error":"bad json"}"#)
            }
        }

        ws.onClose.whenComplete { _ in
            print("🔌 WS client disconnected")
        }
    }

    deinit {
        try? group.syncShutdownGracefully()
    }
}

// Minimal HTTP handler for health (used above)
final class NIOHTTPHandler: ChannelInboundHandler {
    typealias InboundIn = HTTPServerRequestPart
    typealias OutboundOut = HTTPServerResponsePart

    let responder: (HTTPRequestHead, NIOHTTPResponseWriter) -> Void
    init(_ responder: @escaping (HTTPRequestHead, NIOHTTPResponseWriter) -> Void) {
        self.responder = responder
    }
    func channelRead(context: ChannelHandlerContext, data: NIOAny) {
        let part = self.unwrapInboundIn(data)
        switch part {
        case .head(let head):
            let writer = NIOHTTPResponseWriter(context: context)
            self.responder(head, writer)
        case .body: break
        case .end: break
        }
    }
}

struct NIOHTTPResponseWriter {
    let context: ChannelHandlerContext
    func writeHead(status: HTTPResponseStatus) {
        var headers = HTTPHeaders()
        headers.add(name: "Content-Type", value: "text/plain; charset=utf-8")
        let head = HTTPResponseHead(version: .init(major: 1, minor: 1), status: status, headers: headers)
        context.write(NIOAny(HTTPServerResponsePart.head(head)), promise: nil)
    }
    func write(_ s: String) {
        var buffer = context.channel.allocator.buffer(capacity: s.utf8.count)
        buffer.writeString(s)
        context.write(NIOAny(HTTPServerResponsePart.body(.byteBuffer(buffer))), promise: nil)
    }
    func end() {
        context.writeAndFlush(NIOAny(HTTPServerResponsePart.end(nil)), promise: nil)
    }
}

// MARK: - Boot
guard let midi = MIDISender(virtualDestinationName: "Fadebender Out") else {
    fatalError("Failed to create MIDI client/port")
}
let bridge = BridgeServer(midi: midi)!
try bridge.start(host: "127.0.0.1", port: 17890)
