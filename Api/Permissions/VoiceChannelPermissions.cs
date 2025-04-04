namespace Api.Permissions;

[Flags]
public enum VoiceChannelPermissions : uint
{
	Listen = 1,
	Speak = 2,
	UseVoiceActivity = 4,
	ViewCameras = 8,
	StreamCamera = 16,
	ViewScreenStreams = 32,
	StreamScreen = 64,
	// Hex 0000 0080 - 0800 0000 Reserved for future use
	MoveMembers = 536870912,
	ServerMuteMembers = 1073741824,
	ServerDeafenMembers = 2147483648,
}