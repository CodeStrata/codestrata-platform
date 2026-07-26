using System.ServiceModel;

namespace SampleWcf;

[ServiceContract]
public interface IEchoService
{
    [OperationContract]
    string Echo(string message);
}

public sealed class EchoService : IEchoService
{
    public string Echo(string message)
    {
        return message;
    }
}
