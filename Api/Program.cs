namespace Api;

class Program
{
	static void Main(string[] args)
	{
		Console.WriteLine("EchoLib API is running...");

		// Initialize and start the WebSocket server
		Server server = new();
		_ = server.StartAsync();

		// Keep the application running
		Console.WriteLine("Press any key to exit...");
		Console.ReadKey();

		_ = server.StopAsync();
		Console.WriteLine("EchoLib API stopping.");
	}
}