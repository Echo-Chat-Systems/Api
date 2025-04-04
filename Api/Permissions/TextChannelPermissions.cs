namespace Api.Permissions;

[Flags]
public enum TextChannelPermissions : uint
{
	SendMessages = 1,
	DeleteMessages = 2,
	UseEmojis = 4,
	UseAnimatedEmojis = 8,
	UseStickers = 16,
	UseAnimatedStickers = 32,
	UseExternalEmojis = 64,
	UseAnimatedExternalEmojis = 128,
	UseExternalStickers = 256,
	UseAnimatedExternalStickers = 512,
	CreatePublicThreads = 1024,
	DeletePublicThreads = 2048,
	// ReSharper disable once InconsistentNaming
	SendTTSMessages = 4096,
	CreatePrivateThreads = 8192,
	DeletePrivateThreads = 16384,
	AddReactions = 32768,
	AttachFiles = 65536,
	EmbedLinks = 131072,
	PinMessages = 262144,
	UnpinMessages = 524288,
	// Hex 0010 0000 - 0100 0000 Reserved for future use
	ModerateReactions = 33554432,
	ModeratePins = 67108864,
	ModerateAttachments = 134217728,
	ModerateEmbeds = 268435456,
	ModerateMessages = 536870912,
	// Hex 4000 0000 - 8000 0000 Reserved for future use
}