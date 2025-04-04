using System.Data.Common;
using Npgsql;

namespace Api.Database.Handlers;

public class BaseHandler
{
	protected readonly string ConnectionString;

    /// <summary>
    ///  Collection of all handlers.
    /// </summary>
    protected HandlersGroup HandlersGroup = null!;

	protected BaseHandler(string connectionString)
	{
		ConnectionString = connectionString;
	}

    /// <summary>
    ///  Database connection.
    /// </summary>
    protected async Task<NpgsqlConnection> Connection()
	{
		NpgsqlConnection connection;
		int timeWaited = 0;
		while (true)
			try
			{
				connection = new NpgsqlConnection(ConnectionString);
				break;
			}
			catch (PostgresException exception)
			{
				if (exception.SqlState != "53300") throw;
				Console.WriteLine(
					$"Connection limit hit. Waiting 500ms before trying again. Total time waited {timeWaited}");
				await Task.Delay(500);
				timeWaited += 500;
			}

		connection.Open();
		return connection;
	}

	public void Populate(HandlersGroup handlersGroup)
	{
		HandlersGroup = handlersGroup;
	}

	protected async Task ExecuteNonQuery(DbCommand command)
	{
		await using NpgsqlConnection? connection = await Connection();
		await using NpgsqlTransaction? transaction = await connection.BeginTransactionAsync();
		command.Transaction = transaction;

		try
		{
			await command.ExecuteNonQueryAsync();
		}
		catch (Exception error)
		{
			await transaction.RollbackAsync();
			Console.WriteLine($"Failed to execute command: {error.Message}");
			throw;
		}

		await transaction.CommitAsync();
	}

	protected static async Task<NpgsqlDataReader> ExecuteReader(NpgsqlCommand command)
	{
		return await command.ExecuteReaderAsync();
	}
}