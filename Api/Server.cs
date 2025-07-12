using System.Net;
using System.Net.Sockets;
using System.Net.WebSockets;
using Api.Configuration;
using Api.Routing;
using Api.Routing.Handlers;
using EchoLib.Comms;
using Microsoft.Extensions.Configuration;

namespace Api;

/// <summary>
/// Main API server class.
/// </summary>
public class Server
{
	private CancellationTokenSource _cts = new();
	private readonly State _state;
	private readonly HttpListener _listener;

	public Server()
	{
		// Load config
		DotEnv.Load(new FileInfo(".env"));
		Config config = new(
			new ConfigurationBuilder()
				.AddJsonFile("config/appsettings.json")
				.AddEnvironmentVariables()
				.Build()
		);

		// Initialize state
		_state = new State(config, _cts.Token);

		_listener = new HttpListener
		{
			Prefixes = { $"http://localhost:{config.Web.Port}/" }
		};

		// Initialise all handlers
		_state.Handlers.Add(Targets.Auth, new AuthHandler(_state));
	}

	public async Task StartAsync()
	{
		_listener.Start();

		Console.WriteLine($"API server started at {_listener.Prefixes.First()} with a maximum of {_state.Config.Api.ConnectionSlots} connections.");

		while (!_state.CancellationToken.IsCancellationRequested)
		{
			try
			{
				HttpListenerContext context = await _listener.GetContextAsync();

				if (!context.Request.IsWebSocketRequest)
				{
					context.Response.StatusCode = (int)HttpStatusCode.BadRequest;
					context.Response.Close();
					continue;
				}

				_ = Task.Run(() => HandleClientAsync(context), _state.CancellationToken);

			}
			catch (HttpListenerException) when (_state.CancellationToken.IsCancellationRequested)
			{
				// Listener was stopped, exit the loop
				break;
			}
			catch (Exception ex)
			{
				Console.WriteLine($"Error handling request: {ex.Message}");
			}
		}
	}

	public async Task HandleClientAsync(HttpListenerContext context)
	{
		HttpListenerWebSocketContext wsContext = await context.AcceptWebSocketAsync(null);
		WebSocket webSocket = wsContext.WebSocket;

		//
	}

	public async Task StopAsync()
	{
		await _cts.CancelAsync();
	}
}