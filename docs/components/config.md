Athena includes the [Athena::Config][] component as a means to configure an Athena application, which consists of two main aspects: [ACF::Base][Athena::Config::Base] and [ACF::Parameters][Athena::Config::Parameters]. `ACF::Base` relates to _how_ a specific feature/component functions, e.g. the [CORS Listener](Athena::Routing::Listeners::CORS).  `ACF::Parameters` represent reusable configuration values, e.g. a partner API URL for the current environment.

## Basics

Both configuration and parameters make use of the same high level implementation.  A type is used to "model" the structure and type of each value, whether it's a scalar value like a `String`, or another object.  These types are then added into the base types provided by `Athena::Config`.  This approach provides full compile time type safety both in the structure of the configuration/parameters, but also the type of each value.  It also allows for plenty of flexibility in _how_ each object is constructed.

!!!tip
    Structs are the preferred type to use, especially for parameters. 

From an organization standpoint, it is up to the user to determine how they wish to define/organize these configuration/parameter types.  However, the suggested way is to use a central file that should require the individual custom types, for example:

```crystal
# config/config_one.cr
record NestedParameters, id : Int32 = 1  

# Define a struct to store some parameters;
# a scalar value, and a nested object.
struct ConfigOne
  getter do_something : Bool = true
  getter nested_config : NestedConfig = NestedConfig.new
  
  getter special_value : Float64
  
  # Using getters with default values is the suggested way to handle simple/static types.
  # An argless constructor can also be used to apply more custom logic to what the values should be.
  def initialize
    @special_value = # ...
  end
end

# config/config_two.cr
record ConfigTwo, keys : Array(String) = ["a", "b", "c"]

# config.cr
require "./config/config_one"
require "./config/config_two"
# ...

# It is suggested to define custom parameter/configuration types within a dedicated namespace
# e.g. `app`, in order to avoid conflicts with built in types and/or third party shards.
struct MyApp
  getter config_one : ConfigOne = ConfigOne.new
  getter config_two : ConfigTwo = ConfigTwo.new
end

# Add our configuration type into the base type.
class ACF::Base
  getter app : MyApp = MyApp.new
end
```

The parameters and configuration can be accessed directly via `ACF.parameters` and `ACF.config` respectively.  However there are better ways; direct access is (mostly) discouraged.

By default both `ACF::Base` and `ACF::Parameters` types are instantiated by calling `.new` on them without any arguments.  However, `ACF.load_configuration` and/or `ACF.load_parameters` methods can be redefined to change _how_ each object is created.  An example of this could be deserializing a `YAML`, or other configuration type, file into the type itself.

```crystal
# Overload the method that supplies the `ACF::Base` object to create it from a configuration file.
# NOTE: This of course assumes each configuration types includes `JSON::Serializable` or some other deserialization implementation.
def ACF.load_configuration : ACF::Base
  ACF::Base.from_json File.read "./config.json"
end
```

## Configuration

Configuration in Athena is mainly focused on "configuring" _how_ specific features/components provided by Athena itself, or third parties, function at runtime.  This is best explained with an example, such as how [ART::Config::CORS][Athena::Routing::Config::CORS] can be used to control [ART::Listeners::CORS][Athena::Routing::Listeners::CORS] listener.  Say we want to enable CORS for our application from our APP URL, expose some custom headers, and allow credentials to be sent.  To do this we would want to redefine the configuration type's `self.configure` method.  This method should return an instance of `self`, configured how we wish.  Alternatively, it could return `nil` to disable the listener, which is the default.

```crystal
def ART::Config::CORS.configure : ART::Config::CORS?
  new(
    allow_credentials: true,
    allow_origin: %(https://app.example.com),
    expose_headers: %w(X-Transaction-ID X-Some-Custom-Header),
  )
end
```

Other configurable types would be handled in a similar fashion.  However, in some cases `nil` may not be a valid return value if it's required.

### Configuration Resolver

The config component also defines the [ACF::ConfigurationResolverInterface][Athena::Config::ConfigurationResolverInterface] type, which is wired up as a service automatically in order to inject it as a dependency.  This type is the preferred way to access configuration, as opposed to directly via `ACF.config`.

