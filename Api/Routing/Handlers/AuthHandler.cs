using System.Net.WebSockets;
using System.Text.Json.Nodes;
using EchoLib.Comms;
using EchoLib.Helpers;
using EchoLib.Models.Other;
using EchoLib.Params.Auth.Signin;

namespace Api.Routing.Handlers;

public class AuthHandler: BaseHandler
{
	public override string Target { get; } = Targets.Auth;

	public AuthHandler(State state) : base(state)
	{
		RegisterAction(Targets.AuthActions.SigninStart, HandleSigninStart);
	}

	private async Task HandleSigninStart(WebSocket socket, MessageEnvelope<JsonObject> envelope)
	{
		// Try deserializing the parameters to SigninStartParams
		try
		{
			SigninStartParams paramaters = DeserialiseParams<SigninStartParams>(envelope);

		} catch (ArgumentNullException ex)
		{
			await WebSocketTranslator.SendError(socket, ErrorTypes.InvalidParameters & ErrorTypes.DeserializationError, envelope);
			return;
		}
		catch (InvalidOperationException ex)
		{
			await WebSocketTranslator.SendError(socket, ErrorTypes.DeserializationError, envelope);
			return;
		}
	}
}