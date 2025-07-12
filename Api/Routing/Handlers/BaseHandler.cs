using System.Net.WebSockets;
using System.Text.Json;
using System.Text.Json.Nodes;
using EchoLib.Comms;
using EchoLib.Helpers;
using EchoLib.Params;
using EchoLib.Processes;

namespace Api.Routing.Handlers;

public abstract class BaseHandler(State state) : IWebSocketHandler
{
	/// <summary>
	/// The target this handler is responsible for.
	/// </summary>
	public abstract string Target { get; }

	public readonly Dictionary<string, Func<WebSocket, MessageEnvelope<JsonObject>, Task>> Actions = new()
	{
		{ "ping", async (socket, envelope) => await WebSocketTranslator.SendAction<PongAction, PongParams>(socket, new PongParams()) },
		{ "pong", (socket, envelope) => Task.CompletedTask }
	};

	public State State = state ?? throw new ArgumentNullException(nameof(state));
	public readonly Dictionary<Guid, RequestState> Requests = new();

	public async Task HandleAsync(WebSocket socket, MessageEnvelope<JsonObject> envelope)
	{
		if (Actions.TryGetValue(envelope.Target, out Func<WebSocket, MessageEnvelope<JsonObject>, Task>? action))
		{
			await action(socket, envelope);
		}

		throw new NotSupportedException($"No method found for action: {envelope.Data.Action}");
	}

	public class RequestState(object data)
	{
		public DateTime Created { get; } = DateTime.UtcNow;
		public object Data { get; set; } = data;
	}

	protected void RegisterAction(string actionName, Func<WebSocket, MessageEnvelope<JsonObject>, Task> handler)
	{
		if (!Actions.TryAdd(actionName, handler))
		{
			throw new InvalidOperationException($"Action {actionName} is already registered.");
		}
	}

	/// <summary>
	/// Deserialises the parameters from the given envelope into the specified type.
	/// </summary>
	/// <param name="envelope">Message envelope.</param>
	/// <typeparam name="T">Type of message parameters.</typeparam>
	/// <returns>Parameters object.</returns>
	/// <exception cref="ArgumentNullException">Thrown when Data.Params is null</exception>
	/// <exception cref="InvalidOperationException">Thrown when deserialization fails</exception>
	public static T DeserialiseParams<T>(MessageEnvelope<JsonObject> envelope)
		where T : class
	{
		// Attempt to deserialize the parameters from the envelope
		if (envelope.Data.Params is null)
		{
			throw new ArgumentNullException(nameof(envelope.Data.Params), "Parameters cannot be null.");
		}

		T? parameters = envelope.Data.Params.Deserialize<T>();
		if (parameters is null)
		{
			throw new InvalidOperationException($"Failed to deserialize parameters to type {typeof(T).Name}.");
		}
		return parameters;
	}
}