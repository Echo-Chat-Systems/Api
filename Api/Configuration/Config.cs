using EchoLib.Auth;
using EchoLib.Auth.Encryption;
using EchoLib.Auth.Signing;
using EchoLib.Helpers;
using Microsoft.Extensions.Configuration;

namespace Api.Configuration;

public class Keys : KeySet
{
	public Keys(PublicSigningKey pubSk, PrivateSigningKey prvSk, PublicEncryptionKey pubEk, PrivateEncryptionKey prvEk)
	{
		PubSk = pubSk;
		PrvSk = prvSk;
		PubEk = pubEk;
		PrvEk = prvEk;
	}
}

public class Web(string version, string name, string description, int port)
{
	public string Version { get; } = version;
	public string Name { get; } = name;
	public string Description { get; } = description;
	public int Port { get; } = port;
}

public class Api(int connectionSlots)
{
	public int ConnectionSlots { get; } = connectionSlots;
}

public class Timeouts(TimeSpan certificatesExpiration,TimeSpan clientsCleanup, TimeSpan stateStorageExpiration, TimeSpan stateStorageCleanup, TimeSpan sessionExpiration)
{
	public TimeSpan CertificatesExpiration { get; } = certificatesExpiration;
	public TimeSpan ClientsCleanup { get; } = clientsCleanup;
	public TimeSpan StateStorageExpiration { get; } = stateStorageExpiration;
	public TimeSpan StateStorageCleanup { get; } = stateStorageCleanup;
	public TimeSpan SessionExpiration { get; } = sessionExpiration;
}

public class Config
{
	public Config(IConfiguration configuration)
	{
		// Check if keys are present, if not generate them
		if (
			string.IsNullOrEmpty(configuration["Keys:PublicSigningKey"]) &&
			string.IsNullOrEmpty(configuration["Keys:PrivateSigningKey"]) &&
			string.IsNullOrEmpty(configuration["Keys:PublicEncryptionKey"]) &&
			string.IsNullOrEmpty(configuration["Keys:PrivateEncryptionKey"])
		)
		{
			KeySet keys = KdvHelper.Generate();
			configuration["Keys:PublicSigningKey"] = keys.PubSk.ToString();
			configuration["Keys:PrivateSigningKey"] = keys.PrvSk.ToString();
			configuration["Keys:PublicEncryptionKey"] = keys.PubEk.ToString();
			configuration["Keys:PrivateEncryptionKey"] = keys.PrvEk.ToString();

			Console.WriteLine("RUNNING IN DEVELOPMENT MODE: Keys were generated and saved to the configuration.");
		}

		Web = new Web(
			configuration["Web:Version"] ?? throw new MissingFieldException("Web:Version"),
			configuration["Web:Name"] ?? throw new MissingFieldException("Web:Name"),
			configuration["Web:Description"] ?? throw new MissingFieldException("Web:Description"),
			int.Parse(configuration["Web:Port"] ?? throw new MissingFieldException("Web:Port"))
		);

		Api = new Api(
			int.Parse(configuration["Api:ConnectionSlots"] ?? throw new MissingFieldException("Api:ConnectionSlots"))
		);

		Timeouts = new Timeouts(
			TimeSpan.Parse(configuration["Timeouts:CertificatesExpiration"] ?? throw new MissingFieldException("Timeouts:CertificatesExpiration")),
			TimeSpan.Parse(configuration["Timeouts:ClientsCleanup"] ?? throw new MissingFieldException("Timeouts:ClientsCleanup")),
			TimeSpan.Parse(configuration["Timeouts:StateStorageExpiration"] ?? throw new MissingFieldException("Timeouts:StateStorageExpiration")),
			TimeSpan.Parse(configuration["Timeouts:StateStorageCleanup"] ?? throw new MissingFieldException("Timeouts:StateStorageCleanup")),
			TimeSpan.Parse(configuration["Timeouts:SessionExpiration"] ?? throw new MissingFieldException("Timeouts:SessionExpiration"))
		);

		Keys = new Keys(
			new PublicSigningKey(configuration["Keys:PublicSigningKey"] ?? throw new MissingFieldException("Keys:PublicSigningKey")),
			new PrivateSigningKey(configuration["Keys:PrivateSigningKey"] ?? throw new MissingFieldException("Keys:PrivateSigningKey")),
			new PublicEncryptionKey(configuration["Keys:PublicEncryptionKey"] ?? throw new MissingFieldException("Keys:PublicEncryptionKey")),
			new PrivateEncryptionKey(configuration["Keys:PrivateEncryptionKey"] ?? throw new MissingFieldException("Keys:PrivateEncryptionKey"))
		);
	}


	public Web Web { get; }

	public Api Api { get; }

	public Timeouts Timeouts { get; }

	public Keys Keys { get; }
}