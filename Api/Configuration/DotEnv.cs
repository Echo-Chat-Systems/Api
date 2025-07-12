namespace Api.Configuration;

public class DotEnv
{
	/// <summary>
	///  Loads the environment variables from a file.
	/// </summary>
	/// <param name="file">File to load</param>
	// ReSharper disable once MemberCanBePrivate.Global
	public static void Load(FileInfo file)
	{
		if (!file.Exists) return;

		using StreamReader reader = file.OpenText();

		while (reader.ReadLine() is { } line)
		{
			string[] parts = line.Split('=', 2, StringSplitOptions.RemoveEmptyEntries);
			if (parts.Length != 2) continue;

			string key = parts[0];
			string value = parts[1];

			Environment.SetEnvironmentVariable(key, value);
		}
	}

	/// <inheritdoc cref="Load(System.IO.FileInfo)" />
	public static void Load(string file)
	{
		Load(new FileInfo(file));
	}
}