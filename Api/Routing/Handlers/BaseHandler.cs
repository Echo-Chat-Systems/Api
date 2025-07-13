using System.Net.WebSockets;
using System.Text.Json;
using System.Text.Json.Nodes;
using EchoLib.Comms;
using EchoLib.Helpers;
using EchoLib.Processes.Actions;
using EchoLib.Processes.Params;

namespace Api.Routing.Handlers;

public abstract class BaseHandler : IWebSocketHandler
{
	/// <summary>
	/// The target this handler is responsible for.
	/// </summary>
	public abstract string Target { get; }

	/// <summary>
	/// Actions that this handler can perform.
	/// </summary>
	protected readonly Dictionary<string, Func<WebSocket, MessageEnvelope<JsonObject>, Task>> Actions = new()
	{
		{ "ping", async (socket, envelope) => await WebSocketTranslator.SendAction<PongAction, PongParams>(socket, new PongParams()) },
		{ "pong", (socket, envelope) => Task.CompletedTask }
	};

	/// <summary>
	/// Application state storage.
	/// </summary>
	protected readonly State State;

	/// <summary>
	/// Request states for tracking ongoing requests.
	/// </summary>
	protected readonly Dictionary<Guid, RequestState> Requests = new();

	/// <summary>
	/// Initialises a new instance of the <see cref="BaseHandler"/> class.
	/// </summary>
	/// <param name="state">Application state storage.</param>
	protected BaseHandler(State state)
	{
		State = state;

		// Start the periodic cleanup task
		Task.Run(AsyncCleanupRequestsLoop, state.CancellationToken);
	}

	/// <summary>
	/// Cleans up expired requests periodically.
	/// </summary>
	private async Task AsyncCleanupRequestsLoop()
	{
		while (!State.CancellationToken.IsCancellationRequested)
		{
			await Task.Delay(State.Config.Timeouts.StateStorageCleanup, State.CancellationToken);
			CleanupExpiredRequests();
		}
	}

	/// <summary>
	/// Cleans up expired requests from the request state storage.
	/// </summary>
	public void CleanupExpiredRequests()
	{
		DateTime now = DateTime.UtcNow;
		List<Guid> expiredKeys = Requests
			.Where(kvp => now - kvp.Value.Created > State.Config.Timeouts.StateStorageExpiration) // 5 minutes expiration
			.Select(kvp => kvp.Key)
			.ToList();

		foreach (Guid key in expiredKeys)
		{
			Requests.Remove(key);
		}
	}

	/// <summary>
	/// Handles incoming WebSocket messages.
	/// </summary>
	/// <param name="socket">Active socket connection.</param>
	/// <param name="envelope">Message being handled.</param>
	/// <exception cref="NotSupportedException">Thrown when there is no applicable action method for the requested action.</exception>
	public async Task HandleAsync(WebSocket socket, MessageEnvelope<JsonObject> envelope)
	{
		if (Actions.TryGetValue(envelope.Target, out Func<WebSocket, MessageEnvelope<JsonObject>, Task>? action))
		{
			await action(socket, envelope);
		}

		throw new NotSupportedException($"No method found for action: {envelope.Data.Action}");
	}

	/// <summary>
	/// Represents the state of a request, including its creation time and associated data.
	/// </summary>
	/// <param name="data"></param>
	protected class RequestState(object data)
	{
		public DateTime Created { get; } = DateTime.UtcNow;
		public object Data { get; set; } = data;
	}

	/// <summary>
	/// Registers a new action with the handler.
	/// </summary>
	/// <param name="actionName">Action name.</param>
	/// <param name="handler">Handler method.</param>
	/// <exception cref="InvalidOperationException">Thrown if the action handler is already registered.</exception>
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
	protected static T DeserialiseParams<T>(MessageEnvelope<JsonObject> envelope)
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