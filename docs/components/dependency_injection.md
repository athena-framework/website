Athena utilizes the [Dependency Injection (DI)][Athena::DependencyInjection] component in order to provide a service container layer. DI allows controllers/other services to be decoupled from specific implementations. This also makes testing easier as test implementations of the dependencies can be used.

In Athena, most everything is a service that belongs to the container, which is unique to each request.  The major benefit of this is it allows various types to be shared amongst the application without having them bleed state between requests.  This section is _NOT_ an in-depth guide on what DI is, or all the features the DI component has.  It is instead going to focus on high level usage and implementation specifics on how it is used within Athena itself; such how to register services and use them within other types.

See the [API Docs][Athena::DependencyInjection] for more details.

## Basic Usage

A type (class or struct) can be registered as a service by applying the [ADI::Register][Athena::DependencyInjection::Register] annotation to it.  Services can depend upon other services by creating an `initializer` method type to the other service.

```crystal
require "athena"

# Register an example service that provides a name string.
@[ADI::Register]
class NameProvider
  def name : String
    "World"
  end
end

# Register another service that depends on the previous service and provides a value.
@[ADI::Register]
class ValueProvider
  def initialize(@name_provider : NameProvider); end
  
  def value : String
    "Hello " + @name_provider.name
  end
end

# Register a service controller that depends upon the ValueProvider.
@[ADI::Register(public: true)]
class ExampleController < ART::Controller
  def initialize(@value_provider : ValueProvider); end
  
  @[ARTA::Get("/")]
  def get_value : String
    @value_provider.value
  end
end

ART.run

# GET / # => "Hello World"
```

!!! warning
    The "type" of the listener has an effect on its behavior!  When a `struct` service is retrieved or injected into a type, it will be a copy of the one in the SC (passed by value). This means that changes made to it in one type, will *NOT* be reflected in other types. A `class` service on the other hand will be a reference to the one in the SC. This allows it to share state between services.
