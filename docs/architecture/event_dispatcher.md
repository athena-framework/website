As mentioned in the [architecture](README.md#framework-architecture) section, Athena Framework is an event based framework utilizing the [Event Dispatcher][Athena::EventDispatcher] component as its form of middleware.

## Basic Usage

The primary use case for event listeners is to tap into the life-cycle of the request, such as adding common headers, setting state extracted from the request, or whatever else the application requires.
Custom events may also be defined, but more on this soon.

```crystal
require "athena"

@[ADI::Register]
class CustomListener
  include AED::EventListenerInterface

  @[AEDA::AsEventListener]
  def on_response(event : ATH::Events::Response) : Nil
    event.response.headers["FOO"] = "BAR"
  end
end

class ExampleController < ATH::Controller
  get "/" do
    "Hello World"
  end
end

ATH.run

# GET / # => Hello World (with `FOO => BAR` header)
```

See [AEDA::AsEventListener][] for more information.

TIP: A single event listener may listen on multiple events. Instance variables can be used to share state between the events.

WARNING: The "type" of the listener has an effect on its behavior!
When a `struct` service is retrieved or injected into a type, it will be a copy of the one in the SC (passed by value).
This means that changes made to it in one type, will *NOT* be reflected in other types.
A `class` service on the other hand will be a reference to the one in the SC. This allows it to share state between services.

## Custom Events

Using events can be a helpful design pattern to allow for code that is easily extensible.
An event represents something _has happened_ where nobody may be interested in it, or in other words there may be zero or more listeners listening on a given event.
A more concrete example is an event could be dispatched after some core piece of application logic.
From here it would be easy to tap into when this logic is executed to perform some other follow up action, without increasing the complexity of the type that performs the core action.
This also adheres to the [single responsibility](../why_athena.md#single-responsibility) principle.

```crystal
require "athena"

# Define a custom event
class MyEvent < AED::Event
  property value : Int32

  def initialize(@value : Int32); end
end

# Define a listener that listens our the custom event.
@[ADI::Register]
class CustomEventListener
  include AED::EventListenerInterface

  @[AEDA::AsEventListener]
  def call(event : MyEvent) : Nil
    event.value *= 10
  end
end

# Register a controller as a service,
# injecting the event dispatcher to handle processing our value.
@[ADI::Register]
class ExampleController < ATH::Controller
  def initialize(@event_dispatcher : AED::EventDispatcherInterface); end

  @[ARTA::Get("/{value}")]
  def get_value(value : Int32) : Int32
    event = MyEvent.new value

    @event_dispatcher.dispatch event

    event.value
  end
end

ATH.run

# GET /10 # => 100
```
