Athena includes the [Config](https://athena-framework.github.io/config/Athena/Config.html) component as a means to configure an Athena application.

## Configuration

A core part of the config component is defining a `YAML` based way to configure an application in the form of `athena.yml`.  Other components and/or developers may add configuration options to [ACF::Base](https://athena-framework.github.io/athena/Athena/Config/Base.html).  This utilizes `YAML::Serializable`, with the `Strict` module in order to provide type safe configuration for an application.

### CORS

Currently the only configurable piece of Athena is [ART::Config::CORS](https://athena-framework.github.io/athena/Athena/Routing/Config/CORS.html) to support configuring the [ART::Listeners::CORS](https://athena-framework.github.io/athena/Athena/Routing/Listeners/CORS.html) listener.

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

Athena integrates the `Config` component's ability to define custom annotation configurations.  This feature allows developers to define custom annotations, and the data that should be read off of them, then apply/access the annotations on [ART::Controller](https://athena-framework.github.io/athena/Athena/Routing/Controller.html) and/or [ART::Action](https://athena-framework.github.io/athena/Athena/Routing/Action.html)s.

This is a powerful feature that allows for almost limitless flexibility/customization.  Some ideas include: storing some value in the request attributes, raise an exception, invoke some external service; all based on the presence/absence of it, a value read off of it, or either/both of those in-conjunction with an external service

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
    AED::SubscribedEvents{ART::Events::View => 255}
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
