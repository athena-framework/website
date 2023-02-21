As mentioned in the [Why Athena?](../why_athena.md) page, [dependency injection](../why_athena.md#dependency-injection) and [dependency inversion](../why_athena.md#dependency-inversion) play a major part in the overall design of the framework.
In the context of the Athena Framework, each request has its own container instance that allows using services to share state without having to worry about it leaking between requests.

The DI portion of the Athena Framework is quite powerful, checkout [ADI::Register][] for more information on all its feature, or stop by the Discord for any questions.
