using System.Data.Common;
using Database.Handlers.Config;
using EchoLib.Database.Handlers.HandlerGroups;

namespace Database;

public class Db
{
	public HandlersGroup Handlers { get; private init; }

	public Db(DbDataSource dataSource)
	{
		Handlers = new HandlersGroup
		{
			Config = new ConfigHandlers
			{
				Data = new ConfigDataHandler {DataSource = dataSource},
				Owners = new OwnersHandler {DataSource = dataSource}
			},
			Public = new PublicHandlers
			{
				ChannelCategories = null,
				ChannelMembers = null,
				Channels = null,
				Files = null,
				GuildMembers = null,
				Guilds = null,
				Invites = null,
				MessageAttachments = null,
				Messages = null,
				Roles = null,
				UserRoles = null,
				Users = null
			},
			Secure = new SecureHandlers
			{
				
			}
		};

		// Populate the handlers with itself
		Handlers.Populate(Handlers);
	}
}