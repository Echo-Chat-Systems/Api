namespace Api.Permissions;

// Usage derived from https://stackoverflow.com/a/57435831
[Flags]
public enum GuildPermissions : uint
{
	SendInvites    = 4,
	ManageEvents   = 8,
	CreateEvents   = 16,
	DeleteEvents   = 32,
	ManageWebhooks = 64,
	CreateWebhooks = 128,
	DeleteWebhooks = 256, 
	ManageStickers = 512,
	CreateStickers = 1024,
	DeleteStickers = 2048, 
	ManageEmojis   = 4096,
	CreateEmojis   = 8192,
	DeleteEmojis   = 16384,
	ManageInvites  = 32768,
	ManageMembers  = 65536, 
	KickMembers    = 131072, 
	BanMembers     = 262144, 
	UnbanMembers   = 524288, 
	ManageChannels = 1048576,
	CreateChannels = 2097152, 
	DeleteChannels = 4194304, 
	AssignRoles    = 8388608, 
	RemoveRoles    = 16777216, 
	ManageRoles    = 33554432,
	CreateRoles    = 67108864,
	DeleteRoles    = 134217728,
	ManageGuild    = 268435456,
	ViewInsights   = 536870912,
	ViewAuditLogs  = 1073714824,
	Administrator  = 2147483648
}