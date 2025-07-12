using System.Diagnostics;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using EchoLib.Comms;

namespace Api.Routing;

public class Router
{
	private readonly State _state;

	public Router(State state)
	{
		_state = state;
	}

	public async Task Handle(WebSocket socket)
	{
		while (socket.State == WebSocketState.Open)
		{
			try
			{
				MessageEnvelope<JsonObject>? envelope = await ReadEnvelopeAsync(socket);
				if (envelope == null)
				{
					Debug.WriteLine("No envelope read from socket, closing connection.");
					continue; // Skip if no envelope was read
				}

				if (!_state.Handlers.ContainsKey(envelope.Target))
				{
					Debug.WriteLine($"No target found for {envelope.Target}");
					continue;
				}

				await _state.Handlers[envelope.Target].HandleAsync(socket, envelope);
			}
			catch (Exception ex)
			{
				Debug.WriteLine($"Error handling message: {ex.Message}");
			}
		}
	}

	private async Task<MessageEnvelope<JsonObject>?> ReadEnvelopeAsync(WebSocket socket)
	{
		string message = await ReadMessageAsync(socket);
		MessageEnvelope<JsonObject>? envelope = JsonSerializer.Deserialize<MessageEnvelope<JsonObject>>(message);

		return envelope ?? null;
	}


	private async Task<string> ReadMessageAsync(WebSocket socket)
	{
		byte[] buffer = new byte[1024];
		using MemoryStream ms = new();

		WebSocketReceiveResult result;

		do
		{
			result = await socket.ReceiveAsync(new ArraySegment<byte>(buffer), _state.CancellationToken);
			ms.Write(buffer, 0, result.Count);
		} while (!result.EndOfMessage);

		return Encoding.UTF8.GetString(ms.ToArray());
	}
}