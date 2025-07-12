using System.Net.WebSockets;
using System.Text.Json.Nodes;
using EchoLib.Comms;

namespace Api.Routing;

public interface IWebSocketHandler
{
	Task HandleAsync(WebSocket socket, MessageEnvelope<JsonObject> envelope);
}