```crystal
@[ADI::Register]
class MyService
  def initialize(@configuration_resolver : ACF::ConfigurationResolverInterface); end
  
  def execute : Nil
    # `config` would be the configured `MyServiceConfig` instance, or `nil` if it optional and not configured.
    config = @configuration_resolver.resolve(MyServiceConfig)
    
    # ...
  end
end
```

## Parameters

Parameters represent reusable values that can be used as part of an application's configuration, or directly within the application's services.  Parameters allow configuration to be implemented in a way that is agnostic of the current environment.  For example, the URL of the application is a common piece of information, used both in configuration and other services for redirects.  This URl could be defined as a parameter to allow its definition to be centralized and reused.

```crystal
# Assume we added our `AppParams` type to the base `ACF::Parameters` type
# within our centralized configuration file, as mentioned in the "Basics" section.
struct AppParams
  # A getter with a default value is the simplest solution.
  getter app_url : String = ENV["APP_URL"]

  # Alternatively we can define/set the instance variable manually,
  # such as if more complex logic is needed, or ENV vars are not being utilized.
  @app_url : String

  def initialize
    @app_url = case Athena.environment
               when "production" then "https://app.example.com"
               else                   "https://app.dev.example.com"
               end
  end
end
```

We could now update the configuration from the earlier example to use this parameter.

```crystal
def ART::Config::CORS.configure : ART::Config::CORS?
  new(
    allow_credentials: true,
    allow_origin: [ACF.parameters.app.app_url],
    expose_headers: %w(X-Transaction-ID X-Some-Custom-Header),
  )
end
```

With this change, the configuration is now decoupled from the current environment/location where the application is running.  Common parameters could also be defined in their own shard in order to share the values between multiple applications.  It is also possible to access the same parameter directly within a service via a feature of the [Dependency Injection](./dependency_injection.md) component.  See the [Parameters][Athena::DependencyInjection::Register--parameters] section for details.

!!!note
    Accessing parameters directly via `ART.parameters` within a configuration type should be considered the only usecase for direct access.

## Custom Annotations

Athena integrates the `Config` component's ability to define custom annotation configurations.  This feature allows developers to define custom annotations, and the data that should be read off of them, then apply/access the annotations on [ART::Controller][Athena::Routing::Controller] and/or [ART::Action][Athena::Routing::Action]s.

This is a powerful feature that allows for almost limitless flexibility/customization.  Some ideas include: storing some value in the request attributes, raise an exception, invoke some external service; all based on the presence/absence of it, a value read off of it, or either/both of those in-conjunction with an external service.

```crystal
require "athena"

# Define our configuration annotation with an optional `name` argument.
# A default value can also be provided, or made not nilable to be considered required.
ACF.configuration_annotation MyAnnotation, name : String? = nil

# Define and register our listener that will do something based on our annotation.
@[ADI::Register]
class MyAnnotationListener
  include AED::EventListenerInterface

  def self.subscribed_events : AED::SubscribedEvents
    AED::SubscribedEvents{ART::Events::View => 0}
  end

  def call(event : ART::Events::View, dispatcher : AED::EventDispatcherInterface) : Nil
    # Represents all custom annotations applied to the current ART::Action.
    ann_configs = event.request.action.annotation_configurations

    # Check if this action has the annotation
    unless ann_configs.has? MyAnnotation
      # Do something based on presence/absence of it.
      # Would be executed for `ExampleController#one` since it does not have the annotation applied.
    end

    my_ann = ann_configs[MyAnnotation]

  	# Access data off the annotation.
    if my_ann.name == "Fred"
      # Do something if the provided name is/is not some value.
      # Would be executed for `ExampleController#two` since it has the annotation applied, and name value equal to "Fred".
    end
  end
end

class ExampleController < ART::Controller
  @[ART::Get("one")]
  def one : Int32
    1
  end

  @[ART::Get("two")]
  @[MyAnnotation(name: "Fred")]
  def two : Int32
    2
  end
end

ART.run
```

The [Cookbook](../cookbook/listeners#pagination) includes an example of how this can be used for pagination.
