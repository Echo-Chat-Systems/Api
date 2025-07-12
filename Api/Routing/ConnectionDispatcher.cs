using System.Net.WebSockets;

namespace Api.Routing;

public class ConnectionDispatcher
{
	private readonly State _state;
	private readonly Router _router;
	private readonly SemaphoreSlim _slots;

	public ConnectionDispatcher(State state, Router router)
	{
		_state = state ?? throw new ArgumentNullException(nameof(state));
		_router = router ?? throw new ArgumentNullException(nameof(router));
		_slots = new SemaphoreSlim(_state.Config.Api.ConnectionSlots);
	}

	public async Task Assign(WebSocket socket)
	{
		await _slots.WaitAsync();
		try
		{
			await _router.Handle(socket);
		}
		finally
		{
			_slots.Release();
		}
	}

}