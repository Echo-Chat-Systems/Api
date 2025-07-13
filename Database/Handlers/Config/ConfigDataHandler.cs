using System.Data.Common;
using EchoLib.Database.Handlers.Bases.Config;
using EchoLib.Database.Models.Config;

namespace Database.Handlers.Config;

public class ConfigDataHandler : BConfigDataHandler
{
	public async override Task<MConfigData> Create(string key, object value)
	{
		// Create a new command to insert the new config data
		throw new NotImplementedException();

	}

	public async override Task<MConfigData?> Get(string key)
	{
		throw new NotImplementedException();
	}

	public async override Task<MConfigData> Update(MConfigData row)
	{
		throw new NotImplementedException();
	}

	public async override Task Delete(string key)
	{
		throw new NotImplementedException();
	}

	public async override Task<bool> Exists(string key)
	{
		throw new NotImplementedException();
	}
}