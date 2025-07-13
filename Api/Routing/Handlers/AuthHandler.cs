using System.Buffers.Text;
using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text.Json.Nodes;
using EchoLib.Auth;
using EchoLib.Auth.Encryption;
using EchoLib.Auth.Signing;
using EchoLib.Comms;
using EchoLib.Helpers;
using EchoLib.Models.Net.Users.Broadcasts.Server;
using EchoLib.Models.Other;
using EchoLib.Processes.Actions.Auth.SignIn;
using EchoLib.Processes.Params.Auth.Signin;

namespace Api.Routing.Handlers;

public class AuthHandler: BaseHandler
{
	public override string Target { get; } = Targets.Auth;

	public AuthHandler(State state) : base(state)
	{
		RegisterAction(Targets.AuthActions.SigninStart, HandleSigninStart);
	}

	private class SigninState
	{
		public required PublicKeyPair KeyPair { get; set; }
		public required (byte[] signingChallenge, byte[] encryptionChallenge) Challenge { get; set; }
	}

	private async Task HandleSigninStart(WebSocket socket, MessageEnvelope<JsonObject> envelope)
	{
		SigninStartParams parameters;
		// Try deserializing the parameters to SigninStartParams
		try
		{
			parameters = DeserialiseParams<SigninStartParams>(envelope);

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

		// Create a new ref code and challenge
		Guid refCode = Guid.NewGuid();

		while (Requests.ContainsKey(refCode))
		{
			refCode = Guid.NewGuid();
		}

		// Read the public key from the parameters
		PublicKeyPair keyPair = new()
		{
			SigningKey = parameters.Sk,
			EncryptionKey = parameters.Ek
		};

		// Generate a challenge for the key pair
		byte[] signingChallenge = RandomNumberGenerator.GetBytes(128);
		byte[] encryptionChallenge = RandomNumberGenerator.GetBytes(128);
		byte[] encryptedChallenge;
		// Check if the encryption key is valid
		try
		{
			encryptedChallenge = parameters.Ek.Encrypt(encryptionChallenge);
		}
		catch (CryptographicException)
		{
			await WebSocketTranslator.SendError(socket, ErrorTypes.InvalidParameters, envelope, "Invalid encryption key.");
			return;
		}

		// Add the request to the Requests dictionary
		Requests[refCode] = new RequestState(new SigninState
		{
			KeyPair = keyPair,
			Challenge = (signingChallenge, encryptionChallenge)
		});

		// Create the response parameters
		SigninChallengeParams responseParams = new()
		{
			Ref = refCode.ToString(),
			SignChallenge = Convert.ToBase64String(signingChallenge),
			EncryptChallenge = Convert.ToBase64String(encryptedChallenge)
		};

		// Send the response back to the client
		await WebSocketTranslator.SendAction<SignInChallengeAction, SigninChallengeParams>(socket, responseParams);
	}

	private async Task HandleSigninResponse(WebSocket socket, MessageEnvelope<JsonObject> envelope)
	{
		SigninResponseParams parameters;
		// Try deserializing the parameters to SigninResponseParams
		try
		{
			parameters = DeserialiseParams<SigninResponseParams>(envelope);
		}
		catch (ArgumentNullException ex)
		{
			await WebSocketTranslator.SendError(socket, ErrorTypes.InvalidParameters & ErrorTypes.DeserializationError, envelope);
			return;
		}
		catch (InvalidOperationException ex)
		{
			await WebSocketTranslator.SendError(socket, ErrorTypes.DeserializationError, envelope);
			return;
		}

		// Get the request state from the Requests dictionary using the ref code
		if (!Guid.TryParse(parameters.Ref, out Guid refCode) || !Requests.TryGetValue(refCode, out RequestState? requestState))
		{
			await WebSocketTranslator.SendError(socket, ErrorTypes.InvalidParameters, envelope);
			return;
		}

		// Get the state from the request
		if (requestState.Data is not SigninState signinState)
		{
			await WebSocketTranslator.SendError(socket, ErrorTypes.InvalidParameters, envelope);
			return;
		}

		// Check if the signature of the signing challenge matches the one in the parameters
		if (!parameters.Signature.Verify(signinState.KeyPair.SigningKey ?? throw new InvalidOperationException("Somehow signing key is null"), signinState.Challenge.signingChallenge))
		{
			goto Fail;
		}

		// Try to convert the decrypted value from the parameters to a byte array
		byte[]? decrypted;

		try
		{
			decrypted = Convert.FromBase64String(parameters.Decrypted);
		}
		catch (FormatException)
		{
			await WebSocketTranslator.SendError(socket, ErrorTypes.InvalidParameters, envelope, "Invalid base64 string.");
			return;
		}

		// Check if the value returned by the encryption challenge matches the one in the parameters
		if (signinState.Challenge.encryptionChallenge != decrypted) {goto Fail;}

		// Challenge passed, so we can sign in the user and create a session


		Fail:
			SigninCompleteParams responseParams = new()
			{
				Status = 0,
				Message = "Bad credentials."
			};
			await WebSocketTranslator.SendAction<SignInCompleteAction, SigninCompleteParams>(socket, responseParams);

	}
}