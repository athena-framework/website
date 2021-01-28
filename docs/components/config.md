Athena includes the [Athena::Config][] component as a means to configure an Athena application, which consists of two main aspects: [Athena::Config::Base][] and [Athena::Config::Parameters][]. `ACF::Base` relates to _how_ a specific feature/component functions, e.g. the [CORS Listener](Athena::Routing::Listeners::CORS).  `ACF::Parameters` represent reusable configuration values, e.g. a partner API URL for the current environment.

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

The parameters and configuration can be accessed directly via `ACF.parameters` and `ACF.config` respectively.  However there are better ways; direct access is discouraged.

By default both `ACF::Base` and `ACF::Parameters` types are instantiated by calling `.new` on them without any arguments.  However, `ACF.load_configuration` and/or `ACF.load_parameters` methods can be redefined to change _how_ each object is created.  An example of this could be deserializing a `YAML`, or other configuration type, file into the type itself.

```crystal
# Overload the method that supplies the `ACF::Base` object to create it from a configuration file.
# NOTE: This of course assumes each configuration types includes `JSON::Serializable` or some other deserialization implementation.
def ACF.load_configuration : ACF::Base
  ACF::Base.from_json File.read "./config.json"
end
```

## Parameters



## Configuration

A core part of the config component is defining a `YAML` based way to configure an application in the form of `athena.yml`.  Other components and/or developers may add configuration options to [ACF::Base][Athena::Config::Base].  This utilizes `YAML::Serializable`, with the `Strict` module in order to provide type safe configuration for an application.

### CORS

Currently the only configurable piece of Athena is [ART::Config::CORS][Athena::Routing::Config::CORS] to support configuring the [ART::Listeners::CORS][Athena::Routing::Listeners::CORS] listener.

```yaml
---
routing:
  cors:
    allow_credentials: true
    allow_origin: 
      - https://api.myblog.com
    allow_methods:
      - GET
      - POST
      - PUT
      - DELETE
```



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
