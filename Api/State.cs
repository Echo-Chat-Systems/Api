using System.Net.WebSockets;
using System.Text.Json;
using Api.Configuration;
using Api.Routing;
using EchoLib.Auth.Encryption;
using EchoLib.Auth.Signing;
using EchoLib.Helpers;

namespace Api;

public class State(Config config, CancellationToken token)
{
	/// <summary>
	/// Application configuration and settings.
	/// </summary>
	public Config Config { get; } = config;

	/// <summary>
	/// Cancellation token for graceful shutdown and cleanup.
	/// </summary>
	public CancellationToken CancellationToken { get; } = token;

	/// <summary>
	/// Stores the clients connected to the API server.
	/// </summary>
	public ClientsStore Clients { get; } = new(config);

	/// <summary>
	/// Stores the WebSocket handlers for different API targets.
	/// </summary>
	public Dictionary<string, IWebSocketHandler> Handlers { get; } = [];

	/// <summary>
	/// Client store for managing WebSocket connections seamlessly.
	/// </summary>
	/// <param name="config"></param>
	public class ClientsStore(Config config)
	{
		private DateTime _lastCleanup = DateTime.UtcNow;

		private record struct ClientIdentifiers
		{
			/// <summary>
			/// Client signing key.
			/// </summary>
			public required PublicSigningKey Sk { get; init; }

			/// <summary>
			/// Session information for the client.
			/// </summary>
			public required Session Session { get; init; }
		}

		/// <summary>
		/// Session information for a client.
		/// </summary>
		public readonly struct Session : IEquatable<Session>
		{
			/// <summary>
			/// Session initial connection time.
			/// </summary>
			public required DateTime Created { get; init; }

			/// <summary>
			/// The last time the session was used.
			/// </summary>
			public required DateTime LastUsed { get; init; }

			/// <summary>
			/// The public signing key of the client.
			/// </summary>
			public required PublicSigningKey Sk { get; init; }

			/// <summary>
			/// Expiration time of the session.
			/// </summary>
			public required DateTime Expires { get; init; }

			public bool Equals(Session other)
			{
				return Created.Equals(other.Created) && LastUsed.Equals(other.LastUsed) && Sk.Equals(other.Sk) && Expires.Equals(other.Expires);
			}

			public override bool Equals(object? obj)
			{
				return obj is Session other && Equals(other);
			}

			public override int GetHashCode()
			{
				return HashCode.Combine(Created, LastUsed, Sk, Expires);
			}

			public static bool operator ==(Session left, Session right)
			{
				return left.Equals(right);
			}

			public static bool operator !=(Session left, Session right)
			{
				return !(left == right);
			}

			public byte[] Encrypt(PublicEncryptionKey key)
			{
				return key.Encrypt(JsonSerializer.SerializeToUtf8Bytes(this, StaticOptions.JsonSerialzer));
			}
		}

		/// <summary>
		/// Stores the clients connected to the API server.
		///
		/// Key is a server-signed hash of the client's public key and the UTC timestamp of the authentication process completion.
		/// </summary>
		private readonly Dictionary<ClientIdentifiers, WebSocket> _clients = new();

		/// <summary>
		/// Get the connections in use by a specific user.
		/// </summary>
		/// <param name="sk">User ID</param>
		public List<WebSocket> this[PublicSigningKey sk]
		{
			get
			{
				if (ShouldCleanup && _clients.Count > 0) Cleanup();

				lock (_clients)
				{
					return _clients
						.Where(c => c.Key.Sk.Equals(sk))
						.Select(c => c.Value)
						.ToList();
				}
			}
		}

		/// <summary>
		/// Accessor for the client by the server-encrypted key.
		/// </summary>
		/// <param name="key"></param>
		public WebSocket? this[byte[] key]
		{
			get
			{
				if (ShouldCleanup && _clients.Count > 0) Cleanup();

				// Attempt to decrypt the key using the server's private key
				if (!config.Keys.PrvEk.Decrypt(key, out byte[] data)) return null;

				try
				{
					// Deserialize the data into a ClientIdentifiers object
					JsonSerializer.Deserialize<ClientIdentifiers>(data, StaticOptions.JsonSerialzer);
				}
				catch
				{
					return null;
				}

				lock (_clients)
				{
					// Find the client with the matching public key
					return _clients
						.Where(c => c.Key.Sk.Equals(new PublicSigningKey(data)))
						.Select(c => c.Value)
						.FirstOrDefault();
				}
			}
		}

		/// <summary>
		/// Adds a new client session to the store.
		/// </summary>
		/// <param name="webSocket">WebSocket connection associated with this session.</param>
		/// <param name="sk">Public Signing Key of the user on this session.</param>
		/// <returns></returns>
		/// <exception cref="InvalidOperationException"></exception>
		public Session Add(WebSocket webSocket, PublicSigningKey sk)
		{
			if (ShouldCleanup && _clients.Count > 0) Cleanup();

			// Create a new session with the current time and expiration
			Session session = new()
			{
				Created = DateTime.UtcNow,
				LastUsed = DateTime.UtcNow,
				Sk = sk,
				Expires = DateTime.UtcNow + config.Timeouts.SessionExpiration
			};

			ClientIdentifiers identifiers = new()
			{
				Session = session,
				Sk = sk
			};

			lock (_clients)
			{
				if (!_clients.TryAdd(identifiers, webSocket))
					throw new InvalidOperationException("Client already exists");
			}

			return session;
		}

		public bool Contains(PublicSigningKey sk)
		{
			if (ShouldCleanup && _clients.Count > 0) Cleanup();

			lock (_clients)
			{
				return _clients.Any(c => c.Key.Sk.Equals(sk));
			}
		}

		public bool Contains(byte[] key)
		{
			if (ShouldCleanup && _clients.Count > 0) Cleanup();

			// Attempt to decrypt the key using the server's private key
			if (!config.Keys.PrvEk.Decrypt(key, out byte[] data)) return false;

			try
			{
				JsonSerializer.Deserialize<ClientIdentifiers>(data, StaticOptions.JsonSerialzer);
			}
			catch
			{
				return false;
			}

			lock (_clients)
			{
				return _clients.Any(c => c.Key.Sk.Equals(new PublicSigningKey(data)));
			}
		}

		public bool Contains(WebSocket webSocket)
		{
			if (ShouldCleanup && _clients.Count > 0) Cleanup();

			lock (_clients)
			{
				return _clients.ContainsValue(webSocket);
			}
		}

		public bool Remove(WebSocket webSocket)
		{
			if (ShouldCleanup && _clients.Count > 0) Cleanup();

			lock (_clients)
			{
				KeyValuePair<ClientIdentifiers, WebSocket> entry = _clients.FirstOrDefault(c => c.Value == webSocket);
				return !entry.Equals(default(KeyValuePair<ClientIdentifiers, WebSocket>)) && _clients.Remove(entry.Key);
			}
		}

		private bool ShouldCleanup => DateTime.UtcNow - _lastCleanup > config.Timeouts.ClientsCleanup;

		private void Cleanup()
		{
			lock (_clients)
			{
				DateTime now = DateTime.UtcNow;
				List<ClientIdentifiers> expiredSessions = _clients
					.Where(c => c.Key.Session.Expires < now)
					.Select(c => c.Key)
					.ToList();

				foreach (ClientIdentifiers session in expiredSessions)
				{
					_clients.Remove(session);
				}

				_lastCleanup = now;
			}
		}
	}
}